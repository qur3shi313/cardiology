"""Build frame-accurate Canva picture tracks and local review videos from revised scenes."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FFMPEG = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
OUT = HERE / 'full-review'
FPS = 30
END_HOLD = 7.0

@dataclass
class Shot:
    first: int
    last: int
    path: Path
    window: tuple[float,float] | None = None

def shots(route):
    def shot(a,b,p,window=None):return Shot(a,b,HERE/p,window)
    def png(i):return shot(i,i,f'editorial-scenes/{route[0].upper()}{i:02d}.png')
    def shared(i,name):return shot(i,i,f'shared-coronary-scenes/{name}.mp4')
    out=[png(i) for i in (1,2,3)]
    if route=='radial':
        files={4:'find-radial-artery',10:'diagnostic-guidewire',11:'diagnostic-catheter',12:'wrist-to-aorta',19:'withdraw-diagnostic-catheter',20:'remove-sheath-compress',21:'check-wrist-band',22:'recovery-and-discharge'}
        def radial(i):return shot(i,i,f'radial-route-scenes/R{i:02d}-{files[i]}.mp4')
        out+=[radial(4)]
        stops=(0,4.6,8.3,11.2,16.15,21.0)
        out += [shot(i,i,'wrist-proof/radial-access-motion-proof.mp4',(a,b)) for i,(a,b) in enumerate(zip(stops,stops[1:]),5)]
        out += [radial(i) for i in (10,11,12)]
        out += [shared(i,n) for i,n in enumerate(('reach-left-opening','left-contrast','radial-reposition','right-contrast','reading-the-result','deciding-the-next-step'),13)]
        out += [radial(i) for i in (19,20,21,22)]
        out += [png(i) for i in (23,24,25,26)]
    else:
        out += [shot(4,7,'femoral-route-scenes/femoral-f04-f07-arterial-entry.mp4'),shot(8,13,'femoral-proof/femoral-access-alexander-review.mp4'),shot(14,16,'femoral-route-scenes/femoral-f14-f16-diagnostic-route.mp4')]
        out += [shared(i,n) for i,n in enumerate(('reach-left-opening','left-contrast','femoral-left-withdrawal','femoral-right-advance','right-contrast','reading-the-result','deciding-the-next-step'),17)]
        out += [shot(24,27,'femoral-route-scenes/femoral-f24-f27-withdrawal-recovery.mp4')]
        out += [png(i) for i in (28,29,30,31)]
    return out

def run(args, **kwargs):
    return subprocess.run([str(FFMPEG),'-hide_banner',*map(str,args)],check=True,**kwargs)

def duration(path):
    rr=subprocess.run([str(FFMPEG),'-hide_banner','-i',str(path)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    m=re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)',rr.stderr)
    if not m: raise ValueError(f'Cannot read media duration: {path}')
    h,m,s=m.groups()
    return int(h)*3600+int(m)*60+float(s)

def exact_stops(route):
    data=json.loads((HERE/f'{route}-alexander-scene-timing.json').read_text(encoding='utf-8-sig'))
    starts=[round(float(s['narration_start_sec'])*FPS) for s in data['timing']]
    voice=HERE/f'{route}-alexander-full.m4a'
    voice_end=round(duration(voice)*FPS)
    return starts+[voice_end,voice_end+round(END_HOLD*FPS)],data,voice

def normalize(shot, seconds, frames, path):
    if shot.path.suffix.lower()=='.png':
        inputs=['-loop','1','-framerate',FPS,'-i',shot.path]
        trim=''
        factor=1.0
    else:
        inputs=['-i',shot.path]
        if shot.window:
            a,b=shot.window
            d=b-a
            trim=f'trim=start={a}:end={b},'
            # Ease the motion down modestly and hold its final instrument position.
            factor=min(1.28,seconds/d)
        else:
            d=duration(shot.path)
            trim=''
            # Grouped route segments were authored to the original voice cue times.
            # Preserve those times and hold the last frame for the inter-scene breath.
            factor=1.0 if shot.last>shot.first else seconds/d
    vf=f'{trim}setpts={factor:.9f}*(PTS-STARTPTS),fps={FPS},scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration={seconds+1:.6f}'
    run(['-loglevel','error','-y',*inputs,'-filter_threads',2,'-vf',vf,'-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads',3,'-g',60,'-bf',0,'-frames:v',frames,'-video_track_timescale',30000,path])

def assemble(route, only_plan=False):
    planned=shots(route)
    stops,data,voice=exact_stops(route)
    wanted=list(range(1,len(stops)))
    covered=[i for s in planned for i in range(s.first,s.last+1)]
    if covered!=wanted:raise ValueError(f'{route} scene coverage mismatch: {covered} != {wanted}')
    missing=[s.path for s in planned if not s.path.is_file() or s.path.stat().st_size==0]
    if missing:raise FileNotFoundError('Missing or unfinished: '+', '.join(map(str,missing)))
    OUT.mkdir(parents=True,exist_ok=True)
    work=OUT/f'{route}-shots';work.mkdir(exist_ok=True)
    entries=[]
    for s in planned:
        first,last=stops[s.first-1],stops[s.last]
        frames=last-first
        if frames<=0:raise ValueError(f'Scene {s.first} has no duration')
        path=work/f'{s.first:02d}-{s.last:02d}.mp4'
        entries.append({'scene_start':s.first,'scene_end':s.last,'frame_start':first,'frame_end':last,'frames':frames,'source':s.path.relative_to(HERE).as_posix(),'segment':path.relative_to(OUT).as_posix(),'source_window_sec':s.window})
        if not only_plan:
            normalize(s,frames/FPS,frames,path)
            print(f'{route}: encoded {s.first:02d}–{s.last:02d} ({frames/FPS:.2f}s)',flush=True)
    manifest={'route':route,'fps':FPS,'size':[1920,1080],'voice_file':voice.name,'voice_seconds':stops[-2]/FPS,'end_card_seconds':END_HOLD,'picture_seconds':stops[-1]/FPS,'total_frames':stops[-1],'scenes':entries}
    (OUT/f'{route}-assembly.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    if only_plan:return
    listing=OUT/f'{route}-concat.txt'
    listing.write_text(''.join("file '"+e['segment']+"'\n" for e in entries),encoding='utf-8')
    pic=OUT/f'elysian-angiography-{route}-picture.mp4'
    final=OUT/f'elysian-angiography-{route}-revised.mp4'
    sub=HERE/f'{route}-alexander.en.srt'
    run(['-loglevel','error','-y','-f','concat','-safe',0,'-i',listing,'-c:v','copy','-movflags','+faststart',pic])
    run(['-loglevel','error','-y','-i',pic,'-i',voice,'-i',sub,'-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-c:a','copy','-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata:s:a:0','language=eng','-movflags','+faststart',final])
    run(['-loglevel','error','-xerror','-i',final,'-map','0:v:0','-map','0:a:0','-f','null','-'])
    print(f'{route}: full decode passed, {duration(final):.2f}s, {final.stat().st_size:,} bytes',flush=True)

if __name__=='__main__':
    route=sys.argv[1]
    if route not in ('radial','femoral'):raise SystemExit('Choose radial or femoral.')
    assemble(route,'--plan' in sys.argv[2:])
