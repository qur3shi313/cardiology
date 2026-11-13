"""Coronary bypass episode 1: anatomy, stable disease, and emergency decisions."""

from bisect import bisect_right
from functools import lru_cache
from math import cos, hypot, pi, sin
from random import Random

import skia

from . import access, angiogram, restenosis, stent


ART = angiogram.art
CREAM, INK, WHITE = '#eaf4ec', '#143f36', '#effaf1'
GOLD, GRAFT = '#ffcc8f', '#64a998'
SAMPLE = skia.SamplingOptions(skia.FilterMode.kLinear)
LESION, JOIN = stent.LESION, 958
TOPIC = 'CARDIAC SURGERY'


def background(c, dark=False):
    colors = ['#173a36', '#265049', '#102c2b'] if dark else ['#f8fcf6', '#e4f1e7', '#c8e1d6']
    access.rect(c, 0, 0, 1280, 720, access.grad(110, 30, 1090, 690, colors))


def header(c, title, tag=TOPIC, dark=False):
    if skia.Font(access.HEADING, 48).measureText(title) > 1160:
        raise ValueError(f'CABG title exceeds its available width: {title}')
    angiogram.header(c, title, tag, dark)


def footer(c, value):
    access.rect(c, 0, 654, 1280, 66, access.solid('#153d36'))
    access.text(c, value, 55, 695, 32, WHITE)


@lru_cache(maxsize=32)
def lengths(points):
    distances = [0.]
    for a, b in zip(points, points[1:]):
        distances.append(distances[-1] + hypot(b[0] - a[0], b[1] - a[1]))
    return distances


def point(points, fraction):
    distances = lengths(points)
    target = max(0., min(1., fraction)) * distances[-1]
    index = min(len(points) - 2, max(0, bisect_right(distances, target) - 1))
    a, b = points[index:index + 2]
    width = distances[index + 1] - distances[index]
    p = (target - distances[index]) / width if width else 0
    return a[0] + p * (b[0] - a[0]), a[1] + p * (b[1] - a[1])


def particles(c, route, t, *, rate=.57, count=8, radius=9, tone=GOLD, limit=1.):
    distances = lengths(route)
    total = distances[-1]
    for index in range(count):
        q = (t * rate + index / count) % 1
        if q > limit:
            continue
        trail = []
        for k in range(4, -1, -1):
            where = max(0, q - k * .009) * total
            j = min(len(route) - 2, max(0, bisect_right(distances, where) - 1))
            a, b = route[j:j + 2]
            weight = (where - distances[j]) / (distances[j + 1] - distances[j])
            trail.append((a[0] + weight * (b[0] - a[0]), a[1] + weight * (b[1] - a[1])))
        brightness = round(222 * min(1, q * 22, (1 - q) * 22))
        access.line(c, trail, tone, radius * 1.5, brightness)
        angiogram.dot(c, *trail[-1], radius, tone, brightness)


def center(x):
    return stent.center(x) + 36


XS = tuple(range(-90, 1371, 8))
PCI_XS = tuple(range(-90, 1371, 5))
PLAQUE_XS = tuple(range(460, 846, 3))
GRAFT_PATH = tuple(ART.curve(
    (-65, 248), ((102, 235), (230, 190), (413, 211)),
    ((557, 225), (691, 230), (802, 266)),
    ((901, 298), (869, 369), (JOIN, center(JOIN))),
))
DISTAL_FLOW = GRAFT_PATH + tuple((x, center(x)) for x in XS if x > JOIN)


@lru_cache(maxsize=1)
def pci_plate():
    surface = skia.Surface(2560, 1440)
    c = surface.getCanvas()
    c.scale(2, 2)
    outer_top = [(x, stent.center(x)-211-11*cos(x/150)) for x in PCI_XS]
    outer_bottom = [(x, stent.center(x)+218+10*sin(x/170)) for x in PCI_XS]
    rim_top = [(x, stent.center(x)-193-9*cos(x/150)) for x in PCI_XS]
    rim_bottom = [(x, stent.center(x)+198+9*sin(x/170)) for x in PCI_XS]
    outer = access.path(outer_top + outer_bottom[::-1], True)
    c.save()
    c.translate(0, 15)
    shadow = access.solid('#573c3d', 53)
    shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.BlurStyle.kNormal_BlurStyle, 19))
    c.drawPath(outer, shadow)
    c.restore()
    c.drawPath(outer, access.grad(0, 172, 0, 623, ['#a05056','#6b303f','#541f34']))
    c.drawPath(access.path(rim_top + rim_bottom[::-1], True),
               access.grad(0, 190, 0, 590, ['#e58f85','#b44d55','#773247','#d76d6d','#8d3b50'], [0,.29,.50,.83,1]))
    access.line(c, outer_top, '#f6aba1', 4, 193)
    access.line(c, outer_bottom, '#50243a', 3, 210)
    access.line(c, [(x, stent.center(x)-178-9*cos(x/150)) for x in PCI_XS], '#fcb5a3', 3, 92)
    access.line(c, [(x, stent.center(x)+175+9*sin(x/170)) for x in PCI_XS], '#f9b29b', 4, 75)
    return surface.makeImageSnapshot()


@lru_cache(maxsize=1)
def plaque_grain():
    result = {}
    for side in (-1, 1):
        rng = Random(10 + side)
        points = []
        for _ in range(95):
            x = rng.uniform(487, 814)
            points.append((x, rng.uniform(.2, .9), rng.uniform(.4, 1.4), rng.randrange(32, 94)))
        result[side] = points
    return result


@lru_cache(maxsize=3)
def pci_lumen(expansion):
    surface = skia.Surface(2560, 1440)
    c = surface.getCanvas()
    c.scale(2, 2)
    top = [(x, stent.center(x)-stent.lumen_radius(x, -1, expansion)) for x in PCI_XS]
    bottom = [(x, stent.center(x)+stent.lumen_radius(x, 1, expansion)) for x in PCI_XS]
    inner = access.path(top + bottom[::-1], True)
    c.drawPath(inner, access.grad(0, 270, 0, 520, ['#43152b','#7d283e','#8a3044','#43182f'], [0,.30,.58,1]))
    access.line(c, top, '#f4aa99', 3.2, 208)
    access.line(c, bottom, '#f18e83', 3.2, 180)
    for side, thickness in ((-1, 58), (1, 38)):
        edge = [(x, stent.center(x)+side*stent.lumen_radius(x, side, expansion)) for x in PLAQUE_XS]
        away = [(x, y+side*thickness*stent.plaque(x)) for x, y in edge]
        c.drawPath(access.path(edge + away[::-1], True),
                   access.grad(475, 262, 805, 502, ['#c58a63','#f0c998','#b47a60'], [0,.45,1]))
        access.line(c, edge, '#ffe0aa', 2.2, 210)
        for x, distance, radius, opacity in plaque_grain()[side]:
            y = stent.center(x)+side*(stent.lumen_radius(x, side, expansion)+distance*thickness*stent.plaque(x))
            angiogram.dot(c, x, y, radius, '#825345', opacity)
    return surface.makeImageSnapshot(), inner


def pci_vessel(c, expansion):
    extent = skia.Rect.MakeWH(1280, 720)
    nearest = skia.SamplingOptions(skia.FilterMode.kNearest)
    c.drawImageRect(pci_plate(), extent, nearest)
    overlay, lumen = pci_lumen(round(expansion * 240) / 240)
    c.drawImageRect(overlay, extent, nearest)
    return lumen


@lru_cache(maxsize=2)
def cutaway_plate(occluded):
    surface = skia.Surface(1280, 720)
    c = surface.getCanvas()
    background(c)
    lower = tuple((x, 590 + 25 * sin(x / 212)) for x in XS)
    upper = tuple((x, 352 + 18 * cos(x / 263)) for x in XS)
    c.drawPath(access.path(upper + lower[::-1], True),
               access.grad(560, 330, 560, 624, ['#e6a399', '#ba716e', '#814658', '#5d3a50']))
    c.save()
    c.clipPath(access.path(upper + lower[::-1], True), doAntiAlias=True)
    for i in range(7):
        c.drawPath(access.path(ART.curve((-130, 360 + i * 39),
            ((240, 311 + i * 42), (645, 467 + i * 33), (1400, 357 + i * 42)))),
            skia.Paint(Color=access.color('#f5b3a0', 41), StrokeWidth=2, Style=skia.Paint.kStroke_Style, AntiAlias=True))
    c.restore()
    for radius, tones in ((108, ['#80485c','#a85b67','#744152']),
                          (97, ['#f5af9b','#be6c73','#8a4a5f']),
                          (79, ['#cf8180','#ae586b','#653a54'])):
        top = [(x, center(x) - radius) for x in XS]
        bottom = [(x, center(x) + radius) for x in XS]
        c.drawPath(access.path(top + bottom[::-1], True), access.grad(640, 312, 640, 548, tones))
    top = [(x, center(x) - stent.lumen_radius(x, -1, 0)) for x in XS]
    bottom = [(x, center(x) + stent.lumen_radius(x, 1, 0)) for x in XS]
    c.drawPath(access.path(top + bottom[::-1], True),
               access.grad(640, 365, 640, 509, ['#7c394d','#582e44','#854656']))
    # Plaque remains visible above the same lumen in every match cut.
    shoulders = [(x, y) for x, y in top if LESION - 181 < x < LESION + 185]
    backing = [(x, center(x) - 86) for x, _ in shoulders]
    c.drawPath(access.path(backing + shoulders[::-1], True),
               access.grad(575, 354, 671, 462, ['#f0cd99', '#d79e75', '#b67565']))
    access.line(c, shoulders, '#f4cb96', 4, 222)
    for j in range(23):
        x = 499 + (j * 37 % 263)
        y_edge = center(x) - stent.lumen_radius(x, -1, 0)
        if y_edge - center(x) + 86 > 15:
            y = center(x) - 86 + (y_edge - center(x) + 86) * (.25 + (j % 5) * .09)
            angiogram.dot(c, x, y, 2 + j % 4, '#f6c49b', 130)
    if occluded:
        clot = ART.curve((LESION - 38, center(LESION) - 37),
                         ((LESION - 9, center(LESION) - 53), (LESION + 38, center(LESION) - 24), (LESION + 42, center(LESION) + 44)),
                         ((LESION + 33, center(LESION) + 72), (LESION - 38, center(LESION) + 62), (LESION - 38, center(LESION) - 37)))
        c.drawPath(access.path(clot, True),
                   access.grad(LESION - 31, 403, LESION + 21, 483, ['#b24d52','#8a344e','#52243c']))
        for i in range(9):
            angiogram.dot(c, LESION - 24 + i * 29 % 50, center(LESION) - 27 + i * 23 % 75,
                          2.5 + i % 3, '#d47b70', 123)
    return surface.makeImageSnapshot()


def graft_cutaway(c, t, reveal=1., graft=True, *, occluded=False):
    """Fixed schematic of a separate arterial supply feeding a downstream graft."""
    c.drawImage(cutaway_plate(occluded), 0, 0, SAMPLE)
    for lane in (-25, 3, 27):
        for index in range(7):
            x = 60 + 554 * ((t * .47 + index / 7 + lane / 113) % 1)
            if x > LESION - 64:
                continue
            y = center(x) + lane + sin(t * 2 + index) * 3
            access.line(c, [(x - 29, y), (x, y)], '#f3a68a', 7, 150)
            angiogram.dot(c, x, y, 5, '#ffd2a2', 175)
    # A visibly smaller stream can still traverse this narrowed, unblocked artery.
    if not occluded:
        small_flow = ((480., 455.), (573., 466.), (633., 477.), (687., 471.),
                      (769., 451.), (902., 423.), (1110., 408.), (1300., 418.))
        particles(c, small_flow, t, rate=.31, count=3, radius=4, tone='#f5ac93')
    if not graft:
        return
    path = ART.trace(GRAFT_PATH, max(0., min(1., reveal)))
    access.line(c, [(x + 4, y + 9) for x, y in path], '#1c5c51', 63, 52)
    access.line(c, path, '#205b50', 60)
    access.line(c, path, GRAFT, 51)
    access.line(c, path, '#245549', 34)
    access.line(c, [(x, y - 20) for x, y in path], '#c4e6ca', 4, 189)
    if reveal >= .995:
        y = center(JOIN)
        # The neck connects to the open lumen downstream, under the intact lesion.
        access.line(c, [(JOIN - 28, y - 31), (JOIN, y), (JOIN + 37, y - 4)], '#416b58', 34)
        particles(c, DISTAL_FLOW, t, count=9, radius=9)


def callout(c, target, elbow, end, label, *, dark=False):
    ink = WHITE if dark else INK
    plate = '#18453e' if dark else '#e8f4e9'
    width = skia.Font(access.BOLD, 31).measureText(label)
    access.line(c, [target, elbow, end], '#d1ede0' if dark else '#315f51', 3)
    angiogram.dot(c, *target, 6, GOLD if dark else '#225f51')
    angiogram.block(c, end[0], end[1] - 28, width + 22, 45, 10, access.solid(plate, 242))
    access.text(c, label, end[0] + 11, end[1] + 5, 31, ink)


def graft_result(c, p, t, *, labels=True):
    graft_cutaway(c, t, reveal=access.smooth(p / .56), graft=p > 0)
    if labels:
        header(c, 'Why choose bypass surgery?')
        footer(c, 'A new route carries blood beyond the narrowing')


def heart_xy(a):
    return 630 + (a[0] - 311) * 2.53, 191 + (a[1] - 92) * 1.105


@lru_cache(maxsize=4)
def heart_base():
    surface = skia.Surface(1280, 720)
    c = surface.getCanvas()
    xy = heart_xy

    heart = [xy(a) for a in ART.MYOCARDIUM]
    c.drawPath(access.path([(x + 13, y + 13) for x, y in heart], True), access.solid('#3c323f', 53))
    silhouette = access.path(heart, True)
    volume = skia.Paint(AntiAlias=True)
    volume.setShader(skia.GradientShader.MakeRadial(skia.Point(432, 346), 578,
        [access.color(tone) for tone in ('#f5c4a6','#d89587','#9d586f','#58374f')],
        [0, .33, .75, 1]))
    c.drawPath(silhouette, volume)
    rvs = [xy(a) for a in ART.RV_SHADOW]
    c.drawPath(access.path(rvs, True), access.grad(254, 319, 651, 606, ['#d98e88','#995d73']))
    for offset in range(7):
        a = ART.curve((227 + 21 * offset, 233),
                      ((230 + offset * 22, 278), (268 + 24 * offset, 364), (316 + 25 * offset, 420)))
        c.save()
        c.clipPath(silhouette, doAntiAlias=True)
        access.line(c, [xy(v) for v in a], '#f5b29f', 1.8, 59)
        c.restore()
    aorta = tuple(xy(a) for a in ART.AORTA)
    access.line(c, aorta, '#793e5a', 82)
    access.line(c, aorta, '#c88183', 70)
    access.line(c, tuple((x - 10, y - 6) for x, y in aorta), '#edab96', 9, 175)
    vessels = [ART.RCA, ART.LEFT_MAIN, ART.LAD, ART.LCX, *ART.RCA_TWIGS, *ART.LEFT_TWIGS]
    arteries = tuple(tuple(xy(a) for a in branch) for branch in vessels)
    for index, artery in enumerate(arteries):
        w = (18, 19, 17, 14)[index] if index < 4 else 7
        access.line(c, artery, '#77384f', w + 6)
        access.line(c, artery, '#e18e7c', w)
        access.line(c, [(x - 1.4, y - 1) for x, y in artery], '#ffc1a2', max(2, w * .19), 199)
    return surface.makeImageSnapshot(), aorta, arteries


def coronary_map(c, t, *, mode='normal', dark=False, demand=False, healed=False, supplied=False):
    """Anterior projection from the existing named coronary anatomy."""
    background(c, dark)
    image, aorta, arteries = heart_base()
    beat = sin(2 * pi * (1.24 if demand else .86) * t)
    scale = 1. + .025 * beat
    c.save()
    c.translate(630, 400)
    c.scale(scale, scale)
    c.translate(-630, -400)
    c.drawImage(image, 0, 0, SAMPLE)
    if mode == 'left main':
        lesions = [(1, .54)]
    elif mode == 'multivessel':
        lesions = [(2, .30), (3, .56), (0, .62)]
    elif mode == 'urgent':
        lesions = [(2, .31)] if not healed else [(3, .54)]
    elif mode == 'weakened':
        lesions = [(2, .39), (3, .53)]
    else:
        lesions = [(2, .31)] if mode == 'narrow' else []
    if supplied or mode == 'urgent' and not healed:
        territory = [heart_xy(a) for a in ART.curve((339, 303),
            ((350, 284), (395, 306), (408, 358)), ((435, 420), (415, 477), (382, 498)),
            ((352, 501), (326, 432), (318, 378)), ((312, 348), (315, 320), (339, 303)))]
        c.drawPath(access.path(territory, True), access.solid('#a7d3a5' if supplied else '#442f59', 97))
        access.line(c, territory, '#f1e4bb' if supplied else '#e3b1b7', 3, 180)
    for index, artery in enumerate(arteries[:4]):
        blocked = [q for k, q in lesions if k == index]
        if index == 2 and mode == 'urgent' and not healed:
            particles(c, artery, t, limit=.30, count=5, radius=6)
        elif blocked:
            particles(c, artery, t, count=4, radius=4)
        else:
            particles(c, artery, t, count=5, radius=6 if index != 1 else 3)
    if mode == 'urgent' and healed:
        treated = tuple(point(arteries[2], .22 + .20 * i / 15) for i in range(16))
        access.line(c, treated, '#d5e7d9', 20)
        access.line(c, treated, '#9b525d', 9)
        for x, y in treated[2:-1:3]:
            access.line(c, [(x - 8, y - 4), (x + 8, y + 4)], '#e7f0e7', 2)
        particles(c, arteries[2], t, count=5, radius=5)
    if supplied:
        target = point(arteries[2], .68)
        origin = point(aorta, .20)
        graft = tuple(ART.curve(origin, ((origin[0] + 248, origin[1] + 46),
                                       (target[0] + 218, target[1] - 80), target)))
        access.line(c, graft, '#24584e', 26)
        access.line(c, graft, '#72b8a3', 18)
        access.line(c, graft, '#3f7060', 11)
        distal = tuple(point(arteries[2], .68 + .32 * i / 25) for i in range(1, 26))
        particles(c, graft + distal, t, count=7, radius=6)
    marks = []
    for index, q in lesions:
        x, y = point(arteries[index], q)
        angiogram.dot(c, x, y, 20, '#4e3448', 220)
        angiogram.dot(c, x, y, 13 + 1.5 * cos(t * 4), '#f5c78c')
        angiogram.dot(c, x + 4, y - 3, 5, '#fff0c5')
        marks.append((630 + (x - 630) * scale, 400 + (y - 400) * scale))
    c.restore()
    return marks


def ultrasound(c, t, *, weak=False):
    background(c, True)
    x, y = 600, 207
    beam = ART.curve((187, 578), ((382, 695), (832, 720), (1013, 578)))
    field = access.path([(x, y), *beam], True)
    c.drawPath(field, access.grad(400, 212, 777, 657, ['#71948a','#324f50','#102b31']))
    c.save()
    c.clipPath(field, doAntiAlias=True)
    for i in range(11):
        shade = 26 + i % 3 * 11
        yy = y + i * 41 + ((t * 88) % 41)
        access.line(c, [(172, yy), (1032, yy)], '#8bc6b0', 4, shade)
    for i in range(104):
        px = 195 + i * 157 % 815
        py = 215 + i * 47 % 448
        angiogram.dot(c, px, py, 1 + i % 3, '#c9e8ce', 33 + i % 3 * 13)
    beat = (1 - cos(2 * pi * t * .90)) / 2
    narrowing = beat * (14 if weak else 44)
    wall = ART.curve((471, 337), ((393, 391), (408, 506), (521, 574)),
                     ((558, 607), (635, 625), (690, 572)), ((778, 502), (796, 391), (726, 337)),
                     ((680, 290), (538, 280), (471, 337)))
    cavity = ART.curve((497 + narrowing, 357), ((450 + narrowing, 397), (452 + narrowing, 473), (525, 542 - narrowing)),
                       ((570, 577 - narrowing), (628, 580 - narrowing), (677, 535 - narrowing)),
                       ((730 - narrowing, 482), (760 - narrowing, 390), (700 - narrowing, 348)),
                       ((653, 319), (559, 316), (497 + narrowing, 357)))
    c.drawPath(access.path(wall, True), access.grad(467, 346, 726, 601, ['#b0d2b7','#87b0a3','#557d7a']))
    c.drawPath(access.path(cavity, True), access.solid('#173a42'))
    access.line(c, cavity, '#d8e6b9', 7)
    c.restore()
    access.line(c, [(x, y), *beam, (x, y)], '#80b1a1', 2, 142)


def title_cutaway(c, t, local, *, title=True):
    reveal = access.smooth((local - .13) / 2.9)
    graft_cutaway(c, t, reveal=reveal, graft=local > .13)
    if title:
        header(c, 'Why choose bypass surgery?')
        footer(c, 'Blood reaches the coronary artery beyond the narrowing')
    if local < 4.7:
        callout(c, (LESION, 418), (688, 575), (736, 575), 'Narrowing')
    else:
        callout(c, (JOIN, center(JOIN)), (1000, 569), (1010, 569), 'Graft joins here')


def opening(c, p, t):
    if p < .858:
        title_cutaway(c, t, t, title=t >= 4.8)
    else:
        coronary_map(c, t, mode='narrow', supplied=True)
        callout(c, (851, 574), (922, 585), (940, 585), 'Muscle downstream')
        header(c, 'The graft supplies downstream muscle')
        footer(c, 'The narrowed segment stays in place')


def tests(c, p, t):
    if p < .32 or .573 <= p < .767:
        coronary_map(c, t, mode='narrow' if p > .139 else 'normal', demand=p > .246)
        header(c, 'Coronary arteries supply the heart muscle')
        if p >= .573:
            footer(c, 'The team checks where the disease is and what it affects')
        else:
            footer(c, 'Heart muscle may need more blood during activity' if p > .246 else 'Plaque can narrow the artery opening')
    elif p < .573:
        graft_cutaway(c, t, graft=False)
        header(c, 'Narrowing limits blood flow')
        footer(c, 'Reduced blood supply can cause angina' if p > .413 else 'The opening is narrowed by plaque')
        callout(c, (LESION, 418), (688, 585), (735, 585), 'Plaque')
    elif p < .86:
        c.drawImageRect(angiogram.radiograph_plate(), skia.Rect.MakeWH(1280,720), SAMPLE)
        q = (t * .51) % 1
        x, y = angiogram.contrast_paths(c, 'left', access.smooth(q / .68), round(243 - 52 * access.smooth((q - .77) / .23)), -10, True)
        if q > .48:
            callout(c, (x, y), (x + 74, y - 62), (min(x + 107, 1042), y - 62), 'Narrowing', dark=True)
        header(c, 'What the tests show', 'SIMULATED ANGIOGRAM', True)
        footer(c, 'An angiogram shows the openings of the arteries')
    else:
        ultrasound(c, t)
        header(c, 'What the tests show', 'ILLUSTRATED ULTRASOUND', True)
        footer(c, 'Ultrasound helps show how well the pumping chamber works')


def figure(c, t):
    background(c)
    # The face is blank and fully framed by a hood. Long sleeves, gloves and
    # trousers keep this anonymous silhouette fully covered.
    access.line(c, [(0, 602), (1280, 602)], '#a7ccba', 7)
    for x in range(80, 1280, 138):
        shift = (t * 50) % 138
        access.line(c, [(x - shift, 614), (x + 135 - shift, 694)], '#b6d9c4', 4, 140)
    x, y = 663, 335 + 4 * sin(t * 5.6)
    sway = 41 * sin(t * 4.4)
    angiogram.dot(c, x, y - 112, 60, '#295b55')
    angiogram.dot(c, x + 9, y - 108, 44, '#427b70')
    torso = ART.curve((x - 77, y - 61), ((x - 101, y - 28), (x - 72, y + 78), (x - 50, y + 112)),
                       ((x - 8, y + 132), (x + 46, y + 121), (x + 65, y + 97)),
                       ((x + 69, y + 42), (x + 99, y - 33), (x + 55, y - 63)))
    c.drawPath(access.path(torso, True), access.grad(x - 85, y - 65, x + 65, y + 120, ['#5d9588','#265c52']))
    for side in (-1, 1):
        foot = (x + side * (44 + sway), 585)
        access.line(c, [(x + side * 29, y + 104), (x + side * 29 + .6 * sway, y + 183), foot],
                    '#2d5652', 40)
        access.line(c, [foot, (foot[0] + 22, foot[1] + 5)], '#254940', 22)
        glove = (x + side * (99 + .44 * sway), y + 68)
        access.line(c, [(x + side * 56, y - 30), (x + side * 92, y + 12), glove], '#467c72', 32)
        angiogram.dot(c, *glove, 18, '#6a9484')


def stent_view(c, p, t, *, emergency=False):
    background(c)
    deflation = access.smooth((p - .54) / .18)
    removal = access.smooth((p - .72) / .25)
    delivery = access.smooth(p / .19)
    expansion = access.smooth((p - .20) / .34)
    position = stent.LESION - (stent.LESION + 270) * removal
    stent_position = stent.LESION - 410 * (1 - delivery)
    balloon_position = position - 410 * (1 - delivery)
    offset = 36 if not emergency else 0
    c.save()
    c.translate(0, offset)
    lumen = pci_vessel(c, expansion)
    c.save()
    if deflation < .45:
        c.clipRect(skia.Rect.MakeLTRB(0, 0, stent.LESION - 70, 720))
    restenosis.trace_channel(c, t, lumen, expansion, .54 + .46 * deflation)
    c.restore()
    radius = 14 + 102 * expansion
    stent.stent(c, stent_position, radius, False)
    if removal < 1:
        stent.wire(c, 1126 - 1182 * removal)
        stent.balloon(c, balloon_position, 12 + 104 * expansion * (1 - deflation))
    stent.stent(c, stent_position, radius, True)
    c.restore()
    header(c, 'Emergency PCI can restore blood flow' if emergency else 'PCI opens the artery from inside')
    message = 'The equipment reaches the affected section' if p < .2 else 'The balloon expands the stent at the narrowing'
    footer(c, 'The stent supports the treated section' if p > .55 else message)


def stable(c, p, t):
    if p < .401:
        if p < .190:
            figure(c, t)
            header(c, 'Stable coronary disease')
        else:
            coronary_map(c, t, mode='narrow', demand=True)
            header(c, 'What if angina still limits daily life?')
        footer(c, 'Medicines and heart-healthy habits remain part of care')
    elif p < .604:
        stent_view(c, (p - .401) / .203, t)
    elif p < .716:
        graft_cutaway(c, t, reveal=access.smooth((p - .604) / .05))
        header(c, 'Bypass uses a separate vessel')
        footer(c, 'The graft meets the artery beyond the narrowing')
    else:
        coronary_map(c, t, mode='narrow')
        header(c, 'The team weighs the treatment options')
        footer(c, 'Some people continue with medicines alone')


def findings(c, p, t):
    if p < .404:
        marks = coronary_map(c, t, mode='left main')
        callout(c, marks[0], (778, 272), (896, 272), 'Before the split')
        header(c, 'Significant left main disease')
        footer(c, 'The left main supplies two major coronary branches')
    elif p < .729:
        marks = coronary_map(c, t, mode='multivessel')
        callout(c, marks[0], (790, 535), (899, 535), 'LAD narrowing')
        header(c, 'Diabetes and multivessel disease')
        footer(c, 'The pattern includes the left anterior descending artery')
    else:
        # Split composition keeps the distinct case map beside its pumping view.
        background(c)
        for x, function in ((14, coronary_map), (644, ultrasound)):
            c.save()
            c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, 183, 622, 447), 16, 16), doAntiAlias=True)
            c.translate(x - (155 if x == 14 else 62), 162)
            c.scale(.74 if x == 14 else .64, .69)
            if x == 14:
                function(c, t, mode='weakened')
            else:
                function(c, t, weak=True)
            c.restore()
        access.text(c, 'Several arteries', 42, 606, 31, INK)
        access.text(c, 'Illustrated ultrasound', 666, 606, 31, WHITE)
        header(c, 'Weak pumping and several lesions')
        footer(c, 'The team studies location and complexity as well as the number of narrowings')


def urgent(c, p, t):
    if p < .238:
        coronary_map(c, t, mode='urgent', dark=True)
        header(c, 'A heart attack can stop blood flow', dark=True)
        footer(c, 'The team aims to restore flow to threatened muscle quickly')
    elif p < .383:
        stent_view(c, (p - .238) / .145, t, emergency=True)
    elif p < .735:
        graft_cutaway(c, t, reveal=access.smooth((p - .383) / .09), occluded=True)
        header(c, 'Urgent bypass is an option in selected cases')
        footer(c, 'The team needs suitable arteries beyond the blockage')
    else:
        marks = coronary_map(c, t, mode='urgent', healed=True)
        callout(c, marks[0], (940, 320), (971, 320), 'Other narrowing')
        header(c, 'The emergency artery has reopened')
        footer(c, 'Other complex narrowings may be considered later')


SCENES = {'P01': opening, 'P02': tests, 'P03': stable, 'P04': findings, 'P05': urgent}


def draw(canvas, ident, progress, seconds):
    SCENES[ident](canvas, progress, seconds)
