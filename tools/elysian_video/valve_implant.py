"""Original balloon-expandable transcatheter valve sequence and recovery film."""
from bisect import bisect_right
from functools import lru_cache
from math import sin, cos, pi
import json

import skia

from . import access, angiogram, restenosis
from .__main__ import ROOT, SERIES, FPS, WIDTH, HEIGHT
from .encode import encode_scene

CX,ANNULUS,ROOT_ENTRY=655,443,163
LEFT=angiogram.art.curve((487,163),((500,244),(460,299),(450,342)),
                         ((419,384),(453,411),(493,438)),
                         ((467,500),(364,554),(275,673)))
RIGHT=tuple((2*CX-x,y) for x,y in LEFT)

def blend(a,b,p):
    return a+(b-a)*p

def wire_path():
    return angiogram.art.curve((CX,ROOT_ENTRY),((CX,272),(CX,443),(CX,537)),
        ((CX,568),(678,614),(714,620)),((740,625),(754,610),(749,590)),
        ((746,581),(737,579),(730,584)))

WIRE=wire_path()
ROUTE=angiogram.art.curve((445,581),((449,554),(461,531),(483,515)),
    ((504,498),(545,487),(553,450)),((562,414),(562,352),(565,298)),
    ((568,245),(589,209),(627,219)),((669,226),(677,271),(663,307)),
    ((653,327),(651,345),(655,361)))
ACCESS_TUNNEL=angiogram.art.curve((418,604),((428,596),(441,592),ROUTE[0]))
SHEATH=ACCESS_TUNNEL+ROUTE[1:8]
ACCESS_WIRE=ACCESS_TUNNEL+ROUTE[1:]

@lru_cache(maxsize=2)
def route_plate(planning=False):
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    access.rect(c,0,0,1280,720,access.grad(0,0,1280,720,['#f1f8ef','#dbece4','#bed9cd']))
    # Anterior, covered locator. The patient's right appears on the viewer's left.
    body=access.path([(424,187),(505,155),(666,155),(751,181),(855,284),(817,390),
        (847,530),(819,650),(658,680),(579,614),(507,680),(347,650),(320,531),(364,390),(321,285)],True)
    c.drawPath(body,access.grad(354,170,840,667,['#b6cec3','#739a8d','#547c72']))
    heart=angiogram.art.curve((654,302),((624,275),(588,302),(599,338)),
        ((607,375),(653,392),(677,410)),((712,388),(746,345),(727,320)),
        ((711,294),(681,286),(654,302)))
    c.drawPath(access.path(heart,True),access.grad(596,297,718,400,['#cf8e89','#974e68']))
    branches=(
        angiogram.art.curve((569,270),((568,247),(553,216),(529,201))),
        angiogram.art.curve((590,226),((588,211),(590,196),(597,179))),
        angiogram.art.curve((627,219),((631,197),(645,185),(678,181))),
        angiogram.art.curve((535,481),((564,491),(607,510),(624,553)),((630,577),(635,606),(639,637))),
        angiogram.art.curve((445,581),((442,601),(439,616),(439,640))),
        angiogram.art.curve((441,611),((451,614),(461,625),(465,640))),
    )
    for branch in branches:
        access.line(c,branch,'#8f495a',17)
        access.line(c,branch,'#ca8d85',10)
    access.line(c,ROUTE,'#8f495a',29)
    access.line(c,ROUTE,'#d09588',18)
    if planning:
        angiogram.header(c,'Checking a possible groin-to-heart route','ILLUSTRATED CT PLAN')
    else:
        access.line(c,SHEATH,'#24564f',16)
        access.line(c,SHEATH,'#9bcbb9',9)
        access.line(c,[(412,609),(419,603)],'#357469',21)
        angiogram.header(c,'The femoral route to the aortic valve','AORTIC VALVE')
        access.text(c,'Sheath stays in the groin',62,594,27,'#235d50',access.REGULAR)
        access.text(c,'Illustrated route under X-ray guidance',54,686,27,'#245c50')
    access.text(c,'Right femoral artery',62,557,31,'#235d50')
    access.line(c,[(326,568),(389,568),(438,581)],'#245c50',3)
    access.text(c,'Aortic arch',920,240,31,'#235d50')
    access.line(c,[(906,233),(822,233),(649,229)],'#245c50',3)
    return surface.makeImageSnapshot()

def groin_route(c,p,t):
    c.drawImageRect(route_plate(),skia.Rect.MakeWH(1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    # End in the ascending aorta and continue from there in the valve cutaway.
    progress=.85*access.smooth((p-.02)/.97)
    wire=angiogram.art.trace(ACCESS_WIRE,progress)
    access.line(c,wire,'#624c32',8)
    access.line(c,wire,'#f9e1a6',4.3)
    x,y=wire[-1]
    angiogram.dot(c,x,y,6,'#fff3d0')
    # The lower-right inset magnifies the same point on the path, so the
    # moving wire remains visible when the overview is viewed on a phone.
    bx,by,bw,bh=880,320,342,261
    angiogram.block(c,bx,by,bw,bh,18,access.solid('#193e37'))
    access.text(c,'Guidewire detail',bx+20,by+42,32,'#ecf6eb')
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx+14,by+61,bw-28,155),10,10),doAntiAlias=True)
    c.translate(bx+bw/2,by+140)
    c.scale(2.65,2.65)
    c.translate(-x,-y)
    access.rect(c,x-80,y-45,160,90,access.solid('#142b2a'))
    access.line(c,ROUTE,'#9e575d',35)
    access.line(c,ROUTE,'#d1978a',23)
    access.line(c,SHEATH,'#34665d',17)
    access.line(c,SHEATH,'#96c4b4',10)
    access.line(c,wire,'#644932',7)
    access.line(c,wire,'#f8db9c',4.2)
    angiogram.dot(c,x,y,5.8,'#fff3d0')
    c.restore()
    access.text(c,'Magnified from the route',bx+19,by+246,24,'#c5e7d7')

def prosthetic_top(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e5eee6'))
    x,y=654,410
    angiogram.dot(c,x,y,214,'#6a8683')
    angiogram.dot(c,x,y,198,'#b8cbc0')
    angiogram.dot(c,x,y,178,'#845060')
    opening=max(0,(1-cos(t*2*pi*1.08))/2)
    for i in range(3):
        q=2*pi*i/3-pi/2
        edge=(x+163*cos(q),y+163*sin(q))
        a=(x+120*cos(q-.89),y+120*sin(q-.89))
        b=(x+120*cos(q+.89),y+120*sin(q+.89))
        free_edge=(x+98*opening*cos(q),y+98*opening*sin(q))
        c.drawPath(access.path([a,edge,b,free_edge],True),access.grad(*edge,x,y,['#edd0ab','#a96674']))
        access.line(c,[free_edge,edge],'#f8e6c8',3)
    angiogram.header(c,'Tissue leaflets inside a metal frame','BALLOON-EXPANDABLE VALVE')
    access.text(c,'Illustrated view of a replacement valve',56,684,30,'#245c50')

@lru_cache(maxsize=1)
def base():
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    access.rect(c,0,0,1280,720,access.grad(0,0,1270,720,['#f8fbf5','#e3efe8','#bed5ca']))
    for sign in (-1,1):
        branch=angiogram.art.curve((CX+sign*200,327),
                ((CX+sign*258,303),(CX+sign*369,334),(CX+sign*547,268)))
        access.line(c,branch,'#8d4c59',50)
        access.line(c,branch,'#cc8e83',35)
        access.line(c,branch,'#ebaf9a',19)
    c.drawPath(access.path(list(LEFT)+list(reversed(RIGHT)),True),
               access.grad(374,198,810,630,['#f5beaa','#cb8684','#884f64']))
    for side in (LEFT,RIGHT):
        access.line(c,side,'#8b4c5b',47)
        access.line(c,side,'#c47c7d',33)
        access.line(c,side,'#e4a393',13)
    for sign in (-1,1):
        c.drawOval(skia.Rect.MakeXYWH(CX+sign*196-13,311,27,21),access.solid('#743b51'))
    return surface.makeImageSnapshot()

def leaflets(c,t,kind,occupied=0,displacement=0):
    beat=(1-cos(t*2*pi*1.08))/2
    for side in (-1,1):
        old=kind in ('stenosis','displaced')
        height=(38 if old else 72)*beat
        gap=(39 if old else 90)*beat
        if kind=='displaced':
            displacement=1
        if displacement:
            gap=blend(gap,136,displacement)
            height=blend(height,105,displacement)
        if occupied:
            gap=max(gap,occupied+1)
        start=(CX+side*(142 if old else 115),ANNULUS+1)
        tip=(CX+side*gap,ANNULUS-17-height)
        curve=angiogram.art.curve(start,((start[0]-side*13,ANNULUS-8),
                                    (tip[0]+side*24,tip[1]+43),tip))
        access.line(c,curve,'#875264',18 if old else 14)
        access.line(c,curve,'#d9a28a' if old else '#f4dcc0',11 if old else 9)
        access.line(c,[(x,y-2) for x,y in curve],'#ffe6cd',2.9)
        if old:
            for i,r in ((6,12),(13,9),(22,13)):
                x,y=curve[min(i,len(curve)-1)]
                angiogram.dot(c,x,y,r,'#d3b58b')
                angiogram.dot(c,x-2,y-2,r*.69,'#f3d7ab')
    return beat

def cage(c,y,r,*,front):
    h=157
    angles=tuple(i*2*pi/14 for i in range(15))
    for row in range(4):
        ry=y-h/2+row*h/4
        nodes=[]
        for i,a in enumerate(angles):
            theta=a+row*pi/14
            nodes.append((CX+r*sin(theta),ry+(i%2)*h/4,cos(theta)))
        for u,v in zip(nodes,nodes[1:]):
            is_front=(u[2]+v[2])*.5>=0
            if is_front!=front:continue
            access.line(c,[u[:2],v[:2]],'#3f5960' if front else '#7f9291',7 if front else 3)
            access.line(c,[u[:2],v[:2]],'#d9e4dd',2.7 if front else 1.4,245 if front else 140)

def delivery(c,y,r):
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(0,ROOT_ENTRY,1280,720-ROOT_ENTRY),doAntiAlias=True)
    shaft=[(CX,ROOT_ENTRY),(CX,max(ROOT_ENTRY,y+82))]
    access.line(c,shaft,'#456c73',18)
    access.line(c,shaft,'#88b8b9',11)
    balloon=angiogram.art.curve((CX,y-78),((CX-r*.48,y-68),(CX-r,y-59),(CX-r,y-48)),
        ((CX-r,y-22),(CX-r,y+23),(CX-r,y+48)),((CX-r,y+58),(CX-r*.45,y+68),(CX,y+78)),
        ((CX+r*.45,y+68),(CX+r,y+58),(CX+r,y+48)),((CX+r,y+23),(CX+r,y-22),(CX+r,y-48)),
        ((CX+r,y-59),(CX+r*.48,y-68),(CX,y-78)))
    c.drawPath(access.path(balloon,True),access.solid('#80bfbb',183))
    access.line(c,balloon,'#5d9d97',3.4)
    access.line(c,[(CX,y-78),(CX,y+81)],'#477e88',5)
    # A visible central wire in the cutaway stays aligned with the catheter lumen.
    access.line(c,[(CX,ROOT_ENTRY),(CX,max(ROOT_ENTRY,y+82))],'#f2d19b',2.5,160)
    for pos in (y-53,y+53):
        access.line(c,[(CX-4,pos),(CX+4,pos)],'#e6ce96',4)
    c.restore()

def draw_wire(c,progress):
    wire=angiogram.art.trace(WIRE,progress)
    access.line(c,wire,'#8b683d',7)
    access.line(c,wire,'#f9dda4',3.8)
    return wire

def xray(c,wire):
    x,y,w,h=58,365,342,251
    angiogram.block(c,x,y,w,h,17,access.solid('#23312f'))
    angiogram.block(c,x+11,y+56,w-22,h-69,12,access.grad(x,y,x+w,y+h,['#aeb4ae','#69726f']))
    access.text(c,'Simulated X-ray',x+20,y+39,32,'#edf7ed')
    def map_points(points):
        return [(x+168+(a-CX)*.43,y+62+(b-ROOT_ENTRY)*.35) for a,b in points]
    for side in (LEFT,RIGHT):
        access.line(c,map_points(side),'#bfc6c0',4.4)
    access.line(c,map_points(wire),'#343b39',3.4)
    tip_x,tip_y=map_points(wire[-1:])[0]
    angiogram.dot(c,tip_x,tip_y,3.2,'#292f2e')

def pump_flow(c,t,beat,wide):
    if beat<.35:return
    for i in range(12):
        y=668-(i*48+t*245)%484
        x=CX+((i*13)%91-44)*(1.25 if wide else .52)
        access.line(c,[(x,y+13),(x,y-11)],'#d1e6cc',4.5,164)
        access.line(c,[(x-6,y-3),(x,y-11),(x+6,y-3)],'#e5efd3',3.1,184)

def groin_closure(c,p):
    access.rect(c,0,0,1280,720,access.grad(0,0,1280,720,['#193c3a','#24524d','#122e30']))
    for index in range(9):
        y=230+index*54
        access.line(c,[(0,y+51),(341,y),(741,y+38),(1280,y-29)],'#75ad9b',2.3,61)
    angiogram.block(c,397,322,482,165,77,access.solid('#132e30'))
    angiogram.block(c,421,344,434,121,58,access.grad(420,345,840,470,['#e8b68f','#c68776']))
    gone=access.smooth(p/.57)
    if gone<1:
        sheath=[(567-73*gone,241-167*gone),(638-73*gone,404-167*gone)]
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0,165,1280,555),doAntiAlias=True)
        access.line(c,sheath,'#316257',28)
        access.line(c,sheath,'#8fc6b3',16)
        access.line(c,sheath[:1]+[(sheath[0][0]+13,sheath[0][1]+28)],'#356b62',38)
        c.restore()
    access.line(c,[(630,406),(646,402)],'#a76261',3.8)
    cover=access.smooth((p-.57)/.36)
    if cover:
        y=blend(289,405,cover)
        angiogram.block(c,534,y-36,208,72,22,access.solid('#f1e8d3'))
        angiogram.block(c,601,y-26,74,52,12,access.solid('#fff6df'))
    angiogram.header(c,'Closing the groin access site','AORTIC VALVE',True)
    access.text(c,'Access equipment comes out' if p<.57 else 'Staff dress and check the site',
                60,675,30,'#dbeee3')

def result_check(c,p,t):
    x,y,w,h=60,363,331,247
    angiogram.block(c,x,y,w,h,18,access.solid('#183b37'))
    if p<.51:
        access.text(c,'Illustrated echo',x+20,y+38,28,'#def2e6')
        phase=(1-cos(t*2*pi*1.08))/2
        for i in range(4):
            yy=y+75+35*i
            access.line(c,[(x+24,yy),(x+w-24,yy)],'#9dbcb0',1.2,91)
        for side in (-1,1):
            cusp=angiogram.art.curve((x+166+side*89,y+134),
                ((x+166+side*49,y+112),(x+166+side*30*phase,y+149),(x+166+side*58*phase,y+180)))
            access.line(c,cusp,'#b9dbcb',5)
        if phase>.38:
            for i in range(5):
                yy=y+181-(t*104+23*i)%113
                xx=x+166+(i-2)*10
                access.line(c,[(xx,yy+7),(xx,yy-5)],'#e8c485',4,201)
        access.text(c,'Flow through the valve',x+20,y+226,24,'#def2e6')
    else:
        access.text(c,'Heart rhythm check',x+20,y+38,27,'#def2e6')
        for i in range(3):
            yy=y+103+i*44
            access.line(c,[(x+20,yy),(x+w-20,yy)],'#9dbcb0',1.2,91)
        pattern=(0,0,0,-10,0,0,13,-52,32,0,0,-12,-13,0,0,0,0,0)
        start=int(t*14)
        trace=[(x+19+i*8,y+151+pattern[(i+start)%len(pattern)]) for i in range(36)]
        access.line(c,trace,'#bbebd1',4)


def panel(c,title,heading,lines,tag='TAVI PROCEDURE'):
    access.rect(c,0,0,1280,720,access.solid('#e7f0e8'))
    angiogram.header(c,title,tag)
    angiogram.block(c,680,184,547,424,28,access.solid('#193d37'))
    for index,text in enumerate(heading):
        access.text(c,text,56,291+47*index,43,'#004b3d')
    for index,text in enumerate(lines):
        access.text(c,text,56,357+47*(len(heading)-1)+40*index,32,'#333b39',access.REGULAR)


def rhythm(c,t,x,y,w,h):
    pattern=(0,0,0,-5,0,0,11,-49,28,0,0,-11,-15,0,0,0,0,0)
    for index in range(4):
        level=y+index*h/3
        access.line(c,[(x,level),(x+w,level)],'#7bada0',1.8,125)
    phase=t*13
    points=[]
    for index in range(94):
        position=phase+index*.62
        step=int(position)
        height=blend(pattern[step%len(pattern)],pattern[(step+1)%len(pattern)],position-step)
        points.append((x+index*w/93,y+h*.55+height*h/83))
    access.line(c,points,'#4e8977',11)
    access.line(c,points,'#c6f1d8',4.8)


def focus_rows(c,items,progress,*,y=263,step=63):
    position=min(len(items)-.001,progress*len(items))
    selected=int(position)
    for index,label in enumerate(items):
        line_y=y+step*index
        fill='#40796b' if index==selected else '#265349'
        angiogram.block(c,708,line_y-34,490,53,15,access.solid(fill))
        if index==selected:
            underline=415*(position-selected)
            if underline>1:
                angiogram.block(c,758,line_y+8,underline,6,3,access.solid('#8ac5ae'))
        angiogram.dot(c,738,line_y-8,8,'#e4ce99' if index==selected else '#8db4a6')
        access.text(c,label,763,line_y+1,29,'#edf6ea')


def recovery_indicator(c,t,kind):
    """Draw the monitored finding or recovery action alongside its text."""
    angiogram.block(c,709,501,489,80,14,access.solid('#112e2a'))
    if kind in ('rhythm','observe'):
        rhythm(c,t,732,516,430,49)
    elif kind in ('bleeding','injury'):
        access.line(c,[(742,544),(1162,544)],'#a85d65',23)
        access.line(c,[(742,544),(1162,544)],'#e3aa92',12)
        for index in range(6):
            x=755+(index*71+t*144)%394
            angiogram.dot(c,x,544,4,'#f3deab')
        if kind=='bleeding':
            pulse=(1-cos(t*2*pi))/2
            angiogram.dot(c,951,529,8+6*pulse,'#efd0a0')
        else:
            access.line(c,[(930,550),(944,537),(957,550)],'#ffe1ae',4)
    elif kind=='stroke':
        angiogram.dot(c,950,541,30,'#5f9685')
        for sign in (-1,1):
            angiogram.dot(c,950+sign*11,536,3.4,'#e4f2e6')
        access.line(c,[(936,552),(948,555),(962,550+6*(1-cos(t*2*pi))/2)],'#e4f2e6',4)
    else:
        y=539
        for index in range(3):
            x=829+index*121
            angiogram.dot(c,x,y,17,'#659f8d')
            angiogram.dot(c,x,y,7+3*cos(t*3-index),'#d0eddc')
        access.line(c,[(845,y),(933,y)],'#8ebbaa',4)
        access.line(c,[(966,y),(1054,y)],'#8ebbaa',4)


def discharge_indicator(c,t,kind):
    """Identify the action or symptom being highlighted on the home plan."""
    angiogram.block(c,709,501,489,80,14,access.solid('#112e2a'))
    phase=(1-cos(t*2*pi*.65))/2
    if kind in ('medicines','dressing'):
        for index in range(3):
            x=761+index*130
            fill='#d5ebdd' if index==int(t*1.4)%3 else '#689e8f'
            angiogram.block(c,x,520,109,38,19,access.solid(fill))
            if kind=='dressing':
                angiogram.block(c,x+34,525,41,28,8,access.solid('#f3dfb5'))
            else:
                access.line(c,[(x+54,524),(x+54,554)],'#225a50',4)
    elif kind in ('activity','follow-up'):
        for index in range(5):
            x=775+index*87
            y=544+8*sin(t*4-index)
            angiogram.dot(c,x,y,14,'#a7d2be')
            if index:
                access.line(c,[(x-73,544),(x-16,544)],'#6b9f91',5)
    elif kind=='fever':
        angiogram.block(c,765,529,353,22,11,access.solid('#587e75'))
        angiogram.block(c,765,529,162+70*phase,22,11,access.solid('#e2b780'))
        angiogram.dot(c,761,540,24,'#edc68c')
    else:
        angiogram.block(c,754,519,392,48,16,access.solid('#ba8c79'))
        angiogram.block(c,901,523,107,39,13,access.solid('#f5e6c8'))
        if kind=='redness':
            c.drawOval(skia.Rect.MakeXYWH(839,523,60+30*phase,40),access.solid('#985565',210))
        else:
            angiogram.dot(c,1018+19*phase,548,9,'#f0c991')


def planning(c,t):
    if t<5.97:
        clinical(c,'P02',0,t)
        angiogram.block(c,55,183,371,200,20,access.solid('#193d37'))
        access.text(c,'Illustrated echocardiogram',75,230,27,'#e6f3e8')
        beat=(1-cos(t*2*pi*1.08))/2
        for sign in (-1,1):
            cusp=angiogram.art.curve((241+sign*112,307),
                ((241+sign*68,273),(241+sign*35,322),(241+sign*(5+28*beat),293)))
            access.line(c,cusp,'#73a79a',13)
            access.line(c,cusp,'#cbeada',5)
        access.line(c,[(241,365),(241,311)],'#e3cb94',5)
        access.line(c,[(230,325),(241,311),(252,325)],'#e3cb94',5)
        access.rect(c,0,673,1280,47,access.solid('#173b35'))
        access.text(c,'Echo shows how tightly the aortic valve is narrowed',54,705,29,'#e7f4e9')
        return
    if t<11.1:
        c.drawImageRect(route_plate(planning=True),skia.Rect.MakeWH(1280,720),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
        progress=access.smooth((t-5.97)/4.7)
        path=angiogram.art.trace(ROUTE,progress)
        access.line(c,path,'#f3d79a',14)
        x,y=path[-1]
        angiogram.dot(c,x,y,15,'#f3d79a',188)
        angiogram.block(c,888,311,329,241,23,access.solid('#193e37'))
        access.text(c,'Valve fit on CT',912,353,31,'#e6f3e9')
        x,y=1048,443
        for width,height,tone in ((190,138,'#7b9a91'),(163,116,'#a7b9a6'),(133,91,'#284941')):
            c.drawOval(skia.Rect.MakeXYWH(x-width/2,y-height/2,width,height),access.solid(tone))
        marker=404+75*((t-5.97)%2.0)/2.0
        access.line(c,[(970,marker),(1128,marker)],'#d4f3df',5.5)
        access.text(c,'Illustrated annular view',909,527,23,'#c5e7d5')
        access.text(c,'CT assesses both valve anatomy and the access arteries',54,685,29,'#245c50')
        return
    if t<16.5:
        panel(c,'How the Heart Team decides',('Your health and goals',),
              ('The team reviews the findings with you.',))
        focus_rows(c,('Symptoms','Valve and artery anatomy','Overall health','Patient preferences'),
                   (t-11.1)/5.4,y=265,step=85)
    else:
        panel(c,'How the Heart Team decides',('More than one option',),
              ('Surgical valve replacement may','be a better option for some people.'))
        focus_rows(c,('Transcatheter replacement','Surgical valve replacement','Risks and recovery'),
                   (t-16.5)/6.27,y=291,step=102)
    access.text(c,'The decision is tailored to the person',55,672,29,'#2b6456')


def recovery(c,ident,t):
    if ident=='P08':
        title='Recovery in hospital'
        if t<4.9:
            panel(c,title,('Rhythm and groin checks',),('Staff monitor your heart rhythm','and inspect the access site.'))
            access.text(c,'Illustrated rhythm monitor',712,245,31,'#dff2e4')
            rhythm(c,t,715,279,473,157)
            access.text(c,'The team checks the groin site',712,526,28,'#c7e7d8')
        elif t<11.25:
            panel(c,title,('Monitoring for complications',),('The team checks for these risks.','Tell staff about any new symptoms.'))
            progress=(t-4.9)/6.35
            focus_rows(c,('Bleeding','Vessel injury','Stroke','Heart rhythm changes'),progress,y=251,step=69)
            recovery_indicator(c,t,('bleeding','injury','stroke','rhythm')[min(3,int(progress*4))])
        elif t<13.45:
            panel(c,title,('Some need a pacemaker',),('The team uses heart rhythm','checks to guide that decision.'))
            access.text(c,'Illustrated rhythm monitor',712,245,31,'#dff2e4')
            rhythm(c,t,715,279,473,157)
        else:
            panel(c,title,('Recovery time varies',),('Your recovery guides how long','you stay in hospital.'))
            progress=(t-13.45)/3.42
            focus_rows(c,('Observe your progress','Review readiness to go home'),progress,y=291,step=104)
            recovery_indicator(c,t,'observe' if progress<.5 else 'follow-up')
    else:
        title='Your written plan at home'
        if t<7.88:
            panel(c,title,('Ask for written instructions',),('Confirm how your team wants you','to manage recovery at home.'))
            progress=t/7.88
            focus_rows(c,('Medicines','Wound care','Activity and driving','Follow-up'),progress,y=251,step=69)
            discharge_indicator(c,t,('medicines','dressing','activity','follow-up')[min(3,int(progress*4))])
        elif t<11.10:
            panel(c,title,('Mild bruising or soreness',),('This can happen at the groin','access site after TAVI.'))
            access.text(c,'Illustrated groin dressing',711,243,30,'#dff2e4')
            angiogram.block(c,724,282,452,254,36,access.solid('#bb8c78'))
            c.drawOval(skia.Rect.MakeXYWH(814,315,220,159),access.solid('#956279',190))
            angiogram.block(c,845,337,209,100,25,access.solid('#f6e9cc'))
            angiogram.block(c,897,354,104,66,16,access.solid('#fff3db'))
            view=861+156*access.smooth((t-7.88)/2.9)
            access.line(c,[(view,455),(view,489),(view+36,489)],'#ffedc7',7)
            angiogram.dot(c,view+39,489,10,'#fff0d2')
        else:
            panel(c,title,('Call your care team promptly',),('Report a wound that is getting','worse or a new fever.'))
            progress=(t-11.1)/6.37
            focus_rows(c,('Increasing redness or pain','Drainage from the site','Fever'),progress,y=258,step=93)
            discharge_indicator(c,t,('redness','drainage','fever')[min(2,int(progress*3))])
    access.text(c,'Follow your own care team’s advice',55,672,29,'#2b6456')


def clinical(c,ident,p,t):
    if ident=='P04' and p<.64:
        groin_route(c,p/.64,t)
        return
    if ident=='P05' and p<.23:
        prosthetic_top(c,p/.23,t)
        return
    if ident=='P07' and p>=.72:
        groin_closure(c,(p-.72)/.28)
        return
    c.drawImageRect(base(),skia.Rect.MakeWH(1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    if ident in ('P01','P02','P04'):
        if ident=='P04':
            progress=blend(.18,1,access.smooth((p-.64)/.34))
            beat=leaflets(c,t,'stenosis',15*access.smooth((progress-.32)/.13))
            wire=draw_wire(c,progress)
            if p>.81: xray(c,wire)
        else:
            beat=leaflets(c,t,'stenosis')
        if ident!='P04': pump_flow(c,t,beat,False)
        title={'P01':'A new valve through a catheter',
               'P02':'Why the aortic valve narrows',
               'P04':'The wire crosses the narrowed valve'}[ident]
        note={'P01':'Transcatheter aortic valve implantation',
              'P02':'Stiff leaflets leave less room for blood to flow',
              'P04':'From the aorta into the left ventricle'}[ident]
    elif ident=='P05':
        y=blend(263,ANNULUS,access.smooth((p-.24)/.64))
        leaflets(c,t,'stenosis',26 if y+82>=ANNULUS-20 else 13)
        draw_wire(c,1)
        cage(c,y,26,front=False); delivery(c,y,22); cage(c,y,26,front=True)
        title,note='The replacement valve travels compressed','Mounted on a folded balloon and guided over the wire'
    elif ident=='P06':
        opened=access.smooth((p-.07)/.34)
        r=26+103*opened
        collapse=access.smooth((p-.48)/.13)
        retreat=access.smooth((p-.61)/.14)
        y=blend(ANNULUS,70,retreat)
        leaflets(c,t,'stenosis',r-2,opened)
        cage(c,ANNULUS,r,front=False)
        if opened>=.98:
            # Keep the mounted tissue visible as the balloon and wire clear it.
            leaflet_time=.5/1.08+t*max(0,p-.86)/max(p,.86)
            beat=leaflets(c,leaflet_time,'prosthetic')
        if p<.86:
            draw_wire(c,1-access.smooth((p-.75)/.11))
        if p<.75:
            delivery(c,y,blend(22+107*opened,17,collapse))
        if p>=.86:
            pump_flow(c,t,beat,True)
        cage(c,ANNULUS,r,front=True)
        title='The balloon opens the valve frame' if p<.48 else 'The new valve stays in place'
        if p<.48:
            note='The old leaflets are moved aside'
        elif p<.86:
            note='The balloon deflates and the delivery system comes out'
        else:
            note='The new leaflets open and close with each heartbeat'
    else:
        leaflets(c,t,'displaced')
        cage(c,ANNULUS,129,front=False)
        beat=leaflets(c,t,'prosthetic')
        pump_flow(c,t,beat,True)
        cage(c,ANNULUS,129,front=True)
        title='Checking the new valve' if ident=='P07' else 'What TAVI changes'
        note='Imaging checks blood flow through and around the frame'
        if ident=='P07':
            result_check(c,p,t)
            if p>=.51:
                note='The team also checks the heart rhythm'
    angiogram.header(c,title,'AORTIC VALVE')
    access.text(c,'Aorta',1021,225,31,'#235d50')
    access.text(c,'Left ventricle',990,617,31,'#235d50')
    access.rect(c,0,673,1280,47,access.solid('#173b35'))
    access.text(c,note,54,705,29,'#dceddf',access.REGULAR)

EMERGENCY_BEATS=(
    ('Heavy bleeding',('or bleeding that will not stop',),'band'),
    ('Severe chest pain',('or sudden trouble breathing',),'pulse'),
    ('Possible signs of stroke',('Sudden face droop, arm weakness or','trouble speaking'),'call'),
)
EMERGENCY_MARKS=(0.,5.6,10.685,16.167)

def draw(c,ident,p,t):
    if ident=='P12':
        angiogram.clinical_credits(c,'AORTIC VALVE',(
            'ACC and AHA · Valvular heart disease guideline',
            'SCAI · Transcatheter valve delivery guidance',
            'Guy’s and St Thomas’ NHS Foundation Trust · TAVI procedure'),
            'Recovery and follow-up after TAVI')
        return
    if ident=='P03':
        planning(c,t)
        return
    if ident in ('P08','P09'):
        recovery(c,ident,t)
        return
    if ident!='P10':
        clinical(c,ident,p,t)
        return
    index=min(len(EMERGENCY_BEATS)-1,bisect_right(EMERGENCY_MARKS,t)-1)
    start,end=EMERGENCY_MARKS[index:index+2]
    progress=min(1,(t-start)/(end-start))
    heading,lines,icon=EMERGENCY_BEATS[index]
    restenosis.card(c,'When to get emergency help',heading,lines,icon,progress,t,topic='TAVI PROCEDURE')
    access.rect(c,0,632,1280,88,access.solid('#613239'))
    access.text(c,'Call your local emergency number',55,688,34,'#fff3e8')

def render():
    ep=SERIES/'episode-18'
    visual=ep/'visuals'; visual.mkdir(exist_ok=True)
    timeline=json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-tavi-film.mp4'
        tmp=visual/f'{ident}-tavi-film.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'tavi-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
