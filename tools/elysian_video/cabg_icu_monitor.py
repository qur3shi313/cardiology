"""Cardiac surgery recovery scenes: comfort, supported mobility and discharge."""

from math import cos, pi, sin

import skia

from . import access, angiogram, cabg_icu


INK = '#173e35'
WHITE = '#f5fbf5'
CAP = ('#9ac0ad', '#426e60')
PATIENT = ('#9dc0b0', '#4b786c', '#31594f')
STAFF = ('#659784', '#38685f', '#234d43')
FAMILY = ('#b197a3', '#7b6577', '#584b61')


def rect(c, x, y, w, h, color):
    access.rect(c, x, y, w, h, access.solid(color))


def block(c, x, y, w, h, radius, color):
    angiogram.block(c, x, y, w, h, radius, access.solid(color))


def oval(c, x, y, w, h, color, alpha=255):
    c.drawOval(skia.Rect.MakeXYWH(x, y, w, h), access.solid(color, alpha))


def room(c, *, ward=False):
    access.rect(c, 0, 0, 1280, 720,
                access.grad(90, 30, 1170, 700, ['#f6fbf4', '#dfefe5', '#a6cbbb']))
    rect(c, 0, 541, 1280, 179, '#bdd6ca')
    access.line(c, [(0, 541), (1280, 541)], '#90b4a6', 4)
    for x in range(-80, 1380, 174):
        access.line(c, [(x, 541), (640 + (x - 640) * 1.34, 716)], '#d2e7db', 2.4)
    block(c, 78, 194, 304, 215, 12, '#a8c8bc')
    block(c, 86, 201, 289, 198, 9, '#dfefe9')
    rect(c, 225, 201, 8, 199, '#b7d5c8')
    rect(c, 86, 298, 289, 8, '#b7d5c8')
    if ward:
        block(c, 966, 192, 222, 334, 16, '#abc8ba')
        block(c, 983, 209, 184, 310, 10, '#d7ebe0')
        block(c, 1013, 230, 122, 169, 9, '#bad9cc')
        access.line(c, [(1082, 442), (1127, 442)], '#668f82', 8)


def header(c, title):
    angiogram.header(c, title, 'CARDIAC SURGERY')


def footer(c, sentence):
    rect(c, 0, 651, 1280, 69, '#18463b')
    access.text(c, sentence, 56, 695, 32, WHITE)


def cap(c, x, y, width, *, colors=CAP):
    shape = skia.Path()
    shape.moveTo(x - width, y + 8)
    shape.cubicTo(x - 1.08 * width, y - 34, x + .35 * width, y - 51, x + .94 * width, y - 20)
    shape.cubicTo(x + 1.20 * width, y + 17, x + .37 * width, y + 21, x - width, y + 8)
    shape.close()
    c.drawPath(shape, access.grad(x - width, y - 35, x + width, y + 16, list(colors)))


def face(c, x, y, *, facing=1, color='#c59d83'):
    oval(c, x - 38, y - 34, 77, 96, color)
    oval(c, x - 30, y - 12, 52, 63, '#e4b99a', 143)
    cap(c, x - 2, y - 22, 39)
    angiogram.dot(c, x + 14 * facing, y + 12, 3.1, '#684c41')
    access.line(c, [(x + 9 * facing, y + 35), (x + 20 * facing, y + 34)], '#926b58', 2.5)


def body(c, hip, torso, lean):
    x, y = hip
    contour = skia.Path()
    contour.moveTo(x - 52 + lean, y - 146)
    contour.cubicTo(x - 90 + lean, y - 121, x - 71, y - 49, x - 58, y + 6)
    contour.cubicTo(x - 24, y + 19, x + 32, y + 15, x + 58, y + 2)
    contour.cubicTo(x + 65, y - 42, x + 79 + lean, y - 110, x + 48 + lean, y - 146)
    contour.cubicTo(x + 20 + lean, y - 169, x - 23 + lean, y - 167, x - 52 + lean, y - 146)
    contour.close()
    c.drawPath(contour, access.grad(x - 55, y - 128, x + 58, y + 20, list(torso)))
    access.line(c, [(x - 21 + lean, y - 156), (x + lean, y - 135),
                    (x + 22 + lean, y - 155)], '#c3d9cd', 5, 210)
    access.line(c, [(x + 35, y - 58), (x + 29, y - 12), (x - 15, y - 4)],
                '#bdd9ca', 2.4, 160)


def sleeve(c, start, elbow, hand, palette):
    access.line(c, [start, elbow, hand], palette[2], 29)
    access.line(c, [start, elbow, hand], palette[1], 21)
    angiogram.dot(c, *hand, 11, '#d9ad90')


def figure(c, x, floor, t, *, palette=PATIENT, seated=False, walking=False,
           gesture=0., facing=1, scale=1.):
    """One patient identity in different fully covered positions."""
    c.save()
    c.translate(x, floor)
    c.scale(scale, scale)
    oval(c, -85, -16, 170, 28, '#5c8d7f', 87)
    cycle = 2 * pi * .76 * t
    lift = 7 * sin(cycle) ** 2 if walking else 0.
    hip = (0., (-106 if seated else -163) - lift)
    for side in (-1, 1):
        if seated:
            knee = (55 + 27 * side, -102)
            foot = (68 + 26 * side, -11)
        elif walking:
            step = side * sin(cycle)
            knee = (19 * side + step * 25, -89 - 14 * max(step, 0))
            foot = (21 * side + step * 49, -14 - 28 * max(0, side * cos(cycle)))
        else:
            knee = (24 * side, -88)
            foot = (31 * side, -14)
        access.line(c, [(hip[0] + 22 * side, hip[1]), knee, foot],
                    palette[2], 36)
        access.line(c, [foot, (foot[0] + 27, foot[1] + 4)], '#33574e', 23)
    lean = 12 + 4 * sin(cycle) if walking else 2 * sin(t * 2.1)
    body(c, hip, palette, lean)
    if palette is STAFF:
        block(c, lean + 29, hip[1] - 126, 20, 25, 4, '#e5eee6')
        access.line(c, [(lean + 32, hip[1] - 114), (lean + 45, hip[1] - 114)], '#558475', 2)
    head = (lean + facing * 7, hip[1] - 190 + sin(t * 2.4) * 2.8)
    face(c, *head, facing=facing)
    swing = 22 * sin(cycle) if walking else 0
    left_hand = (-64 - swing, hip[1] - 33)
    right_hand = (73 + swing + gesture * 25, hip[1] - 40 - gesture * 58)
    sleeve(c, (-49 + lean, hip[1] - 123), (-76, hip[1] - 73), left_hand, palette)
    sleeve(c, (49 + lean, hip[1] - 123), (71, hip[1] - 76 - 17 * gesture), right_hand, palette)
    c.restore()


def bed(c, t, *, tilt=0., report=False):
    # Reuse the earlier bedside scene's patient, cap, gown and blanket geometry.
    # Reframe slightly around the fixed near rail as the headrest position changes.
    c.save()
    c.translate(544, 501)
    c.rotate(-2.8 * tilt)
    c.translate(-544, -501)
    cabg_icu.bed(c, t, awake=True, nod=report)
    c.restore()
    if report:
        gesture = 12 * sin(t * 2.7)
        sleeve(c, (383, 409), (448, 388 + gesture * .5), (476, 352 + gesture), PATIENT)


def orientation_items(c, t, p):
    room(c)
    block(c, 421, 305, 743, 244, 38, '#c2dbcd')
    block(c, 427, 300, 720, 227, 32, '#eef7ee')
    access.line(c, [(444, 513), (1122, 513)], '#b0cdbc', 5)
    for x in (474, 1085):
        access.line(c, [(x, 526), (x, 612)], '#81a493', 15)
    clock_x, clock_y = 1003, 351
    angiogram.dot(c, clock_x, clock_y, 107, '#7aab9a')
    angiogram.dot(c, clock_x, clock_y, 96, '#edf7eb')
    for hour in range(12):
        angle = hour * pi / 6
        start = (clock_x + 78 * sin(angle), clock_y - 78 * cos(angle))
        end = (clock_x + 88 * sin(angle), clock_y - 88 * cos(angle))
        access.line(c, [start, end], '#74998a', 3)
    access.line(c, [(clock_x, clock_y), (clock_x + 42, clock_y - 28)], '#406e60', 7)
    access.line(c, [(clock_x, clock_y), (clock_x - 13, clock_y - 63)], '#406e60', 5)
    radius = 75
    angle = t * .41
    access.line(c, [(clock_x, clock_y), (clock_x + radius * sin(angle), clock_y - radius * cos(angle))], '#ce9f75', 4)
    angiogram.dot(c, clock_x, clock_y, 7, '#406e60')
    block(c, 475, 390, 265, 94, 39, '#659685')
    block(c, 476, 398, 263, 74, 34, '#a8cbb9')
    scale = .99 + .07 * access.smooth(p)
    c.save()
    c.translate(610, 419)
    c.scale(scale, scale)
    for side in (-1, 1):
        cx = 50 * side
        oval(c, cx - 41, -26, 82, 55, '#416e61')
        oval(c, cx - 35, -20, 70, 43, '#ccdfd6')
    access.line(c, [(-19, -7), (0, -14), (19, -7)], '#416e61', 6)
    c.restore()
    for index in range(2):
        x, y = 786 + 55 * index, 454 + 11 * index
        oval(c, x - 12, y - 23, 28, 46, '#a88c79')
        tail = [(x + 12, y - 13), (x + 29, y - 20), (x + 40, y - 7), (x + 37, y + 1)]
        access.line(c, tail, '#8f8278', 3)
        angiogram.dot(c, x + 37, y + 2, 4.5, '#726d66')


def comfort(c, p, t):
    if p < .41:
        room(c)
        tilt = access.smooth((p - .19) / .13)
        cabg_icu.monitor(c, t)
        bed(c, t, tilt=tilt, report=p < .20)
        figure(c, 745, 623, t, palette=STAFF, gesture=.44 + .24 * sin(t * 2), facing=-1, scale=.82)
        footer(c, 'Tell the nurse if pain affects breathing or movement' if p < .19
               else 'Staff can review pain relief and support your movement')
    elif p < .82:
        room(c)
        bed(c, t, tilt=.8)
        figure(c, 779, 629, t, palette=FAMILY, gesture=.44 + .32 * sin(t * 2.25), facing=-1, scale=.79)
        figure(c, 1052, 629, t, palette=STAFF, gesture=.18 + .18 * sin(t * 1.8), facing=-1, scale=.86)
        footer(c, 'Tell the nurse about new confusion or unusual sleepiness' if p < .59
               else 'Changes in attention can come and go')
    else:
        orientation_items(c, t, (p - .82) / .18)
        footer(c, 'Ask if familiar conversation, glasses or hearing aids may help')
    header(c, 'Tell the nurse what has changed')


def chair(c, x, y):
    block(c, x - 97, y - 176, 169, 163, 32, '#6c9c8a')
    block(c, x - 89, y - 165, 153, 150, 26, '#a0c1af')
    block(c, x - 95, y - 31, 184, 35, 13, '#507f71')
    for offset in (-68, 64):
        access.line(c, [(x + offset, y), (x + offset, y + 114)], '#577b70', 13)


def mobility(c, p, t):
    if p < .25:
        if p < .125:
            room(c)
            cabg_icu.monitor(c, t)
        else:
            room(c, ward=True)
        bed(c, t, tilt=.58)
        figure(c, 873 if p < .125 else 961, 631, t, palette=STAFF, facing=-1, scale=.88)
        footer(c, 'The team decides when ward care can take over')
    elif p < .40:
        room(c, ward=True)
        chair(c, 586, 526)
        figure(c, 589, 635, t, seated=True, scale=1.1)
        figure(c, 842, 631, t, palette=STAFF, gesture=.32 + .25 * sin(t * 2.4), facing=-1, scale=1.05)
        footer(c, 'Sitting in a chair')
    elif p < .54:
        room(c, ward=True)
        chair(c, 529, 526)
        figure(c, 618, 634, t, gesture=.20 + .16 * sin(t * 2.1), scale=1.05)
        figure(c, 838, 630, t, palette=STAFF, facing=-1, scale=1.1)
        footer(c, 'Standing with help')
    elif p < .75:
        room(c, ward=True)
        travel = access.smooth((p - .54) / .21)
        position = 454 + 286 * travel
        figure(c, position, 630, t, walking=True, scale=1.05)
        figure(c, position + 183, 622, t - .36, palette=STAFF, walking=True, scale=1.04)
        footer(c, 'Taking a short walk with staff')
    else:
        room(c, ward=True)
        chair(c, 540, 526)
        figure(c, 550, 635, t, seated=True, gesture=.4 + .25 * sin(t * 2.8), scale=1.06)
        figure(c, 825, 629, t, palette=STAFF, facing=-1, scale=1.09)
        footer(c, 'Tell staff if you feel dizzy, breathless or too uncomfortable' if p < .94
               else 'Your next step depends on how you are recovering')
    header(c, 'Move with the team’s help')


def paper(c, x, y, w, h):
    block(c, x + 11, y + 17, w, h, 22, '#9cbeb1')
    block(c, x, y, w, h, 22, '#537e6e')
    block(c, x + 12, y + 12, w - 24, h - 24, 16, '#f7fbf3')
    block(c, x + w * .35, y - 10, w * .30, 28, 12, '#9cbeab')


PLAN_ROWS = ('Medicines', 'Wounds', 'Activity, driving and work',
             'Follow-up and contacts')


def plan(c, t, emphasis, message):
    room(c, ward=True)
    figure(c, 267, 628, t, seated=True, gesture=.12 + .16 * sin(t * 2.2), scale=.91)
    figure(c, 1107, 623, t, palette=STAFF, gesture=.29 + .20 * sin(t * 2.6), facing=-1, scale=.85)
    oval(c, 210, 548, 898, 73, '#537e6e', 51)
    block(c, 199, 527, 905, 57, 27, '#a4c7b5')
    c.save()
    c.translate(640, 416)
    c.rotate(.55 * sin(t * 1.19))
    c.translate(-640, -416)
    paper(c, 359, 190, 562, 389)
    access.text(c, 'My discharge plan', 396, 253, 40, INK, access.HEADING)
    for index, row in enumerate(PLAN_ROWS):
        y = 306 + 62 * index
        if index == emphasis:
            block(c, 388, y - 34, 502, 49, 11, '#d0e8d6')
            progress = .85 + .08 * sin(t * 2.1)
            access.line(c, [(437, y + 10), (437 + 329 * progress, y + 10)], '#8cb79e', 2.7)
        angiogram.dot(c, 412, y - 7, 6.2, '#4b856f')
        access.text(c, row, 436, y, 32, INK)
    c.restore()
    footer(c, message)


def covered_dressings(c, t, p):
    room(c)
    block(c, 83, 181, 536, 443, 27, '#d2e7db')
    block(c, 647, 181, 550, 443, 27, '#dcece2')
    breath = 1. + .024 * sin(t * 2.1)
    c.save()
    c.translate(350, 439)
    c.scale(breath, breath)
    body(c, (0, 101), PATIENT, 0.)
    sleeve(c, (-47, -21), (-79, 25), (-90, 82), PATIENT)
    sleeve(c, (47, -21), (79, 25), (90, 82), PATIENT)
    block(c, -20, -18, 40, 110, 15, '#f0dbbc')
    block(c, -13, -6, 26, 84, 10, '#fff1d7')
    c.restore()
    access.text(c, 'Chest dressing', 204, 590, 32, INK)
    for index, offset in enumerate((0, 1)):
        x = 839 + 99 * offset
        bend = 10 * sin(t * .9 + index)
        access.line(c, [(x, 301), (x + bend, 391), (x + 16, 518)], '#52786d', 89)
        access.line(c, [(x - 25, 305), (x - 22 + bend, 388), (x - 8, 510)], '#779f91', 6, 180)
        access.line(c, [(x + 8, 535), (x + 53, 538)], '#36594e', 41)
        if index == 0:
            block(c, x - 20 + bend, 386, 52, 94, 14, '#f0dbbc')
            block(c, x - 10 + bend, 395, 32, 75, 11, '#fff1d7')
    detail = 'Leg dressing, if applicable'
    access.text(c, detail, 727, 590, 32, INK)
    footer(c, 'Ask for instructions for each wound')


def discharge(c, p, t):
    if p < .25:
        plan(c, t, 0, 'Ask which medicines changed and what to take now')
    elif p < .53:
        covered_dressings(c, t, (p - .25) / .28)
    elif p < .75:
        plan(c, t, 2, 'Ask about activity, driving, work and help at home')
    else:
        plan(c, t, 3, 'Keep your follow-up details and after-hours contact')
    header(c, 'Take home a plan you can use')


SCENES = {'P04': comfort, 'P05': mobility, 'P06': discharge}


def draw(canvas, ident, progress, seconds):
    SCENES[ident](canvas, progress, seconds)
