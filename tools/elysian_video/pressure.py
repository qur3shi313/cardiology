"""Physiology animation: aortic reference and distal coronary pressure."""
from math import sin, pi, exp
import json

import skia

from . import access, angiogram, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

TRACE_CYCLES = 3.2


def trace(c,x,y,width,amp,t,shade,*,dashed=False):
    points=[]
    for i in range(96):
        f=i/95
        cycle=(f*TRACE_CYCLES+t*.47)%1
        value=.7*exp(-((cycle-.24)/.105)**2)+.24*exp(-((cycle-.43)/.20)**2)
        points.append((x+f*width,y-amp*value))
    if dashed:
        for i in range(0,len(points)-2,5):
            access.line(c,points[i:i+3],shade,3.8)
    else:
        access.line(c,points,shade,4.3)


def diastolic_bands(c, x, y, width, height, t):
    """Highlight the same illustrative resting window for both pressure traces."""
    phase = (t * .47) % 1
    for beat in range(5):
        # Schematic phases only: the declining portion of each pressure beat.
        left = max(0, (beat + .62 - phase) / TRACE_CYCLES)
        right = min(1, (beat + .94 - phase) / TRACE_CYCLES)
        if left < right:
            access.rect(c, x + left * width, y, (right - left) * width, height,
                        access.solid('#9cc9b4', 82))

def diagram(c,ident,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e7f1e9'))
    c.drawOval(skia.Rect.MakeXYWH(54,255,269,343),
               art.gradient(50,255,324,595,['#bd736f','#7c414d']))
    c.drawOval(skia.Rect.MakeXYWH(75,282,224,292),access.solid('#742e44'))
    art_surface=art.artery(c,.1)
    rate=1.0 if ident=='P04' else .43
    s=art.Motion(1126,-280,12,-280,14,.1,rate)
    art.blood_flow(c,t*(1.5 if ident=='P04' else .73),s,art_surface)
    restenosis.trace_channel(c,t,art_surface,.1,rate)
    # A guide catheter sits in the aortic root/at the coronary origin.
    access.line(c,[(79,205),(114,256),(145,330),(177,371),(238,401)],'#2a5b58',23)
    access.line(c,[(79,205),(114,256),(145,330),(177,371),(238,401)],'#8bb4a7',13)
    access.line(c,[(79,205),(114,256),(145,330),(177,371),(238,401)],'#d3eade',3)
    tip=80+1046*access.smooth((p-.21)/.60) if ident=='P03' else 1126
    art.wire(c,tip)
    if tip>820:
        x=tip-30; y=art.center(x)
        c.drawRoundRect(skia.Rect.MakeXYWH(x-14,y-7,29,14),7,7,access.solid('#9edcda'))
        if ident=='P03':
            access.line(c,[(x,y),(x-67,y-93),(894,y-93)],'#1b6359',3)
            access.text(c,'Downstream sensor',875,y-109,31,'#174c42')
    if ident=='P03':
        access.line(c,[(140,333),(217,239),(415,239)],'#2c655a',3)
        access.text(c,'Aortic reference',224,222,32,'#164a40')
        detail='Pressure at the guide catheter and beyond the narrowing'
        title='Two pressure measurements'
    else:
        y=601
        angiogram.block(c,50,555,1171,133,24,access.solid('#153832'))
        if ident == 'P05':
            diastolic_bands(c, 670, y - 14, 489, 68, t)
        trace(c,670,y+27,489,34,t,'#b0e6cf')
        trace(c,670,y+47,489,25,t,'#deb98f',dashed=True)
        access.text(c,'Conceptual pressure signals',70,y+14,29,'#d9ede2')
        title='FFR: increased-flow condition' if ident=='P04' else 'iFR: resting heartbeat window'
        detail='Illustrative signals, not clinical readings'
    angiogram.header(c,title,'CORONARY PHYSIOLOGY')
    if ident=='P03':
        access.text(c,detail,55,674,29,'#265f51')
    else:
        access.text(c,detail,72,654,24,'#a9d4c3',access.REGULAR)

def draw(c,ident,p,t):
    if ident=='P01':
        if p<.46:
            angiogram.imaging(c,'P29',p/.46,t,0)
            return
        access.rect(c,0,0,1280,720,access.solid('#11332e'))
        angiogram.header(c,'Can a narrowing limit blood supply?','CORONARY PHYSIOLOGY',True)
        for k in range(2):
            x=64+k*604
            angiogram.block(c,x,210,549,351,24,access.solid('#285148'))
            trace(c,x+41,378,465,104,t,'#d5eddc')
            trace(c,x+41,449 if k else 405,465,74,t+.05,'#f1c7a1',dashed=True)
        access.text(c,'Same-looking narrowing, different pressure pattern',56,661,31,'#b9dfd1')
        return
    if ident=='P02':
        c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
        first=p<.52
        phase=p/.52 if first else (p-.52)/.48
        fill=access.smooth(phase/.65)
        opacity=round(238-115*access.smooth((phase-.64)/.36))
        x,y=angiogram.contrast_paths(c,'left',fill,opacity,-15 if first else 7,True)
        if phase>.32:
            c.drawCircle(x,y,17,access.solid('#f3d2a2',120))
        angiogram.header(c,'What the angiogram shows','SIMULATED X-RAY',True)
        return
    if ident in ('P03','P04','P05'):
        diagram(c,ident,p,t)
        return
    cfg={
        'P06':('Putting the result in context','A measurement is one clue',
               ('Symptoms and other findings matter','when the team chooses a next step'),'check'),
        'P07':('What the test can answer','One question about one narrowing',
               ('Does it limit blood supply in','the tested condition?'),'pulse'),
        'P08':('A useful question to ask','What does the measurement change?',
               ('Ask how it affects the options','your team discusses with you'),'list'),
        'P09':('Clinical sources','Coronary physiology',
               ('ACC, AHA and SCAI guidance','ESC chronic coronary syndromes'),'check'),
    }
    title,heading,lines,icon=cfg[ident]
    restenosis.card(c,title,heading,lines,icon,p,t)

def render():
    episode=SERIES/'episode-11'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-pressure-film.mp4'
        tmp=visual/f'{ident}-pressure-film.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'pressure-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
