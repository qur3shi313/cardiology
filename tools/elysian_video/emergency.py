"""Separate emergency PCI and multivessel decision films."""
from math import exp
import argparse
import json

import skia

from . import access, angiogram, coating, pci, pressure, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

def culprit_contrast(c,p,*,restored=False):
    """Show the same projection and branch before treatment and on the final check."""
    c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    branches,total=angiogram.tree('left')
    phase=p if restored else p*2-min(int(p*2),1)
    head=total*access.smooth(phase/.62)
    opacity=round(255-102*access.smooth((phase-.64)/.36))
    culprit=branches[1]
    cut_index=round((len(culprit[0])-1)*.43)
    cutoff=culprit[2]+culprit[1][cut_index]
    def xy(xy):
        u,v=xy
        return (222+3.48*u,101+1.88*v)
    for i,(pts,lengths,entry,thick) in enumerate(branches):
        remaining=head-entry
        if not restored and i in (4,5,6) and entry>=cutoff:
            continue
        if remaining<=0: continue
        end=sum(d<=remaining for d in lengths)
        if not restored and i==1: end=min(end,cut_index+1)
        coordinates=list(map(xy,pts[:end]))
        access.line(c,coordinates,'#566461',thick*2+4,opacity)
        access.line(c,coordinates,'#192522',thick*2.06,opacity)
    x,y=xy(culprit[0][cut_index])
    if p>.41:
        c.drawCircle(x,y,12,access.solid('#f8d18f',187))
        access.line(c,[(x,y),(x+125,y-84),(x+260,y-84)],'#fff0c6',3)
        label = 'Contrast passes this point' if restored else 'Contrast stops here'
        access.text(c,label,x+132,y-101,30,'#fff4d3')
    title = 'Checking flow after treatment' if restored else 'Finding the blockage'
    angiogram.header(c,title,'SIMULATED X-RAY',True)

def bypass(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e5eee7'))
    from .angiogram import art as anatomy
    heart=anatomy.MYOCARDIUM
    def xy(q): return (638+(q[0]-289)*1.9,227+(q[1]-110)*1.14)
    pts=list(map(xy,heart))
    c.drawPath(access.path(pts,True),access.grad(335,224,990,622,['#da9990','#a6636f','#694052']))
    aorta=anatomy.curve((306,229),((298,182),(300,132),(322,108)),((358,63),(392,100),(397,166)))
    access.line(c,list(map(xy,aorta)),'#a55a68',42)
    access.line(c,list(map(xy,aorta)),'#e2a197',28)
    lad=list(map(xy,anatomy.LAD))
    access.line(c,lad,'#77394c',17)
    access.line(c,lad,'#cf7d7b',10)
    narrowed=lad[int(len(lad)*.42)]
    c.drawCircle(*narrowed,10,access.solid('#dba176'))
    target=lad[int(len(lad)*.73)]
    origin=xy((355,87))
    path=anatomy.curve(origin,((origin[0]+180,origin[1]+105),(target[0]+187,target[1]-61),target))
    graft=anatomy.trace(path,access.smooth((p-.16)/.55))
    access.line(c,graft,'#356c60',22)
    access.line(c,graft,'#8fc4ad',13)
    if p>.71:
        for i in range(7):
            position=int(((t*.72+i/7)%1)*(len(path)-1))
            angiogram.dot(c,*path[position],8,'#d3f4d8',219)
    if p>.72:
        x,y=target
        access.line(c,[(x,y),(1012,y+7),(1188,y+7)],'#235d50',2.7)
        access.text(c,'Beyond the narrowing',917,y+50,29,'#21594c')
    angiogram.header(c,'Coronary bypass creates another route','MULTIVESSEL DISEASE')
    access.text(c,'Illustrated graft; the team chooses a plan for the patient',56,675,29,'#285f51')

def triple(c,title,beats,p,t,*,topic):
    index=min(len(beats)-1,int(p*len(beats)))
    heading,lines,icon=beats[index]
    restenosis.card(c,title,heading,lines,icon,p*len(beats)-index,t,topic=topic)


def restore_culprit_flow(c, t):
    check_start = 16.2
    if t >= check_start:
        culprit_contrast(c, min(1, (t-check_start)/(20.5-check_start)), restored=True)
        return

    lesion = art.LESION
    wire = 80 + 1046*art.ease(t, 5.98, 9.15)
    advance = art.ease(t, 9.27, 11.35)
    expansion = art.ease(t, 11.4, 13.22)
    deflate = art.ease(t, 13.25, 14.55)
    withdraw = art.ease(t, 14.6, 16.16)
    stent = -280+(lesion+280)*advance
    balloon = stent-(lesion+280)*withdraw
    access.rect(c,0,0,1280,720,access.solid('#e6f0e9'))
    lumen = art.artery(c, expansion)

    # Before the balloon deflates, moving blood is visible only up to the blocked site.
    c.save()
    if deflate < .68:
        c.clipRect(skia.Rect.MakeLTRB(0,0,lesion-33,720))
    restenosis.trace_channel(c,t,lumen,expansion,.45+.55*deflate)
    c.restore()

    # Keep a rim of clot against the wall as the channel widens in this example.
    xs = range(lesion-104, lesion+105, 4)
    top = [(x, art.center(x)-art.lumen_radius(x, -1, expansion)) for x in xs]
    depth = 1-.89*expansion
    lower = [(x, y+depth*(art.lumen_radius(x,-1,expansion)+art.lumen_radius(x,1,expansion))
                     *exp(-abs((x-lesion)/52)**2.6)) for x,y in top]
    c.save()
    c.clipPath(lumen, doAntiAlias=True)
    c.drawPath(art.enclosed(top,lower),art.gradient(537,302,723,485,['#763349','#431d2d']))
    c.restore()

    mesh_radius = 14+102*expansion
    if stent+art.MESH_HALF>art.X0:
        art.stent(c,stent,mesh_radius,False)
    if t >= 5.98:
        art.wire(c,wire)
    if balloon+art.BALLOON_HALF>art.X0:
        art.balloon(c,balloon,12+104*expansion*(1-deflate))
    if stent+art.MESH_HALF>art.X0:
        art.stent(c,stent,mesh_radius,True)

    if t < 5.98:
        detail = 'A clot blocks flow through this artery'
    elif t < 9.27:
        detail = 'A guidewire passes beyond the blockage'
    elif t < 13.25:
        detail = 'In this example, a balloon opens the stent'
    else:
        detail = 'The balloon comes out and the stent stays in place'
    angiogram.header(c,'Restoring blood flow','ILLUSTRATED EMERGENCY PCI')
    access.text(c,detail,55,677,31,'#20584d')


def emergency(c,ident,p,t):
    if ident=='P01':
        restenosis.lumen_view(c,t,'clot',p,scaffold=False)
        angiogram.header(c,'A blocked heart artery needs help fast','HEART ATTACK AND PCI')
        access.text(c,'A clot can interrupt blood flow to heart muscle',57,677,31,'#265e50')
    elif ident=='P02':
        triple(c,'Recognising a possible heart attack',(
           ('Chest pressure or breathlessness',('Symptoms can vary by person',),'pulse'),
           ('Other warning signs',('Sweating, nausea or pain in the arm,','back or jaw can occur'),'check'),
           ('Call local emergency services',('Get help immediately if a heart','attack is suspected'),'call')),p,t,topic='HEART ATTACK AND PCI')
    elif ident=='P03':
        triple(c,'Early emergency assessment',(
           ('An ECG records electrical activity',('A pattern may guide an urgent plan',),'pulse'),
           ('A blood test can show injury',('Troponin is one piece of the assessment',),'check')),p,t,topic='HEART ATTACK AND PCI')
    elif ident=='P04':
        triple(c,'The emergency treatment path',(
           ('Promptly restore blood flow',('For STEMI, opening the artery is urgent',),'vessel'),
           ('Treatment depends on the situation',('The emergency team chooses the path',),'list')),p,t,topic='HEART ATTACK AND PCI')
    elif ident=='P05':
        culprit_contrast(c,p)
    elif ident=='P06':
        restore_culprit_flow(c,t)
    elif ident=='P07':
        triple(c,'Recovery and prevention',(
           ('Monitoring after treatment',('Ask what the tests showed',),'pulse'),
           ('Ongoing care',('Medicines, rehabilitation and follow-up','may be part of your plan'),'list')),p,t,topic='HEART ATTACK AND PCI')
    else:
        angiogram.clinical_credits(c,'HEART ATTACK AND PCI',(
            'ACC, AHA and partner societies · Acute coronary syndromes',
            'SCAI · Expert consensus on STEMI and primary PCI',
            'American Heart Association · Heart attack warning signs'),
            'Treatment decisions when several coronary arteries are narrowed')

def multiple(c,ident,p,t):
    if ident=='P01':
        s='left' if p<.53 else 'right'
        c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
        local=p/.53 if s=='left' else (p-.53)/.47
        opacity=round(244-110*access.smooth((local-.63)/.37))
        point=angiogram.contrast_paths(c,s,access.smooth(local/.60),opacity,-15 if s=='left' else 20,True)
        if local>.47:
            x,y=point
            border=access.solid('#f1db9e'); border.setStyle(skia.Paint.kStroke_Style); border.setStrokeWidth(3)
            c.drawCircle(x,y,22,border)
        angiogram.header(c,'When several coronary arteries are narrowed','SIMULATED X-RAY',True)
        return
    if ident=='P02':
        triple(c,'Stable and emergency care differ',(
            ('Heart attack',('The artery causing the emergency','is often the first priority'),'pulse'),
           ('Stable coronary disease',('There is usually time to review tests','and discuss options'),'clock')),p,t,topic='MULTIVESSEL DISEASE')
    elif ident=='P03':
        if p>.62:
            pressure.diagram(c,'P03',(p-.62)/.38,t)
        else:
            angiogram.imaging(c,'P29',p/.62,t,0)
    elif ident=='P04':
        triple(c,'Medicines and prevention',(
            ('Part of care across options',('Medicines can help control symptoms',),'medicine'),
           ('Review goals and test results',('The team weighs potential benefits','and risks'),'check')),p,t,topic='MULTIVESSEL DISEASE')
    elif ident=='P05':
        pci.draw(c,'P09',p,t)
    elif ident=='P06':
        bypass(c,p,t)
    elif ident=='P07':
        triple(c,'The Heart Team and the patient',(
            ('Specialists review the options',('Cardiology, interventional cardiology','and cardiac surgery'),'check'),
           ('The patient is part of the decision',('Discuss risks, recovery and what','matters in daily life'),'list')),p,t,topic='MULTIVESSEL DISEASE')
    else:
        angiogram.clinical_credits(c,'MULTIVESSEL DISEASE',(
            'ACC, AHA and SCAI · Coronary revascularisation',
            'AHA and ACC · Chronic coronary disease',
            'ACC, AHA and partner societies · Acute coronary syndromes'),
            'What happens in aortic stenosis')

def render(number):
    ep=SERIES/f'episode-{number:02}'
    visual=ep/'visuals'; visual.mkdir(exist_ok=True)
    timeline=json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    draw=emergency if number==14 else multiple
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-clinical-film.mp4'
        temp=visual/f'{ident}-clinical-film.part.mp4'
        if not target.is_file():
            encode_scene(temp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            temp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'clinical-picture-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode',type=int,choices=(14,15))
    render(parser.parse_args().episode)
