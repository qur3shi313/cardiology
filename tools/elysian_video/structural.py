"""Planning, recovery, and comparison for the structural-heart episodes."""
import argparse
import json
from math import sin, cos, pi

import skia

from . import access, angiogram, emergency, pressure, restenosis, valve_implant as valve
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

def annulus_scan(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#123331'))
    x,y=700,405
    for w,h,sh in ((568,423,'#6c867f'),(502,367,'#a4b5a7'),(428,321,'#435b57'),(361,258,'#1b3835')):
        c.drawOval(skia.Rect.MakeXYWH(x-w/2,y-h/2,w,h),access.solid(sh))
    for sign in (-1,1):
        px=x+sign*279
        c.drawOval(skia.Rect.MakeXYWH(px-29,y-126,58,33),access.solid('#a8bdb0'))
    for i in range(6):
        a=.82+i*.14
        angiogram.dot(c,x+225*cos(a),y+159*sin(a),12+(i%3)*3,'#f3d7a1')
    if p>.20:
        access.line(c,[(x-207,y),(x+207,y)],'#e7eee3',3.4)
        for sign in (-1,1):
            access.line(c,[(x+sign*207,y-17),(x+sign*207,y+17)],'#d5ede0',4)
    access.rect(c,454,268+((t*47)%210),496,3,access.solid('#c7ede0',83))
    angiogram.header(c,'Where a new valve would sit','ILLUSTRATED CT VIEW',True)
    access.text(c,'Annulus and nearby coronary openings',59,674,31,'#d8f0e2')

def echo(c,p,t,implanted):
    if implanted:
        valve.clinical(c,'P11',p,t)
    else:
        valve.clinical(c,'P02',p,t)
    angiogram.block(c,62,198,335,193,19,access.solid('#173d35'))
    pressure.trace(c,85,325,287,69,t,'#c4ead7')
    access.text(c,'Illustrated ultrasound',86,245,29,'#e1f2e8')

def plan(c,ident,p,t):
    if ident=='P01':
        annulus_scan(c,p,t)
        return
    if ident=='P02':
        echo(c,p,t,False)
        return
    if ident=='P03':
        annulus_scan(c,p,t)
        return
    if ident=='P04':
        valve.groin_route(c,p,t)
        return
    rows={
     'P05':('The assessment goes beyond the valve',(
         ('Blood tests and heart rhythm',('The team may also review the arteries',),'pulse'),
         ('Day-to-day health and preferences',('The patient’s goals matter',),'list'))),
     'P06':('How the Heart Team recommends a plan',(
         ('Imaging, catheter treatment, surgery',('Specialists review the findings together',),'check'),
         ('A recommendation that fits',('Further tests or a surgical opinion','may be helpful'),'list'))),
     'P07':('Preparing for the discussion',(
         ('Why this option?',('Ask about risks and recovery',),'check'),
         ('What happens next?',('Next episode: how TAVI is performed',),'vessel'))),
     'P08':('Clinical sources',(
         ('Heart valve guidelines',('ESC and EACTS clinical guidance',),'vessel'),
         ('Imaging and patient guidance',('American Heart Association and NHS',),'list'))),
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t)

def recovery(c,ident,p,t):
    if ident=='P01':
        if p<.42: valve.clinical(c,'P11',p/.42,t)
        else: echo(c,(p-.42)/.58,t,True)
        return
    if ident=='P03':
        valve.clinical(c,'P11',p,t)
        q=((t*.92)%1)
        a=[(731,483),(757,536),(787,579),(812,603)]
        access.line(c,a,'#f8dc9f',5,190)
        for i,(x,y) in enumerate(a):
            angiogram.dot(c,x,y,7+(i==int(q*4))*6,'#fff2c4')
        angiogram.block(c,65,260,327,200,23,access.solid('#183b35'))
        pressure.trace(c,88,398,277,81,t,'#cbead7')
        access.text(c,'Rhythm monitoring',88,309,29,'#e1f2e7')
        return
    if ident=='P04':
        echo(c,p,t,True)
        return
    rows={
     'P02':('The first checks in hospital',(
         ('The covered access site',('Staff look for bleeding and swelling',),'band'),
         ('Rhythm and blood pressure',('Recovery time depends on the checks',),'pulse'))),
     'P05':('The plan for recovery at home',(
         ('Wound care, activity, medicines',('Follow the plan your team gives you',),'list'),
         ('Know your contact and next visit',('The details vary with your recovery',),'call'))),
     'P06':('When to get emergency help',(
         ('Severe bleeding',('Call local emergency services',),'band'),
         ('Possible stroke signs',('Sudden face droop, arm weakness','or trouble speaking need emergency help'),'call'))),
     'P07':('Follow-up checks',(
         ('Symptoms, medicines and rhythm',('The team may arrange another ultrasound',),'pulse'),
         ('Know who will arrange follow-up',('Ask whom to call with questions',),'list'))),
     'P08':('Clinical sources',(
         ('Heart valve recovery',('ESC, EACTS, AHA and NHS',),'check'),
         ('Next episode',('TAVI and surgical valve replacement',),'list'))),
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t)

def surgical(c,p,t):
    c.drawImageRect(valve.base(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    if p<.37:
        valve.leaflets(c,t,'stenosis')
        label='The diseased valve is removed'
    else:
        c.drawOval(skia.Rect.MakeXYWH(valve.CX-148,valve.ANNULUS-28,296,56),access.solid('#59726b'))
        c.drawOval(skia.Rect.MakeXYWH(valve.CX-129,valve.ANNULUS-19,258,40),access.solid('#aa7b79'))
        beat=valve.leaflets(c,t,'prosthetic')
        valve.pump_flow(c,t,beat,True)
        for i in range(9):
            x=valve.CX-130+i*32.5
            y=valve.ANNULUS-12+9*sin(i*pi/8)
            access.line(c,[(x-5,y-5),(x+5,y+5)],'#f5d8a1',3)
        label='A replacement valve is seated in its place'
    angiogram.header(c,'Surgical aortic valve replacement','HEART VALVE OPTIONS')
    access.text(c,label,56,680,30,'#245c51')

def compare(c,ident,p,t):
    if ident=='P01':
        if p<.36: valve.clinical(c,'P02',p/.36,t)
        elif p<.68: valve.clinical(c,'P11',(p-.36)/.32,t)
        else: surgical(c,.56+(p-.68)/.32*.44,t)
        return
    if ident=='P02':
        if p<.36: valve.groin_route(c,p/.36,t)
        else: valve.clinical(c,'P06',(p-.36)/.64,t)
        return
    if ident=='P03':
        surgical(c,p,t)
        return
    if ident=='P04':
        if p<.55: annulus_scan(c,p/.55,t)
        else: emergency.bypass(c,(p-.55)/.45,t)
        return
    rows={
     'P05':('Recovery and risks',(
         ('Early recovery can differ',('The team explains what to expect',),'clock'),
         ('Risks and support at home',('Discuss the risks that apply to you',),'list'))),
     'P06':('Thinking beyond the first procedure',(
         ('How long the valve may work',('Overall health and long-term needs matter',),'vessel'),
         ('Options for future care',('The first valve may affect another procedure',),'check'))),
     'P07':('A shared decision',(
         ('The Heart Team explains the reasons',('Bring your own goals and questions',),'list'),
         ('Next series: cardiac surgery',('Why a team may recommend','coronary artery bypass'),'vessel'))),
     'P08':('Clinical sources',(
         ('Heart valve guidance',('ESC and EACTS valve guidelines',),'check'),
         ('Patient resources',('American Heart Association and NHS',),'list'))),
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t)

def render(number):
    ep=SERIES/f'episode-{number:02}'
    visual=ep/'visuals'; visual.mkdir(exist_ok=True)
    timeline=json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig'))
    draw={17:plan,19:recovery,20:compare}[number]
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-structural-film.mp4'
        tmp=visual/f'{ident}-structural-film.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'structural-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode',type=int,choices=(17,19,20))
    render(p.parse_args().episode)
