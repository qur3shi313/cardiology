"""Original moving device views for the drug-eluting stent episode."""
from math import sin, pi
import json

import skia

from . import access, angiogram, pci, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

TITLES={
    'P01':('What stays in the artery?', 'Drug-eluting stent'),
    'P02':('Two jobs for one device','Support the artery and release medicine'),
    'P03':('How the stent gets there','Balloon-expandable stent'),
    'P04':('Medicine releases near the wall','Release rate and coating vary by design'),
    'P05':('A drug-coated balloon comes out','A balloon-only treatment leaves no new scaffold'),
    'P06':('Checking the treated segment','The team checks opening and downstream flow'),
    'P07':('Two different jobs for medicine','Coating and antiplatelet medicines'),
    'P08':('Follow-up after a stent','A treated segment and ongoing care'),
    'P09':('Clinical sources','Elysian Biomedical LLP · Educational animation'),
}

def device(c,p,t,mesh,expansion,balloon_x=-280,balloon_r=12,wire=True,diffusion=0):
    c.drawRect(skia.Rect.MakeWH(1280,720),
        art.gradient(0,0,1280,720,['#f9fbf4','#e4efe7','#cadfd4'],[0,.60,1]))
    lumen=art.artery(c,expansion)
    s=art.Motion(1126,balloon_x,balloon_r,art.LESION if mesh else -280,116,expansion,1)
    art.blood_flow(c,t,s,lumen)
    if mesh: art.stent(c,art.LESION,116,False)
    if wire: art.wire(c,1126)
    if balloon_x+art.BALLOON_HALF>art.X0: art.balloon(c,balloon_x,balloon_r)
    if mesh: art.stent(c,art.LESION,116,True)
    if diffusion:
        for i in range(16):
            x=art.LESION-122+(i*37)%244
            v=(t*.5+i*.153)%1
            radius=(116 if mesh else 92)+18*v
            y=art.center(x)+(-1 if i%2 else 1)*radius
            c.drawCircle(x,y,3.5,art.paint('#f7dc99',round(190*(1-v)*diffusion)))

def summary(c,ident,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e7f0e8'))
    angiogram.block(c,675,185,527,422,47,access.solid('#193d37'))
    if ident=='P06':
        if p<.55:
            angiogram.imaging(c,'P25',p/.55,t,0)
            access.rect(c,0,67,1280,79,access.solid('#142d2a'))
            access.text(c,TITLES[ident][0],55,132,48,'#f0fbf1',access.HEADING)
            return
        # Cross-sectional concept: concentric radial imaging within an expanded
        # scaffold, without depicting a specific device or a diagnostic result.
        center=(935,393)
        for r,color in ((154,'#6c3d48'),(131,'#a97679'),(104,'#51433d'),(92,'#111c1f')):
            angiogram.dot(c,*center,r,color)
        for i in range(16):
            from math import cos
            a=i*2*pi/16
            angiogram.dot(c,center[0]+100*cos(a),center[1]+100*sin(a),5,'#d6cec0')
        angiogram.dot(c,*center,21,'#9ec9b9')
        r=25+((p-.55)*220)%59
        pen=access.solid('#b9e7d3',137); pen.setStyle(skia.Paint.kStroke_Style); pen.setStrokeWidth(3)
        c.drawCircle(*center,r,pen)
        label='Imaging from inside the artery'
        detail=('A selected check of stent expansion',)
    elif ident=='P07':
        first=p<.43
        angiogram.icon(c,'vessel' if first else 'medicine',p if first else (p-.43)/.57,t)
        label='The coating' if first else 'Antiplatelet medicines'
        detail=('Helps limit growth near the stent',) if first else ('Help lower the chance of a clot','Follow your care team’s medicine plan')
    elif ident=='P08':
        first=p<.39
        angiogram.icon(c,'vessel' if first else 'check',p if first else (p-.39)/.61,t)
        label='One treated section' if first else 'Ongoing care'
        detail=('A stent supports this part of the artery',) if first else ('Discuss medicines and symptoms','Next: coronary drug-coated balloons')
    else:
        angiogram.icon(c,'list',p,t)
        label='Clinical sources'
        detail=('American Heart Association','Society for Cardiovascular Angiography','FDA-hosted device information')
    angiogram.header(c,TITLES[ident][0],'CORONARY STENTS')
    access.text(c,label,56,306,37,'#004b3d')
    for i,line in enumerate(detail):
        access.text(c,line,56,374+i*47,29,'#333b39',access.REGULAR)

def draw(c,ident,p,t):
    if ident in ('P06','P07','P08','P09'):
        summary(c,ident,p,t)
        return
    if ident=='P01':
        retract=access.smooth(p/.43)
        device(c,p,t,True,1,art.LESION-(art.LESION+280)*retract,14,True,p*.6)
    elif ident=='P02':
        device(c,p,t,True,1,wire=False,diffusion=access.smooth((p-.46)/.34))
    elif ident=='P03':
        if p<.50: pci.draw(c,'P08',p/.50,t)
        else: pci.draw(c,'P09',(p-.50)/.50,t)
        return
    elif ident=='P04':
        device(c,p,t,True,1,wire=False,diffusion=1)
    else:
        x=access.smooth((p-.13)/.38)
        out=access.smooth((p-.77)/.21)
        inflate=x*(1-access.smooth((p-.67)/.10))
        device(c,p,t,False,0.45*x,art.LESION-(art.LESION+280)*out,12+70*inflate,True,inflate)
    angiogram.header(c,TITLES[ident][0],'CORONARY STENTS')
    access.text(c,TITLES[ident][1],54,678,32,'#235e50')

def render():
    episode=SERIES/'episode-07'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; frames=row['end_frame']-row['start_frame']
        dst=visual/f'{ident}-coating-film.mp4'
        temp=visual/f'{ident}-coating-film.part.mp4'
        if not dst.is_file():
            encode_scene(temp,frames,lambda c,i:draw(c,ident,i/max(1,frames-1),i/FPS))
            temp.replace(dst)
        out[ident]={'path':dst.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':frames/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'coating-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({frames} frames)',flush=True)

if __name__=='__main__':
    render()
