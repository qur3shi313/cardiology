"""Render the four steps before the femoral introducer exchange."""
from __future__ import annotations

from math import hypot
from random import Random
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
from render_route import (
    ENTRY, GREEN, H, MUTED, PATH, W, chrome, composite_tools, cutaway, font,
    proof, render_group, smooth, titles, tube, wire,
)


STAGES = ("site", "needle", "short_wire", "needle_out")


def needle(draw, tip):
    hub = tip - 297
    tube(draw, hub, tip, 5.8, (55, 85, 84, 255), taper=23)
    tube(draw, hub, tip, 4.6, (173, 193, 188, 255), taper=23)
    tube(draw, hub + 3, tip - 4, 1.05, (249, 251, 236, 255), shift=-2.1)
    tube(draw, hub - 57, hub + 17, 12.2, (18, 83, 98, 255))
    tube(draw, hub - 49, hub + 16, 9.1, (61, 142, 160, 255), shift=-1.5)
    tube(draw, hub - 45, hub + 10, 1.9, (179, 229, 231, 255), shift=-5.9)


def probe(draw, x, y):
    draw.polygon(((x - 21, y), (x + 23, y), (x + 83, y + 163), (x - 84, y + 164)), fill=(113, 202, 170, 39))
    draw.rounded_rectangle((x - 48, y - 67, x + 42, y - 6), 20, fill=(239, 247, 240, 255),
                           outline=(84, 123, 114, 255), width=3)
    draw.rounded_rectangle((x - 32, y - 86, x + 24, y - 45), 17, fill=(244, 248, 241, 255),
                           outline=(102, 132, 124, 255), width=2)
    draw.rounded_rectangle((x - 36, y - 17, x + 31, y + 5), 8, fill=(82, 133, 120, 255),
                           outline=(63, 111, 103, 255), width=2)


def ultrasound(image, needle_progress=None):
    draw = ImageDraw.Draw(image)
    rect = (1124, 218, 1515, 410)
    draw.rounded_rectangle(rect, 14, fill=(31, 53, 55), outline=(101, 142, 130), width=2)
    draw.text((1140, 230), "Ultrasound illustration", font=font(18, "semibold"), fill=(224, 240, 228))
    sector = ((1191, 271), (1456, 271), (1467, 367), (1177, 367))
    draw.polygon(sector, fill=(72, 88, 88))
    random = Random(216)
    for _ in range(430):
        x = random.randrange(1190, 1454)
        y = random.randrange(274, 365)
        v = random.randrange(64, 140)
        draw.point((x, y), fill=(v, v + 7, v + 7))
    draw.line(((1193, 282), (1247, 289), (1301, 281), (1383, 288), (1449, 284)), fill=(180, 193, 188), width=3)
    draw.ellipse((1245, 299, 1336, 352), fill=(39, 59, 60), outline=(194, 217, 206), width=4)
    draw.ellipse((1252, 304, 1329, 347), outline=(153, 186, 172), width=1)
    draw.ellipse((1361, 316, 1431, 350), fill=(47, 65, 66), outline=(138, 157, 150), width=2)
    if needle_progress is not None:
        a = (1195, 277)
        target = (1291, 321)
        tip = tuple(round(s + (e - s) * needle_progress) for s, e in zip(a, target))
        draw.line((a, tip), fill=(247, 247, 226), width=3)
        if needle_progress > .5:
            draw.ellipse((tip[0] - 3, tip[1] - 3, tip[0] + 3, tip[1] + 3), fill=(244, 214, 145))
    draw.text((1242, 381), "Artery", font=font(17, "semibold"), fill=(226, 238, 224))
    draw.text((1364, 381), "Vein", font=font(17), fill=(180, 203, 194))


def prep(image, progress):
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((1124, 218, 1515, 409), 14, fill=(236, 245, 234, 255), outline=(151, 177, 158, 255), width=2)
    draw.text((1140, 233), "Prepare the access site", font=font(19, "semibold"), fill=GREEN)
    draw.rounded_rectangle((1151, 271, 1487, 356), 12, fill=(106, 172, 156, 255), outline=(63, 135, 115, 255), width=2)
    draw.ellipse((1270, 283, 1380, 345), fill=(238, 186, 162, 255), outline=(251, 212, 184, 255), width=3)
    if progress < .73:
        x = 1310 + round(28 * smooth((progress - .56) / .17))
        draw.rounded_rectangle((x - 25, 295, x + 25, 320), 5, fill=(251, 248, 230, 255), outline=(215, 214, 195, 255), width=2)
        draw.text((1151, 375), "Clean skin and sterile drape", font=font(17), fill=MUTED)
    else:
        draw.line((1228, 290, 1333, 322), fill=(87, 111, 101, 255), width=2)
        draw.line((1247, 295, 1300, 311), fill=(245, 250, 236, 255), width=11)
        draw.line((1247, 295, 1300, 311), fill=(115, 159, 144, 255), width=3)
        draw.line((1228, 288, 1250, 296), fill=(80, 129, 111, 255), width=6)
        draw.ellipse((1328, 317, 1338, 327), outline=(24, 113, 87, 255), width=2)
        draw.text((1151, 375), "Local anaesthetic at the skin", font=font(17), fill=MUTED)


def pelvic_xray(image, progress):
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1124, 218, 1515, 410), 14, fill=(30, 49, 51), outline=(101, 140, 126), width=2)
    draw.text((1140, 232), "Fluoroscopy illustration", font=font(18, "semibold"), fill=(225, 240, 229))
    draw.line((1318, 264, 1318, 352), fill=(112, 130, 128), width=20)
    for side in (-1, 1):
        x = 1318 + side * 102
        draw.ellipse((x - 40, 280, x + 40, 354), outline=(137, 151, 147), width=11)
        draw.ellipse((x - 21, 325, x + 21, 363), outline=(172, 180, 174), width=8)
        draw.line((x + side * 6, 359, x + side * 14, 379), fill=(137, 151, 147), width=18)
    course = ((1210, 379), (1223, 352), (1259, 331), (1290, 318), (1317, 296), (1317, 265))
    length = [0.0]
    for a, b in zip(course, course[1:]):
        length.append(length[-1] + hypot(b[0] - a[0], b[1] - a[1]))
    shown = length[-1] * (.42 + .55 * smooth((progress - .58) / .42))
    section = [course[0]]
    for a, b, d0, d1 in zip(course, course[1:], length, length[1:]):
        t = max(0.0, min(1.0, (shown - d0) / (d1 - d0)))
        section.append(tuple(x + (y - x) * t for x, y in zip(a, b)))
    draw.line(section, fill=(245, 234, 207), width=3, joint="curve")
    draw.text((1337, 382), "Main iliac artery", font=font(16, "semibold"), fill=(225, 240, 229))


def entry_frame(stage, progress):
    layer = Image.new("RGBA", (W, H))
    pen = ImageDraw.Draw(layer)
    needle_tip = None
    if stage == "site" and progress < .56:
        x = round(666 + 101 * smooth(progress / .56))
        probe(pen, x, 409)
    elif stage == "needle":
        needle_tip = -20 + (ENTRY + 20) * progress
        needle(pen, needle_tip)
    elif stage == "short_wire":
        needle(pen, ENTRY)
        fine_tip = ENTRY - 89 + (proof.FINE_TIP - ENTRY + 89) * progress
        wire(pen, -63, fine_tip, fine=True)
    elif stage == "needle_out":
        needle(pen, ENTRY - 602 * progress)
        wire(pen, -63, proof.FINE_TIP, fine=True)

    image = composite_tools(cutaway(), layer)
    if stage in ("site", "needle") or (stage == "short_wire" and progress > .58):
        locator_top = (1285, 200, 1463, 221)
        image.paste(chrome().crop(locator_top), locator_top[:2])
    pen = titles(image, stage)
    if stage == "site":
        if progress < .56:
            ultrasound(image)
            proof.locator(pen, 847, 440, "Entry above the arterial division", PATH.at(ENTRY + 24))
        else:
            prep(image, progress)
    elif stage == "needle":
        ultrasound(image, progress)
        if progress > .58:
            proof.locator(pen, 847, 439, "Needle tip", PATH.at(needle_tip - 4))
    elif stage == "short_wire":
        if progress > .58:
            pelvic_xray(image, progress)
            proof.locator(pen, 926, 435, "Fine access wire", PATH.at(fine_tip - 4))
    elif stage == "needle_out":
        proof.locator(pen, 953, 439, "Fine wire stays", PATH.at(proof.FINE_TIP - 8))
    return image


if __name__ == "__main__":
    render_group("femoral-f04-f07-arterial-entry", STAGES, entry_frame,
                 [(0, .28), (0, .92), (1, .92), (2, .92), (3, .43), (3, .92)])
