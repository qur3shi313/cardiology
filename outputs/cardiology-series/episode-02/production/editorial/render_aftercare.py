"""Render recovery, antiplatelets, aftercare, conclusion, and sources for episode 02."""
from __future__ import annotations

from functools import lru_cache
from math import cos, pi, sin
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
from render_story import (
    GOLD, GREEN, H, INK, LINE, MINT, MUTED, OUT, PANEL, W, WHITE, WARM,
    artery, background, blend_frames, card, encode, font, heart, label, pill, proto, shared, smooth,
)


def path(start, *segments):
    return shared.curve(start, *segments)


def figure(pen, outline, fill, edge, width=2):
    pen.polygon(outline, fill=fill)
    pen.line(outline + outline[:1], fill=edge, width=width, joint="curve")


def checkmark(pen, x, y, radius=17):
    pen.ellipse((x-radius, y-radius, x+radius, y+radius), fill="#d9eee0")
    pen.line(((x-8, y), (x-2, y+6), (x+10, y-7)), fill="#347b65", width=3, joint="curve")


def document(pen, x, y, scale=1, title=""):
    def box(a, b, c, d):
        return x+a*scale, y+b*scale, x+c*scale, y+d*scale

    pen.rounded_rectangle(box(0, 12, 271, 318), round(16*scale), fill="#c5ddcd", outline="#7ca797", width=max(1, round(3*scale)))
    pen.rounded_rectangle(box(19, 31, 252, 296), round(9*scale), fill="#fbfbf2", outline="#b2c9b8", width=max(1, round(2*scale)))
    pen.rounded_rectangle(box(83, 0, 188, 39), round(8*scale), fill="#4e8f7b")
    if title:
        pen.text((x+136*scale, y+90*scale), title, font=font(round(23*scale), "semibold"), fill=GREEN, anchor="mm")
    for j in range(3):
        py = y + (142 + j * 45) * scale
        checkmark(pen, x + 54 * scale, py, round(11 * scale))
        pen.line((x + 77*scale, py, x + 218*scale, py), fill="#a9c4b7", width=max(2, round(3*scale)))


@lru_cache(maxsize=1)
def observation_scene():
    image = background("Recovery and discharge", "Recovery and discharge instructions").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 250, 1522, 779))
    pen.ellipse((152, 632, 1030, 710), fill="#e2eee3")
    pen.rounded_rectangle((122, 585, 1006, 672), 21, fill="#a4c7b8", outline="#84aa9b", width=2)
    pen.rounded_rectangle((118, 572, 1012, 612), 14, fill="#f9faf0", outline="#c1d6ca", width=2)
    pen.line((157, 658, 171, 710), fill="#8bb6a6", width=12)
    pen.line((961, 657, 948, 710), fill="#8bb6a6", width=12)
    pen.rounded_rectangle((150, 462, 349, 575), 26, fill="#f7f4df", outline="#d2d6bd", width=2)
    patient_head = path((192, 515), ((165, 500), (168, 458), (190, 443)), ((214, 428), (236, 434), (246, 457)),
                        ((255, 457), (268, 465), (260, 472)), ((257, 493), (248, 505), (237, 511)),
                        ((239, 526), (251, 531), (269, 535)), ((247, 547), (217, 542), (192, 515)))
    figure(pen, patient_head, "#e7af98", "#ba8275")
    hair = path((176, 482), ((163, 458), (176, 440), (192, 438)), ((214, 426), (230, 434), (237, 442)),
                ((216, 442), (200, 452), (196, 468)), ((193, 481), (187, 489), (176, 482)))
    figure(pen, hair, "#645650", "#63544e", 1)
    gown = path((244, 524), ((276, 495), (333, 501), (381, 524)), ((445, 532), (506, 533), (568, 515)),
                ((650, 493), (805, 522), (944, 548)), ((974, 554), (982, 575), (964, 592)),
                ((794, 608), (557, 596), (384, 593)), ((312, 589), (267, 565), (244, 524)))
    figure(pen, gown, "#a9cdbd", "#7fae9b")
    pen.line(((380, 552), (518, 553), (667, 535), (827, 550), (926, 565)), fill="#c2dfce", width=4, joint="curve")
    # Nurse at the bedside, with the gloved hand at the patient's wrist.
    nurse_body = path((676, 455), ((655, 429), (650, 392), (667, 369)), ((682, 350), (735, 350), (760, 365)),
                      ((794, 385), (806, 444), (807, 529)), ((770, 538), (708, 535), (657, 522)),
                      ((661, 500), (660, 474), (676, 455)))
    figure(pen, nurse_body, "#6ba797", "#4e8b7c")
    nurse_head = path((689, 368), ((667, 351), (668, 309), (694, 290)), ((718, 277), (747, 290), (751, 313)),
                      ((755, 328), (746, 350), (730, 363)), ((714, 370), (708, 383), (689, 368)))
    figure(pen, nurse_head, "#d7a58e", "#a77668")
    nurse_hair = path((668, 336), ((662, 308), (673, 291), (696, 285)), ((722, 277), (744, 287), (751, 302)),
                      ((734, 300), (714, 305), (701, 324)), ((690, 339), (679, 345), (668, 336)))
    figure(pen, nurse_hair, "#615550", "#665551", 1)
    pen.rounded_rectangle((727, 393, 755, 411), 4, fill="#deeee1")
    arm = path((343, 556), ((416, 549), (502, 553), (572, 548)), ((610, 543), (649, 543), (675, 551)),
               ((694, 556), (701, 567), (687, 574)), ((659, 580), (609, 573), (573, 572)),
               ((488, 579), (400, 580), (342, 574)))
    figure(pen, arm, "#e5b29d", "#b7897b")
    pen.rounded_rectangle((607, 545, 634, 575), 6, fill="#6faea3", outline="#477c72", width=2)
    pen.rounded_rectangle((609, 547, 634, 556), 4, fill="#c4e3d4", outline="#72a393", width=1)
    pen.line(((724, 423), (708, 472), (656, 528), (628, 547)), fill="#478b7c", width=18, joint="curve")
    pen.line(((725, 420), (711, 473), (661, 527), (637, 545)), fill="#80bbab", width=12, joint="curve")
    pen.rounded_rectangle((619, 538, 642, 554), 7, fill="#bde2d1", outline="#599b87", width=2)
    label(pen, (616, 563), (546, 707), "Wrist access site")
    card(pen, (1046, 318, 1484, 651), fill="#e9f5e9", radius=19)
    pen.text((1076, 343), "What staff check", font=font(31, "semibold"), fill=GREEN)
    for i, item in enumerate(("Blood pressure", "Pulse", "Access site")):
        y = 425 + 71 * i
        checkmark(pen, 1094, y, 16)
        pen.text((1129, y), item, font=font(27), fill=INK, anchor="lm")
    return image


@lru_cache(maxsize=1)
def discharge_scene():
    image = background("Recovery and discharge", "Discharge timing depends on your condition and why the procedure was done.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 250, 1522, 779))
    pen.ellipse((171, 318, 625, 732), fill=MINT)
    document(pen, 232, 337, 1.20, "Discharge plan")
    pen.text((676, 300), "Your discharge plan", font=font(48, "heading"), fill=GREEN)
    for i, item in enumerate(("Wound care", "Activity", "Medicines", "Follow-up")):
        y = 418 + 76 * i
        checkmark(pen, 704, y, 23)
        pen.text((751, y), item, font=font(34, "semibold"), fill=INK, anchor="lm")
    return image


def p13(p):
    return blend_frames(observation_scene(), discharge_scene(), smooth((p - .49) / .13))


@lru_cache(maxsize=1)
def platelet_scene():
    image = background("Antiplatelet medicines", "Antiplatelets make platelets less likely to clump and help prevent a clot inside the stent.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 253, 1522, 764))
    position = artery(image, (109, 367, 1489, 685), treated=True)
    for index, (x, offset) in enumerate(((388, 4), (505, 20), (602, -18), (693, 12), (754, -25), (832, 6),
                                         (914, -15), (1007, 11), (1086, -20), (1185, 2), (1290, 19))):
        px, py = position(x, proto.center(x) + offset)
        radius = 10 + (index % 3) * 2
        pen.ellipse((px-radius, py-radius*.57, px+radius, py+radius*.57), fill="#e0c9e4", outline="#815b88", width=2)
        pen.arc((px-radius+3, py-radius*.57+2, px+radius-3, py+radius*.57-2), 190, 332, fill="#f2e6ef", width=2)
    label(pen, position(1090, proto.center(1090) - 18), (1155, 317), "Platelets")
    label(pen, position(proto.TARGET-95, proto.center(proto.TARGET-95) - 67), (348, 305), "Stent")
    return image


@lru_cache(maxsize=1)
def antiplatelet_card():
    image = background("Antiplatelet medicines", "Your cardiology team tailors your medicine plan to your situation.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 253, 1522, 764))
    pen.ellipse((164, 311, 622, 707), fill=MINT)
    document(pen, 231, 340, 1.13, "Medicines")
    pen.rounded_rectangle((443, 562, 526, 642), 11, fill="#a8cebc", outline="#5e9281", width=3)
    pen.rounded_rectangle((453, 539, 517, 567), 7, fill="#76a995", outline="#5e9281", width=2)
    pen.rounded_rectangle((456, 584, 514, 617), 5, fill="#edf7e9")
    pen.text((680, 346), "Take antiplatelets", font=font(53, "heading"), fill=GREEN)
    pen.text((680, 408), "as prescribed", font=font(53, "heading"), fill=GREEN)
    pen.line((681, 501, 1422, 501), fill=LINE, width=2)
    pen.text((683, 547), "Contact your cardiology team", font=font(30, "semibold"), fill=INK)
    pen.text((683, 592), "before stopping or changing them.", font=font(30), fill=MUTED)
    return image


def p14(p):
    return blend_frames(platelet_scene(), antiplatelet_card(), smooth((p - .52) / .12))


def wrist_symbol(pen, x, y, scale=1):
    def xy(points):
        return tuple((x+a*scale, y+b*scale) for a,b in points)

    shape = path((0, 45), ((38, 37), (53, 28), (69, 12)), ((87, -6), (100, -5), (100, 7)),
                 ((94, 20), (80, 27), (77, 35)), ((104, 29), (125, 22), (145, 27)),
                 ((158, 34), (149, 45), (132, 47)), ((147, 46), (154, 51), (149, 60)),
                 ((145, 65), (132, 67), (115, 66)), ((128, 65), (140, 68), (134, 76)),
                 ((126, 85), (114, 82), (99, 83)), ((93, 92), (83, 93), (63, 92)),
                 ((41, 93), (14, 86), (0, 85)))
    figure(pen, xy(shape), "#e9b8a0", "#b98373", max(1, round(2*scale)))
    band = xy(((29, 36), (48, 30), (61, 89), (41, 91)))
    figure(pen, band, "#85b9a8", "#537f72", max(1, round(2*scale)))


def medical_icon(pen, x, y, kind):
    pen.ellipse((x-31, y-31, x+31, y+31), fill="#f4dfd2")
    if kind == "pain":
        points = ((x-21, y), (x-9, y), (x-3, y-10), (x+4, y+13), (x+11, y-4), (x+20, y-4))
        pen.line(points, fill="#91484b", width=4, joint="curve")
    elif kind == "bleed":
        outline = path((x, y-22), ((x-8, y-10), (x-15, y-4), (x-15, y+6)),
                       ((x-15, y+25), (x+15, y+25), (x+15, y+6)), ((x+15, y-4), (x+8, y-10), (x, y-22)))
        figure(pen, outline, "#ae5b5c", "#94454b", 1)
    else:
        for angle in (0, pi/3, 2*pi/3):
            vx, vy = 17*cos(angle), 17*sin(angle)
            pen.line((x-vx, y-vy, x+vx, y+vy), fill="#91484b", width=3)


@lru_cache(maxsize=3)
def aftercare_scene(kind):
    title = "Aftercare and urgent symptoms"
    if kind == "urgent":
        image = background(title, "Use your local emergency number.").copy()
        pen = ImageDraw.Draw(image)
        card(pen, (76, 248, 1522, 772), fill="#fff8f0", outline="#d0b9ab")
        pen.text((122, 287), "Get emergency help", font=font(48, "heading"), fill="#883d44")
        symptoms = (
            ("pain", "Severe or persistent chest pain"),
            ("bleed", "Bleeding that won’t stop"),
            ("cold", "A cold or numb hand or foot on the side used for the procedure"),
        )
        for i, (icon, phrase) in enumerate(symptoms):
            y = 412 + 116*i
            medical_icon(pen, 148, y, icon)
            pen.text((207, y), phrase, font=font(31, "semibold"), fill=INK, anchor="lm")
        wrist_symbol(pen, 1281, 609, 1.16)
        return image
    image = background(title, "Follow the activity and wound-care instructions from your hospital.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 248, 1522, 772))
    pen.ellipse((151, 315, 586, 718), fill=MINT)
    if kind == "wound":
        document(pen, 214, 331, 1.13, "At home")
        wrist_symbol(pen, 372, 572, 1.20)
        pen.text((681, 405), "Follow your hospital’s", font=font(47, "heading"), fill=GREEN)
        pen.text((681, 466), "activity and wound-care", font=font(47, "heading"), fill=GREEN)
        pen.text((681, 527), "instructions", font=font(47, "heading"), fill=GREEN)
    else:
        walking_figure(pen, 368, 491, 1.8)
        pen.text((681, 397), "Follow-up and", font=font(49, "heading"), fill=GREEN)
        pen.text((681, 464), "cardiac rehabilitation", font=font(49, "heading"), fill=GREEN)
        pen.text((683, 579), "Ask your care team what is right for you.", font=font(27), fill=MUTED)
    return image


def walking_figure(pen, x, y, scale):
    def xy(points):
        return tuple((x+a*scale, y+b*scale) for a,b in points)

    pen.ellipse((x-16*scale, y-71*scale, x+16*scale, y-39*scale), fill="#d6a38d", outline="#b58376", width=2)
    spine = xy(((0, -31), (-6, 15), (7, 39)))
    limbs = (spine, xy(((-4, -19), (20, 1), (38, -9))), xy(((-6, -13), (-30, 4), (-43, -5))),
             xy(((1, 29), (-24, 56), (-41, 81))), xy(((6, 28), (30, 55), (49, 55))))
    for points in limbs:
        pen.line(points, fill="#4d927e", width=round(12*scale), joint="curve")
    pen.line(xy(((-43, 84), (-27, 84))), fill="#366c60", width=round(7*scale))
    pen.line(xy(((46, 55), (61, 55))), fill="#366c60", width=round(7*scale))


def p15(p):
    if p < .69:
        return blend_frames(aftercare_scene("wound"), aftercare_scene("urgent"), smooth((p - .16) / .07))
    return blend_frames(aftercare_scene("urgent"), aftercare_scene("follow"), smooth((p - .69) / .10))


@lru_cache(maxsize=1)
def treated_scene():
    image = background("What treatment changes", "The stent supports one treated section. Coronary artery disease needs ongoing care.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 743))
    position = artery(image, (108, 361, 1490, 673), treated=True)
    label(pen, position(proto.TARGET + 64, proto.center(proto.TARGET + 64) - 58), (1013, 311), "Treated section")
    return image


def conversation(pen, x, y):
    pen.ellipse((x-15, y+94, x+265, y+128), fill="#dceade")
    for off, top, gown, skin in ((0, 0, "#8bb8a7", "#e3ae97"), (155, 6, "#588f82", "#cf9a86")):
        px, py = x+off, y+top
        pen.rounded_rectangle((px, py+49, px+94, py+129), 28, fill=gown)
        pen.ellipse((px+25, py+1, px+69, py+50), fill=skin, outline="#a4796e", width=2)
        pen.arc((px+23, py, px+70, py+49), 170, 333, fill="#5a524d", width=9)
    pen.rounded_rectangle((x+67, y-21, x+178, y+16), 10, fill="#f3f8ed", outline="#b6cebf", width=2)
    pen.polygon(((x+85, y+14), (x+82, y+24), (x+105, y+14)), fill="#f3f8ed")
    for dot in (101, 122, 143):
        pen.ellipse((x+dot-3, y-4, x+dot+3, y+2), fill="#56917e")


@lru_cache(maxsize=3)
def question_scene(index):
    image = background("What treatment changes", "Ask your care team about your recovery plan.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 764))
    point = heart(image, 133, 282, .99, treated=True)
    label(pen, point, (471, 648), "Treated section")
    pen.line((760, 333, 760, 692), fill=LINE, width=2)
    questions = ("What was treated?", "Which medicines should I take?", "When can I return to usual activities?")
    parts = (questions[0], "Which medicines\nshould I take?", "When can I return\nto usual activities?")
    for i, row in enumerate(parts[index].splitlines()):
        pen.text((818, 335+62*i), row, font=font(47, "heading"), fill=GREEN)
    conversation(pen, 1010, 534)
    return image


def p16(p):
    if p < .54:
        return blend_frames(treated_scene(), question_scene(0), smooth((p - .32) / .12))
    if p < .72:
        return blend_frames(question_scene(0), question_scene(1), smooth((p - .54) / .07))
    return blend_frames(question_scene(1), question_scene(2), smooth((p - .72) / .08))


def p17():
    image = background("Sources and production", "Find the complete source links in the video description.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 246, 1522, 775))
    pen.text((118, 289), "Coronary angioplasty and stent placement", font=font(40, "heading"), fill=GREEN)
    pen.line((119, 371, 1477, 371), fill=LINE, width=2)
    sources = (
        ("American Heart Association", "Patient guide to coronary angioplasty"),
        ("ACC · AHA · SCAI", "Coronary revascularization and heart disease guidelines"),
        ("NIH · National Heart, Lung, and Blood Institute", "Stent placement, recovery and living with a stent"),
        ("NHS · Guy’s and St Thomas’", "Angioplasty procedure and recovery guidance"),
    )
    for i, (organization, description) in enumerate(sources):
        x, y = 119+(i%2)*694, 410+(i//2)*99
        pen.text((x, y), organization, font=font(25, "semibold"), fill=INK)
        pen.text((x, y+40), description, font=font(22), fill=MUTED)
    pen.line((119, 622, 1477, 622), fill=LINE, width=2)
    pen.text((119, 662), "Original educational animation", font=font(25, "semibold"), fill=GREEN)
    pen.text((119, 706), "Alexander narration generated with ElevenLabs", font=font(23), fill=MUTED)
    pen.text((1477, 686), "Elysian Biomedical LLP", font=font(25, "semibold"), fill=GREEN, anchor="ra")
    file = OUT / "P17.png"
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(file, optimize=True)
    with Image.open(file) as check:
        assert check.size == (1920, 1080)
        check.verify()
    print(f"{file.name} 1920×1080", flush=True)


if __name__ == "__main__":
    clips = {"P13": (23, p13), "P14": (27, p14), "P15": (21, p15), "P16": (18, p16), "P17": None}
    for scene in sys.argv[1:] or clips:
        if scene == "P17":
            p17()
        else:
            encode(scene, *clips[scene])
