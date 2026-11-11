"""Render silent, retimable 1440p pictures for What the Four Tools Do."""

import argparse
from functools import lru_cache
import json
from math import cos, hypot, sin
from pathlib import Path
import importlib.util
import shutil
import subprocess
import tempfile

import numpy as np
import skia

from tools.elysian_video import access as wrist
from tools.elysian_video import angiogram as coronary
from tools.elysian_video.__main__ import FPS, HEIGHT, LEGACY_FFMPEG, ROOT, WIDTH


HERE = Path(__file__).resolve().parent
ART = coronary.art
FEMORAL_SOURCE = HERE.parents[1] / 'episode-01/visuals/render_groin.py'
spec = importlib.util.spec_from_file_location('elysian_femoral_source', FEMORAL_SOURCE)
femoral = importlib.util.module_from_spec(spec)
spec.loader.exec_module(femoral)
GREEN, MINT, PALE = '#004b3d', '#73c0aa', '#eff8ee'
DARK, INK, MUTED = '#0d3531', '#213c37', '#4c7168'
CREAM, GOLD, CORAL = '#f2fbf3', '#e7bd77', '#aa5969'
BASE = {1: 15, 2: 13, 3: 14, 4: 14, 5: 12, 6: 15,
        7: 13, 8: 13, 9: 14, 10: 12, 11: 13, 12: 8}
solid, gradient, line, path = wrist.solid, wrist.grad, wrist.line, wrist.path
curve = ART.curve


def ease(p, a, b):
    return wrist.smooth((p-a)/(b-a))


def mix(a, b, p):
    return a+(b-a)*p


def rect(x, y, w, h):
    return skia.Rect.MakeXYWH(x, y, w, h)


def block(c, x, y, w, h, radius, fill):
    paint = solid(fill) if isinstance(fill, str) else fill
    c.drawRoundRect(rect(x, y, w, h), radius, radius, paint)


def oval(c, x, y, rx, ry, fill, opacity=255):
    paint = solid(fill, opacity) if isinstance(fill, str) else fill
    c.drawOval(rect(x-rx, y-ry, 2*rx, 2*ry), paint)


def words(c, label, x, y, size=29, color=INK, *, face=None, align='left', opacity=255):
    font = skia.Font(face or wrist.BOLD, size)
    font.setEdging(skia.Font.kAntiAlias)
    width = font.measureText(label)
    x -= width/2 if align == 'center' else width if align == 'right' else 0
    if not 0 <= x <= 1280-width or not 36 <= y <= 703:
        raise ValueError(f'Out of frame: {label!r} at {x:.1f},{y:.1f}')
    c.drawString(label, x, y, font, solid(color, opacity))


def brand(c, dark=False, x=56):
    c.drawImageRect(wrist.LOGO, rect(x, 32, 49, 49), skia.SamplingOptions(skia.FilterMode.kLinear))
    words(c, 'Elysian Biomedical LLP', x+65, 64, 25, CREAM if dark else GREEN)


def title(c, label, dark=False, size=47):
    words(c, label, 55, 137, size, CREAM if dark else GREEN, face=wrist.HEADING)


def tag(c, label, x=55, y=629, dark=False):
    font = skia.Font(wrist.BOLD, 29)
    w = font.measureText(label)
    fill = solid('#143d36', 242) if dark else solid('#f3faf0', 243)
    block(c, x-12, y-34, w+24, 48, 10, fill)
    words(c, label, x, y, 29, CREAM if dark else GREEN)


def marker(c, label, x, y, target, *, dark=False):
    stroke = '#d5eddf' if dark else '#1b574b'
    tx, ty = target
    font = skia.Font(wrist.BOLD, 29)
    w = font.measureText(label)
    anchor = x-12 if tx<x else x+w+12
    direction = -1 if tx<x else 1
    line(c, [(anchor, y-12), (anchor+direction*33, y-12), (tx, ty)], stroke, 2.4)
    oval(c, tx, ty, 6.1, 6.1, stroke)
    oval(c, tx, ty, 2.8, 2.8, GOLD)
    tag(c, label, x, y, dark)


def field(c, dark=False):
    shades = ['#112b2a', '#1d4941', '#102a29'] if dark else ['#f8fcf5', '#d9ebe2', '#9bc2b3']
    c.drawRect(rect(0, 0, 1280, 720), gradient(125, 0, 1097, 720, shades))


def halo(c, x, y, size, t, color=GREEN):
    p = (t%1.9)/1.9
    edge = solid(color, round(160*(1-p)))
    edge.setStyle(skia.Paint.kStroke_Style)
    edge.setStrokeWidth(2.6)
    c.drawCircle(x, y, size+17*p, edge)


def shaft(c, points, width, colors):
    dark, body, shine = colors
    line(c, points, dark, width+3)
    line(c, points, body, width)
    line(c, [(x-.8, y-width*.22) for x,y in points], shine, max(1.4,width*.13))


TUBE = ('#234e51', '#a5c6be', '#e5f3eb')
WIRE = ('#745433', '#e9c680', '#fff3ce')
SHEATH = ('#184c45', '#539483', '#b4e1cf')
NEEDLE = ('#496462', '#9fb6b2', '#ecf4ed')


def tray_tool(c, tool, x, y, scale, t, active):
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.translate(0, 4*sin(t*2.0) if active else 0)
    oval(c, 9, 31, 144, 17, '#31504a', 34)
    if tool == 0:
        shaft(c, [(-130, 0), (123, 0)], 32, SHEATH)
        block(c, -132, -24, 73, 48, 11, gradient(-128,-25,-62,31,['#c7ede0','#75b0a0','#2d6c62']))
        oval(c, 123, 0, 8, 16, '#244842')
        oval(c, 124, 0, 4, 10, '#0c2825')
        shaft(c, [(-74, -10), (-94,-54),(-140,-54)], 10, SHEATH)
    elif tool == 1:
        points = curve((-144,10),((-86,-27),(-19,-27),(62,-14)),((109,-9),(144,-2),(147,14)),
                       ((146,27),(134,31),(123,24)))
        shaft(c, points, 7, WIRE)
        oval(c, 123, 24, 3.5, 3.5, '#fff1c4')
    elif tool == 2:
        points = curve((-144,6),((-76,-3),(28,-7),(86,-7)),((120,-7),(132,7),(145,30)))
        shaft(c, points, 13, TUBE)
        block(c, -150, -10, 39, 31, 7, '#539184')
        oval(c, 145, 30, 4.5, 6.5, '#31595a')
    else:
        block(c, -128, -23, 209, 46, 11, gradient(-126,-23,-126,24,['#edf3e8','#b1ccc4','#6b9e91']))
        block(c, -106, -15, 177, 30, 5, gradient(-106,-15,-106,15,['#fff0c6','#e9be73','#c29455']))
        block(c, -166, -6, 63, 13, 5, '#5b897f')
        block(c, -172, -21, 12, 42, 6, '#426d63')
        shaft(c, [(81,0),(130,0),(151,8)], 9, TUBE)
    c.restore()


TOOL_NAMES = ('Sheath', 'Guidewire', 'Catheter', 'Contrast')


def tool_row(c, p, t, ending=False):
    field(c)
    brand(c)
    title(c, 'How the tools work together' if ending else 'Four tools in a coronary angiogram')
    active = min(3, int(p*4))
    for j, name in enumerate(TOOL_NAMES):
        x = 192 + 298*j
        y = 380
        offset = 34*(1-ease(p, j*.10, j*.10+.20))
        scale = .84 + (.19*ease(p, j*.25, j*.25+.13) if active == j else 0)
        tray_tool(c,j,x,y+offset,scale,t,j==active)
    x = 192+298*active
    words(c, TOOL_NAMES[active], x, 522, 35, GREEN, align='center')
    halo(c, x, 552, 4, t, GREEN)


def xray(c, p, t, *, side='left', angle=5, label=None, recording=False, hook=False):
    c.drawImageRect(coronary.radiograph_plate(), rect(0, 0, 1280, 720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    fill = ease(p, 0, .47)
    alpha = round(249*(1-ease(p,.65,.94)))
    coronary.contrast_paths(c, side, fill, alpha, angle, False)
    words(c, 'Simulated coronary X-ray', 55, 67, 30, CREAM)
    if label:
        tag(c, label, dark=True)
    if recording and .05 < p < .81:
        oval(c, 1027, 57, 6.5, 6.5, '#f9cfb0')
        words(c, 'Recording', 1047, 67, 28, CREAM)
    if hook and t >= 5:
        block(c, 42, 84, 863, 70, 12, solid(DARK, 239))
        title(c, 'Four tools in a coronary angiogram', True, 43)


def opener(c,p,t):
    if t < 6:
        xray(c,min(.63,t/7),t,hook=True)
    else:
        tool_row(c,ease(t,6,15),t)


@lru_cache(maxsize=1)
def body_plate():
    surface = skia.Surface(WIDTH, HEIGHT)
    c = surface.getCanvas()
    c.scale(2,2)
    field(c)
    c.save()
    c.translate(222, 106)
    c.scale(1.20, 1.04)
    c.drawPath(path(ART.BODY, True), gradient(89,65,490,553,['#c1ddd0','#7ba99b','#4e887b']))
    # Opaque drape is baked in above the illustration and has no external features.
    drape = curve((170,412),((230,402),(343,405),(416,417)),((426,443),(438,492),(442,560)),
                  ((378,582),(231,581),(159,556)),((161,500),(158,456),(170,412)))
    c.drawPath(path(drape,True),gradient(163,420,440,565,['#9cc7b6','#4c8f82','#27665f']))
    for i in range(7):
        x = 178 + 38*i
        line(c, curve((x,429),((x+12,460),(x-13,508),(x+8,557))), '#acd3bf', 2, 112)
    heart = curve((289,193),((269,171),(238,183),(238,211)),((233,245),(273,260),(291,277)),
                  ((318,300),(349,279),(368,244)),((396,202),(338,177),(289,193)))
    c.drawPath(path(heart,True),gradient(230,184,376,285,['#e6a49a','#b5626a','#763b51']))
    for points in (ART.RADIAL, ART.FEMORAL, ART.BODY_OTHER_ILIAC):
        shaft(c,points,10,('#8d4b5a','#c0747e','#efb6a8'))
    c.restore()
    return surface.makeImageSnapshot()


def body(c,p,t, diagnostic=False):
    c.drawImageRect(body_plate(),rect(0,0,1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    c.save()
    c.translate(222, 106)
    c.scale(1.20, 1.04)
    radial = ART.RADIAL
    femoral = ART.FEMORAL
    if diagnostic:
        advance = .37+.63*ease(p,0,.59)
        cath = max(0,advance-.20+.167*ease(p,.38,.90))
        shaft(c,ART.trace(radial,advance),6.3,WIRE)
        shaft(c,ART.trace(radial,cath),9,TUBE)
        endpoint = ART.trace(radial,advance)[-1]
        halo(c,*endpoint,8,t,'#fff0b6')
    else:
        route, advance = (radial,ease(p,0,.52)) if p<.55 else (femoral,ease(p,.55,.92))
        active = ART.trace(route,advance)
        shaft(c,active,7.4,('#175a51','#9fe0c7','#e4fff0'))
        halo(c,*route[0],8,t,'#e6f7e8')
        if len(active)>1:
            oval(c,*active[-1],4,4,'#f2f9cb')
    c.restore()
    brand(c)
    title(c,'The wire and catheter travel together' if diagnostic else 'Two routes reach the aortic root')
    name = 'Long wire leads the catheter' if diagnostic else ('Right wrist route' if p<.55 else 'Right groin route')
    tag(c,name)
    endpoint = radial[-1]
    if p>.68:
        marker(c,'Aortic root',825,289,(222+endpoint[0]*1.2,106+endpoint[1]*1.04))


@lru_cache(maxsize=1)
def wrist_plate():
    surface = skia.Surface(WIDTH, HEIGHT)
    c = surface.getCanvas()
    c.scale(2,2)
    field(c)
    wrist.vessel(c)
    return surface.makeImageSnapshot()


def wrist_base(c,t,label):
    c.drawImageRect(wrist_plate(),rect(0,0,1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    wrist.flow(c,-t)
    brand(c,x=889)
    words(c,label,1222,138,47,GREEN,face=wrist.HEADING,align='right')
    tag(c,'Right radial artery')


def access_wire(c,p,t):
    wrist_base(c,t,'The short access wire')
    needle_tip = 591*ease(p,.02,.26)-117*(1-ease(p,.02,.26))-777*ease(p,.69,.93)
    if p>.29:
        wire_tip = mix(221,797,ease(p,.29,.67))
        wrist.tube(c,wire_tip-930,wire_tip,3.8,wrist.WIRE,taper=7)
    wrist.tube(c,needle_tip-432,needle_tip,6.7,wrist.NEEDLE,taper=25)
    wrist.tube(c,needle_tip-476,needle_tip-429,12,wrist.SHEATH)
    if p>.36:
        marker(c,'Short wire',813,213,wrist.xy(wire_tip))
    elif needle_tip>200:
        marker(c,'Needle tip',800,211,wrist.xy(needle_tip))


def access_sheath(c,p,t):
    wrist_base(c,t,'The sheath stays at the wrist')
    tip = mix(25,631,ease(p,.02,.54))
    leave = ease(p,.63,.90)
    dilator_tip = tip+24-830*leave
    wire_tip = 797-1040*leave
    wrist.sheath(c,tip,dilator_tip if leave<.98 else None)
    wrist.tube(c,wire_tip-940,wire_tip,3.8,wrist.WIRE,taper=6)
    marker(c,'Sheath and dilator' if leave<.93 else 'Open sheath tip',781,216,wrist.xy(tip))


def groin_map(points):
    return [(95+(x-54)*3.0,151+(y-106)*2.12) for x,y in points]


def groin_position(fraction):
    return groin_map(femoral.ACCESS.trace(fraction))[-1]


@lru_cache(maxsize=1)
def groin_plate():
    surface = skia.Surface(WIDTH,HEIGHT)
    c = surface.getCanvas()
    c.scale(2,2)
    field(c,True)
    for i in range(20):
        y = 107+32*i
        line(c,curve((0,y+19),((310,y-31),(865,y+24),(1280,y-4))),'#3d7568',1.6,91)
    block(c,79,135,1061,497,100,'#133d37')
    block(c,100,147,1026,469,86,gradient(120,132,901,618,['#deb194','#c98878','#814656']))
    shape = [(75,212),(134,203),(241,211),(342,194),(375,209),
             (371,275),(340,301),(113,299),(77,272)]
    c.drawPath(path(groin_map(shape),True),gradient(165,358,888,567,['#d29583','#9f5a63','#693948']))
    line(c,groin_map(shape[:5]),'#f8ccab',6.5)
    branch=curve((165,252),((145,257),(129,270),(117,285)))
    main=curve((103,254),((145,250),(222,255),(280,252)),((315,251),(344,247),(365,238)))
    for points,width in ((branch,29),(main,59)):
        outline=groin_map(points)
        shaft(c,outline,width,('#673741','#c57577','#ecab9e'))
        line(c,outline,'#682d41',width*.55)
    return surface.makeImageSnapshot()


def groin(c,p,t):
    c.drawImageRect(groin_plate(),rect(0,0,1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    brand(c,True)
    title(c,'One way to enter at the groin',True)
    tag(c,'Right common femoral artery',dark=True)
    route = femoral.ACCESS
    if p<.49:
        q = ease(p,.02,.38)
        tip = mix(femoral.MICRO-.23,femoral.MICRO,q)
        shaft(c,groin_map(route.trace(tip,max(0,tip-.29))),14,SHEATH)
        shaft(c,groin_map(route.trace(tip+.022,max(0,tip-.31))),8,TUBE)
        shaft(c,groin_map(route.trace(femoral.FINE,.02)),3.4,WIRE)
        marker(c,'Temporary introducer',784,210,groin_position(tip),dark=True)
    elif p<.57:
        block(c,0,260,1280,246,0,solid(DARK,248))
        words(c,'After the wire exchange',640,396,49,CREAM,face=wrist.HEADING,align='center')
    else:
        tip=femoral.WORKING
        shaft(c,groin_map(route.trace(tip,max(0,tip-.35))),22,SHEATH)
        point=groin_position(tip)
        oval(c,*point,5,9,'#153e36')
        marker(c,'Working sheath',810,215,point,dark=True)
        halo(c,*point,11,t,GOLD)


def diagnostic_wire(c,p,t):
    if p>=.67:
        body(c,(p-.67)/.33,t,diagnostic=True)
        return
    wrist_base(c,t,'The long diagnostic guidewire')
    wire_tip = mix(100,1194,ease(p,.02,.34))
    cath_tip = mix(87,1035,ease(p,.36,.65))
    wrist.sheath(c,631)
    wrist.tube(c,wire_tip-1320,wire_tip,3.9,wrist.WIRE,taper=7)
    if p>.36:
        wrist.tube(c,cath_tip-1330,cath_tip,8.6,wrist.CATHETER,taper=10,opacity=241)
    if wire_tip>295:
        marker(c,'Long guidewire' if p<.38 else 'Catheter follows',722,214,
               wrist.xy(wire_tip if p<.38 else cath_tip))


def mapped(points):
    return [(690+(x-1147)*3.1, 148+(y-334)*1.47) for x,y in points]


def root_point(point):
    return mapped([point])[0]


LEFT, RIGHT = coronary.LEFT, coronary.RIGHT
L_COR = curve(LEFT,((1294,516),(1315,534),(1356,544)))
R_COR = curve(RIGHT,((1037,518),(1001,535),(954,556)))
VALVE = curve((1071,604),((1109,596),(1120,614),(1158,629)),
              ((1193,614),(1218,601),(1258,603)))


@lru_cache(maxsize=1)
def root_plate():
    surface = skia.Surface(WIDTH,HEIGHT)
    c = surface.getCanvas()
    c.scale(2,2)
    field(c)
    for points in (L_COR,R_COR):
        pts = mapped(points)
        shaft(c,pts,64,('#803e50','#c17c7e','#e2a59d'))
        line(c,pts,'#713a50',37)
    c.drawPath(path(mapped(coronary.ROOT_OUTLINE),True),
               gradient(436,150,991,650,['#db9d94','#a96470','#673647']))
    c.drawPath(path(mapped(coronary.ROOT_LUMEN),True),
               gradient(478,150,925,629,['#df9b90','#a65b6b','#733b4f']))
    for point in (LEFT,RIGHT):
        oval(c,*root_point(point),21,13,'#663648')
    line(c,mapped(VALVE),'#5b3044',24)
    line(c,mapped(VALVE),'#edb7a7',10)
    return surface.makeImageSnapshot()


def root(c,p,t,inject=False):
    c.drawImageRect(root_plate(),rect(0,0,1280,720),skia.SamplingOptions(skia.FilterMode.kNearest))
    for i in range(17):
        y = 350+(i*19-t*33)%244
        x = 1146+((i*23)%66)-33
        oval(c,*root_point((x,y)),3.7,2.2,'#f6c0ab',99)
    q = 1 if inject else ease(p,.56,.92)
    tip = tuple(mix(a,b,q) for a,b in zip(coronary.NEUTRAL,LEFT))
    catheter = coronary.instrument_path(tip)
    c.save()
    c.clipRect(rect(385,145,755,486))
    shaft(c,mapped(catheter),17,TUBE)
    wire_target = None
    if not inject:
        release = 1-ease(p,.08,.49)
        if release>0:
            # The stable catheter masks the part of the wire inside its shaft.
            wire = curve(coronary.NEUTRAL,((1143,535),(1144,553),coronary.WIRE))
            tip_path = mapped(ART.trace(wire,release))
            shaft(c,tip_path,5,WIRE)
            if len(tip_path)>1:
                wire_target = tip_path[-1]
    else:
        length = ease(p,0,.32)
        line(c,mapped(ART.trace(catheter,length)),GOLD,7,240)
        if p>.29:
            branch=ART.trace(L_COR,ease(p,.29,.80))
            line(c,mapped(branch),GOLD,13,236)
            if len(branch)>1:
                oval(c,*mapped(branch)[-1],6.5,6.5,'#ffdf9e')
    c.restore()
    brand(c)
    title(c,'Contrast travels through the catheter' if inject else 'The catheter stays. The guidewire leaves.')
    if wire_target and p<.40:
        marker(c,'Long guidewire',968,327,wire_target)
    else:
        marker(c,'Left coronary opening',968,327,root_point(LEFT))
    marker(c,'Aortic valve',86,578,root_point((1158,629)))


def contrast(c,p,t):
    if p<.48:
        root(c,p/.48,t,True)
    else:
        xray(c,(p-.48)/.52,t,label='Left coronary arteries')


def c_arm(c,p,t):
    field(c,True)
    brand(c,True)
    title(c,'A different X-ray view',True)
    c.save()
    c.translate(0,35)
    c.rotate(mix(-19,23,ease(p,0,1)),646,413)
    ring = curve((666,188),((439,128),(295,235),(316,437)),((333,590),(447,628),(646,613)))
    shaft(c,ring,44,('#0a2425','#4d7970','#87b5a7'))
    block(c,604,165,131,62,15,gradient(0,165,0,227,['#d4e4dc','#8cb1a6','#54796e']))
    block(c,591,584,148,52,13,'#8eb1a5')
    c.restore()
    block(c,449,472,619,23,8,'#b2cebf')
    block(c,726,489,26,132,6,'#416a61')
    tag(c,'The next run is a separate recording',dark=True)


def imaging_runs(c,p,t):
    if p<.36:
        xray(c,p/.36,t,label='Left coronary view',recording=True)
    elif p<.57:
        c_arm(c,(p-.36)/.21,t)
    else:
        xray(c,(p-.57)/.43,t,side='right',angle=-17,label='Right coronary view',recording=True)


def consultation(c,p,t):
    field(c)
    brand(c)
    before = p<.52
    title(c,'Before the test' if before else 'During the test')
    # Frosted clinical-glass partitions and a consultation desk.
    for x in (0,429,856):
        c.drawRect(rect(x,161,425,394),gradient(x,161,x+425,555,['#e5f1e7','#bedbd0','#a7c7bb']))
        line(c,[(x,162),(x,550)],'#fcfdf1',4,163)
    block(c,519,207,245,196,15,gradient(519,207,761,403,['#49776c','#1d4a43','#1b3935']))
    block(c,530,219,224,174,8,gradient(530,218,750,393,['#bdd9cb','#7ba89b','#498478']))
    q=ease(p,0,.45) if before else ease(p,.52,.93)
    if before:
        for s in (-1,1):
            xx=640+s*36
            kidney=curve((xx,272),((xx-s*32,240),(xx+s*49,229),(xx+s*40,279)),
                         ((xx+s*30,325),(xx+s*1,337),(xx-s*7,311)),
                         ((xx-s*16,289),(xx+s*14,288),(xx,272)))
            c.drawPath(path(kidney,True),gradient(xx-20,239,xx+41,341,['#f3bfaa','#b97775','#804c5a']))
        line(c,[(581,355),(581+121*q,355)],'#f2f6df',4)
    else:
        trace=curve((564,313),((578,313),(588,315),(605,313)),((615,312),(621,284),(629,289)),
                    ((638,315),(643,330),(651,311)),((666,306),(676,316),(721,313)))
        line(c,ART.trace(trace,.4+.6*q),'#e8f6d8',4)
    # Two anonymous, fully clothed people. Facial and body characteristics are omitted.
    for i,(x, colors) in enumerate(((373,('#b0cfbf','#67958a','#356d62')),
                                    (866,('#d6e6dc','#9cbdb1','#5d8d83')))):
        y = 305-12*sin(t*1.8+i)
        oval(c,x,y,60,69,gradient(x-62,y-71,x+53,y+54,colors))
        suit = curve((x-180,577),((x-172,456),(x-143,405),(x-61,397)),
                     ((x-42,425),(x+42,425),(x+59,397)),
                     ((x+149,400),(x+172,480),(x+180,577)))
        c.drawPath(path(suit,True),gradient(x-160,402,x+139,594,colors))
        line(c,[(x-90,529),(x-79,569)],'#d0e1d7',3,120)
    block(c,165,562,952,48,12,gradient(165,562,1091,606,['#f2f9ec','#b6d1c4','#7daa9d']))
    if before:
        tag(c,'Kidney problems',169,626)
        tag(c,'Past reaction to contrast',760,626)
    else:
        tag(c,'Brief warmth can happen',145,626)
        tag(c,'Tell staff if you feel unwell',730,626)


def recap(c,p,t):
    if p>.57:
        tool_row(c,(p-.57)/.43,t,True)
        return
    wrist_base(c,t,'The team removes the tools')
    cath_tip = mix(1035,-139,ease(p,0,.23))
    sheath_tip = mix(631,-180,ease(p,.33,.55))
    wrist.sheath(c,sheath_tip)
    wrist.tube(c,cath_tip-1320,cath_tip,9,wrist.CATHETER,taper=11)
    if p>.28:
        alpha = round(207*ease(p,.28,.39))
        oval(c,329,428,42,148,'#70c5b0',alpha//2)
        block(c,295,272,68,47,11,solid('#1c6659',alpha))
        oval(c,329,310,29,15,'#c3ecda',alpha)
    if p>.45:
        marker(c,'Wrist compression',776,210,(329,311))


def sources(c,p,t):
    field(c,True)
    brand(c,True)
    title(c,'Cardiology Education Series',True)
    words(c,'Clinical sources',55,239,36,CREAM)
    words(c,'AHA · SCAI · NHS · American College of Radiology',55,291,27,'#d3efe0')
    words(c,'Original animation · Simulated imaging · Synthetic narration',55,345,25,'#d3efe0')
    words(c,'Next episode',55,456,32,CREAM)
    words(c,'How clinicians read a coronary angiogram',55,518,36,'#bbdfcf',face=wrist.HEADING)
    line(c,[(56,560),(56+590*ease(p,.03,.94),560)],'#72baa8',3)


SCENES = (opener,body,access_wire,access_sheath,groin,diagnostic_wire,
          root,contrast,imaging_runs,consultation,recap,sources)


def thumbnail():
    surface = skia.Surface(1280, 720)
    c = surface.getCanvas()
    field(c)
    c.save()
    c.translate(-52, 7)
    c.scale(1.10, 1.10)
    wrist.vessel(c)
    wrist.flow(c,0)
    wrist.sheath(c,631)
    wrist.tube(c,-185,1054,9.7,wrist.CATHETER,taper=11)
    wrist.tube(c,1047,1205,4.2,wrist.WIRE,taper=6)
    c.restore()
    brand(c,x=443)
    words(c,'Four Angiography',440,182,86,GREEN,face=wrist.HEADING)
    words(c,'Tools',440,284,105,GREEN,face=wrist.HEADING)
    surface.makeImageSnapshot().save(str(HERE.parent/'thumbnail.png'))


def render(ids, ffmpeg, still_only, force):
    pixels = np.empty((HEIGHT, WIDTH, 4), dtype=np.uint8)
    info = skia.ImageInfo.Make(WIDTH, HEIGHT, skia.ColorType.kRGBA_8888_ColorType,
                               skia.AlphaType.kPremul_AlphaType)
    surface = skia.Surface.MakeRasterDirect(info, pixels, WIDTH*4)
    canvas = surface.getCanvas()
    canvas.scale(2,2)
    for ident in ids:
        number = int(ident[1:])
        duration = BASE[number]
        motion = SCENES[number-1]
        if still_only:
            for p in (.20,.52,.85):
                motion(canvas,p,p*duration)
                surface.makeImageSnapshot().save(str(HERE/f'{ident}-review-{round(p*100)}.png'))
            continue
        target = HERE/f'{ident}.mp4'
        if target.exists() and not force:
            print(f'{ident} already rendered',flush=True)
            continue
        partial = target.with_suffix('.partial.mp4')
        frames = duration*FPS
        # Spool one scene at a time. On Windows this avoids copying 14 MB
        # frames through a small anonymous pipe while another process encodes.
        if shutil.disk_usage(HERE).free < frames*pixels.nbytes+64*1024**2:
            raise OSError(f'Insufficient workspace for {ident} native frame spool')
        with tempfile.NamedTemporaryFile(prefix=f'.{ident}-',suffix='.rgba',dir=HERE,delete=False) as raw:
            raw_path=Path(raw.name)
            try:
                for index in range(frames):
                    motion(canvas,index/max(1,frames-1),index/FPS)
                    raw.write(memoryview(pixels).cast('B'))
                    if index%150==0:
                        print(f'{ident} drawing frame {index+1}/{frames}',flush=True)
                raw.close()
                arguments = [
                    str(ffmpeg),'-hide_banner','-v','error','-y','-f','rawvideo','-pixel_format','rgba',
                    '-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(FPS),'-i',str(raw_path),
                    '-an','-filter_threads','1','-c:v','libx264','-threads','2','-preset','fast',
                    '-x264-params','rc-lookahead=14:sync-lookahead=0:ref=2',
                    '-crf','15','-profile:v','high','-pix_fmt','yuv420p','-g','60','-bf','2',
                    '-movflags','+faststart',str(partial),
                ]
                print(f'{ident} encoding {frames} frames',flush=True)
                subprocess.run(arguments,check=True)
            finally:
                raw.close()
                raw_path.unlink(missing_ok=True)
        partial.replace(target)
        print(f'{ident} {duration:.3f} s  {target.name}',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenes',nargs='*',choices=[f'P{i:02d}' for i in BASE])
    parser.add_argument('--ffmpeg')
    parser.add_argument('--stills',action='store_true')
    parser.add_argument('--thumbnail',action='store_true')
    parser.add_argument('--force',action='store_true')
    args = parser.parse_args()
    exe = args.ffmpeg or shutil.which('ffmpeg') or LEGACY_FFMPEG
    if args.thumbnail:
        thumbnail()
    else:
        render(args.scenes or [f'P{i:02d}' for i in BASE],exe,args.stills,args.force)
