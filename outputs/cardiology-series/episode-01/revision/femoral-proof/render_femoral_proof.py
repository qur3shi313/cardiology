"""Render and decode the common femoral introducer exchange motion proof."""
from __future__ import annotations

from bisect import bisect_right
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
from random import Random
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


OUT = Path(__file__).resolve().parent
EPISODE = OUT.parents[1]
VIDEO = OUT / "femoral-access-motion-proof.mp4"
SHEET = OUT / "femoral-access-decoded-check.jpg"
FPS = 24
STOPS = (0, 3.55, 6.7, 10.1, 13.5, 17.15, 21)
SAMPLES = (3.26, 6.46, 9.85, 13.25, 16.88, 20.76)
STAGES = ("sheath_in", "short_out", "exchange_wire", "micro_out", "working_sheath", "working_dilator_out")
scene_list = json.loads((EPISODE / "production/scenes.json").read_text(encoding="utf-8-sig"))["femoral"]
scenes = {scene["stage"]: scene for scene in scene_list}
assert [scene["stage"] for scene in scene_list if scene["stage"] in STAGES] == list(STAGES)

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("wrist_art", OUT.parent / "wrist-proof/render_wrist_proof.py")
wrist_art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrist_art)
W, H = wrist_art.W, wrist_art.H
INK, MUTED, GREEN = wrist_art.INK, wrist_art.MUTED, wrist_art.GREEN
blend, smooth, bezier, curve = wrist_art.blend, wrist_art.smooth, wrist_art.bezier, wrist_art.curve
font, gradient = wrist_art.font, wrist_art.vertical_gradient
mask, overlay = wrist_art.shape_mask, wrist_art.flat_overlay
locator, tube = wrist_art.locator, wrist_art.tube

# The leg is to the left and the proximal common femoral artery is to the right.
# The puncture is on the anterior wall, upstream of the distal bifurcation.
ARTERIAL_ENTRY = (743, 564)
PATH = wrist_art.Track([
    (346, 267), ARTERIAL_ENTRY,
    *list(bezier(ARTERIAL_ENTRY, (767, 582), (800, 587), (839, 586)))[1:],
    *list(bezier((839, 586), (1004, 582), (1251, 563), (1478, 557)))[1:],
])
wrist_art.PATH = PATH
ENTRY = PATH.distance[1]
MICRO = ENTRY + 47
WORKING = ENTRY + 74
FINE_TIP = ENTRY + 196
EXCHANGE_TIP = ENTRY + 399

OUTLINE_TOP = curve((95, 514), [
    ((110, 463), (184, 449), (254, 431)),
    ((367, 403), (468, 409), (600, 387)),
    ((804, 347), (1047, 330), (1287, 330)),
    ((1398, 330), (1477, 334), (1520, 352)),
])
SKIN_EDGE = curve((95, 514), [
    ((191, 532), (275, 494), (353, 476)),
    ((477, 446), (589, 448), (735, 424)),
    ((984, 386), (1249, 381), (1519, 401)),
])
LOWER = curve((95, 514), [
    ((122, 576), (170, 638), (253, 671)),
    ((427, 740), (654, 750), (845, 732)),
    ((1046, 717), (1307, 707), (1522, 676)),
])
BODY = OUTLINE_TOP + list(reversed(LOWER))
TOP = OUTLINE_TOP + list(reversed(SKIN_EDGE))
SECTION = SKIN_EDGE + list(reversed(LOWER))

VESSEL = curve((147, 626), [
    ((251, 634), (377, 612), (475, 606)),
    ((565, 599), (652, 594), (743, 590)),
    ((985, 583), (1208, 562), (1519, 557)),
])
DEEP_BRANCH = curve((215, 674), [
    ((308, 667), (376, 630), (453, 614)),
    ((490, 606), (534, 606), (588, 599)),
])


def vessel(draw, points, scale):
    tones = (
        (-47, (129, 64, 68)), (-43, (163, 80, 80)), (-37, (209, 116, 107)),
        (-30, (171, 69, 77)), (-25, (111, 40, 56)), (-9, (137, 56, 69)),
        (15, (95, 38, 55)), (24, (137, 51, 67)), (31, (185, 86, 88)),
        (38, (204, 113, 103)), (43, (159, 75, 79)), (47, (110, 52, 61)),
    )
    for (a, first), (b, second) in zip(tones, tones[1:]):
        a, b = round(a * scale), round(b * scale)
        for offset in range(a, b):
            draw.polygon([(x, y + offset) for x, y in points] +
                         [(x, y + offset + 1) for x, y in reversed(points)],
                         fill=blend(first, second, (offset - a) / (b - a)))


def groin_locator(image):
    hips = curve((1315, 208), [
        ((1314, 225), (1310, 239), (1304, 256)),
        ((1299, 269), (1297, 288), (1302, 315)),
        ((1318, 317), (1336, 317), (1351, 316)),
        ((1358, 295), (1370, 279), (1377, 278)),
        ((1386, 281), (1395, 300), (1400, 316)),
        ((1417, 317), (1436, 317), (1451, 315)),
        ((1457, 288), (1454, 270), (1449, 256)),
        ((1442, 240), (1439, 226), (1438, 208)),
    ])
    overlay(image, (73, 110, 89), [(x + 1, y + 4) for x, y in hips], 64, 8)
    image.paste(gradient((250, 228, 206), (224, 168, 145)), (0, 0), mask(hips))
    pen = ImageDraw.Draw(image)
    pen.line(hips, fill=(172, 122, 103), width=1, joint="curve")
    pen.arc((1314, 238, 1367, 279), 32, 142, fill=(184, 126, 109), width=2)
    pen.arc((1387, 238, 1441, 279), 32, 142, fill=(184, 126, 109), width=2)
    pen.ellipse((1375, 226, 1381, 230), fill=(183, 128, 110))
    pen.line((1340, 265, 1340, 327, 1494, 327), fill=(40, 115, 92), width=2)
    pen.ellipse((1334, 259, 1346, 271), fill=(22, 113, 87), outline=(243, 250, 241), width=2)
    pen.text((1500, 315), "Right groin", font=font(16, "semibold"), fill=GREEN, anchor="rs")


@lru_cache(maxsize=1)
def background():
    image = gradient((244, 250, 245), (220, 233, 226))
    overlay(image, (255, 255, 251), [(0, 0), (1200, 0), (1030, 697), (0, 663)], 112, 105)
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((76, 57, 126, 107), 9, fill=(255, 255, 255))
    brand = ImageOps.fit(Image.open(wrist_art.LOGO).convert("RGB"), (46, 46), method=Image.Resampling.LANCZOS)
    image.paste(brand, (78, 59))
    pen.text((144, 62), "Elysian Biomedical LLP", font=font(24, "semibold"), fill=GREEN)
    pen.text((144, 93), "Cardiology Education Series", font=font(18), fill=MUTED)
    pen.text((1518, 65), "RIGHT GROIN", font=font(21, "semibold"), fill=GREEN, anchor="rt")
    pen.text((1518, 94), "Anatomical illustration", font=font(17), fill=MUTED, anchor="rt")
    pen.line((77, 128, 1522, 128), fill=(179, 204, 191), width=1)
    pen.text((76, 151), "How the femoral sheath is placed", font=font(57, "heading"), fill=INK)
    groin_locator(image)

    overlay(image, (42, 67, 51), [(x + 13, y + 25) for x, y in BODY], 49, 25)
    image.paste(gradient((250, 211, 177), (150, 83, 75)), (0, 0), mask(BODY))
    image.paste(gradient((255, 229, 204), (195, 128, 111)), (0, 0), mask(TOP))
    image.paste(gradient((235, 171, 145), (124, 68, 69)), (0, 0), mask(SECTION))
    upper_fat = [(x, y + 9) for x, y in SKIN_EDGE]
    lower_fat = [(x, y + 58 + 15 * x / W) for x, y in SKIN_EDGE]
    overlay(image, (222, 155, 119), upper_fat + list(reversed(lower_fat)), 102, 8)
    overlay(image, (255, 223, 193), [(205, 458), (579, 402), (940, 350), (1405, 353),
                                    (1460, 369), (1036, 390), (614, 425), (285, 478)], 115, 21)
    overlay(image, (106, 54, 61), [(145, 562), (482, 649), (823, 665), (1482, 630),
                                  (1494, 677), (852, 727), (444, 710), (195, 646)], 77, 22)

    fibers = Image.new("RGBA", (W, H))
    fiber_pen = ImageDraw.Draw(fibers)
    random = Random(113)
    for _ in range(2600):
        x = random.randrange(100, 1518)
        y = random.randrange(370, 732)
        fiber_pen.line((x, y, x + random.uniform(1, 9), y + random.uniform(-1.4, 1.6)),
                       fill=(254, 219, 184, random.randrange(7, 22)), width=1)
    composite = Image.alpha_composite(image.convert("RGBA"), fibers.filter(ImageFilter.GaussianBlur(.48))).convert("RGB")
    image.paste(composite, (0, 0), mask(BODY))
    pen = ImageDraw.Draw(image)
    pen.line(OUTLINE_TOP, fill=(222, 177, 153), width=2, joint="curve")
    pen.line(SKIN_EDGE, fill=(156, 93, 84), width=12, joint="curve")
    pen.line([(x, y - 4) for x, y in SKIN_EDGE], fill=(253, 205, 171), width=4, joint="curve")
    pen.line([(x, y + 5) for x, y in SKIN_EDGE], fill=(213, 151, 124), width=2, joint="curve")
    pen.line(LOWER, fill=(107, 60, 61), width=2, joint="curve")
    vessel(pen, DEEP_BRANCH, .56)
    vessel(pen, VESSEL, 1)
    pen.ellipse((1500, 512, 1537, 604), fill=(169, 74, 86), outline=(111, 48, 59), width=2)
    pen.ellipse((1504, 520, 1533, 596), fill=(112, 43, 59), outline=(218, 115, 107), width=2)
    pen.arc((1509, 527, 1529, 589), 88, 271, fill=(231, 128, 116), width=2)

    pen.line((1264, 591, 1324, 761, 1516, 761), fill=(101, 108, 93), width=2, joint="curve")
    pen.ellipse((1259, 586, 1269, 596), fill=(248, 230, 208), outline=(88, 65, 58), width=1)
    pen.text((1516, 773), "Common femoral artery", font=font(21, "semibold"), fill=INK, anchor="rt")
    pen.text((1516, 806), "Toward the heart →", font=font(17), fill=MUTED, anchor="rt")
    pen.line((394, 645, 453, 708, 587, 708), fill=(251, 221, 199), width=1, joint="curve")
    pen.ellipse((390, 641, 398, 649), fill=(251, 227, 207), outline=(91, 57, 54), width=1)
    pen.text((466, 711), "Femoral branches", font=font(17, "semibold"), fill=(255, 234, 220))
    return image.convert("RGBA")


def wire(draw, start, end, *, fine=False, hook=False):
    outer, core = (2.8, 1.75) if fine else (4.1, 2.7)
    tube(draw, start, end, outer, (103, 72, 42, 255))
    tube(draw, start, end, core, (244, 213, 144, 255), shift=-.35)
    tube(draw, start, end, .68, (255, 242, 190, 255), shift=-1.0)
    if hook and end > ENTRY + 108:
        x, y = PATH.at(end)
        draw.arc((x - 15, y - 15, x + 9, y + 2), 269, 91, fill=(93, 65, 42, 255), width=6)
        draw.arc((x - 15, y - 15, x + 9, y + 2), 269, 91, fill=(248, 220, 149, 255), width=3)


def introducer(draw, tip, *, working=False):
    radius = 19 if working else 12
    length = 338 if working else 303
    hub = tip - length
    edge, core, clear, shine = ((9, 72, 66, 222), (54, 159, 141, 164), (152, 219, 194, 115), (219, 246, 224, 228)) if working else ((22, 77, 96, 236), (62, 141, 165, 172), (156, 207, 218, 124), (222, 244, 239, 229))
    tube(draw, hub, tip, radius, edge, taper=16)
    tube(draw, hub, tip, radius - 2.7, core, taper=15)
    tube(draw, hub, tip - 3, radius * .56, clear, shift=-1.4, taper=12)
    tube(draw, hub + 14, tip - 6, 1.5, shine, shift=-radius * .62, taper=13)
    tube(draw, hub - 37, hub + 20, radius + 5, edge[:3] + (255,))
    tube(draw, hub - 32, hub + 17, radius + 1, core[:3] + (255,), shift=-1.8)
    tube(draw, hub - 28, hub + 13, 2.4, shine, shift=-radius * .74)
    if working:
        x, y = PATH.uv(hub + 6, -radius)
        draw.line(((x, y), (x + 15, y - 24), (x + 34, y - 30)), fill=edge, width=10, joint="curve")
        draw.line(((x, y), (x + 15, y - 24), (x + 34, y - 30)), fill=core[:3] + (255,), width=5, joint="curve")
        draw.line(((x + 32, y - 30), (x + 41, y - 33)), fill=shine, width=8)


def dilator(draw, tip, *, working=False):
    radius = 11 if working else 6.6
    length = 422 if working else 375
    start = tip - length
    tube(draw, start, tip, radius, (150, 136, 115, 225), taper=28)
    tube(draw, start, tip, radius - 1.3, (238, 226, 202, 237), shift=-.5, taper=28)
    tube(draw, start + 6, tip - 3, 1.2, (255, 249, 229, 237), shift=-radius * .46, taper=19)
    tube(draw, start - 11, start + 37, radius + 4, (213, 200, 168, 255))
    tube(draw, start - 5, start + 33, 1.9, (255, 248, 216, 255), shift=-radius * .70)


@lru_cache(maxsize=1)
def tool_alpha():
    alpha = Image.new("L", (1, H))
    alpha.putdata([min(255, max(0, (y - 226) * 11)) for y in range(H)])
    return alpha.resize((W, H))


def frame(t):
    stage = min(len(STAGES) - 1, bisect_right(STOPS, t) - 1)
    start, stop = STOPS[stage:stage + 2]
    p = smooth((t - start - .08) / (stop - start - .62))
    layer = Image.new("RGBA", (W, H))
    pen = ImageDraw.Draw(layer)
    callouts = []

    if stage == 0:
        tip = MICRO - (1 - p) * 219
        introducer(pen, tip)
        dilator(pen, tip + 27)
        wire(pen, -63, FINE_TIP, fine=True)
        if p > .40:
            callouts = [(808, 344, "Temporary introducer", tip - 72),
                        (1060, 426, "Fine access wire", FINE_TIP - 3)]
    elif stage == 1:
        introducer(pen, MICRO)
        if p < .995:
            dilator(pen, MICRO + 27 - 627 * p)
            wire(pen, -63 - 714 * p, FINE_TIP - 729 * p, fine=True)
        callouts = [(845, 362, "Outer introducer stays", MICRO - 32)]
    elif stage == 2:
        introducer(pen, MICRO)
        tip = 209 + (EXCHANGE_TIP - 209) * p
        wire(pen, -63, tip, hook=True)
        if p > .45:
            callouts = [(1038, 412, "Larger exchange wire", tip - 9)]
    elif stage == 3:
        if p < .995:
            introducer(pen, MICRO - 573 * p)
        wire(pen, -63, EXCHANGE_TIP, hook=True)
        callouts = [(1040, 416, "Exchange wire stays", EXCHANGE_TIP - 24)]
    elif stage == 4:
        tip = WORKING - (1 - p) * 222
        introducer(pen, tip, working=True)
        dilator(pen, tip + 31, working=True)
        wire(pen, -63, EXCHANGE_TIP, hook=True)
        if p > .48:
            callouts = [(812, 352, "Working sheath", tip - 64), (1088, 413, "Inner dilator", tip + 19)]
    else:
        introducer(pen, WORKING, working=True)
        if p < .995:
            dilator(pen, WORKING + 31 - 642 * p, working=True)
            wire(pen, -63 - 905 * p, EXCHANGE_TIP - 920 * p, hook=True)
        callouts = [(868, 361, "Working sheath stays", WORKING - 43)]

    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), tool_alpha()))
    image = Image.alpha_composite(background(), layer).convert("RGB")
    pen = ImageDraw.Draw(image)
    for x, y, label, point in callouts:
        locator(pen, x, y, label, PATH.at(point))
    scene = scenes[STAGES[stage]]
    pen.text((77, 769), scene["title"], font=font(29, "semibold"), fill=GREEN)
    pen.text((77, 804), scene["detail"], font=font(22), fill=MUTED)
    x0, x1, y = 77, 1522, 853
    pen.line((x0, y, x1, y), fill=(172, 193, 181), width=2)
    pen.line((x0, y, x0 + (x1 - x0) * t / STOPS[-1], y), fill=(0, 115, 85), width=4)
    for mark in STOPS[1:-1]:
        x = x0 + (x1 - x0) * mark / STOPS[-1]
        pen.line((x, y - 5, x, y + 5), fill=(128, 156, 142), width=2)
    return image


def render():
    command = [str(wrist_art.FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an",
               "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-c:v", "libx264",
               "-preset", "fast", "-crf", "16", "-movflags", "+faststart", str(VIDEO)]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as ffmpeg:
        for i in range(STOPS[-1] * FPS):
            ffmpeg.stdin.write(frame(i / FPS).tobytes())
        ffmpeg.stdin.close()
        if ffmpeg.wait():
            raise RuntimeError("FFmpeg encoding failed")


def validate_and_sheet():
    ffmpeg = str(wrist_art.FFMPEG)
    check = subprocess.run([ffmpeg, "-hide_banner", "-xerror", "-i", str(VIDEO), "-f", "null", "-"],
                           check=True, capture_output=True, text=True).stderr
    assert "1920x1080" in check and "Audio:" not in check and "00:00:21.00" in check, check
    sample_frames = [round(t * FPS) for t in SAMPLES]
    select = "+".join(f"eq(n\\,{i})" for i in sample_frames)
    width, height = 520, 292
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", str(VIDEO), "-vf", f"select={select},scale={width}:{height}",
                          "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    step = width * height * 3
    assert len(raw) == step * len(SAMPLES), (len(raw), step * len(SAMPLES))
    sheet = Image.new("RGB", (1600, 637), (224, 236, 228))
    pen = ImageDraw.Draw(sheet)
    for index, sample in enumerate(sample_frames):
        x, y = 10 + (index % 3) * 530, 12 + (index // 3) * 310
        panel = Image.frombytes("RGB", (width, height), raw[index * step:(index + 1) * step])
        sheet.paste(panel, (x, y))
        pen.text((x + 8, y + 294), f"{sample / FPS:05.2f}s", font=font(14), fill=MUTED)
    sheet.save(SHEET, quality=94)
    print(f"Decoded {len(SAMPLES)} review frames from {VIDEO.name}")


if __name__ == "__main__":
    render()
    validate_and_sheet()
