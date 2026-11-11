"""Timeline-aligned native picture scenes for Topic 16, aortic stenosis."""

import argparse
from functools import lru_cache
import json
from math import cos, pi, sin
from random import Random

import skia

from .__main__ import FPS, ROOT, SERIES
from .access import HEADING, LOGO, grad, line, path, rect, solid
from .aortic import beat, draw_root, draw_valve_face, draw_valve_frame, ring, spline, valve_deposit_point
from .encode import encode_scene
from .reading import (DARK, GOLD, INK, SAMPLE, TEAL, WHITE, badge, blend, block,
                      clinical_backdrop, cue, heading, label, picture_entry)


FOLDER=SERIES/'episode-16'
ASSETS=FOLDER/'visuals'
W,H=1280,720


def dot(c,x,y,r,tone,alpha=255):
    c.drawCircle(x,y,r,solid(tone,alpha))


def guide_label(c,copy,x,y,target,*,right=False):
    tone='#205c52'
    tx,ty=target
    bend=x-28 if right else x+30
    line(c,((x,y+12),(bend,y+12),(tx,ty)),tone,2.8)
    dot(c,tx,ty,5.5,tone)
    label(c,copy,x,y,34,INK,align='right' if right else 'left')


def comparison(c,t,d):
    clinical_backdrop(c)
    p,opening,_=beat(t+.49)
    y=372+11*sin(t*.69)
    r=205+8*sin(t*.7)
    line(c,[(639,148),(639,611)],'#6e9f91',2.5,148)
    for x,calcium in ((328,0),(948,.93)):
        draw_valve_face(c,x,y,r,opening=opening,calcium=calcium)
    label(c,'Normal opening',328,641,39,INK,align='center')
    label(c,'Narrowed opening',948,641,39,INK,align='center')
    if t>3.1:
        c.drawImageRect(LOGO,skia.Rect.MakeXYWH(1177,42,56,56),SAMPLE)
        heading(c,'What happens in aortic stenosis',dark=False)
    else:
        label(c,'Aortic valve',58,91,39,INK,face=HEADING)


def normal_flow(c,t,d):
    clinical_backdrop(c)
    p,opening,contract=beat(t+.10)
    cx=660+24*sin(t*.28)
    cy=366+6*sin(t*.45)
    scale=.88+.03*cue(t,0,8.7)
    draw_root(c,cx,cy,scale,opening=opening,contraction=contract,flow=True,t=t)
    heading(c,'Blood leaves the left ventricle',dark=False)
    if t<8.4:
        guide_label(c,'Left ventricle',99,469,(cx-52*scale,cy+162*scale))
        guide_label(c,'Aorta',1114,192,(cx+5*scale,cy-163*scale),right=True)
    else:
        guide_label(c,'Aortic valve',1086,335,(cx+44*scale,cy-13*scale),right=True)
        badge(c,'Pumping · valve opens' if p<.52 else 'Relaxing · valve closes',68,624,dark=False,size=33)


def calcium_scene(c,t,d):
    clinical_backdrop(c)
    _,opening,_=beat(t+.37)
    if t<10.25:
        progress=.67+.26*cue(t,4.2,9.8)
        cx=666+43*sin(t*.26)
        cy=377+11*sin(t*.62)
        radius=230+16*cue(t,2.3,9)
        draw_valve_face(c,cx,cy,radius,opening=opening,calcium=progress)
        heading(c,'Stiff leaflets open less',dark=False)
        if t>4.25:
            target=valve_deposit_point(cx,cy,radius,opening=opening,calcium=progress)
            guide_label(c,'Calcium deposits',70,262,target)
        badge(c,'Three-leaflet example',58,633,dark=False,size=32)
    else:
        cx=654+28*sin((t-10.25)*.46)
        cy=380+8*sin((t-10.25)*.58)
        calcium=.08+.59*cue(t,15.8,20.4)
        draw_valve_face(c,cx,cy,235,opening=opening,calcium=calcium,cusps=2)
        heading(c,'Some valves have two leaflets',dark=False)
        badge(c,'Separate example · bicuspid valve',58,633,dark=False,size=32)


def workload(c,t,d):
    clinical_backdrop(c)
    _,opening,contraction=beat(t+.38)
    if t<5.6:
        line(c,[(639,144),(639,625)],'#6e9f91',2.2,157)
        for x,calcium in ((333,0),(943,.93)):
            draw_root(c,x,324,.79,opening=opening,calcium=calcium,contraction=contraction,flow=True,t=t)
        heading(c,'More work for the heart',dark=False)
        label(c,'Normal outlet',334,650,37,INK,align='center')
        label(c,'Tighter outlet',943,650,37,INK,align='center')
        return
    thickening=.92*cue(t,6.0,12.75)
    cx=646+30*sin(t*.31)
    cy=369+7*sin(t*.42)
    draw_root(c,cx,cy,.91,opening=opening,calcium=.93,contraction=contraction,
              hypertrophy=thickening,flow=True,t=t)
    if t<13:
        heading(c,'The muscle wall can thicken',dark=False)
        badge(c,'Changes over time',61,624,dark=False,size=34)
        guide_label(c,'Ventricular muscle',105,485,(cx-137,cy+109))
    else:
        heading(c,'The heart may have to work harder',dark=False)
        badge(c,'Effects vary from person to person',61,624,dark=False,size=32)


def clothed_person(c,x,y,scale,step=0.,*,shade='#4f8a7e'):
    c.save()
    c.translate(x,y)
    c.scale(scale,scale)
    q=sin(step)
    coat=spline((-52,-150),(((-30,-170),(29,-166),(47,-145)),
                  ((68,-119),(66,-72),(52,-43)),((24,-28),(-25,-30),(-52,-46)),
                  ((-68,-78),(-69,-121),(-52,-150))),True)
    for side in (-1,1):
        kick=side*q
        heel=(side*27+43*kick,129-18*max(0,kick))
        knee=(side*22+32*kick,52-12*max(0,-kick))
        line(c,[(side*23,-47),knee,heel],'#38584f',31)
        line(c,[(heel[0]-8,heel[1]+5),(heel[0]+21,heel[1]+5)],'#223d37',16)
    for side in (-1,1):
        swing=side*q
        line(c,[(side*48,-138),(side*67-17*swing,-93),(side*72-25*swing,-56)],
             '#3b7267',24)
    c.drawPath(coat,grad(-70,-157,64,-47,[shade,'#3e766c','#295e56']))
    line(c,[(6,-146),(5,-49)],'#9ac2b0',2.6,167)
    dot(c,0,-206,38,'#a1bcb0')
    c.drawPath(path(((-39,-204),(-33,-229),(-17,-245),(20,-242),(37,-225),(42,-202)),True),
               solid('#3f7167'))
    block(c,-30,-195,62,27,7,solid('#76978b'))
    c.restore()


def symptoms(c,t,d):
    clinical_backdrop(c)
    heading(c,'Symptoms can develop gradually',dark=False)
    floor_y=627
    line(c,[(44,floor_y),(1227,floor_y)],'#8db6a6',3.0)
    if t<10.3:
        moving=blend(268,633,cue(t,0,10.3))
        for i in range(9):
            start=34+(i*154-70*t)%1260
            line(c,[(start,598),(min(1265,start+64),598)],'#b8d1c6',4.0)
        c.drawOval(skia.Rect.MakeXYWH(moving-96,590,178,32),solid('#466f63',71))
        gait=t*6.6-.24*t*t
        clothed_person(c,moving,451+7*sin(gait*2),1.08,gait)
        if t<2.9:
            label(c,'Some people feel well for a long time',952,305,32,INK,align='center')
        elif t<6.45:
            label(c,'Breathlessness',760,303,40,INK)
            label(c,'Chest discomfort',760,364,38,INK)
        elif t<8.7:
            label(c,'Dizziness',800,303,42,INK)
            label(c,'Fainting',800,366,39,INK)
        else:
            label(c,'Reduced activity',804,344,38,INK)
    else:
        clothed_person(c,396,443,1.02+.04*sin(t*.6),step=.1)
        # A clinical review cue uses abstract equipment and a chart, with no
        # person-level prediction or assessment result.
        x=832+24*sin(t*.45)
        block(c,x-102,213,234,298,23,solid('#4c8879'))
        block(c,x-84,234,199,253,15,solid('#e7f3e6'))
        block(c,x-26,197,78,49,10,solid('#a9c6b3'))
        for i in range(4):
            y=290+i*50
            dot(c,x-57,y,7,'#5d9d8c',round(120+92*sin(t*.55+i)**2))
            line(c,[(x-32,y),(x+88,y)],'#77aa9c',4.4)
        label(c,'Symptoms and scan findings',x+14,562,34,INK,align='center')


@lru_cache(maxsize=1)
def echo_plate():
    surface=skia.Surface(W*2,H*2)
    c=surface.getCanvas()
    c.scale(2,2)
    rect(c,0,0,W,H,grad(0,0,W,H,['#142f2d','#26423e','#0d2423']))
    block(c,54,134,628,488,21,solid('#101a19'))
    block(c,708,134,520,488,21,solid('#172e2b'))
    random=Random(82)
    c.save()
    c.clipPath(path(((335,158),(96,589),(647,589)),True),doAntiAlias=True)
    for _ in range(710):
        x,y,r,a=(random.randrange(89,667),random.randrange(155,594),
                 random.randrange(1,4),random.randrange(23,107))
        dot(c,x,y,r,'#b9d3be',a)
    c.restore()
    return surface.makeImageSnapshot()


def echo(c,t,d):
    c.drawImageRect(echo_plate(),skia.Rect.MakeWH(W,H),SAMPLE)
    p,opening,contraction=beat(t+.21)
    cx=359+21*sin(t*.37)
    cy=397
    wedge=path(((335,158),(96,589),(647,589)),True)
    c.save()
    c.clipPath(wedge,doAntiAlias=True)
    c.save()
    c.translate(cx,cy)
    c.rotate(180)
    draw_root(c,0,0,.68,opening=opening,calcium=.91,contraction=contraction,
              monochrome=True,flow=False,t=t)
    c.restore()
    c.restore()
    heading(c,'An echocardiogram')
    label(c,'Simulated ultrasound',1218,63,31,WHITE,align='right')
    label(c,'Valve motion',354,652,36,WHITE,align='center')
    center=279
    line(c,[(751,center),(1184,center)],'#9bc6b6',2.0,177)
    for y in (350,423,496,568):
        line(c,[(751,y),(1184,y)],'#718c81',1.2,109)
    z=(t*.44)%1
    points=[]
    for i in range(125):
        x=751+i*3.45
        q=(i/48-z)%1
        envelope=sin(pi*q/.67)**1.2 if 0<q<.67 else 0
        y=center+(116+18*sin(t*.42))*envelope
        points.append((x,y))
    filled=path(((751,center),*points,(1179,center)),True)
    c.drawPath(filled,solid('#cde6ce',123))
    line(c,points,'#e5f0d9',3.1)
    label(c,'Doppler flow speed',970,652,36,WHITE,align='center')


def calendar(c,x,y,t):
    block(c,x-140,y-132,280,272,22,solid('#488b7b'))
    block(c,x-124,y-86,248,207,14,solid('#ebf5e8'))
    for dx in (-73,73):
        block(c,x+dx-9,y-153,18,58,8,solid('#82b3a1'))
    index=int((t*1.35)%12)
    for i in range(12):
        u=x-83+i%4*54
        v=y-53+i//4*62
        r=11+4*sin(t*3) if i==index else 6.3
        dot(c,u,v,r,'#ce9d5c' if i==index else '#75ac9c')


def next_steps(c,t,d):
    clinical_backdrop(c)
    if t<8.05:
        heading(c,'What happens next?',dark=False)
        calendar(c,355,370,t)
        x=812+15*sin(t*.6)
        draw_valve_face(c,x,365,145,opening=beat(t+.4)[1],calcium=.86)
        label(c,'Monitoring',353,625,37,INK,align='center')
        label(c,'Valve assessment',824,625,37,INK,align='center')
    elif t<12.1:
        heading(c,'Daily life matters in the decision',dark=False)
        clothed_person(c,370+111*cue(t,8.05,12.1),468,1.01,step=t*4.1)
        draw_root(c,859,370,.70,opening=beat(t)[1],calcium=.88,flow=True,t=t)
    else:
        heading(c,'Planning a possible valve replacement',dark=False)
        _,op,contract=beat(t+.39)
        draw_root(c,427,359,.79,opening=op,calcium=.88,contraction=contract,flow=True,t=t)
        x=930+18*sin(t*.51)
        halo=119+12*sin(t*1.5)
        dot(c,x,366,halo,'#dcece0',208)
        ring(c,x,366,halo,'#81b2a3',2.6)
        draw_valve_frame(c,x,419,1.18,expansion=1.,tone='#387c70')
        label(c,'Heart Team planning',x,626,35,INK,align='center')


@lru_cache(maxsize=1)
def end_card_plate():
    surface=skia.Surface(W*2,H*2)
    c=surface.getCanvas()
    c.scale(2,2)
    rect(c,0,0,W,H,grad(63,38,1190,714,['#133f37','#102f2e','#0c2423']))
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(62,57,84,84),SAMPLE)
    label(c,'Elysian Biomedical LLP',170,113,36,WHITE)
    label(c,'Cardiology Education Series',61,194,34,'#bfe9d5')
    label(c,'Clinical sources',59,277,51,WHITE,face=HEADING)
    label(c,'Original educational animation · Synthetic narration',60,643,28,'#d1ecde')
    return surface.makeImageSnapshot()


def end_card(c,t,d):
    c.drawImageRect(end_card_plate(),skia.Rect.MakeWH(W,H),SAMPLE)
    names=('American Heart Association','ESC / EACTS valve disease guideline')
    for i,name in enumerate(names):
        label(c,name,61,346+50*i,30,'#d3eee0',alpha=round(255*cue(t,.18+i*.28,1.05+i*.38)))
    p=cue(t,3.1,4.2)
    if p>0:
        label(c,'Next in the series',60,515,30,'#abd6c2',alpha=round(255*p))
        label(c,'How the Heart Team plans TAVI',60,573,35,WHITE,alpha=round(255*p))


SCENES={'P01':comparison,'P02':normal_flow,'P03':calcium_scene,'P04':workload,
        'P05':symptoms,'P06':echo,'P07':next_steps,'P08':end_card}


def still(scene,t,d,path):
    surface=skia.Surface(W,H)
    scene(surface.getCanvas(),t,d)
    surface.makeImageSnapshot().save(str(path),skia.kPNG)


def write_overrides(entries):
    if entries:
        output=ASSETS/'aortic-stenosis-overrides.json'
        pending=output.with_suffix('.partial.json')
        pending.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
        pending.replace(output)


def thumbnail():
    surface=skia.Surface(W,H)
    c=surface.getCanvas()
    clinical_backdrop(c)
    draw_valve_face(c,931,381,277,opening=1.,calcium=.93)
    rect(c,0,0,624,H,grad(0,0,624,0,['#102d2a','#1b433a']))
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(62,52,72,72),SAMPLE)
    label(c,'Elysian Biomedical LLP',154,100,35,'#d5ebdc')
    label(c,'Aortic valve',56,299,91,WHITE,face=HEADING)
    label(c,'narrowing',56,424,105,GOLD,face=HEADING)
    label(c,'Cardiology Education Series',58,639,36,'#cee8d9')
    surface.makeImageSnapshot().save(str(FOLDER/'thumbnail.jpg'),skia.kJPEG,95)


def build(only=(),*,stills=False,replace=False):
    ASSETS.mkdir(exist_ok=True)
    rows=json.loads((FOLDER/'timeline.json').read_text(encoding='utf-8-sig'))['scenes']
    entries={}
    for row in rows:
        target=ASSETS/f"{row['id']}-aortic-stenosis.mp4"
        if target.is_file():
            entries[row['id']]=picture_entry(target,row['end_frame']-row['start_frame'])
    for row in rows:
        ident=row['id']
        if only and ident not in only:
            continue
        frames=row['end_frame']-row['start_frame']
        d=frames/FPS
        draw=SCENES[ident]
        target=ASSETS/f'{ident}-aortic-stenosis.mp4'
        still(draw,d*.66,d,target.with_suffix('.png'))
        if stills or target.is_file() and not replace:
            continue
        def render(c,frame):
            if frame and frame%150==0:
                print(f'{ident}: drawing frame {frame}/{frames}',flush=True)
            draw(c,frame/FPS,d)
        pending=target.with_suffix('.partial.mp4')
        encode_scene(pending,frames,render,preset='veryfast',threads=2)
        pending.replace(target)
        entries[ident]=picture_entry(target,frames)
        write_overrides(entries)
        print(f'{ident}: {frames} frames',flush=True)
    write_overrides(entries)
    thumbnail()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('scenes',nargs='*',metavar='SCENE')
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    if set(args.scenes)-set(SCENES):
        parser.error('Use scene IDs P01 through P08.')
    build(args.scenes,stills=args.stills,replace=args.replace)
