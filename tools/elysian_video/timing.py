"""Lock scene boundaries and captions to the complete Alexander recording."""
from difflib import SequenceMatcher
import argparse
import json
from pathlib import Path
import re
import textwrap

from .__main__ import ROOT, SERIES, FPS, WIDTH, HEIGHT, LEGACY_FFMPEG, run

WORD=re.compile(r"[^\W_]+(?:['’][^\W_]+)?",re.UNICODE)

def norm(s):
    return s.casefold().replace('’',"'").replace("'",'')

def clock(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def measured_duration(audio,ffmpeg):
    p=run(ffmpeg,'-i',audio,check=False,capture_output=True,encoding='utf-8',errors='replace')
    m=re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)',p.stderr)
    if not m: raise ValueError('Could not measure narration duration')
    h,m,s=m.groups()
    return int(h)*3600+int(m)*60+float(s)

def align_words(rows, transcript, duration):
    offsets=[]; desired=[]; heard=[]; times=[]
    for row in rows:
        offsets.append(len(desired))
        desired.extend(norm(m.group()) for m in WORD.finditer(row.get('narration','')))
    for item in transcript:
        tokens=[norm(m.group()) for m in WORD.finditer(item['text'])]
        if not tokens or item.get('start') is None or item.get('end') is None: continue
        a,b=float(item['start']),float(item['end'])
        heard.extend(tokens)
        times.extend((a+(b-a)*j/len(tokens),a+(b-a)*(j+1)/len(tokens)) for j in range(len(tokens)))
    matcher=SequenceMatcher(None,desired,heard,autojunk=False)
    matching={a+k:times[b+k] for a,b,n in matcher.get_matching_blocks() for k in range(n)}
    differences=[{'script':desired[a:b],'scribe':heard[c:d]} for op,a,b,c,d in matcher.get_opcodes()
                 if op!='equal']
    rate=len(matching)/len(desired)
    if rate<.96:
        raise ValueError(f'Narration word alignment {rate:.1%} requires review: {differences}')
    for i in range(len(desired)):
        if i in matching: continue
        left=max((k for k in matching if k<i),default=-1)
        right=min((k for k in matching if k>i),default=len(desired))
        start=matching[left][1] if left>=0 else 0
        end=matching[right][0] if right<len(desired) else duration
        step=max(0,end-start)/(right-left-1)
        matching[i]=(start+step*(i-left-1),start+step*(i-left))
    return offsets, desired, matching, rate, differences


def phrase_index(words, phrase):
    target = [norm(match.group()) for match in WORD.finditer(phrase)]
    matches = [i for i in range(len(words) - len(target) + 1) if words[i:i + len(target)] == target]
    if not target or len(matches) != 1:
        raise ValueError(f'Expected one occurrence of anchor phrase: {phrase!r}')
    return matches[0], matches[0] + len(target) - 1


def align(rows, transcript, duration, *, anchors=None):
    offsets, desired, matching, rate, differences = align_words(rows, transcript, duration)
    stops=[0.]
    for i in range(1,len(rows)):
        word=offsets[i]
        if word==len(desired):
            stops.append(duration)
        else:
            prior=matching[word-1][1]
            following=matching[word][0]
            stops.append((prior+following)/2)
    cues=[]
    for row,off in zip(rows,offsets):
        sentence=row.get('narration','')
        tokens=list(WORD.finditer(sentence))
        j=0
        while j<len(tokens):
            k=j+1
            while k<len(tokens):
                previous=sentence[tokens[k-1].end():tokens[k].start()]
                last=tokens[k+1].start() if k+1<len(tokens) else len(sentence)
                if (re.search(r'[.?!]',previous) and k-j>=4 or
                    len(textwrap.wrap(sentence[tokens[j].start():last],42))>2 or
                    matching[off+k][1]-matching[off+j][0]>5.4):
                    break
                k+=1
            last=tokens[k].start() if k<len(tokens) else len(sentence)
            text='\n'.join(textwrap.wrap(sentence[tokens[j].start():last],42))
            a,b=matching[off+j][0],matching[off+k-1][1]
            cues.append((a,b,text))
            j=k
    if anchors is None:
        return stops,cues,rate,differences
    phrase_times = {}
    indexes = {row['id']: i for i, row in enumerate(rows)}
    for scene, phrases in anchors.items():
        if scene not in indexes:
            raise ValueError(f'Unknown scene in phrase anchors: {scene}')
        i = indexes[scene]
        offset = offsets[i]
        end = offsets[i + 1] if i + 1 < len(offsets) else len(desired)
        scene_times = {}
        for key, spec in phrases.items():
            first, last = phrase_index(desired[offset:end], spec['phrase'])
            edge = spec.get('edge', 'start')
            if edge not in ('start', 'end'):
                raise ValueError(f'Invalid edge for {scene}.{key}: {edge!r}')
            scene_times[key] = matching[offset + first][0] if edge == 'start' else matching[offset + last][1]
        phrase_times[scene] = scene_times
    return stops,cues,rate,differences,phrase_times

def prepare(folder,audio,scribe,ffmpeg, *, anchors=None):
    rows=json.loads((folder/'scenes.json').read_text(encoding='utf-8-sig'))
    transcript=json.loads(scribe.read_text(encoding='utf-8-sig'))
    if isinstance(transcript,dict): transcript=transcript['words']
    duration=measured_duration(audio,ffmpeg)
    result=align(rows,transcript,duration,anchors=anchors)
    stops,cues,score,diff=result[:4]
    frames=list(map(lambda t:round(t*FPS),stops))
    last=rows[-1]
    holds=last.get('target_end_sec',0)-last.get('target_start_sec',0)
    frames.append(round((duration+(min(8,max(6,holds)) if not last.get('narration') else 0))*FPS))
    if not all(a<b for a,b in zip(frames,frames[1:])): raise ValueError('Scene times overlap or are empty')
    audio_rel=audio.relative_to(ROOT).as_posix()
    scenes=[]
    for row,a,b in zip(rows,frames,frames[1:]):
        source=folder/row['visual_file']
        spoken=row.get('narration','')
        scenes.append({'id':row['id'],'title':row['title'],'start_frame':a,'end_frame':b,'narration':spoken,
                       'audio':{'path':audio_rel,'in_sec':a/FPS,'out_sec':min(b/FPS,duration)}
                       if spoken else None,
                       'footage':{'path':source.relative_to(ROOT).as_posix(),'in_sec':0,
                                  'out_sec':row['target_end_sec']-row['target_start_sec'],
                                  'reference_only':True}})
    captions=folder/'captions.en.srt'
    buf=[]
    for i,(a,b,label) in enumerate(cues):
        cap=cues[i+1][0] if i+1<len(cues) else duration
        b=min(cap,max(a+.18,b))
        if round(b*1000)<=round(a*1000):
            raise ValueError(f'Non-positive cue duration around {clock(a)}')
        buf.append(f'{i+1}\n{clock(a)} --> {clock(b)}\n{label}\n')
    captions.write_text('\n'.join(buf),encoding='utf-8')
    chapter=folder/'chapters.txt'
    chapter.write_text(''.join(f'{a//(60*FPS):02}:{a//FPS%60:02} {row["title"]}\n'
                               for a,row in zip(frames,rows)),encoding='utf-8')
    data={'schema_version':1,'episode':folder.name,'fps':FPS,'size':[WIDTH,HEIGHT],'duration_frames':frames[-1],
          'caption_file':captions.name,'chapter_file':chapter.name,
          'voice_alignment':{'matched_fraction':score,'scribe_differences':diff,'requires_listening':True},
          'scenes':scenes}
    if anchors is not None:
        data['aligned_phrase_seconds'] = result[4]
    (folder/'timeline.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode')
    p.add_argument('audio',type=Path)
    p.add_argument('scribe',type=Path)
    p.add_argument('--ffmpeg',default=LEGACY_FFMPEG)
    args=p.parse_args()
    if not re.fullmatch(r'episode-\d{2}',args.episode): p.error('Expected episode-NN')
    data=prepare(SERIES/args.episode,args.audio.resolve(),args.scribe.resolve(),args.ffmpeg)
    print(f'{len(data["scenes"])} scenes at {data["duration_frames"]/FPS:.3f} seconds; word alignment '
          f'{data["voice_alignment"]["matched_fraction"]:.1%}')
