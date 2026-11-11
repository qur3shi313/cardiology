"""Original schematic illustrations for the coronary angiography draft."""

from functools import lru_cache
from math import hypot, sin, tau
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 640, 560
NAVY = "#081726"
PALE = "#e1f5fa"
MUTED = "#a1b7c6"
CYAN = "#76dbe4"
CONTRAST = "#ffcb92"
ARTERY = "#a65053"


def curve(start, *segments):
    points = [start]
    for control_a, control_b, end in segments:
        x0, y0 = points[-1]
        x1, y1 = control_a
        x2, y2 = control_b
        x3, y3 = end
        for index in range(1, 17):
            t = index / 16
            q = 1 - t
            points.append((
                q**3 * x0 + 3 * q*q*t * x1 + 3 * q*t*t * x2 + t**3 * x3,
                q**3 * y0 + 3 * q*q*t * y1 + 3 * q*t*t * y2 + t**3 * y3,
            ))
    return tuple(points)


def trace(points, fraction):
    if fraction >= 1:
        return points
    if fraction <= 0:
        return points[:1]
    remaining = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])) * fraction
    result = [points[0]]
    for a, b in zip(points, points[1:]):
        length = hypot(b[0] - a[0], b[1] - a[1])
        if 0 < remaining < length:
            result.append((a[0] + (b[0] - a[0]) * remaining / length,
                           a[1] + (b[1] - a[1]) * remaining / length))
            break
        result.append(b)
        remaining -= length
    return tuple(result)


@lru_cache(maxsize=12)
def font(size, bold=False):
    filename = "segoeuib.ttf" if bold else "segoeui.ttf"
    local = Path("C:/Windows/Fonts") / filename
    if local.is_file():
        return ImageFont.truetype(str(local), size)
    return ImageFont.load_default(size=size)


def line(draw, path, color, width=1):
    if len(path) >= 2:
        draw.line(path, fill=color, width=width, joint="curve")


def circle(draw, point, radius, fill, outline=None, width=1):
    x, y = point
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill, outline=outline, width=width)


def tube(draw, path, color=ARTERY, width=12, highlight="#c46f6c", border="#502f40"):
    line(draw, path, border, width + 5)
    line(draw, path, color, width)
    if highlight:
        line(draw, tuple((x-1.4, y-1.4) for x, y in path), highlight, max(1, width // 5))


def callout(draw, point, elbow, text, *, end=False, color=MUTED):
    x, y = elbow
    stop = (x-8, y) if end else (x+8, y)
    line(draw, (point, elbow, stop), "#517384", 1)
    circle(draw, point, 2.4, CYAN)
    draw.text((x-12 if end else x+12, y), text, font=font(16), fill=color,
              anchor="rm" if end else "lm")


@lru_cache(maxsize=1)
def backdrop():
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        light = 1 - abs(y - 205) / HEIGHT
        draw.line((0, y, WIDTH, y), fill=(int(7 + 5 * light), int(18 + 11 * light), int(29 + 14 * light)))
    for x in range(24, WIDTH, 20):
        for y in range(22, HEIGHT, 20):
            if ((x-320)/380)**2 + ((y-270)/355)**2 < 1:
                draw.point((x, y), fill="#2d4655")
    draw.rounded_rectangle((1, 1, WIDTH-2, HEIGHT-2), 20, outline="#294556", width=1)
    return image


BODY = curve(
    (252, 34),
    ((252, 76), (245, 91), (201, 101)),
    ((159, 111), (133, 119), (117, 154)),
    ((96, 199), (94, 252), (71, 292)),
    ((60, 316), (48, 346), (43, 376)),
    ((35, 398), (28, 411), (22, 429)),
    ((16, 450), (22, 461), (33, 449)),
    ((44, 434), (50, 426), (52, 426)),
    ((53, 446), (45, 470), (54, 473)),
    ((63, 474), (77, 443), (83, 429)),
    ((94, 406), (87, 385), (107, 355)),
    ((134, 310), (159, 261), (173, 214)),
    ((174, 276), (165, 330), (180, 383)),
    ((190, 428), (183, 476), (174, 540)),
    ((201, 555), (231, 553), (268, 540)),
    ((273, 515), (280, 487), (293, 466)),
    ((304, 489), (312, 520), (316, 541)),
    ((350, 553), (384, 552), (409, 542)),
    ((398, 489), (391, 433), (404, 383)),
    ((417, 329), (413, 281), (413, 214)),
    ((426, 257), (451, 308), (478, 354)),
    ((498, 385), (491, 406), (502, 429)),
    ((508, 443), (522, 474), (531, 473)),
    ((540, 470), (532, 446), (533, 426)),
    ((535, 426), (541, 434), (552, 449)),
    ((563, 461), (569, 450), (563, 429)),
    ((557, 411), (550, 398), (542, 376)),
    ((537, 346), (525, 316), (514, 292)),
    ((491, 252), (489, 199), (468, 154)),
    ((452, 119), (426, 111), (384, 101)),
    ((340, 91), (333, 76), (333, 34)),
)
RADIAL = curve(
    (60, 397),
    ((70, 364), (93, 318), (115, 281)),
    ((133, 254), (139, 205), (153, 174)),
    ((165, 145), (196, 135), (219, 132)),
    ((240, 128), (257, 128), (267, 121)),
    ((272, 134), (280, 143), (291, 151)),
    ((286, 160), (285, 183), (286, 199)),
)
FEMORAL = curve(
    (222, 483),
    ((226, 463), (225, 440), (241, 412)),
    ((254, 392), (271, 382), (295, 373)),
    ((312, 364), (316, 328), (318, 293)),
    ((321, 258), (325, 215), (325, 181)),
    ((325, 145), (308, 139), (295, 147)),
    ((284, 154), (285, 182), (286, 199)),
)
BODY_LEFT_SUBCLAVIAN = curve((316, 147), ((337, 122), (365, 129), (393, 137)),
                             ((414, 142), (430, 154), (439, 177)))
BODY_CAROTIDS = (
    curve((267, 121), ((273, 110), (273, 93), (270, 76))),
    curve((302, 144), ((307, 124), (309, 97), (312, 76))),
)
BODY_OTHER_ILIAC = curve((295, 373), ((322, 383), (342, 398), (347, 424)),
                         ((350, 444), (355, 472), (360, 494)))


def route_panel(route, progress):
    image = backdrop().copy()
    draw = ImageDraw.Draw(image, "RGBA")
    body = tuple((x * .92 + 4, y * .91 + 22) for x, y in BODY)
    draw.polygon(body, fill="#253747")
    line(draw, body, "#4c6371", 1)
    for path in (
        curve((203, 111), ((239, 108), (265, 126), (289, 135))),
        curve((383, 111), ((351, 108), (324, 126), (300, 135))),
        curve((293, 139), ((290, 201), (292, 273), (293, 348))),
        curve((185, 380), ((214, 399), (244, 420), (286, 435))),
        curve((401, 380), ((369, 399), (340, 419), (300, 435))),
    ):
        line(draw, tuple((x*.92+4, y*.91+22) for x, y in path), "#395363", 1)
    for rib in range(5):
        y = 151 + 18 * rib
        for direction in (-1, 1):
            rib_path = curve((293, y+21), ((293 + direction*27, y+12),
                             (293 + direction*62, y-16), (293 + direction*91, y+3)))
            line(draw, tuple((x*.92+4, y*.91+22) for x, y in rib_path), "#334b5c", 1)
    faint_heart = curve((289, 190), ((260, 156), (229, 191), (239, 221)),
                        ((249, 255), (294, 275), (329, 298)),
                        ((355, 267), (367, 217), (334, 194)),
                        ((318, 180), (303, 184), (289, 190)))
    draw.polygon(tuple((x*.92+4, y*.91+22) for x, y in faint_heart), fill=(147, 79, 87, 71))

    def map_path(path):
        return tuple((x*.92+4, y*.91+22) for x, y in path)

    for path, width in (
        (BODY_LEFT_SUBCLAVIAN, 6), (BODY_CAROTIDS[0], 5), (BODY_CAROTIDS[1], 5),
        (BODY_OTHER_ILIAC, 7), (RADIAL, 8), (FEMORAL, 11),
    ):
        tube(draw, map_path(path), "#79515b", width, "#a77577", "#433343")

    active = map_path(FEMORAL if route == "femoral" else RADIAL)
    tube(draw, active, "#b9575a", 11 if route == "femoral" else 8, "#d78476")
    advancement = 0.04 + 0.96 * progress
    wire = trace(active, advancement)
    catheter = trace(active, max(.015, advancement - .045))
    line(draw, wire, "#88aab2", 2)
    line(draw, catheter, CYAN, 3)
    circle(draw, wire[-1], 4, PALE)
    circle(draw, active[0], 10, None, CYAN)
    circle(draw, active[0], 4, CYAN)
    circle(draw, active[-1], 7, None, "#d99789")

    if route == "radial":
        callout(draw, active[0], (79, 401), "Radial artery")
        callout(draw, map_path(((145, 196),))[0], (91, 203), "Brachial", end=True)
        callout(draw, map_path(((170, 153),))[0], (105, 133), "Axillary", end=True)
        callout(draw, map_path(((235, 130),))[0], (377, 103), "Right subclavian")
        callout(draw, map_path(((273, 136),))[0], (401, 142), "Brachiocephalic trunk")
        callout(draw, map_path(((309, 145),))[0], (406, 173), "Aortic arch")
        callout(draw, active[-1], (380, 205), "Aortic root")
    else:
        callout(draw, active[0], (266, 481), "Common femoral artery")
        callout(draw, map_path(((245, 405),))[0], (386, 414), "External iliac")
        callout(draw, map_path(((274, 382),))[0], (399, 378), "Common iliac")
        callout(draw, map_path(((314, 334),))[0], (397, 332), "Abdominal aorta")
        callout(draw, map_path(((323, 238),))[0], (394, 260), "Descending thoracic aorta")
        callout(draw, map_path(((310, 145),))[0], (389, 139), "Aortic arch")
        callout(draw, active[-1], (381, 202), "Aortic root")
    return image


MYOCARDIUM = curve(
    (306, 185),
    ((279, 168), (231, 175), (197, 199)),
    ((151, 230), (154, 290), (179, 337)),
    ((209, 392), (267, 416), (301, 454)),
    ((330, 486), (355, 506), (382, 497)),
    ((428, 471), (466, 421), (484, 365)),
    ((508, 288), (472, 230), (429, 202)),
    ((389, 173), (343, 181), (306, 185)),
)
RV_SHADOW = curve((187, 235), ((164, 283), (193, 335), (238, 365)),
                  ((273, 390), (301, 400), (326, 432)),
                  ((328, 380), (290, 303), (259, 252)),
                  ((240, 218), (218, 219), (187, 235)))
AORTA = curve(
    (308, 239),
    ((306, 212), (302, 183), (306, 154)),
    ((310, 116), (326, 85), (360, 90)),
    ((396, 94), (407, 127), (409, 160)),
    ((411, 184), (409, 205), (410, 228)),
)
ROOT = (308, 233)
RCA_OSTIUM = (296, 220)
LEFT_OSTIUM = (324, 219)
RCA = curve(
    RCA_OSTIUM,
    ((282, 224), (275, 234), (262, 242)),
    ((239, 254), (207, 255), (192, 284)),
    ((173, 317), (202, 347), (239, 365)),
    ((254, 374), (267, 381), (271, 397)),
)
LEFT_MAIN = curve(LEFT_OSTIUM, ((333, 218), (347, 232), (350, 244)))
LAD = curve((350, 244), ((343, 260), (333, 275), (337, 292)),
            ((339, 329), (352, 337), (354, 368)),
            ((353, 399), (373, 432), (383, 477)))
LCX = curve((350, 244), ((373, 234), (391, 244), (407, 255)),
            ((434, 274), (449, 281), (464, 301)),
            ((469, 312), (469, 325), (466, 336)))
RCA_TWIGS = (
    curve((201, 270), ((185, 270), (176, 278), (171, 289))),
    curve((194, 306), ((212, 305), (216, 319), (225, 336))),
    curve((219, 354), ((212, 368), (225, 384), (239, 397))),
    curve((247, 370), ((260, 367), (274, 379), (294, 396))),
)
LEFT_TWIGS = (
    curve((340, 279), ((318, 285), (303, 304), (296, 334))),
    curve((340, 315), ((366, 311), (382, 328), (398, 351))),
    curve((353, 361), ((338, 373), (339, 390), (342, 411))),
    curve((362, 409), ((393, 399), (413, 424), (417, 445))),
    curve((397, 248), ((397, 269), (412, 295), (426, 310))),
    curve((429, 271), ((447, 285), (441, 320), (438, 340))),
    curve((450, 287), ((467, 281), (475, 286), (477, 294))),
)


def heart_anatomy(route, stage, progress):
    image = backdrop().copy()
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((138, 88, 523, 514), fill=(92, 55, 64, 22))
    draw.ellipse((163, 119, 490, 512), fill=(115, 60, 71, 20))
    desc = curve((410, 182), ((410, 268), (401, 317), (394, 388)),
                 ((390, 435), (384, 463), (382, 491)))
    tube(draw, desc, "#543745", 24, "#6e4951", "#392d3b")

    draw.polygon(MYOCARDIUM, fill="#733d50")
    line(draw, MYOCARDIUM, "#ab6268", 2)
    for layer in range(12):
        inset = 1 - .033 * (layer + 1)
        path = tuple((x * inset + 321*(1-inset), y * inset + 307*(1-inset))
                     for x, y in MYOCARDIUM)
        draw.polygon(path, fill=(183, 99, 100, 11))
    draw.polygon(RV_SHADOW, fill=(50, 40, 58, 81))
    for index in range(22):
        x = 195 + index * 12
        y = 251 + abs(x-310)*.08
        extent = 100 + 67 * max(0, 1 - abs(x-339)/144)
        fiber = curve((x, y), ((x-13, y+extent*.32), (x+9, y+extent*.71),
                              (min(472, x+25), y+extent)))
        line(draw, fiber, (239, 138, 129, 23), 1)
    sv = curve((207, 109), ((207, 142), (207, 173), (224, 195)))
    tube(draw, sv, "#3b5d75", 24, "#5f7c8b", "#253c54")
    pulmonary = curve((281, 216), ((272, 177), (279, 160), (298, 143)),
                      ((313, 130), (330, 129), (353, 138)))
    tube(draw, pulmonary, "#526b7d", 27, "#7c919c", "#3a4c63")
    brachio = curve((322, 110), ((312, 89), (288, 67), (270, 60)),
                   ((258, 55), (248, 56), (238, 54)))
    carotids = (
        curve((279, 66), ((275, 55), (275, 43), (278, 31))),
        curve((351, 92), ((344, 76), (344, 59), (346, 41))),
        curve((380, 100), ((390, 86), (401, 70), (416, 61))),
    )
    for path in carotids:
        tube(draw, path, "#945058", 12, "#bf746e")
    tube(draw, brachio, "#ad585c", 17, "#d28b7a")
    tube(draw, AORTA, "#bd6767", 29, "#d38f85", "#683e4d")
    root = curve((299, 250), ((291, 232), (291, 220), (299, 210)),
                 ((309, 202), (323, 204), (330, 214)),
                 ((336, 226), (330, 240), (320, 250)))
    draw.polygon(root, fill=(165, 78, 88, 240))
    line(draw, root, "#d08c81", 2)
    if stage != "heart":
        draw.ellipse((293, 233, 326, 247), fill="#452d40", outline="#d19084", width=1)
        line(draw, ((300, 240), (309, 237), (317, 242)), "#b97878", 1)

    artery_sets = (
        (RCA, 8, "right"), (LEFT_MAIN, 9, "left"),
        (LAD, 8, "left"), (LCX, 7, "left"),
    )
    for path in RCA_TWIGS + LEFT_TWIGS:
        tube(draw, path, "#ad6d68", 3, None, "#603d50")
    for path, width, side in artery_sets:
        selected = stage == f"{side}_contrast"
        tube(draw, path, "#cc8777" if selected else "#be7b70", width, "#e2a88c", "#633d4c")
        if selected:
            visible = .14 + min(1, progress * 1.6) * .86
            line(draw, trace(path, visible), CONTRAST, max(3, width-2))
    branch_set = RCA_TWIGS if stage == "right_contrast" else LEFT_TWIGS
    if stage in ("left_contrast", "right_contrast"):
        for path in branch_set:
            line(draw, trace(path, max(0, min(1, progress*2.6-.55))), "#f5b780", 3)

    if stage == "heart":
        callout(draw, (384, 103), (448, 81), "Aorta")
        callout(draw, (338, 236), (442, 211), "Left main")
        callout(draw, (368, 419), (461, 463), "LAD")
        callout(draw, (432, 276), (506, 257), "Circumflex")
        callout(draw, (205, 271), (121, 260), "Right coronary", end=True)
        return image

    if route == "femoral":
        # The descending thoracic aorta lies posterior to this heart view.
        # The complete course appears in the preceding route illustration.
        catheter_path = AORTA[53::-1]
    else:
        catheter_path = brachio[::-1] + AORTA[25::-1]
    shaft = catheter_path[:-9]
    left_tip = ((307, 213), (310, 214), (316, 219), (319, 221), (321, 220), (326, 219))
    root_tip = ((309, 201), (310, 204), (310, 208), (310, 210), (309, 211), (308, 212))
    right_tip = ((313, 214), (309, 226), (301, 223), (299, 222), (297, 220), (295, 221))

    def blend(a, b, t):
        t = max(0, min(1, t))
        return tuple((ax + (bx-ax)*t, ay + (by-ay)*t) for (ax, ay), (bx, by) in zip(a, b))

    def path_to(tip):
        return shaft + curve(shaft[-1], tip[:3], tip[3:])

    if stage == "root":
        catheter = path_to(blend(root_tip, left_tip, (progress - .46) / .54))
        if progress < .42:
            wire_path = path_to(root_tip)
            wire = trace(wire_path, 1 - progress * .80)
            line(draw, wire, "#90bcc8", 2)
    elif stage == "radial_transfer":
        tip = blend(left_tip, root_tip, progress * 2) if progress < .5 else blend(root_tip, right_tip, (progress - .5) * 2)
        catheter = path_to(tip)
    elif stage == "femoral_left_out":
        catheter = trace(path_to(left_tip), 1 - progress * .94)
    elif stage == "femoral_right_in":
        approach = path_to(blend(root_tip, right_tip, (progress - .70) / .30))
        catheter = trace(approach, min(1, .34 + progress * 1.6))
        if progress < .70:
            wire = trace(path_to(root_tip), min(1, .48 + progress * 1.7))
            line(draw, wire, "#90bcc8", 2)
    else:
        catheter = path_to(right_tip if stage == "right_contrast" else left_tip)
    line(draw, catheter, "#1f596c", 7)
    line(draw, catheter, "#f0fbfe", 3)
    circle(draw, catheter[-1], 4, PALE)
    if stage in ("root", "radial_transfer", "femoral_left_out", "femoral_right_in"):
        callout(draw, (310, 210), (442, 191), "Aortic root")
        callout(draw, (321, 240), (467, 246), "Aortic valve")
        callout(draw, (325, 220), (447, 221), "Left coronary opening")
        callout(draw, (296, 221), (202, 208), "Right coronary opening", end=True)
    return image


ANGIO_LEFT = (
    (curve((86, 42), ((86, 60), (106, 71), (109, 86))), 9),
    (curve((109, 86), ((127, 99), (134, 118), (139, 144)),
           ((144, 167), (163, 192), (154, 224)),
           ((148, 250), (152, 266), (163, 284))), 8),
    (curve((109, 86), ((86, 97), (78, 120), (62, 139)),
           ((46, 157), (47, 173), (34, 195))), 7),
    (curve((128, 117), ((161, 117), (187, 136), (196, 178))), 4),
    (curve((138, 140), ((105, 151), (104, 171), (97, 198))), 4),
    (curve((149, 173), ((180, 184), (192, 206), (194, 240))), 4),
    (curve((153, 221), ((125, 231), (118, 248), (109, 263))), 3),
    (curve((76, 119), ((58, 121), (37, 138), (31, 154))), 3),
    (curve((60, 142), ((76, 148), (71, 169), (67, 183))), 3),
    (curve((182, 151), ((205, 153), (214, 163), (222, 179))), 2),
)
ANGIO_RIGHT = (
    (curve((116, 36), ((147, 44), (164, 75), (160, 100)),
           ((154, 131), (127, 143), (95, 147)),
           ((64, 152), (49, 171), (55, 195)),
           ((61, 220), (99, 220), (116, 242)),
           ((123, 252), (124, 270), (123, 287))), 9),
    (curve((155, 119), ((169, 128), (168, 151), (172, 166))), 4),
    (curve((124, 140), ((133, 160), (135, 175), (151, 188))), 4),
    (curve((92, 148), ((100, 171), (104, 187), (116, 198))), 3),
    (curve((55, 175), ((32, 182), (24, 198), (29, 217))), 4),
    (curve((64, 209), ((65, 231), (52, 246), (43, 254))), 3),
    (curve((101, 226), ((115, 215), (145, 215), (161, 236)),
           ((174, 256), (193, 260), (208, 270))), 4),
    (curve((158, 233), ((169, 224), (186, 224), (202, 234))), 2),
)


def angiogram(side, progress, narrowed=False):
    image = Image.new("RGB", (246, 320), "#a1a9ae")
    draw = ImageDraw.Draw(image, "RGBA")
    for y in range(320):
        level = int(171 - 23 * sin(y/320 * tau - .75) - y/27)
        draw.line((0, y, 246, y), fill=(level, level+5, level+8))
    for offset in range(9):
        y = 35 + offset * 30
        line(draw, curve((-12, y+27), ((57, y-7), (128, y-24), (233, y+20))),
             (237, 242, 245, 27), 3)
    draw.ellipse((17, 29, 226, 315), fill=(47, 54, 62, 24))
    draw.ellipse((37, 64, 231, 329), fill=(35, 41, 51, 22))
    vessels = ANGIO_RIGHT if side == "right" else ANGIO_LEFT
    fullness = min(1, .23 + progress * 1.52)
    for index, (path, width) in enumerate(vessels):
        visible = max(0, fullness - (0 if index < 3 else .13))
        points = trace(path, visible)
        for segment, (a, b) in enumerate(zip(points, points[1:])):
            pos = segment / max(1, len(path)-1)
            weight = max(1, round(width * (1 - pos*.51)))
            if narrowed and index == 1 and .43 < pos < .53:
                weight = 2
            line(draw, (a, b), (33, 38, 41, 130), weight+2)
            line(draw, (a, b), (19, 25, 28, 240), weight)
    draw.rounded_rectangle((0, 0, 245, 319), 9, outline="#42545e", width=2)
    return image


def contrast_panel(route, stage, progress):
    side = "right" if stage == "right_contrast" else "left"
    image = backdrop().copy()
    anatomy = heart_anatomy(route, stage, progress)
    anatomy = anatomy.crop((130, 18, 520, 519))
    anatomy.thumbnail((365, 470), Image.Resampling.LANCZOS)
    image.paste(anatomy, (24, 49))
    draw = ImageDraw.Draw(image)
    title = "Right coronary artery" if side == "right" else "Left coronary system"
    draw.text((36, 31), title, font=font(21, True), fill=PALE)
    draw.text((440, 104), "Illustrated X-ray view", font=font(14), fill=MUTED)
    panel = angiogram(side, progress)
    panel.thumbnail((170, 240), Image.Resampling.LANCZOS)
    image.paste(panel, (440, 130))
    if side == "left":
        callout(draw, (222, 254), (316, 244), "Left main")
        callout(draw, (298, 283), (330, 300), "Circumflex")
        callout(draw, (240, 407), (305, 413), "LAD")
    else:
        callout(draw, (82, 297), (65, 340), "RCA")
    return image


def stenosis_panel(progress):
    image = backdrop().copy()
    draw = ImageDraw.Draw(image)
    film = angiogram("left", max(.55, progress), narrowed=True)
    film = film.resize((288, 374), Image.Resampling.LANCZOS)
    image.paste(film, (37, 90))
    draw.text((38, 57), "Illustrated angiogram", font=font(20, True), fill=PALE)
    point = (205, 282)
    circle(draw, point, 18, None, "#ffcf93", 2)
    line(draw, (point, (340, 279), (360, 279)), "#d5a779", 1)
    draw.rounded_rectangle((361, 193, 611, 358), 14, fill="#142937", outline="#496370")
    wall = curve((380, 238), ((425, 224), (430, 223), (459, 232)),
                 ((488, 241), (501, 238), (533, 231)),
                 ((558, 225), (579, 227), (594, 233)))
    lower = curve((594, 299), ((560, 303), (552, 299), (526, 299)),
                  ((501, 300), (479, 306), (458, 307)),
                  ((425, 307), (402, 308), (380, 304)))
    draw.polygon(wall + lower, fill="#996368")
    channel_top = curve((380, 253), ((418, 248), (433, 243), (454, 255)),
                        ((468, 262), (469, 271), (487, 271)),
                        ((503, 271), (502, 253), (521, 251)),
                        ((550, 247), (575, 249), (594, 248)))
    channel_lower = curve((594, 282), ((548, 282), (528, 284), (508, 285)),
                          ((474, 287), (454, 288), (430, 288)),
                          ((406, 288), (390, 290), (380, 289)))
    draw.polygon(channel_top + channel_lower, fill="#f3b888")
    draw.text((486, 329), "Narrowed channel", font=font(17, True), fill=PALE, anchor="mm")
    return image


def aftercare_panel(route):
    image = backdrop().copy()
    draw = ImageDraw.Draw(image)
    if route == "femoral":
        body = curve((167, 108), ((131, 210), (162, 291), (169, 386)),
                     ((168, 418), (157, 452), (151, 496)),
                     ((216, 507), (271, 509), (309, 498)),
                     ((312, 443), (326, 417), (335, 395)),
                     ((349, 418), (364, 452), (368, 498)),
                     ((428, 509), (478, 507), (517, 496)),
                     ((505, 430), (497, 397), (505, 343)),
                     ((529, 245), (505, 170), (495, 108)))
        draw.polygon(body, fill="#687c87")
        line(draw, body, "#a9bac0", 2)
        line(draw, curve((174, 305), ((213, 327), (257, 365), (319, 391))), "#435d6e", 2)
        draw.rounded_rectangle((246, 343, 316, 393), 7, fill="#dce8e8", outline="#8eb6bf", width=2)
        callout(draw, (278, 362), (373, 270), "Dressing or closure site")
        return image
    forearm = curve(
        (77, 361),
        ((133, 332), (189, 312), (267, 291)),
        ((309, 279), (347, 259), (359, 239)),
        ((376, 210), (405, 188), (423, 178)),
        ((442, 167), (459, 146), (471, 155)),
        ((479, 164), (466, 177), (453, 193)),
        ((481, 190), (505, 175), (533, 170)),
        ((552, 166), (566, 170), (567, 180)),
        ((566, 194), (533, 194), (512, 207)),
        ((542, 204), (573, 191), (585, 200)),
        ((601, 215), (572, 225), (523, 238)),
        ((547, 236), (571, 229), (577, 242)),
        ((583, 254), (551, 263), (521, 271)),
        ((532, 271), (549, 271), (549, 281)),
        ((547, 297), (512, 304), (476, 310)),
        ((437, 324), (414, 330), (377, 328)),
        ((353, 334), (329, 347), (296, 357)),
        ((221, 388), (166, 422), (118, 438)),
    )
    draw.polygon(forearm, fill="#a57e78")
    line(draw, forearm, "#c7998a", 2)
    draw.polygon(((274, 282), (321, 264), (365, 335), (314, 357)), fill="#adc7cc")
    draw.polygon(((283, 283), (312, 273), (353, 339), (321, 350)), fill="#dce9e9")
    draw.rounded_rectangle((300, 283, 343, 330), 12, fill="#75b8c3", outline="#e6f5f5", width=2)
    draw.ellipse((309, 295, 335, 319), fill="#9bd6db", outline="#4e8e9e", width=1)
    callout(draw, (325, 300), (278, 210), "Wrist compression band", end=True)
    return image


@lru_cache(maxsize=120)
def frame(route, stage, step):
    progress = step / 24
    if stage == "route":
        return route_panel(route, progress)
    if stage in ("left_contrast", "right_contrast"):
        return contrast_panel(route, stage, progress)
    if stage == "stenosis":
        return stenosis_panel(progress)
    if stage == "aftercare":
        return aftercare_panel(route)
    return heart_anatomy(route, stage, progress)


@lru_cache(maxsize=160)
def sized_frame(route, stage, step, width, height):
    source = frame(route, stage, step)
    scale = min(width/WIDTH, height/HEIGHT)
    actual_size = (max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale)))
    return source.resize(actual_size, Image.Resampling.LANCZOS)


def draw_vascular(image, box, route, stage, progress):
    """Paint a clinical illustration into (left, top, right, bottom) on a PIL image."""
    left, top, right, bottom = (round(value) for value in box)
    width, height = right-left, bottom-top
    if width <= 0 or height <= 0:
        return
    route = "femoral" if route == "femoral" else "radial"
    step = round(24 * min(1, max(0, progress)))
    if stage in ("heart", "aftercare"):
        step = 24
    panel = sized_frame(route, stage, step, width, height)
    if panel.size != (width, height):
        ImageDraw.Draw(image).rectangle((left, top, right-1, bottom-1), fill=NAVY)
    image.paste(panel, (left + (width-panel.width)//2, top + (height-panel.height)//2))
