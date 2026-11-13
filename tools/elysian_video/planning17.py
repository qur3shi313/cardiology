"""Episode 17: cue-aligned planning images for the Heart Team's TAVI assessment."""

from functools import lru_cache
from math import cos, pi, sin

import skia

from . import access, angiogram, structural, valve_implant as valve


TOPIC = 'TAVI PLANNING'
SCENES = ('P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07')
CREAM, GREEN, WHITE = '#e8f2e9', '#214c43', '#edf8ed'
FILTER = skia.SamplingOptions(skia.FilterMode.kLinear)


def scale_label(canvas, value, x, y, size, width, color=GREEN):
    measured = skia.Font(access.BOLD, size).measureText(value)
    access.text(canvas, value, x, y, min(size, int(size * width / measured)), color)


def panel(canvas, title, lead, lines):
    access.rect(canvas, 0, 0, 1280, 720, access.solid(CREAM))
    angiogram.header(canvas, title, TOPIC)
    scale_label(canvas, lead, 55, 302, 43, 440)
    for index, line in enumerate(lines):
        access.text(canvas, line, 56, 365 + index * 43, 31, GREEN, access.REGULAR)
    angiogram.block(canvas, 514, 179, 711, 454, 28, access.solid('#22473f'))


def ring(canvas, x, y, radius, phase):
    """Oblique annular plane. Calcified leaflets lie inside the plane's border."""
    for fraction, shade in ((1.16, '#4c7169'), (1.02, '#92afa1'), (.88, '#2b4f49')):
        width = radius * 2 * fraction
        height = width * .69
        canvas.drawOval(skia.Rect.MakeXYWH(x-width/2, y-height/2, width, height), access.solid(shade))
    for side in (-1, 1):
        cusp = angiogram.art.curve((x+side*.76*radius, y+8),
                ((x+side*.55*radius, y+48), (x+side*.16*radius, y+45), (x+side*.06*radius, y+7)))
        access.line(canvas, cusp, '#bdc6a5', 6.5)
    for i in range(4):
        angiogram.dot(canvas, x + radius * (.31 + i*.09), y+17+i*4, 7+i%2, '#e4c393')
    canvas.save()
    clip = skia.Path()
    clip.addOval(skia.Rect.MakeXYWH(x-radius, y-.69*radius, radius*2, 1.38*radius))
    canvas.clipPath(clip, doAntiAlias=True)
    level = y-.76*radius+((phase*1.11)%1)*1.52*radius
    light = access.grad(x, level-22, x, level+28, ['#8db9ab','#f7e6b8','#8db9ab'])
    light.setAlpha(113)
    access.rect(canvas, x-radius, level-22, 2*radius, 50, light)
    canvas.restore()


def opening(canvas, time):
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#163b35'))
    if time < 3.4:
        ring(canvas, 647, 398, 212 + time*10, time*.54)
        access.text(canvas, 'How will a new valve fit?', 57, 660, 45, WHITE, access.HEADING)
        return
    if time < 8.54:
        canvas.drawImageRect(valve.base(), skia.Rect.MakeWH(1280,720), FILTER)
        valve.leaflets(canvas, time, 'stenosis')
        angiogram.header(canvas, 'How the Heart Team plans TAVI', TOPIC)
        access.rect(canvas, 0, 655, 1280, 65, access.solid('#173b35'))
        access.text(canvas, 'The aortic root and the arteries form the planning map', 58, 695, 31, WHITE)
        return
    canvas.drawImageRect(valve.route_plate(planning=True), skia.Rect.MakeWH(1280,720), FILTER)
    access.rect(canvas, 0, 0, 1280, 147, access.solid(CREAM))
    angiogram.header(canvas, 'How the Heart Team plans TAVI', TOPIC)
    access.line(canvas, angiogram.art.trace(valve.ROUTE, access.smooth((time-8.54)/3.25)), '#fde4ad', 13)


def echo_panel(canvas, time, chamber):
    x, y = 232, 213
    angiogram.block(canvas, 60, 172, 344, 370, 23, access.solid('#173934'))
    access.text(canvas, 'Illustrated ultrasound', 80, 213, 29, WHITE)
    cone = angiogram.art.curve((84,447), ((127,523),(324,527),(380,447)))
    canvas.drawPath(access.path([(x,247), *cone], True), access.grad(155,258,277,502,['#254943','#77988a','#375851']))
    beat = (1-cos(time*2*pi*1.08))/2
    for side in (-1, 1):
        edge = [(x+side*(68+15*beat),374),(x+side*(45+11*beat),429),(x+side*24,456)]
        access.line(canvas, edge, '#bed5c6', 5, 200)
        cusp = angiogram.art.curve((x+side*57,365), ((x+side*40,366),(x+side*20,362),(x+side*(5+16*beat),352)))
        access.line(canvas, cusp, '#e7f0d6', 5.4)
    if beat>.35:
        for index in range(5):
            yy = 411 - (index*21+time*119)%123
            xx = x + (index-2)*7
            access.line(canvas, [(xx,yy+4),(xx,yy-5)], '#e9c590', 4.5, 210)
    if chamber:
        access.line(canvas, [(277,424),(346,458)], '#f0d5a5', 2.2)
        angiogram.dot(canvas, 276, 424, 7, '#f1d8a6')
    access.text(canvas, 'Pumping chamber' if chamber else 'Valve opening and flow', 80, 513, 24, WHITE)


def assess_echo(canvas, time):
    canvas.drawImageRect(valve.base(), skia.Rect.MakeWH(1280,720), FILTER)
    beat = valve.leaflets(canvas, time, 'stenosis')
    valve.pump_flow(canvas, time, beat, False)
    if time >= 4.57:
        echo_panel(canvas, time, time >= 9.91)
    else:
        angiogram.block(canvas, 55, 285, 328, 110, 19, access.solid('#244d42'))
        access.text(canvas, 'Review symptoms', 74, 331, 34, WHITE)
        access.text(canvas, 'and valve narrowing', 75, 370, 29, WHITE)
    angiogram.header(canvas, 'Checking the narrowed aortic valve', TOPIC)
    access.rect(canvas, 0, 655, 1280, 65, access.solid('#173b35'))
    if time >= 13.94:
        label = 'These findings help the team decide whether to consider replacement'
    elif time >= 9.91:
        label = 'Echo also helps assess the left ventricle'
    elif time < 4.57:
        label = 'The team first reviews symptoms and how severe the narrowing is'
    else:
        label = 'Echo helps assess how the narrowed valve opens and blood moves'
    access.text(canvas, label, 56, 695, 31, WHITE)


def scan_label(canvas, label, position, elbow, endpoint):
    access.line(canvas, [position, elbow, endpoint], '#dbeed9', 2.5)
    angiogram.dot(canvas, *endpoint, 6, '#f4dca8')
    access.text(canvas, label, position[0], position[1]-14, 29, WHITE)


def root_scan(canvas, time):
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#153934'))
    angiogram.header(canvas, 'Where a new valve would sit', 'ILLUSTRATED CT VIEW', True)
    if time < 9.29 or time >= 17.16:
        x, y = 695, 383
        ring(canvas, x, y, 209, time*.65)
        if time >= 4.98:
            span = 184*access.smooth((time-4.98)/1.5)
            access.line(canvas, [(x-span,y),(x+span,y)], '#f2eed5', 4)
            for sign in (-1, 1):
                access.line(canvas, [(x+sign*span,y-17),(x+sign*span,y+17)], '#f2eed5', 4)
            scan_label(canvas, 'Valve ring', (137,501), (405,501), (x-164,y+80))
        footer = ('Measurements help the team assess fit' if time >= 17.16
                  else 'A CT reformat can show the aortic root and valve ring')
    else:
        left = [(535,184),(530,260),(487,312),(489,361),(526,418),(565,460),(509,567)]
        right = [(1420-x,y) for x,y in left]
        canvas.drawPath(access.path(left + right[::-1], True), access.grad(519,184,926,565,['#557e75','#365d56','#254641']))
        for wall in (left,right):
            access.line(canvas, wall, '#a2b9a7', 20)
            access.line(canvas, wall, '#78988a', 11)
        for sign in (-1, 1):
            ostium = (710 + sign*215, 325)
            branch = angiogram.art.curve(ostium, ((710+sign*265,316),(710+sign*337,332),(710+sign*405,293)))
            access.line(canvas, branch, '#7a9a8d', 15)
            angiogram.dot(canvas, *ostium, 11, '#edd9aa')
            cusp = angiogram.art.curve((710+sign*141,456), ((710+sign*103,447),(710+sign*46,460),(710+sign*25,411)))
            access.line(canvas, cusp, '#c5ceb5', 8)
        # These openings are above the annulus in this conceptual longitudinal view.
        access.line(canvas, [(567,461),(853,461)], '#d9e6cb', 4)
        scan_label(canvas, 'Valve ring', (113,531), (411,531), (565,461))
        scan_label(canvas, 'Coronary openings', (84,284), (364,284), (495,325))
        if time >= 13.66:
            for index in range(4):
                angiogram.dot(canvas, 777+index*17, 434+5*sin(index), 8, '#edc691')
            scan_label(canvas, 'Calcium', (952,512), (908,512), (794,438))
        y = 201+(time*81)%337
        light = access.grad(525,y,525,y+47,['#517a6d','#c2d9bd','#517a6d'])
        light.setAlpha(80)
        canvas.save()
        canvas.clipPath(access.path(left+right[::-1],True),doAntiAlias=True)
        access.rect(canvas, 480, y, 465, 47, light)
        canvas.restore()
        footer = 'Calcium distribution' if time >= 13.66 else 'Coronary openings sit above the valve ring'
    access.text(canvas, footer, 55, 673, 32, WHITE)


def pathway(canvas, time):
    structural.delivery_route_plan(canvas, time)
    # A moving CT scan plane highlights the map without suggesting that a device moves through it.
    level = 167 + (time*104)%432
    canvas.save()
    canvas.clipPath(access.path([(424,187),(505,155),(666,155),(751,181),(855,284),(817,390),
        (847,530),(819,650),(658,680),(579,614),(507,680),(347,650),(320,531),(364,390),(321,285)],True),
        doAntiAlias=True)
    wash = access.grad(560,level-48,560,level+48,['#5f9383','#dce4bc','#5f9383'])
    wash.setAlpha(152)
    access.rect(canvas,318,level-48,539,96,wash)
    canvas.restore()
    progress = access.smooth((time-.3)/8.5)
    emphasis = int(157 + 91*sin(time*2.8))
    access.line(canvas, angiogram.art.trace(valve.ROUTE, progress), '#fff0b6', 15, emphasis)
    if time >= 9.54:
        x = 943+(time*86)%217
        wash = access.grad(x-23, 443, x+23, 443, ['#52796b','#d1e2bd','#52796b'])
        wash.setAlpha(110)
        access.rect(canvas,x-23,405,46,36,wash)
        access.rect(canvas,x-23,508,46,35,wash)
    else:
        access.line(canvas,[(912,334),(965,334)],'#a97e44',8)
        access.text(canvas,'Potential route',979,343,27,GREEN)
    access.rect(canvas, 0, 653, 1280, 67, access.solid('#dcece2'))
    if time >= 14.11:
        footer = 'If this route is unsuitable, the team discusses other options'
    elif time >= 9.54:
        footer = 'The team checks artery size, bends and calcium'
    elif time >= 5.04:
        footer = 'The groin is the most common access route'
    else:
        footer = 'CT can map a potential arterial route'
    access.text(canvas, footer, 55, 693, 31, GREEN)


def person(canvas, x, y, color, size=1, hand=0):
    canvas.save()
    canvas.translate(x,y)
    canvas.scale(size,size)
    angiogram.dot(canvas,0,-42,32,'#c5aa8d')
    canvas.drawPath(access.path([(-34,4),(-73,28),(-85,109),(87,109),(70,25),(35,4)],True),
                    access.grad(-70,18,60,114,[color,'#406d61']))
    access.line(canvas,[(42,25),(69,75),(114,79+hand)],'#a6c4ad',15)
    angiogram.dot(canvas,113,79+hand,9,'#d3b693')
    canvas.restore()


def ecg(canvas,time):
    angiogram.block(canvas, 557, 242, 448, 281, 18, access.solid('#14342f'))
    for i in range(8):
        x=581+55*i
        access.line(canvas,[(x,262),(x,500)],'#70a78f',1,78)
    for i in range(5):
        y=270+52*i
        access.line(canvas,[(578,y),(985,y)],'#70a78f',1,78)
    pattern=[(0,0),(15,0),(23,-12),(33,0),(50,0),(59,16),(64,-70),(72,31),(79,0),(94,0),(105,-20),(126,0)]
    canvas.save()
    canvas.clipRect(skia.Rect.MakeXYWH(581,271,398,224))
    offset=(time*140)%142
    points=[(581+142*i+x-offset,393+y) for i in range(5) for x,y in pattern]
    access.line(canvas, points, '#c6f1cd', 4.6)
    canvas.restore()
    for index in range(2):
        canvas.save()
        canvas.translate(1036+index*47,371+index*30)
        canvas.rotate(-22+sin(time*1.24+index)*13)
        angiogram.block(canvas, -13,-67,34,146,16,access.solid('#dfecde'))
        angiogram.block(canvas, -13,-72,34,26,7,access.solid('#a8788c'))
        angiogram.block(canvas, -8,7,24,61,9,access.solid('#ac666d'))
        canvas.restore()
    access.text(canvas, 'Illustrated ECG', 579, 557, 31, WHITE)


def tile(canvas, x, y, text, index, time):
    travel = 25*sin(time*1.18+.85*index)
    y += travel
    angiogram.block(canvas,x+8,y+11,289,86,19,access.solid('#416e5f'))
    angiogram.block(canvas,x,y,289,86,18,access.solid('#e4efdf'))
    scale_label(canvas,text,x+19,y+53,34,248)


def health_checks(canvas,time):
    if time < 7.37:
        panel(canvas, 'The assessment goes beyond the valve', 'Other checks may help',
              ('Blood tests and an ECG', 'The coronary arteries may', 'also be assessed'))
        ecg(canvas,time)
    elif time < 13.8:
        panel(canvas, 'The assessment goes beyond the valve', 'Overall health and goals',
              ('Other conditions and function', 'What the patient wants', 'from treatment'))
        person(canvas,703,387,'#a0bfad',1.14,22*sin(time*1.8))
        tile(canvas,871,312,'Daily function',0,time)
        tile(canvas,871,431,'Patient goals',1,time)
    else:
        panel(canvas, 'The assessment goes beyond the valve', 'Benefits and risks',
              ('The team weighs both', 'for the available options'))
        angle = 8*sin(time*1.08)
        access.line(canvas,[(866,545),(866,373)],'#c4dfc6',15)
        access.line(canvas,[(806,552),(925,552)],'#c4dfc6',16)
        canvas.save()
        canvas.rotate(angle,866,372)
        access.line(canvas,[(653,373),(1082,373)],'#c4dfc6',13)
        for x,word in ((659,'Benefits'),(1075,'Risks')):
            access.line(canvas,[(x,373),(x,448)],'#c4dfc6',4)
            angiogram.block(canvas,x-77,445,154,54,13,access.solid('#d7e9d3'))
            scale_label(canvas,word,x-64,480,27,124)
        canvas.restore()


def team(canvas,time):
    if time < 9.85:
        panel(canvas, 'How the Heart Team recommends a plan', 'Specialists review together',
              ('Imaging, catheter treatment', 'and surgery inform the plan'))
        for index,x in enumerate((663,862,1064)):
            person(canvas,x,369,'#91b8a2',.82,22*sin(time*1.8+index*1.1))
        angiogram.block(canvas,573,462,590,92,20,access.solid('#82a894'))
        canvas.drawOval(skia.Rect.MakeXYWH(788,467,151,78),access.solid('#d9e9d9'))
        ring(canvas,862,506,49,time*1.1)
    elif time < 15.78:
        panel(canvas, 'How the Heart Team recommends a plan', 'Next steps can differ',
              ('Further testing or', 'a surgical opinion may help'))
        tile(canvas,562,315,'Further testing',0,time)
        tile(canvas,896,430,'Surgical opinion',1,time)
    else:
        panel(canvas, 'How the Heart Team recommends a plan', 'The recommendation',
              ('Valve anatomy and wider', 'health both matter'))
        ring(canvas,697,401,98,time*.7)
        tile(canvas,868,355,'Overall health',0,time)


def discussion(canvas,time):
    if time < 10.96:
        panel(canvas,'Preparing for the discussion','Questions to ask',
              ('Why this option?', 'What are the risks?', 'What could recovery involve?'))
        person(canvas,702,374,'#90b3a0',1.,24*sin(time*1.6))
        person(canvas,1004,366,'#a5beab',.93,24*cos(time*1.52))
        angiogram.block(canvas,577,477,592,63,18,access.solid('#88ae98'))
        tile(canvas,712,235,'Your next steps',0,time)
    else:
        valve.clinical(canvas,'P02',0.,time)
        access.rect(canvas,0,0,1280,154,access.solid(CREAM))
        angiogram.header(canvas,'Next episode: how TAVI is performed',TOPIC)
        access.rect(canvas,0,652,1280,68,access.solid('#173b35'))
        access.text(canvas,'A planned example follows a new valve to this position',55,694,33,WHITE)


DRAW = {'P01':opening,'P02':assess_echo,'P03':root_scan,'P04':pathway,
        'P05':health_checks,'P06':team,'P07':discussion}


def draw(canvas, ident, time):
    DRAW[ident](canvas,time)
