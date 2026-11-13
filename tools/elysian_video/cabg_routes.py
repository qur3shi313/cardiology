"""Native CABG graft routing and end-to-side junction illustrations."""

from math import sin

import skia

from . import access as art
from . import angiogram
from . import cabg_graft as gfx


INK = gfx.INK
MUTED = gfx.MUTED
FLOW = gfx.FLOW
ANATOMY = gfx.ANATOMY
TOPIC = 'CARDIAC SURGERY'


def oblique(point):
    x, y = point
    return .95*x + .17*(y-346) + 43, .93*y + 21


# The obtuse marginal branch originates on the circumflex and follows the
# lateral left-ventricular surface. Its native stenosis precedes the graft join.
OM_START = gfx.LCX[23]
OM = ANATOMY.curve(OM_START,
                   ((825, 411), (841, 435), (857, 463)),
                   ((879, 491), (869, 524), (844, 550)))
OM_LESION_INDEX = 9
OM_TARGET_INDEX = 23
OM_LESION = OM[OM_LESION_INDEX]
OM_TARGET = OM[OM_TARGET_INDEX]
OM_TWIG = ANATOMY.curve(OM[27], ((884, 525), (903, 534), (912, 552)))
FREE = ANATOMY.curve(gfx.ROOT_JUNCTION,
                     ((636, 237), (721, 246), (799, 263)),
                     ((871, 278), (934, 318), (940, 384)),
                     ((950, 429), (943, 488), (906, 500)),
                     ((895, 504), (880, 508), OM_TARGET))
CHEST_FLOW_PATH = (gfx.AORTA[:39] + gfx.SUBCLAVIAN[1:19] +
                   gfx.CHEST_GRAFT[1:] + gfx.LAD[gfx.GRAFT_INDEX+1:])
FREE_FLOW_PATH = tuple(map(oblique, gfx.AORTA[:17] + FREE[1:] + OM[OM_TARGET_INDEX+1:]))
FREE_SIDE_PATH = tuple(map(oblique, gfx.AORTA[:17] + FREE[1:] +
                           OM[OM_TARGET_INDEX+1:28] + OM_TWIG[1:]))
CHEST_SIDE_PATH = (gfx.AORTA[:39] + gfx.SUBCLAVIAN[1:19] + gfx.CHEST_GRAFT[1:] +
                   gfx.LAD[gfx.GRAFT_INDEX+1:38] + gfx.DIAGONAL[1:])


def heading(canvas, label):
    angiogram.header(canvas, label, TOPIC)


def one_marker(canvas, points, seconds, *, speed=170, offset=0., repeat=None, size=12):
    """One visible pulse travels inside an already continuous lumen."""
    lengths = gfx.distances(points)
    distance = lengths[-1]
    period = repeat or (distance + 40) / speed
    head = ((seconds + offset) % period) * speed
    if head > distance + 32:
        return
    alpha = round(255 * min(1, head/25, max(0, (distance+32-head)/45)))
    tail = max(0, head - 52)
    steps = 14
    trail = tuple(gfx.location(points, lengths, tail + (head-tail)*i/steps)
                  for i in range(steps+1))
    art.line(canvas, trail, '#ebaa64', size*1.48, alpha)
    art.line(canvas, trail, '#ffe6ab', size*.72, alpha)
    point = trail[-1]
    angiogram.dot(canvas, *point, size*.51, '#fff1c6', alpha)


def mark_stenosis(canvas, route, index, size):
    lesion = route[index-2:index+3]
    art.line(canvas, lesion, '#623b49', size+2)
    art.line(canvas, lesion, '#e7b286', size*.56)
    art.line(canvas, lesion, '#f7c0ac', size*.27)


def connector(canvas, point, anchor, tip, text, x, y):
    gfx.guide(canvas, (point, anchor, tip), text, x, y)


def spotlight(canvas, point, seconds):
    """Keep the current anatomical feature conspicuous while a tracer travels."""
    x, y = point
    sweep = .5 + .5*sin(seconds*3.7)
    radius = 38 + 27*sweep
    for delta, width, alpha in ((0, 12, 185), (15, 4, 100)):
        brush = art.solid('#c8893d', round(alpha-28*sweep))
        brush.setStyle(skia.Paint.kStroke_Style)
        brush.setStrokeWidth(width)
        canvas.drawCircle(x, y, radius+delta, brush)
    angiogram.dot(canvas, x, y, 4.5, '#fff0c0', 224)


def chest_route(canvas, progress, seconds, *, labels=True, tracer=True, thoracic=.36, joined=.61):
    gfx.draw_anatomy(canvas)
    start = max(.08, thoracic-.12)
    grow = art.smooth((progress-start)/(joined-start))
    gfx.vessel(canvas, gfx.SUBCLAVIAN, 20, gfx.ARTERIAL)
    gfx.vessel(canvas, gfx.CHEST_GRAFT, 18, gfx.GRAFT, 78)
    if grow > 0:
        gfx.vessel(canvas, ANATOMY.trace(gfx.CHEST_GRAFT, grow), 18, gfx.GRAFT)
    if tracer:
        if progress < joined:
            gfx.graft_pulses(canvas, gfx.AORTA[:39] + gfx.SUBCLAVIAN[1:], seconds,
                             speed=144, depth=19, tail=89)
        else:
            one_marker(canvas, CHEST_FLOW_PATH, seconds, speed=188)
            if progress > joined + (1-joined)*.58:
                one_marker(canvas, CHEST_SIDE_PATH, seconds, speed=188, offset=1.8, size=8)
    if labels:
        focus = gfx.CHEST_ORIGIN if progress < thoracic else (gfx.CHEST_GRAFT[19]
                if progress < joined else gfx.TARGET)
        spotlight(canvas, focus, seconds)
    if labels and progress < thoracic:
        connector(canvas, gfx.CHEST_ORIGIN, (946, 192), (1225, 192),
                  'Left subclavian artery', 946, 179)
    elif labels and progress < joined:
        connector(canvas, gfx.CHEST_GRAFT[19], (921, 322), (1224, 322),
                  'Internal thoracic artery', 909, 307)
    elif labels:
        connector(canvas, gfx.TARGET, (928, 464), (1227, 464),
                  'LAD beyond narrowing', 920, 451)
        connector(canvas, gfx.PLAQUE, (382, 392), (68, 392), 'Original narrowing', 69, 378)


def free_route(canvas, progress, seconds, *, labels=True, tracer=True, aortic=.27, joined=.56):
    canvas.save()
    # The consistent affine view approximates a left-oblique teaching diagram.
    canvas.concat(skia.Matrix.MakeAll(.95, .17, 43-.17*346, 0, .93, 21, 0, 0, 1))
    gfx.draw_anatomy(canvas)
    gfx.vessel(canvas, OM, 12, gfx.ARTERIAL)
    gfx.vessel(canvas, OM_TWIG, 7, gfx.ARTERIAL)
    mark_stenosis(canvas, OM, OM_LESION_INDEX, 12)
    start = max(.08, aortic-.025)
    grow = art.smooth((progress-start)/(joined-start))
    if grow > 0:
        visible = ANATOMY.trace(FREE, grow)
        # The soft separating rim makes the foreground graft's overlap with
        # the descending aortic silhouette read as an overpass.
        art.line(canvas, visible, '#e0ebe0', 26)
        gfx.vessel(canvas, visible, 18, gfx.GRAFT)
        proximal = FREE[:3]
        gfx.vessel(canvas, proximal, 18, gfx.GRAFT)
    canvas.restore()
    if tracer:
        if progress < joined:
            gfx.graft_pulses(canvas, tuple(map(oblique, gfx.AORTA[:23])), seconds,
                             speed=160, depth=22, tail=93)
        else:
            one_marker(canvas, FREE_FLOW_PATH, seconds, speed=190)
            if progress > joined + (1-joined)*.47:
                one_marker(canvas, FREE_SIDE_PATH, seconds, speed=190, offset=1.7, size=8)
    if labels:
        focus = gfx.ROOT_JUNCTION if progress < joined-.10 else OM_TARGET
        spotlight(canvas, oblique(focus), seconds)
    if labels and progress < joined-.10:
        origin = oblique(gfx.ROOT_JUNCTION)
        connector(canvas, origin, (421, 245), (67, 245), 'Ascending aorta', 69, 230)
    elif labels and progress < joined+(1-joined)*.44:
        origin = oblique(OM_START)
        connector(canvas, origin, (995, 351), (1230, 351), 'Circumflex', 1029, 337)
        target = oblique(OM_TARGET)
        connector(canvas, target, (992, 495), (1230, 495),
                  'Obtuse marginal branch', 905, 480)
    elif labels:
        target = oblique(OM_TARGET)
        connector(canvas, target, (995, 497), (1230, 497), 'Obtuse marginal branch', 905, 484)
        connector(canvas, oblique(OM_LESION), (754, 511), (58, 511),
                  'Original narrowing', 62, 496)


def graft_panel(canvas, kind, seconds, *, tracer=True):
    """Render either complete teaching case without titles or callouts."""
    if kind == 'chest':
        chest_route(canvas, 1, seconds, labels=False, tracer=tracer)
    elif kind == 'free':
        free_route(canvas, 1, seconds, labels=False, tracer=tracer)
    else:
        raise ValueError(f'Unknown bypass graft type: {kind}')


# The same longitudinal LAD section is kept across P01, P02, P03, and P07.
# Both source paths end at the center of a shared distal channel.
NATIVE_JOIN = (774, 435)
NATIVE_PATH = ANATOMY.curve((70, 435), ((286, 418), (378, 430), (500, 435)),
                            ((603, 445), (702, 435), NATIVE_JOIN),
                            ((909, 432), (1050, 463), (1240, 436)))
CUT_GRAFT = ANATOMY.curve((411, 226), ((482, 231), (562, 256), (608, 305)),
                          ((654, 368), (681, 421), NATIVE_JOIN))
OUTLET = NATIVE_PATH[32:]
CUT_GRAFT_FLOW = CUT_GRAFT + OUTLET[1:]
DISTAL_SIDE = ANATOMY.curve(OUTLET[7],
                            ((934, 493), (967, 547), (1084, 595)))
GRAFT_BRANCH = CUT_GRAFT + OUTLET[1:8] + DISTAL_SIDE[1:]


def layered_coronary(canvas, channel, width, *, opacity=255, graft=False):
    if graft:
        colors = ('#1d5d55', '#4c887c', '#8dc4a5')
    else:
        colors = ('#8a5360', '#ba7b7d', '#e5a59b')
    art.line(canvas, channel, colors[0], width+5, opacity)
    art.line(canvas, channel, colors[1], width-3, opacity)
    art.line(canvas, tuple((x, y-6) for x, y in channel), colors[2], width*.42, opacity)


def plaque(canvas, *, opacity=255):
    lower = ANATOMY.curve((419, 483), ((451, 469), (470, 444), (503, 443)),
                          ((549, 444), (559, 466), (598, 485)))
    upper = ANATOMY.curve((427, 382), ((451, 392), (470, 425), (503, 426)),
                          ((548, 423), (553, 401), (585, 385)))
    for shape, base in ((lower, 487), (upper, 379)):
        outlines = shape + ((shape[-1][0], base), (shape[0][0], base))
        canvas.drawPath(art.path(outlines, True), art.solid('#efba81', opacity))
        art.line(canvas, shape, '#f6d09c', 3, opacity)


def native_tracer(canvas, seconds):
    length = gfx.distances(NATIVE_PATH)
    for offset in (0, 294, 587, 881):
        distance = (seconds*179 + 86 + offset) % length[-1]
        x, y = gfx.location(NATIVE_PATH, length, distance)
        slender = 468 <= x <= 547
        trail = min(distance, 13 if slender else 58)
        tail = gfx.location(NATIVE_PATH, length, distance-trail)
        opacity = round(255 * min(1, distance/24, (length[-1]-distance)/24))
        art.line(canvas, (tail, (x, y)), '#e9ab79', 3.6 if slender else 15, opacity)
        art.line(canvas, (tail, (x, y)), '#ffe6b2', 2.1 if slender else 7, opacity)


def distal_join(canvas, seconds, *, scale=1.0, transparent=1.0, both=False,
                labels=True, include_graft=True, branch=False, marker_offset=2.1):
    """One fixed end-to-side junction, with optional native and graft inflow."""
    canvas.save()
    canvas.translate(640, 392)
    canvas.scale(scale, scale)
    canvas.translate(-640, -392)
    haze = art.grad(116, 318, 1172, 621, ['#f5e5da', '#f2d2c2', '#d9b4af'])
    gfx.oval(canvas, 87, 309, 1136, 329, haze)
    for i in range(13):
        x = 132 + i*83
        striation = ANATOMY.curve((x, 512),
                                  ((x+22, 544), (x+50, 552), (x+61, 564)))
        art.line(canvas, striation, '#f8e3d6', 2, 140)

    if branch:
        layered_coronary(canvas, DISTAL_SIDE, 43)
    layered_coronary(canvas, NATIVE_PATH, 115)
    if include_graft:
        layered_coronary(canvas, CUT_GRAFT, 96, graft=True)
        art.line(canvas, NATIVE_PATH, '#874b62', 82)
        if branch:
            art.line(canvas, DISTAL_SIDE, '#9d5a6c', 30)
        lumen = round(255 * transparent)
        art.line(canvas, CUT_GRAFT, '#234d4a', 62, lumen)
        art.line(canvas, CUT_GRAFT[-5:], '#874b62', 58, lumen)
        art.line(canvas, NATIVE_PATH[29:35], '#874b62', 65, lumen)
    else:
        art.line(canvas, NATIVE_PATH, '#874b62', 82)
    plaque(canvas, opacity=round(130 + 125*transparent))

    if include_graft:
        if transparent > .68:
            path = GRAFT_BRANCH if branch else CUT_GRAFT_FLOW
            one_marker(canvas, path, seconds, speed=234, offset=marker_offset, size=16)
    else:
        both = True
    if both:
        # Fade and compress the native tracer inside the actual residual channel.
        native_tracer(canvas, seconds)
    if labels:
        connector(canvas, (495, 415), (307, 296), (75, 296), 'Narrowing', 77, 280)
        if include_graft:
            connector(canvas, (695, 408), (849, 254), (1200, 254), 'Graft', 1067, 238)
    canvas.restore()


def opening(canvas, progress, seconds, cues):
    gfx.studio_light(canvas)
    wide = cues.get('wide', .67)
    if progress < wide:
        # Offset the first tracer so it crosses the distal join in the opening beat.
        distal_join(canvas, seconds, branch=progress > .42, marker_offset=.46)
        if seconds >= 1.22:
            spotlight(canvas, NATIVE_JOIN, seconds)
        if seconds >= 3.4:
            heading(canvas, 'How a bypass graft works')
    else:
        chest_route(canvas, 1, seconds, labels=True)
        heading(canvas, 'How a bypass graft works')
    gfx.footer(canvas, 'The graft delivers blood beyond the original narrowing')


def original_route(canvas, progress, seconds, cues):
    gfx.studio_light(canvas)
    coronary = cues.get('coronary', .20)
    lad = cues.get('lad', .39)
    cutaway = cues.get('cutaway', .60)
    if progress < cutaway:
        gfx.draw_anatomy(canvas)
        gfx.graft_pulses(canvas, gfx.AORTA[:41], seconds, speed=164, depth=19, tail=87)
        if progress < coronary:
            connector(canvas, gfx.AORTA[15], (465, 236), (65, 236), 'Aorta', 68, 219)
        elif progress < lad:
            for route in (gfx.LAD, gfx.LCX):
                gfx.graft_pulses(canvas, gfx.LEFT_MAIN+route[1:], seconds,
                                 speed=132, depth=10, tail=61)
            connector(canvas, gfx.LEFT_MAIN[6], (474, 323), (65, 323),
                      'Left main coronary artery', 66, 307)
            connector(canvas, gfx.LCX[27], (1000, 376), (1224, 376),
                      'Circumflex artery', 987, 361)
        else:
            gfx.graft_pulses(canvas, gfx.LEFT_MAIN+gfx.LAD[1:], seconds,
                             speed=153, depth=13, tail=74)
            connector(canvas, gfx.LAD[21], (867, 436), (1223, 436),
                      'Left anterior descending', 898, 421)
    else:
        distal_join(canvas, seconds, include_graft=False)
        connector(canvas, (535, 435), (839, 273), (1219, 273),
                  'Some blood can pass', 867, 257)
    heading(canvas, 'The original route')
    gfx.footer(canvas, 'The coronary arteries bring oxygen-rich blood to the heart muscle')


def open_connection(canvas, progress, seconds, cues):
    gfx.studio_light(canvas)
    open_at = cues.get('open', .24)
    closer = cues.get('closer', .71)
    transparency = art.smooth((progress-open_at)/.18)
    camera = 1 if progress < closer else 1 + .115*art.smooth((progress-closer)/.14)
    distal_join(canvas, seconds, scale=camera, transparent=transparency,
                branch=progress > .55, labels=False)
    heading(canvas, 'The graft joins beyond the narrowing')
    if progress < open_at:
        connector(canvas, NATIVE_JOIN, (935, 302), (1220, 302),
                  'End-to-side join', 950, 285)
    elif progress < closer:
        connector(canvas, NATIVE_JOIN, (917, 294), (1220, 294),
                  'Continuous open channel', 887, 277)
    else:
        target = DISTAL_SIDE[-5]
        point = 640+(target[0]-640)*camera, 392+(target[1]-392)*camera
        connector(canvas, point, (1084, 552), (1226, 552),
                  'To heart muscle', 1009, 536)
    gfx.footer(canvas, 'The original plaque remains in the artery wall')


def covered_leg(canvas, seconds):
    # A simple sex-neutral trouser-leg outline with a vein map inside it.
    edge = ANATOMY.curve((148, 276), ((138, 305), (143, 341), (166, 394)),
                          ((182, 442), (182, 486), (178, 533)),
                          ((173, 564), (200, 582), (229, 578)),
                          ((278, 578), (272, 547), (248, 532)),
                          ((247, 487), (258, 418), (245, 389)),
                          ((228, 347), (230, 300), (221, 273)))
    canvas.drawPath(art.path(edge, True),
                    art.grad(137, 294, 260, 585, ['#d3e8d8', '#a8cebf', '#77a598']))
    vein = ANATOMY.curve((195, 290), ((181, 354), (204, 380), (214, 418)),
                          ((221, 461), (213, 524), (217, 549)))
    gfx.vessel(canvas, vein, 10, gfx.VENOUS)
    curve = ANATOMY.trace(vein, .20 + .73 * ((seconds*.42) % 1))
    art.line(canvas, curve[-10:], '#c9ebe8', 8)
    spotlight(canvas, curve[-1], seconds)
    art.text(canvas, 'Saphenous vein', 66, 605, 29, INK)


def chest_case(canvas, progress, seconds, cues):
    gfx.studio_light(canvas)
    chest_route(canvas, progress, seconds, thoracic=cues.get('thoracic', .36),
                joined=cues.get('joined', .61))
    heading(canvas, 'Chest artery graft')
    gfx.footer(canvas, 'Its upper connection keeps the original blood supply')


def vein_case(canvas, progress, seconds, cues):
    gfx.studio_light(canvas)
    leg_until = cues.get('aorta', .27)
    free_route(canvas, progress, seconds, labels=progress >= leg_until,
               aortic=leg_until, joined=cues.get('joined', .56))
    if progress < leg_until:
        covered_leg(canvas, seconds)
    heading(canvas, 'Free vein graft')
    if progress < .63:
        gfx.footer(canvas, 'In this example, a vein from the leg forms a separate graft')
    else:
        gfx.footer(canvas, 'The vein graft now carries oxygen-rich blood to the heart muscle')


SCENES = {
    'P01': opening,
    'P02': original_route,
    'P03': open_connection,
    'P04': chest_case,
    'P05': vein_case,
}


def draw(canvas, ident, progress, seconds, *, cues=None):
    SCENES[ident](canvas, progress, seconds, cues or {})
