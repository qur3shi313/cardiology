"""Original balloon-expandable transcatheter valve sequence and recovery film."""
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

@lru_cache(maxsize=1)
def route_plate():
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
    access.line(c,SHEATH,'#24564f',16)
    access.line(c,SHEATH,'#9bcbb9',9)
    access.line(c,[(412,609),(419,603)],'#357469',21)
    angiogram.header(c,'The femoral route to the aortic valve','AORTIC VALVE')
    access.text(c,'Right femoral artery',62,557,31,'#235d50')
    access.text(c,'Sheath stays in the groin',62,594,27,'#235d50',access.REGULAR)
    access.line(c,[(326,568),(389,568),(438,581)],'#245c50',3)
    access.text(c,'Aortic arch',920,240,31,'#235d50')
    access.line(c,[(906,233),(822,233),(649,229)],'#245c50',3)
    access.text(c,'Illustrated route under X-ray guidance',54,686,27,'#245c50')
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
    cover=access.smooth((p-.53)/.36)
    if cover:
        y=blend(289,405,cover)
        angiogram.block(c,534,y-36,208,72,22,access.solid('#f1e8d3'))
        angiogram.block(c,601,y-26,74,52,12,access.solid('#fff6df'))
    angiogram.header(c,'The groin access site is closed','AORTIC VALVE',True)
    access.text(c,'Access equipment comes out' if p<.55 else 'Staff dress and check the site',
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
        if ident=='P07': result_check(c,p,t)
    angiogram.header(c,title,'AORTIC VALVE')
    access.text(c,'Aorta',1021,225,31,'#235d50')
    access.text(c,'Left ventricle',990,617,31,'#235d50')
    access.rect(c,0,673,1280,47,access.solid('#173b35'))
    access.text(c,note,54,705,29,'#dceddf',access.REGULAR)

TEXT={
 'P03':('How the Heart Team decides',(
        ('Echocardiography',('Checks how tightly the valve is narrowed',),'pulse'),
        ('CT helps plan the approach',('See where the valve would sit and','how the device might reach it'),'check'),
        ('The team reviews options with you',('Anatomy, health and preferences matter',),'list'))),
 'P08':('Recovery in hospital',(
        ('Heart rhythm and access site',('Staff monitor the rhythm and groin site',),'pulse'),
        ('Recovery time varies',('A pacemaker is needed in some cases',),'clock'))),
 'P09':('Your written plan at home',(
        ('Medicines, wound care and activity',('Follow your team’s instructions',),'list'),
        ('Contact your team promptly',('Increasing redness, pain, drainage or fever','need advice'),'call'))),
 'P10':('When to get emergency help',(
        ('Heavy or persistent bleeding',('Call local emergency services',),'band'),
        ('Chest pain or breathing trouble',('Call local emergency services',),'pulse'),
        ('Possible signs of stroke',('Sudden face droop, arm weakness or','trouble speaking'),'call'))),
 'P12':('Clinical sources',(
        ('Heart valve treatment',('ESC and EACTS clinical guidance',),'vessel'),
        ('Patient care and recovery',('American Heart Association and NHS',),'list'))),
}

def draw(c,ident,p,t):
    if ident not in TEXT:
        clinical(c,ident,p,t)
        return
    title,beats=TEXT[ident]
    i=min(len(beats)-1,int(p*len(beats)))
    heading,lines,icon=beats[i]
    restenosis.card(c,title,heading,lines,icon,p*len(beats)-i,t)

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
