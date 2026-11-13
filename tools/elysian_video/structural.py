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
        span=207*access.smooth((p-.2)/.66)
        access.line(c,[(x-span,y),(x+span,y)],'#e7eee3',3.4)
        for sign in (-1,1):
            access.line(c,[(x+sign*span,y-17),(x+sign*span,y+17)],'#d5ede0',4)
    c.save()
    field=skia.Path()
    field.addOval(skia.Rect.MakeXYWH(x-252,y-184,504,368))
    c.clipPath(field,doAntiAlias=True)
    level=224+(t*73)%365
    sweep_paint=access.grad(x,level,x,level+56,['#6f9f96','#c7ede0','#6f9f96'])
    sweep_paint.setAlpha(105)
    c.drawRect(skia.Rect.MakeXYWH(x-260,level,520,56),sweep_paint)
    c.restore()
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


def delivery_route_plan(c,t):
    c.drawImageRect(valve.route_plate(planning=True),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    progress = access.smooth((t-.3)/8.5)
    route = angiogram.art.trace(valve.ROUTE,progress)
    access.line(c,route,'#f5ddb0',16,195)
    if t >= 9.54:
        angiogram.block(c,893,290,331,282,23,access.solid('#20443e'))
        access.text(c,'What CT can show',917,333,29,'#e7f2e8')
        access.text(c,'Size and bends',918,380,27,'#c4e2d4')
        bend = angiogram.art.curve((919,421),((980,386),(1048,453),(1191,418)))
        access.line(c,bend,'#bc8b85',22)
        access.line(c,bend,'#593b48',12)
        access.text(c,'Calcium in the wall',918,487,27,'#c4e2d4')
        access.line(c,[(924,526),(1188,526)],'#bc8b85',22)
        access.line(c,[(924,526),(1188,526)],'#593b48',12)
        access.line(c,[(1036,518),(1091,518)],'#f1d6a4',8)
    detail = ('The team can discuss another route or treatment' if t>=14.11
              else 'The team reviews the arteries before choosing access')
    access.rect(c,0,654,1280,66,access.solid('#dcece2'))
    access.text(c,detail,55,685,29,'#245c50')


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
        delivery_route_plan(c,t)
        return
    if ident=='P08':
        angiogram.clinical_credits(c,'TAVI PLANNING',(
            'ESC and EACTS · Valvular heart disease guidelines',
            'Guy’s and St Thomas’ NHS Foundation Trust · TAVI assessment'),
            'How transcatheter aortic valve implantation is performed')
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
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t,topic='TAVI PLANNING')

def recovery_plan(c,t):
    paper, ink, mint = '#eaf4eb', '#1c4c40', '#a9d3bc'
    access.rect(c,0,0,1280,720,access.solid(paper))
    angiogram.header(c,'The plan for recovery at home','TAVI RECOVERY')
    angiogram.block(c,491,166,711,456,26,access.solid('#1c433a'))
    if t>=9.76:
        appointment=access.smooth((t-9.76)/3.45)
        access.text(c,'Contact and next visit',69,315,39,ink)
        access.text(c,'Your plan is personal',69,391,34,ink,access.REGULAR)
        angiogram.block(c,618,225,455,307,20,access.solid('#b0d8be'))
        access.line(c,[(620,292),(1071,292)],'#375f52',8)
        if t<13.21:
            angiogram.block(c,658+289*appointment,328,66,158,9,access.solid('#527f69'))
        else:
            access.rect(c,618,301,455,231,access.solid('#b0d8be'))
            reveal=max(0,min(1,(t-13.21)/5.42))
            angiogram.block(c,654,330,383,152,14,access.solid('#305748'))
            curve=[(690,396),(757,443),(829,367),(880,413),(1004,357)]
            access.line(c,angiogram.art.trace(curve,reveal),'#f1d3a3',23)
        access.text(c,'Follow the plan your care team gives you',64,677,31,ink)
        return
    items = ('Wound care','Build up activity','Prescribed medicines')
    cue_times = (0, 4.7, 6.72, 9.76)
    for index,(label,cue) in enumerate(zip(items,cue_times)):
        y=238+index*90
        progress=access.smooth((t-cue)/.72)
        active=cue<=t<cue_times[index+1]
        sweep=max(0,min(1,(t-cue)/(cue_times[index+1]-cue)))
        access.text(c,label,75,y+12,36,ink,access.REGULAR)
        access.line(c,[(540,y),(1135,y)],'#44695b',2.5)
        if progress>0:
            access.line(c,[(540,y),(540+595*sweep,y)],mint,15)
            angiogram.dot(c,540+595*sweep,y,9 if active else 4,'#f5ddb0')
        if progress>.1:
            angiogram.dot(c,519,y,10,'#a8d5bb')
        if active and index==0:
            zoom=access.smooth(sweep)*110
            angiogram.block(c,742-zoom/2,258,132+zoom,50,8,access.solid('#d9bc9a'))
            angiogram.block(c,793-zoom/4,258,28+zoom/2,50,5,access.solid('#f3e2c9'))
        if active and index==1:
            for step in range(3):
                offset=(step*33+t*80)%115
                c.drawOval(skia.Rect.MakeXYWH(785+offset,351+(step%2)*11,20,10),access.solid(mint))
        if active and index==2:
            angiogram.block(c,807,439,108,30,15,access.solid('#a8d5bb'))
            access.line(c,[(861,441),(861,468)],'#385f51',3)
    access.text(c,'Follow the plan your care team gives you',64,677,31,ink)


def recovery_echo(c,p,t):
    valve.clinical(c,'P11',p,t)
    valve.result_check(c,0,t)


def recovery_follow_up(c,t):
    if t<11.9:
        recovery_echo(c,t/11.9,t)
        access.rect(c,0,0,1280,139,access.solid('#eaf4eb'))
        angiogram.header(c,'Follow-up checks the replacement valve','TAVI RECOVERY')
        access.rect(c,0,648,1280,72,access.solid('#eaf4eb'))
        label='The team may repeat an ultrasound' if t>=9.7 else 'The team reviews recovery and how the valve is working'
        access.text(c,label,59,682,30,'#255b4c')
        return
    access.rect(c,0,0,1280,720,access.solid('#eaf4eb'))
    angiogram.header(c,'Know who will arrange your follow-up','TAVI RECOVERY')
    angiogram.block(c,635,172,564,456,26,access.solid('#1c433a'))
    access.text(c,'Follow-up appointment',72,315,40,'#1c4c40')
    access.text(c,'Who to call with questions',72,524,37,'#1c4c40')
    angiogram.block(c,716,226,392,167,15,access.solid('#b0d8be'))
    access.line(c,[(718,269),(1105,269)],'#375f52',7)
    selected=max(0,min(1,(t-11.9)/3.48))
    angiogram.block(c,749+260*selected,278,65,87,6,access.solid('#4e7a65'))
    for day in range(5):
        x=782+65*day
        angiogram.dot(c,x,322,7,'#395e4e')
    call=max(0,min(1,(t-14.7)/3.97))
    call_path=[(746,445),(746,562),(1008,562),(1080,601),(1080,445),(746,445)]
    access.line(c,call_path,'#436e5e',21)
    access.line(c,angiogram.art.trace(call_path,call),'#b0d8be',21)
    for index in range(3):
        angiogram.dot(c,899+29*index,519,5+3*(.5+.5*sin(t*5-index)),'#e2f4e5')


def recovery(c,ident,p,t):
    if ident=='P01':
        if p<.42: valve.clinical(c,'P11',p/.42,t)
        else: recovery_echo(c,(p-.42)/.58,t)
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
        recovery_echo(c,p,t)
        access.rect(c,0,648,1280,72,access.solid('#eaf4eb'))
        label=('The team also checks for leakage around the frame' if t>=9.1
               else 'An ultrasound shows how the valve opens and closes')
        access.text(c,label,59,682,30,'#255b4c')
        return
    if ident=='P05':
        recovery_plan(c,t)
        return
    if ident=='P07':
        recovery_follow_up(c,t)
        return
    if ident=='P08':
        angiogram.clinical_credits(c,'TAVI RECOVERY',(
            'ESC and EACTS · Valvular heart disease guidelines',
            'Guy’s and St Thomas’ NHS Foundation Trust · TAVI recovery',
            'University Hospital Southampton · Post-TAVI care'),
            'TAVI, surgery and how the Heart Team weighs the options')
        return
    rows={
     'P02':('The first checks in hospital',(
         ('The covered access site',('Staff look for bleeding and swelling',),'band'),
         ('Rhythm and blood pressure',('Recovery time depends on the checks',),'pulse'))),
     'P06':('When to get emergency help',(
         ('Severe bleeding',('Call local emergency services',),'band'),
         ('Possible stroke signs',('Sudden face droop, arm weakness','or trouble speaking need emergency help'),'call'))),
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t,topic='TAVI RECOVERY')

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
    if ident=='P08':
        angiogram.clinical_credits(c,'HEART VALVE OPTIONS',(
            'ESC and EACTS · Valvular heart disease guidelines',
            'American Heart Association · Heart valve replacement options',
            'NHS · Recovering from heart valve replacement'),
            'Why a team may recommend coronary artery bypass',next_label='Next series · Cardiac surgery')
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
    }
    title,beats=rows[ident]
    emergency.triple(c,title,beats,p,t,topic='HEART VALVE OPTIONS')

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
