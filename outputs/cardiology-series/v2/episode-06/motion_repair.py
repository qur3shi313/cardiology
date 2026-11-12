"""Narration-timed native pictures for v2 angioplasty and drug-eluting stents."""
from bisect import bisect_right
from functools import lru_cache
import importlib.util
import json
from math import cos, pi, sin
import os
from random import Random
import subprocess
import sys

import av
import skia

from tools.elysian_video import access as ink, angiogram as xray, stent as art
from tools.elysian_video.__main__ import FPS, HEIGHT, ROOT, SERIES, WIDTH
from tools.elysian_video.encode import encode_scene

sys.path.insert(0, str(SERIES / 'episode-02' / 'visuals'))
import comparison_editorial as care
import render_comparison as anatomy


GREEN = '#123d35'
GOLD = '#ffe0a6'
LIGHT = '#f5fdf2'
TEAL = '#246e5d'
V = skia.Rect.MakeWH(1280, 720)
MID = art.LESION
OFF = -280
DISTAL = 1126
SAMPLE = skia.SamplingOptions(skia.FilterMode.kLinear)
NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest)
block = xray.block
dot = xray.dot
line = ink.line
solid = ink.solid
e = art.ease


def frame(c, title, detail='', *, dark=False, sim=False):
    brand, text, accent = ('#132d29', LIGHT, '#b3decb') if dark else ('#eaf3e9', GREEN, TEAL)
    ink.rect(c, 0, 0, 1280, 152, solid(brand))
    c.drawImageRect(ink.LOGO, skia.Rect.MakeXYWH(55, 23, 52, 52), SAMPLE)
    ink.text(c, 'Elysian Biomedical LLP', 125, 58, 27, accent)
    if sim:
        ink.text(c, 'SIMULATED CORONARY X-RAY', 848, 58, 25, accent)
    ink.text(c, title, 55, 133, 48, text, ink.HEADING)
    ink.rect(c, 0, 640, 1280, 80, solid(brand))
    if detail:
        ink.text(c, detail, 55, 690, 30, accent)


@lru_cache(maxsize=2)
def field_plate(dark):
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    tones = ['#173d36', '#102925'] if dark else ['#eff7ec', '#bed9cc']
    c.drawRect(V, art.gradient(0, 115, 1250, 655, tones))
    return surface.makeImageSnapshot()


def field(c, dark=False):
    c.drawImageRect(field_plate(dark),V,NEAREST)


def viewport(c, zoom=1, x=640, y=394):
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 152, 1280, 640))
    c.translate(x, y)
    c.scale(zoom, zoom)
    c.translate(-x, -y)


@lru_cache(maxsize=1)
def vessel_wall():
    surface = skia.Surface(WIDTH, HEIGHT)
    c = surface.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(2, 2)
    outer_top=[(x,art.center(x)-211-11*cos(x/150)) for x in art.XS]
    outer_bottom=[(x,art.center(x)+218+10*sin(x/170)) for x in art.XS]
    rim_top=[(x,art.center(x)-193-9*cos(x/150)) for x in art.XS]
    rim_bottom=[(x,art.center(x)+198+9*sin(x/170)) for x in art.XS]
    c.drawPath(art.enclosed(outer_top,outer_bottom),art.gradient(0,170,0,617,
               ['#a34f58','#653043','#541f34'],[0,.52,1]))
    c.drawPath(art.enclosed(rim_top,rim_bottom),art.gradient(0,190,0,590,
               ['#e58f85','#b44d55','#773247','#d76d6d','#8d3b50'],[0,.29,.50,.83,1]))
    line(c,outer_top,'#f6aba1',4,193)
    line(c,outer_bottom,'#50243a',3,210)
    line(c,[(x,art.center(x)-178-9*cos(x/150)) for x in art.XS],'#fcb5a3',3,92)
    line(c,[(x,art.center(x)+175+9*sin(x/170)) for x in art.XS],'#f9b29b',4,75)
    return surface.makeImageSnapshot()


ARTERIES=[(x,art.center(x),art.plaque(x)) for x in art.XS]
PLAQUE=[(x,art.center(x),art.plaque(x)) for x in range(460,846,3)]
PLAQUE_GRAIN={side:[(x:=rng.uniform(487,814),art.center(x),art.plaque(x),rng.uniform(.2,.9),
                    rng.uniform(.4,1.4),rng.randrange(32,94)) for _ in range(95)]
              for side in (-1,1) for rng in [Random(10+side)]}


def vessel_lumen(c, expansion, clean):
    c.drawImageRect(vessel_wall(),V,NEAREST)
    constriction=0 if clean else 1-expansion
    top=[(x,y-116+84*q*constriction) for x,y,q in ARTERIES]
    bottom=[(x,y+116-40*q*constriction) for x,y,q in ARTERIES]
    lumen=art.enclosed(top,bottom)
    c.drawPath(lumen,art.gradient(0,270,0,521,['#43152b','#7d283e','#8a3044','#43182f'],[0,.30,.58,1]))
    line(c,top,'#f4aa99',3.2,208)
    line(c,bottom,'#f18e83',3.2,180)
    if not clean:
        for side,narrow,depth in ((-1,84,58),(1,40,38)):
            edge=[(x,y+side*(116-narrow*q*constriction)) for x,y,q in PLAQUE]
            away=[(x,y+side*(116+(depth-narrow*constriction)*q)) for x,y,q in PLAQUE]
            c.drawPath(art.enclosed(edge,away),art.gradient(475,262,805,502,
                       ['#c58a63','#f0c998','#b47a60'],[0,.45,1]))
            line(c,edge,'#ffe0aa',2.2,210)
            for x,y,q,p,r,alpha in PLAQUE_GRAIN[side]:
                dot(c,x,y+side*(116+(depth*p-narrow*constriction)*q),r,'#825345',alpha)
    return lumen


@lru_cache(maxsize=3)
def stable_vessel(expansion,clean):
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(2,2)
    lumen=vessel_lumen(c,expansion,clean)
    return surface.makeImageSnapshot(),lumen


def blood(c, t, expansion, block_amount=0):
    """Red-cell silhouettes follow the lumen and attenuate behind an obstruction."""
    for i in range(49):
        velocity = 81 + (i % 7) * 15
        x = (i * 263 + t * velocity) % 1500 - 100
        if x<0 or x>1280:
            continue
        if block_amount and x > MID - 75:
            fade = 1 - block_amount * e(x, MID - 75, MID + 60)
        else:
            fade = 1
        lane = ((i * 47) % 170 - 84) / 100
        side = 1 if lane > 0 else -1
        y = art.center(x) + lane * art.lumen_radius(x, side, expansion)
        width = 7 + i % 6
        height = 2.5 + i % 3
        rect = skia.Rect.MakeLTRB(x-width, y-height, x+width, y+height)
        c.drawOval(rect, solid('#ffab9a', round(fade * (88 + (i % 4) * 18))))
        c.drawOval(skia.Rect.MakeLTRB(x-width*.47, y-height*.48, x+width*.47, y+height*.48),
                   solid('#9f4754', round(141 * fade)))


def guide(c, extent=1):
    x1 = -95 + extent * 319
    if x1 <= -89:
        return
    points = [(x, art.center(x)) for x in range(-90, int(x1), 5)] + [(x1, art.center(x1))]
    line(c, points, '#29464a', 26)
    line(c, points, '#87bcaf', 17)
    line(c, [(x, y-6) for x, y in points], '#d1e6d3', 3)


def coating(c, t, strength, *, radius=116, balloon=False):
    """A local wall tint depicts transfer, with a fixed footprint around the device."""
    for side in (-1, 1):
        xa, xb = MID-130, MID+130
        for i in range(17):
            x = xa + (xb-xa) * i/16
            phase = (t*.48+i*.089+(side == 1)*.24) % 1
            rr = radius + (4 if balloon else 8) + 27 * phase
            y = art.center(x) + side*rr
            c.drawOval(skia.Rect.MakeLTRB(x-14,y-4,x+14,y+4),
                       solid('#ffdf90', round(strength * 155 * sin(pi*phase))))
    for side in (-1, 1):
        base = [(x, art.center(x)+side*(radius+3)) for x in range(MID-132,MID+134,5)]
        line(c, base, '#f6d48d', 4.5, round(180*strength))


def thrombus(c, amount):
    """An acute clot grows into the channel from the illustrated plaque."""
    cx = MID-6
    y = art.center(cx)-art.lumen_radius(cx,-1,0)
    r = 55*amount
    for x, dy, w, h in ((-25, 15, .66, .53), (18, 28, .97, .78), (47, 12, .51, .52)):
        c.drawOval(skia.Rect.MakeXYWH(cx+x-r*w, y+dy*.47-r*h*.35, 2*r*w, 2*r*h),
                   art.gradient(cx,y,cx,y+76,['#f1a89a','#bc5c64','#6a293d']))


def section(c, t, *, expansion=1, mesh=OFF, radius=116, balloon=OFF, balloon_radius=12,
            wire=-90, catheter=0, medicine=0, dcb=False, clean=False, clot=0, zoom=1, focus=640):
    field(c)
    viewport(c,zoom*1.055,focus)
    plateau=round(expansion,3)
    if plateau in (0,.29,.36,.49,.51,.58,1):
        image,_=stable_vessel(plateau,clean)
        c.drawImageRect(image,V,NEAREST)
    else:
        image,_=stable_vessel(0,False)
        c.drawImageRect(image,V,NEAREST)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(421,246,891,549))
        vessel_lumen(c,expansion,clean)
        c.restore()
    obstruct = max(e(balloon_radius,39,108),.87*clot)
    blood(c,t,expansion,obstruct)
    if clot:
        thrombus(c,clot)
    if mesh + art.MESH_HALF > art.X0:
        art.stent(c,mesh,radius,False)
    guide(c,catheter)
    if wire > art.X0+1:
        art.wire(c,wire)
    if balloon + art.BALLOON_HALF > art.X0:
        art.balloon(c,balloon,balloon_radius)
        if dcb:
            for k in range(29):
                x = balloon-142 + k*10
                for side in (-1,1):
                    dot(c,x,art.center(x)+side*balloon_radius,2.9,'#ffe0a0',216)
    if mesh + art.MESH_HALF > art.X0:
        art.stent(c,mesh,radius,True)
    if medicine:
        coating(c,t,medicine,radius=balloon_radius if dcb else radius,balloon=dcb)
    c.restore()


@lru_cache(maxsize=1)
def xray_viewport():
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    viewport(c,1.16)
    c.drawImageRect(xray.radiograph_plate(),V,SAMPLE)
    c.restore()
    return surface.makeImageSnapshot()


def coronary_xray(c, t, title, detail, *, narrowed=True, length=7.8, angle=-13, locate=True):
    c.drawImageRect(xray_viewport(),V,NEAREST)
    viewport(c,1.16)
    fill = min(1, max(0,(t+.24) / max(1.6, length*.43)))
    alpha = round(250-129*e(t,length*.63,length))
    x,y = xray.contrast_paths(c,'left',fill,alpha,angle,narrowed)
    if locate and fill > .59:
        q = e(t,length*.37,length*.64)
        r = 33-10*q
        ring = solid(GOLD,round(q*247)); ring.setStyle(skia.Paint.kStroke_Style); ring.setStrokeWidth(3.8)
        c.drawCircle(x,y,r,ring)
        line(c,[(x+r,y-10),(x+101,y-62),(x+228,y-62)],GOLD,2.8,round(q*240))
        ink.text(c,'Narrowing' if narrowed else 'Treated segment',x+107,y-73,28,GOLD,alpha=round(q*255))
    c.restore()
    frame(c,title,detail,dark=True,sim=True)


def focused_image(c,t,p):
    """Conceptual intravascular imaging sweep and an expanded cross-section."""
    field(c, True)
    x0,x1,y = 78, 646, 388
    block(c,x0,y-111,x1-x0,222,74,art.gradient(x0,y-111,x1,y+111,['#cd7e7c','#763d51','#c57877']))
    block(c,x0+4,y-76,x1-x0-8,152,66,solid('#481d35'))
    for i in range(12):
        x = 158+33*i
        line(c,[(x,y-70),(x+12,y-46),(x-2,y-22),(x+12,y),(x-2,y+22),(x+12,y+46),(x,y+70)],'#c9d8ca',3.6)
    sensor = 191 + 346*e(p,0,1)
    line(c,[(x0+7,y),(sensor,y)],'#99c6bb',12)
    block(c,sensor-12,y-12,28,24,7,solid('#f4d396'))
    line(c,[(sensor,y-95),(sensor,y+95)],GOLD,3.8,190)
    line(c,[(sensor,y-103),(sensor,230),(747,230)],'#a4cebb',2.2,179)
    cx,cy=945,393
    for r,tone in ((182,'#623548'),(165,'#965765'),(142,'#d39389'),(112,'#4d313a'),(100,'#192b2a')):
        dot(c,cx,cy,r,tone)
    for i in range(18):
        a=i*2*pi/18
        dot(c,cx+109*cos(a),cy+109*sin(a),5.9,'#e3ebd7')
    sweep=pi*t*.9
    fan=skia.Path(); fan.moveTo(cx,cy)
    for i in range(19):
        theta=sweep+i*.038
        fan.lineTo(cx+96*cos(theta),cy+96*sin(theta))
    fan.close()
    c.drawPath(fan,solid('#9fe7cf',91))
    dot(c,cx,cy,10,'#b0daca')
    frame(c,'Imaging from inside the artery','Selected cases: check how the mesh has opened',dark=True)


def callout(c,label,at,target,progress):
    if progress<=0:
        return
    x,y=at
    w=skia.Font(ink.BOLD,28).measureText(label)
    alpha=round(246*progress)
    tx,ty=target
    line(c,[(tx,ty),(x+10,y+24),(x+20,y+7)],'#ffe6b8',2.8,alpha)
    dot(c,tx,ty,4.8,'#ffe6b8',alpha)
    block(c,x,y-31,w+27,43,11,solid('#602d40',round(222*progress)))
    ink.text(c,label,x+13,y,28,'#fff0cb',alpha=alpha)


def step(t, marks, duration):
    i=bisect_right(marks,t)-1
    end=marks[i+1] if i+1<len(marks) else duration
    return i,min(1,max(0,(t-marks[i])/max(.01,end-marks[i])))


def route(c,t,duration):
    if t<11.1:
        field(c)
        choice=step(t,(0,5.1,8.25),11.1)[0]
        viewport(c,1.02+.06*e(t,0,11),663,392)
        routes=[]
        if choice:
            routes=[('wrist' if choice==1 else 'groin',e(t,5.10,8.25) if choice==1 else e(t,8.25,11.10))]
        anatomy.body(c,677,355,1.17,routes,t)
        c.restore()
        labels=('Percutaneous coronary intervention','One access option: wrist','Another access option: groin')
        frame(c,'Getting to the coronary opening',labels[choice])
        return
    p=(t-11.1)/(duration-11.1)
    c.drawImageRect(xray.root_plate(),V,SAMPLE)
    tip=xray.blend_point(xray.NEUTRAL,xray.LEFT,e(p,.02,.82))
    catheter=xray.root_trace(xray.instrument_path(tip))
    line(c,catheter,'#1c514d',21); line(c,catheter,'#76aba3',13); line(c,catheter,'#d2eee0',3)
    x,y=xray.root_coord(xray.LEFT)
    dot(c,x,y,5,'#e6ffe8')
    line(c,[(x,y),(962,y-61),(1198,y-61)],'#165849',3)
    ink.text(c,'Coronary opening',970,y-74,28,GREEN)
    frame(c,'The guide catheter reaches the opening','The tip rests at the coronary opening above the aortic valve')


def pci_device(c, ident, t, duration):
    """Motion boundaries follow complete Alexander clauses in captions.en.srt."""
    opts={'wire':DISTAL,'catheter':1}
    if ident=='P05':
        opts.update(expansion=0,wire=215+911*e(t,.9,11.7))
        title,detail='The guidewire crosses first','The wire tip stays beyond the narrowing'
    elif ident=='P06':
        stretch=e(t,11.4,17.9)
        opts.update(expansion=.49*stretch,balloon=OFF+(MID-OFF)*e(t,5.75,10.95),balloon_radius=12+75*stretch)
        title,detail='A separate balloon prepares the artery','The folded balloon travels over the guidewire'
        if t>=11.4:
            detail='Balloon inflation presses plaque toward the wall'
    elif ident=='P07':
        collapse=e(t,.2,2.2)
        opts.update(expansion=.49-.13*collapse,balloon=MID-(MID-OFF)*e(t,2.3,5.55),balloon_radius=87-75*collapse)
        title,detail='The first balloon comes out','The guidewire remains in place'
        if t>10.8:
            detail='In suitable cases the stent can go directly over the wire'
    elif ident=='P08':
        x=OFF+(MID-OFF)*e(t,1.5,15.8)
        opts.update(expansion=.36,balloon=x,mesh=x,radius=14)
        title,detail='The stent arrives on a folded balloon','The mounted mesh and balloon travel together over the wire'
    elif ident=='P09':
        inflate=e(t,.30,5.07)
        collapse=e(t,9.5,11.8)
        opts.update(expansion=.36+.64*inflate,balloon=MID-(MID-OFF)*e(t,11.8,14.48),
                    balloon_radius=12+104*inflate*(1-collapse),mesh=MID,radius=14+102*inflate)
        title,detail='The balloon opens the stent','The stent opens against the artery wall'
        if t>9.5:
            detail='The balloon deflates and comes out. The mesh stays.'
    else:
        opts.update(mesh=MID,wire=-90,catheter=0,medicine=e(t,.4,4.6),zoom=1+.12*e(t,6,duration))
        title,detail='A drug-eluting coating releases medicine','Medicine from the coating acts near the treated wall'
    section(c,t,**opts)
    if ident=='P05':
        callout(c,'Guidewire tip',(911,229),(1153,art.center(DISTAL)-12),e(t,11.72,12.35))
    elif ident=='P08':
        callout(c,'Mounted stent',(735,220),(746,art.center(746)-14),e(t,15.8,16.57))
    elif ident=='P09':
        callout(c,'Expanded stent',(777,220),(747,art.center(747)-120),e(t,14.6,15.30))
    frame(c,title,detail)


def coronary_choices(c,t):
    if t<10.62:
        coronary_xray(c,t,'From diagnosis to treatment','Contrast outlines the artery channel',length=10.62)
        return
    if t<16.7:
        section(c,t,expansion=0,zoom=1+.09*e(t,10.62,16.7))
        frame(c,'The team reviews the narrowing','Angioplasty may follow in the same session or be planned later')
        return
    field(c)
    choices=('Medicines','Angioplasty','Bypass surgery')
    for i,(label,icon) in enumerate(zip(choices,('medicine','pulse','heart'))):
        onset=(16.73,18.51,20.76)[i]
        reveal=e(t,onset,onset+1.70)
        if t<onset:
            continue
        x=237+i*400
        dot(c,x,372+37*(1-reveal),101+34*reveal,'#aed3c2',round(102+149*reveal))
        cy=372+37*(1-reveal)
        if icon=='medicine':
            block(c,x-35,cy-47,70,97,14,solid(TEAL))
            block(c,x-40,cy-56,80,20,6,solid('#407f71'))
            block(c,x-23,cy-10,46,34,6,solid('#cce9d6'))
            line(c,[(x-12,cy+7),(x+12,cy+7)],TEAL,3.2)
        elif icon=='pulse':
            line(c,[(x-65,cy),(x+65,cy)],TEAL,10)
            c.drawOval(skia.Rect.MakeLTRB(x-44,cy-25,x+44,cy+25),solid('#a8e1ce'))
            line(c,[(x-53,cy),(x+55,cy)],'#effced',3)
        else:
            care.pictogram(c,icon,x,cy,1.18+reveal*.16,TEAL)
            line(c,[(x+10,cy-44),(x+37,cy-14),(x+25,cy+28),(x+5,cy+39)],'#fde2aa',4)
        words=skia.Font(ink.BOLD,32).measureText(label)
        ink.text(c,label,x-words/2,560,32,GREEN)
    frame(c,'The team reviews the options','Treatment may follow in the same session or be planned later')


def remove_equipment(c,t,duration):
    if t<4.85:
        section(c,t,mesh=MID,wire=DISTAL-(DISTAL+90)*e(t,.25,2.24),catheter=1-e(t,2.45,4.77))
        frame(c,'The wire and catheter come out','The expanded stent stays in place')
    elif t<9.6:
        p=.34+.66*e(t,4.9,9.57)
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0,152,1280,640))
        ink.scene(c,'P35',p,t)
        c.restore()
        frame(c,'Pressure at the wrist','A compression band helps control bleeding')
    else:
        p=e(t,9.68,duration)
        field(c)
        anatomy.groin_surface(c,674,396,1.28+.10*p)
        anatomy.glove(c,804,497-65*p,1.02,-1)
        frame(c,'Closure at the groin','The team may use pressure or a closure device')


def monitor(c,t):
    block(c,797,204,395,209,23,solid('#2b5650'))
    block(c,815,227,359,151,12,solid('#143834'))
    for i in range(5):
        line(c,[(827,250+i*24),(1159,250+i*24)],'#78ad9c',1,94)
    points=[]
    for i in range(166):
        x=i*2
        u=(x+t*138)%111
        y=314-10*sin(u*.14)-39*max(0,1-abs(u-39)/6)+23*max(0,1-abs(u-49)/7)
        points.append((828+x,y))
    line(c,points,'#c5f0bf',3.9)
    ink.text(c,'Pulse monitoring',841,400,25,LIGHT)


def plan(c,t,p,entries,detail,title='Follow-up and medicines',check=True):
    field(c)
    block(c,807,157,431,373,26,art.gradient(807,157,1238,530,['#e3f0e6','#9cc7b8']))
    line(c,[(1025,172),(1025,505)],'#cee7db',6)
    line(c,[(819,331),(1226,331)],'#cee7db',6)
    care.patient(c,970,401,1.76,'staff_check',t)
    block(c,-2,555,1284,86,12,art.gradient(0,555,1238,640,['#9ac4b5','#61998e']))
    line(c,[(0,575),(1280,575)],'#d6e9db',3,190)
    x=34+65*p
    y=190-15*p
    block(c,x+14,y+17,661,438,28,solid('#456f65',136))
    block(c,x,y,661,438,28,art.gradient(x,y,x+661,y+438,['#fffdf0','#dbeadd']))
    block(c,x+212,y-12,237,44,12,solid('#65a194'))
    for i,name in enumerate(entries):
        yy=y+137+i*72
        q=e(p,-.10+i*.14,.29+i*.18)
        dot(c,x+63,yy-9,15,'#a2cbb5')
        if check:
            line(c,[(x+55,yy-8),(x+61,yy-2),(x+71,yy-16)],TEAL,3.6,round(255*q))
        ink.text(c,name,x+96,yy,30,GREEN)
    frame(c,title,detail)


def platelet_view(c,t,p,*,paired=False):
    field(c)
    viewport(c,1+.09*p)
    y=390
    block(c,53,y-167,1174,335,112,art.gradient(55,y-168,1160,y+168,['#cf827b','#8b4d60','#c57776']))
    block(c,66,y-106,1148,212,86,solid('#4c2239'))
    for i in range(34):
        velocity=98+i%4*17
        x=99+(i*233+t*velocity)%1074
        dy=((i*59)%148)-75
        if paired and i<12:
            target=(i%6)*16
            q=e(p,.03,.78)
            x=x*(1-q)+(801+target)*q
            dy=dy*(1-q)+(43+(i//6)*19)*q
        c.drawOval(skia.Rect.MakeLTRB(x-12,y+dy-5,x+12,y+dy+5),solid('#e6ac8f' if i%4 else '#e07878',204))
    c.restore()


def editorial(c,ident,t,duration):
    if ident=='P13':
        if t<9.93:
            field(c)
            p=e(t,0,9.9)
            care.patient(c,245+49*p,456,1.37,'flat',t)
            care.patient(c,547,346,1.02,'staff_check',t)
            monitor(c,t)
            detail='The team checks blood pressure, pulse and the access site'
            if t>=5.2:
                detail='Staff watch for complications at the access site'
            frame(c,'Recovery after angioplasty',detail)
        else:
            plan(c,t,e(t,9.93,duration),('Dressing and activity','Medicines','Follow-up'),
                 'Discharge timing depends on your situation','Your discharge plan')
    elif ident=='P14':
        if t<4.92:
            section(c,t,mesh=MID,zoom=1+.10*e(t,.3,4.92))
            frame(c,'Why antiplatelet medicines are used','Your team usually prescribes them after a stent')
        elif t<10.2:
            example=t<7.55
            platelet_view(c,t,e(t,4.92,7.55) if example else e(t,7.55,10.2),paired=example)
            frame(c,'Why antiplatelet medicines are used','Platelets can clump together and form a clot' if example
                  else 'Antiplatelet medicines make this less likely')
        else:
            plan(c,t,e(t,10.2,duration),('Take the medicines as prescribed','Ask before changing them'),
                 'Your cardiology team chooses the medicines and duration','Your antiplatelet plan')
    elif ident=='P15':
        if t<4.93:
            plan(c,t,e(t,0,4.93),('Dressing and activity',),'Follow your hospital’s instructions','Wound care and activity')
        elif t<14.44:
            j,p=step(t,(4.93,8.4,11.35),14.44)
            signs=(('chest',('Severe or persistent','chest pain')),('bleed',('Bleeding that','will not stop')),
                   ('pain',('Cold or numb hand or foot','on the accessed side')))
            icon,words=signs[j]
            if j==2:
                field(c,True)
                anatomy.wrist_surface(c,1.31,60+38*e(p,0,1),100,cool=True)
                for i,words_line in enumerate(words):
                    ink.text(c,words_line,688,359+i*52,36,LIGHT)
            else:
                care.advice(c,'Get emergency help',icon,words,t,p,emergency=True)
            frame(c,'Get emergency help','Call your local emergency number',dark=True)
        else:
            plan(c,t,e(t,14.44,duration),('Follow-up visit','Cardiac rehabilitation'),
                 'Discuss your recovery with your team','Aftercare and follow-up')
    elif ident=='P16':
        if t<3.5:
            section(c,t,mesh=MID,zoom=1+.09*e(t,0,3.5))
            frame(c,'What treatment changes','The stent supports one treated section')
        else:
            plan(c,t,e(t,3.5,duration),('What was treated','Which medicines to take','When to return to usual activities'),
                 'Coronary artery disease still needs ongoing care','What to ask at follow-up')
    else:
        sources(c,t,duration,6)


def sources(c,t,duration,episode):
    field(c,True)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(750,153,1280,640))
    c.translate(750-64*e(t,0,duration),159)
    c.scale(.67,.63)
    art.artery(c,1)
    blood(c,t,1)
    art.stent(c,MID,116,False); art.stent(c,MID,116,True)
    c.restore()
    names=('American Heart Association','NHS coronary angioplasty guidance','FDA-hosted coronary stent labeling')
    if episode==7:
        names=('NIH National Heart, Lung, and Blood Institute','American Heart Association','ACC/AHA/SCAI and FDA device information')
    for i,name in enumerate(names):
        yy=228+i*65
        dot(c,66,yy-8,5,'#9dd7bd')
        ink.text(c,name,90,yy,29,LIGHT)
    ink.text(c,'Original educational animation',56,479,29,LIGHT)
    ink.text(c,'Alexander narration via ElevenLabs',56,534,27,'#bedecf')
    ink.text(c,'Cardiology Education Series',56,585,25,'#bedecf')
    detail='Next: how drug-eluting stents work' if episode==6 else 'Next: how a drug-coated balloon works'
    frame(c,'Clinical sources and credits',detail,dark=True)


def angioplasty(c,ident,t,duration):
    if ident=='P01':
        if t<5.45:
            coronary_xray(c,t,'Where does the artery narrow?','A coronary angiogram shows the channel',length=5.45)
        elif t<10.28:
            widening=e(t,6.65,9.90)
            section(c,t,expansion=.58*widening,wire=DISTAL,balloon=162+(MID-162)*e(t,5.46,6.64),
                    balloon_radius=12+77*widening,catheter=1)
            frame(c,'Coronary angioplasty and stent placement','A balloon can help widen the narrowed passage')
        else:
            section(c,t,mesh=MID,zoom=1+.09*e(t,10.3,duration))
            frame(c,'Coronary angioplasty and stent placement','From the first X-ray images to treatment and recovery')
    elif ident=='P02':
        if t<5.15:
            section(c,t,clean=True)
            frame(c,'Why the artery narrows','Coronary arteries supply the heart muscle')
        elif t<10.69:
            section(c,t,expansion=0,zoom=1+.13*e(t,5.15,10.69))
            frame(c,'Why the artery narrows','Plaque in the artery wall can narrow the channel')
        else:
            section(c,t,expansion=0,clot=e(t,10.75,14.5),zoom=1.13)
            frame(c,'Why the artery narrows','A clot can suddenly reduce or block blood flow')
    elif ident=='P03':
        coronary_choices(c,t)
    elif ident=='P04':
        route(c,t,duration)
    elif ident in {'P05','P06','P07','P08','P09','P10'}:
        pci_device(c,ident,t,duration)
    elif ident=='P11':
        if t<12.18:
            coronary_xray(c,t,'Checking the treated segment','Contrast shows the treated channel and downstream branches',
                          narrowed=False,length=12.18)
        else:
            focused_image(c,t,(t-12.18)/(duration-12.18))
    elif ident=='P12':
        remove_equipment(c,t,duration)
    else:
        editorial(c,ident,t,duration)


def drug_eluting(c,ident,t,duration):
    if ident=='P01':
        x=MID-(MID-OFF)*e(t,0,1.82)
        section(c,t,mesh=MID,balloon=x,wire=DISTAL,medicine=.81*e(t,7.05,12.6),zoom=1+.08*e(t,3.0,7.0))
        frame(c,'What stays in the artery?' if t<4.5 else 'Drug-eluting stents',
              'The balloon comes out. The metal mesh stays.' if t<7.1 else 'The mesh supports the artery and the coating releases medicine')
    elif ident=='P02':
        section(c,t,mesh=MID,medicine=e(t,8.02,11.8),zoom=1+.15*e(t,4.0,13.2))
        detail='The metal scaffold helps hold open the treated section' if t<8 else 'The coating releases medicine near the treated wall'
        frame(c,'Two jobs for one device',detail)
    elif ident=='P03':
        x=108+(MID-108)*e(t,7.6,11.38)
        expand=e(t,11.48,13.55)
        collapse=e(t,13.77,15.35)
        balloon_x=x-(MID-OFF)*e(t,15.43,18.07)
        section(c,t,expansion=.29+.71*expand,mesh=x,radius=14+102*expand,balloon=balloon_x,
                balloon_radius=12+104*expand*(1-collapse),wire=DISTAL,catheter=1)
        detail='The mesh travels mounted on a folded balloon' if t<11.46 else 'The balloon expands the mesh against the wall'
        if t>=13.75:
            detail='The balloon deflates and is withdrawn. The mesh stays.'
        frame(c,'How the stent gets there',detail)
    elif ident=='P04':
        section(c,t,mesh=MID,medicine=.95,zoom=1+.18*e(t,3.7,14.2),focus=632)
        callout(c,'Medicine coating',(745,225),(743,art.center(743)-139),e(t,2.8,4.2)*(1-e(t,10,10.75)))
        detail='Medicine acts near the vessel wall' if t<10.0 else 'Stent designs and coatings differ'
        if t>=14.45:
            detail='The mesh continues to support the treated section'
        frame(c,'Medicine releases near the wall',detail)
    elif ident=='P05':
        x=142+(MID-142)*e(t,1.40,6.44)-(MID-OFF)*e(t,13.00,14.52)
        inflate=e(t,6.48,8.36)
        contact=inflate*(1-e(t,11.9,12.95))
        section(c,t,expansion=.51*inflate,balloon=x,balloon_radius=12+83*contact,
                wire=DISTAL,dcb=True,medicine=.97*contact)
        detail='Medicine is carried on the balloon’s surface' if t<6.5 else 'Some medicine transfers during balloon contact'
        if t>=12.55:
            detail='The balloon leaves no new metal scaffold in a balloon-only treatment'
        frame(c,'A drug-coated balloon comes out',detail)
    elif ident=='P06':
        if t<8.5:
            coronary_xray(c,t,'Checking the treated segment','The team checks contrast flow beyond the stent',narrowed=False,length=8.5)
        else:
            focused_image(c,t,(t-8.5)/(duration-8.5))
    elif ident=='P07':
        if t<11.40:
            section(c,t,mesh=MID,medicine=e(t,.24,4.0),zoom=1+.11*e(t,4.0,11.4))
            frame(c,'Two different jobs for medicine','The coating acts near the stent')
        elif t<15.55:
            platelet_view(c,t,e(t,11.4,15.55))
            frame(c,'Antiplatelet medicines','They help lower the chance of a clot')
        else:
            plan(c,t,e(t,15.55,duration),('Which medicines to take','How long to take them'),
                 'Your care team chooses your medicine plan','Your antiplatelet plan')
    elif ident=='P08':
        if t<7.85:
            section(c,t,mesh=MID,zoom=1+.13*e(t,0,7.85))
            frame(c,'Follow-up after a stent','The stent supports one treated section')
        elif t<17.46:
            plan(c,t,e(t,7.85,17.46),('What was treated','Your medicine plan','What to do if symptoms return'),
                 'Coronary artery disease needs ongoing care','Follow-up after a stent')
        else:
            x=149+(MID-149)*e(t,17.47,duration)
            section(c,t,expansion=0,balloon=x,wire=DISTAL,dcb=True)
            frame(c,'Next: drug-coated balloons','How a balloon carries medicine')
    else:
        sources(c,t,duration,7)


def draw(c,episode,ident,number,count):
    scene = angioplasty if episode==6 else drug_eluting
    scene(c,ident,number/FPS,count/FPS)


def clips(episode):
    folder=SERIES/f'episode-{episode:02}'
    visuals=folder/'visuals'
    manifest=json.loads((folder/'timeline.json').read_text(encoding='utf-8-sig'))
    mapping={}
    for row in manifest['scenes']:
        ident=row['id']
        n=row['end_frame']-row['start_frame']
        suffix='motion-reframed' if episode==6 and ident in ('P01','P03') else 'motion'
        final=visuals/f'{ident}-{suffix}.mp4'
        if not final.is_file():
            temp=final.with_suffix('.part.mp4')
            print(f'{folder.name} {ident} rendering {n} frames',flush=True)
            def render_frame(c,i):
                if i and i%150==0:
                    print(f'{folder.name} {ident} {i}/{n} frames',flush=True)
                draw(c,episode,ident,i,n)

            encode_scene(temp,n,render_frame,preset='ultrafast',threads=2)
            with av.open(str(temp)) as media:
                stream=media.streams.video[0]
                if (stream.width,stream.height,stream.frames)!=(WIDTH,HEIGHT,n):
                    raise ValueError(f'{ident}: invalid motion render dimensions or frame count')
                if next(media.decode(stream),None) is None:
                    raise ValueError(f'{ident}: invalid motion render decode')
            temp.replace(final)
        print(f'{folder.name} {ident} ready',flush=True)
        mapping[ident]={'path':final.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                        'reference_only':False,'native_composition':True}
    target=visuals/('clinical-overrides.json' if episode==6 else 'coating-overrides.json')
    temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    temporary.replace(target)


def worker(episodes):
    child_options={}
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes

        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        kernel.SetPriorityClass.argtypes=(wintypes.HANDLE,wintypes.DWORD)
        kernel.GetPriorityClass.argtypes=(wintypes.HANDLE,)
        pid_handle=kernel.GetCurrentProcess()
        priority=subprocess.BELOW_NORMAL_PRIORITY_CLASS
        if not kernel.SetPriorityClass(pid_handle,priority) or kernel.GetPriorityClass(pid_handle)!=priority:
            raise ctypes.WinError(ctypes.get_last_error())
        child_options['creationflags']=priority
        print(f'Motion worker {os.getpid()} running BelowNormal',flush=True)
    for episode in episodes:
        clips(episode)
        completed=subprocess.run([sys.executable,'-m','tools.elysian_video.batch',f'episode-{episode:02}'],
                                 cwd=ROOT,**child_options)
        print(f'episode-{episode:02} build exit {completed.returncode}',flush=True)
        if completed.returncode not in (0,1):
            raise SystemExit(completed.returncode)


def inspect_package(episode):
    """Collect exact companion samples and compare locked narration to the master."""
    from PIL import Image, ImageDraw
    from tools.elysian_video.__main__ import LEGACY_FFMPEG
    from tools.elysian_video.qa import file_hash

    folder=SERIES/f'episode-{episode:02}'
    delivery=folder/'delivery'
    master=delivery/f'{folder.name}-1440p.mp4'
    short=delivery/f'{folder.name}-short.mp4'
    thumbnail=delivery/f'{folder.name}-thumbnail.jpg'
    mapping=folder/'visuals'/('clinical-overrides.json' if episode==6 else 'coating-overrides.json')
    picture_paths=[row['path'] for row in json.loads(mapping.read_text(encoding='utf-8-sig')).values()]
    qa_file=folder/'QA.json'
    if not all('-motion' in path for path in picture_paths) or qa_file.stat().st_mtime_ns<mapping.stat().st_mtime_ns:
        raise ValueError(f'{folder.name} revised package is still assembling')
    report=json.loads(qa_file.read_text(encoding='utf-8-sig'))
    review_hash=file_hash(master)
    if report['sha256']!=review_hash:
        raise ValueError(f'{folder.name} needs QA for its current master')
    scenes=json.loads((folder/'timeline.json').read_text(encoding='utf-8-sig'))['scenes']
    source=ROOT/scenes[0]['audio']['path']
    if any(ROOT/row['audio']['path']!=source for row in scenes if row.get('audio')):
        raise ValueError(f'{folder.name} needs a separate check for each narration file')
    picker=SERIES/'episode-02'/'finish_topic.py'
    spec=importlib.util.spec_from_file_location('series_voice_alignment',picker)
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    def reference_time(target):
        for row in scenes:
            start,end=row['start_frame']/FPS,row['end_frame']/FPS
            if start<=target<end and row.get('audio'):
                return row['audio']['in_sec']+target-start
        raise ValueError(f'No Alexander speech mapped at {target} seconds')

    points=(2,39,80,158,222,264) if episode==6 else (1,20,43,77,102,138)
    voice=verifier.voice_alignment(LEGACY_FFMPEG,source,master,[(reference_time(t),t) for t in points])
    finish=json.loads((folder/'finish-config.json').read_text(encoding='utf-8-sig'))
    a,b=finish['short']['seconds']
    short_points=(.65,4.9,9.0,min(14.2,b-a-3.05))
    short_voice=verifier.voice_alignment(LEGACY_FFMPEG,source,short,
                                        [(reference_time(a+t),t) for t in short_points])
    if any(m['correlation']<.90 or abs(m['offset_sec'])>=.05 for m in voice+short_voice):
        raise ValueError(f'{folder.name} narration comparison needs review')
    with Image.open(thumbnail) as thumb:
        if thumb.size!=(1280,720):
            raise ValueError(f'{folder.name} thumbnail has the wrong dimensions')
        thumb.verify()

    review_times=[.3+(b-a-.7)*i/7 for i in range(8)]
    sheet=Image.new('RGB',(752,706),'#123d35')
    labels=ImageDraw.Draw(sheet)
    with av.open(str(short)) as media:
        stream=media.streams.video[0]
        if (stream.width,stream.height)!=(1080,1920):
            raise ValueError(f'{folder.name} Short has the wrong dimensions')
        checked=0
        for f in media.decode(stream):
            if f.time is None or f.time<review_times[checked]:
                continue
            x,y=4+188*(checked%4),4+353*(checked//4)
            pic=f.to_image()
            pic.thumbnail((180,320),Image.Resampling.LANCZOS)
            sheet.paste(pic,(x,y))
            labels.text((x+6,y+326),f'{f.time:.2f} s',fill='#eaf5ea')
            checked+=1
            if checked==len(review_times):
                break
        if checked!=len(review_times):
            raise ValueError(f'{folder.name} Short is shorter than its verified picture window')
    contact=delivery/f'{folder.name}-short-phone.jpg'
    sheet.save(contact,quality=92)
    evidence={'master_sha256':review_hash,'short_sha256':file_hash(short),
              'thumbnail_sha256':file_hash(thumbnail),'narration_sha256':file_hash(source),
              'master_voice_alignment':voice,'short_voice_alignment':short_voice,
              'short_contact_sheet':contact.relative_to(folder).as_posix(),
              'status':'Exact sample evidence for visual review'}
    path=folder/'motion-exact-evidence.json'
    path.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(path,flush=True)


if __name__=='__main__':
    if sys.argv[1:2]==['audit']:
        for selection in sys.argv[2:]:
            inspect_package(int(selection))
    else:
        worker([int(value) for value in sys.argv[1:]] or [6,7])
