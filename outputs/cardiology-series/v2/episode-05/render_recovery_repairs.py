"""Rebuild the five revised picture sequences for angiogram recovery."""

import argparse
from functools import lru_cache
import json
from math import cos, pi, sin
from pathlib import Path

import skia

from tools.elysian_video import access, angiogram
from tools.elysian_video.__main__ import FPS, HEIGHT, WIDTH
from tools.elysian_video.encode import encode_scene


HERE = Path(__file__).resolve().parent
VISUALS = HERE/'visuals'
DARK, GREEN, LIGHT = '#133b34', '#004b3d', '#f1fbf2'
INK, MUTED = '#263f3a', '#4c7065'
solid, gradient, line, polygon = access.solid, access.grad, access.line, access.path
curve = angiogram.art.curve


def ease(p,a,b):
    return access.smooth((p-a)/(b-a))


def box(x,y,w,h):
    return skia.Rect.MakeXYWH(x,y,w,h)


def rect(c,x,y,w,h,r,tone):
    paint=solid(tone) if isinstance(tone,str) else tone
    c.drawRoundRect(box(x,y,w,h),r,r,paint)


def oval(c,x,y,rx,ry,tone,alpha=255):
    paint=solid(tone,alpha) if isinstance(tone,str) else tone
    c.drawOval(box(x-rx,y-ry,rx*2,ry*2),paint)


def text(c,label,x,y,size=30,tone=GREEN,*,heading=False):
    font=skia.Font(access.HEADING if heading else access.BOLD,size)
    font.setEdging(skia.Font.kAntiAlias)
    if x<0 or x+font.measureText(label)>1276:
        raise ValueError(f'Text outside the picture: {label}')
    c.drawString(label,x,y,font,solid(tone))


def header(c,label,*,dark=False):
    color=LIGHT if dark else GREEN
    c.drawImageRect(access.LOGO,box(54,28,49,49),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(c,'Elysian Biomedical LLP',118,61,27,color)
    text(c,label,53,136,48,color,heading=True)


def tag(c,label,x=55,y=663,*,dark=False):
    width=skia.Font(access.BOLD,30).measureText(label)
    rect(c,x-11,y-35,width+22,48,10,solid(DARK,244) if dark else solid(LIGHT,247))
    text(c,label,x,y,30,LIGHT if dark else GREEN)


def snap(draw):
    surface=skia.Surface(WIDTH,HEIGHT)
    canvas=surface.getCanvas()
    canvas.scale(2,2)
    draw(canvas)
    return surface.makeImageSnapshot()


def image(c,plate,*,zoom=1,x=640,y=399):
    c.save()
    if zoom!=1:
        c.translate(x*(1-zoom),y*(1-zoom))
        c.scale(zoom,zoom)
    sampling=skia.FilterMode.kLinear if zoom!=1 else skia.FilterMode.kNearest
    c.drawImageRect(plate,box(0,0,1280,720),skia.SamplingOptions(sampling))
    c.restore()


@lru_cache(maxsize=2)
def field(dark=False):
    colors=['#102d2b','#225548','#133730'] if dark else ['#f9fcf3','#d9ebe1','#a3c9bc']
    return snap(lambda c:c.drawRect(box(0,0,1280,720),gradient(67,0,1149,720,colors)))


@lru_cache(maxsize=1)
def wrist_cutaway():
    def draw(c):
        image(c,field())
        access.vessel(c)
    return snap(draw)


def flowing(c,t):
    for i in range(42):
        x=(i*79-t*(65+i%6*8))%1350-26
        y=access.center(x)+i*37%34-16
        oval(c,x,y,9+i%6*1.2,2.8+i%4*.55,'#ea9389',109+i%4*17)


@lru_cache(maxsize=2)
def arm_plate(worsening=False):
    def draw(c):
        image(c,field())
        rect(c,-90,302,1430,282,123,gradient(140,288,1236,602,['#e8c09f','#c99483','#9a6264']))
        rect(c,-87,289,438,309,68,gradient(26,288,380,604,['#a9d6c3','#6ca998','#36796d']))
        for i in range(6):
            x=50+i*42
            line(c,[(x,330),(x-6,542)],'#9acdbd',3,98)
        oval(c,635,430,115 if worsening else 61,52 if worsening else 28,
             '#c36573' if worsening else '#986d8b',86 if worsening else 63)
        rect(c,554,329,169,193,33,gradient(549,325,746,529,['#e4eadb','#b4c9b9','#82ac9d']))
        rect(c,587,350,103,105,21,gradient(583,350,689,463,['#f4f6e7','#cfdbcc','#afc9ba']))
        line(c,[(575,486),(695,486)],'#edf5e5',4,211)
    return snap(draw)


def gloved_check(c,q):
    x,y=819-93*q,286+61*q
    fingers=curve((x+99,y-78),((x+37,y-59),(x+20,y-49),(x+2,y-34)),
                  ((x-18,y-20),(x-62,y-12),(x-83,y+1)),
                  ((x-103,y+17),(x-103,y+34),(x-75,y+35)),
                  ((x-16,y+32),(x+25,y+12),(x+45,y+2)),
                  ((x+67,y-7),(x+78,y+17),(x+107,y-8)),
                  ((x+128,y-21),(x+146,y-51),(x+164,y-62)))
    c.drawPath(polygon(fingers,True),gradient(x-89,y+10,x+162,y-60,['#80bdaa','#4b9a88','#347767']))


def paper(c,q,*,mode='result',x=850):
    y=390+54*(1-q)
    c.save()
    c.translate(x,y)
    c.rotate(-9+8*q)
    c.scale(.89+.13*q,.89+.13*q)
    oval(c,19,179,171,37,'#316a5e',44)
    rect(c,-156,-184,312,358,22,gradient(-169,-183,157,177,['#eaffec','#c4ded2','#83b1a1']))
    rect(c,-132,-162,264,307,13,'#f6fbef')
    rect(c,-74,-205,148,66,14,gradient(-73,-200,80,-138,['#a5d0b9','#63a88f','#3b7e71']))
    if mode=='result':
        path=curve((-94,-53),((-35,-76),(-10,-51),(19,-12)),((44,24),(58,62),(93,87)))
        line(c,path,'#569986',12)
        line(c,curve((9,-23),((13,-5),(-41,18),(-83,23))),'#62a895',6.5)
    else:
        for row in range(3):
            yy=-83+72*row
            line(c,[(-47,yy),(93,yy)],'#92ad9e',4)
            if q>.08+.19*row:
                line(c,[(-97,yy),(-85,yy+12),(-65,yy-11)],'#378b73',6)
    c.restore()


@lru_cache(maxsize=2)
def ward_plate(longer=False):
    def draw(c):
        image(c,field())
        for x in (0,436,875):
            rect(c,x,168,431,361,0,gradient(x,178,x+431,531,['#dcefe4','#badbcf','#8fb7a8']))
            line(c,[(x+5,171),(x+5,525)],'#f5faf0',4)
        rect(c,180,459,850,54,22,'#aec5b8')
        rect(c,232,510,739,93,20,'#67978a')
        rect(c,239,375,225,77,42,'#e6eee3')
        oval(c,393,407,59,49,'#7fa79a')
        body=curve((435,394),((509,365),(624,386),(690,411)),((774,416),(903,401),(1036,422)),
                   ((1110,432),(1094,484),(1040,489)),((859,483),(598,490),(436,459)))
        c.drawPath(polygon(body,True),gradient(434,377,1041,493,['#b6d7c7','#77aa9a','#448777']))
        for x in range(535,1041,92):
            line(c,[(x,422),(x-9,469)],'#b9dbcb',3,139)
        if longer:
            rect(c,829,201,264,156,15,'#28574d')
            rect(c,840,212,242,135,9,'#497a6d')
            rect(c,950,357,27,74,7,'#628e80')
        else:
            oval(c,952,266,92,86,'#315f53')
            oval(c,952,266,77,72,'#c8decd')
            for i in range(4):
                a=pi*i/2
                oval(c,952+65*cos(a),266+62*sin(a),4,4,'#6a9c87')
    return snap(draw)


def open_scene(c,p,t):
    if p<.41:
        image(c,wrist_cutaway())
        flowing(c,t)
        tip=631-823*ease(p,.25,.405)
        catheter=1040-1215*ease(p,.008,.23)
        access.sheath(c,tip)
        access.tube(c,catheter-1360,catheter,8.6,access.CATHETER,taper=11)
        if p>.29:
            press=ease(p,.29,.406)
            rect(c,293,247+25*press,74,38,8,solid('#3d8c78',round(220*press)))
            oval(c,330,293+14*press,29,12,'#a4cdb9',round(227*press))
        if p>.33:
            header(c,'After your angiogram')
    elif p<.70:
        q=ease(p,.41,.70)
        image(c,arm_plate(),zoom=1+.10*q,x=635,y=420)
        gloved_check(c,q)
        header(c,'After your angiogram')
        tag(c,'The team checks the access site')
    else:
        q=ease(p,.70,1)
        image(c,field())
        paper(c,q)
        header(c,'After your angiogram')
        text(c,'The result and next steps',55,359,43,GREEN,heading=True)
        tag(c,'Ask about your follow-up plan')


def discharge(c,p,t):
    if p<.22:
        q=ease(p,0,.22)
        scale=1+.12*q
        image(c,ward_plate(),zoom=scale,x=805,y=404)
        a=-pi/2+.78*q
        c.save()
        c.translate(805*(1-scale),404*(1-scale))
        c.scale(scale,scale)
        line(c,[(952,266),(952+51*cos(a),266+51*sin(a))],'#225e52',7)
        line(c,[(952,266),(985,279)],'#315c50',5)
        oval(c,952,266,7,7,'#225e52')
        c.restore()
        header(c,'Before leaving the hospital')
        tag(c,'Some people leave after observation')
    elif p<.67:
        q=ease(p,.22,.67)
        scale=1+.19*q
        image(c,ward_plate(True),zoom=scale,x=960,y=295)
        path=curve((859,286),((879,286),(905,290),(918,286)),((929,281),(933,250),(939,258)),
                   ((947,287),(953,308),(965,286)),((986,286),(1024,287),(1064,286)))
        c.save()
        c.translate(960*(1-scale),295*(1-scale))
        c.scale(scale,scale)
        line(c,angiogram.art.trace(path,.12+.88*((t*.6)%1)),'#d8f7db',5)
        c.restore()
        header(c,'Before leaving the hospital')
        tag(c,'Some need longer monitoring')
    else:
        q=ease(p,.67,1)
        image(c,field())
        paper(c,q,mode='written')
        header(c,'Ask for written instructions')
        text(c,'Who should I contact?',55,340,42,GREEN,heading=True)
        text(c,'Ask about the journey home',55,409,31,MUTED)


def watch_site(c,p,t):
    if p<.18:
        q=ease(p,0,.18)
        image(c,arm_plate(),zoom=1+.12*q,x=630,y=436)
        header(c,'What to watch at the access site')
        tag(c,'A small bruise or mild soreness can occur')
    elif p<.72:
        q=ease(p,.18,.72)
        image(c,arm_plate(True),zoom=1+.25*q,x=633,y=436)
        header(c,'Contact your care team promptly')
        tag(c,'Increasing pain or swelling' if p<.45 else 'Redness, drainage or fever')
    else:
        q=ease(p,.72,1)
        image(c,field(True))
        x,y=891,417
        size=1+.17*q
        rect(c,x-112*size,y-204*size,224*size,399*size,40,
             gradient(768,199,1003,616,['#b4decb','#76a997','#488577']))
        rect(c,x-89*size,y-172*size,178*size,315*size,25,'#315e54')
        oval(c,x,y-2,34*size,34*size,'#b6ddc9')
        line(c,[(x-17,y-4),(x-6,y+8),(x+22,y-20)],'#347662',7)
        header(c,'Get advice if the clinic is closed',dark=True)
        tag(c,'Ask your care team how to contact them',dark=True)


def recap(c,p,t):
    if p<.68:
        boundaries=(0,.18,.35,.49,.68)
        names=('Three things to get in writing','What did the angiogram show?',
               'What is the recovery plan?','Who should I contact?')
        for index,(start,end) in enumerate(zip(boundaries,boundaries[1:])):
            if p<end:
                q=ease(p,start,end)
                break
        image(c,field())
        paper(c,q,mode='result' if index==1 else 'written')
        header(c,'Before you go')
        text(c,names[index],54,375,43,GREEN,heading=True)
    else:
        q=ease(p,.68,1)
        image(c,field(True))
        paper(c,q,mode='result',x=312-70*(1-q))
        paper(c,q,mode='written',x=939+70*(1-q))
        header(c,'Your plan depends on your care',dark=True)
        tag(c,'Diagnostic test alone',148,651,dark=True)
        tag(c,'Test and treatment',814,651,dark=True)


@lru_cache(maxsize=1)
def sources_plate():
    def draw(c):
        image(c,field(True))
        header(c,'Cardiology Education Series',dark=True)
        text(c,'Clinical sources',55,243,37,LIGHT)
        text(c,'NHS · SCAI · American Heart Association · ESC',55,296,29,'#cbe8d8')
        text(c,'Original medical illustration · Synthetic English narration',55,349,27,'#cbe8d8')
        text(c,'Next episode',55,462,33,LIGHT)
        text(c,'Coronary angioplasty and stent placement',55,522,39,'#c6e6d4',heading=True)
    return snap(draw)


def credits(c,p,t):
    image(c,sources_plate())
    line(c,[(55,562),(55+613*ease(p,.03,.94),562)],'#82c9b0',3)


REPAIRS={'P01':open_scene,'P05':discharge,'P07':watch_site,'P10':recap,'P11':credits}


def thumbnail():
    surface=skia.Surface(1280,720)
    c=surface.getCanvas()
    image(c,field())
    oval(c,903,576,416,93,'#366e61',42)
    palm=curve((1268,378),((1129,356),(1029,390),(927,414)),
               ((864,427),(800,431),(748,426)),((725,406),(716,365),(689,348)),
               ((675,334),(657,338),(657,355)),((657,376),(671,403),(675,427)),
               ((630,419),(577,412),(534,414)),((511,415),(509,439),(529,447)),
               ((555,457),(604,455),(626,461)),((589,461),(549,459),(512,466)),
               ((490,470),(490,491),(510,497)),((537,502),(583,492),(625,499)),
               ((596,504),(565,506),(537,516)),((518,523),(524,545),(543,546)),
               ((574,549),(612,534),(652,534)),((628,548),(608,555),(589,567)),
               ((572,578),(580,595),(598,593)),((630,590),(676,565),(710,558)),
               ((749,559),(783,577),(825,570)),((906,550),(971,541),(1033,559)),
               ((1100,577),(1181,599),(1268,590)),((1292,563),(1290,417),(1268,378)))
    skin=polygon(palm,True)
    c.drawPath(skin,gradient(641,356,896,601,['#f4d1a9','#d49a7c','#9d6260']))
    c.save()
    c.clipPath(skin,doAntiAlias=True)
    oval(c,805,459,221,79,'#f7c8a2',42)
    oval(c,1125,413,230,54,'#fff0cf',27)
    c.restore()
    for pts in (curve((681,441),((719,463),(728,498),(702,532))),
                curve((664,469),((695,484),(722,483),(756,473))),
                curve((673,497),((712,518),(758,515),(790,495)))):
        line(c,pts,'#a47162',2.8,113)
    c.save()
    c.translate(911,486)
    c.rotate(-12)
    rect(c,-52,-96,113,199,39,gradient(-53,-99,60,103,['#f4f6e5','#bed2c3','#799f91']))
    rect(c,-65,-65,136,107,30,gradient(-68,-70,67,44,['#cdeee2','#7cc4b4','#518d86']))
    rect(c,-45,-48,94,76,24,gradient(-46,-49,50,30,['#eaf5e1','#bfd8c8','#7aada1']))
    line(c,[(-32,-32),(36,-32)],'#f6faed',4,192)
    c.restore()
    c.drawImageRect(access.LOGO,box(56,25,52,52),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(c,'Elysian Biomedical LLP',126,61,28,GREEN)
    text(c,'After your',54,195,88,GREEN,heading=True)
    text(c,'angiogram',54,287,88,GREEN,heading=True)
    text(c,'Wrist and groin recovery',57,371,33,MUTED)
    surface.makeImageSnapshot().save(str(HERE/'thumbnail.png'))


def render(ids):
    timeline=json.loads((HERE/'timeline.json').read_text(encoding='utf-8-sig'))
    sizes={row['id']:row['end_frame']-row['start_frame'] for row in timeline['scenes']}
    for ident in ids:
        frames=sizes[ident]
        destination=VISUALS/f'{ident}-recovery-film.mp4'
        temporary=VISUALS/f'{ident}-recovery-film.repair.mp4'
        scene=REPAIRS[ident]
        encode_scene(temporary,frames,
                     lambda c,i:scene(c,i/max(1,frames-1),i/FPS),
                     preset='fast',threads=2)
        temporary.replace(destination)
        print(f'{ident} repaired · {frames} frames',flush=True)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('scenes',nargs='*',choices=tuple(REPAIRS))
    cli.add_argument('--thumbnail',action='store_true')
    args=cli.parse_args()
    if args.thumbnail:
        thumbnail()
    else:
        render(args.scenes or REPAIRS)
