"""Build isolated opening and assessment alternates for the restenosis episode."""

import argparse
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
import json

import skia

from render_thrombus_alternate import SAMPLE, ease, header
from tools.elysian_video import access, angiogram, restenosis
from tools.elysian_video.__main__ import FPS, HEIGHT, WIDTH
from tools.elysian_video.encode import encode_scene


HERE = Path(__file__).resolve().parent


def opening(c, t):
    if t >= 8.35:
        spread = .26+.74*ease(t,8.35,12.76)
        restenosis.lumen_view(c,t,'tissue',spread)
        header(c,'Why a stent can narrow again')
        access.text(c,'The cause shapes the next step',55,677,32,'#245f51')
        return

    c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),SAMPLE)
    fill = .065+.935*ease(t,.0,5.78)
    alpha = round(248-126*ease(t,5.1,8.35))
    x,y=angiogram.contrast_paths(c,'left',fill,alpha,-13,True)
    if t<3.0:
        access.text(c,'Simulated coronary X-ray',55,75,35,'#e1f1e7')
    else:
        angiogram.header(c,'Why a stent can narrow again','SIMULATED X-RAY',True)
    if t>=4.0:
        radius=26+8*ease(t,4.0,5.7)
        pen=access.solid('#ffe4a9',218)
        pen.setStyle(skia.Paint.kStroke_Style)
        pen.setStrokeWidth(5)
        c.drawCircle(x,y,radius,pen)
        access.line(c,[(x+radius,y-10),(x+110,y-53),(x+246,y-53)],'#ffe4a9',4)
        access.text(c,'Narrowed channel',x+122,y-67,32,'#ffefc1')


@lru_cache(maxsize=1)
def review_room():
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    c.drawRect(skia.Rect.MakeWH(1280,720),access.grad(17,0,1210,720,
               ['#f8fcf1','#dbeee1','#92bcae']))
    c.drawOval(skia.Rect.MakeXYWH(449,166,948,637),access.solid('#ecf7e7',99))
    return surface.makeImageSnapshot()


def paper(c, x, y, rotation):
    c.translate(x,y)
    c.rotate(rotation)
    brush=access.solid('#426e60',64)
    brush.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle,13))
    c.drawRoundRect(skia.Rect.MakeXYWH(-228,-178,474,398),38,38,brush)
    angiogram.block(c,-241,-199,482,402,32,access.grad(-214,-188,257,239,
                    ['#f2f9e8','#cadecf','#9bbeb0']))
    angiogram.block(c,-214,-174,428,348,20,access.solid('#f3f9ed'))
    angiogram.block(c,-96,-221,192,85,25,access.grad(-95,-211,99,-132,
                    ['#a9cbbb','#65a28d','#3d796d']))


def progress_line(c, y, amount):
    if amount<=0:
        return
    access.line(c,[(-140,y),(148,y)],'#98baaa',5,133)
    access.line(c,[(-140,y),(-140+288*amount,y)],'#4a9f84',6)
    if amount>.80:
        access.line(c,[(-180,y-5),(-171,y+5),(-155,y-10)],'#2d8a70',7)


def sheet_label(c,label,x,y):
    font=skia.Font(access.BOLD,31)
    font.setEdging(skia.Font.kAntiAlias)
    c.drawString(label,x,y,font,access.solid('#235f51'))


def artery_note(c,p):
    angiogram.block(c,-180,-109,360,147,29,access.grad(-173,-109,180,40,
                    ['#d6887d','#a54f60','#783747']))
    angiogram.block(c,-169,-82,338,92,22,access.solid('#683347'))
    size=26+24*p
    access.line(c,[(-152,-29),(-59,-29),(-11,-29+size*.29),(43,-29),(152,-29)],'#ecad8a',9)
    for i in range(8):
        x=-69+i*19
        access.line(c,[(x,-71),(x+10,-56),(x,-43),(x+10,-28),(x,-15),(x+10,0)],'#f1d6bc',2.8)
    c.drawCircle(12,-26,15+13*p,access.solid('#f8d79b',round(87+85*p)))
    for i in range(2):
        progress_line(c,84+i*46,ease(p,.12+.23*i,.61+.22*i))


def imaging_note(c,t):
    angiogram.block(c,-159,-109,318,249,25,access.solid('#20493f'))
    for radius,tone in ((99,'#ac8384'),(85,'#b89991'),(71,'#242e36')):
        c.drawCircle(0,15,radius,access.solid(tone))
    c.drawOval(skia.Rect.MakeXYWH(-60,-46,77,57),access.solid('#a47d81'))
    for i in range(14):
        angle=2*pi*i/14
        c.drawCircle(78*cos(angle),15+78*sin(angle),4.1,access.solid('#f3d6ae'))
    angle=t*3.7
    endpoint=(71*cos(angle),15+71*sin(angle))
    access.line(c,[(0,15),endpoint],'#a1e2cc',7)
    c.drawCircle(0,15,12,access.solid('#c7efda'))


def assessment(c,t):
    c.drawImageRect(review_room(),skia.Rect.MakeWH(1280,720),SAMPLE)
    header(c,'Questions after the assessment')
    if t<6.8:
        heading='What did the team find?'
        x=898+159*(1-ease(t,0,4.5))
        phase='result'
    elif t<9.65:
        heading='What caused the narrowing?'
        x=889+66*(1-ease(t,6.8,9.64))
        phase='result'
    elif t<11.85:
        heading='How did the team check it?'
        x=874+63*(1-ease(t,9.65,11.84))
        phase='imaging'
    else:
        heading='What changes in my care?'
        x=874+104*(1-ease(t,11.85,18.48))
        phase='plan'
    access.text(c,heading,56,358,40,'#164f42')
    c.save()
    paper(c,x,407,-8+8*ease(t,0,8.95))
    if phase=='imaging':
        imaging_note(c,t-9.65)
    elif phase=='plan':
        sheet_label(c,'Medicines',-154,-90)
        sheet_label(c,'Follow-up',-154,24)
        progress_line(c,-32,ease(t,11.86,15.0))
        progress_line(c,83,ease(t,14.31,18.48))
    else:
        local=ease(t,0,6.76) if t<6.8 else ease(t,6.8,9.64)
        artery_note(c,local)
    c.restore()


if __name__=='__main__':
    import ctypes

    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
    selections={'P01':(opening,'angiogram-opening'),'P08':(assessment,'care-questions')}
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenes',nargs='*',choices=tuple(selections))
    args=parser.parse_args()
    timeline=json.loads((HERE.parent/'timeline.json').read_text(encoding='utf-8-sig'))
    sizes={row['id']:row['end_frame']-row['start_frame'] for row in timeline['scenes']}
    for ident in args.scenes or selections:
        draw,name=selections[ident]
        frames=sizes[ident]
        target=HERE/f'{ident}-{name}-alternate.mp4'
        temporary=target.with_suffix('.part.mp4')
        encode_scene(temporary,frames,lambda c,i:draw(c,i/FPS),preset='veryfast',threads=1)
        temporary.replace(target)
        print(f'{target}: {frames} frames',flush=True)
