"""Coronary bypass results, recovery and safety-net scenes for Cardiac Surgery 01."""

from math import cos, pi, sin

import skia

from . import access, angiogram, cabg_core


TOPIC = 'CARDIAC SURGERY'
INK = '#123e35'
MUTED = '#315b53'
MINT = '#cce9da'
EMERALD = '#00835b'
AMBER = '#f4d4a4'
EMERGENCY = '#7c343d'


def round_box(canvas, x, y, width, height, radius, color):
    angiogram.block(canvas, x, y, width, height, radius, access.solid(color))


def ellipse(canvas, x, y, width, height, paint):
    canvas.drawOval(skia.Rect.MakeXYWH(x, y, width, height), paint)


def title(canvas, heading):
    angiogram.header(canvas, heading, TOPIC)


def footer(canvas, first, second=None, *, urgent=False):
    tone = EMERGENCY if urgent else '#17463c'
    height = 119 if second else 76
    access.rect(canvas, 0, 720-height, 1280, height, access.solid(tone))
    access.text(canvas, first, 55, 720-height+46, 40 if second else 36, '#f5fcf7')
    if second:
        access.text(canvas, second, 57, 691, 29, '#f6e4db' if urgent else MINT,
                    access.REGULAR)


def pulse_points(x, y, width, height, seconds):
    shape = (0, 0, -5, -10, 0, 0, 4, -34, 20, -2, 0, 0, -10, -12, 0, 0, 0)
    points = []
    for index in range(110):
        position = index*.59-seconds*16
        start = int(position // 1)
        fraction = position-start
        value = shape[start % len(shape)]*(1-fraction)+shape[(start+1) % len(shape)]*fraction
        points.append((x+index*width/109, y+height*value/48))
    return points


def monitor(canvas, seconds, *, x=865, y=204, width=323):
    round_box(canvas, x+10, y+15, width, 234, 25, '#b9d0c7')
    round_box(canvas, x, y, width, 234, 25, '#25443e')
    round_box(canvas, x+17, y+17, width-34, 184, 14, '#102c29')
    for row in range(3):
        yy = y+80+42*row
        access.line(canvas, [(x+34, yy), (x+width-34, yy)], '#385b52', 1.5)
    trace = pulse_points(x+34, y+101, width-68, 57, seconds)
    access.line(canvas, trace, '#68b89f', 9, 125)
    access.line(canvas, trace, '#c5efcf', 4)
    breathing = [(x+36+i*(width-74)/87,
                  y+166+12*sin(i*.12-seconds*2.8)) for i in range(88)]
    access.line(canvas, breathing, '#f2c996', 3.5)
    canvas.save()
    canvas.clipRect(skia.Rect.MakeXYWH(x+18, y+18, width-36, 179))
    left = x+18+((seconds*103) % (width-36))
    access.rect(canvas, left, y+19, 27, 176, access.solid('#a2d9c3', 29))
    canvas.restore()
    angiogram.dot(canvas, x+width-31, y+216, 5, '#b0dbc3')
    access.text(canvas, 'Illustrated monitoring', x+23, y+227, 23, '#e5f2e7')


def graft_shot(canvas, seconds, *, close=False):
    if close:
        canvas.save()
        canvas.translate(-61, -27)
        canvas.scale(1.095, 1.095)
    cabg_core.graft_cutaway(canvas, seconds, reveal=1.0, graft=True)
    if close:
        canvas.restore()
    # Keep the original graft and lesion positions, even as the frame shifts.
    access.rect(canvas, 0, 0, 1280, 155,
                access.grad(0, 0, 0, 155, ['#f3f9f4', '#e4f0e8']))


def result(canvas, progress, seconds):
    if progress < .23:
        graft_shot(canvas, seconds, close=progress >= .14)
        title(canvas, 'Blood takes a new route')
        footer(canvas, 'The graft carries blood beyond the narrowing' if progress < .14
               else 'Some people have less angina after recovery')
        return
    if progress < .42:
        cabg_core.coronary_map(canvas, seconds)
        title(canvas, 'Which areas get a new blood supply?')
        footer(canvas, 'The team considers why surgery was recommended')
        return
    if progress < .63:
        access.rect(canvas, 0, 0, 1280, 720,
                    access.grad(0, 0, 1260, 710, ['#f4f9f3', '#e0eee7', '#b5d5c5']))
        title(canvas, 'The team explains the risks')
        canvas.save()
        canvas.translate(26, 22)
        monitor(canvas, seconds, x=669, y=190, width=483)
        access.line(canvas, [(910, 424), (910, 494), (795, 528), (1050, 528)],
                    '#466e60', 13)
        canvas.restore()
        if progress < .53:
            access.text(canvas, 'Bleeding or infection', 60, 330, 40, INK)
            access.text(canvas, 'Changes in heart rhythm', 60, 388, 34, MUTED)
        else:
            access.text(canvas, 'Kidney problems', 60, 330, 40, INK)
            access.text(canvas, 'Heart attack or stroke', 60, 388, 34, MUTED)
        footer(canvas, 'Risk varies with the person and the operation')
        return
    if progress < .90:
        graft_shot(canvas, seconds)
        if progress < .74:
            title(canvas, 'Bypass restores supply to selected arteries')
            footer(canvas, 'The new route reaches the artery beyond the narrowing')
        else:
            title(canvas, 'Coronary disease can still progress')
            footer(canvas, 'Grafts can also narrow or block over time')
        return
    title_document(canvas, 'Prevention and follow-up continue',
                   ('Medicines', 'Cardiac rehabilitation', 'Follow-up visits'),
                   seconds, (progress-.90)/.10)


def bedside(canvas, seconds, supported):
    access.rect(canvas, 0, 0, 1280, 720,
                access.grad(0, 0, 1200, 650, ['#f1f8f1', '#e8f5ef', '#a6c8bb']))
    access.rect(canvas, 0, 540, 1280, 180, access.solid('#bad2c7'))
    for x in range(0, 1280, 151):
        access.line(canvas, [(x, 540), (1.19*x-124, 720)], '#d6e8de', 2, 153)
    ellipse(canvas, 157, 591, 1005, 112, access.solid('#5c887a', 64))
    round_box(canvas, 117, 472, 803, 102, 32, '#315a50')
    round_box(canvas, 136, 451, 770, 79, 28, '#ebf4ee')
    access.line(canvas, [(206, 555), (209, 609), (778, 609), (810, 557)], '#607f72', 16)
    for x in (210, 778):
        angiogram.dot(canvas, x, 615, 16, '#2f594e')

    # The gown covers the neckline and shoulders. The opaque blanket covers
    # the torso, arms and lower body even where the support tubes are shown.
    canvas.save()
    canvas.rotate(25, 290, 386)
    round_box(canvas, 133, 335, 302, 121, 48, '#bcd9ca')
    round_box(canvas, 152, 344, 266, 99, 42, '#f6f9f3')
    canvas.restore()
    breath = (1+sin(seconds*2*pi*.32))/2
    head = skia.Path()
    head.moveTo(227, 316)
    head.cubicTo(253, 275, 313, 275, 345, 304)
    head.cubicTo(371, 330, 358, 368, 342, 383)
    head.cubicTo(318, 412, 272, 397, 248, 376)
    head.cubicTo(228, 363, 215, 337, 227, 316)
    head.close()
    canvas.drawPath(head, access.grad(216, 281, 358, 399, ['#e8c4a4', '#be987d', '#806657']))
    cap = skia.Path()
    cap.moveTo(219, 347)
    cap.cubicTo(214, 275, 308, 250, 342, 301)
    cap.cubicTo(311, 304, 270, 320, 240, 361)
    cap.close()
    canvas.drawPath(cap, access.grad(214, 258, 337, 350, ['#b8d6c9', '#618d82', '#416c60']))
    gown = [(325, 371), (372, 353), (421, 362), (480, 393), (503, 465), (373, 485)]
    canvas.drawPath(access.path(gown, True),
                    access.grad(347, 362, 487, 473, ['#afd1c3', '#6f9b8d', '#47756a']))
    blanket = skia.Path()
    blanket.moveTo(369, 402)
    blanket.cubicTo(401, 373-15*breath, 465, 375-15*breath, 495, 401)
    blanket.cubicTo(565, 429, 656, 428, 740, 421)
    blanket.cubicTo(846, 412, 904, 425, 910, 472)
    blanket.cubicTo(906, 511, 851, 526, 770, 528)
    blanket.lineTo(394, 520)
    blanket.cubicTo(359, 494, 345, 435, 369, 402)
    blanket.close()
    canvas.drawPath(blanket, access.grad(359, 371, 753, 542,
                                       ['#b4d8cb', '#87b4a4', '#4d8172']))
    access.line(canvas, [(392, 419-12*breath), (493, 446), (625, 467), (848, 468)],
                '#cce1d8', 4, 170)
    access.line(canvas, [(416, 465-9*breath), (520, 480), (720, 507)], '#639788', 5, 193)
    round_box(canvas, 742, 429, 25, 77, 12, '#e4f3e9')
    round_box(canvas, 801, 430, 24, 70, 12, '#e4f3e9')
    access.line(canvas, [(630, 535), (852, 535), (882, 471)], '#dcf0e3', 8)
    monitor(canvas, seconds)
    access.line(canvas, [(1025, 439), (1025, 556), (949, 588), (1115, 588)],
                '#537c6e', 13)
    if supported:
        round_box(canvas, 484, 208, 188, 135, 15, '#a8c9bd')
        round_box(canvas, 497, 216, 163, 94, 12, '#38675c')
        round_box(canvas, 510, 228, 137, 54, 9, '#203e38')
        access.line(canvas, [(525+i*3.5, 256+9*sin(i*.26-seconds*3)) for i in range(31)],
                    '#b7e7d6', 4)
        access.line(canvas, [(564, 336), (564, 461)], '#4a7669', 10)
        ellipse(canvas, 314, 325, 58, 53, access.solid('#cee8e8', 200))
        ellipse(canvas, 320, 333, 46, 35, access.solid('#e7f2ed', 210))
        tubing = [(354, 346), (395, 341), (439, 307), (477, 321), (522, 319)]
        access.line(canvas, tubing,
                    '#c1dfd8', 13)
        access.line(canvas, tubing, '#62978b', 3)
        access.line(canvas, [(574, 510), (574, 560), (625, 581), (625, 601)],
                    '#e7e0ce', 9)
        round_box(canvas, 598, 581, 55, 59, 10, '#f5f1e0')
        round_box(canvas, 605, 619, 41, 14, 5, '#c49579')


def covered_walker(canvas, x, floor, seconds, palette, step_offset=0):
    cycle = seconds*2*pi*.86+step_offset
    lift = 6*(1-cos(2*cycle))
    hip_y = floor-151-lift
    palette_dark, palette_light = palette
    ellipse(canvas, x-73, floor-13, 149, 22, access.solid('#5b887a', 76))
    for sign, shade in ((-1, palette_dark), (1, '#35594f')):
        foot_x = x+sign*62*sin(cycle)
        foot_y = floor-12-31*max(0, sign*cos(cycle))
        knee = (x+sign*35*sin(cycle)+18, (hip_y+foot_y)*.51)
        access.line(canvas, [(x+sign*17, hip_y-6), knee, (foot_x, foot_y)], shade, 33)
        access.line(canvas, [(foot_x-8, foot_y), (foot_x+20, foot_y+2)], '#1e3f37', 17)
    torso = [(x-46, hip_y-103), (x+35, hip_y-111), (x+59, hip_y-72),
             (x+48, hip_y+4), (x-48, hip_y+4), (x-54, hip_y-66)]
    canvas.drawPath(access.path(torso, True),
                    access.grad(x-54, hip_y-115, x+52, hip_y, [palette_light, palette_dark]))
    round_box(canvas, x-16, hip_y-128, 33, 26, 7, palette_dark)
    arm = sin(cycle)*48
    access.line(canvas, [(x-32, hip_y-84), (x+arm*.36, hip_y-46), (x+arm, hip_y-27)],
                palette_dark, 26)
    access.line(canvas, [(x+31, hip_y-89), (x+27-arm*.35, hip_y-48),
                         (x+15-arm*.61, hip_y-33)], palette_light, 19)
    ellipse(canvas, x-37, hip_y-193, 71, 84,
            access.grad(x-35, hip_y-186, x+30, hip_y-116, ['#e7c4a4', '#8e6c58']))
    ellipse(canvas, x-40, hip_y-202, 74, 54,
            access.grad(x-40, hip_y-201, x+30, hip_y-152, ['#bbd7c8', palette_dark]))


def mobility(canvas, seconds, progress, rehabilitation):
    access.rect(canvas, 0, 0, 1280, 720,
                access.grad(0, 200, 1280, 660, ['#f5f9f1', '#d7eae0', '#accbbc']))
    access.rect(canvas, 0, 486, 1280, 234, access.solid('#b4cfc3'))
    for x in range(46, 1280, 154):
        access.line(canvas, [(580+(x-580)*.53, 485), (x, 720)], '#d5e6dd', 2)
    for y in (529, 581, 642):
        access.line(canvas, [(0, y), (1280, y)], '#cadfd5', 2)
    round_box(canvas, 66, 173, 310, 235, 12, '#bfdcd0')
    round_box(canvas, 79, 186, 284, 209, 8, '#eaf5e9')
    access.line(canvas, [(218, 187), (218, 395)], '#bdd9ca', 7)
    access.line(canvas, [(80, 294), (360, 294)], '#bdd9ca', 7)
    if rehabilitation:
        for x in (471, 1089):
            access.line(canvas, [(x, 430), (x, 590)], '#577f70', 16)
        access.line(canvas, [(462, 430), (1100, 430)], '#76a094', 17)
    position = 460+340*progress
    covered_walker(canvas, position+164, 571, seconds, ('#3a7768', '#abd0bf'), .6)
    covered_walker(canvas, position, 597, seconds, ('#496966', '#9bbeb3'))


def title_document(canvas, heading, items, seconds, progress):
    access.rect(canvas, 0, 0, 1280, 720,
                access.grad(0, 0, 1280, 720, ['#f2f8f1', '#d0e5d8', '#9bc3b2']))
    title(canvas, heading)
    canvas.save()
    canvas.translate(646, 406)
    canvas.rotate(-8+13*progress)
    scale = .95+.11*progress
    canvas.scale(scale, scale)
    round_box(canvas, -278, -214, 580, 453, 31, '#6d9585')
    round_box(canvas, -294, -231, 580, 453, 31, '#28594d')
    round_box(canvas, -275, -208, 542, 401, 24, '#f6faf2')
    round_box(canvas, -94, -244, 169, 55, 17, '#8bb4a6')
    access.text(canvas, 'MY CARE PLAN', -220, -129, 32, INK)
    active = min(len(items)-1, int(progress*len(items)))
    for index, item in enumerate(items):
        y = -76+69*index
        if index == active:
            round_box(canvas, -235, y-30, 474, 59, 14, '#cce7d9')
            access.line(canvas, [(-180, y+18), (-180+385*((seconds*.68)%1), y+18)],
                        '#95c8b3', 5)
        access.text(canvas, item, -176, y+4, 30, MUTED)
        access.line(canvas, [(-219, y-4), (-209, y+7), (-195, y-12)],
                    EMERALD if index <= active else '#a4beb3', 5)
    canvas.restore()
    footer(canvas, 'Follow the plan your care team gives you')


def recovery(canvas, progress, seconds):
    if progress < .31:
        supported = progress >= .145
        bedside(canvas, seconds, supported)
        title(canvas, 'Monitoring after surgery')
        footer(canvas, 'Temporary breathing support and drains may be used'
               if supported else 'Staff monitor breathing, heart rhythm and blood pressure')
    elif progress < .45:
        mobility(canvas, seconds, (progress-.31)/.14, False)
        title(canvas, 'Getting moving with support')
        footer(canvas, 'Staff help you start moving when it is safe')
    elif progress < .73:
        title_document(canvas, 'Take home a written recovery plan',
                       ('Wound care', 'Medicines', 'Activity and driving', 'Follow-up'),
                       seconds, (progress-.45)/.28)
    elif progress < .87:
        mobility(canvas, seconds, (progress-.73)/.14, True)
        title(canvas, 'Cardiac rehabilitation')
        footer(canvas, 'Build activity with the support of your team')
    else:
        title_document(canvas, 'Review your medicines with the care team',
                       ('What to take', 'How to take it', 'Who to contact'),
                       seconds, (progress-.87)/.13)


def dressing(canvas, progress, seconds):
    access.rect(canvas, 0, 0, 1280, 720,
                access.grad(0, 0, 1270, 720, ['#f9f7ec', '#ecf3e9', '#cddfce']))
    canvas.save()
    canvas.translate(803, 371)
    canvas.rotate(-13+9*progress)
    round_box(canvas, -287, -166, 581, 333, 43, '#8bad9e')
    round_box(canvas, -302, -183, 581, 333, 43, '#bfdbcf')
    for i in range(-280, 267, 18):
        access.line(canvas, [(i, -154), (i, 121)], '#b4cfc2', 1.4)
    extent = 235+30*sin(seconds*2.7)
    ellipse(canvas, -extent*.5, -96, extent, 173, access.solid('#c4786a', 64))
    round_box(canvas, -168, -73, 337, 142, 32, '#f2e1c4')
    round_box(canvas, -98, -63, 195, 123, 19, '#f8eee1')
    for i in range(-75, 94, 17):
        access.line(canvas, [(i, -57), (i, 52)], '#f2e2d3', 1.7)
    if progress>.45:
        ellipse(canvas, -36, -24, 37+39*progress, 42,
                access.solid('#a6755c', 69))
    canvas.restore()
    title(canvas, 'When to call after surgery')
    access.text(canvas, 'Wound changes', 57, 323, 43, INK)
    access.text(canvas, 'or fever', 57, 381, 43, INK)
    footer(canvas, 'Contact your care team promptly',
           'Increasing pain, redness, drainage or fever')


def symptom_figure(canvas, seconds, symptom, stroke_phase):
    # The anonymous figure is fully clothed. Only the face is visible so the
    # asymmetric mouth in the FAST example can be shown clearly.
    x, y = 938, 360
    body = skia.Path()
    body.moveTo(x-154, y+195)
    body.cubicTo(x-151, y+71, x-106, y+37, x-37, y+21)
    body.lineTo(x+30, y+21)
    body.cubicTo(x+102, y+37, x+147, y+78, x+160, y+195)
    body.close()
    canvas.drawPath(body, access.grad(x-150, y+28, x+134, y+200,
                                     ['#a2c1b4', '#5f867a', '#355a50']))
    round_box(canvas, x-49, y+18, 95, 50, 21, '#476d62')
    ellipse(canvas, x-64, y-127, 129, 164,
            access.grad(x-65, y-108, x+61, y+35, ['#e9c8a9', '#ba977b', '#977362']))
    ellipse(canvas, x-69, y-146, 137, 90,
            access.grad(x-65, y-147, x+55, y-55, ['#a8c9ba', '#6a9283', '#496f64']))
    for side in (-1, 1):
        angiogram.dot(canvas, x+side*22, y-26, 4, '#705b4b')
    droop = 17 if symptom == 'stroke' and stroke_phase == 0 else 0
    access.line(canvas, [(x-21, y+3), (x-6, y+8), (x+17, y+3+droop)], '#83544f', 5)
    phase = (1-cos(seconds*2*pi*.63))/2
    if symptom == 'chest':
        # A broad chest region conveys diffuse pressure. No point is used
        # as a diagnostic location or a simulation of the pulse.
        for shift in (0, .44):
            scale = .75+.43*((seconds*.50+shift)%1)
            w, h = 214*scale, 122*scale
            ellipse(canvas, x-w/2, y+116-h/2, w, h,
                    access.solid('#e2917b', round(65+110*(1.17-scale))))
        ellipse(canvas, x-48, y+88, 96, 56, access.solid('#f1bd91', 152))
        return
    if stroke_phase == 0:
        outline = [(x-31, y-10), (x-23, y+14), (x+8, y+22), (x+32, y+14)]
        access.line(canvas, outline, '#8d4543', 5+3*phase)
    elif stroke_phase == 1:
        access.line(canvas, [(x-118, y+82), (x-170, y+49-13*phase),
                             (x-211, y+19-28*phase)], '#7ca496', 34)
        access.line(canvas, [(x+116, y+80), (x+153, y+111), (x+186, y+128)],
                    '#61877b', 34)
    else:
        access.line(canvas, [(x+34, y-1), (x+103, y-30), (x+132, y-30)], '#9c5449', 5)
        for i in range(3):
            angiogram.dot(canvas, x+118+24*i, y-74, 7+4*sin(seconds*5-i), '#af624f')


def emergency_signs(canvas, seconds, symptom, stroke_phase=0, shot_progress=0):
    access.rect(canvas, 0, 0, 1280, 720,
                access.grad(0, 0, 1280, 720, ['#f4f1e7', '#e6eee6', '#c5dccc']))
    title(canvas, 'When to get emergency help')
    canvas.save()
    focus_y = 318 if symptom == 'stroke' and stroke_phase == 0 else 402
    canvas.translate(940, focus_y)
    zoom = 1.0+.39*shot_progress
    canvas.scale(zoom, zoom)
    canvas.translate(-940, -focus_y)
    symptom_figure(canvas, seconds, symptom, stroke_phase)
    canvas.restore()
    if symptom == 'chest':
        access.text(canvas, 'Sudden chest pressure', 56, 317, 42, INK)
        access.text(canvas, 'that does not go away', 56, 374, 40, INK)
    else:
        access.text(canvas, 'Possible stroke', 56, 287, 45, INK)
        signs = ('Face droop', 'Arm weakness', 'Trouble speaking')
        for index, sign in enumerate(signs):
            y = 343+54*index
            angiogram.dot(canvas, 65, y-11, 8 if stroke_phase==index else 5, EMERGENCY)
            access.text(canvas, sign, 89, y, 34, EMERGENCY if stroke_phase==index else MUTED)
    footer(canvas, 'Call your local emergency number',
           'Act immediately if you suspect a heart attack or stroke', urgent=True)


def warning_signs(canvas, progress, seconds):
    if progress < .30:
        dressing(canvas, progress/.30, seconds)
    elif progress < .52:
        emergency_signs(canvas, seconds, 'chest', shot_progress=(progress-.30)/.22)
    elif progress < .77:
        position = 3*(progress-.52)/.25
        phase = min(2, int(position))
        emergency_signs(canvas, seconds, 'stroke', phase, position-phase)
    else:
        title_document(canvas, 'Keep these details with your home plan',
                       ('Who to call', 'Next appointment'), seconds, (progress-.77)/.23)


def closing(canvas, progress, seconds):
    remaining = seconds*(1-progress)/progress if progress else float('inf')
    if remaining > 8.0:
        graft_shot(canvas, seconds)
        title(canvas, 'A new route for blood')
        footer(canvas, 'The best option depends on the person and the findings')
        return
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#173c35'))
    angiogram.header(canvas, 'Clinical sources', TOPIC, True)
    sources = (
        'ACC, AHA and SCAI · Coronary revascularization',
        'ACC and AHA · Acute coronary syndromes',
        'American Heart Association · Prevention after bypass',
        'NHLBI and NHS · Bypass surgery and recovery',
    )
    for index, source in enumerate(sources):
        access.text(canvas, source, 56, 227+59*index, 32, '#e6f3e8')
    access.line(canvas, [(56, 475), (1204, 475)], '#628e7c', 2)
    access.text(canvas, 'Cardiac Surgery Education Series', 55, 528, 36, '#edf7ee')
    access.text(canvas, 'Original educational animation · Synthetic English narration',
                56, 582, 30, '#c5e3d5')
    access.text(canvas, 'Full clinical links in the description', 56, 643, 29, '#c5e3d5')


def draw(canvas, ident, progress, seconds):
    scenes = {'P09': result, 'P10': recovery, 'P11': warning_signs, 'P12': closing}
    scenes[ident](canvas, progress, seconds)
