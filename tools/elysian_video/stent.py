"""Original coronary stent mechanics for the complete angioplasty episode."""

from dataclasses import dataclass
from functools import lru_cache
from math import cos, exp, pi, sin
from random import Random

import skia


from .access import HEADING as TITLE, REGULAR as BODY, BOLD, LOGO
DURATION = 34.0
X0, X1, LESION = -90, 1370, 648
MESH_HALF, BALLOON_HALF, OPEN_RADIUS = 158, 185, 116


def color(value, alpha=255):
    value = value.removeprefix('#')
    return skia.ColorSetARGB(alpha, *(int(value[i:i+2], 16) for i in (0, 2, 4)))


def paint(value, alpha=255):
    return skia.Paint(AntiAlias=True, Color=color(value, alpha))


def gradient(x0, y0, x1, y1, tones, stops=None):
    brush = skia.Paint(AntiAlias=True)
    brush.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)], [color(tone) for tone in tones], stops,
    ))
    return brush


def line(canvas, points, value, width=1, alpha=255):
    if len(points) < 2:
        return
    path = skia.Path()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    brush = paint(value, alpha)
    brush.setStyle(skia.Paint.kStroke_Style)
    brush.setStrokeWidth(width)
    brush.setStrokeCap(skia.Paint.kRound_Cap)
    brush.setStrokeJoin(skia.Paint.kRound_Join)
    canvas.drawPath(path, brush)


def enclosed(top, bottom):
    path = skia.Path()
    path.moveTo(*top[0])
    for point in top[1:] + bottom[::-1]:
        path.lineTo(*point)
    path.close()
    return path


def ease(t, a, b):
    u = min(1.0, max(0.0, (t-a)/(b-a)))
    return u*u*(3-2*u)


def center(x):
    return 392 + 12*sin((x-135)/244) - 8*sin(x/138)


def plaque(x):
    return exp(-abs((x-LESION)/120)**2.7)


def lumen_radius(x, side, expansion):
    narrowing = plaque(x)*(84 if side < 0 else 40)
    return OPEN_RADIUS - narrowing*(1-expansion)


@dataclass(frozen=True)
class Motion:
    wire_tip: float
    delivery_x: float
    delivery_radius: float
    stent_x: float
    stent_radius: float
    expansion: float
    flow: float


def motion(t):
    wire_tip = 80 + 1046*ease(t, .16, 5.53)
    advance = ease(t, 6.02, 14.45)
    expansion = ease(t, 16.58, 20.46)
    collapse = ease(t, 24.98, 27.46)
    retract = ease(t, 27.68, 30.94)
    delivery_x = -191 + (LESION+191)*advance - (LESION+191)*retract
    delivery_radius = 13 + (OPEN_RADIUS-14)*expansion*(1-collapse)
    stent_x = -191 + (LESION+191)*advance
    stent_radius = 15 + (OPEN_RADIUS-15)*expansion
    flow = 1.0 - .96*ease(expansion, .18, 1.0)*(1-collapse)
    return Motion(wire_tip, delivery_x, delivery_radius, stent_x, stent_radius, expansion, flow)


XS = list(range(X0, X1+1, 5))
def text(canvas, value, x, baseline, size, tone, face=BOLD, alpha=255):
    font = skia.Font(face, size)
    font.setSubpixel(True)
    font.setEdging(skia.Font.Edging.kAntiAlias)
    canvas.drawString(value, x, baseline, font, paint(tone, alpha))


def draw_artery(canvas, expansion):
    outer_top = [(x, center(x)-211-11*cos(x/150)) for x in XS]
    outer_bottom = [(x, center(x)+218+10*sin(x/170)) for x in XS]
    rim_top = [(x, center(x)-193-9*cos(x/150)) for x in XS]
    rim_bottom = [(x, center(x)+198+9*sin(x/170)) for x in XS]
    top = [(x, center(x)-lumen_radius(x, -1, expansion)) for x in XS]
    bottom = [(x, center(x)+lumen_radius(x, 1, expansion)) for x in XS]
    outer = enclosed(outer_top, outer_bottom)
    inner = enclosed(top, bottom)

    canvas.save()
    canvas.translate(0, 15)
    shadow = paint('#573c3d', 53)
    shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, 19))
    canvas.drawPath(outer, shadow)
    canvas.restore()
    canvas.drawPath(outer, gradient(0, 172, 0, 623, ['#a05056','#6b303f','#541f34']))
    canvas.drawPath(enclosed(rim_top, rim_bottom), gradient(0, 190, 0, 590,
        ['#e58f85','#b44d55','#773247','#d76d6d','#8d3b50'], [0,.29,.50,.83,1]))
    line(canvas, outer_top, '#f6aba1', 4, 193)
    line(canvas, outer_bottom, '#50243a', 3, 210)
    line(canvas, [(x, center(x)-178-9*cos(x/150)) for x in XS], '#fcb5a3', 3, 92)
    line(canvas, [(x, center(x)+175+9*sin(x/170)) for x in XS], '#f9b29b', 4, 75)
    canvas.drawPath(inner, gradient(0, 270, 0, 520, ['#43152b','#7d283e','#8a3044','#43182f'], [0,.30,.58,1]))
    line(canvas, top, '#f4aa99', 3.2, 208)
    line(canvas, bottom, '#f18e83', 3.2, 180)
    for side in (-1, 1):
        xs = list(range(460, 846, 3))
        edge = [(x, center(x)+side*lumen_radius(x, side, expansion)) for x in xs]
        thickness = 58 if side < 0 else 38
        away = [(x, y+side*thickness*plaque(x)) for x, y in edge]
        canvas.drawPath(enclosed(edge, away), gradient(475, 262, 805, 502,
            ['#c58a63','#f0c998','#b47a60'], [0,.45,1]))
        line(canvas, edge, '#ffe0aa', 2.2, 210)
        rng = Random(10+side)
        for _ in range(95):
            x = rng.uniform(487, 814)
            y = center(x)+side*(lumen_radius(x, side, expansion)+rng.uniform(.2,.9)*thickness*plaque(x))
            canvas.drawCircle(x,y,rng.uniform(.4,1.4),paint('#825345',rng.randrange(32,94)))
    return inner

@lru_cache(maxsize=3)
def artery_plate(expansion):
    surface=skia.Surface(2560,1440)
    canvas=surface.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    canvas.scale(2,2)
    lumen=draw_artery(canvas,expansion)
    return surface.makeImageSnapshot(),lumen

def artery(canvas,expansion):
    # Cache the stable medical illustration; device animation is composed
    # independently at every frame. Subpixel changes retain smooth expansion.
    image,lumen=artery_plate(round(expansion*240)/240)
    canvas.drawImageRect(image,skia.Rect.MakeWH(1280,720),
                         skia.SamplingOptions(skia.FilterMode.kNearest))
    return lumen

def blood_flow(canvas, t, state, lumen):
    canvas.save()
    canvas.clipPath(lumen, doAntiAlias=True)
    for i in range(34):
        x = (i*95 + t*(74+8*(i%5))) % 1470 - 95
        y = center(x) + ((i*31)%160-80) * lumen_radius(x, -1 if i%2 else 1, state.expansion)/117
        opacity = int((23+i%5*6)*state.flow)
        rect = skia.Rect.MakeLTRB(x-8,y-2.2,x+8,y+2.2)
        canvas.drawOval(rect, paint('#f49b83',opacity))
    canvas.restore()


def wire(canvas, tip):
    xs = list(range(X0, int(tip), 5)) + [tip]
    points = [(x, center(x)-12*ease(x,tip-53,tip)) for x in xs]
    line(canvas, points, '#311927', 6.6)
    line(canvas, points, '#ecd0a0', 3.9)
    line(canvas, points[-10:], '#fff0ce', 2.4)


def draw_stent(canvas, x0, radius, front):
    ring_count, struts = 11, 16
    period = 2*pi/struts
    radius_at=radius if callable(radius) else lambda x:radius
    for i in range(ring_count):
        x = x0-MESH_HALF+2*MESH_HALF*i/(ring_count-1)
        nodes = []
        for j in range(struts+1):
            theta = (j+(i%2)*.5)*period
            xx = x+(-1)**j*9
            nodes.append((xx,center(xx)+radius_at(xx)*sin(theta),theta))
        for a,b in zip(nodes,nodes[1:]):
            depth = cos((a[2]+b[2])*.5)
            if (depth>=0) != front:
                continue
            points = [a[:2],b[:2]]
            if front:
                line(canvas,points,'#434553',5.9)
                line(canvas,points,'#e9eee5' if depth>.52 else '#b8c6bd',3.1)
                line(canvas,[(x-1,y-1) for x,y in points],'#f6f3e4',.8,193)
            else:
                line(canvas,points,'#899695',2.3,139)
        if i+1 < ring_count:
            for j in (0, 4, 8, 12):
                x0n,y0n,theta=nodes[j]
                if (cos(theta)>=0) != front:
                    continue
                xb=x0n+2*MESH_HALF/(ring_count-1)-7
                line(canvas,[(x0n,y0n),(xb,center(xb)+radius_at(xb)*sin(theta+period*.5))],
                     '#c5cfc4' if front else '#7f908b',2.8,220 if front else 126)

@lru_cache(maxsize=4)
def stent_plate(radius,front):
    surface=skia.Surface(2560,1440)
    canvas=surface.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    canvas.scale(2,2)
    draw_stent(canvas,LESION,radius,front)
    return surface.makeImageSnapshot()

def stent(canvas,x0,radius,front):
    if x0==LESION and not callable(radius) and radius in (116,75):
        canvas.drawImageRect(stent_plate(radius,front),skia.Rect.MakeWH(1280,720),
                             skia.SamplingOptions(skia.FilterMode.kNearest))
    else:
        draw_stent(canvas,x0,radius,front)


def balloon_profile(at, x, radius):
    left, right = x - BALLOON_HALF, x + BALLOON_HALF
    local_radius = radius(at) if callable(radius) else radius
    return 4 + (local_radius - 4) * ease(at, left, left + 34) * ease(right - at, 0, 34)


def balloon(canvas, x, radius):
    left, right = x-BALLOON_HALF, x+BALLOON_HALF
    shaft = [(at,center(at)) for at in range(X0,round(right)+1,5)]
    line(canvas,shaft,'#24525b',14)
    line(canvas,shaft,'#79abae',8)
    line(canvas,shaft,'#b5d9cd',2.4,140)
    xs = list(range(round(left),round(right)+1,4))
    top = [(at,center(at)-balloon_profile(at,x,radius)) for at in xs]
    bottom = [(at,center(at)+balloon_profile(at,x,radius)) for at in xs]
    path = enclosed(top,bottom)
    canvas.drawPath(path,paint('#77bdbd',171))
    line(canvas,top,'#c1ebe0',2.4,227)
    line(canvas,bottom,'#3c717b',2.4,230)
    for offset in (-MESH_HALF+4, MESH_HALF-4):
        at=x+offset
        line(canvas,[(at,center(at)-5),(at,center(at)+5)],'#e8c998',3.6)


STEPS = (
    (0, 'GUIDEWIRE', 'Crosses the narrowing'),
    (5.76, 'STENT DELIVERY', 'A folded balloon carries the mesh'),
    (15.74, 'EXPANSION', 'The mesh opens against the artery wall'),
    (24.70, 'BALLOON REMOVAL', 'The balloon deflates before withdrawal'),
    (30.99, 'STENT IN PLACE', 'The mesh supports the wider channel'),
)


def marker(canvas, x, y, target, label):
    anchor = (x, y+14)
    line(canvas,[anchor,(x,y+37),target],'#f7e6cc',1.7,200)
    canvas.drawCircle(*target,3.8,paint('#ffdfac'))
    text(canvas,label,x-10,y+8,28,'#fff1de')


def scene(canvas, t):
    canvas.drawRect(skia.Rect.MakeWH(1280,720),gradient(0,0,1280,720,['#f9faf3','#e2eee5','#d5e4dc'],[0,.6,1]))
    state = motion(t)
    channel = artery(canvas,state.expansion)
    blood_flow(canvas,t,state,channel)
    if state.stent_x+MESH_HALF > X0:
        stent(canvas,state.stent_x,state.stent_radius,False)
    wire(canvas,state.wire_tip)
    if state.delivery_x+BALLOON_HALF > X0:
        balloon(canvas,state.delivery_x,state.delivery_radius)
    if state.stent_x+MESH_HALF > X0:
        stent(canvas,state.stent_x,state.stent_radius,True)

    canvas.drawImageRect(LOGO,skia.Rect.MakeXYWH(49,30,42,42),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(canvas,'ELYSIAN BIOMEDICAL LLP',106,55,24,'#23574c')
    text(canvas,'How a coronary stent opens',48,124,48,'#123b33',TITLE)
    text(canvas,'EDUCATIONAL CUTAWAY',899,56,24,'#365f55')
    if 3.6 < t < 5.76:
        target=(state.wire_tip,center(state.wire_tip)-12)
        marker(canvas,1003,311,target,'Guidewire tip')
    elif 13.45 < t < 15.74:
        marker(canvas,745,302,(state.stent_x+92,center(state.stent_x+92)-state.stent_radius),'Crimped stent')
    elif 20.54 < t < 24.70 or t>31.07:
        marker(canvas,779,225,(743,center(743)-state.stent_radius),'Stent mesh')

    _, label, caption = next(step for step in reversed(STEPS) if t >= step[0])
    text(canvas,label,49,665,24,'#286153')
    text(canvas,caption,49,701,28,'#163f36',BOLD)
    progress = min(1.0,t/DURATION)
    canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(989,680,240,4),2,2),paint('#b3c9bc'))
    if progress>0:
        canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(989,680,240*progress,4),2,2),paint('#438672'))
