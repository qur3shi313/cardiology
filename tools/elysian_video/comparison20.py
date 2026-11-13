"""Episode 20: matched anatomy, recovery, and the shared treatment decision."""

from functools import lru_cache
from math import cos, pi, sin

import skia

from . import access, angiogram, planning17 as planning, valve_implant as valve


SCENES = ('P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07')
TOPIC = 'HEART VALVE OPTIONS'
GREEN, CREAM, WHITE = '#214c43', '#e8f2e9', '#edf8ed'
FILTER = skia.SamplingOptions(skia.FilterMode.kLinear)


def header(canvas, title):
    access.rect(canvas,0,0,1280,148,access.solid(CREAM))
    angiogram.header(canvas,title,TOPIC)


def footer(canvas, detail):
    access.rect(canvas,0,653,1280,67,access.solid('#173b35'))
    access.text(canvas,detail,55,693,32,WHITE)


def panel(canvas, title, lead, lines):
    planning.panel(canvas,title,lead,lines)
    header(canvas,title)


def root(canvas):
    canvas.drawImageRect(valve.base(),skia.Rect.MakeWH(1280,720),FILTER)


def surgical_tissue(canvas,time):
    x,y = valve.CX,valve.ANNULUS
    canvas.drawOval(skia.Rect.MakeXYWH(x-148,y-24,296,48),access.solid('#557970'))
    canvas.drawOval(skia.Rect.MakeXYWH(x-131,y-15,262,30),access.solid('#b78e82'))
    beat=valve.leaflets(canvas,time,'prosthetic')
    valve.pump_flow(canvas,time,beat,True)
    for index in range(9):
        mark=x-126+31.5*index
        access.line(canvas,[(mark-4,y+14),(mark+4,y+9)],'#f1d9ad',3.5)


def transcatheter_tissue(canvas,time):
    valve.leaflets(canvas,time,'displaced')
    valve.cage(canvas,valve.ANNULUS,129,front=False)
    beat=valve.leaflets(canvas,time,'prosthetic')
    valve.pump_flow(canvas,time,beat,True)
    valve.cage(canvas,valve.ANNULUS,129,front=True)


def opening(canvas,time):
    if time < 2.55:
        root(canvas)
        beat=valve.leaflets(canvas,time,'stenosis')
        valve.pump_flow(canvas,time,beat,False)
        footer(canvas,'One narrowed aortic valve')
        return
    access.rect(canvas,0,0,1280,720,access.solid(CREAM))
    for x, name, draw in ((36,'TAVI',transcatheter_tissue),(654,'Surgical replacement',surgical_tissue)):
        box=skia.Rect.MakeXYWH(x,211,590,414)
        canvas.save()
        canvas.clipRRect(skia.RRect.MakeRectXY(box,19,19),doAntiAlias=True)
        canvas.translate(x-102,121)
        canvas.scale(.625,.72)
        root(canvas)
        draw(canvas,time)
        canvas.restore()
        access.text(canvas,name,x+16,190,35,GREEN)
    header(canvas,'Two routes to a new aortic valve')
    footer(canvas,'The Heart Team weighs how each option fits the person' if time >= 9.95
           else 'Both routes replace the same valve and restore forward flow')


def catheter_option(canvas,time):
    if time < 4.95:
        root(canvas)
        beat=valve.leaflets(canvas,time,'stenosis')
        valve.pump_flow(canvas,time,beat,False)
        header(canvas,'Catheter-based valve replacement')
        footer(canvas,'TAVI means transcatheter aortic valve implantation')
    elif time < 10.67:
        valve.groin_route(canvas,(time-4.95)/5.72,time)
        header(canvas,'One common route is through a groin artery')
        footer(canvas,'The team guides a wire toward the heart from the femoral artery')
    elif time < 13.1:
        advance=access.smooth((time-10.67)/2.35)
        valve.clinical(canvas,'P05',.24+.64*advance,time)
        header(canvas,'The compressed valve follows the guidewire')
        footer(canvas,'The folded valve reaches the narrowed opening')
    elif time < 18.70:
        progress=.07+.79*(time-13.1)/5.6
        valve.clinical(canvas,'P06',progress,time)
        header(canvas,'The frame expands' if progress<.30 else 'The new frame holds the old leaflets aside')
        footer(canvas,'The frame opens inside the narrowed valve' if progress<.48
               else 'The balloon deflates and the delivery system comes out')
    else:
        root(canvas)
        transcatheter_tissue(canvas,time)
        header(canvas,'The new leaflets control blood flow')
        footer(canvas,'The implanted frame stays in place')


def tissue_top(canvas,x,y,time):
    angiogram.dot(canvas,x,y,155,'#6a8880')
    angiogram.dot(canvas,x,y,144,'#b3c6ac')
    angiogram.dot(canvas,x,y,128,'#83596a')
    beat=(1-cos(time*2*pi*1.08))/2
    for index in range(3):
        theta=2*pi*index/3-pi/2
        a=(x+108*cos(theta-.9),y+108*sin(theta-.9))
        b=(x+108*cos(theta+.9),y+108*sin(theta+.9))
        attach=(x+124*cos(theta),y+124*sin(theta))
        free=(x+72*beat*cos(theta),y+72*beat*sin(theta))
        canvas.drawPath(access.path([a,attach,b,free],True),
                        access.grad(*attach,x,y,['#edd9b2','#a76d7c']))
        access.line(canvas,[a,free,b],'#f2d7b4',4)


def mechanical_top(canvas,x,y,time):
    angiogram.dot(canvas,x,y,154,'#819d91')
    angiogram.dot(canvas,x,y,143,'#c8d5bc')
    angiogram.dot(canvas,x,y,130,'#405c55')
    angiogram.dot(canvas,x,y,119,'#142e2c')
    beat=(1-cos(time*2*pi*1.08))/2
    clip=skia.Path()
    clip.addCircle(x,y,118)
    canvas.save()
    canvas.clipPath(clip,doAntiAlias=True)
    for side in (-1,1):
        hinge=x+side*80
        edge=x+side*5
        outer=[(x+side*118,y-18),(x+side*115,y+64),(x+side*60,y+113),
               (edge,y+91),(edge,y-91),(x+side*60,y-113)]
        stretch=1-.64*beat
        projected=[(hinge+(px-hinge)*stretch,py) for px,py in outer]
        canvas.drawPath(access.path(projected,True),access.grad(x-118,y-92,x+100,y+103,['#8fa6a0','#45615c','#698580']))
        access.line(canvas,projected+[projected[0]],'#dae4d5',3)
        angiogram.dot(canvas,hinge,y,7,'#d4dfca')
    canvas.restore()


def surgical_option(canvas,time):
    if time < 9.72:
        root(canvas)
        if time < 4.15:
            beat=valve.leaflets(canvas,time,'stenosis')
            valve.pump_flow(canvas,time,beat,False)
            caption='The original valve is narrowed'
        elif time < 6.55:
            opacity=int(255*(1-access.smooth((time-4.15)/2.4)))
            canvas.saveLayer(skia.Rect.MakeWH(1280,720),skia.Paint(Alphaf=opacity/255))
            valve.leaflets(canvas,time,'stenosis')
            canvas.restore()
            caption='The diseased leaflets are typically removed'
        else:
            surgical_tissue(canvas,time)
            caption='A replacement valve is placed at the same opening'
        header(canvas,'Surgical aortic valve replacement')
        footer(canvas,caption)
        return
    access.rect(canvas,0,0,1280,720,access.solid(CREAM))
    header(canvas,'Surgical valves can be tissue or mechanical')
    tissue=9.72<=time<14.87
    for x,name,draw,active in ((69,'Tissue valve',tissue_top,tissue),(654,'Mechanical valve',mechanical_top,not tissue)):
        shade='#28584b' if active else '#25463e'
        angiogram.block(canvas,x,190,552,423,25,access.solid(shade))
        access.text(canvas,name,x+32,244,38,WHITE)
        draw(canvas,x+276,411,time)
    footer(canvas,'The team discusses the available choices and long-term priorities')


@lru_cache(maxsize=1)
def coronary_geometry():
    art=angiogram.art
    def xy(point):
        return 626+(point[0]-289)*1.82,186+(point[1]-110)*1.12
    muscle=list(map(xy,art.MYOCARDIUM))
    aorta=list(map(xy,art.AORTA))
    lad=list(map(xy,art.LAD))
    main=list(map(xy,art.LEFT_MAIN))
    narrowing_index=int((len(lad)-1)*.44)
    join_index=int((len(lad)-1)*.76)
    source=aorta[len(aorta)//3]
    target=lad[join_index]
    graft=art.curve(source,((source[0]+232,source[1]+18),(target[0]+257,target[1]-12),target))
    return muscle,aorta,main,lad,narrowing_index,join_index,graft


def coronary_bridge(canvas,time,*,transition):
    muscle,aorta,main,lad,narrowing,join,graft=coronary_geometry()
    access.rect(canvas,0,0,1280,720,access.solid(CREAM))
    canvas.drawPath(access.path(muscle,True),access.grad(387,193,845,621,['#d69a8e','#af6471','#743e55']))
    access.line(canvas,aorta,'#945267',39)
    access.line(canvas,aorta,'#e0a195',25)
    access.line(canvas,main+lad[1:],'#743b4d',22)
    access.line(canvas,main+lad[1:],'#dc9384',12)
    px,py=lad[narrowing]
    angiogram.dot(canvas,px,py,12,'#d9a26e')
    access.line(canvas,[(px,py),(411,py+6),(235,py+6)],GREEN,3)
    access.text(canvas,'Narrowing',62,py+16,33,GREEN)
    progress=access.smooth((time-.42)/3.25)
    route=angiogram.art.trace(graft,progress)
    access.line(canvas,route,'#33675a',29)
    access.line(canvas,route,'#91c5ab',17)
    if progress>.97:
        x,y=lad[join]
        angiogram.dot(canvas,x,y,10,'#d6efcf')
        access.line(canvas,[(x,y),(942,y+14),(1166,y+14)],GREEN,3)
        access.text(canvas,'Joins beyond the narrowing',920,y+52,25,GREEN)
        full_route=graft+tuple(lad[join+1:])
        for index in range(5):
            position=(time*.31+index/5)%1
            trail=[angiogram.art.trace(full_route,position+.092*step/8)[-1] for step in range(9)
                   if position+.092*step/8 <= 1]
            access.line(canvas,trail,'#e7efca',12,230)
            angiogram.dot(canvas,*trail[-1],7,'#f3f0c6',239)
    header(canvas,'Next series: cardiac surgery' if transition else 'When bypass is also being considered')
    footer(canvas,'An illustrated graft carries blood around the narrowing' if transition
           else 'A need for coronary bypass can influence the valve treatment plan')


def anatomy_option(canvas,time):
    if time < 5.08:
        planning.root_scan(canvas,5.+time)
        return
    if time < 8.52:
        planning.pathway(canvas,9.9+(time-5.08)*1.3)
        footer(canvas,'The team also checks whether the arteries can carry a catheter')
        return
    if time < 12.70:
        panel(canvas,'Other heart conditions can matter','What else needs treatment?',
              ('The team considers other', 'valve or coronary problems'))
        planning.ring(canvas,717,409,105,time*.82)
        planning.tile(canvas,869,301,'Coronary disease',0,time)
        planning.tile(canvas,869,431,'Another valve',1,time)
        return
    coronary_bridge(canvas,time-12.70,transition=False)


def walking(canvas,x,y,time):
    step=sin(time*5)
    c=canvas
    angiogram.dot(c,x,y-100,32,'#d5bc9d')
    access.line(c,[(x,y-64),(x+11,y+25)],'#a9cbb4',37)
    for side in (-1,1):
        knee=(x+side*35+side*25*step,y+79)
        heel=(knee[0]+side*13,y+119-14*max(0,side*step))
        access.line(c,[(x+11,y+19),knee,heel],'#a1c6b0',14)
        access.line(c,[(x+5,y-50),(x+side*41,y-9+side*22*step)],'#c2d9bd',11)


def recovery(canvas,time):
    if time < 10.0:
        surgical=time>=5.1
        panel(canvas,'Recovery differs from person to person',
              'After surgical treatment' if surgical else 'After catheter treatment',
              ('Surgery may still suit','some people even with','a longer recovery') if surgical else
              ('Early recovery is often shorter','after catheter treatment'))
        walking(canvas,678+(time*88)%370,411,time)
        access.line(canvas,[(565,550),(1170,550)],'#649380',4)
        return
    if time < 17.59:
        panel(canvas,'Recovery differs from person to person','Discuss individual risks',
              ('Bleeding, stroke or changes', 'in heart rhythm are possible'))
        valve.rhythm(canvas,time,573,282,582,188)
        access.text(canvas,'Illustrated rhythm tracing',578,547,36,WHITE)
        return
    panel(canvas,'Recovery differs from person to person','Support at home',
          ('Ask what help could be useful','during your own recovery'))
    access.line(canvas,[(637,405),(867,241),(1097,405)],'#b5d0b8',20)
    angiogram.block(canvas,682,397,372,159,19,access.solid('#366a59'))
    glow = access.grad(682,405,1054,550,['#4d7e68','#9bb49a','#4d7e68'])
    glow.setAlpha(int(102+70*sin(time*2.8)))
    angiogram.block(canvas,692,407,352,139,15,glow)
    planning.person(canvas,779,450,'#a9c5af',.66,22*sin(time*1.8))
    planning.person(canvas,951,450,'#a5c7b0',.66,22*cos(time*1.8))


def future(canvas,time):
    if time < 8.31:
        panel(canvas,'Thinking beyond the first procedure','How long may it work?',
              ('Valve durability, overall health','and future care all matter'))
        access.line(canvas,[(601,435),(1140,435)],'#8fb7a1',12)
        for index,(x,label) in enumerate(((619,'First valve'),(853,'Follow-up'),(1119,'Future care'))):
            phase=(time*.7+index/3)%1
            angiogram.dot(canvas,x,435,27+13*phase,'#a9d0b0',round(181*(1-phase)))
            angiogram.dot(canvas,x,435,14,'#ecd2a0')
            planning.scale_label(canvas,label,x-51,516,25,119,WHITE)
        glow=604+(time*102)%532
        access.line(canvas,[(glow-23,435),(glow+23,435)],'#e0edcf',7)
        return
    if time < 13.32:
        panel(canvas,'Thinking beyond the first procedure','If more treatment is needed',
              ('The first valve can affect','the next options'))
        planning.ring(canvas,735,400,111,time*.91)
        planning.tile(canvas,872,302,'Prior valve',0,time)
        planning.tile(canvas,872,447,'Reassess options',1,time)
        return
    panel(canvas,'Thinking beyond the first procedure','Compare the whole course',
          ('The team weighs future care','alongside the first treatment'))
    planning.tile(canvas,565,284,'First recovery',0,time)
    planning.tile(canvas,880,425,'Future care',1,time)
    access.line(canvas,[(803,429),(875,381),(946,363)],'#a3c3aa',4)


def decision(canvas,time):
    if time >= 10.08:
        coronary_bridge(canvas,time-10.08,transition=True)
        return
    patient_turn=time>=5.33
    panel(canvas,'A shared treatment decision','What matters to you?' if patient_turn else 'Why this recommendation?',
          ('Bring your goals, preferences','and questions to the discussion') if patient_turn else
          ('The Heart Team explains','the evidence and the options'))
    planning.person(canvas,700,382,'#91b8a2',1.12,31*sin(time*1.72))
    planning.person(canvas,1006,381,'#a7c5ad',1.12,31*cos(time*1.65))
    angiogram.block(canvas,577,495,607,67,16,access.solid('#81a994'))
    planning.tile(canvas,721,238,'Patient priorities' if patient_turn else 'Options and evidence',0,time)


DRAW = {'P01':opening,'P02':catheter_option,'P03':surgical_option,'P04':anatomy_option,
        'P05':recovery,'P06':future,'P07':decision}


def draw(canvas, ident, time):
    DRAW[ident](canvas,time)
