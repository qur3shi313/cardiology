"""Render a clearer clot illustration without replacing the active source."""

from functools import lru_cache
from math import cos, exp, pi, sin
from pathlib import Path
import json

import skia

from tools.elysian_video import access, angiogram, stent
from tools.elysian_video.__main__ import FPS, HEIGHT, WIDTH
from tools.elysian_video.encode import encode_scene


HERE = Path(__file__).resolve().parent
LESION = stent.LESION
SAMPLE = skia.SamplingOptions(skia.FilterMode.kNearest)


def ease(t, start, end):
    return access.smooth((t-start)/(end-start))


@lru_cache(maxsize=1)
def artery_plate():
    image = skia.Surface(WIDTH, HEIGHT)
    c = image.getCanvas()
    c.scale(2, 2)
    c.drawRect(skia.Rect.MakeWH(1280, 720), access.grad(0, 0, 1280, 720,
               ['#fafcf4', '#e8f2e8', '#c7ddd1']))
    lumen = stent.artery(c, 1.)
    stent.stent(c, LESION, 116, False)
    return image.makeImageSnapshot(), lumen


def clot_shape(spread):
    width = 64+75*spread
    upper, lower = [], []
    for x in range(round(LESION-width), round(LESION+width)+1, 3):
        u = (x-LESION)/width
        boundary = stent.center(x)-stent.lumen_radius(x, -1, 1.)
        profile = exp(-abs(u/.61)**2.65) * max(0., 1-u*u)**.49
        texture = .92+.05*sin(x*.127)+.037*sin(x*.259+.9)
        upper.append((x,boundary-.4))
        lower.append((x,boundary+(46+211*spread)*profile*texture))
    return stent.enclosed(upper, lower), lower


def moving_flow(c, t, lumen, clot, obstruction):
    c.save()
    c.clipPath(lumen, doAntiAlias=True)
    c.clipPath(clot, skia.ClipOp.kDifference, doAntiAlias=True)
    full = 1-ease(obstruction, .32, .91)
    cutoff = LESION-84
    for i in range(25):
        lane = ((i*37)%157-78)/100
        q = (i*113+t*(110+i%5*12))%1470-95
        x = cutoff-((cutoff-q) % (cutoff+95)) if i%3 else q
        opacity = 188 if i%3 else round(176*full)
        if opacity < 3:
            continue
        fade = .58+.42*ease(cutoff-x,0,115) if i%3 else 1
        points = []
        for step in range(5):
            px = x-step*(9+i%3*1.7)
            y = stent.center(px)+lane*stent.lumen_radius(px,-1,1.)
            points.append((px,y))
        access.line(c, points, '#f8be9e', 7.6, round(opacity*fade))
    c.restore()


def header(c, title, dark=False):
    c.drawImageRect(access.LOGO, skia.Rect.MakeXYWH(55,24,52,52), SAMPLE)
    access.text(c, 'Elysian Biomedical LLP', 121, 60, 31, '#e9f9ef' if dark else '#004b3d')
    access.text(c, title, 55, 145, 49, '#eff9ef' if dark else '#004b3d', access.HEADING)


def show_thrombus(c, t):
    base, lumen = artery_plate()
    c.drawImageRect(base, skia.Rect.MakeWH(1280, 720), SAMPLE)
    spread = ease(t, 1.6, 6.8)
    clot, edge = clot_shape(spread)
    moving_flow(c, t, lumen, clot, spread)
    c.save()
    c.clipPath(lumen, doAntiAlias=True)
    c.drawPath(clot, access.grad(556, 291, 733, 516,
               ['#e47878','#b73e54','#6b203c']))
    c.save()
    c.clipPath(clot, doAntiAlias=True)
    for i in range(52):
        x = 507+(i*59)%279
        y = 280+(i*73)%245
        c.drawCircle(x,y,2.8+i%5*.93,access.solid('#ffd0b1',35+i%4*13))
    c.restore()
    access.line(c, edge, '#fda19a', 3.7, 235)
    c.restore()
    stent.stent(c, LESION, 116, True)
    header(c, 'Stent thrombosis')
    x,y=max(edge,key=lambda point:point[1])
    access.line(c, [(x+11,y-21),(862,y-32),(862,251),(951,251)],'#f6d2b9',5,235)
    c.drawCircle(x+11,y-21,8,access.solid('#ffe1bb'))
    access.rect(c,951,226,224,55,access.solid('#182d2c',236))
    access.text(c, 'Clot in the stent', 965, 263, 29, '#fbf5e7')
    if t>5.7:
        access.text(c, 'Blood flow can stop suddenly', 55, 670, 32, '#254e44')
    else:
        access.text(c, 'A separate illustrative example', 55, 670, 32, '#254e44')


def show_emergency(c, t):
    c.drawRect(skia.Rect.MakeWH(1280,720),access.grad(0,0,1280,720,
               ['#173935','#194e43','#173531']))
    header(c, 'Get emergency help', dark=True)
    access.text(c,'Severe chest pressure', 57, 330, 46, '#eff9ed')
    access.text(c,'Sudden trouble breathing', 57, 430, 46, '#eff9ed')
    for i in range(3):
        phase=(t*.51+i/3)%1
        radius=84+96*phase
        pen=access.solid('#99d2be',round(152*(1-phase)))
        pen.setStyle(skia.Paint.kStroke_Style)
        pen.setStrokeWidth(5)
        c.drawCircle(975,378,radius,pen)
    angiogram.block(c,922,275,106,206,24,access.solid('#a2d3c0'))
    angiogram.block(c,933,287,84,179,15,access.solid('#346d62'))
    angle=pi*.65
    points=[(975+39*cos(angle+i*pi/25),385+39*sin(angle+i*pi/25)) for i in range(18)]
    access.line(c,points,'#edf8eb',11)


def draw(c,t):
    if t<14.1:
        show_thrombus(c,t)
    else:
        show_emergency(c,t-14.1)


if __name__ == '__main__':
    import ctypes

    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
    timeline=json.loads((HERE.parent/'timeline.json').read_text(encoding='utf-8-sig'))
    scene=next(row for row in timeline['scenes'] if row['id']=='P04')
    frames=scene['end_frame']-scene['start_frame']
    target=HERE/'P04-thrombus-alternate.mp4'
    temporary=target.with_suffix('.part.mp4')
    encode_scene(temporary,frames,lambda c,i:draw(c,i/FPS),preset='veryfast',threads=1)
    temporary.replace(target)
    print(f'{target}: {frames} frames')
