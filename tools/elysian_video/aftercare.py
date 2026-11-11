"""Make the connected post-angiography recovery film from approved scenes."""
import json
from pathlib import Path

import skia

from . import access, angiogram
from .__main__ import ROOT, SERIES, LEGACY_FFMPEG, FPS, WIDTH, HEIGHT, run, concat_list, scratch
from .encode import encode_scene

EDITORIAL={
    'P01':('What happens after the angiogram?',(
        ('Check the access site','Recovery starts with the entry site','band'),
        ('Understand your result','Ask what the images showed','check'),
        ('Know your next step','Make sure you have a follow-up plan','list'))),
    'P05':('Before leaving the hospital',(
        ('Short observation','Some people go home the same day','clock'),
        ('Longer monitoring','Some people stay for more checks','pulse'),
        ('Written plan and a contact','Ask who should accompany you','list'))),
    'P06':('Your written recovery plan',(
        ('Dressing and activity','Follow the instructions you receive','band'),
        ('Medicines','Confirm what to take and what changed','medicine'),
        ('After a stent','Contact the team before changing medicines','call'))),
    'P07':('What to watch at the access site',(
        ('A little bruising or soreness','Mild symptoms can occur','band'),
        ('Changes need a prompt call','Increasing pain, swelling, redness or drainage','call'),
        ('Fever or concern','Check who to call when the clinic is closed','check'))),
    'P08':('When to get emergency help',(
        ('Bleeding or rapid swelling','Get emergency help','band'),
        ('A cold, pale or numb hand or foot','Get emergency help','call'),
        ('Chest pain or trouble breathing','Get emergency help','pulse'))),
    'P09':('Why follow-up matters',(
        ('Review the findings','Ask what they mean for your symptoms','check'),
        ('Review the plan','Ask about medicines or further tests','medicine'),
        ('Cardiac rehabilitation','Ask about joining if recommended','pulse'))),
    'P10':('Three things to get in writing',(
        ('What did the images show?','Know the result and the next step','check'),
        ('What is my recovery plan?','Confirm medicines and activity guidance','list'),
        ('Who should I contact?','Know how to get help if needed','call'))),
    'P11':('Clinical sources',(
        ('Angiogram recovery','Guy’s and St Thomas’ NHS Foundation Trust','band'),
        ('Cath-lab best practices','Society for Cardiovascular Angiography & Interventions','check'),
        ('Patient recovery guidance','NHS and American Heart Association','list'))),
}

SHOTS={
    'P02':(('P35',0.24),('P36',0.27),('F25-close',0.26),('F26-checks',0.23)),
    'P03':(('F27-recovery',1.0),),
    'P04':(('P29',0.25),('P30',0.75)),
}
MARKS={'P01':(.0,.36,.72),'P05':(.0,.31,.71),'P06':(.0,.36,.67),'P07':(.0,.23,.67),
       'P08':(.0,.39,.69),'P09':(.0,.30,.67),'P10':(.0,.34,.65),'P11':(.0,.34,.67)}
AVAILABLE=SERIES/'episode-01/visuals'

def clip_for(name):
    if name in ('P35','P36'): return AVAILABLE/f'{name}-radial-cutaway.mp4'
    if name in ('P29','P30'): return AVAILABLE/f'{name}-angiogram-visual.mp4'
    return AVAILABLE/f'{name}.mp4'

def review_frame(canvas, ident, p, elapsed):
    from bisect import bisect_right
    s=MARKS[ident]
    idx=bisect_right(s,p)-1
    a,b=s[idx],s[idx+1] if idx+1<len(s) else 1
    local=(p-a)/(b-a)
    title,topics=EDITORIAL[ident]
    label,desc,kind=topics[idx]
    access.rect(canvas,0,0,1280,720,access.solid('#e4efe7'))
    if ident=='P08':
        access.rect(canvas,0,0,1280,720,access.solid('#f4ede4'))
    angiogram.header(canvas,title,'ANGIOGRAM RECOVERY')
    angiogram.block(canvas,694,198,492,404,44,access.solid('#183c35'))
    angiogram.icon(canvas,kind,local,elapsed)
    access.text(canvas,label,62,292,37,'#004b3d')
    desc_font=skia.Font(access.REGULAR,31)
    lines=[]
    line=''
    for word in desc.split():
        candidate=(line+' '+word).strip()
        if line and desc_font.measureText(candidate)>580:
            lines.append(line)
            line=word
        else:
            line=candidate
    if line: lines.append(line)
    for i,line in enumerate(lines):
        access.text(canvas,line,63,362+45*i,31,'#333b39',access.REGULAR)
    for j in range(len(topics)):
        angiogram.block(canvas,63+63*j,514,46,7,3,access.solid('#004b3d' if j==idx else '#a5c6b8'))
    if ident!='P11':
        access.text(canvas,'Follow the advice of your own care team',63,677,31,'#356a5b',access.REGULAR)
    else:
        access.text(canvas,'Next: Coronary angioplasty and stent placement',62,677,31,'#356a5b',access.REGULAR)

def montage(target, shots, frames):
    from .qa import invoke
    import re
    with scratch('elysian-recovery-') as temp:
        folder=Path(temp)
        rendered=[]
        cumulative=0
        offset=0
        for i,(name,fraction) in enumerate(shots):
            source=clip_for(name)
            if not source.is_file(): raise FileNotFoundError(source)
            p=invoke(str(LEGACY_FFMPEG),'-i',source,check=False)
            m=re.search(r'Duration: (\d+):(\d+):([\d.]+)',p.stderr.decode('utf-8','replace'))
            if not m: raise ValueError(f'Cannot measure {source}')
            h,mn,sec=m.groups()
            duration=int(h)*3600+int(mn)*60+float(sec)
            cumulative+=fraction
            end=round(cumulative*frames) if i+1<len(shots) else frames
            n=end-offset
            offset=end
            factor=n/FPS/duration
            out=folder/f'part-{i}.mp4'
            filt=(f'setpts={factor:.8f}*(PTS-STARTPTS),fps=30,scale={WIDTH}:{HEIGHT}:flags=lanczos,'
                  'setsar=1,tpad=stop_mode=clone:stop_duration=0.15,format=yuv420p')
            run(LEGACY_FFMPEG,'-v','error','-y','-i',source,'-map','0:v:0','-an',
                '-vf',filt,'-frames:v',n,'-c:v','libx264','-preset','fast','-crf',16,
                '-profile:v','high','-threads',2,'-g',60,'-bf',2,'-video_track_timescale',30000,out)
            rendered.append(out)
        names=concat_list(folder,'montage.txt',rendered)
        run(LEGACY_FFMPEG,'-v','error','-y','-f','concat','-safe',0,'-i',names,
            '-c','copy','-movflags','+faststart',target)

def render():
    episode=SERIES/'episode-05'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    selected={}
    for row in timeline['scenes']:
        ident=row['id']
        frames=row['end_frame']-row['start_frame']
        result=visual/f'{ident}-recovery-film.mp4'
        temporary=visual/f'{ident}-recovery-film.part.mp4'
        if not result.is_file():
            if ident in SHOTS:
                if not all(clip_for(name).is_file() for name,_ in SHOTS[ident]):
                    print(f'{ident} waiting on its selected clinical shot',flush=True)
                    continue
                montage(temporary,SHOTS[ident],frames)
            else:
                encode_scene(temporary,frames,
                             lambda c,f:review_frame(c,ident,f/max(1,frames-1),f/FPS))
            temporary.replace(result)
        selected[ident]={'path':result.relative_to(ROOT).as_posix(),'in_sec':0,
                         'out_sec':frames/FPS,'reference_only':False,'native_composition':True}
        (visual/'recovery-overrides.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({frames} frames)',flush=True)

if __name__=='__main__':
    render()
