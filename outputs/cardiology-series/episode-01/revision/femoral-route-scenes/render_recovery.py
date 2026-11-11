"""Render femoral catheter withdrawal, manual pressure and monitored recovery."""
from __future__ import annotations

from functools import lru_cache
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
from render_route import (
    CATH_TIP, ENTRY, GREEN, H, INK, MUTED, PATH, W, WORKING, chrome, composite_tools,
    curve, cutaway, draw_catheter, font, gradient, overlay, proof, render_group, smooth, titles,
)


STAGES = ("catheter_out", "remove", "closure", "aftercare")


def gloved_pressure(draw, progress):
    lift = round(86 * (1 - smooth(progress)))
    glove = curve((1045, 272), [
        ((1004, 271), (971, 272), (951, 285)),
        ((917, 308), (889, 333), (844, 338)),
        ((791, 347), (708, 351), (659, 354)),
        ((631, 356), (609, 358), (605, 370)),
        ((602, 381), (618, 386), (642, 386)),
        ((622, 387), (607, 389), (607, 401)),
        ((608, 413), (631, 414), (654, 413)),
        ((683, 413), (744, 411), (793, 406)),
        ((853, 401), (894, 389), (936, 363)),
        ((973, 342), (1014, 339), (1047, 343)),
    ])
    draw.rounded_rectangle((578, 401 - lift, 808, 425 - lift), 10,
                           fill=(244, 244, 226, 255), outline=(211, 216, 197, 255), width=3)
    shape = [(x, y - lift) for x, y in glove]
    draw.polygon(shape, fill=(102, 174, 162, 255))
    draw.line(shape, fill=(61, 130, 120, 255), width=3, joint="curve")
    draw.line(((638, 383 - lift), (711, 381 - lift), (779, 369 - lift)), fill=(161, 207, 189, 255), width=3, joint="curve")
    draw.line(((657, 401 - lift), (725, 397 - lift), (790, 387 - lift)), fill=(70, 146, 135, 255), width=2, joint="curve")
    draw.line(((986, 289 - lift), (997, 333 - lift)), fill=(177, 218, 197, 255), width=4)


def closure_stitch(draw, progress):
    x, y = PATH.at(ENTRY - 4)
    height = round(24 * (1 - smooth(progress)))
    stitch = curve((x - 21, y - 3), [
        ((x - 15, y - 12), (x - 17, y - 24), (x - 8, y - 27 - height)),
        ((x - 1, y - 31 - height), (x + 4, y - 31 - height), (x + 10, y - 27 - height)),
        ((x + 18, y - 24), (x + 18, y - 10), (x + 21, y - 3)),
    ])
    draw.line(stitch, fill=(35, 81, 74, 255), width=7, joint="curve")
    draw.line(stitch, fill=(128, 212, 185, 255), width=3, joint="curve")
    draw.ellipse((x - 4, y - 33 - height, x + 5, y - 24 - height),
                 fill=(106, 192, 166, 255), outline=(33, 88, 77, 255), width=2)


def foot_check(image, pulse):
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1109, 223, 1516, 424), 15, fill=(237, 247, 237), outline=(149, 182, 163), width=2)
    draw.text((1128, 239), "Check circulation in the leg", font=font(20, "semibold"), fill=GREEN)
    shape = curve((1290, 275), [
        ((1295, 296), (1293, 322), (1287, 332)),
        ((1276, 344), (1245, 347), (1225, 358)),
        ((1212, 366), (1204, 373), (1212, 382)),
        ((1224, 394), (1254, 388), (1281, 388)),
        ((1320, 389), (1357, 391), (1384, 385)),
        ((1404, 379), (1414, 365), (1403, 351)),
        ((1387, 332), (1378, 306), (1383, 275)),
    ])
    draw.polygon(shape, fill=(233, 188, 164))
    draw.line(shape, fill=(163, 123, 112), width=2, joint="curve")
    draw.arc((1332, 321, 1379, 363), 22, 125, fill=(182, 130, 115), width=2)
    size = round(8 + 8 * pulse)
    draw.ellipse((1266 - size, 350 - size, 1266 + size, 350 + size), outline=(41, 128, 97), width=2)
    draw.ellipse((1262, 346, 1270, 354), fill=(31, 116, 91))


def closure_frame(stage, progress):
    layer = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(layer)
    if stage == "catheter_out":
        proof.introducer(draw, WORKING, working=True)
        tip = CATH_TIP - (CATH_TIP + 132) * progress
        draw_catheter(draw, tip - 1700, tip)
    elif stage == "remove":
        withdrawal = smooth(progress / .60)
        if withdrawal < 1:
            proof.introducer(draw, WORKING - 668 * withdrawal, working=True)
        if progress > .48:
            gloved_pressure(draw, (progress - .48) / .38)
    elif stage == "closure":
        closure_stitch(draw, progress)

    image = composite_tools(cutaway(), layer)
    pen = titles(image, stage)
    if stage == "catheter_out":
        proof.locator(pen, 868, 370, "Working sheath stays", PATH.at(WORKING - 41))
        if progress < .30:
            proof.locator(pen, 1050, 441, "Diagnostic catheter", PATH.at(tip - 10))
    elif stage == "remove" and progress > .60:
        proof.locator(pen, 1085, 458, "Firm pressure at the groin", (744, 412))
    elif stage == "closure":
        pen.text((78, 224), "Alternative to manual pressure", font=font(22, "semibold"), fill=GREEN)
        proof.locator(pen, 862, 449, "Closure stitch example", PATH.at(ENTRY - 6))
        if progress > .36:
            locator_top = (1285, 200, 1463, 226)
            image.paste(chrome().crop(locator_top), locator_top[:2])
            foot_check(image, smooth((progress - .36) / .64))
    return image


HEAD = curve((322, 449), [
    ((286, 442), (268, 426), (269, 399)),
    ((268, 378), (280, 357), (308, 351)),
    ((329, 345), (348, 353), (353, 367)),
    ((361, 370), (361, 379), (358, 385)),
    ((374, 388), (375, 395), (365, 399)),
    ((368, 414), (359, 428), (348, 431)),
    ((344, 447), (353, 453), (369, 458)),
])
GOWN = curve((359, 445), [
    ((394, 424), (427, 428), (468, 443)),
    ((516, 456), (599, 454), (652, 443)),
    ((684, 440), (706, 461), (728, 476)),
    ((713, 494), (717, 530), (730, 545)),
    ((622, 553), (492, 552), (391, 536)),
    ((361, 527), (348, 489), (359, 445)),
])
LEG = curve((682, 475), [
    ((742, 466), (813, 469), (876, 483)),
    ((952, 488), (1032, 485), (1097, 497)),
    ((1138, 506), (1195, 508), (1235, 503)),
    ((1254, 499), (1253, 481), (1259, 470)),
    ((1268, 460), (1277, 471), (1278, 483)),
    ((1278, 498), (1289, 507), (1290, 529)),
    ((1287, 548), (1266, 548), (1242, 544)),
    ((1149, 543), (1055, 540), (951, 539)),
    ((849, 537), (765, 548), (683, 540)),
])


@lru_cache(maxsize=1)
def recovery_background():
    image = chrome().copy()
    overlay(image, (81, 112, 95), [(149, 555), (1399, 555), (1461, 720), (109, 720)], 52, 26)
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((129, 546, 1450, 626), 28, fill=(170, 198, 181), outline=(106, 148, 132), width=2)
    pen.rounded_rectangle((124, 540, 1454, 585), 21, fill=(238, 245, 232), outline=(167, 194, 178), width=2)
    pen.line((174, 606, 192, 710), fill=(123, 162, 146), width=14)
    pen.line((1390, 606, 1375, 710), fill=(123, 162, 146), width=14)
    pen.rounded_rectangle((211, 431, 381, 546), 25, fill=(250, 249, 230), outline=(194, 207, 186), width=2)
    pen.polygon([(x + 12, y - 8) for x, y in LEG], fill=(215, 166, 148))
    pen.polygon(LEG, fill=(236, 190, 166))
    pen.line(LEG, fill=(174, 131, 117), width=2, joint="curve")
    pen.polygon(GOWN, fill=(123, 183, 166))
    pen.line(GOWN, fill=(74, 136, 124), width=2, joint="curve")
    pen.line(((382, 453), (432, 466), (479, 473), (520, 482), (565, 478)),
             fill=(165, 208, 186), width=3, joint="curve")
    pen.polygon(HEAD, fill=(233, 189, 167))
    pen.line(HEAD, fill=(180, 137, 123), width=2, joint="curve")
    hair = curve((270, 408), [((257, 381), (270, 358), (297, 350)),
                              ((320, 343), (342, 348), (350, 363)),
                              ((336, 359), (321, 363), (308, 371)),
                              ((294, 384), (289, 405), (288, 421)),
                              ((280, 420), (273, 414), (270, 408))])
    pen.polygon(hair, fill=(114, 99, 87))
    pen.line((342, 386, 351, 385), fill=(150, 117, 103), width=2)
    pen.rounded_rectangle((709, 478, 759, 511), 8, fill=(250, 241, 211), outline=(172, 161, 127), width=2)
    pen.rounded_rectangle((717, 485, 750, 502), 4, fill=(249, 246, 226), outline=(208, 193, 151), width=1)
    return image


def recovery_frame(progress):
    image = recovery_background().copy()
    pen = titles(image, "aftercare")
    proof.locator(pen, 752, 365, "Groin dressing", (734, 494))
    proof.locator(pen, 1081, 593, "Leg kept straight as advised", (1009, 527))
    if progress < .54:
        pen.rounded_rectangle((1033, 242, 1460, 413), 16, fill=(233, 244, 232), outline=(144, 180, 160), width=2)
        pen.text((1054, 261), "What staff monitor", font=font(24, "semibold"), fill=GREEN)
        pen.text((1054, 309), "Pulse and blood pressure", font=font(21), fill=INK)
        pen.text((1054, 349), "Groin site and leg circulation", font=font(21), fill=INK)
        pulse = ((1344, 286), (1363, 286), (1374, 277), (1384, 303), (1394, 274), (1403, 287), (1433, 287))
        pen.line(pulse, fill=(71, 149, 111), width=3, joint="curve")
    else:
        pen.rounded_rectangle((1011, 226, 1460, 419), 16, fill=(234, 244, 232), outline=(144, 180, 160), width=2)
        pen.text((1032, 245), "Before you go home", font=font(24, "semibold"), fill=GREEN)
        for i, label in enumerate(("What did the angiogram show?", "When can I walk, lift or drive?", "Who do I contact with questions?")):
            y = 301 + 36 * i
            pen.ellipse((1035, y - 4, 1043, y + 4), fill=(73, 150, 115))
            pen.text((1056, y), label, font=font(20), fill=INK, anchor="lm")
    return image


def frame(stage, progress):
    return recovery_frame(progress) if stage == "aftercare" else closure_frame(stage, progress)


if __name__ == "__main__":
    render_group("femoral-f24-f27-withdrawal-recovery", STAGES, frame,
                 [(0, .27), (0, .92), (1, .92), (2, .79), (3, .30), (3, .92)])
