"""Align a complete narration to its illustrated scenes and export a captioned 1080p film."""
from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw

SERIES = Path(__file__).resolve().parent
FFMPEG = SERIES.parents[1] / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
FPS = 24
WORD = re.compile(r"\b[\w]+(?:[’'][\w]+)*\b", re.UNICODE)


def run(*args: object, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run([str(FFMPEG), '-hide_banner', *map(str, args)], check=True, capture_output=capture)


def duration(path: Path) -> float:
    p = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(path)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    match = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', p.stderr)
    if not match:
        raise ValueError(f'Cannot read media duration for {path}')
    h, m, s = match.groups()
    return 3600 * int(h) + 60 * int(m) + float(s)


def words(s: str) -> list[str]:
    return [m.group().casefold().replace('’', "'").replace("'", '') for m in WORD.finditer(s)]


def align(scenes: list[dict], transcript: list[dict], voice_length: float) -> tuple[list[float], list[tuple[float, float, str]], float]:
    expected, offsets = [], []
    for scene in scenes:
        offsets.append(len(expected))
        expected.extend(words(scene['narration']))
    observed, observed_times = [], []
    for item in transcript:
        tokens = words(item['text'])
        if not tokens or item.get('start') is None or item.get('end') is None:
            continue
        a, b = float(item['start']), float(item['end'])
        for k, token in enumerate(tokens):
            observed.append(token)
            observed_times.append((a + (b-a)*k/len(tokens), a + (b-a)*(k+1)/len(tokens)))
    matcher = difflib.SequenceMatcher(None, expected, observed, autojunk=False)
    mapping = {block.a + k: observed_times[block.b + k] for block in matcher.get_matching_blocks() for k in range(block.size)}
    score = len(mapping) / len(expected)
    if score < .92:
        raise ValueError(f'Narration alignment too weak: {score:.1%}')
    for i in range(len(expected)):
        if i in mapping:
            continue
        left = max((p for p in mapping if p < i), default=-1)
        right = min((p for p in mapping if p > i), default=len(expected))
        a = mapping[left][1] if left >= 0 else 0
        b = mapping[right][0] if right < len(expected) else voice_length
        gap = max(0, b-a) / (right-left-1)
        mapping[i] = (a + gap*(i-left-1), a + gap*(i-left))
    stops, cues = [], []
    for scene, off in zip(scenes, offsets):
        line = scene['narration']
        tokens = list(WORD.finditer(line))
        stops.append(mapping[off][0] if tokens else voice_length)
        first = 0
        while first < len(tokens):
            last = first + 1
            while last < len(tokens):
                text = line[tokens[first].start():tokens[last].end()]
                elapsed = mapping[off+last][1] - mapping[off+first][0]
                previous_gap = line[tokens[last-1].end():tokens[last].start()]
                if len(textwrap.wrap(text, 43)) > 2 or elapsed > 5.6 or (re.search(r'[.!?]', previous_gap) and last-first > 4):
                    break
                last += 1
            char_end = tokens[last].start() if last < len(tokens) else len(line)
            display = '\n'.join(textwrap.wrap(line[tokens[first].start():char_end].strip(), 43))
            a, b = mapping[off+first][0], mapping[off+last-1][1]
            cues.append((a, max(a+.25,b), display))
            first = last
    stops[0] = 0
    if any(b <= a for a,b in zip(stops, stops[1:])):
        raise ValueError(f'Scenes are not in spoken order: {stops}')
    return stops, cues, score


def stamp(seconds: float) -> str:
    ms = round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def normalize(source: Path, frames: int, target: Path) -> None:
    still = source.suffix.lower() in {'.png', '.jpg', '.jpeg'}
    seconds = frames/FPS
    inputs = ['-loop', '1', '-framerate', str(FPS)] if still else []
    factor = 1 if still else seconds / duration(source)
    vf = f'setpts={factor:.10f}*(PTS-STARTPTS),fps={FPS},scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=1'
    run('-v','error','-y',*inputs,'-i',source,'-filter_threads',2,'-vf',vf,'-an','-c:v','libx264','-preset','veryfast','-crf',19,'-threads',3,'-g',48,'-bf',0,'-frames:v',frames,'-video_track_timescale',24000,target)


def scene_source(episode: Path, scene: dict) -> Path:
    if scene.get('visual_file'):
        return episode / scene['visual_file']
    possible = list((episode/'production').glob(f'*/{scene["id"]}.*'))
    possible = [p for p in possible if p.suffix.lower() in {'.mp4','.png','.jpg','.jpeg'}]
    if len(possible) != 1:
        raise ValueError(f'Expected one visual for {scene["id"]}, found {possible}')
    return possible[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('episode', type=Path)
    parser.add_argument('stem')
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--stage-through', type=int, help='Prepare the first N completed visuals while later scenes are being rendered.')
    args = parser.parse_args()
    episode = args.episode.resolve()
    prod = episode/'production'
    scenes = json.loads((episode/'scenes.json').read_text(encoding='utf-8-sig'))
    if scenes[-1]['narration'].strip():
        scenes.append({'id':f'P{len(scenes)+1:02}', 'title':'Clinical sources', 'narration':''})
    transcript = json.loads((prod/'scribe.json').read_text(encoding='utf-8-sig'))
    if isinstance(transcript, dict):
        transcript = transcript['words']
    voice = prod/'alexander.mp3'
    end = duration(voice)
    stops, cues, score = align(scenes, transcript, end)
    frames = [round(s*FPS) for s in stops] + [round((end+8)*FPS)]
    output = prod/'delivery'
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'voice_seconds':end, 'video_seconds':frames[-1]/FPS, 'alignment_score':score, 'scenes':[]}
    for s, a, b in zip(scenes,frames,frames[1:]):
        manifest['scenes'].append({'id':s['id'],'title':s['title'],'start_seconds':a/FPS,'end_seconds':b/FPS})
    (output/'timing.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    subtitle = output/f'{args.stem}.en.srt'
    lines=[]
    for i,(a,b,caption) in enumerate(cues):
        if i+1<len(cues):
            b=min(b,cues[i+1][0]-.001)
        if b>a:
            lines.append(f'{len(lines)+1}\n{stamp(a)} --> {stamp(b)}\n{caption}\n')
    subtitle.write_text('\n'.join(lines),encoding='utf-8')
    print(f'Narration {end:.2f}s, script word match {score:.1%}, {len(lines)} caption cues, {len(scenes)} scenes',flush=True)
    if args.plan_only:
        return
    selected = scenes[:args.stage_through] if args.stage_through else scenes
    sources = [scene_source(episode,s) for s in selected]
    if any(not p.is_file() or p.stat().st_size==0 for p in sources):
        raise FileNotFoundError('One or more scene visuals are not ready')
    shots = output/'shots';shots.mkdir(exist_ok=True)
    segments=[]
    for s,source,a,b in zip(selected,sources,frames,frames[1:]):
        target=shots/f'{s["id"]}.mp4'
        info = source.stat()
        signature = {'source':str(source), 'mtime':info.st_mtime_ns, 'bytes':info.st_size, 'frames':b-a, 'fps':FPS}
        cache = target.with_suffix('.json')
        if not (target.is_file() and target.stat().st_size and cache.is_file() and json.loads(cache.read_text()) == signature):
            normalize(source,b-a,target)
            cache.write_text(json.dumps(signature),encoding='utf-8')
        segments.append(target)
        print(f'Ready {s["id"]} {source.name} ({(b-a)/FPS:.2f}s)',flush=True)
    if args.stage_through:
        return
    concat=output/'concat.txt'
    concat.write_text(''.join(f"file 'shots/{p.name}'\n" for p in segments),encoding='utf-8')
    video=output/f'{args.stem}.mp4'
    run('-v','error','-y','-f','concat','-safe',0,'-i',concat,'-i',voice,'-i',subtitle,'-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-c:a','aac','-b:a','192k','-c:s','mov_text','-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-movflags','+faststart',video)
    run('-v','error','-xerror','-i',video,'-map','0:v:0','-map','0:a:0','-f','null','-')
    columns=4
    sheet=Image.new('RGB',(columns*400,math.ceil(len(scenes)/columns)*247),'#e4eee9')
    for i,(s,a,b) in enumerate(zip(scenes,frames,frames[1:])):
        sample=shots/f'{s["id"]}.jpg'
        run('-v','error','-y','-ss',(a+(b-a)*.65)/FPS,'-i',video,'-frames:v',1,'-vf','scale=384:216',sample)
        x,y=(i%columns)*400,(i//columns)*247
        sheet.paste(Image.open(sample),(x+8,y+8))
        ImageDraw.Draw(sheet).text((x+10,y+229),f'{s["id"]} {s["title"]}',fill='#163a31')
    sheet.save(output/'decoded-review.jpg',quality=92)
    print(f'Full A/V decode passed: {video}, {duration(video):.2f}s',flush=True)


if __name__=='__main__':
    main()
