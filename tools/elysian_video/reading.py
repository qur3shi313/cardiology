"""Native motion scenes for Topic 04, reading a coronary angiogram."""

import argparse
from bisect import bisect_right
from functools import lru_cache
import json
from math import cos, exp, hypot, pi, radians, sin
from random import Random

import skia

from .__main__ import FPS, ROOT, SERIES
from .access import BOLD, HEADING, LOGO, REGULAR, color, grad, line, path, rect, solid
from .angiogram import art, block, dot, tree
from .encode import encode_scene


FOLDER = SERIES/'episode-04'
ASSETS = FOLDER/'visuals'
W, H = 1280, 720
INK, TEAL, DARK = '#112f2e', '#297568', '#0e2927'
LIGHT, WHITE, GOLD = '#d3e9da', '#f6fff8', '#ffe4a3'
FILM, FILM_INK = '#bdc5c1', '#161c1c'
ROSE, PLAQUE = '#ad6368', '#e3ba76'
SAMPLE = skia.SamplingOptions(skia.FilterMode.kLinear)
OVERLAP, CLEAR = 53, -21
LESION_INDEX = .55


def smooth(p):
    p = max(0., min(1., p))
    return p*p*(3-2*p)


def cue(t, start, end):
    return smooth((t-start)/(end-start))


def blend(a, b, p):
    return a+(b-a)*p


FACES = {}


def font(size, face):
    key = (size, id(face))
    if key not in FACES:
        result = skia.Font(face, size)
        result.setEdging(skia.Font.kAntiAlias)
        FACES[key] = result
    return FACES[key]


def label(c, copy, x, y, size=34, tone=WHITE, *, face=BOLD, align='left', alpha=255):
    f = font(size, face)
    width = f.measureText(copy)
    start = x if align == 'left' else x-width if align == 'right' else x-width/2
    if start < 0 or start+width > W:
        raise ValueError(f'Label exceeds frame: {copy}')
    c.drawString(copy, start, y, f, solid(tone, alpha))


def heading(c, copy, *, dark=True):
    if dark:
        pen=skia.Paint(AntiAlias=True)
        pen.setShader(skia.GradientShader.MakeLinear([skia.Point(0,0),skia.Point(0,135)],
                      [color('#102b28',237),color('#102b28',152),color('#102b28',0)], [0,.63,1]))
        rect(c,0,0,W,135,pen)
    label(c, copy, 56, 106, 56, WHITE if dark else INK, face=HEADING)


def badge(c, copy, x=57, y=640, *, dark=True, size=29):
    f = font(size, BOLD)
    width = f.measureText(copy)+35
    block(c, x, y, width, 46, 9, solid(DARK if dark else '#ebf5eb', 244))
    label(c, copy, x+17, y+33, size, WHITE if dark else INK)


def disclosure(c, copy='Simulated X-ray'):
    f = font(28, BOLD)
    width = f.measureText(copy)
    block(c, 1216-width-31, 33, width+31, 48, 8, solid('#132f2e', 242))
    label(c, copy, 1200, 67, 28, WHITE, align='right')


def ring(c, point, radius=23, tone=GOLD, width=3):
    pen = solid(tone)
    pen.setStyle(skia.Paint.kStroke_Style)
    pen.setStrokeWidth(width)
    c.drawCircle(*point, radius, pen)


def clinical_backdrop(c):
    rect(c, 0, 0, W, H, grad(120, 0, 1130, 750, ['#edf7ee','#cbe3d8','#96c1b4']))
    c.drawOval(skia.Rect.MakeXYWH(500, 90, 870, 690), solid('#eff8eb', 88))


def vignette(c):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(643, 344), 755,
                [color('#e3e7df'), color('#aeb9b4'), color('#394d49')], [0, .55, 1]))
    rect(c, 0, 0, W, H, p)


@lru_cache(maxsize=1)
def film_plate():
    surface = skia.Surface(W*2, H*2)
    c = surface.getCanvas()
    c.scale(2, 2)
    vignette(c)
    c.drawOval(skia.Rect.MakeXYWH(297, 115, 600, 610), solid('#e8e8de', 81))
    c.drawOval(skia.Rect.MakeXYWH(692, 109, 500, 626), solid('#647a73', 23))
    for i in range(7):
        y = 123+i*71
        points = art.curve((15,y+37), ((270,y-3),(441,y-37),(629,y+2)),
                           ((815,y+41),(1035,y+3),(1260,y+29)))
        line(c, points, '#edf0ea', 8, 27)
        line(c, points, '#657772', 1.8, 25)
    random = Random(421)
    for _ in range(2150):
        dot(c, random.uniform(5,W-5),random.uniform(4,H-4),random.uniform(.25,1.15),
            '#34423d',random.randrange(11,38))
    return surface.makeImageSnapshot()


def film(c, alpha=255):
    c.drawImageRect(film_plate(), skia.Rect.MakeWH(W,H), SAMPLE, solid(WHITE, alpha))


def dz(x,y):
    return 17*sin(y/70)+(x-128)*.10


@lru_cache(maxsize=2)
def model(side):
    branches, distance = tree(side)
    if side == 'right':
        return tuple((tuple((x,y,dz(x,y)) for x,y in pts), lengths, entry, width)
                     for pts,lengths,entry,width in branches),distance
    lad = branches[1][0]
    ix = round((len(lad)-1)*LESION_INDEX)
    lx,ly = lad[ix]
    covering = branches[4][0]
    over = min(range(len(covering)), key=lambda i:abs(covering[i][1]-ly))
    bx,by = covering[over]
    q = radians(OVERLAP)
    rise = (lx-bx)*cos(q)/sin(q)+dz(lx,ly)-dz(bx,by)
    out = []
    for branch_id,(pts,lengths,entry,width) in enumerate(branches):
        coords = []
        for i,(x,y) in enumerate(pts):
            z = dz(x,y)
            if branch_id == 4:
                z += rise*smooth(i/max(1,over))
            coords.append((x,y,z))
        out.append((tuple(coords),lengths,entry,width))
    return tuple(out),distance


@lru_cache(maxsize=1)
def lesion_spec():
    branches,_ = model('left')
    pts,lengths,_,_ = branches[1]
    i = round((len(pts)-1)*LESION_INDEX)
    return pts[i], lengths[i]/lengths[-1]


def project(point, angle, cx=642, cy=374, zoom=1.):
    x,y,z = point
    q = radians(angle)
    return cx+zoom*((x-128)*cos(q)+z*sin(q))*5.02, cy+zoom*(y-157)*2.25


def reveal(points, distances, amount):
    if amount <= 0:
        return (),()
    if amount >= distances[-1]:
        return points,distances
    index = max(0,bisect_right(distances,amount)-1)
    a,b = points[index:index+2]
    p = (amount-distances[index])/(distances[index+1]-distances[index])
    endpoint = tuple(blend(x,y,p) for x,y in zip(a,b))
    return (*points[:index+1],endpoint), (*distances[:index+1],amount)


def outline(points, widths):
    left,right = [],[]
    for i,(x,y) in enumerate(points):
        a,b = points[max(0,i-1)],points[min(len(points)-1,i+1)]
        length = max(.001,hypot(b[0]-a[0],b[1]-a[1]))
        dx,dy = -(b[1]-a[1])/length*widths[i]/2,(b[0]-a[0])/length*widths[i]/2
        left.append((x+dx,y+dy)); right.append((x-dx,y-dy))
    return path((*left,*reversed(right)), True)


def coronary(c, side='left', *, angle=CLEAR, fill=1., alpha=255, narrowed=True,
             cx=642, cy=374, zoom=1., anatomical=False, highlight=None, trace=1., catheter=True):
    branches, extent = model(side)
    _, stenosis_u = lesion_spec()
    to_screen = lambda pt: project(pt,angle,cx,cy,zoom)
    for i,(points,lengths,entry,width) in enumerate(branches):
        visible = fill*extent-entry
        segment, portion = reveal(points,lengths,visible)
        if len(segment) < 2:
            continue
        factor = lengths[-1]
        screen = tuple(map(to_screen,segment))
        widths = []
        for d in portion:
            u = d/factor
            neck = .70*exp(-((u-stenosis_u)/.054)**2) if narrowed and side=='left' and i==1 else 0
            widths.append(max(1.75,width*2.55*(1-.48*u)*(1-neck))*zoom)
        border = '#68383e' if anatomical else '#66726e'
        inner = '#ce7372' if anatomical else FILM_INK
        c.drawPath(outline(screen,tuple(w+4.1*zoom for w in widths)), solid(border,int(alpha*.74)))
        c.drawPath(outline(screen,widths),solid(inner,alpha))
        if i == highlight:
            selected,_ = reveal(points,lengths,factor*trace)
            selected = tuple(map(to_screen,selected))
            line(c,selected,'#dfffbd' if anatomical else '#f9df91',4.2*zoom,243)
            if selected:
                dot(c,*selected[-1],5.7*zoom,GOLD)
    ostium = to_screen(branches[0][0][0])
    if catheter:
        x,y = ostium
        guide=art.curve((x-185*zoom,y-49*zoom),((x-129*zoom,y-37*zoom),
                        (x-30*zoom,y-61*zoom),(x,y)))
        line(c,guide,'#345149' if anatomical else '#3b4a45',8.5*zoom)
        line(c,guide,'#b2e4ce' if anatomical else '#89958e',2.3*zoom)
    return to_screen(lesion_spec()[0]) if side=='left' else ostium


def leader(c, copy, point, x, y, *, dark=True):
    tone = GOLD if dark else '#1e6154'
    px,py = point
    bend = x-26 if px<x else x+26
    line(c,((px,py),(bend,y+10),(x,y+10)),tone,2.7)
    dot(c,px,py,5.,tone)
    label(c,copy,x+9,y,31,WHITE if dark else INK)


def heart(c, x, y, scale, *, branch=None):
    c.save()
    c.translate(x,y)
    c.scale(scale,scale)
    shell = art.curve((5,-80),((-61,-139),(-158,-92),(-142,5)),
                      ((-130,79),(-43,142),(52,183)),
                      ((111,143),(153,70),(142,-6)),
                      ((137,-85),(62,-127),(5,-80)))
    c.drawPath(path(shell,True),grad(-119,-104,153,191,['#eda695','#a95160','#692b42']))
    line(c,shell,'#f1b1a5',2.6,155)
    arch = art.curve((22,-85),((19,-125),(15,-155),(37,-172)),
                    ((54,-185),(89,-167),(92,-129)))
    line(c,arch,'#6d3441',28)
    line(c,arch,'#c97674',22)
    line(c,arch,'#efa99a',5)
    main=art.curve((27,-86),((18,-71),(3,-53),(-9,-39)))
    lad=art.curve((-9,-39),((-5,-7),(11,27),(20,49)),((28,82),(23,114),(42,143)))
    lcx=art.curve((-9,-39),((-44,-24),(-77,-32),(-117,-11)))
    rca=art.curve((42,-81),((66,-58),(99,-38),(109,-2)),((109,18),(99,51),(77,73)))
    for i,v in enumerate((main,lad,lcx,rca)):
        line(c,v,'#773743',11)
        line(c,v,GOLD if branch in (i,'all') else '#d98f84',6.5)
    c.restore()


def imaging_open(c,t,d):
    film(c)
    # Both projections share all world coordinates and the same lumen contour.
    swing=cue(t,.9,4.7)-cue(t,6.1,8.1)+cue(t,9.75,12.6)
    angle=blend(OVERLAP,CLEAR,swing)
    pos=coronary(c,angle=angle,fill=.21+.79*cue(t,-.2,2.35),zoom=1.02+.14*t/d,cy=371)
    if t>=4.75:
        heading(c,'How to read an angiogram')
        ring(c,pos,29+3*sin(t*2.1),'#624f28',5)
        ring(c,pos,25+3*sin(t*2.1),GOLD,3)
        badge(c,'One narrowing · Two views')
    else:
        badge(c,'Overlapping branch' if t<2.65 else 'View changing')
    disclosure(c)


def image_meaning(c,t,d):
    clinical_backdrop(c)
    warm=1-cue(t,9.5,13.8)
    if warm>0:
        heart(c,683,310,1.84)
    if warm<1:
        film(c,round((1-warm)*255))
    amount=.07+.93*cue(t,3,12.9)
    angle=CLEAR+6.5*sin(t/d*pi)
    coronary(c,angle=angle,fill=amount,alpha=round(248-39*cue(t,15.9,d)),zoom=1.01+.15*t/d,
             anatomical=warm>.48)
    heading(c,'Contrast outlines the channel',dark=warm<.55)
    if warm<.55:
        disclosure(c)
    if 4.6<t<9.7:
        badge(c,'Contrast enters at the coronary opening',dark=warm<.55)
    elif t>=9.7:
        badge(c,'The open lumen fills',dark=warm<.55)


def branches_scene(c,t,d):
    film(c)
    left = t<12.5 or t>=16.55
    if t<5.3:
        branch,title,start=0,'Left main',0
    elif t<9.9:
        branch,title,start=1,'Left anterior descending',5.3
    elif t<12.5:
        branch,title,start=2,'Circumflex',9.9
    elif t<16.55:
        branch,title,start=0,'Right coronary artery',12.5
    else:
        branch,title,start=1,'LAD · Site of the narrowing',16.55
    side='left' if left else 'right'
    angle=(CLEAR if left else 15)+7*sin(t/d*pi)
    local=t-start
    spot=coronary(c,side,angle=angle,cx=732,cy=380,zoom=.97+.12*t/d,
                  fill=1 if left else .18+.82*cue(local,-.2,2.8),
                  narrowed=left,highlight=branch,trace=.08+.92*cue(local,0,3.9))
    heart(c,232,319,1.02,branch=branch if left else 3)
    if left and t>=16.55:
        ring(c,spot,25,GOLD)
    heading(c,'Follow the branches')
    disclosure(c)
    badge(c,title)


def anatomy_channel(c,t,*, mode='narrow', pressure=False, lead=0.):
    clinical_backdrop(c)
    left,right,mid=65,1214,630
    samples=range(left,right+1,13)
    xs=tuple(samples)
    cy=371+(15 if pressure else 6)*sin(t*.79)
    top=lambda x: cy-47+((45 if mode=='occluded' else 37)*exp(-((x-mid)/116)**2)
                      if mode!='open' else 0)
    bottom=lambda x: cy+45-((47 if mode=='occluded' else 18)*exp(-((x-mid)/110)**2)
                          if mode!='open' else 0)
    outer=(*((x,cy-91) for x in xs),*((x,cy+91) for x in reversed(xs)))
    c.drawPath(path(outer,True),grad(67,cy-98,1150,cy+93,['#70404d','#bb6874','#7e394f']))
    lumen=(*((x,top(x)) for x in xs),*((x,bottom(x)) for x in reversed(xs)))
    c.drawPath(path(lumen,True),grad(62,cy-48,1190,cy+50,['#7d3d49','#b56164','#713846']))
    line(c,[(x,top(x)) for x in xs],'#dc8e8a',2.8,198)
    line(c,[(x,bottom(x)) for x in xs],'#da9991',2.8,180)
    if mode!='open':
        plaque_x=range(466,797,8)
        back=tuple((x,top(x)-17*exp(-((x-mid)/110)**2)) for x in plaque_x)
        front=tuple((x,top(x)) for x in reversed(tuple(plaque_x)))
        c.drawPath(path((*back,*front),True),solid(PLAQUE))
    if mode=='occluded':
        c.drawOval(skia.Rect.MakeXYWH(602,cy-24,59,50),solid('#d4aa70'))
    else:
        for i in range(9):
            x=80+((t*115+i*139)%1098)
            mid_lumen=(top(x)+bottom(x))/2
            line(c,[(x-7,mid_lumen),(x+8,mid_lumen)],'#e1a69b',2.8,138)
    if pressure:
        guide_y=cy-2
        line(c,[(66,guide_y),(196,guide_y)],'#3b6f60',20)
        line(c,[(66,guide_y),(196,guide_y)],'#a4d2b7',12)
        tip=blend(170,1023,lead)
        screen=[(x,(top(x)+bottom(x))/2) for x in range(75,int(tip),8)]
        if screen:
            screen.append((tip,(top(tip)+bottom(tip))/2))
            line(c,screen,'#5b4b2f',5)
            line(c,screen,GOLD,2.6)
            if lead>.73:
                sx,sy=screen[-1]
                dot(c,sx-13,sy,5,GOLD)
        return (198,guide_y),(tip-13,(top(tip)+bottom(tip))/2)
    return (mid,cy)


def narrowing_scene(c,t,d):
    if t<13.0:
        film(c)
        amount=.45+.55*cue(t,-.3,4.5)
        zoom=1.04+.18*cue(t,2.0,11.5)
        focus=coronary(c,fill=amount,zoom=zoom,cx=616-29*sin(t/d*pi),cy=357)
        heading(c,'Find the focal narrowing')
        disclosure(c)
        if t<6.4:
            ring(c,focus,22+3*sin(t*3),GOLD)
            badge(c,'Contrast reaches beyond it')
        elif t<10.4:
            pt=project(model('left')[0][1][0][16],CLEAR,616-29*sin(t/d*pi),357,zoom)
            ring(c,pt,23,'#c2f2d5')
            badge(c,'Nearby reference segment')
        else:
            ring(c,focus,28,GOLD)
            badge(c,'Focal narrowing')
    elif t<16.9:
        anatomy_channel(c,t)
        heading(c,'The channel remains open',dark=False)
        leader(c,'Plaque in the vessel wall',(624,341),820,263,dark=False)
    else:
        anatomy_channel(c,t,mode='occluded')
        heading(c,'Complete blockage example',dark=False)
        leader(c,'Channel closed here',(630,371),815,253,dark=False)


def two_views(c,t,d):
    film(c)
    if t<12.7:
        angle=blend(OVERLAP,CLEAR,cue(t,7.6,12.2))
        zoom=1.06+.18*(t/12.7)
        spot=coronary(c,angle=angle,zoom=zoom,cx=641-19*sin(t*.29))
        if t<7.6:
            ring(c,spot,29,'#f7d790')
            badge(c,'Branch overlap')
        else:
            ring(c,spot,25+2*sin(t*2.2),GOLD)
            badge(c,'The same narrowing')
    else:
        line(c,[(641,142),(641,626)],'#344d46',3.3,202)
        phase=cue(t,12.7,15.4)
        for x,angle,view in ((321,OVERLAP,'View 1'),(961,CLEAR,'View 2')):
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(x-318,139,636,475))
            pos=coronary(c,angle=angle,cx=x,cy=384,zoom=.62+.14*phase+.04*(t/d))
            ring(c,pos,18.6+2.3*sin(t*2),GOLD,2.7)
            c.restore()
            label(c,view,x,655,32,WHITE,align='center')
    heading(c,'Same artery, different angle')
    disclosure(c)


def physiology(c,t,d):
    if t<5.2:
        film(c)
        spot=coronary(c,zoom=1.13+.18*(t/5.2),angle=CLEAR+3*sin(t*.41))
        ring(c,spot,24+5*cue(t,.3,4.7),GOLD)
        heading(c,'The picture is one part')
        disclosure(c)
        return
    lead=cue(t,6.5,13.4)
    upstream,distal=anatomy_channel(c,t,pressure=True,lead=lead)
    heading(c,'Pressure adds information' if t<10.3 else 'FFR and iFR',dark=False)
    if t<13.75:
        badge(c,'Pressure-sensing wire',dark=False)
    else:
        leader(c,'Upstream pressure',upstream,71,205,dark=False)
        leader(c,'Beyond the narrowing',distal,842,205,dark=False)
        for start in (248,774):
            waveform=tuple((start+i*5,574-18*max(0,sin(i*.21-t*4.2))**7+5*sin(i*.21-t*4.2))
                           for i in range(54))
            line(c,waveform,'#237969',3.4)


def micro_vessels(c,t):
    clinical_backdrop(c)
    c.save()
    c.translate(31*sin((t-4.55)*.48),-12*cos((t-4.55)*.52))
    c.drawOval(skia.Rect.MakeXYWH(257,140,822,545),
               grad(250,150,1079,685,['#a35e6b','#c98c8b','#793b52']))
    for i in range(9):
        y=202+i*47
        wave=14*sin(i*.84)
        trunk=art.curve((275,y+25),((440,y-30),(542,y+20),(631,y+wave)),
                        ((780,y+39),(913,y-15),(1031,y+21)))
        line(c,trunk,'#723b54',8.1)
        line(c,trunk,'#ecb69f',3.3)
        for j in range(3):
            x0=400+j*189
            offset=28 if (i+j)%2 else -29
            line(c,[(x0,y+4),(x0+41,y+offset),(x0+89,y+offset*.6)],'#dfaa9d',3.2)
        q=(t*.29+i*.173)%1
        x=294+q*716
        dot(c,x,y+7+6*sin(q*pi*2),3.3,'#f5dca9',204)
    c.restore()


def spasm(c,t):
    clinical_backdrop(c)
    p=.23+.77*sin(min(1,(t-9)/7)*pi)**2
    xs=range(93,1190,10)
    half=lambda x: 67-45*p*exp(-((x-651)/122)**2)
    cy=374+12*sin((t-9.9)*.72)
    outer=tuple((x,cy-half(x)-29) for x in xs)+tuple((x,cy+half(x)+29) for x in reversed(xs))
    c.drawPath(path(outer,True),grad(90,270,1170,490,['#854454','#ba6d75','#733f53']))
    inner=tuple((x,cy-half(x)) for x in xs)+tuple((x,cy+half(x)) for x in reversed(xs))
    c.drawPath(path(inner,True),grad(91,311,1162,460,['#632c40','#b36567','#733c48']))
    for i in range(7):
        x=101+((t*140+i*167)%1070)
        dot(c,x,cy+9*sin(i*.69+t),4.2,'#e9b0a0',143)


def second_case(c,t,d):
    if t<4.55:
        film(c)
        coronary(c,narrowed=False,angle=8+7*sin(t*.6),zoom=1.09+.15*(t/4.55),
                 fill=.27+.73*cue(t,0,3.55))
        heading(c,'A different example')
        disclosure(c)
        badge(c,'Major artery appears open')
    elif t<9.9:
        micro_vessels(c,t)
        heading(c,'The small blood vessels',dark=False)
        badge(c,'Concept illustration',dark=False)
    else:
        spasm(c,t)
        heading(c,'Temporary artery tightening',dark=False)
        badge(c,'Separate concept illustration',dark=False)


def option_icon(c,which,t):
    x,y=930,353
    r=131+6*sin(t*2)
    c.drawCircle(x,y,r,solid('#edf8ed',180))
    ring(c,(x,y),r,'#69a597',2)
    if which in ('findings','assessment','urgent'):
        if which=='assessment':
            ring(c,(x-13,y-15),44,TEAL,12)
            line(c,[(x+20,y+20),(x+73,y+76)],TEAL,18)
        else:
            beat=((x-81,y+10),(x-43,y+10),(x-20,y-15),(x-4,y+43),(x+15,y-59),
                  (x+36,y+11),(x+79,y+11))
            line(c,beat,'#ad5763' if which=='urgent' else TEAL,9)
            dot(c,*beat[min(len(beat)-1,int((t*3.2)%len(beat)))],7.0,'#ab5a62')
    elif which=='medicines':
        c.save()
        c.translate(x,y)
        c.rotate(-29)
        block(c,-88,-35,176,70,35,solid('#327d70'))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0,-36,90,72))
        block(c,-88,-35,176,70,35,solid('#e5ba77'))
        c.restore()
        c.restore()
    elif which=='pci':
        for k in range(7):
            v=x-95+k*28
            line(c,[(v,y-44),(v+13,y-15),(v,y+14),(v+13,y+43)],'#458e80',5)
        line(c,[(x-115,y),(x+115,y)],'#be9961',3)
    else:
        main=art.curve((x-102,y-19),((x-35,y-32),(x+31,y+21),(x+103,y+19)))
        graft=art.curve((x-73,y-23),((x-45,y-103),(x+48,y-64),(x+84,y+17)))
        line(c,main,'#9b5561',15)
        line(c,graft,'#4a8e7d',11)


def choices(c,t,d):
    clinical_backdrop(c)
    heart(c,427+24*sin(t*.27),344,1.44+.15*sin(t/d*pi),branch='all')
    if t<7.8:
        option,copy='findings','Findings, symptoms and urgency'
    elif t<10.5:
        option,copy='medicines','Medicines and prevention'
    elif t<13.1:
        option,copy='assessment','Further assessment'
    elif t<17.9:
        option,copy='pci','Angioplasty and stenting'
    elif t<20.7:
        option,copy='bypass','A discussion about bypass'
    else:
        option,copy='urgent','Heart attack care can be urgent'
    option_icon(c,option,t)
    heading(c,'Findings guide the next decision',dark=False)
    label(c,copy,920,568,31,INK,align='center')


def questions(c,t,d):
    film(c)
    spot=coronary(c,angle=CLEAR+7*sin(t*.24),cx=751,cy=380,zoom=.89+.13*t/d)
    block(c,47,185,464,368,22,solid('#142f2d',234))
    if t<8:
        copy=('Which artery','was involved?')
        ring(c,spot,23+4*sin(t*2.4),GOLD)
    elif t<12.3:
        copy=('Does it affect','blood supply?')
        line(c,[(spot[0],spot[1]),(spot[0]+65,spot[1]+50),(spot[0]+99,spot[1]+73)],GOLD,2.6)
        ring(c,(spot[0]+99,spot[1]+73),18+4*sin(t*2.3),GOLD)
    else:
        copy=('What follow-up','or treatment?')
        ring(c,spot,24+5*sin(t*2.2),'#c7eed2')
    heading(c,'Three questions to ask')
    disclosure(c)
    for i,text in enumerate(copy):
        label(c,text,84,329+i*71,55,WHITE,face=HEADING)


def sources(c,t,d):
    rect(c,0,0,W,H,grad(77,41,1240,703,['#133f39','#0f2f2e','#0b2223']))
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(62,60,83,83),SAMPLE)
    label(c,'Elysian Biomedical LLP',169,117,36,WHITE)
    label(c,'Cardiology Education Series',60,191,35,'#bfe8d4')
    label(c,'Clinical sources',60,285,51,WHITE,face=HEADING)
    for i,name in enumerate(('American Heart Association','ACC / AHA / SCAI','European Society of Cardiology')):
        label(c,name,61,345+i*49,30,'#d0eadc',alpha=round(255*cue(t,.25+i*.21,1.07+i*.29)))
    label(c,'Simulated imaging · Synthetic narration',62,641,29,'#bde4d0')
    p=cue(t,3.2,4.25)
    if p>0:
        label(c,'Next in the series',62,520,29,'#9fcebc',alpha=round(255*p))
        label(c,'Recovery and next steps',62,560,34,WHITE,alpha=round(255*p))
        label(c,'after a coronary angiogram',62,598,34,WHITE,alpha=round(255*p))


SCENES={'P01':imaging_open,'P02':image_meaning,'P03':branches_scene,'P04':narrowing_scene,
        'P05':two_views,'P06':physiology,'P07':second_case,'P08':choices,'P09':questions,'P10':sources}


def save_still(scene,d,t,target):
    surface=skia.Surface(W,H)
    scene(surface.getCanvas(),t,d)
    image=surface.makeImageSnapshot()
    image.save(str(target),skia.kPNG)


def thumbnail():
    surface=skia.Surface(W,H)
    c=surface.getCanvas()
    film(c)
    spot=coronary(c,cx=937,cy=387,zoom=.89)
    ring(c,spot,37,'#654b2b',7)
    ring(c,spot,34,GOLD,4)
    rect(c,0,0,634,H,grad(0,0,634,0,['#112f2d','#163c37']))
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(62,54,71,71),SAMPLE)
    label(c,'Elysian Biomedical LLP',155,99,35,'#d5ebdc')
    label(c,'One',59,280,106,WHITE,face=HEADING)
    label(c,'Narrowing',59,389,99,WHITE,face=HEADING)
    label(c,'Two Views',61,533,81,GOLD,face=HEADING)
    badge(c,'Simulated X-ray',57,630,size=32)
    surface.makeImageSnapshot().save(str(FOLDER/'thumbnail.jpg'),skia.kJPEG,95)


def build(only=(), *, stills=False):
    ASSETS.mkdir(exist_ok=True)
    data=json.loads((FOLDER/'timeline.json').read_text(encoding='utf-8-sig'))
    entries={}
    for row in data['scenes']:
        ident=row['id']
        scene=SCENES[ident]
        count=row['end_frame']-row['start_frame']
        target=ASSETS/f'{ident}-reading.mp4'
        if not only or ident in only:
            d=count/FPS
            save_still(scene,d,d*(.65 if ident!='P01' else .45),ASSETS/f'{ident}-reading.png')
            if not stills and not target.is_file():
                tmp=target.with_suffix('.partial.mp4')
                encode_scene(tmp,count,lambda canvas,frame:scene(canvas,frame/FPS,d),preset='veryfast',threads=2)
                tmp.replace(target)
                print(f'{ident}: {count} frames',flush=True)
        if target.is_file():
            entries[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':count/FPS,
                            'reference_only':False,'native_composition':True}
            dest=ASSETS/'reading-overrides.json'
            pending=dest.with_suffix('.partial.json')
            pending.write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
            pending.replace(dest)
    thumbnail()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('scenes',nargs='*',metavar='SCENE')
    parser.add_argument('--stills',action='store_true')
    args=parser.parse_args()
    if set(args.scenes)-set(SCENES):
        parser.error('Use scene IDs P01 through P10.')
    build(args.scenes,stills=args.stills)
