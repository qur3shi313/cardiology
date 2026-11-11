"""Illustrated femoral angiography scenes, independent of the legacy video frames."""

from argparse import ArgumentParser
from functools import lru_cache
from math import hypot, pi, sin
from pathlib import Path
import os
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
FONTS = ROOT / 'outputs/website-v2/elysian-corporate/assets/fonts'
FPS = 30
INK = '#132f2c'
TEAL = '#246c60'
PALE = '#e7f3ea'
WHITE = '#f6fff7'
GOLD = '#ffdb83'
WIRE = '#ffe8a3'
SHEATH = '#71ccb1'
CATHETER = '#edf8ef'
DILATOR = '#f3e4bf'
MICRO_COLOR = '#81b1a9'
AR_WALL = '#673741'
AR_BODY = '#a6525c'
AR_EDGE = '#d18580'

# Final-output names deliberately retain the source storyboard numbers.
SCENES = {
    'R12': ('R12-route', 260 / FPS),
    'F04': ('F04-locator', 164 / FPS),
    'F05': ('F05-needle', 255 / FPS),
    'F06': ('F06-fine-wire', 300 / FPS),
    'F07': ('F07-needle-out', 95 / FPS),
    'F08': ('F08-introducer', 207 / FPS),
    'F09': ('F09-fine-wire-out', 280 / FPS),
    'F10': ('F10-exchange-wire', 182 / FPS),
    'F11': ('F11-introducer-out', 216 / FPS),
    'F12': ('F12-working-sheath', 169 / FPS),
    'F13': ('F13-exchange-out', 318 / FPS),
    'F16': ('F16-route', 507 / FPS),
    'F24': ('F24-withdraw', 259 / FPS),
    'F25': ('F25-close', 233 / FPS),
    'F26': ('F26-checks', 309 / FPS),
    'F27': ('F27-recovery', 284 / FPS),
}


def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


def phase(progress, start, stop):
    return smooth((progress - start) / (stop - start))


def mix(a, b, amount):
    return a + (b - a) * amount


def curve(start, *sections):
    points = [start]
    for first, second, end in sections:
        a = points[-1]
        for i in range(1, 23):
            t = i / 22
            u = 1 - t
            points.append(tuple(u**3*a[j] + 3*u*u*t*first[j] + 3*u*t*t*second[j] + t**3*end[j]
                                for j in (0, 1)))
    return tuple(points)


class PathTrace:
    def __init__(self, points):
        self.points = points
        self.distance = [0.0]
        for a, b in zip(points, points[1:]):
            self.distance.append(self.distance[-1] + hypot(b[0]-a[0], b[1]-a[1]))

    def trace(self, progress, start=0):
        first = self.distance[-1] * start
        last = self.distance[-1] * progress
        if last <= first:
            return ()
        output = []
        for index, (a, b) in enumerate(zip(self.distance, self.distance[1:])):
            lo, hi = max(a, first), min(b, last)
            if hi <= lo:
                continue
            if not output:
                output.append(self.interpolate(index, (lo-a)/(b-a)))
            output.append(self.interpolate(index, (hi-a)/(b-a)))
        return tuple(output)

    def interpolate(self, index, amount):
        a, b = self.points[index:index+2]
        return mix(a[0], b[0], amount), mix(a[1], b[1], amount)


@lru_cache(maxsize=24)
def font(size, title=False):
    filename = 'josefin-sans-variable.ttf' if title else 'fira-sans-semibold.ttf'
    face = ImageFont.truetype(FONTS / filename, size)
    if title:
        face.set_variation_by_axes([600])
    return face


class Canvas:
    """Draw 640×360 logical coordinates at 3× delivery resolution."""

    def __init__(self, image, camera=(1, 0, 0)):
        self.image = image
        self.scale = image.width / 640
        self.pen = ImageDraw.Draw(image)
        self.zoom, self.dx, self.dy = camera

    def project(self, point):
        x, y = point
        return x*self.zoom+self.dx, y*self.zoom+self.dy

    def point(self, x, y):
        u, v = self.project((x, y))
        return round(u*self.scale), round(v*self.scale)

    def box(self, bounds):
        return self.point(*bounds[:2]) + self.point(*bounds[2:])

    def line(self, points, fill, width):
        if len(points) > 1:
            self.pen.line([self.point(*p) for p in points], fill=fill,
                          width=max(1, round(width*self.scale*self.zoom)), joint='curve')

    def poly(self, points, fill):
        self.pen.polygon([self.point(*p) for p in points], fill=fill)

    def roundrect(self, box, radius, fill, outline=None, width=1):
        self.pen.rounded_rectangle(self.box(box), round(radius*self.scale*self.zoom), fill=fill,
                                   outline=outline, width=max(1, round(width*self.scale*self.zoom)))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.pen.ellipse(self.box(box), fill=fill, outline=outline,
                         width=max(1, round(width*self.scale*self.zoom)))

    def dot(self, point, radius, fill, outline=None, width=1):
        x, y = point
        self.ellipse((x-radius, y-radius, x+radius, y+radius), fill, outline, width)

    def text(self, x, y, message, size, fill=INK, *, title=False, anchor='lt'):
        self.pen.text(self.point(x, y), message, font=font(round(size*self.scale), title),
                      fill=fill, anchor=anchor)


@lru_cache(maxsize=8)
def field(size, dark=False):
    top = (29, 67, 66) if dark else (242, 250, 243)
    bottom = (12, 37, 40) if dark else (173, 209, 198)
    ramp = Image.new('RGB', (1, 360))
    ramp.putdata([tuple(round(mix(a, b, y / 359)) for a, b in zip(top, bottom))
                  for y in range(360)])
    return ramp.resize(size, Image.Resampling.BICUBIC)


def mark(canvas, title, *, dark=False, right=False):
    canvas.text(614 if right else 29, 25, title, 28, WHITE if dark else INK,
                title=True, anchor='rt' if right else 'lt')


def label(canvas, text, x, y, target, *, dark=False):
    color = '#d9f6e8' if dark else '#174b44'
    tx, ty = target
    lines = text.splitlines()
    floor = y + len(lines)*21
    canvas.line(((x, floor), (x, floor+4), (tx, ty)), color, 1.15)
    canvas.dot(target, 3.2, WHITE, color, 1)
    for index, line in enumerate(lines):
        canvas.text(x, y+21*index, line, 18, color)


def vessel(canvas, points, width=18):
    canvas.line(points, AR_WALL, width+4)
    canvas.line(points, AR_EDGE, width)
    canvas.line(points, AR_BODY, width-4)
    canvas.line(tuple((x-1.6, y-1.6) for x, y in points), '#c46c6d', 1.4)


def device(canvas, points, color, width):
    canvas.line(points, '#1b3e3a', width+3)
    canvas.line(points, color, width)


# Coordinates use the same patient-right frontal orientation and retrograde
# centerline as episode-01/production/vascular_art.py:FEMORAL.
ROUTE = PathTrace(curve((222, 483),
                        ((226, 463), (225, 440), (241, 412)),
                        ((254, 392), (271, 382), (295, 373)),
                        ((312, 364), (316, 328), (318, 293)),
                        ((321, 258), (325, 215), (325, 181)),
                        ((325, 145), (308, 139), (295, 147)),
                        ((284, 154), (285, 182), (286, 199))))
RADIAL_ROUTE = PathTrace(curve((60, 397),
                               ((70, 364), (93, 318), (115, 281)),
                               ((133, 254), (139, 205), (153, 174)),
                               ((165, 145), (196, 135), (219, 132)),
                               ((240, 128), (257, 128), (267, 121)),
                               ((272, 134), (280, 143), (291, 151)),
                               ((286, 160), (285, 183), (286, 199))))
OTHER_ILIAC = curve((295, 373), ((322, 383), (342, 398), (347, 424)),
                    ((350, 444), (355, 472), (360, 494)))
INTERNAL_ILIAC = curve((259, 391), ((265, 401), (275, 415), (280, 433)))
ARCH_BRANCHES = (
    curve((316, 148), ((337, 122), (365, 129), (393, 137)), ((414, 142), (430, 154), (439, 177))),
    curve((304, 144), ((306, 125), (309, 99), (312, 76))),
    curve((292, 150), ((280, 130), (274, 103), (271, 80))),
)
TORSO = curve((240, 65), ((229, 94), (204, 101), (179, 107)),
              ((140, 115), (124, 138), (114, 184)), ((98, 252), (84, 325), (74, 414)),
              ((91, 427), (112, 433), (131, 433)), ((146, 383), (160, 336), (172, 286)),
              ((177, 349), (168, 419), (170, 501)), ((233, 520), (354, 519), (419, 500)),
              ((419, 429), (410, 357), (416, 286)), ((433, 347), (447, 396), (462, 435)),
              ((481, 432), (501, 427), (514, 414)), ((504, 339), (490, 263), (478, 186)),
              ((468, 141), (451, 116), (410, 108)), ((382, 102), (357, 96), (347, 65)))
HEART = curve((287, 196), ((258, 166), (226, 192), (236, 227)),
              ((248, 262), (287, 289), (328, 300)), ((366, 274), (375, 218), (340, 193)),
              ((322, 180), (303, 181), (287, 196)))


def map_shape(canvas, project, *, radial=False):
    canvas.poly(tuple(project((x+9, y+7)) for x, y in TORSO), '#244e4c')
    canvas.poly(tuple(map(project, TORSO)), '#3f8175')
    canvas.line(tuple(map(project, TORSO)), '#5d9b87', 1.5)
    if radial:
        sleeve = ((115, 170), (163, 168), (154, 266), (88, 416), (43, 410), (73, 314))
        canvas.poly(tuple(map(project, sleeve)), '#3f8175')
        canvas.line(tuple(map(project, sleeve[2:6])), '#5d9b87', 1.5)
    for y in (124, 141, 432, 447, 462, 477):
        canvas.line((project((178, y)), project((411, y))), '#428579', 1.0)
    canvas.poly(tuple(map(project, HEART)), '#8b4854')
    canvas.line(tuple(map(project, HEART)), '#be756f', 2.2)
    for branch in (*ARCH_BRANCHES, OTHER_ILIAC, INTERNAL_ILIAC):
        vessel(canvas, tuple(map(project, branch)), 7)
    vessel(canvas, tuple(map(project, ROUTE.points)), 11)
    if radial:
        vessel(canvas, tuple(map(project, RADIAL_ROUTE.points)), 10)
    root = project((286, 199))
    canvas.line(((root[0]-5.5, root[1]+1), (root[0], root[1]+3), (root[0]+5.5, root[1]+1)), '#e7b09a', 1.6)


def route_frame(size, p, *, radial=False):
    if p < .14 and not radial:
        return route_intro(size, p/.14)
    if not radial:
        p = (p-.14)/.86
    base = field(size, True).copy()
    canvas = Canvas(base)
    scale = .70 + .20*phase(p, .33, .98)
    wire_p = .05 + .934 * min(1, p / .985)
    catheter_p = max(.024, wire_p - mix(.055, .024, phase(p, .88, 1)))
    active = RADIAL_ROUTE if radial else ROUTE
    route_tip = active.trace(wire_p)[-1]
    focus_y = mix(-14, 138-scale*route_tip[1], phase(p, .34, .92))
    project = lambda pt: (54 + pt[0]*scale, focus_y + pt[1]*scale)
    map_shape(canvas, project, radial=radial)
    skin = project(active.points[0])
    sheath = (skin[0]-19, skin[1]+9), skin, project(active.trace(.027)[-1])
    device(canvas, sheath, SHEATH, 5.5)
    device(canvas, tuple(map(project, active.trace(catheter_p))), CATHETER, 4.5)
    exposed = tuple(map(project, active.trace(wire_p, catheter_p)))
    device(canvas, exposed, WIRE, 2.4)
    if exposed:
        canvas.dot(exposed[-1], 3.5, GOLD, '#664830', .9)
    if radial:
        boundaries = (.19, .47, .69, .84)
        labels = ('Right radial artery', 'Brachial artery', 'Axillary and subclavian',
                  'Brachiocephalic trunk', 'Aortic root')
        stage = labels[sum(wire_p >= boundary for boundary in boundaries)]
    elif wire_p < .12:
        stage = 'Right femoral artery'
    elif wire_p < .32:
        stage = 'Iliac arteries'
    elif wire_p < .51:
        stage = 'Abdominal aorta'
    elif wire_p < .77:
        stage = 'Thoracic aorta'
    else:
        stage = 'Aortic arch and root'
    mark(canvas, 'Wrist to the heart' if radial else 'Groin to the heart', dark=True)
    canvas.text(454, 259, stage, 19, WHITE, anchor='mt')
    if exposed:
        x, y = exposed[-1]
        canvas.line(((x+6, y), (365, 247), (454, 247)), '#94c8ad', 1.1)
    return base


def entry_layer(size, p, scene):
    image = field(size, True).copy()
    canvas = Canvas(image)
    for y in range(95, 341, 14):
        canvas.line(((14, y+16), (105, y-4), (334, y+9), (625, y-2)), '#275450', 1)
    for y in range(98, 343, 28):
        canvas.line(((14, y+13), (122, y-10), (340, y+7), (625, y-8)), '#36635b', 2)
    # Optical movement in one plane. Track the active access window while
    # clinical tools follow their separately defined physical trajectories.
    zoom = .93 + .27*p
    shift_x = mix(-12, 9, p) if scene in ('F04', 'F25') else mix(8, -9, p)
    shift_y = mix(4, 20, p) if scene in ('F07', 'F09', 'F11', 'F24') else mix(3, -13, p)
    art = Canvas(image, (zoom, (1-zoom)*207+shift_x, (1-zoom)*201+shift_y))
    draw_entry_window(art)
    return image, art, canvas


def draw_entry_window(canvas):
    canvas.roundrect((54, 106, 398, 324), 48, '#153e3d')
    canvas.roundrect((66, 114, 385, 315), 46, '#a46d61')
    canvas.roundrect((72, 117, 380, 306), 43, '#d3a581')
    canvas.roundrect((76, 123, 374, 299), 42, '#e4bc9b')
    # The only uncovered area is the schematic access window. Its visible
    # internal vessel is a longitudinal cutaway with a distal bifurcation.
    canvas.poly(((75, 212), (134, 203), (241, 211), (342, 194), (375, 209),
                 (371, 275), (340, 301), (113, 299), (77, 272)), '#b8786f')
    canvas.line(((76, 212), (134, 203), (241, 211), (342, 194), (375, 209)), '#f0c9a2', 4)
    main = curve((103, 254), ((145, 250), (222, 255), (280, 252)), ((315, 251), (344, 247), (365, 238)))
    branch = curve((165, 252), ((145, 257), (129, 270), (117, 285)))
    vessel(canvas, branch, 11)
    vessel(canvas, main, 25)
    canvas.line(((89, 216), (131, 211), (232, 219), (346, 203)), '#cc8e7f', 1.8)


def entry_frame(size, p):
    image, art, canvas = entry_layer(size, p, 'F04')
    mark(canvas, 'Finding the groin artery', dark=True)
    x = mix(315, 225, phase(p, .12, .87))
    label(canvas, 'Right common\nfemoral artery', 445, 160, art.project((x, 251)), dark=True)
    art.dot((x, 251), 8+phase(p, .54, .99)*10, None, '#f0df9c', 1.6)
    return image


# Project the reviewed femoral-proof PATH, without inheriting its backdrop.
LEGACY_ENTRY = (743, 564)
ACCESS_SOURCE = PathTrace(((346, 267), *curve(LEGACY_ENTRY,
                         ((767, 582), (800, 587), (839, 586)),
                         ((1004, 582), (1251, 563), (1478, 557)))))


def access_point(point):
    x, y = point
    return 110+(x-346)*.222, 108+(y-267)*.45


ACCESS = PathTrace(tuple(map(access_point, ACCESS_SOURCE.points)))
ACCESS.distance = ACCESS_SOURCE.distance
ENTRY_DIST = ACCESS.distance[1]
ACCESS_LEN = ACCESS.distance[-1]
ENTRY = ENTRY_DIST / ACCESS_LEN
MICRO = (ENTRY_DIST+47) / ACCESS_LEN
WORKING = (ENTRY_DIST+74) / ACCESS_LEN
FINE = (ENTRY_DIST+196) / ACCESS_LEN
EXCHANGE = (ENTRY_DIST+399) / ACCESS_LEN


def wire_at(canvas, tip, start=.02, *, exchange=False):
    path = ACCESS.trace(tip, start)
    device(canvas, path, WIRE, 2.35 if exchange else 1.55)
    if len(path) > 1:
        canvas.dot(path[-1], 2.0 if exchange else 1.4, GOLD)


def tool_at(canvas, tip, length, color, width, *, hub=True):
    points = ACCESS.trace(tip, max(0, tip-length))
    device(canvas, points, color, width)
    if hub and len(points) > 1:
        x, y = points[0]
        canvas.dot((x, y), width*.73, color, '#24443e', 1.0)


def needle_at(canvas, progress):
    a = access_point(ACCESS_SOURCE.points[0])
    b = access_point(LEGACY_ENTRY)
    tip = tuple(mix(x, y, progress) for x, y in zip(a, b))
    shaft = (tip[0]-76, tip[1]-115)
    device(canvas, (shaft, tip), '#c7d7ce', 3.8)
    canvas.dot(shaft, 5.0, '#6da89b', '#28554c', 1.2)


def imaging(canvas, stage, progress):
    canvas.roundrect((398, 111, 620, 264), 8, '#253b37', '#85aa9d', 1.1)
    x0, y0 = 410, 125
    for offset in range(0, 117, 5):
        value = 56+(offset*21)%25
        canvas.line(((x0, y0+offset), (x0+100, y0+offset+1.4), (608, y0+offset)),
                    (value, value+5, value+4), .7)
    if stage == 'F05':
        canvas.ellipse((428, 170, 494, 222), '#142320', '#d4e0d5', 1.7)
        canvas.ellipse((524, 185, 576, 216), '#192a27', '#819a90', 1.4)
        tip = (mix(420, 459, progress), mix(142, 198, progress))
        canvas.line(((420, 142), tip), '#f2ead6', 1.8)
        canvas.text(509, 277, 'Simulated ultrasound', 18, WHITE, anchor='mt')
    else:
        for x in (460, 559):
            canvas.ellipse((x-29, 148, x+29, 224), None, '#82948d', 4)
            canvas.dot((x, 218), 13, '#627a71', '#97a89e', 2)
        if stage == 'F06':
            line = PathTrace(curve((452, 245), ((459, 210), (492, 197), (508, 174)),
                                   ((512, 155), (513, 143), (513, 132))))
            canvas.line(line.trace(.20+.78*progress), '#f7ead3', 2.1)
        else:
            canvas.line(((431, 244), (450, 232), (466, 219)), '#d8e4d8', 2.4)
            canvas.dot((466, 219), 5+5*progress, None, '#f7ead3', 1.8)
        canvas.text(509, 277, 'Simulated X-ray', 18, WHITE, anchor='mt')


def access_frame(size, p, scene):
    image, art, canvas = entry_layer(size, p, scene)
    q = phase(p, .02, .97)
    details = {
        'F05': ('The fine access needle', 'Groin artery'),
        'F06': ('The fine access wire', 'Fine wire advances'),
        'F07': ('The needle comes out', 'Fine wire stays'),
        'F08': ('The temporary introducer', 'Over the fine wire'),
        'F09': ('The inner tools come out', 'Outer introducer stays'),
        'F10': ('The larger exchange wire', 'Through the introducer'),
        'F11': ('The introducer comes out', 'Exchange wire stays'),
        'F12': ('The working groin sheath', 'Sheath and dilator'),
        'F13': ('The working sheath stays', 'Wire and dilator out'),
    }
    title, detail = details[scene]
    mark(canvas, title, dark=True, right=True)
    if scene == 'F05':
        needle_at(art, q)
        imaging(canvas, scene, q)
    elif scene == 'F06':
        needle_at(art, 1)
        fine_tip = mix(ENTRY*.77, FINE, q)
        art.line(ACCESS.trace(min(fine_tip, ENTRY), .04), '#e2cca0', .75)
        wire_at(art, fine_tip, ENTRY)
        imaging(canvas, scene, q)
    elif scene == 'F07':
        needle_at(art, 1-q*1.92)
        wire_at(art, FINE)
    elif scene == 'F08':
        tip = mix(MICRO-.23, MICRO, q)
        tool_at(art, tip, .29, MICRO_COLOR, 5.1)
        tool_at(art, tip+.022, .33, DILATOR, 2.75)
        wire_at(art, FINE)
    elif scene == 'F09':
        tool_at(art, MICRO, .29, MICRO_COLOR, 5.1)
        tool_at(art, MICRO+.022-.49*q, .33, DILATOR, 2.75)
        wire_at(art, FINE-.65*q)
    elif scene == 'F10':
        tool_at(art, MICRO, .29, MICRO_COLOR, 5.1)
        wire_at(art, mix(.15, EXCHANGE, q), exchange=True)
    elif scene == 'F11':
        tool_at(art, MICRO-.48*q, .29, MICRO_COLOR, 5.1)
        wire_at(art, EXCHANGE, exchange=True)
    elif scene == 'F12':
        tip = mix(WORKING-.23, WORKING, q)
        tool_at(art, tip, .35, SHEATH, 7.4)
        tool_at(art, tip+.025, .38, DILATOR, 3.4)
        wire_at(art, EXCHANGE, exchange=True)
    else:
        tool_at(art, WORKING, .35, SHEATH, 7.4)
        pull = phase(p, .03, .61)
        tool_at(art, WORKING+.025-.58*pull, .38, DILATOR, 3.4)
        wire_at(art, EXCHANGE-.83*pull, exchange=True)
        if p > .62:
            imaging(canvas, scene, phase(p, .62, .98))
    if scene not in ('F05', 'F06') and (scene != 'F13' or p <= .62):
        canvas.text(512, 169, detail, 18, WHITE, anchor='mt')
    return image


def route_intro(size, p):
    image, art, canvas = entry_layer(size, p, 'F16')
    mark(canvas, 'Through the groin sheath', dark=True)
    tool_at(art, WORKING, .35, SHEATH, 7.4)
    wire = mix(.23, .99, phase(p, .02, .55))
    catheter = .87*phase(p, .41, .99)
    device(art, ACCESS.trace(catheter), CATHETER, 3.7)
    device(art, ACCESS.trace(wire, catheter), WIRE, 2.1)
    canvas.text(402, 170, 'Guidewire' if p < .53 else 'Diagnostic catheter', 19, WHITE)
    return image


def dressing(canvas, x, y, scale=1):
    canvas.roundrect((x-25*scale, y-16*scale, x+25*scale, y+16*scale), 5*scale,
                     '#f5e8ca', '#a9926b', 1.1)
    canvas.roundrect((x-12*scale, y-8*scale, x+12*scale, y+8*scale), 3*scale, '#fff6dc')


def gloved_hand(canvas, x, y):
    outline = curve((x+62, y-47), ((x+48, y-35), (x+46, y-26), (x+25, y-22)),
                    ((x+8, y-23), (x-16, y-18), (x-31, y-7)),
                    ((x-41, y+3), (x-26, y+11), (x-12, y+6)),
                    ((x+7, y+3), (x+19, y+1), (x+24, y+3)),
                    ((x+45, y+8), (x+56, y+2), (x+75, y-25)))
    canvas.poly(outline, '#7ac2a7')
    canvas.line(outline, '#255e53', 2)
    canvas.line(((x-22, y-4), (x+10, y-10), (x+25, y-10)), '#b2e1c5', 2.1)
    canvas.poly(((x+47, y-50), (x+75, y-27), (x+97, y-42), (x+70, y-67)), '#40796c')


def aftercare_frame(size, p, scene):
    image, art, canvas = entry_layer(size, p, scene)
    if scene == 'F24':
        mark(canvas, 'The catheter comes out', dark=True)
        tool_at(art, WORKING, .35, SHEATH, 7.4)
        travel = .98 * phase(p, .05, .94)
        device(art, ACCESS.trace(.98-travel), CATHETER, 3.7)
        label(canvas, 'Sheath stays in place', 404, 137, art.project(access_point(LEGACY_ENTRY)), dark=True)
    elif scene == 'F25':
        mark(canvas, 'Closing the access site', dark=True)
        end = WORKING*(1-phase(p, .08, .47))
        tool_at(art, end, .35, SHEATH, 7.4)
        if p > .48:
            gloved_hand(art, 172, 211+mix(-28, 2, phase(p, .48, .92)))
        canvas.text(410, 177, 'Firm pressure' if p > .55 else 'Sheath removal', 19, WHITE)
    elif p < .53:
        mark(canvas, 'Another way to close the site', dark=True)
        puncture = access_point(LEGACY_ENTRY)
        x, y = puncture
        a = phase(p, .03, .47)
        stitch = curve((x-11-a*4, y-5), ((x-10, y+8), (x+1, y+4), (x+9+a*4, y-1)),
                       ((x+3, y-11), (x+3, y-9), (x-2, y-5)))
        art.line(stitch, '#f6e0a1', 2.7)
        art.dot(puncture, 4.6+a*3, None, '#f3cf81', 1.4)
        canvas.text(410, 179, 'Closure stitch example', 19, WHITE)
    else:
        mark(canvas, 'Checking the access site', dark=True)
        dressing(art, 172, 211, 1.27)
        gloved_hand(art, 198, mix(176, 206, phase(p, .54, .98)))
        canvas.text(426, 167, 'Leg circulation', 19, WHITE)
        q = phase(p, .55, .99)
        sock = curve((443, 217), ((478, 213), (503, 219), (527, 214)),
                     ((533, 208), (531, 197), (541, 201)),
                     ((556, 204), (549, 231), (548, 238)),
                     ((543, 252), (539, 253), (521, 250)),
                     ((486, 249), (463, 245), (443, 247)))
        canvas.poly(sock, '#4a887b')
        canvas.line(sock, '#9bcab7', 2)
        canvas.dot((523, 230), mix(5, 13, q), None, '#ebefba', 2.2)
    return image


@lru_cache(maxsize=3)
def recovery_layer(size):
    image = field(size).copy()
    canvas = Canvas(image)
    canvas.roundrect((30, 243, 602, 311), 22, '#95b4ab')
    canvas.roundrect((40, 228, 604, 292), 22, '#e8f1e3', '#a2bab0', 2)
    canvas.line(((76, 293), (76, 333)), '#50766f', 9)
    canvas.line(((561, 294), (556, 333)), '#50766f', 9)
    # A neutral face shape and cloth cap sit above the covered patient.
    canvas.roundrect((55, 207, 168, 244), 13, '#ecf4e9', '#afc5b6', 2)
    canvas.ellipse((76, 170, 153, 232), '#95b8a9', '#5e8b7e', 2)
    canvas.poly(((76, 211), (70, 192), (80, 175), (107, 168), (127, 176),
                 (111, 182), (98, 216)), '#4b8478')
    cover = curve((136, 223), ((144, 213), (147, 209), (153, 210)),
                  ((196, 202), (239, 190), (299, 200)),
                  ((350, 209), (418, 217), (488, 207)), ((528, 195), (553, 210), (557, 235)),
                  ((553, 260), (553, 272), (514, 273)), ((398, 264), (180, 273), (85, 262)),
                  ((111, 260), (128, 239), (136, 223)))
    canvas.poly(cover, '#67a397')
    canvas.line(cover, '#346c63', 2)
    for dx in (0, 24, 52):
        canvas.line(curve((180+dx, 213), ((234+dx, 202), (282+dx, 227), (348+dx, 224))),
                    '#88bcac', 2)
    canvas.line(curve((327, 246), ((403, 255), (462, 251), (527, 243))), '#4c877e', 2)
    canvas.roundrect((418, 71, 599, 177), 12, '#3b6760')
    canvas.roundrect((427, 80, 590, 164), 7, '#173d39')
    canvas.line(((553, 176), (553, 206)), '#5b8a82', 5)
    return image


def recovery_frame(size, p):
    image = recovery_layer(size).copy()
    canvas = Canvas(image)
    mark(canvas, 'Recovery after groin access')
    speed = (p*4.5) % 1
    data = tuple((436+i*1.5, 122 - (sin((i*.19-speed*2*pi))**11)*19) for i in range(96))
    canvas.line(data, '#beecc4', 1.7)
    if p < .38:
        label(canvas, 'Pulse and blood pressure', 97, 111, (442, 120))
    elif p < .75:
        label(canvas, 'Access-site checks', 189, 117, (270, 212))
        gloved_hand(canvas, 274, 219+mix(-22, 0, phase(p, .38, .67)))
    else:
        label(canvas, 'Leg straight as advised', 326, 173, (431, 241))
    return image


def draw_frame(scene, size, progress):
    if scene == 'R12':
        return route_frame(size, progress, radial=True)
    if scene == 'F04':
        return entry_frame(size, progress)
    if scene in ('F05', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'F13'):
        return access_frame(size, progress, scene)
    if scene == 'F16':
        return route_frame(size, progress)
    if scene == 'F27':
        return recovery_frame(size, progress)
    return aftercare_frame(size, progress, scene)


def ffmpeg_path():
    ffmpeg = os.environ.get('FFMPEG') or shutil.which('ffmpeg')
    if not ffmpeg:
        bundled = sorted((ROOT / 'work/video-runtime/imageio_ffmpeg/binaries').glob('ffmpeg*'))
        ffmpeg = bundled[0] if bundled else None
    if not ffmpeg:
        raise SystemExit('Install FFmpeg or set FFMPEG to its executable.')
    return str(ffmpeg)


def render(scene, seconds, width, *, still_only=False):
    height = width * 9 // 16
    canvas_size = (width*3, height*3)
    output_size = (width, height)
    name = SCENES[scene][0]
    draw_frame(scene, canvas_size, .44).resize(output_size, Image.Resampling.LANCZOS,
                                               reducing_gap=1.5).save(OUT / f'{name}.png')
    if still_only:
        return
    target = OUT / f'{name}.mp4'
    pending = target.with_suffix('.partial.mp4')
    ffmpeg = ffmpeg_path()
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
               '-video_size', f'{width}x{height}', '-framerate', str(FPS), '-i', '-', '-an',
               '-c:v', 'libx264', '-threads', '2', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
               '-g', '60', '-bf', '2', '-movflags', '+faststart', str(pending)]
    count = round(FPS*seconds)
    with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
        with process.stdin as pipe:
            for index in range(count):
                picture = draw_frame(scene, canvas_size, index/max(1, count-1))
                pipe.write(picture.resize(output_size, Image.Resampling.LANCZOS,
                                          reducing_gap=1.5).tobytes())
        if process.wait():
            raise RuntimeError(f'{scene} video encode failed')
    subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(pending), '-map', '0:v:0', '-f', 'null', '-'],
                   check=True)
    pending.replace(target)
    print(f'{scene}: {target.name}, {width}×{height}, {count/FPS:.3f} s, full decode passed', flush=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('scene', choices=SCENES)
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--width', choices=(1920, 2560), type=int, default=1920)
    parser.add_argument('--still-only', action='store_true')
    args = parser.parse_args()
    render(args.scene, args.seconds or SCENES[args.scene][1], args.width, still_only=args.still_only)
