"""Mechanism comparisons for coronary in-stent restenosis."""
from math import cos, sin, pi, exp
import json

import skia

from . import access, angiogram, coating, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

def lumen_view(c,t,kind,p=1.0,*,scaffold=True):
    access.rect(c,0,0,1280,720,access.solid('#e3eee7'))
    width=116
    radius=(lambda x:116-41*exp(-abs((x-art.LESION)/88)**2.6)) if kind=='underexpanded' else 116
    expansion=.52 if kind=='underexpanded' else 1.
    lumen=art.artery(c,expansion)
    s=art.Motion(-350,-350,10,art.LESION,width,expansion,.16 if kind=='clot' else 1)
    art.blood_flow(c,t,s,lumen)
    if scaffold:
        art.stent(c,art.LESION,radius,False)
    if kind in ('tissue','plaque','clot'):
        xs=range(art.LESION-153,art.LESION+154,4)
        if kind=='clot':
            spread=access.smooth(p/.60)
            top=[(x,art.center(x)-104) for x in xs]
            low=[(x,art.center(x)-104+196*spread*exp(-abs((x-art.LESION)/68)**2.7)) for x in xs]
            c.drawPath(art.enclosed(top,low),art.gradient(500,270,720,510,['#7f3348','#481c2e']))
        else:
            spread=access.smooth(p/.46)
            top=[(x,art.center(x)-112) for x in xs]
            low=[(x,art.center(x)-112+66*spread*exp(-abs((x-art.LESION)/114)**2.9)) for x in xs]
            c.drawPath(art.enclosed(top,low),art.gradient(480,278,780,350,['#e9b299','#a95568']))
            if kind=='plaque':
                core=list(range(art.LESION-68,art.LESION+70,4))
                a=[(x,art.center(x)-107) for x in core]
                b=[(x,art.center(x)-107+33*spread*exp(-((x-art.LESION)/51)**2)) for x in core]
                c.drawPath(art.enclosed(a,b),art.gradient(585,279,709,320,['#e9cf9e','#c29368']))
    if scaffold:
        art.stent(c,art.LESION,radius,True)

def label(c,title,detail):
    angiogram.header(c,title,'CORONARY STENTS')
    access.text(c,detail,55,677,30,'#1c5d50')

def cross_section(c,p,t,mode):
    access.rect(c,0,0,1280,720,access.solid('#183333'))
    center=(733,397)
    for r,shade in ((224,'#633a46'),(207,'#a57175'),(177,'#71504e'),(153,'#101e23')):
        angiogram.dot(c,*center,r,shade)
    for i in range(18):
        a=i*2*pi/18
        angiogram.dot(c,center[0]+164*cos(a),center[1]+164*sin(a),6,'#d8d1b8')
    c.drawOval(skia.Rect.MakeXYWH(596,268,177,130),access.solid('#8f6670'))
    angiogram.dot(c,*center,21,'#9ac6b7')
    angle=t*3.8
    x,y=center
    access.line(c,[(x,y),(x+140*cos(angle),y+140*sin(angle))],
                '#caeccd' if mode=='OCT' else '#94cdd0',4)
    angiogram.header(c,'Looking inside the stent','ILLUSTRATED IMAGING',True)
    access.text(c,'OCT uses light' if mode=='OCT' else 'IVUS uses sound',53,392,39,'#d9efe5')
    access.text(c,'Conceptual cross-section',55,677,31,'#b5d5c6')

def card(c,title,heading,lines,icon,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e7f0e8'))
    angiogram.header(c,title,'CORONARY STENTS')
    angiogram.block(c,681,190,508,412,39,access.solid('#173c35'))
    angiogram.icon(c,icon,p,t)
    def wrap(value,face,size):
        f=skia.Font(face,size)
        out=[]
        line=''
        for word in value.split():
            v=(line+' '+word).strip()
            if line and f.measureText(v)>590:
                out.append(line)
                line=word
            else:
                line=v
        if line: out.append(line)
        return out
    headings=wrap(heading,access.BOLD,38)
    for i,value in enumerate(headings):
        access.text(c,value,55,307+45*i,38,'#004b3d')
    body=[x for value in lines for x in wrap(value,access.REGULAR,30)]
    body_start=372+(len(headings)-1)*45
    for i,value in enumerate(body):
        access.text(c,value,55,body_start+43*i,30,'#333b39',access.REGULAR)
    access.text(c,'Follow your own care team’s advice',55,672,29,'#2b6456')

def draw(c,ident,p,t):
    if ident=='P01':
        angiogram.imaging(c,'P29',p,t,0)
        if p>.30:
            access.rect(c,0,66,1280,77,access.solid('#152d2b'))
            access.text(c,'Can a stented artery narrow again?',55,132,47,'#e8f6ea',access.HEADING)
        return
    if ident=='P02':
        lumen_view(c,t,'tissue',p)
        label(c,'In-stent restenosis','A narrowing can persist or return near the stent')
        return
    if ident=='P03':
        i=min(2,int(p*3))
        kind=('underexpanded','tissue','plaque')[i]
        detail=('The scaffold did not open fully','Tissue grows into the open channel','New plaque may form within the treated area')[i]
        lumen_view(c,t,kind,min(1.,p*3-i))
        label(c,('Underexpansion','Tissue growth','New plaque inside the stent')[i],detail)
        return
    if ident=='P04':
        if p<.66:
            lumen_view(c,t,'clot',p/.66)
            label(c,'A clot is a different problem','Stent thrombosis can interrupt blood flow suddenly')
        else:
            card(c,'Get emergency help','Severe chest pressure',
                 ('Sudden trouble breathing also','needs emergency assessment'),'call',(p-.66)/.34,t)
        return
    if ident=='P05':
        if p<.62:
            angiogram.imaging(c,'P29',p/.62,t,0)
        else:
            q=(p-.62)/.38
            angiogram.imaging(c,'P25',q,t,0)
            access.rect(c,0,67,1280,78,access.solid('#152d2b'))
            access.text(c,'The team also reviews earlier images',55,132,47,'#eff9ef',access.HEADING)
        return
    if ident=='P06':
        cross_section(c,p,t,'IVUS' if p<.56 else 'OCT')
        return
    if ident=='P07':
        if p<.34:
            lumen_view(c,t,'underexpanded')
            label(c,'The cause guides the next step','An underexpanded stent needs a mechanical assessment')
        elif p<.45:
            card(c,'The cause guides the next step','Reassess the mechanical problem',
                 ('The following are separate examples','of options for selected cases'),'check',(p-.34)/.11,t)
        elif p<.75:
            local=(p-.45)/.30
            inflation=access.smooth(local/.37)*(1-access.smooth((local-.58)/.14))
            x=art.LESION-(art.LESION+280)*access.smooth((local-.75)/.25)
            coating.device(c,local,t,True,1,x,12+75*inflation,True,inflation)
            label(c,'Drug-coated balloon','The balloon comes out after treatment')
        else:
            coating.device(c,p,t,True,1,wire=False,diffusion=.8)
            art.stent(c,art.LESION,103,True)
            label(c,'Another drug-eluting stent','A new inner scaffold remains within the treated section')
        return
    if ident=='P08':
        card(c,'Questions after the assessment','What was the cause?',
             ('Ask how the team checked the finding','and what changes in your plan'),'check',p,t)
        return
    card(c,'Clinical sources','SCAI, ESC, AHA and NHLBI',
         ('Original animation · Synthetic English narration','Next: recovery and medicines after PCI'),'list',p,t)

def render():
    episode=SERIES/'episode-09'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    result={}
    for row in timeline['scenes']:
        ident=row['id']; frames=row['end_frame']-row['start_frame']
        path=visual/f'{ident}-restenosis-film.mp4'
        temp=visual/f'{ident}-restenosis-film.part.mp4'
        if not path.is_file():
            encode_scene(temp,frames,lambda c,i:draw(c,ident,i/max(1,frames-1),i/FPS))
            temp.replace(path)
        result[ident]={'path':path.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':frames/FPS,
                       'reference_only':False,'native_composition':True}
        (visual/'restenosis-overrides.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({frames} frames)',flush=True)

if __name__=='__main__':
    render()
