"""Cue-aligned motion and anatomy for Episode 14, heart attack and emergency PCI."""

from importlib.util import module_from_spec, spec_from_file_location
from math import cos, exp, pi, sin

import skia

from . import access, angiogram, emergency, stent as art
from .__main__ import SERIES


_care_spec = spec_from_file_location('recovery_motion', SERIES / 'episode-10' / 'render_recovery_revisions.py')
care = module_from_spec(_care_spec)
_care_spec.loader.exec_module(care)

TOPIC = 'HEART ATTACK AND PCI'


def card_text(c, title, heading, lines, *, footer=None):
    angiogram.header(c, title, TOPIC)
    access.text(c, heading, 55, 325, 39, '#174c42')
    for index, line in enumerate(lines):
        access.text(c, line, 55, 383 + index * 44, 31, '#285c51', access.REGULAR)
    if footer:
        access.text(c, footer, 55, 674, 29, '#24584c')


def urgent_footer(c):
    access.rect(c, 0, 631, 1280, 89, access.solid('#613239'))
    access.text(c, 'If a heart attack is suspected, call your local emergency number',
                55, 686, 33, '#fff6ee')


def clot_flow(c, t):
    """Particles slow proximal to the same obstruction and never cross it."""
    c.save()
    c.clipPath(art.artery_plate(0.)[1], doAntiAlias=True)
    for index in range(33):
        travel = (t * (.34 + (index % 5) * .025) + index * .137) % 1
        x = -80 + 665 * (1 - (1 - travel) ** 1.34)
        y = art.center(x) + ((index * 31) % 155) - 77
        alpha = round(195 * min(1., (1 - travel) * 9))
        c.drawOval(skia.Rect.MakeXYWH(x - 18, y - 7, 36, 14), access.solid('#eea18e', alpha))
        c.drawOval(skia.Rect.MakeXYWH(x - 9, y - 3, 17, 6), access.solid('#ad515d', alpha))
    c.restore()


def heart_territory(c, t):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e7f0e8'))
    model = angiogram.art
    zoom = 1.17 + .08 * min(t / 6.7, 1)

    def xy(point):
        return 664 + (point[0] - 323) * zoom, 188 + (point[1] - 121) * zoom

    muscle = access.path(list(map(xy, model.MYOCARDIUM)), True)
    c.drawPath(muscle, access.grad(447, 251, 902, 663, ['#d58b87', '#aa6273', '#733f55']))
    branch = list(map(xy, model.LAD))
    cut = int((len(branch) - 1) * .43)
    sx, sy = branch[cut]
    c.save()
    c.clipPath(muscle, doAntiAlias=True)
    distal = [(sx, sy), xy((309, 374)), xy((335, 459)), xy((383, 498)), xy((434, 457)), xy((424, 371))]
    c.drawPath(access.path(distal, True), access.grad(sx, sy, sx+130, sy+200, ['#875466', '#643f57']))
    c.restore()
    access.line(c, list(map(xy, model.AORTA)), '#945266', 30)
    access.line(c, list(map(xy, model.AORTA)), '#e1a092', 19)
    for vessel in (model.RCA, model.LEFT_MAIN, model.LCX):
        access.line(c, list(map(xy, vessel)), '#743747', 10)
    access.line(c, branch, '#5e3549', 15)
    access.line(c, branch[:cut+1], '#da897f', 9)
    upstream = list(map(xy, model.LEFT_MAIN)) + branch[1:cut+1]
    for index in range(5):
        step = (t * .63 + index / 5) % 1
        x, y = model.trace(upstream, step)[-1]
        angiogram.dot(c, x, y, 6.8, '#ffe1ba', round(225 * min(1., (1-step) * 8)))
    angiogram.dot(c, sx, sy, 12, '#6c283e')
    access.line(c, [(sx, sy), (sx + 145, sy - 57), (1047, sy - 57)], '#24574b', 3)
    access.text(c, 'Blockage', 1011, sy - 72, 30, '#22564b')
    if t >= 1.2:
        access.rect(c,0,0,1280,147,access.solid('#e7f0e8'))
        angiogram.header(c, 'A blocked artery needs help fast', TOPIC)
    access.text(c, 'Less oxygen reaches the muscle beyond the blockage', 55, 674, 31, '#23574a')


def opening(c, t):
    if 2.9 <= t < 11.8:
        heart_territory(c, t - 2.9)
        return
    emergency.restore_culprit_flow(c, 0.)
    clot_flow(c, t)
    access.rect(c, 0, 0, 1280, 156, access.solid('#e6f0e9'))
    access.rect(c, 0, 641, 1280, 79, access.solid('#e6f0e9'))
    if t >= 11.8:
        angiogram.header(c, 'A blocked artery needs help fast', TOPIC)
        detail = 'Emergency care can help restore blood flow'
    else:
        detail = 'A clot can stop flow in a coronary artery'
    access.text(c, detail, 55, 674, 31, '#23574a')


def warning_person(c, t, second):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e7f1e9'))
    angiogram.block(c, 525, 175, 700, 435, 29, access.solid('#254d45'))
    sway = 38 * sin(t * .76)
    x = 860 + sway
    person = [(x-55,316),(x-117,345),(x-157,526),(x-121,554),(x-82,462),
              (x-76,587),(x+77,587),(x+86,462),(x+122,554),(x+157,526),
              (x+115,345),(x+58,316)]
    c.drawPath(access.path(person,True),access.grad(x-120,325,x+130,588,['#9cc2b2','#619987']))
    angiogram.dot(c,x,271,44,'#b2d5c0')
    if second:
        anchors=((x-105,433),(x+28,300),(x+13,491))
        focus=anchors[min(2,int(t/2.8))]
    else:
        focus=(x-12,391)
    for index in range(3):
        phase=(t*1.05+index/3)%1
        c.drawCircle(*focus,17+77*phase,access.solid('#f3b49f',round(137*(1-phase))))
    angiogram.dot(c,*focus,13,'#f9c8aa',232)
    if second:
        card_text(c,'Recognising a possible heart attack','Other warning signs',
                  ('Sweating, nausea or discomfort','in the arm, back or jaw'))
    else:
        card_text(c,'Recognising a possible heart attack','Chest pressure',
                  ('Shortness of breath can happen','with or without chest discomfort'))
    urgent_footer(c)


def call_help(c, t):
    access.rect(c,0,0,1280,720,access.solid('#e7f1e9'))
    angiogram.block(c,525,175,700,435,29,access.solid('#254d45'))
    x = 840+55*sin(t*.61)
    angiogram.block(c,x-96,208,192,354,38,access.solid('#83b39e'))
    angiogram.block(c,x-81,228,162,306,27,access.solid('#153a32'))
    for index in range(4):
        phase=(t*.9+index/4)%1
        c.drawCircle(x,377,28+110*phase,access.solid('#a9e6be',round(98*(1-phase))))
    angiogram.dot(c,x,377,24,'#c9f0cf')
    heading = 'Emergency responders' if t>=5.55 else 'Get emergency help'
    details = ('They can assess you','and coordinate hospital care') if t>=5.55 else ('Symptoms vary from person','to person')
    card_text(c,'Recognising a possible heart attack',heading,details)
    urgent_footer(c)


def symptoms(c, t):
    if t >= 13.02:
        call_help(c,t-13.02)
    elif t >= 4.74:
        warning_person(c,t-4.74,True)
    else:
        warning_person(c,t,False)


def ecg(c, t, *, recovery=False, urgent=False):
    access.rect(c,0,0,1280,720,access.solid('#e7f1e9'))
    angiogram.block(c,520,173,712,444,27,access.solid('#285247'))
    angiogram.block(c,544,194,664,392,21,access.solid('#143a33'))
    for y in range(295,530,47):
        access.line(c,[(568,y),(1183,y)],'#8bb9a7',1.8,109)
    for x in range(568,1184,56):
        access.line(c,[(x,282),(x,541)],'#8bb9a7',1.8,109)
    points=[]
    for index in range(143):
        x=571+4.25*index
        phase=(t*1.36+index/43)%1
        rise=114*max(0,1-abs(phase-.29)/.071)
        dip=43*max(0,1-abs(phase-.43)/.082)
        points.append((x,419-rise+dip))
    c.drawPath(access.path([(571,539),*points,(1175,539)],True),access.solid('#60a987',119))
    access.line(c,points,'#92cfa9',10)
    access.line(c,points,'#e3f9d9',3.4)
    access.text(c,'Illustrated heart tracing',568,257,31,'#e6f6e7')
    if recovery:
        card_text(c,'Recovery and prevention','Monitoring in hospital',
                  ('Ask what your tests showed', 'and what comes next'))
    elif urgent:
        card_text(c,'Early emergency assessment','An urgent treatment plan',
                  ('A pattern on the ECG can','help guide the next step'))
    else:
        card_text(c,'Early emergency assessment','Electrocardiogram (ECG)',
                  ('Records the heart’s','electrical activity'))


def troponin(c,t):
    access.rect(c,0,0,1280,720,access.solid('#e7f1e9'))
    angiogram.block(c,520,173,712,444,27,access.solid('#285247'))
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(520,173,712,444),27,27),doAntiAlias=True)
    x=640+61*t
    c.translate(x,386)
    c.rotate(-24+9*t)
    angiogram.block(c,-137,-52,397,104,49,access.solid('#bddfd1'))
    angiogram.block(c,-117,-35,354,70,34,access.solid('#f0ded5'))
    angiogram.block(c,28,-35,208,70,33,access.solid('#a85764'))
    angiogram.block(c,-151,-59,106,119,21,access.solid('#8e7285'))
    angiogram.block(c,-39,-38,163,76,14,access.solid('#f7f0e7'))
    access.text(c,'Blood test',-18,11,29,'#314e45')
    c.restore()
    card_text(c,'Early emergency assessment','Troponin blood test',
              ('Can detect injury to','the heart muscle'))


def assessment(c,t):
    if t<9.88:
        ecg(c,t)
    elif t<14.55:
        troponin(c,t-9.88)
    else:
        ecg(c,t-14.55,urgent=True)


def pathway(c,t):
    if t<5.48:
        page=('STEMI',('A time-sensitive emergency','Restore blood flow','Urgent assessment'))
        care.document_scene(c,'The emergency treatment path','Time matters in STEMI',
                            ('Opening the artery quickly','is a priority'),page,t/5.48)
    elif t<12.31:
        page=('Emergency PCI',('When available promptly','Reopen the artery','Restore flow'))
        care.document_scene(c,'The emergency treatment path','Emergency angioplasty',
                            ('Often preferred when','it can be done promptly'),page,(t-5.48)/6.83)
    else:
        page=('Care pathway',('Access to treatment','Test results','The patient’s condition'))
        care.document_scene(c,'The emergency treatment path','The team chooses the path',
                            ('Other approaches may be used','depending on the situation'),page,(t-12.31)/7.024)
    access.rect(c,865,25,394,48,access.solid('#e5f2e8'))
    access.text(c,TOPIC,878,57,24,'#276b5a')


def culprit_view(c,t,*,restored=False):
    """Use the same left coronary projection on both contrast checks."""
    shot=4.7 if not restored else 4.3
    phase=(t%shot)/shot if not restored else min(1,t/shot)
    head_fraction=access.smooth(phase/.76)
    fade=access.smooth((phase-.79)/.21)
    opacity=round(251-151*fade)
    branches,total=angiogram.tree('left')
    culprit=branches[1]
    cut=round((len(culprit[0])-1)*.43)
    cutoff=culprit[2]+culprit[1][cut]
    head=total*head_fraction
    c.save()
    c.translate(640,387)
    scale=1+.085*phase
    c.scale(scale,scale)
    c.translate(-640,-387)
    c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kLinear))

    def xy(point):
        return 222+3.48*point[0],101+1.88*point[1]

    for index,(points,lengths,entry,thickness) in enumerate(branches):
        remaining=head-entry
        if remaining<=0 or (not restored and index in (4,5,6) and entry>=cutoff):
            continue
        end=sum(distance<=remaining for distance in lengths)
        if not restored and index==1:
            end=min(end,cut+1)
        coordinates=list(map(xy,points[:end]))
        access.line(c,coordinates,'#566461',thickness*2+4,opacity)
        access.line(c,coordinates,'#192522',thickness*2.06,opacity)
    if head>=cutoff and (restored or t>=5.07):
        x,y=xy(culprit[0][cut])
        angiogram.dot(c,x,y,12,'#f8d18f',208)
        access.line(c,[(x,y),(x+104,y-67),(x+240,y-67)],'#ffedbd',3)
        label='Contrast passes this point' if restored else 'Contrast stops here'
        access.text(c,label,x+107,y-83,30,'#fff4d3')
    c.restore()
    angiogram.header(c,'Checking flow after treatment' if restored else 'Finding the blockage',
                    'SIMULATED X-RAY',True)


def treatment(c,t):
    if t>=16.2:
        culprit_view(c,t-16.2,restored=True)
        return
    emergency.restore_culprit_flow(c,t)
    if t<5.98:
        clot_flow(c,t)


def recovery(c,t):
    if t<6.:
        ecg(c,t,recovery=True)
    elif t<9.78:
        care.document_scene(c,'Recovery and prevention','Ongoing care',
                            ('Your team explains what','your tests showed'),
                            ('Recovery plan',('Medicines','Test results','Next steps')),(t-6.)/3.78)
    elif t<15.10:
        care.rehabilitation(c,(t-9.78)/5.32,t-9.78)
    else:
        care.document_scene(c,'Recovery and prevention','Make a follow-up plan',
                            ('Ask what to do if','symptoms return'),
                            ('Follow-up',('Other narrowings','Future care','Returning symptoms')),(t-15.10)/6.534)


SCENES={
    'P01':opening,
    'P02':symptoms,
    'P03':assessment,
    'P04':pathway,
    'P05':culprit_view,
    'P06':treatment,
    'P07':recovery,
}


def draw(c, ident, p, t):
    SCENES[ident](c,t)
