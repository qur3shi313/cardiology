"""Original balloon-expandable transcatheter valve sequence and recovery film."""
from functools import lru_cache
from math import sin, cos, pi
import json

import skia

from . import access, angiogram, restenosis
from .__main__ import ROOT, SERIES, FPS, WIDTH, HEIGHT
from .encode import encode_scene

CX,ANNULUS=655,443
LEFT=angiogram.art.curve((487,163),((500,244),(460,299),(450,342)),
                         ((419,384),(453,411),(493,438)),
                         ((467,500),(364,554),(275,673)))
RIGHT=tuple((2*CX-x,y) for x,y in LEFT)

def blend(a,b,p):
    return a+(b-a)*p

def wire_path():
    return angiogram.art.curve((933,156),((825,179),(748,222),(701,308)),
        ((643,366),(639,459),(656,502)),((673,542),(720,607),(666,647)))

WIRE=wire_path()

def groin_route(c,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e4efe6'))
    # Fully covered torso locator. The chart is anatomical, not to scale.
    body=access.path([(526,185),(584,154),(705,154),(759,185),(811,292),(801,402),
        (844,522),(817,640),(716,665),(649,603),(590,665),(486,644),(459,527),(505,410),(482,287)],True)
    c.drawPath(body,access.grad(470,170,841,658,['#a7bfb4','#739a8d','#547c72']))
    arterial=angiogram.art.curve((564,579),((560,551),(578,530),(628,492)),
      ((659,462),(644,422),(646,377)),((647,327),(633,264),(676,245)),
      ((734,216),(757,274),(710,321)),((694,340),(670,351),(666,379)))
    access.line(c,arterial,'#8f495a',28)
    access.line(c,arterial,'#d09588',16)
    progress=access.smooth((p-.03)/.88)
    visible=angiogram.art.trace(arterial,progress)
    # Highlight the established route while keeping the catheter tip distinct.
    for index in range(6):
        phase=(t*.42+index/6)%1
        if phase<progress:
            point=int(phase*(len(arterial)-1))
            start=max(0,point-3)
            access.line(c,arterial[start:point+1],'#eac298',19,175)
    access.line(c,visible,'#624c32',8)
    access.line(c,visible,'#f9e1a6',4.3)
    if visible:
        x,y=visible[-1]
        angiogram.dot(c,x,y,8,'#fff3d0')
    angiogram.header(c,'The femoral route to the aortic valve','AORTIC VALVE')
    access.text(c,'Femoral artery',83,598,32,'#235d50')
    access.line(c,[(290,590),(508,590),(564,579)],'#245c50',3)
    access.text(c,'Aorta',927,264,33,'#235d50')
    access.line(c,[(911,259),(814,259),(732,244)],'#245c50',3)
    access.text(c,'Illustrated route under X-ray guidance',54,686,29,'#245c50')

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

def leaflets(c,t,kind,occupied=0):
    beat=(1-cos(t*2*pi*1.08))/2
    for side in (-1,1):
        old=kind in ('stenosis','displaced')
        height=(38 if old else 72)*beat
        gap=(39 if old else 90)*beat
        if kind=='displaced':
            gap,height=131,105
        else:
            gap=max(gap,occupied+1 if occupied else 0)
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
    shaft=angiogram.art.curve((934,154),((806,168),(749,238),(CX,y-70)))
    access.line(c,shaft,'#456c73',19)
    access.line(c,shaft,'#88b8b9',12)
    access.line(c,shaft,'#d5ece1',3)
    c.drawRoundRect(skia.Rect.MakeXYWH(CX-r,y-72,2*r,151),
                    min(r,31),min(r,31),access.solid('#80bfbb',180))
    access.line(c,[(CX,y-70),(CX,y+72)],'#477e88',5)
    for pos in (y-53,y+53):
        access.line(c,[(CX-4,pos),(CX+4,pos)],'#e6ce96',4)

def pump_flow(c,t,beat,wide):
    if beat<.35:return
    for i in range(12):
        y=668-(i*48+t*245)%484
        x=CX+((i*13)%91-44)*(1.25 if wide else .52)
        access.line(c,[(x,y+13),(x,y-11)],'#d1e6cc',4.5,164)
        access.line(c,[(x-6,y-3),(x,y-11),(x+6,y-3)],'#e5efd3',3.1,184)

def clinical(c,ident,p,t):
    if ident=='P04' and p<.64:
        groin_route(c,p/.64,t)
        return
    if ident=='P05' and p<.23:
        prosthetic_top(c,p/.23,t)
        return
    c.drawImageRect(base(),skia.Rect.MakeWH(1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    if ident in ('P01','P02','P04'):
        if ident=='P04':
            wire=angiogram.art.trace(WIRE,access.smooth((p-.64)/.36))
            access.line(c,wire,'#8b683d',7)
            access.line(c,wire,'#f9dda4',3.8)
        beat=leaflets(c,t,'stenosis',15 if ident=='P04' else 0)
        if ident!='P04': pump_flow(c,t,beat,False)
        title={'P01':'A new valve through a catheter',
               'P02':'Why the aortic valve narrows',
               'P04':'The wire crosses the narrowed valve'}[ident]
        note={'P01':'Transcatheter aortic valve implantation',
              'P02':'Stiff leaflets leave less room for blood to flow',
              'P04':'From the aorta into the left ventricle'}[ident]
    elif ident=='P05':
        y=blend(274,ANNULUS,access.smooth((p-.29)/.63))
        leaflets(c,t,'stenosis',22 if p>.75 else 0)
        access.line(c,WIRE,'#916d46',7)
        access.line(c,WIRE,'#f2d19b',3.8)
        cage(c,y,26,front=False); delivery(c,y,22); cage(c,y,26,front=True)
        title,note='The replacement valve travels compressed','Mounted on a folded balloon and guided over the wire'
    elif ident=='P06':
        opened=access.smooth((p-.05)/.28)
        r=26+103*opened
        collapse=access.smooth((p-.48)/.17)
        retreat=access.smooth((p-.64)/.17)
        y=blend(ANNULUS,177,retreat)
        if opened<.995:
            leaflets(c,t,'stenosis',r-3)
        else:
            leaflets(c,t,'displaced')
        cage(c,ANNULUS,r,front=False)
        if p<.88:
            wire=angiogram.art.trace(WIRE,1-access.smooth((p-.74)/.14))
            access.line(c,wire,'#916d46',7)
            access.line(c,wire,'#f2d19b',3.8)
        if p<.81:
            delivery(c,y,blend(22+107*opened,17,collapse))
        if p>.88:
            beat=leaflets(c,t,'prosthetic')
            pump_flow(c,t,beat,True)
        cage(c,ANNULUS,r,front=True)
        title='The balloon opens the valve frame' if p<.46 else 'The new valve stays in place'
        note='The old leaflets are moved aside' if p<.46 else 'The balloon deflates and the delivery system comes out'
    else:
        leaflets(c,t,'displaced')
        cage(c,ANNULUS,129,front=False)
        beat=leaflets(c,t,'prosthetic')
        pump_flow(c,t,beat,True)
        cage(c,ANNULUS,129,front=True)
        title='Checking the new valve' if ident=='P07' else 'What TAVI changes'
        note='Imaging checks blood flow through and around the frame'
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
