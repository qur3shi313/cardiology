"""Waking, respiratory support and bedside equipment after coronary bypass."""

from functools import lru_cache
from math import exp, pi, sin

import skia

from . import access as art
from . import angiogram
from .cabg_recovery import footer, pulse_points, round_box


INK = '#143f37'
MUTED = '#305c52'
CREAM = '#f6f9ee'
AIR = '#c7e2da'
TRACE_TONES = ('#bfe9b6', '#a4dce3', '#ebc38b')
SCENE_TAG = 'CARDIAC SURGERY'
SAMPLE = skia.SamplingOptions(skia.FilterMode.kLinear)
curve = angiogram.art.curve

MOUTH = (346, 350)
VENT_LINE = tuple(curve((742, 334), ((691, 344), (691, 407), (644, 414)),
                        ((557, 425), (527, 329), (452, 324)),
                        ((419, 320), (395, 348), MOUTH)))
OXYGEN_LINE = tuple(curve((610, 306), ((586, 332), (622, 386), (566, 389)),
                          ((487, 402), (435, 370), (365, 360))))
ECG_LINE = tuple(curve((472, 422), ((551, 442), (626, 352), (687, 339)),
                       ((766, 324), (805, 354), (917, 340))))
FINGER_LINE = tuple(curve((566, 477), ((642, 509), (725, 408), (772, 385)),
                          ((822, 354), (877, 371), (918, 365))))
PRESSURE_LINE = tuple(curve((530, 471), ((608, 516), (707, 509), (772, 471)),
                            ((840, 431), (824, 410), (919, 394))))
IV_LINE = tuple(curve((724, 268), ((721, 363), (706, 439), (644, 455)),
                      ((592, 467), (544, 442), (499, 448))))
CHEST_DRAIN = tuple(curve((501, 523), ((540, 533), (496, 553), (523, 577)),
                          ((547, 590), (547, 559), (567, 557))))
URINE_DRAIN = tuple(curve((758, 526), ((758, 543), (791, 550), (796, 573)),
                          ((804, 586), (812, 584), (818, 582))))
PACING_LINE = tuple(curve((481, 499), ((530, 548), (678, 533), (689, 467)),
                          ((702, 434), (730, 469), (763, 477))))


def oval(canvas, x, y, w, h, paint):
    canvas.drawOval(skia.Rect.MakeXYWH(x, y, w, h), paint)


def heading(canvas, title):
    art.rect(canvas, 0, 0, 1280, 150, art.grad(0, 0, 0, 150, ['#f5faf1', '#e5f0e7']))
    angiogram.header(canvas, title, SCENE_TAG)


def annotation(canvas, target, elbow, tail, label, position):
    art.line(canvas, [target, elbow, tail], '#356757', 4)
    angiogram.dot(canvas, *target, 7, '#f4d6a3')
    art.text(canvas, label, *position, 33, INK)


@lru_cache(maxsize=1)
def room_plate():
    """An original vector plate keeps the environment stable across bedside cuts."""
    surface = skia.Surface(2560, 1440)
    canvas = surface.getCanvas()
    canvas.scale(2, 2)
    art.rect(canvas, 0, 0, 1280, 720,
             art.grad(0, 0, 1210, 650, ['#f7fbf3', '#e7f3e9', '#b1d3c5']))
    art.rect(canvas, 0, 513, 1280, 207,
             art.grad(0, 515, 0, 720, ['#bed7c9', '#aac8ba']))
    for x in range(30, 1260, 176):
        art.line(canvas, [(588+.59*(x-588), 513), (x, 720)], '#d7e7db', 2.5, 185)
    for y in (539, 592, 674):
        art.line(canvas, [(0, y), (1280, y)], '#ccdfd2', 2)
    round_box(canvas, 101, 169, 440, 265, 10, '#bdcfbc')
    round_box(canvas, 114, 181, 410, 226, 8, '#e6f4e8')
    art.rect(canvas, 119, 186, 400, 214,
             art.grad(122, 183, 519, 402, ['#eff8ee', '#d1e5d8', '#cae6de']))
    for x in (241, 371):
        art.line(canvas, [(x, 185), (x, 402)], '#b5d5c7', 7)
    art.line(canvas, [(118, 300), (519, 300)], '#bdd9ca', 5)
    round_box(canvas, 101, 407, 440, 24, 4, '#afcbbe')
    round_box(canvas, 925, 193, 265, 37, 11, '#a6c8b9')
    round_box(canvas, 918, 186, 269, 37, 11, '#d4e7dc')
    for x in (951, 991, 1044, 1100, 1143):
        angiogram.dot(canvas, x, 204, 6, '#90ad9c')
    oval(canvas, 155, 579, 1035, 91, art.solid('#45695c', 71))
    return surface.makeImageSnapshot()


def cart(canvas, x, y, w, h):
    round_box(canvas, x+10, y+10, w, h, 21, '#99bfb0')
    round_box(canvas, x, y, w, h, 21, '#416f63')
    art.line(canvas, [(x+w*.52, y+h), (x+w*.52, 562)], '#6f998b', 14)
    art.line(canvas, [(x+w*.21, 571), (x+w*.80, 571)], '#527e70', 15)
    for a in (.24, .78):
        angiogram.dot(canvas, x+w*a, 586, 12, '#385d54')


def waveform(canvas, points, tone, glow=8):
    art.line(canvas, points, tone, glow, 100)
    art.line(canvas, points, tone, 3.2, 255)


def monitor(canvas, seconds, focus=None):
    cart(canvas, 918, 244, 290, 186)
    round_box(canvas, 932, 257, 262, 144, 11, '#193733')
    for index, label in enumerate(('ECG', 'SpO₂', 'Pressure')):
        y = 283+45*index
        if focus == label:
            round_box(canvas, 937, y-21, 250, 42, 7, '#315a50')
        art.text(canvas, label, 946, y+5, 25, TRACE_TONES[index])
        art.line(canvas, [(1051, y+2), (1179, y+2)], '#427361', 1.4, 173)
        if index == 0:
            trace = pulse_points(1051, y, 126, 29, seconds)
        elif index == 1:
            trace = [(1051+j*126/55, y-14*exp(-abs((j*.095-seconds*1.5)%1-.43)*6))
                     for j in range(56)]
        else:
            trace = [(1051+j*126/55, y-15*exp(-abs((j*.073-seconds*1.46)%1-.31)*4))
                     for j in range(56)]
        waveform(canvas, trace, TRACE_TONES[index])
    art.text(canvas, 'Illustrated monitor', 934, 422, 25, '#e3f4e9')


def ventilator(canvas, seconds, focus=False):
    cart(canvas, 741, 231, 154, 147)
    round_box(canvas, 751, 243, 134, 101, 8, '#213e37')
    if focus:
        round_box(canvas, 756, 250, 124, 82, 7, '#325d51')
    phase = seconds*.52
    trace = [(759+j*111/57, 292+15*sin(j*.15-phase*2*pi)) for j in range(58)]
    waveform(canvas, trace, '#a5d9c8')
    angiogram.dot(canvas, 874, 361, 7, '#a7d0bc')


def oxygen_source(canvas):
    round_box(canvas, 594, 226, 104, 86, 13, '#6b9f8f')
    round_box(canvas, 608, 241, 77, 50, 10, '#285a4d')
    art.text(canvas, 'O₂', 624, 280, 31, '#dbf3e7')
    art.line(canvas, [(610, 306), (610, 320)], '#477b6d', 14)


def staff(canvas, seconds):
    y = 273+2.5*sin(seconds*1.8)
    oval(canvas, 91, 520, 230, 56, art.solid('#345a50', 65))
    art.line(canvas, [(168, 480), (155, 551)], '#365b51', 43)
    art.line(canvas, [(238, 480), (260, 554)], '#406b5d', 43)
    art.line(canvas, [(133, 554), (169, 555)], '#28473e', 22)
    art.line(canvas, [(253, 555), (288, 557)], '#28473e', 22)
    gown = skia.Path()
    gown.moveTo(101, 439)
    gown.cubicTo(113, 350, 120, 316, 151, 307)
    gown.cubicTo(195, 290, 239, 302, 264, 328)
    gown.cubicTo(283, 367, 280, 422, 281, 492)
    gown.lineTo(112, 494)
    gown.close()
    canvas.drawPath(gown, art.grad(100, 298, 279, 501, ['#9bc4b3','#4e8c77','#316453']))
    forearm = ((254, 345), (281, 374), (296+13*sin(seconds*2), 351+8*sin(seconds*2)))
    art.line(canvas, forearm, '#5c9583', 33)
    angiogram.dot(canvas, *forearm[-1], 13, '#dfbd9c')
    oval(canvas, 153, y-86, 85, 122,
         art.grad(157, y-81, 239, y+26, ['#ebc4a5','#b79074','#876b60']))
    oval(canvas, 145, y-99, 93, 66, art.grad(149, y-90, 237, y-27, ['#9ec5b3','#5c8f7f']))
    round_box(canvas, 162, y-22, 74, 36, 11, '#e0eee5')
    art.line(canvas, [(164, y-13), (226, y-8)], '#b2ccbe', 2.3)
    art.line(canvas, [(195, y-37), (206, y-38), (215, y-34)], '#8a705e', 2.6)
    art.line(canvas, [(219, y-34), (227, y-32), (232, y-30)], '#806557', 3)
    angiogram.dot(canvas, 225, y-31, 3.5, '#4c453d')


def bed(canvas, seconds, awake=False, nod=False):
    # All external support paths meet a covered patient, with no insertion
    # sites visible. A slight head motion preserves the secured mouth position.
    round_box(canvas, 241, 488, 650, 85, 25, '#3c695b')
    round_box(canvas, 253, 456, 626, 78, 24, '#eef7ed')
    art.line(canvas, [(295, 559), (295, 593), (831, 593), (831, 557)], '#668f80', 16)
    for x in (295, 831):
        angiogram.dot(canvas, x, 603, 13, '#34594f')
    canvas.save()
    canvas.rotate(25, 296, 388)
    round_box(canvas, 224, 334, 172, 112, 37, '#aecfc1')
    round_box(canvas, 224, 334, 157, 98, 34, '#e8f5eb')
    canvas.restore()
    breath = (1+sin(seconds*2*pi*.33))*.5
    canvas.save()
    if nod:
        canvas.rotate(9*exp(-abs((seconds-.45)%4.1-1.5)*3)*sin(seconds*3.1), *MOUTH)
    head = skia.Path()
    head.moveTo(255, 338)
    head.cubicTo(254, 306, 285, 282, 318, 293)
    head.cubicTo(337, 299, 340, 317, 354, 334)
    head.cubicTo(362, 344, 349, 352, 352, 362)
    head.cubicTo(353, 382, 319, 395, 289, 382)
    head.cubicTo(274, 378, 257, 360, 255, 338)
    head.close()
    canvas.drawPath(head, art.grad(257, 290, 351, 389, ['#edc7a5','#c49779','#a37d6b']))
    cap = skia.Path()
    cap.moveTo(252, 344)
    cap.cubicTo(244, 318, 260, 289, 286, 280)
    cap.cubicTo(313, 273, 337, 283, 341, 308)
    cap.cubicTo(309, 304, 277, 331, 263, 354)
    cap.close()
    canvas.drawPath(cap, art.grad(247, 278, 340, 353, ['#aacdbb','#67978a','#47786c']))
    art.line(canvas, [(305, 319), (319, 321), (327, 320)], '#836757', 3)
    if awake and sin(seconds*2.7) < .94:
        angiogram.dot(canvas, 321, 320, 4, '#504d41')
    canvas.restore()
    upper = [(332, 379), (375, 358), (419, 367), (475, 407), (454, 482), (377, 488)]
    canvas.drawPath(art.path(upper, True), art.grad(339, 362, 460, 476,
                    ['#a9cbbd','#6f9d8d','#4b7e70']))
    blanket = skia.Path()
    blanket.moveTo(375, 413)
    blanket.cubicTo(411, 368-18*breath, 472, 393-13*breath, 513, 418)
    blanket.cubicTo(601, 451, 674, 430, 748, 433)
    blanket.cubicTo(822, 429, 864, 438, 875, 475)
    blanket.cubicTo(891, 510, 860, 530, 792, 537)
    blanket.lineTo(437, 537)
    blanket.cubicTo(377, 516, 369, 472, 375, 413)
    blanket.close()
    canvas.drawPath(blanket, art.grad(375, 381, 867, 541, ['#c5e3d1','#80b29e','#558777']))
    art.line(canvas, [(409, 435-15*breath), (493, 446), (613, 479), (822, 473)],
             '#d1e7da', 4.4, 192)
    art.line(canvas, [(457, 488), (596, 510), (830, 510)], '#77a594', 6, 174)
    art.line(canvas, [(656, 474), (848, 474), (866, 512), (665, 512)], '#d6ebdd', 8)


def line(canvas, path, tone='#7da89a', width=10):
    art.line(canvas, path, '#2d5a4e', width+5, 153)
    art.line(canvas, path, tone, width)
    art.line(canvas, [(x, y-2) for x, y in path], '#e7f4ec', 2.7, 187)


def path_motion(canvas, path, seconds, tone, *, rate=.50, length=.28, width=10):
    """Moving emphasis follows a connected path and conveys no flow value."""
    p = (seconds*rate) % 1.
    q = max(0., p-length)
    portion = [point(path, q+(p-q)*i/27) for i in range(28)]
    art.line(canvas, portion, tone, width+6, 96)
    art.line(canvas, portion, tone, width, 233)


@lru_cache(maxsize=32)
def route_lengths(path):
    from math import hypot

    values = [0.]
    for a,b in zip(path, path[1:]):
        values.append(values[-1]+hypot(a[0]-b[0], a[1]-b[1]))
    return tuple(values)


def point(path, fraction):
    from bisect import bisect_right

    cumulative = route_lengths(path)
    current = cumulative[-1]*min(1., max(0., fraction))
    index = min(len(path)-2, max(0, bisect_right(cumulative, current)-1))
    a,b = path[index:index+2]
    delta = cumulative[index+1]-cumulative[index]
    progress = (current-cumulative[index])/delta if delta else 0
    return a[0]+(b[0]-a[0])*progress, a[1]+(b[1]-a[1])*progress


def breathing_circuit(canvas, seconds, later=False, focus=False):
    if later:
        oxygen_source(canvas)
        line(canvas, OXYGEN_LINE, '#d2e9e0', 6)
        oval(canvas, 326, 325, 56, 61, art.solid('#a8c9c2', 220))
        oval(canvas, 331, 331, 44, 49, art.solid('#dff0ea', 205))
        art.line(canvas, [(325, 350), (304, 343), (282, 346)], '#91b9ae', 4)
        if focus:
            path_motion(canvas, OXYGEN_LINE, seconds, '#6db998', width=13, length=.42)
        return
    ventilator(canvas, seconds, focus)
    line(canvas, VENT_LINE, AIR, 13)
    for fraction in (.08, .13, .18, .23, .28, .33, .38, .43, .48, .53, .58, .63,
                     .68, .73, .78, .83, .88):
        x,y = point(VENT_LINE, fraction)
        angiogram.dot(canvas, x, y, 5, '#d6ece2', 228)
    round_box(canvas, 338, 341, 28, 18, 5, '#edf5eb')
    art.line(canvas, [(346, 350), (364, 350)], '#9bb9ac', 5)
    if focus:
        path_motion(canvas, VENT_LINE, seconds, '#76bea3', width=16, length=.42)


def collection(canvas, seconds, chest, focused):
    if chest:
        x,y,w,h = 556,553,70,66
        path = CHEST_DRAIN
        tone = '#c49382'
    else:
        x,y,w,h = 812,581,81,52
        path = URINE_DRAIN
        tone = '#d7b878'
    line(canvas, path, '#d4e7d9', 6)
    round_box(canvas, x,y,w,h,9, '#d7ede3')
    round_box(canvas, x+7,y+7,w-14,h-14,6, '#eef5e9')
    level = 11+1.2*sin(seconds*1.4)
    round_box(canvas, x+8,y+h-9-level,w-16,level,4,tone)
    for i in range(3):
        art.line(canvas, [(x+w-24, y+14+i*10), (x+w-14, y+14+i*10)],
                 '#8aab9c', 2)
    if focused:
        path_motion(canvas, path, seconds, tone, width=12, length=.55)


def infusion(canvas, seconds, focus):
    art.line(canvas, [(736, 202), (736, 476)], '#7da899', 8)
    art.line(canvas, [(711, 202), (756, 202)], '#7da899', 8)
    round_box(canvas, 701, 213, 47, 59, 10, '#d4e6dc')
    round_box(canvas, 706, 221, 37, 42, 7, '#e7f3e9')
    art.rect(canvas, 708, 243, 33, 16, art.solid('#b6d7c9'))
    line(canvas, IV_LINE, '#a6cdb8', 6)
    if focus:
        path_motion(canvas, IV_LINE, seconds, '#548e74', width=13, length=.39)


def device(canvas, seconds, focus=None):
    signal = {'ecg': 'ECG', 'oxygen': 'SpO₂', 'pressure': 'Pressure'}.get(focus)
    monitor(canvas, seconds, signal)
    if focus in ('ecg', 'all'):
        line(canvas, ECG_LINE, '#8cb699', 7)
        if focus == 'ecg':
            path_motion(canvas, ECG_LINE, seconds, '#ceebac', width=11)
    if focus in ('oxygen', 'all'):
        # A clearly depicted probe rests on the exposed fingertip of a
        # sleeved, anonymous patient. No vascular entry is shown.
        round_box(canvas, 520, 457, 41, 29, 12, '#669a88')
        round_box(canvas, 549, 459, 27, 24, 9, '#d5af90')
        round_box(canvas, 560, 456, 20, 26, 8, '#e5f4e9')
        line(canvas, FINGER_LINE, '#9fcfd3', 7)
        if focus == 'oxygen':
            path_motion(canvas, FINGER_LINE, seconds, '#bfeaf1', width=11)
    if focus in ('pressure', 'all'):
        line(canvas, PRESSURE_LINE, '#d0ad83', 7)
        round_box(canvas, 769, 449, 47, 29, 6, '#e9ddc4')
        if focus == 'pressure':
            path_motion(canvas, PRESSURE_LINE, seconds, '#f2d9a4', width=11)
    if focus in ('iv', 'all'):
        infusion(canvas, seconds, focus == 'iv')
    if focus in ('chest', 'urine', 'all'):
        if focus != 'urine':
            collection(canvas, seconds, True, focus == 'chest')
        if focus != 'chest':
            collection(canvas, seconds, False, focus == 'urine')
    if focus == 'pacing':
        line(canvas, PACING_LINE, '#b8cbe1', 7)
        round_box(canvas, 750, 448, 92, 98, 14, '#416774')
        round_box(canvas, 760, 461, 72, 44, 7, '#27434c')
        trace = pulse_points(769, 488, 54, 26, seconds)
        waveform(canvas, trace, '#b8dddb', glow=7)
        path_motion(canvas, PACING_LINE, seconds, '#d3e7ec', width=10)


def bedside(canvas, seconds, *, later=False, awake=False, nod=False,
            with_staff=False, breathing_focus=False, focus=None):
    canvas.drawImageRect(room_plate(), skia.Rect.MakeWH(1280, 720), SAMPLE)
    if with_staff:
        staff(canvas, seconds)
    bed(canvas, seconds, awake, nod)
    breathing_circuit(canvas, seconds, later, breathing_focus)
    device(canvas, seconds, focus)


def airway_insert(canvas, seconds):
    art.rect(canvas, 0, 0, 1280, 720,
             art.grad(0, 0, 1260, 710, ['#f5f8ef','#dfeee3','#b9d9ca']))
    # The insert is a deliberately simplified sagittal anatomical model.
    # The oral tube passes behind the tongue and continues in the trachea.
    # The oesophagus runs behind the airway and stays empty.
    profile = skia.Path()
    profile.moveTo(702, 161)
    profile.cubicTo(504, 151, 346, 211, 347, 285)
    profile.cubicTo(341, 312, 286, 342, 295, 366)
    profile.cubicTo(309, 381, 350, 379, 360, 408)
    profile.cubicTo(360, 478, 429, 490, 550, 471)
    profile.cubicTo(607, 485, 605, 568, 618, 650)
    profile.lineTo(821, 650)
    profile.cubicTo(786, 531, 852, 431, 859, 315)
    profile.cubicTo(870, 234, 816, 164, 702, 161)
    profile.close()
    canvas.drawPath(profile, art.grad(320, 172, 850, 643, ['#f2c9a6','#d59a81','#ab7465']))
    pharynx = tuple(curve((353, 359), ((422, 325), (531, 325), (585, 359)),
                          ((646, 400), (624, 437), (645, 477))))
    trachea = tuple(curve((645, 477), ((630, 521), (636, 578), (650, 651))))
    esophagus = tuple(curve((638, 409), ((699, 440), (699, 531), (721, 651))))
    art.line(canvas, esophagus, '#b47772', 49)
    art.line(canvas, esophagus, '#875f62', 25)
    art.line(canvas, pharynx, '#a56260', 74)
    art.line(canvas, pharynx, '#76494e', 47)
    art.line(canvas, trachea, '#d5ad97', 91)
    art.line(canvas, trachea, '#a87a72', 63)
    art.line(canvas, trachea, '#62484c', 42)
    tongue = skia.Path()
    tongue.moveTo(363, 373)
    tongue.cubicTo(420, 344, 488, 350, 540, 389)
    tongue.cubicTo(506, 428, 409, 429, 363, 373)
    tongue.close()
    canvas.drawPath(tongue, art.grad(364, 369, 541, 409, ['#d99186','#b56e6b']))
    oral_tube = tuple(curve((209, 362), ((285, 358), (321, 352), (369, 351)),
                            ((474, 337), (558, 340), (601, 390)),
                            ((631, 425), (631, 477), (640, 505)),
                            ((647, 532), (642, 563), (644, 593))))
    line(canvas, oral_tube, '#cfe9df', 26)
    path_motion(canvas, oral_tube, seconds, '#eaf9d7', width=21)
    annotation(canvas, oral_tube[-23], (721, 465), (916, 465), 'Breathing tube', (919, 478))
    annotation(canvas, (647, 624), (767, 571), (918, 571), 'Windpipe', (923, 585))
    heading(canvas, 'The tube sits in the windpipe')
    footer(canvas, 'Illustrated anatomy · The tube is already in place')


def waking(canvas, progress, seconds):
    # A gentle pullback establishes where both the nurse and devices are.
    canvas.save()
    zoom = 1+.32*(1-art.smooth(progress/.48))
    canvas.translate(348, 344)
    canvas.scale(zoom, zoom)
    canvas.translate(-348, -344)
    bedside(canvas, seconds, awake=True, nod=True, with_staff=True,
            breathing_focus=True)
    canvas.restore()
    if seconds >= 4.8:
        heading(canvas, 'Waking up after bypass')
    message = ('A nurse can communicate with you as you wake' if progress < .51
               else 'The team checks what support you still need')
    if seconds >= 4.8:
        footer(canvas, message)


def ventilation(canvas, progress, seconds, cues):
    airway = cues.get('airway', .09)
    respond = cues.get('respond', .30)
    readiness = cues.get('readiness', .53)
    oxygen = cues.get('oxygen', .75)
    if airway <= progress < respond:
        airway_insert(canvas, seconds)
        return
    if progress >= oxygen:
        bedside(canvas, seconds, later=True, awake=True, with_staff=True, breathing_focus=True)
        annotation(canvas, (355, 345), (405, 213), (449, 213), 'Extra oxygen, if needed',
                   (458, 222))
        heading(canvas, 'Breathing support can change')
        footer(canvas, 'A face mask or nasal tubes may supply extra oxygen')
        return
    bedside(canvas, seconds, awake=True, nod=respond <= progress < readiness,
            with_staff=True, breathing_focus=True)
    heading(canvas, 'Breathing support after bypass')
    if progress < respond:
        annotation(canvas, (806, 252), (770, 194), (691, 194), 'Ventilator', (539, 202))
        footer(canvas, 'A ventilator can help you breathe through the tube')
    elif progress < readiness:
        footer(canvas, 'A nod or head shake can answer a simple question')
    else:
        footer(canvas, 'Staff decide when it is safe to remove the tube')


def equipment(canvas, progress, seconds, cues):
    phases = (
        ('ecg', cues.get('ecg', .075), 'Heart rhythm', 'The ECG shows the rate and rhythm'),
        ('oxygen', cues.get('oxygen', .155), 'Blood oxygen', 'A finger sensor helps staff check blood oxygen'),
        ('pressure', cues.get('pressure', .275), 'Arterial pressure', 'An arterial line can measure pressure continuously'),
        ('iv', cues.get('iv', .368), 'IV line', 'An IV can give fluids or medicines'),
        ('chest', cues.get('chest', .444), 'Chest drainage', 'A chest drain leads to its own collection system'),
        ('urine', cues.get('urine', .563), 'Urine measurement', 'A separate catheter collects urine so staff can measure it'),
        ('pacing', cues.get('pacing', .684), 'Temporary pacing, if needed',
         'Temporary pacing wires can support the heart rhythm'),
        ('all', cues.get('removal', .855), 'Bedside support',
         'The team decides when each support is no longer needed'),
    )
    focus, _, title, detail = next(
        (item for item in reversed(phases) if progress >= item[1]),
        ('all',0.,'Bedside support','Different equipment answers different questions'),
    )
    bedside(canvas, seconds, later=True, awake=True, focus=focus)
    heading(canvas, title)
    footer(canvas, detail)


def draw(canvas, ident, progress, seconds, *, cues=None):
    if ident == 'P01':
        waking(canvas, progress, seconds)
    elif ident == 'P02':
        ventilation(canvas, progress, seconds, cues or {})
    elif ident == 'P03':
        equipment(canvas, progress, seconds, cues or {})
    else:
        raise ValueError(f'Unsupported CABG ICU scene: {ident}')
