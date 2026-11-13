"""Graft comparison, flow assessment and follow-up for Cardiac Surgery 02."""

from math import sin

import skia

from . import access, angiogram, cabg_core, cabg_routes
from .cabg_recovery import footer, round_box


TOPIC = 'CARDIAC SURGERY'
INK = '#123e35'
MUTED = '#315b53'
GOLD = '#ffce92'
HOLD_SECONDS = 8


def heading(canvas, label):
    angiogram.header(canvas, label, TOPIC)


def text_fit(canvas, text, x, y, width, size, color=INK):
    measured = skia.Font(access.BOLD, size).measureText(text)
    access.text(canvas, text, x, y, min(size, int(width*size/measured)), color)


def route_marker(canvas, kind, seconds):
    path = cabg_routes.CHEST_FLOW_PATH if kind == 'chest' else cabg_routes.FREE_FLOW_PATH
    head = (seconds*.46) % 1
    tail = tuple(cabg_core.point(path, max(0, head-.38+.38*i/31)) for i in range(32))
    access.line(canvas, tail, '#86be92', 32, 210)
    access.line(canvas, tail, '#cbe9bc', 15, 221)
    cabg_core.particles(canvas, path, seconds, rate=.46, count=3, radius=11, tone=GOLD)


def make_panel(canvas, kind, seconds, x, y, w, h, *, tracer=True):
    """Show the approved routes at a different scale with their geometry intact."""
    canvas.save()
    canvas.clipRect(skia.Rect.MakeXYWH(x, y, w, h), doAntiAlias=True)
    source_x, source_y, source_w, source_h = 240, 130, 724, 515
    scale = min(w/source_w, h/source_h)
    canvas.translate(x+(w-source_w*scale)/2, y+(h-source_h*scale)/2)
    canvas.scale(scale, scale)
    canvas.translate(-source_x, -source_y)
    cabg_routes.graft_panel(canvas, kind, seconds, tracer=False)
    if tracer:
        route_marker(canvas, kind, seconds)
    canvas.restore()


def compare_routes(canvas, progress, seconds):
    cabg_core.background(canvas)
    if .56 <= progress < .73:
        forearm(canvas, progress, seconds)
        return

    heading(canvas, 'Two sources, one purpose')
    if progress < .19:
        focus = 'chest'
    elif progress < .35:
        focus = 'free'
    else:
        focus = None
    cases = (
        ('chest', 'In-place chest artery', 'Left subclavian', 'LAD'),
        ('free', 'Free vein graft', 'Ascending aorta', 'Obtuse marginal branch'),
    )
    for index, (kind, label, source, target) in enumerate(cases):
        x = 48+603*index
        selected = kind == focus or focus is None
        round_box(canvas, x, 171, 581, 457, 23, '#c8e2d3' if selected else '#d8e6df')
        round_box(canvas, x+2, 172, 577, 452, 22, '#f4faf4' if selected else '#eaf2ec')
        make_panel(canvas, kind, seconds-.7*index, x+12, 221, 553, 331, tracer=selected)
        text_fit(canvas, label, x+24, 216, 535, 38)
        access.line(canvas, [(x+24, 555), (x+555, 555)], '#9cbdaf', 1.5)
        text_fit(canvas, source, x+24, 598, 234, 31, MUTED)
        text_fit(canvas, target, x+280, 598, 273, 30, MUTED)
        access.line(canvas, [(x+240, 588), (x+270, 588)], '#5b8b79', 3)
        access.line(canvas, [(x+262, 580), (x+270, 588), (x+262, 596)], '#5b8b79', 3)
    message = ('The grafts receive blood from different connections' if progress < .35
               else 'Both join a coronary artery beyond its narrowing'
               if progress < .56 else 'The surgical plan depends on the person and the target arteries')
    footer(canvas, message)


def forearm(canvas, progress, seconds):
    heading(canvas, 'The radial artery is another option')
    canvas.save()
    canvas.translate(640, 415)
    scale = .93+.19*access.smooth((progress-.56)/.17)
    canvas.scale(scale, scale)
    canvas.translate(-640, -415)
    # An anonymized, covered arm with an isolated anatomical layer beneath it.
    shell = skia.Path()
    shell.moveTo(91, 292)
    shell.cubicTo(323, 278, 614, 295, 905, 337)
    shell.cubicTo(991, 343, 1043, 320, 1110, 330)
    shell.cubicTo(1216, 351, 1209, 441, 1113, 476)
    shell.cubicTo(1011, 510, 971, 492, 900, 489)
    shell.cubicTo(564, 524, 338, 526, 93, 496)
    shell.close()
    canvas.drawPath(shell, access.grad(90, 291, 1184, 530, ['#abcabc','#6b9b89','#578a7c']))
    for index in range(5):
        access.line(canvas, [(116, 318+index*37), (387, 317+index*40), (523, 330+index*41)],
                    '#c5dfd0', 2.4, 139)
    # Orient the hand explicitly so the radial artery remains on the thumb
    # side in the viewer's overhead illustration.
    thumb = skia.Path()
    thumb.moveTo(963, 352)
    thumb.cubicTo(1016, 320, 1059, 277, 1092, 287)
    thumb.cubicTo(1112, 295, 1107, 321, 1085, 338)
    thumb.lineTo(1034, 381)
    thumb.close()
    canvas.drawPath(thumb, access.grad(953, 299, 1113, 386, ['#99bead','#5c8c7b']))
    cut = skia.Path()
    cut.moveTo(296, 374)
    cut.cubicTo(511, 343, 783, 351, 989, 372)
    cut.cubicTo(1003, 399, 992, 438, 977, 459)
    cut.cubicTo(749, 466, 497, 473, 316, 453)
    cut.close()
    canvas.drawPath(cut, access.grad(296, 358, 992, 480, ['#edc3a1','#cf927d','#b47669']))
    art = angiogram.art
    brachial = tuple(art.curve((308, 415), ((379, 413), (443, 418), (488, 410))))
    radial = tuple(art.curve((488, 410), ((570, 377), (683, 380), (749, 390)),
                            ((819, 395), (924, 381), (977, 400))))
    ulnar = tuple(art.curve((488, 410), ((610, 440), (850, 443), (974, 440))))
    for path, w in ((brachial, 29), (ulnar, 18), (radial, 25)):
        access.line(canvas, path, '#874753', w+7)
        access.line(canvas, path, '#e79b8b', w)
        access.line(canvas, [(x, y-4) for x, y in path], '#f6c4a2', 4, 175)
    cabg_core.particles(canvas, brachial + radial[1:], seconds, rate=.41,
                       count=8, radius=7, tone=GOLD)
    call = radial[len(radial)//2]
    access.line(canvas, [call, (786, 267), (867, 267)], '#244f44', 3.3)
    angiogram.dot(canvas, *call, 6, '#f6ddac')
    access.text(canvas, 'Radial artery', 880, 257, 34, INK)
    canvas.restore()
    footer(canvas, 'An artery from the forearm can be used in suitable cases')


def probe(canvas, progress, seconds):
    cabg_core.background(canvas)
    heading(canvas, 'How the team can assess graft flow')
    angle = -3+6*access.smooth(progress)
    canvas.save()
    canvas.rotate(angle, 640, 414)
    # External probe housing. The graft remains a separate structure in its
    # open cradle, with the flow path confined to the vessel lumen.
    ellipse = skia.Rect.MakeXYWH(158, 547, 1007, 65)
    canvas.drawOval(ellipse, access.solid('#628a7a', 53))
    access.line(canvas, [(836, 486), (1019, 551), (1140, 538), (1286, 601)], '#5d8779', 20)
    access.line(canvas, [(836, 482), (1019, 547), (1140, 534), (1286, 597)], '#a6c2b6', 8)
    round_box(canvas, 449, 358, 399, 179, 44, '#23443e')
    round_box(canvas, 457, 345, 383, 179, 39, '#5c897d')
    path = tuple(angiogram.art.curve((-30, 436), ((228, 402), (467, 407), (652, 416)),
                                    ((832, 422), (1019, 374), (1297, 397))))
    for width, tone in ((123,'#306357'), (111,'#5f9a86'), (86,'#86b39b'), (58,'#3a6959')):
        access.line(canvas, path, tone, width)
    access.line(canvas, [(x,y-42) for x,y in path], '#c7e1c5', 6, 186)
    cabg_core.particles(canvas, path, seconds, rate=.50, count=12, radius=12, tone=GOLD)
    # One near-side prong rises in front of the lengthwise vessel. A smaller
    # end-on view clarifies how the open U cradles the same circular vessel.
    round_box(canvas, 463, 491, 373, 45, 19, '#6b9c8c')
    round_box(canvas, 768, 408, 68, 115, 22, '#6b9c8c')
    round_box(canvas, 771, 410, 65, 31, 15, '#9abfaf')
    access.line(canvas, [(480, 498), (789, 498)], '#b0cebb', 4)
    canvas.restore()
    round_box(canvas, 962, 173, 254, 203, 24, '#dcece1')
    arc = angiogram.art.curve((1011, 245), ((1009, 299), (1040, 332), (1088, 332)),
                               ((1136, 332), (1167, 300), (1167, 245)))
    access.line(canvas, arc, '#345d50', 28)
    access.line(canvas, arc, '#77a795', 15)
    angiogram.dot(canvas, 1089, 260, 54, '#4d806c')
    angiogram.dot(canvas, 1089, 260, 43, '#86ad95')
    angiogram.dot(canvas, 1089, 260, 33, '#37665a')
    beat = .5+.5*sin(seconds*4.3)
    angiogram.dot(canvas, 1089, 260, 14+9*beat, '#f4cb96', round(160+90*beat))
    text_fit(canvas, 'Ultrasound flow sensor', 977, 363, 221, 28, MUTED)
    access.line(canvas, [(802, 466), (893, 410), (977, 373)], '#476d60', 3.2)
    angiogram.dot(canvas, 802, 466, 6, '#d5e7d8')
    footer(canvas, 'A sensor outside the graft can measure flow'
           if progress < .60 else 'The team interprets the measurement in context')


def assessment(canvas, progress, seconds):
    if progress < .52:
        probe(canvas, progress/.52, seconds)
        return
    cabg_core.background(canvas)
    cabg_routes.distal_join(canvas, seconds, scale=1.0, transparent=1.0,
                            both=True, labels=False)
    access.rect(canvas, 0, 0, 1280, 155,
                access.grad(0, 0, 0, 155, ['#f6faf2','#e7f2e8']))
    heading(canvas, 'Both routes can feed the same artery')
    label = ('A partly open artery can still carry blood'
             if progress < .78 else 'Illustrated flow · Speeds and spacing are simplified')
    footer(canvas, label)


def followup_document(canvas, progress, seconds):
    cabg_core.background(canvas)
    heading(canvas, 'Protecting heart health after bypass')
    q = access.smooth(progress)
    canvas.save()
    canvas.translate(646, 383)
    canvas.rotate(-3+5*q)
    zoom = .98+.10*q
    canvas.scale(zoom, zoom)
    canvas.translate(-646, -383)
    round_box(canvas, 99, 182, 1099, 434, 28, '#8fb1a2')
    round_box(canvas, 85, 170, 1099, 434, 28, '#fffdf5')
    round_box(canvas, 118, 200, 526, 371, 19, '#e8f3e9')
    make_panel(canvas, 'chest', seconds, 118, 244, 526, 319)
    access.text(canvas, 'My graft map', 144, 243, 31, INK)
    access.line(canvas, [(674, 207), (674, 568)], '#bed3c6', 2)
    items = ('Prescribed medicines', 'Cardiac rehabilitation', 'Follow-up plan')
    for index, line in enumerate(items):
        amount = access.smooth((progress-index*.22)/.26)
        y = 264+91*index
        if amount:
            round_box(canvas, 716, y-29, 413*amount, 59, 15, '#cfe8d9')
        angiogram.dot(canvas, 741, y, 8+2*sin(seconds*3-index), '#5d9380')
        text_fit(canvas, line, 767, y+10, 345, 32)
    canvas.restore()
    message = ('Your care team can explain which arteries were bypassed' if progress < .72
               else 'Ask which artery each graft supplies')
    footer(canvas, message)


def follow_up(canvas, progress, seconds):
    if progress >= .36:
        followup_document(canvas, (progress-.36)/.64, seconds)
        return
    cabg_core.background(canvas)
    make_panel(canvas, 'chest', seconds, 36, 153, 1208, 491)
    heading(canvas, 'Protecting heart health after bypass')
    label = ('A working graft gives blood an additional route' if progress < .19
             else 'The artery and the graft can change over time')
    footer(canvas, label)


def recap_route(canvas, progress, seconds):
    cabg_core.background(canvas)
    kind = 'chest' if progress < .64 else 'free'
    canvas.save()
    canvas.translate(0, 24)
    cabg_routes.graft_panel(canvas, kind, seconds, tracer=True)
    path = cabg_routes.CHEST_FLOW_PATH if kind == 'chest' else cabg_routes.FREE_FLOW_PATH
    q = progress/.64 if kind == 'chest' else (progress-.64)/.36
    trail = tuple(cabg_core.point(path, max(0,q-.19+.19*i/23)) for i in range(24))
    access.line(canvas, trail, '#efab69', 36, 224)
    access.line(canvas, trail, '#ffe6b8', 17)
    angiogram.dot(canvas, *trail[-1], 19, '#ffe6b8')
    canvas.restore()
    heading(canvas, 'Follow blood from source to muscle')
    checkpoints = ('Source', 'Graft', 'Join beyond narrowing')
    thresholds = (.0, .25, .71)
    starts = (64, 281, 499)
    access.rect(canvas, 0, 644, 1280, 76, access.solid('#17463c'))
    for index, label in enumerate(checkpoints):
        if q >= thresholds[index]:
            access.text(canvas, label, starts[index], 693, 35, '#f4faef')
            if index < 2 and q >= thresholds[index+1]:
                x = starts[index]+139
                access.line(canvas, [(x, 681), (x+45, 681)], GOLD, 4)
                access.line(canvas, [(x+35, 671), (x+45, 681), (x+35, 691)], GOLD, 4)


def credits(canvas):
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#173c35'))
    angiogram.header(canvas, 'Clinical sources', TOPIC, True)
    sources = ('NHLBI and NHS · Coronary blood flow and bypass',
               'STS · Bypass conduit anatomy and configurations',
               'Circulation · Graft flow assessment and prevention')
    for index, source in enumerate(sources):
        access.text(canvas, source, 56, 221+54*index, 31, '#e8f3e9')
    access.line(canvas, [(56, 370), (825, 370)], '#659080', 2)
    access.text(canvas, 'Next in the series', 56, 426, 29, '#bbdccd')
    access.text(canvas, 'Intensive care and recovery after bypass surgery',
                56, 479, 32, '#e8f3e9')
    access.text(canvas, 'Original educational animation · Synthetic English narration',
                56, 585, 29, '#bbdccd')
    access.text(canvas, 'Full clinical links in the description', 56, 632, 29, '#bbdccd')


def closing(canvas, progress, seconds):
    duration = seconds/progress if progress else 27.
    if duration-seconds <= HOLD_SECONDS:
        credits(canvas)
        return
    recap_route(canvas, min(1., seconds/max(.01, duration-HOLD_SECONDS)), seconds)


def draw(canvas, ident, progress, seconds):
    scenes = {'P06': compare_routes, 'P07': assessment, 'P08': follow_up, 'P09': closing}
    scenes[ident](canvas, progress, seconds)
