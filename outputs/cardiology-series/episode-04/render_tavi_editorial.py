"""Render the TAVI assessment, recovery, emergency and sources scenes."""
from __future__ import annotations

from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
from random import Random
import json
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "visuals"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "episode-01/revision"))
from render_editorial_cards import DEEP, INK, LINE, MUTED, ROOT, font, gradient, write
from vascular_art import curve


W, H = 1920, 1080
PANEL = (70, 290, 1850, 928)
FFMPEG = ROOT / "work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
LOGO = ROOT / "work/company-logo-original-686.jpg"
SCENES = {scene["id"]: scene for scene in json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))}
PALE = "#f8fcf8"
MINT = "#e2f1e7"
JADE = "#447f70"
SKIN = "#e4b39e"
SKIN_LINE = "#b58377"
CORAL = "#ae6268"
GOLD = "#eed8a3"
WARN = "#813a43"


def ease(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def crossfade(first, second, p):
    if p <= 0:
        return first
    if p >= 1:
        return second
    return Image.blend(first, second, p)


def panel(draw, box, fill=PALE, outline="#c7dace", radius=32):
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)


def tag(draw, x, y, name, *, fill=MINT, color=DEEP):
    width = draw.textlength(name, font=font(26, "bold"))
    draw.rounded_rectangle((x, y, x+width+38, y+48), 10, fill=fill)
    write(draw, x+19, y+9, name, 26, "bold", color)


def shape(draw, points, fill, edge=None, width=2):
    draw.polygon(points, fill=fill)
    if edge:
        draw.line((*points, points[0]), fill=edge, width=width, joint="curve")


def leader(draw, start, target, *, color="#4b7969", dot="#f9f5df"):
    x, y = start
    tx, ty = target
    draw.line((x, y, tx, y, tx, ty), fill=color, width=3, joint="curve")
    draw.ellipse((tx-5, ty-5, tx+5, ty+5), fill=dot, outline=color, width=2)


@lru_cache(maxsize=1)
def logo():
    return Image.open(LOGO).convert("RGB").resize((75, 75), Image.Resampling.LANCZOS)


@lru_cache(maxsize=16)
def base(id, takeaway):
    image = gradient((249, 252, 248), (226, 240, 231)).copy()
    draw = ImageDraw.Draw(image)
    image.paste(logo(), (68, 41))
    write(draw, 162, 49, "Elysian Biomedical LLP", 33, "bold", DEEP)
    write(draw, 164, 88, "Cardiology Education Series", 24, "body", MUTED)
    draw.text((1848, 51), "EPISODE 04", fill=DEEP, font=font(27, "bold"), anchor="rt")
    draw.line((69, 137, 1850, 137), fill=LINE, width=2)
    write(draw, 69, 174, SCENES[id]["title"], 72, "title")
    draw.line((69, 968, 1850, 968), fill=LINE, width=2)
    write(draw, 69, 992, takeaway, 32, "bold", DEEP)
    return image


@lru_cache(maxsize=1)
def echo_background():
    image = base("P03", "An echo shows how the valve opens.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    panel(d, (113, 342, 1177, 867), fill="#243234", outline="#5d7771", radius=17)
    tag(d, 142, 366, "Illustrated heart ultrasound", fill="#405553", color="#f4faf0")
    sector = ((510, 449), (724, 449), (1113, 825), (184, 825))
    shape(d, sector, "#414e4e")
    random = Random(74)
    for _ in range(6700):
        y = random.randrange(453, 824)
        left = 510 - (y - 449) * .86
        right = 724 + (y - 449) * 1.03
        x = random.randrange(round(left), round(right))
        shade = random.randrange(51, 115)
        d.point((x, y), fill=(shade, shade + 9, shade + 8))
    lv = curve((321, 747), ((296, 695), (357, 630), (436, 625)),
               ((501, 622), (543, 641), (617, 621)), ((687, 594), (734, 569), (800, 555)),
               ((867, 544), (918, 553), (968, 565)), ((1001, 578), (1003, 606), (995, 622)),
               ((949, 626), (890, 623), (843, 641)), ((797, 652), (785, 674), (751, 697)),
               ((712, 715), (643, 713), (588, 732)), ((476, 771), (392, 801), (321, 747)))
    shape(d, lv, "#313e3d", "#aabdb4", 8)
    d.line(curve((329, 738), ((418, 784), (491, 755), (580, 727)),
                 ((638, 706), (673, 704), (719, 699))), fill="#80968d", width=12, joint="curve")
    d.line(curve((624, 742), ((673, 761), (718, 786), (748, 807))), fill="#a2b8af", width=5, joint="curve")
    write(d, 1242, 391, "Heart ultrasound", 49, "title", DEEP)
    write(d, 1244, 495, "The team looks at how far the valve opens and how blood flows through it.", 34, color=MUTED, maxwidth=523)
    return image


def echo_image(phase):
    image = echo_background().copy()
    d = ImageDraw.Draw(image)
    opens = 0.5 + 0.5 * sin(phase * 2*pi)
    upper_end = (755 + 18*opens, 629 - 12*opens)
    lower_end = (757 + 16*opens, 648 + 13*opens)
    for tip, start in ((upper_end, (735, 572)), (lower_end, (767, 688))):
        leaflet = curve(start, ((start[0]+3, start[1]-9), (tip[0]-11, tip[1]+7), tip))
        d.line(leaflet, fill="#d8d9c5", width=8, joint="curve")
        d.ellipse((tip[0]-7, tip[1]-6, tip[0]+7, tip[1]+6), fill=GOLD)
    d.ellipse((717, 577, 818, 684), outline=GOLD, width=3)
    d.line((816, 608, 876, 482, 1054, 482), fill=GOLD, width=3, joint="curve")
    write(d, 877, 451, "Narrowed aortic valve", 25, "bold", "#f5edce")
    return image


@lru_cache(maxsize=1)
def ct_background():
    image = base("P03", "CT helps the team plan where the valve fits and how to reach it.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    for x, name in ((124, "Aortic root"), (1017, "Pelvic arteries")):
        panel(d, (x, 342, x+779, 873), fill="#253335", outline="#607e74", radius=17)
        tag(d, x+26, 367, name, fill="#405553", color="#f4faf0")
    for x in (513, 1407):
        d.ellipse((x-318, 462, x+318, 821), fill="#374849", outline="#849b92", width=3)
        d.ellipse((x-293, 477, x+293, 804), outline="#5f7572", width=2)
    d.ellipse((293, 504, 680, 777), fill="#55676a", outline="#708783", width=3)
    d.ellipse((497, 495, 716, 781), fill="#a7b6ad", outline="#c8d2c7", width=6)
    d.ellipse((523, 519, 688, 753), fill="#525f5d", outline="#c2d1c4", width=4)
    center = (603, 636)
    for angle in (-pi/2, pi/6, 5*pi/6):
        ax, ay = center[0]+73*cos(angle), center[1]+96*sin(angle)
        control = (((ax+center[0])*.5)+9, ((ay+center[1])*.5)-12)
        d.line(curve((ax, ay), (control, (center[0]+18, center[1]+4), center)),
               fill="#dbe5d6", width=4, joint="curve")
        d.ellipse((ax-10, ay-10, ax+10, ay+10), fill=GOLD)
    for direction in (-1, 1):
        x = 1407 + direction*190
        d.ellipse((x-107, 506, x+107, 724), outline="#aab8ac", width=20)
        d.ellipse((x-58, 591, x+58, 711), outline="#cad4c4", width=8)
    d.ellipse((1352, 486, 1462, 598), fill="#8b9b93", outline="#bdcabd", width=10)
    d.line(curve((1405, 602), ((1381, 620), (1341, 635), (1298, 711))), fill="#c9d6ca", width=20, joint="curve")
    d.line(curve((1405, 602), ((1431, 621), (1474, 641), (1518, 711))), fill="#a0aca3", width=20, joint="curve")
    d.text((1110, 812), "Patient’s right", fill="#e2eee1", font=font(20, "bold"))
    d.text((1376, 810), "Illustrated CT planning views", fill="#d2e3d5", font=font(21))
    return image


def ct_image(phase):
    image = ct_background().copy()
    d = ImageDraw.Draw(image)
    a = round(10 + 11*sin(phase*pi))
    d.ellipse((500-a, 494-a, 715+a, 783+a), outline=GOLD, width=3)
    d.ellipse((1298-21-a*.3, 711-21-a*.3, 1298+21+a*.3, 711+21+a*.3), outline=GOLD, width=3)
    d.line((1095, 763, 1209, 763, 1280, 723), fill=GOLD, width=3, joint="curve")
    write(d, 1095, 725, "Groin route", 23, "bold", "#f4edd2")
    return image


def person(d, x, y, gown, skin, hair, role):
    d.rounded_rectangle((x-96, y+91, x+96, y+241), 49, fill=gown)
    d.ellipse((x-47, y-10, x+47, y+102), fill=skin, outline=SKIN_LINE, width=2)
    d.arc((x-49, y-12, x+49, y+103), 170, 342, fill=hair, width=15)
    d.ellipse((x+18, y+37, x+24, y+43), fill="#796256")
    d.arc((x+5, y+53, x+32, y+69), 15, 137, fill="#a27467", width=2)
    d.text((x, y+270), role, font=font(28, "bold"), fill=DEEP, anchor="mt")


@lru_cache(maxsize=1)
def team_image():
    image = base("P03", "The Heart Team talks through the options with you.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    tag(d, 124, 336, "Heart Team")
    d.ellipse((142, 658, 1056, 806), fill=MINT)
    for args in ((320, 460, "#92bba9", "#d3a18b", "#66594e", "Patient"),
                 (605, 443, "#70a99b", "#e8bba3", "#675a4d", "Cardiologist"),
                 (880, 463, "#598c82", "#bc8671", "#514940", "Heart surgeon")):
        person(d, *args)
    d.rounded_rectangle((431, 679, 763, 715), 11, fill="#c6dbcd", outline="#a8c8b9", width=2)
    d.polygon(((527, 640), (662, 640), (698, 704), (565, 704)), fill="#fcfcf0", outline="#9bbfae")
    d.line((561, 657, 645, 657), fill="#82a996", width=3)
    d.line((571, 672, 654, 672), fill="#82a996", width=3)
    for y, name in ((402, "Transcatheter replacement"), (596, "Surgical replacement")):
        panel(d, (1096, y, 1766, y+156), fill="#eff7ed", radius=20)
        d.ellipse((1128, y+36, 1212, y+120), fill="#d9eee0")
        d.ellipse((1150, y+57, 1190, y+99), outline=JADE, width=4)
        for theta in (pi/2, 7*pi/6, 11*pi/6):
            d.line((1170, y+78, 1170+18*cos(theta), y+78+18*sin(theta)), fill=JADE, width=3)
        d.text((1240, y+78), name, font=font(35, "bold"), fill=INK, anchor="lm")
    return image


def p03(t):
    if t < 8.7:
        return echo_image(t / 1.42)
    if t < 9.4:
        return crossfade(echo_image(8.7 / 1.42), ct_image(0), ease((t-8.7)/.7))
    if t < 15.5:
        return ct_image(ease((t-9.4)/6.1))
    return crossfade(ct_image(1), team_image(), ease((t-15.5)/.8))


@lru_cache(maxsize=2)
def hospital(add_pacer=False):
    image = base("P08", "Staff monitor your heart rhythm and groin site.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    d.ellipse((130, 747, 1291, 836), fill="#e4efe5")
    d.rounded_rectangle((151, 708, 1284, 803), 23, fill="#a7c9ba", outline="#86af9f", width=2)
    d.rounded_rectangle((143, 687, 1292, 733), 19, fill="#f7f8ee", outline="#c0d7c9", width=2)
    d.line((186, 788, 206, 855), fill="#8ab3a3", width=14)
    d.line((1242, 786, 1230, 855), fill="#8ab3a3", width=14)
    d.rounded_rectangle((193, 582, 389, 701), 24, fill="#faf6df", outline="#ccd3bd", width=2)
    head = curve((241, 625), ((206, 616), (210, 562), (239, 545)), ((268, 527), (300, 539), (306, 561)),
                 ((324, 566), (328, 576), (317, 582)), ((317, 605), (306, 616), (292, 623)),
                 ((288, 637), (305, 644), (322, 650)), ((289, 669), (258, 651), (241, 625)))
    shape(d, head, SKIN, SKIN_LINE)
    hair = curve((217, 592), ((208, 565), (222, 544), (246, 538)),
                 ((270, 530), (297, 541), (302, 551)), ((275, 546), (261, 567), (252, 596)),
                 ((237, 609), (226, 603), (217, 592)))
    shape(d, hair, "#62534e")
    leg = curve((742, 622), ((804, 615), (850, 617), (926, 626)), ((1021, 638), (1111, 639), (1172, 640)),
                ((1191, 635), (1190, 611), (1197, 601)), ((1208, 591), (1216, 614), (1220, 632)),
                ((1234, 638), (1237, 663), (1216, 674)), ((1102, 681), (955, 680), (838, 685)),
                ((797, 685), (754, 684), (725, 676)))
    shape(d, [(x+10,y-8) for x,y in leg], "#cb9788")
    shape(d, leg, SKIN, SKIN_LINE)
    gown = curve((307, 635), ((345, 608), (403, 607), (478, 617)),
                 ((539, 622), (615, 606), (671, 603)), ((706, 599), (728, 612), (762, 624)),
                 ((752, 638), (753, 667), (764, 680)), ((620, 698), (515, 697), (396, 697)),
                 ((349, 687), (322, 667), (307, 635)))
    shape(d, gown, "#a5caba", "#7fa99a")
    d.line(((342, 635), (435, 647), (538, 651), (627, 638)), fill="#c7dfcf", width=4, joint="curve")
    nurse = curve((864, 563), ((844, 525), (849, 460), (883, 432)), ((907, 411), (957, 415), (981, 431)),
                  ((1020, 464), (1021, 536), (1033, 608)), ((968, 628), (905, 613), (843, 608)),
                  ((847, 588), (852, 574), (864, 563)))
    shape(d, nurse, "#6eaa9b", "#4d887c")
    nurse_head = curve((894, 420), ((868, 399), (871, 349), (895, 324)), ((920, 300), (957, 309), (972, 337)),
                       ((983, 355), (972, 391), (957, 406)), ((948, 424), (916, 437), (894, 420)))
    shape(d, nurse_head, "#d6a48e", SKIN_LINE)
    d.arc((873, 312, 977, 418), 173, 334, fill="#605450", width=18)
    d.rounded_rectangle((946, 452, 977, 470), 4, fill="#e8f5e9")
    d.rounded_rectangle((756, 619, 805, 654), 7, fill="#f4f1d6", outline="#a79d81", width=2)
    d.rounded_rectangle((766, 625, 794, 645), 3, fill="#fff9e5", outline="#c5b998")
    d.line(((920, 481), (895, 539), (841, 589), (790, 625)), fill="#4b9083", width=23, joint="curve")
    d.line(((920, 480), (898, 538), (845, 589), (792, 625)), fill="#87bdad", width=14, joint="curve")
    d.rounded_rectangle((778, 617, 805, 637), 7, fill="#c4e4d5", outline="#619c88", width=2)
    write(d, 563, 817, "Groin dressing", 28, "bold", DEEP)
    leader(d, (770, 833), (778, 646))
    panel(d, (1299, 355, 1795, 648), fill="#e9f4e9", radius=18)
    write(d, 1330, 379, "Heart-rhythm monitor", 33, "bold", DEEP)
    panel(d, (1330, 450, 1766, 601), fill="#29433e", outline="#6e9b8a", radius=10)
    if add_pacer:
        panel(d, (1298, 680, 1795, 852), fill="#eff7ed", radius=17)
        d.rounded_rectangle((1332, 727, 1399, 790), 15, fill="#b8d8c9", outline="#57917f", width=3)
        d.line(curve((1390, 727), ((1415, 695), (1426, 718), (1422, 761)),
                     ((1419, 781), (1439, 784), (1449, 774))), fill=JADE, width=3, joint="curve")
        write(d, 1470, 725, "Some people need", 27, "bold", INK)
        write(d, 1470, 762, "a pacemaker", 27, "bold", INK)
    return image


def p08(t):
    p = ease((t - 12.6) / .8)
    image = crossfade(hospital(False), hospital(True), p).copy()
    d = ImageDraw.Draw(image)
    shape_points = ((-62, 0), (-26, 0), (-16, -10), (-5, 5), (1, -41), (10, 38), (22, -5),
                    (44, -5), (59, 0), (80, 0))
    for beat in (-1, 0, 1, 2):
        cx = 1368 + ((t*82) % 182) + beat*182
        points = [(cx+x, 527+y) for x,y in shape_points]
        for a, b in zip(points, points[1:]):
            if a[0] >= 1344 and b[0] <= 1751:
                d.line((a,b), fill="#b5e6c5", width=3)
    return image


def groin_locator(d, x, y, scale=1.0):
    hip = curve((50, 0), ((47, 38), (42, 77), (27, 117)), ((10, 155), (10, 188), (18, 229)),
                ((48, 231), (82, 230), (121, 228)), ((129, 189), (153, 172), (162, 171)),
                ((172, 173), (195, 191), (205, 229)), ((243, 232), (278, 230), (308, 229)),
                ((317, 187), (313, 151), (298, 116)), ((282, 75), (275, 36), (275, 0)))
    xy = lambda a,b: (x+a*scale,y+b*scale)
    shape(d, [xy(a,b) for a,b in hip], SKIN, SKIN_LINE, 3)
    d.line([xy(a,b) for a,b in curve((41, 102), ((79, 121), (122, 153), (149, 176)))], fill="#be8477", width=3, joint="curve")
    d.line([xy(a,b) for a,b in curve((285, 102), ((243, 127), (205, 152), (177, 175)))], fill="#be8477", width=3, joint="curve")
    d.rounded_rectangle((*xy(82, 123), *xy(126, 157)), 6, fill="#fbf2d8", outline="#a99b80", width=2)
    d.rounded_rectangle((*xy(91, 129), *xy(118, 150)), 4, fill="#fff9e3", outline="#d1c19a", width=1)
    return xy(104, 140)


def check(d, x, y):
    d.ellipse((x-21, y-21, x+21, y+21), fill="#d8eddf")
    d.line(((x-10,y), (x-3,y+8), (x+11,y-9)), fill=JADE, width=4, joint="curve")


@lru_cache(maxsize=2)
def discharge(alert):
    takeaway = "Contact your care team for new or worsening wound symptoms." if alert else "Follow your own discharge instructions."
    image = base("P09", takeaway).copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    d.ellipse((136, 376, 771, 846), fill=MINT)
    access = groin_locator(d, 214, 424, 1.53)
    write(d, 550, 777, "Groin dressing", 28, "bold", DEEP)
    leader(d, (540, 790), access)
    panel(d, (870, 347, 1786, 864), fill="#eef7ed", radius=20)
    if alert:
        write(d, 919, 393, "Call your care team", 48, "title", DEEP)
        rows = ("Increasing redness or pain", "Fluid draining from the wound", "Fever")
        for i, name in enumerate(rows):
            y = 522+i*97
            d.ellipse((925, y-8, 941, y+8), fill=JADE)
            d.text((965, y), name, font=font(36, "bold"), fill=INK, anchor="lm")
    else:
        write(d, 918, 386, "Your discharge plan", 47, "title", DEEP)
        for i, name in enumerate(("Medicines", "Wound care", "Activity and driving", "Follow-up")):
            y = 507+i*79
            check(d, 951, y)
            d.text((1003, y), name, font=font(35, "bold"), fill=INK, anchor="lm")
    return image


def p09(t):
    return crossfade(discharge(False), discharge(True), ease((t - 9.3) / .8))


def urgent_icon(d, x, y, kind):
    d.ellipse((x-45, y-45, x+45, y+45), fill="#f3e0d5")
    if kind == "bleeding":
        outline = curve((x, y-29), ((x-11,y-12),(x-22,y-7),(x-22,y+9)),
                        ((x-22,y+35),(x+22,y+35),(x+22,y+9)), ((x+22,y-7),(x+11,y-12),(x,y-29)))
        shape(d, outline, "#af6265", WARN)
    elif kind == "chest":
        d.line(((x-30,y),(x-13,y),(x-4,y-17),(x+5,y+18),(x+15,y-8),(x+31,y-8)), fill=WARN, width=5, joint="curve")
    elif kind == "breathing":
        for sign in (-1,1):
            lung = curve((x+sign*5,y-16), ((x+sign*16,y-30),(x+sign*30,y-3),(x+sign*32,y+16)),
                         ((x+sign*31,y+30),(x+sign*19,y+29),(x+sign*7,y+22)))
            shape(d, lung, "#c68484", WARN)
        d.line((x,y-31,x,y+11), fill=WARN, width=4)
    elif kind == "face":
        d.ellipse((x-23,y-28,x+23,y+28), outline=WARN, width=4)
        for off in (-9,9):
            d.ellipse((x+off-3,y-9,x+off+3,y-3), fill=WARN)
        d.line(((x-10,y+12),(x+1,y+13),(x+12,y+18)), fill=WARN, width=4, joint="curve")
    elif kind == "arm":
        d.ellipse((x-9,y-25,x+9,y-7), fill=WARN)
        d.line(((x,y-3),(x,y+22)), fill=WARN, width=6)
        d.line(((x-26,y-9),(x,y+3),(x+23,y+16)), fill=WARN, width=5, joint="curve")
    else:
        d.rounded_rectangle((x-28,y-20,x+28,y+15), 10, outline=WARN, width=4)
        d.line(((x-10,y+14),(x-14,y+26),(x+3,y+14)), fill=WARN, width=4, joint="curve")
        for off in (-13,0,13):
            d.ellipse((x+off-3,y-5,x+off+3,y+1), fill=WARN)


@lru_cache(maxsize=2)
def urgent(stroke):
    image = base("P10", "Call your local emergency number.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL, fill="#fff8f1", outline="#d9c2b4")
    write(d, 126, 342, "Signs of stroke" if stroke else "Get emergency help", 54, "title", WARN)
    rows = (("face", "Sudden face drooping"), ("arm", "Sudden arm weakness"), ("speech", "Sudden trouble speaking")) if stroke else (
        ("bleeding", "Heavy bleeding or bleeding that won’t stop"), ("chest", "Severe chest pain"), ("breathing", "Sudden trouble breathing"))
    for i, (icon, words) in enumerate(rows):
        y = 501 + i*147
        urgent_icon(d, 175, y, icon)
        d.text((252, y), words, font=font(40, "bold"), fill=INK, anchor="lm")
    return image


def p10(t):
    return urgent(t >= 10.0)


@lru_cache(maxsize=1)
def references():
    image = base("P12", "Full references are in the video description.").copy()
    d = ImageDraw.Draw(image)
    panel(d, PANEL)
    write(d, 124, 343, "Transcatheter aortic valve implantation", 46, "title", DEEP)
    d.line((124, 423, 1795, 423), fill=LINE, width=2)
    write(d, 125, 469, "American Heart Association · Aortic stenosis and TAVR", 32, "bold", INK)
    write(d, 125, 532, "ACC/AHA · Valvular heart disease guideline", 32, "bold", INK)
    write(d, 125, 595, "NHS · TAVI assessment, procedure and recovery", 32, "bold", INK)
    write(d, 125, 658, "FDA · Transcatheter valve patient labeling", 32, "bold", INK)
    d.line((124, 735, 1795, 735), fill=LINE, width=2)
    write(d, 124, 776, "Original educational animation", 29, "bold", DEEP)
    write(d, 125, 827, "Alexander synthetic English narration via ElevenLabs", 28, color=MUTED)
    return image


FUNCTIONS = {"P03": p03, "P08": p08, "P09": p09, "P10": p10, "P12": lambda t: references()}
KEY_TIMES = {"P03": 5.4, "P08": 16.0, "P09": 6.0, "P10": 6.0, "P12": 0}


def render(id):
    scene = SCENES[id]
    seconds = scene["target_end_sec"] - scene["target_start_sec"]
    draw = FUNCTIONS[id]
    key = OUT / f"{id}.png"
    video = OUT / f"{id}.mp4"
    draw(KEY_TIMES[id]).save(key, optimize=True)
    with Image.open(key) as check_image:
        assert check_image.size == (W,H)
        check_image.verify()
    rate = 12 if id in ("P03", "P08", "P09") else 4
    tail = ["-an", "-vf", "fps=24", "-c:v", "libx264", "-preset", "veryfast", "-threads", "3", "-crf", "17",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)]
    command = [str(FFMPEG), "-y", "-v", "error"]
    if id == "P12":
        subprocess.run(command + ["-loop", "1", "-framerate", "24", "-i", str(key), "-t", str(seconds)] + tail, check=True)
    else:
        command += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", str(rate), "-i", "-"]
        with subprocess.Popen(command + tail, stdin=subprocess.PIPE) as writer:
            last_image, buffer = None, None
            for n in range(seconds*rate):
                image = draw(n/rate)
                if image is not last_image:
                    last_image, buffer = image, image.tobytes()
                writer.stdin.write(buffer)
            writer.stdin.close()
            if writer.wait():
                raise RuntimeError(f"Could not encode {video.name}")
    metadata = subprocess.run([str(FFMPEG), "-hide_banner", "-xerror", "-i", str(video), "-f", "null", "-"],
                              capture_output=True, text=True, check=True).stderr
    assert "1920x1080" in metadata and "Audio:" not in metadata and f"00:00:{seconds:02}.00" in metadata, metadata
    print(f"{id} · {seconds}s · 1920×1080 silent clip and key PNG verified", flush=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for id in sys.argv[1:] or FUNCTIONS:
        render(id)
