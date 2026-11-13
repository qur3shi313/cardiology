"""Cue-aligned motion for Episode 15's multivessel decision film."""

from math import pi, sin

import skia

from . import access, angiogram, pressure, restenosis, stent
from .emergency14 import care


TOPIC = 'MULTIVESSEL DISEASE'


def document(c, title, heading, details, page, progress):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e5f2e8'))
    angiogram.block(c, 540, 174, 694, 466, 26, access.solid('#285e53'))
    c.save()
    c.translate(887, 407)
    c.rotate(-3.+6.*progress)
    scale = .75+.105*progress
    c.scale(scale, scale)
    sampling = skia.SamplingOptions(skia.FilterMode.kLinear)
    c.drawImage(care.document_art(*page), -320, -243, sampling)
    c.restore()
    angiogram.header(c, title, TOPIC)
    font = skia.Font(access.BOLD, 38)
    heading_size = min(38, int(38*465/font.measureText(heading)))
    access.text(c, heading, 55, 321, heading_size, '#164c3f')
    for index, line in enumerate(details):
        access.text(c, line, 55, 376+44*index, 31, '#2b5a4e', access.REGULAR)
    access.text(c, 'Follow your own care team’s advice', 55, 674, 29, '#276353')


def timing(c, t):
    title = 'Stable and emergency care differ'
    if t < 5.6:
        document(c, title, 'Suspected heart attack',
                 ('The team assesses the', 'emergency first'),
                 ('Emergency care', ('Symptoms', 'Urgent tests', 'Immediate plan')), t/5.6)
    elif t < 10.9:
        document(c, title, 'Which artery caused it?',
                 ('That artery is often', 'the first priority'),
                 ('Urgent decisions', ('Culprit artery', 'Other narrowings', 'When to treat')), (t-5.6)/5.3)
    elif t < 15.9:
        document(c, title, 'Stable coronary disease',
                 ('There is usually time', 'to review the options'),
                 ('Stable disease', ('Symptoms', 'Test results', 'Medical history')), (t-10.9)/5.)
    else:
        document(c, title, 'Discuss the options',
                 ('The findings help the', 'team and patient plan'),
                 ('Care discussion', ('What the tests show', 'Treatment choices', 'Patient goals')), (t-15.9)/5.2)


def testing(c, t):
    if t < 6.75:
        access.rect(c, 0, 0, 1280, 720, access.solid('#152d2b'))
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, 151, 1280, 720))
        c.translate(640, 150)
        scale = 1.+.075*t/6.75
        c.scale(scale, scale)
        c.translate(-640, -150)
        c.drawImageRect(angiogram.radiograph_plate(), skia.Rect.MakeWH(1280,720),
                        skia.SamplingOptions(skia.FilterMode.kLinear))
        fill = access.smooth(t/3.2)
        x, y = angiogram.contrast_paths(c, 'left', fill, 246, -24+15*t/6.75, True)
        if t > 2.7:
            access.line(c, [(x, y), (x+66, y-63), (x+184, y-63)], '#fff3c6', 4)
            access.text(c, 'Narrowing', x+72, y-76, 33, '#fff5ce')
        c.restore()
        angiogram.header(c, 'What the angiogram shows', 'SIMULATED X-RAY', True)
    elif t < 9.85:
        access.rect(c, 0, 0, 1280, 720, access.solid('#e6f0e8'))
        beat = sin((t-6.75)*2*pi*.87)
        access.text(c, 'One factor in deciding the treatment plan', 55, 668, 31, '#265c51')
        c.save()
        c.translate(650, 406)
        c.scale(1.+.045*beat, 1.+.062*beat)
        shell = [(1, -196), (-144, -176), (-207, -112), (-203, -17), (-151, 79),
                 (-29, 199), (65, 178), (152, 102), (198, -11), (180, -121), (92, -178)]
        c.drawPath(access.path(shell, True),
                   access.grad(-180, -160, 170, 165, ['#d7968c', '#a76472', '#653a4d']))
        chamber = [(45,-133),(114,-109),(137,-62),(128,-2),(87,77),(20,131),
                   (-47,66),(-82,-2),(-74,-64),(-25,-104)]
        c.drawPath(access.path(chamber, True), access.solid('#6e394b'))
        c.restore()
        angiogram.header(c, 'How well the heart pumps', TOPIC)
        access.line(c, [(765, 433), (881, 377), (1090, 377)], '#276453', 3)
        access.text(c, 'Pumping chamber', 890, 361, 32, '#23564b')
        access.text(c, 'Illustrated cross-section', 879, 416, 27, '#3f6359')
    else:
        local = t-9.85
        pressure.diagram(c, 'P03', min(1., local/7.75), local)
        if local > 3.1:
            # Follow the downstream pressure trace after the sensor crosses.
            x = 826 + 345*((local*.38) % 1)
            access.line(c, [(x, 603), (x, 677)], '#d8f9e6', 4, 207)


def prevention(c, t):
    title = 'Medicines and prevention'
    if t < 5.12:
        document(c, title, 'A foundation of care',
                 ('Medicines and prevention', 'continue across options'),
                 ('Coronary care', ('Prevention plan', 'Medicines', 'Follow-up')), t/5.12)
    elif t < 12.65:
        document(c, title, 'Symptoms and future risk',
                 ('Stable disease care can', 'address both goals'),
                 ('Treatment goals', ('Symptom control', 'Heart risk', 'Daily activities')), (t-5.12)/7.53)
    elif t < 17.95:
        document(c, title, 'When symptoms persist',
                 ('The team may discuss', 'restoring blood flow'),
                 ('Symptoms', ('What has changed', 'Effects on daily life', 'Current treatment')), (t-12.65)/5.3)
    else:
        document(c, title, 'What the tests add',
                 ('Findings can change', 'the expected benefit'),
                 ('Review together', ('Test findings', 'Potential benefit', 'Treatment risks')), (t-17.95)/3.75)


def stenting(c, t):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e6f0e9'))
    expansion = access.smooth((t-.45)/5.15)
    deflation = access.smooth((t-7.9)/1.85)
    removal = access.smooth((t-10.2)/6.4)
    wire_removal = access.smooth((t-18.55)/2.10)
    delivery_x = stent.LESION-(stent.LESION+280)*removal
    balloon_radius = 12+104*expansion*(1-deflation)
    stent_radius = 14+102*expansion
    lumen_open = .36+.64*expansion
    flow = 1.-.93*expansion*(1-deflation)
    c.save()
    c.translate(640, 397)
    zoom = 1+.035*sin(pi*t/21.6)
    c.scale(zoom, zoom)
    c.translate(-640, -397)
    lumen = stent.artery(c, lumen_open)
    c.save()
    if flow < .55:
        c.clipRect(skia.Rect.MakeLTRB(0, 0, stent.LESION-52, 720))
    restenosis.trace_channel(c, t, lumen, lumen_open, max(.56, flow))
    c.restore()
    stent.stent(c, stent.LESION, stent_radius, False)
    if wire_removal < 1.:
        tip = 1126-(1126+90)*wire_removal
        stent.wire(c, tip)
    if delivery_x+stent.BALLOON_HALF > stent.X0:
        stent.balloon(c, delivery_x, balloon_radius)
    stent.stent(c, stent.LESION, stent_radius, True)
    c.restore()
    angiogram.header(c, 'Angioplasty and stenting (PCI)', TOPIC)
    if t < 7.9:
        detail = 'The balloon expands the stent at the selected narrowing'
    elif t < 10.2:
        detail = 'The balloon deflates while the mesh supports the artery'
    else:
        detail = 'The delivery devices come out and the stent stays in place'
    access.text(c, detail, 55, 675, 30, '#23554a')


def bypass(c, t):
    access.rect(c, 0, 0, 1280, 720, access.solid('#e7f0e8'))
    model = angiogram.art
    scale = 1. + .065*min(1., t/8.) + .038*sin(2*pi*t*.86)

    def xy(point):
        return 500+(point[0]-289)*1.60*scale, 214+(point[1]-110)*.90*scale

    heart = list(map(xy, model.MYOCARDIUM))
    c.drawPath(access.path(heart, True), access.grad(170, 214, 810, 626,
                                                    ['#d58f86', '#a35c70', '#643d50']))
    aorta = list(map(xy, model.AORTA))
    access.line(c, aorta, '#93536a', 34)
    access.line(c, aorta, '#e0a19a', 24)
    for vessel in (model.RCA, model.LEFT_MAIN, model.LCX):
        access.line(c, list(map(xy, vessel)), '#784151', 10)
    lad = list(map(xy, model.LAD))
    access.line(c, lad, '#783c4d', 15)
    access.line(c, lad, '#e49b89', 9)
    narrowed = lad[int((len(lad)-1)*.42)]
    target = lad[int((len(lad)-1)*.73)]
    angiogram.dot(c, *narrowed, 10, '#f0bc80')
    origin = aorta[int((len(aorta)-1)*.18)]
    graft = model.curve(origin, ((origin[0]+211, origin[1]-71),
                                 (target[0]+263, target[1]-65), target))
    length = access.smooth((t-1.9)/6.35)
    progress = model.trace(graft, length)
    access.line(c, progress, '#23594f', 29)
    access.line(c, progress, '#75b49e', 20)
    if t > 8.25:
        for index in range(7):
            phase = ((t-8.25)*.65 + index/7) % 1
            travel = model.trace(graft, phase)
            trail = travel[-max(2, len(graft)//9):]
            opacity = round(216*min(1., phase*15, (1-phase)*15))
            access.line(c, trail, '#d4f6d0', 12, opacity)
        x, y = target
        access.line(c, [(x, y), (x+113, y+34), (828, y+34)], '#326a5c', 3)
        access.text(c, 'Beyond the narrowing', 838, y+45, 31, '#214f44')
    if t < 8.25:
        x, y = narrowed
        access.line(c, [(x, y), (x+129, y-44), (828, y-44)], '#315b4f', 3)
        access.text(c, 'Existing narrowing', 838, y-32, 31, '#214f44')
    else:
        access.text(c, 'Blood takes a new route', 838, 283, 34, '#214f44')
        access.text(c, 'through the graft', 838, 328, 31, '#315f53')
    angiogram.header(c, 'Coronary bypass creates another route', TOPIC)
    access.text(c, 'Illustrated graft · The care team considers each patient’s situation',
                55, 676, 29, '#24564b')


def decision(c, t):
    title = 'The Heart Team and the patient'
    if t < 4.94:
        document(c, title, 'When the choice is unclear',
                 ('The Heart Team can', 'review the options'),
                 ('Heart Team review', ('Test results', 'Overall health', 'Options')), t/4.94)
    elif t < 9.56:
        document(c, title, 'Specialists work together',
                 ('Different specialists bring', 'different perspectives'),
                 ('Specialist input', ('Cardiology', 'Interventional cardiology', 'Cardiac surgery')), (t-4.94)/4.62)
    elif t < 16.55:
        document(c, title, 'The patient helps decide',
                 ('Discuss what matters', 'in daily life'),
                 ('Shared decision', ('Potential benefits', 'Risks and recovery', 'Patient priorities')), (t-9.56)/6.99)
    else:
        document(c, title, 'A plan the patient understands',
                 ('Connect the test results', 'with the next steps'),
                 ('Treatment plan', ('What the tests mean', 'The chosen approach', 'Next steps')), (t-16.55)/5.184)


SCENES = {
    'P02': timing, 'P03': testing, 'P04': prevention, 'P05': stenting,
    'P06': bypass, 'P07': decision,
}


def draw(canvas, ident, progress, elapsed):
    SCENES[ident](canvas, elapsed)
