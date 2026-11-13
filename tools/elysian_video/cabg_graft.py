"""Original consultation, graft anatomy, and bypass-circuit animation for CABG."""

from bisect import bisect_right
from functools import lru_cache
from math import hypot, sin, tau

import skia

from . import access as art
from . import angiogram


INK = '#18463b'
MUTED = '#43695d'
PALE = '#f2f8f2'
GRAFT = ('#185c52', '#579e87', '#c0dfba')
ARTERIAL = ('#854858', '#d88b83', '#f6b1a1')
VENOUS = ('#305665', '#5f8b99', '#b4d3d7')
FLOW = '#ffe2a9'
ANATOMY = angiogram.art
TOPIC = 'CARDIAC SURGERY'


def oval(canvas, x, y, width, height, brush):
    canvas.drawOval(skia.Rect.MakeXYWH(x, y, width, height), brush)


def rounded(canvas, x, y, width, height, radius, shade, alpha=255):
    angiogram.block(canvas, x, y, width, height, radius, art.solid(shade, alpha))


def studio_light(canvas):
    art.rect(canvas, 0, 0, 1280, 720,
             art.grad(150, 20, 1100, 720, ['#fafcf9', '#eff6ef', '#d8eae0']))


def footer(canvas, label, accent=MUTED):
    art.rect(canvas, 54, 644, 1172, 2, art.solid('#bacfc4'))
    art.text(canvas, label, 55, 686, 30, accent, art.REGULAR)


def vessel(canvas, points, width, colors=ARTERIAL, alpha=255):
    """A vessel with a distinct wall and light rim on the same centerline."""
    wall, lumen, rim = colors
    art.line(canvas, points, wall, width + 5, alpha)
    art.line(canvas, points, lumen, width, alpha)
    art.line(canvas, tuple((x - 1.5, y - 1.9) for x, y in points), rim,
             max(1, width * .22), alpha)


@lru_cache(maxsize=128)
def distances(points):
    result = [0.]
    for a, b in zip(points, points[1:]):
        result.append(result[-1] + hypot(b[0] - a[0], b[1] - a[1]))
    return tuple(result)


def location(points, length, value):
    if value <= 0:
        return points[0]
    if value >= length[-1]:
        return points[-1]
    index = bisect_right(length, value)
    before, after = points[index - 1:index + 1]
    portion = (value - length[index - 1]) / (length[index] - length[index - 1])
    return tuple(a + (b - a) * portion for a, b in zip(before, after))


def flow(canvas, points, time, *, speed=139, spacing=126, radius=5, shade=FLOW):
    length = distances(points)
    for offset in range(0, round(length[-1]), spacing):
        phase = (time * speed + offset) % length[-1]
        tail = location(points, length, phase - radius * 1.7)
        point = location(points, length, phase)
        opacity = round(255 * min(1, phase / 14, (length[-1] - phase) / 16))
        art.line(canvas, (tail, point), shade, radius * 1.65, opacity)
        angiogram.dot(canvas, *point, radius, shade, opacity)


def graft_pulses(canvas, points, time, *, speed=168, depth=12.5, tail=52):
    """Long tracer pulses make progress legible in the smaller vertical crop."""
    length = distances(points)
    for offset in range(0, round(length[-1]), 188):
        phase = (time * speed + offset) % length[-1]
        start = max(0., phase - tail)
        left = bisect_right(length, start)
        right = bisect_right(length, phase)
        trail = (location(points, length, start), *points[left:right],
                 location(points, length, phase))
        opacity = round(240 * min(1., phase / 33, (length[-1] - phase) / 26))
        art.line(canvas, trail, '#edb66e', depth, opacity)
        art.line(canvas, trail, '#ffe7ad', depth*.48, opacity)


def guide(canvas, points, label, x, y, *, shade=INK):
    art.line(canvas, points, shade, 2.4, 215)
    angiogram.dot(canvas, *points[0], 5.4, '#fff7df')
    art.text(canvas, label, x, y, 30, shade)


def position(point):
    return 270 + (point[0] - 151) * 1.87, 166 + (point[1] - 76) * 1.06


HEART = tuple(map(position, ANATOMY.MYOCARDIUM))
AORTA = tuple(map(position, ANATOMY.AORTA))
LAD = tuple(map(position, ANATOMY.LAD))
LEFT_MAIN = tuple(map(position, ANATOMY.LEFT_MAIN))
LCX = tuple(map(position, ANATOMY.LCX))
RCA = tuple(map(position, ANATOMY.RCA))
ROOT_JUNCTION = AORTA[16]
NARROW_INDEX = 13
GRAFT_INDEX = 29
PLAQUE = LAD[NARROW_INDEX]
TARGET = LAD[GRAFT_INDEX]
DIAGONAL = ANATOMY.curve(LAD[37], ((701, 514), (745, 522), (769, 560)))

# In the anterior view the patient's left is to the right of the screen.
# Branches progress from the ascending side toward the descending side.
BRACHIOCEPHALIC = ANATOMY.curve(AORTA[22], ((551, 160), (501, 145), (486, 140)))
LEFT_CAROTID = ANATOMY.curve(AORTA[30], ((635, 175), (652, 155), (656, 139)))
SUBCLAVIAN = ANATOMY.curve(AORTA[38], ((713, 165), (747, 163), (779, 172)),
                           ((818, 176), (868, 181), (907, 205)))
CHEST_ORIGIN = SUBCLAVIAN[18]
CHEST_GRAFT = ANATOMY.curve(CHEST_ORIGIN,
                            ((805, 219), (809, 266), (801, 325)),
                            ((790, 400), (729, 440), TARGET))
FREE_GRAFT = ANATOMY.curve(ROOT_JUNCTION,
                           ((612, 225), (713, 218), (776, 274)),
                           ((834, 346), (762, 435), TARGET))


@lru_cache(maxsize=1)
def anatomy_plate():
    """Vector anatomy cached as a 2× texture. No flow is baked into the plate."""
    surface = skia.Surface(2560, 1440)
    canvas = surface.getCanvas()
    canvas.scale(2, 2)
    oval(canvas, 281, 289, 653, 335,
         art.grad(320, 306, 886, 637, ['#e7eee6', '#b6cec0', '#deece3']))
    art.line(canvas, AORTA[52:], '#6b424e', 49)
    canvas.drawPath(art.path(HEART, True),
                    art.grad(343, 284, 882, 626, ['#f3b8a2', '#bf7981', '#683f53']))
    canvas.drawPath(art.path(tuple(map(position, ANATOMY.RV_SHADOW)), True),
                    art.grad(375, 364, 698, 537, ['#e2a394', '#bc7580', '#96566b']))
    art.line(canvas, HEART, '#824956', 3, 203)
    for i in range(19):
        x = 396 + i * 20
        extent = 114 + 110 * (1 - abs(i - 11) / 12)
        y = 355 + abs(i - 11) * 2.4
        fibers = ANATOMY.curve((x, y), ((x-11, y+extent*.28),
                                         (x+16, y+extent*.67), (x+31, y+extent)))
        canvas.save()
        canvas.clipPath(art.path(HEART, True), doAntiAlias=True)
        art.line(canvas, fibers, '#ffcab5', 1.5, 45)
        canvas.restore()

    for branch in (BRACHIOCEPHALIC, LEFT_CAROTID, SUBCLAVIAN):
        vessel(canvas, branch, 20)
    vessel(canvas, AORTA, 47)
    for branch in (*ANATOMY.RCA_TWIGS, *ANATOMY.LEFT_TWIGS):
        vessel(canvas, tuple(map(position, branch)), 5,
               ('#824955', '#bf7680', '#e6a497'), 219)
    for branch, width in ((RCA, 13), (LEFT_MAIN, 13), (LCX, 11), (LAD, 14), (DIAGONAL, 8)):
        vessel(canvas, branch, width)

    # Both graft examples retain this lesion. The native channel narrows here.
    wedge = LAD[NARROW_INDEX-2:NARROW_INDEX+3]
    art.line(canvas, wedge, '#633b4a', 16)
    art.line(canvas, wedge, '#f0a496', 4.2)
    art.line(canvas, tuple((x-4.5, y-.4) for x, y in wedge), '#e2ab72', 4.3)
    art.line(canvas, tuple((x+4.5, y+.6) for x, y in wedge), '#e2ab72', 4.3)
    return surface.makeImageSnapshot()


def draw_anatomy(canvas):
    canvas.drawImageRect(anatomy_plate(), skia.Rect.MakeWH(1280, 720),
                         skia.SamplingOptions(skia.FilterMode.kLinear))


def graft_example(canvas, progress, seconds, chest_artery=False, heading=None,
                  caption=None, *, joined_at=.52):
    """Fixed anterior view. Moving markers enter the LAD past the native lesion."""
    studio_light(canvas)
    draw_anatomy(canvas)
    heading = heading or ('In-place chest artery graft' if chest_artery else 'Free vein graft')
    graft = CHEST_GRAFT if chest_artery else FREE_GRAFT
    origin = CHEST_ORIGIN if chest_artery else ROOT_JUNCTION
    lead = SUBCLAVIAN[:19] if chest_artery else AORTA[5:17]
    background_flow = AORTA[:38]
    flow(canvas, background_flow, seconds, speed=126, spacing=128, radius=6)
    flow(canvas, LEFT_MAIN + LAD[1:NARROW_INDEX], seconds, speed=92, spacing=82, radius=4)

    # A traced emphasis reveals a graft that is already joined anatomically.
    # Its last point always meets the same centerline in both examples.
    traced = art.smooth((progress - .10) / (joined_at - .10))
    vessel(canvas, graft, 14, GRAFT, 82)
    if traced > 0:
        vessel(canvas, ANATOMY.trace(graft, traced), 17, GRAFT)

    if progress >= joined_at:
        vessel(canvas, graft[-3:], 13, GRAFT)
        main_outlet = lead + graft[1:] + LAD[GRAFT_INDEX+1:]
        side_outlet = lead + graft[1:] + LAD[GRAFT_INDEX+1:38] + DIAGONAL[1:]
        graft_pulses(canvas, main_outlet, seconds)
        if progress >= joined_at + .10:
            branch_start = distances(side_outlet)[len(side_outlet) - len(DIAGONAL)]
            # One tracer enters the diagonal beyond its real LAD connection.
            travel = (seconds * 168) % (distances(side_outlet)[-1] + 35)
            if branch_start <= travel <= distances(side_outlet)[-1]:
                x, y = location(side_outlet, distances(side_outlet), travel)
                angiogram.dot(canvas, x, y, 5.2, FLOW)
    else:
        emphasis = ANATOMY.trace(lead, .18 + .82 * art.smooth(progress / .23))
        art.line(canvas, emphasis, '#fff0ba', 4.5)
        inflow_route = AORTA[:17] if not chest_artery else AORTA[:39] + SUBCLAVIAN[1:19]
        graft_pulses(canvas, inflow_route, seconds, speed=182, depth=23, tail=96)
        active_length = max(.02, traced)
        active = ANATOMY.trace(graft, active_length)
        if len(active) > 1:
            guide_start = distances(active)[-1] - 49
            lead_length = distances(active)
            moving = (location(active, lead_length, guide_start), *active[-6:])
            art.line(canvas, moving, '#a7e1b1', 10.8)
            art.line(canvas, moving, '#e7f4d6', 5.7)
        # Switch the teaching camera emphasis to the upcoming connection without
        # changing the anatomy or implying flow across the highlight before it joins.
        if progress >= joined_at * .44:
            ring = 28 + 11 * (.5 + .5 * sin(seconds * 3.4))
            center_x, center_y = active[-1]
            oval(canvas, center_x-ring, center_y-ring, 2*ring, 2*ring,
                 art.solid('#e4e9a7', 73))
            angiogram.dot(canvas, center_x, center_y, 6.7, '#f4e5ad', 215)

    angiogram.header(canvas, heading, TOPIC)
    if progress < joined_at - .05:
        label = 'Left subclavian artery' if chest_artery else 'Ascending aorta'
        if chest_artery:
            guide(canvas, (origin, (947, 194), (1210, 194)), label, 947, 181)
            art.text(canvas, 'Patient’s left', 955, 236, 26, MUTED, art.REGULAR)
        else:
            guide(canvas, (origin, (443, 232), (68, 232)), label, 67, 216)
    elif progress < max(.83, joined_at + .11):
        guide(canvas, (TARGET, (905, 478), (1225, 478)),
              'Join beyond narrowing', 905, 465)
    else:
        guide(canvas, (PLAQUE, (421, 401), (69, 401)), 'Original narrowing', 68, 384)
        guide(canvas, (LAD[-8], (869, 551), (1201, 551)), 'Downstream artery', 879, 538)
    footer(canvas, caption or 'Oxygen-rich blood travels through the graft to the heart muscle')


def consultation_figure(canvas, x, y, scale, clothes, direction, t):
    """Anonymous, fully clothed participant, shown without identifying features."""
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(scale * direction, scale)
    coat = ANATOMY.curve((-88, 176), ((-85, 125), (-65, 97), (-35, 94)),
                         ((-20, 90), (10, 89), (27, 94)),
                         ((68, 106), (85, 129), (89, 176)))
    canvas.drawPath(art.path(coat, True),
                    art.grad(-82, 90, 95, 184, clothes))
    oval(canvas, -38, 20, 76, 89, art.solid('#c9ab95'))
    oval(canvas, -40, 13, 75, 40, art.solid('#7c8d80'))
    art.line(canvas, ((-25, 103), (0, 124), (25, 102)), clothes[0], 5, 237)
    reach = .5 + .5 * sin(t * 2.05)
    sleeve = ANATOMY.curve((51, 130), ((70, 143), (99, 153), (113 + reach*13, 159 - reach*10)))
    art.line(canvas, sleeve, clothes[1], 27)
    angiogram.dot(canvas, *sleeve[-1], 9, '#c9ab95')
    canvas.restore()


def heart_team(canvas, progress, seconds, cues):
    tests = cues.get('tests', .27)
    pump = cues.get('pumping', .31)
    health = cues.get('health', .43)
    priorities = cues.get('priorities', .58)
    question1 = cues.get('question1', .81)
    question2 = cues.get('question2', .91)
    studio_light(canvas)
    angiogram.header(canvas, 'How the Heart Team weighs the choice', TOPIC)
    if progress < priorities:
        consultation_figure(canvas, 182, 230, 1.20, ('#b5c3ab', '#8f9d7c', '#687956'), 1, seconds)
        consultation_figure(canvas, 1090, 218, 1.18, ('#79ae99', '#588777', '#356456'), -1, seconds + .95)
        consultation_figure(canvas, 934, 187, .78, ('#d6e5d9', '#a9c4b4', '#87a99c'), -1, seconds + 2.3)
        desk = [(70, 505), (379, 379), (876, 373), (1212, 505), (1184, 578), (92, 578)]
        canvas.drawPath(art.path(desk, True),
                        art.grad(330, 390, 985, 581, ['#d8e7df', '#bbd2c3', '#a7c1b1']))
        art.line(canvas, desk[1:5], '#ecf4eb', 4)
        shift = -47 + 78 * art.smooth(progress / .24)
        canvas.save()
        canvas.translate(shift, 0)
        rounded(canvas, 342, 208, 610, 296, 22, '#99b6a7', 100)
        rounded(canvas, 331, 195, 610, 296, 22, '#214b42')
        if progress < pump:
            center = (602, 296)
            coronary = ANATOMY.curve((500, 245), ((533, 266), (545, 287), center),
                                      ((631, 318), (611, 367), (587, 429)))
            branch = ANATOMY.curve(center, ((658, 285), (701, 303), (757, 364)))
            for route in (coronary, branch):
                vessel(canvas, route, 14, ('#5d7e72', '#c7d3bf', '#f0ebd4'))
                flow(canvas, route, seconds, speed=91, spacing=75, radius=5)
            art.text(canvas, 'Simulated angiogram', 373, 468, 26, '#e9f4e7', art.REGULAR)
        elif progress < health:
            phase = .5 + .5 * sin(seconds * tau * .99)
            chamber = ANATOMY.curve((513, 255), ((570, 225), (676, 248), (686, 299)),
                                     ((698, 360), (650, 401), (620, 423)),
                                     ((586, 419), (531, 367), (513, 255)))
            canvas.save()
            canvas.translate(603, 330)
            canvas.scale(1-.14*phase, 1-.09*phase)
            canvas.translate(-603, -330)
            canvas.drawPath(art.path(chamber, True),
                            art.grad(528, 244, 683, 420, ['#c3e0cd', '#92baa9', '#487b6e']))
            canvas.restore()
            art.text(canvas, 'Illustrated heart ultrasound', 373, 468, 26, '#e9f4e7', art.REGULAR)
        else:
            lane = (progress-health) / (priorities-health)
            focus = art.smooth(lane)
            rounded(canvas, 460, 244, 368, 179, 16, '#315c50')
            for i, (label, y) in enumerate((('Health conditions', 305), ('Strength and mobility', 378))):
                rounded(canvas, 481, y-38, 320, 55, 11, '#508475' if (i == int(focus > .46)) else '#3b675b')
                art.text(canvas, label, 500, y, 27, '#e8f4e9')
                x = 479 + 313 * ((seconds * .55 + i * .24) % 1)
                art.line(canvas, ((x, y+10), (x+7, y+10)), '#91c4b1', 3)
            art.text(canvas, 'Examples of health factors', 373, 468, 26, '#e9f4e7', art.REGULAR)
        canvas.restore()
        caption = ('Specialists review options with the patient' if progress < tests
                   else 'Test results, pumping function and overall health')
    else:
        # Move from tests to the patient's questions while keeping the consultation visible.
        consultation_figure(canvas, 166, 266, 1.48, ('#b5c3ab', '#8f9d7c', '#687956'), 1, seconds)
        consultation_figure(canvas, 1104, 265, 1.48, ('#79ae99', '#588777', '#356456'), -1, seconds+.95)
        questions = (
            ('Symptoms, risks', 'and recovery', 'What matters most to you?'),
            ('What could this', 'treatment do for me?', 'Ask about expected benefits'),
            ('What alternatives', 'fit my situation?', 'Discuss choices with the care team'),
        )
        index = 0 if progress < question1 else (1 if progress < question2 else 2)
        line1, line2, caption = questions[index]
        y = 238 + 7 * sin(seconds * 1.1)
        rounded(canvas, 328, y, 624, 273, 25, '#c1d8ca')
        rounded(canvas, 319, y-9, 624, 273, 25, '#f7fbf5')
        art.line(canvas, ((374, y+54), (585, y+54)), '#4a8c76', 6)
        art.text(canvas, line1, 373, y+125, 55, INK, art.HEADING)
        art.text(canvas, line2, 373, y+189, 55, INK, art.HEADING)
        progress_bar = .5 + .5 * sin(seconds * 1.55)
        art.line(canvas, ((374, y+227), (451 + 73*progress_bar, y+227)), '#99bbab', 5)
    footer(canvas, caption)


def covered_patient(canvas, seconds):
    """Draped horizontal figure and bedside monitor. No procedure site is exposed."""
    rounded(canvas, 109, 473, 1001, 56, 17, '#799f91')
    rounded(canvas, 146, 521, 928, 26, 9, '#51786e')
    rounded(canvas, 220, 555, 21, 66, 8, '#739d8b')
    rounded(canvas, 951, 555, 21, 66, 8, '#739d8b')
    rounded(canvas, 165, 370, 249, 104, 34, '#d8eae0')
    oval(canvas, 219, 381, 127, 89, art.solid('#c8a690'))
    oval(canvas, 209, 377, 94, 79, art.solid('#779c90'))
    lift = sin(seconds * tau * .33) * 8
    drape = ANATOMY.curve((320, 438), ((385, 378), (483, 337+lift), (580, 354+lift)),
                          ((722, 372+lift), (829, 418), (1001, 431)),
                          ((1062, 432), (1086, 462), (1083, 482)))
    canvas.drawPath(art.path(drape + ((335, 482),), True),
                    art.grad(447, 353, 682, 502, ['#b2d8cc', '#6ca89a', '#367a70']))
    art.line(canvas, drape, '#c4e3d7', 4)
    rounded(canvas, 862, 176, 287, 186, 20, '#294c46')
    rounded(canvas, 881, 194, 249, 144, 12, '#123d37')
    trace = []
    for i in range(100):
        phase = (i/63 + seconds * .99) % 1
        beat = max(0, 1 - abs(phase - .38) / .07)
        trough = max(0, 1 - abs(phase - .47) / .061)
        trace.append((891 + i * 2.30, 265 - 58*beat + 22*trough))
    art.line(canvas, trace, '#bdebd0', 4)


@lru_cache(maxsize=1)
def operation_plate():
    surface = skia.Surface(2560, 1440)
    canvas = surface.getCanvas()
    canvas.scale(2, 2)
    canvas.translate(-154, 57)
    canvas.scale(.90, .86)
    draw_anatomy(canvas)
    return surface.makeImageSnapshot()


def operation_point(point):
    return .90 * point[0] - 154, .86 * point[1] + 57


VENOUS_DRAIN = ANATOMY.curve((205, 343), ((183, 407), (216, 508), (362, 546)),
                             ((528, 581), (656, 528), (800, 500)))
ARTERIAL_RETURN = ANATOMY.curve((800, 278), ((650, 278), (548, 213), (479, 222)),
                               ((406, 233), (390, 265), operation_point(ROOT_JUNCTION)))


def cardiopulmonary_bypass(canvas, progress, seconds, cues):
    join = cues.get('join', .60)
    resume = cues.get('resume', .73)
    studio_light(canvas)
    tissue = operation_plate()
    return_to_heart = progress >= resume
    canvas.save()
    if return_to_heart:
        motion = 1 + .022 * sin(seconds * tau * 1.05)
        canvas.translate(337, 359)
        canvas.scale(motion, motion)
        canvas.translate(-337, -359)
    canvas.drawImageRect(tissue, skia.Rect.MakeWH(1280, 720),
                         skia.SamplingOptions(skia.FilterMode.kLinear))
    if progress >= join:
        graft = tuple(map(operation_point, FREE_GRAFT))
        vessel(canvas, graft, 14, GRAFT)
        if return_to_heart:
            flow(canvas, graft + tuple(map(operation_point, LAD[GRAFT_INDEX+1:])),
                 seconds, speed=155, spacing=115, radius=5)
    canvas.restore()

    line_alpha = 255 if not return_to_heart else round(255*(1-.73*art.smooth((progress-resume)/.08)))
    vessel(canvas, VENOUS_DRAIN, 15, VENOUS, line_alpha)
    vessel(canvas, ARTERIAL_RETURN, 15, ARTERIAL, line_alpha)
    if not return_to_heart:
        flow(canvas, VENOUS_DRAIN, seconds, speed=166, spacing=115, radius=5, shade='#d0e5ec')
        flow(canvas, ARTERIAL_RETURN, seconds, speed=166, spacing=115, radius=5)

    rounded(canvas, 793, 212, 385, 333, 25, '#a0bcb1', 125)
    rounded(canvas, 783, 201, 385, 333, 25, '#224d43')
    rounded(canvas, 812, 229, 328, 244, 15, '#153b34')
    art.text(canvas, 'Heart-lung machine', 827, 393, 30, '#edf6e9')
    y1, y2 = 432, 278
    internal = ((800, 500), (930, 500), (930, y1), (1062, y1),
                (1062, y2), (800, y2))
    vessel(canvas, internal[:4], 14, VENOUS, line_alpha)
    vessel(canvas, internal[3:], 14, ARTERIAL, line_alpha)
    oval(canvas, 1039, 312, 46, 85, art.solid('#b8d5c5', line_alpha))
    for row in range(5):
        shift = (seconds * 41 + row * 14) % 64 if not return_to_heart else row * 13
        art.line(canvas, ((1048, 323+shift), (1077, 323+shift)),
                 '#6b9d94', 3, line_alpha)
    if not return_to_heart:
        flow(canvas, internal[:4], seconds, speed=152, spacing=106, radius=4.8, shade='#d0e5ec')
        flow(canvas, internal[3:], seconds, speed=152, spacing=106, radius=4.8)
    heading = 'The heart resumes pumping' if return_to_heart else 'Temporary support during surgery'
    angiogram.header(canvas, heading, TOPIC)
    if progress < join:
        guide(canvas, ((676, 511), (675, 575), (768, 575)),
              'Venous drainage', 456, 614, shade='#3b606b')
        guide(canvas, ((646, 244), (695, 177), (1121, 177)),
              'Oxygenated arterial return', 710, 164, shade='#764854')
    if join <= progress < resume:
        target = operation_point(TARGET)
        guide(canvas, (target, (649, 503), (764, 503)), 'Graft joined', 620, 488)
    footer(canvas, 'The team comes off the machine when it is safe' if return_to_heart
           else 'The machine adds oxygen and pumps blood to the body')


def surgery(canvas, progress, seconds, cues):
    anaesthesia = cues.get('anaesthesia', .16)
    breastbone = cues.get('breastbone', .30)
    machine = cues.get('machine', .44)
    beating = cues.get('beating', .81)
    if progress < machine:
        studio_light(canvas)
        covered_patient(canvas, seconds)
        if progress < anaesthesia:
            title = 'Planning and preparation'
            detail = 'Follow the hospital’s individual instructions'
        elif progress < breastbone:
            title = 'General anaesthesia and monitoring'
            detail = 'The team watches the patient throughout surgery'
        else:
            title = 'Reaching the heart'
            detail = 'In the conventional approach, the team reaches the heart through the breastbone'
            # Internal-only orientation silhouette above the drape.
            outline = ANATOMY.curve((520, 209), ((555, 179), (622, 172), (654, 188)),
                                     ((693, 179), (742, 194), (767, 218)),
                                     ((751, 252), (730, 305), (699, 339)),
                                     ((675, 359), (638, 358), (614, 341)),
                                     ((573, 323), (546, 274), (520, 209)))
            canvas.drawPath(art.path(outline, True),
                            art.grad(548, 198, 743, 341, ['#c7ddd0', '#7aa897']))
            midline = ANATOMY.curve((643, 204), ((652, 226), (656, 270), (655, 321)))
            art.line(canvas, midline, '#eff3df', 12)
            trace = ANATOMY.trace(midline, .2 + .8 * ((seconds * .44) % 1))
            art.line(canvas, trace, '#537f70', 4)
        angiogram.header(canvas, title, TOPIC)
        footer(canvas, detail)
    elif progress < beating:
        cardiopulmonary_bypass(canvas, progress, seconds, cues)
    else:
        studio_light(canvas)
        canvas.save()
        canvas.translate(651, 398)
        pulse = 1 + .034 * sin(seconds * tau * 1.04)
        canvas.scale(pulse, pulse)
        canvas.translate(-651, -398)
        draw_anatomy(canvas)
        vessel(canvas, FREE_GRAFT, 16, GRAFT)
        flow(canvas, FREE_GRAFT + LAD[GRAFT_INDEX+1:], seconds, speed=165, spacing=115, radius=5)
        canvas.restore()
        target_x, target_y = TARGET
        # A stabilizer holds a small local area while surrounding muscle moves.
        art.line(canvas, ((1046, 284), (889, 361), (target_x+43, target_y-15)), '#446c67', 14)
        art.line(canvas, ((target_x-15, target_y-18), (target_x+42, target_y-18)), '#8cb3a5', 11)
        art.line(canvas, ((target_x-15, target_y+18), (target_x+42, target_y+18)), '#8cb3a5', 11)
        angiogram.header(canvas, 'Selected beating-heart option', TOPIC)
        guide(canvas, ((target_x+31, target_y+18), (871, 538), (1194, 538)),
              'Small area steadied', 886, 525)
        footer(canvas, 'In selected cases, surgery can be performed without a heart-lung machine')


def draw(canvas, ident, progress, seconds, *, cues=None):
    """Draw a scene with optional exact voice cue fractions relative to that scene."""
    cues = cues or {}
    if ident == 'P06':
        heart_team(canvas, progress, seconds, cues)
    elif ident == 'P07':
        free_start = cues.get('free_start', .48)
        if progress < free_start:
            joined = cues.get('chest_join', free_start*.73) / free_start
            graft_example(canvas, progress / free_start, seconds, chest_artery=True,
                          joined_at=joined)
        else:
            joined = (cues.get('free_join', free_start+(1-free_start)*.42) - free_start) / (1-free_start)
            graft_example(canvas, (progress-free_start) / (1-free_start), seconds,
                          chest_artery=False, joined_at=joined)
    elif ident == 'P08':
        surgery(canvas, progress, seconds, cues)
    else:
        raise ValueError(f'Unknown CABG graft scene: {ident}')
