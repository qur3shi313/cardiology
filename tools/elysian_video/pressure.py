"""Physiology animation: aortic reference and distal coronary pressure."""
from math import sin, pi, exp
import json

import skia

from . import access, angiogram, restenosis, stent as art
from .__main__ import ROOT, SERIES, FPS
from .encode import encode_scene

TRACE_CYCLES = 3.2
OSTIUM = 301


def trace(c,x,y,width,amp,t,shade,*,dashed=False,fill=None):
    points=[]
    for i in range(96):
        f=i/95
        cycle=(f*TRACE_CYCLES+t*.47)%1
        value=.7*exp(-((cycle-.24)/.105)**2)+.24*exp(-((cycle-.43)/.20)**2)
        points.append((x+f*width,y-amp*value))
    if fill:
        region = [(x, y + 5), *points, (x + width, y + 5)]
        c.drawPath(access.path(region, True), access.solid(fill, 108))
    if dashed:
        for i in range(0,len(points)-2,5):
            access.line(c,points[i:i+3],shade,3.8)
    else:
        access.line(c,points,shade,4.3)


def diastolic_bands(c, x, y, width, height, t):
    """Highlight the same illustrative resting window for both pressure traces."""
    phase = (t * .47) % 1
    for beat in range(5):
        # Schematic phases only: the declining portion of each pressure beat.
        left = max(0, (beat + .62 - phase) / TRACE_CYCLES)
        right = min(1, (beat + .94 - phase) / TRACE_CYCLES)
        if left < right:
            access.rect(c, x + left * width, y, (right - left) * width, height,
                        access.solid('#9cc9b4', 82))


def aortic_connection(c):
    """Join the aortic lumen to the coronary cross-section at one open ostium."""
    bounds = skia.Rect.MakeLTRB(0, 146, 368, 645)
    c.saveLayer(bounds, None)
    outer = skia.Path()
    outer.moveTo(51, 173)
    outer.cubicTo(106, 151, 182, 150, 224, 171)
    outer.cubicTo(263, 192, 284, 183, 340, 177)
    outer.lineTo(364, 182)
    outer.lineTo(364, 607)
    outer.lineTo(338, 608)
    outer.cubicTo(291, 605, 263, 598, 220, 619)
    outer.cubicTo(169, 642, 102, 631, 51, 603)
    outer.close()
    c.drawPath(outer, art.gradient(51, 172, 51, 618, ['#a15157', '#7b3d4b', '#5d273c']))
    rim = skia.Path()
    rim.moveTo(62, 187)
    rim.cubicTo(112, 163, 180, 163, 221, 186)
    rim.cubicTo(264, 211, 291, 201, 343, 198)
    rim.lineTo(360, 200)
    rim.lineTo(360, 592)
    rim.cubicTo(294, 594, 258, 584, 215, 603)
    rim.cubicTo(166, 623, 106, 610, 62, 589)
    rim.close()
    c.drawPath(rim, art.gradient(51, 187, 51, 605, ['#e58f85', '#b44d55', '#773247', '#d76d6d', '#8d3b50'],
                                 [0, .29, .50, .83, 1]))
    lumen = skia.Path()
    lumen.moveTo(88, 211)
    lumen.cubicTo(126, 187, 172, 186, 200, 209)
    lumen.cubicTo(228, 232, 222, 269, 245, 285)
    lumen.cubicTo(266, 298, 293, 272, 340, art.center(340)-116)
    lumen.lineTo(363, art.center(363)-116)
    lumen.lineTo(363, art.center(363)+116)
    lumen.cubicTo(304, 505, 269, 495, 244, 515)
    lumen.cubicTo(220, 537, 216, 568, 189, 588)
    lumen.cubicTo(158, 608, 115, 592, 88, 574)
    lumen.close()
    c.drawPath(lumen, art.gradient(0, 270, 0, 520, ['#43152b', '#7d283e', '#8a3044', '#43182f'],
                                   [0, .30, .58, 1]))
    seam = skia.Paint(BlendMode=skia.BlendMode.kDstIn)
    seam.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(323, 0), skia.Point(363, 0)], [skia.ColorWHITE, skia.ColorTRANSPARENT]))
    c.drawRect(bounds, seam)
    c.restore()
    return lumen


def catheter_and_sensor(c, root_lumen, tip):
    """Keep the wire coaxial with the guide until it exits into the coronary lumen."""
    y = art.center(OSTIUM)
    guide = skia.Path()
    guide.moveTo(143, 177)
    guide.cubicTo(143, 267, 144, 344, 190, 373)
    guide.cubicTo(216, 390, 257, y, OSTIUM, y)
    c.save()
    c.clipPath(root_lumen, doAntiAlias=True)
    for shade, width in (('#224b49', 27), ('#84b6aa', 18), ('#d5ece1', 3)):
        stroke = access.solid(shade)
        stroke.setStyle(skia.Paint.kStroke_Style)
        stroke.setStrokeWidth(width)
        c.drawPath(guide, stroke)
    c.restore()
    if tip > OSTIUM:
        points = [(OSTIUM, y), *[(x, art.center(x)) for x in range(OSTIUM+5, int(tip), 5)],
                  (tip, art.center(tip))]
        access.line(c, points, '#433a30', 5.6)
        access.line(c, points, '#f5d89c', 2.5)
    if tip < 820:
        return None
    x = tip - 30
    y = art.center(x)
    c.drawRoundRect(skia.Rect.MakeXYWH(x-14,y-7,29,14),7,7,access.solid('#9edcda'))
    return x, y


def sensor_callout(c, label, left, width, endpoint):
    x, y = endpoint
    start = left + width / 2
    access.line(c, [(start, 177), (start, 221), (x, y)], '#f3edca', 4)
    c.drawCircle(x, y, 7, access.solid('#f3edca'))
    angiogram.block(c, left, 145, width, 39, 11, access.solid('#173e37'))
    access.text(c, label, left + 13, 173, 28, '#eff8ed')


def pressure_flow(c, t, lumen, fast):
    """Make the difference between resting and increased flow visible in the lumen."""
    c.save()
    c.clipPath(lumen, doAntiAlias=True)
    for index in range(27):
        speed = (158 if fast else 91) + 14*(index % 4)
        x = (index*127 + t*speed) % 1430
        lane = ((index*17)%91-45) / 66
        radius = art.lumen_radius(x, -1 if lane < 0 else 1, .1)
        y = art.center(x) + lane*radius
        length = 26 + 7*(index % 3)
        c.drawRoundRect(skia.Rect.MakeXYWH(x-length, y-5, length, 10), 5, 5,
                        access.solid('#ffc6a5', 118 if fast else 92))
    c.restore()


def pressure_panel(c, t, resting=False):
    angiogram.block(c, 50, 555, 1171, 133, 24, access.solid('#153832'))
    if resting:
        diastolic_bands(c, 670, 583, 489, 85, t)
    trace(c, 670, 630, 489, 56, t, '#b0e6cf', fill='#7cbf9e')
    trace(c, 670, 658, 489, 43, t, '#deb98f', dashed=True, fill='#9b7653')
    access.text(c, 'Conceptual pressure signals', 70, 615, 29, '#d9ede2')
    access.text(c, 'Illustrative signals only', 72, 654, 24, '#a9d4c3', access.REGULAR)
    access.line(c, [(487, 607), (525, 607)], '#b0e6cf', 4.3)
    access.text(c, 'Aortic', 537, 616, 27, '#d9ede2')
    for left in (487, 502, 517):
        access.line(c, [(left, 643), (left+8, 643)], '#deb98f', 3.8)
    access.text(c, 'Distal', 537, 652, 27, '#d9ede2')


def diagram(c,ident,p,t):
    access.rect(c,0,0,1280,720,access.solid('#e7f1e9'))
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(312, 0, 1280, 720))
    art_surface=art.artery(c,.1)
    pressure_flow(c, t, art_surface, fast=ident=='P04')
    c.restore()
    root_lumen = aortic_connection(c)
    tip = OSTIUM + (1126-OSTIUM)*access.smooth((p-.075)/.245) if ident == 'P03' else 1126
    sensor = catheter_and_sensor(c, root_lumen, tip)
    if ident=='P03':
        if p > .33:
            sensor_callout(c, 'Aortic reference', 105, 233, (OSTIUM-28, art.center(OSTIUM)))
        if sensor:
            sensor_callout(c, 'Downstream sensor', 886, 267, sensor)
        title='Two pressure measurements'
        if p > .33:
            pressure_panel(c, t)
        else:
            access.text(c, 'Pressure at the guide catheter and beyond the narrowing', 55, 674, 29, '#265f51')
    else:
        pressure_panel(c, t, resting=ident=='P05')
        title='FFR: increased-flow condition' if ident=='P04' else 'iFR: resting heartbeat window'
    angiogram.header(c,title,'CORONARY PHYSIOLOGY')


def sources(c, p, t):
    """Keep credits and the next episode legible throughout the closing card."""
    c.drawRect(skia.Rect.MakeWH(1280, 720),
               access.grad(0, 0, 1280, 720, ['#f7fbf4', '#dcefe4', '#bcd7cd']))
    angiogram.header(c, 'Clinical sources and production', 'CORONARY PHYSIOLOGY')
    for index, reference in enumerate((
        'AHA scientific statement on coronary physiology',
        'ACC/AHA/SCAI revascularization guideline',
        'ESC chronic coronary syndromes guideline',
    )):
        access.text(c, reference, 55, 241+47*index, 30, '#214f43')
    access.text(c, 'Original animation · Synthetic English narration',
                55, 414, 28, '#2e5d50', access.REGULAR)
    access.line(c, [(55, 449), (787, 449)], '#6c9d8b', 3)
    access.text(c, 'Next episode', 55, 508, 32, '#276a57')
    access.text(c, 'Looking inside coronary arteries', 55, 566, 37, '#173f36', access.HEADING)
    access.text(c, 'with IVUS and OCT', 55, 613, 37, '#173f36', access.HEADING)
    x, y, w, h = 844, 324, 359, 287
    if p < .50:
        angiogram.block(c, x, y, w, h, 28, access.solid('#173e37'))
        trace(c, x+38, y+154, w-76, 83, t, '#b0e6cf')
        trace(c, x+38, y+192, w-76, 57, t, '#deb98f', dashed=True)
        return
    angiogram.block(c, x, y, w, h, 28, access.solid('#22544a'))
    cx, cy = x+w/2, y+h/2
    for radius, color in ((109, '#73978c'), (92, '#aac1ab'), (76, '#143a34')):
        angiogram.dot(c, cx, cy, radius, color)
    pen = access.solid('#c4ebd2', 184)
    pen.setStyle(skia.Paint.kStroke_Style)
    pen.setStrokeWidth(4)
    for index in range(3):
        c.drawCircle(cx, cy, 18+((t*38+index*25)%53), pen)
    angiogram.dot(c, cx, cy, 13, '#e1f5db')


def review_panel(c, t, *, combine=False):
    angiogram.block(c, 675, 218, 538, 407, 31, access.solid('#183d35'))
    if combine:
        entries = ('Symptoms', 'Artery anatomy', 'Other findings')
        active = min(2, int((t-4.56)/1.38))
        for index, entry in enumerate(entries):
            y = 272 + 91*index
            fill = '#386f60' if index == active else '#274f45'
            angiogram.block(c, 729, y, 430, 71, 16, access.solid(fill))
            angiogram.dot(c, 768, y+36, 9, '#c3e8d3')
            access.text(c, entry, 799, y+48, 33, '#edf7e8')
        return
    trace(c, 725, 457, 430, 125, t, '#aee6cc', fill='#619c82')
    trace(c, 725, 520, 430, 83, t, '#e2bf9c', dashed=True, fill='#996c51')
    access.text(c, 'Illustrated pressure signals', 721, 294, 33, '#e7f5e8')


def assessment(c, t):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e7f0e8'))
    angiogram.header(c, 'Putting the result in context', 'CORONARY PHYSIOLOGY')
    if t < 4.56:
        title, detail = 'Check the signals', ('The team checks that the pressure', 'measurements are reliable.')
    elif t < 8.713:
        title, detail = 'Review the whole picture', ('Symptoms and other findings', 'help put the pressure in context.')
    elif t < 13.937:
        title, detail = 'A stent may be deferred', ('The team considers how much', 'the narrowing affects blood flow.')
    else:
        title, detail = 'Discuss treatment when it fits', ('The result and clinical picture', 'guide the next step.')
    access.text(c, title, 55, 309, 37, '#174b40')
    for index, line in enumerate(detail):
        access.text(c, line, 55, 377+45*index, 31, '#34594e', access.REGULAR)
    review_panel(c, t, combine=4.56 <= t < 8.713)


def case_panel(c, x, t, different):
    angiogram.block(c, x, 249, 551, 362, 25, access.solid('#21443c'))
    access.text(c, 'Illustrative case B' if different else 'Illustrative case A',
                x+26, 299, 29, '#e6f3e7')
    y = 376
    line = [(x+26, y-29), (x+194, y-29), (x+248, y-13), (x+301, y-29), (x+525, y-29)]
    access.line(c, line, '#c17d7c', 13)
    access.line(c, [(px, 2*y-py) for px,py in line], '#c17d7c', 13)
    for index in range(14):
        px = x+34 + (index*59 + t*(108+index%3*15)) % 473
        py = y + ((index*13)%29-14)*(.50 if x+190 < px < x+305 else 1)
        access.line(c, [(px-9, py), (px+9, py)], '#f3bf9c', 5, 147)
    trace(c, x+33, 502, 484, 59, t, '#b5e7d0', fill='#7cbf9e')
    trace(c, x+33, 568 if different else 526, 484, 44 if different else 53, t,
          '#dfb98f', dashed=True, fill='#a17b54')


def next_step(c, t):
    access.rect(c, 0, 0, 1280, 720, access.solid('#163932'))
    angiogram.header(c, 'A useful question to ask', 'CORONARY PHYSIOLOGY', True)
    access.text(c, 'What does the measurement change?', 56, 210, 42, '#ecf8ee')
    case_panel(c, 63, t, False)
    case_panel(c, 664, t, True)
    if t < 7.641:
        detail = 'Ask how the result affects your next step'
    elif t < 10.044:
        detail = 'The angiogram supplies the map'
    else:
        detail = 'Pressure adds information about the effect of the narrowing'
    access.text(c, detail, 55, 671, 30, '#c1e3d4')


def draw(c,ident,p,t):
    if ident=='P01':
        if p<.46:
            angiogram.imaging(c,'P29',p/.46,t,0)
            return
        access.rect(c,0,0,1280,720,access.solid('#11332e'))
        angiogram.header(c,'Can a narrowing limit blood supply?','CORONARY PHYSIOLOGY',True)
        for k in range(2):
            x=64+k*604
            angiogram.block(c,x,210,549,351,24,access.solid('#285148'))
            trace(c,x+41,378,465,104,t,'#d5eddc')
            trace(c,x+41,449 if k else 405,465,74,t+.05,'#f1c7a1',dashed=True)
        access.text(c,'Same-looking narrowing, different pressure pattern',56,661,31,'#b9dfd1')
        return
    if ident=='P02':
        c.drawImageRect(angiogram.radiograph_plate(),skia.Rect.MakeWH(1280,720),
                        skia.SamplingOptions(skia.FilterMode.kNearest))
        first=p<.52
        phase=p/.52 if first else (p-.52)/.48
        fill=access.smooth(phase/.65)
        opacity=round(238-115*access.smooth((phase-.64)/.36))
        x,y=angiogram.contrast_paths(c,'left',fill,opacity,-15 if first else 7,True)
        if phase>.32:
            c.drawCircle(x,y,17,access.solid('#f3d2a2',120))
        angiogram.header(c,'What the angiogram shows','SIMULATED X-RAY',True)
        return
    if ident in ('P03','P04','P05'):
        diagram(c,ident,p,t)
        return
    if ident == 'P06':
        assessment(c, t)
        return
    if ident == 'P08':
        next_step(c, t)
        return
    if ident == 'P09':
        sources(c, p, t)
        return
    if ident == 'P07':
        restenosis.card(c, 'What the test can answer', 'One question about one narrowing',
                        ('Does it limit blood supply in', 'the tested condition?'), 'pulse', p, t)
        return
    raise ValueError(f'Unknown pressure scene {ident}')

def render():
    episode=SERIES/'episode-11'
    visual=episode/'visuals'
    visual.mkdir(exist_ok=True)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    out={}
    for row in timeline['scenes']:
        ident=row['id']; n=row['end_frame']-row['start_frame']
        target=visual/f'{ident}-pressure-film.mp4'
        tmp=visual/f'{ident}-pressure-film.part.mp4'
        if not target.is_file():
            encode_scene(tmp,n,lambda c,i:draw(c,ident,i/max(1,n-1),i/FPS))
            tmp.replace(target)
        out[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':n/FPS,
                    'reference_only':False,'native_composition':True}
        (visual/'pressure-overrides.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({n} frames)',flush=True)

if __name__=='__main__':
    render()
