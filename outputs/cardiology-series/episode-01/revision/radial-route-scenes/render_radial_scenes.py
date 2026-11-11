"""Render narrated-timeline picture clips for the right radial coronary route."""
from __future__ import annotations

import argparse
import importlib.util
import json
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter


OUT = Path(__file__).resolve().parent
REVISION = OUT.parent
EPISODE = REVISION.parent
W, H, FPS = 1600, 900, 30
sys.dont_write_bytecode = True


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wrist = load_module("wrist_art", REVISION / "wrist-proof" / "render_wrist_proof.py")
vascular = load_module("vascular_art", EPISODE / "production" / "vascular_art.py")
INK = wrist.INK
GREEN = wrist.GREEN
MUTED = wrist.MUTED
SHEATH_NOSE = wrist.ASSEMBLY_NOSE
WIRE_END = wrist.NEEDLE_DISTANCE + 510
WIRE_LENGTH = WIRE_END + 92
CATHETER_END = WIRE_END - 46
CATHETER_LENGTH = 1110
CATHETER = (68, 141, 139)
SCENE_TITLES = {
    4: "Find the radial artery",
    10: "The long guidewire",
    11: "The diagnostic catheter",
    12: "From the wrist to the aorta",
    19: "The catheter comes out",
    20: "Position the compression band",
    21: "Check the wrist band",
    22: "Recovery and discharge",
}
SCENE_NAMES = {
    4: "find-radial-artery",
    10: "diagnostic-guidewire",
    11: "diagnostic-catheter",
    12: "wrist-to-aorta",
    19: "withdraw-diagnostic-catheter",
    20: "remove-sheath-compress",
    21: "check-wrist-band",
    22: "recovery-and-discharge",
}


def color(tone, alpha=255):
    return (*tone, alpha)


def ease_time(t, start, stop):
    return wrist.smooth((t - start) / (stop - start))


@lru_cache(maxsize=1)
def paper():
    image = wrist.vertical_gradient((244, 250, 245), (220, 233, 226))
    wrist.flat_overlay(image, (255, 255, 251),
                       [(0, 0), (1220, 0), (1025, 694), (0, 663)], 112, 105)
    return image


@lru_cache(maxsize=12)
def plate(scene, closeup):
    image = wrist.background().copy() if closeup else paper().copy()
    if closeup:
        # Clear only the previous proof heading and preserve the inset.
        image.paste(paper().crop((0, 138, 1185, 214)), (0, 138))
    else:
        image.paste(wrist.background().crop((0, 0, W, 130)), (0, 0))
    d = ImageDraw.Draw(image)
    d.text((76, 151), SCENE_TITLES[scene], font=wrist.font(57, "heading"), fill=INK)
    return image


def clean_top(layer):
    layer.paste((0, 0, 0, 0), (0, 0, W, 210))
    for row in range(210, 225):
        strip = layer.crop((0, row, W, row + 1))
        strip.putalpha(strip.getchannel("A").point(lambda value: round(value * (row - 210) / 15)))
        layer.paste(strip, (0, row))


def composite(image, layer):
    clean_top(layer)
    return Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")


def footer(draw, primary, secondary):
    draw.text((76, 751), primary, font=wrist.font(42, "semibold"), fill=GREEN)
    draw.text((76, 804), secondary, font=wrist.font(24), fill=MUTED)
    draw.line((76, 852, 1522, 852), fill=(168, 190, 177), width=2)


def catheter(d, end):
    start = end - CATHETER_LENGTH
    wrist.tube(d, start, end, 12.7, (19, 72, 70, 255))
    wrist.tube(d, start, end, 10.4, color(CATHETER))
    wrist.tube(d, start, end - 2, 5.5, (161, 209, 197, 236), shift=-.4)
    wrist.tube(d, start, end - 1, 1.8, (232, 249, 232, 237), shift=-6.5)
    x, y = wrist.PATH.at(end)
    d.ellipse((x - 2.4, y - 2.4, x + 2.4, y + 2.4), fill=(33, 82, 72, 255))


def tools_at_wrist(scene, t):
    base = plate(scene, True)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    wrist.assembly(layer, SHEATH_NOSE, inner=False)
    if scene == 10:
        end = -188 + (WIRE_END + 188) * ease_time(t, .52, 7.35)
        wrist.wire(d, end - WIRE_LENGTH, end)
        result = composite(base, layer)
        pen = ImageDraw.Draw(result)
        if end > SHEATH_NOSE + 65:
            wrist.locator(pen, 1034, 358, "Long guidewire", wrist.PATH.at(end - 4))
        footer(pen, "Guidewire through the sheath", "The team tracks its position with live X-ray.")
        return result

    if scene == 11:
        end = -188 + (CATHETER_END + 188) * ease_time(t, .22, 5.22)
        catheter(d, end)
        wrist.wire(d, WIRE_END - WIRE_LENGTH, WIRE_END)
        result = composite(base, layer)
        pen = ImageDraw.Draw(result)
        if end > SHEATH_NOSE + 50:
            wrist.locator(pen, 1045, 363, "Diagnostic catheter", wrist.PATH.at(end - 18))
        wrist.locator(pen, 719, 365, "Sheath stays", wrist.PATH.at(SHEATH_NOSE - 136))
        footer(pen, "Catheter over the wire", "The short sheath stays at the wrist.")
        return result

    end = CATHETER_END - (CATHETER_END + 188) * ease_time(t, .45, 6.05)
    catheter(d, end)
    result = composite(base, layer)
    pen = ImageDraw.Draw(result)
    if end > SHEATH_NOSE + 45:
        wrist.locator(pen, 1043, 362, "Catheter withdrawing", wrist.PATH.at(end - 15))
    wrist.locator(pen, 787, 364, "Sheath stays", wrist.PATH.at(SHEATH_NOSE - 155))
    footer(pen, "Catheter out first", "The team leaves the short sheath at the access site.")
    return result


def point_map(point):
    x, y = point
    return 75 + 1.22 * x, 214 + 1.14 * y


ROUTE = wrist.Track([point_map(p) for p in vascular.RADIAL])
ROUTE_LENGTH = ROUTE.distance[-1]


def map_line(draw, points, shade, width):
    points = tuple(points)
    if len(points) > 1:
        draw.line(points, width=width, fill=shade, joint="curve")


def mapped_vessel(draw, points, width=11):
    outer = tuple(point_map(p) for p in points)
    map_line(draw, outer, (134, 69, 69), width + 4)
    map_line(draw, outer, (182, 99, 91), width)
    map_line(draw, ((x - 1.5, y - 1.5) for x, y in outer), (225, 151, 137), 3)


@lru_cache(maxsize=1)
def map_base():
    image = plate(12, False).copy()
    body = [point_map(p) for p in vascular.BODY]
    wrist.flat_overlay(image, (68, 102, 86), [(x + 7, y + 10) for x, y in body], 55, 15)
    image.paste(wrist.vertical_gradient((246, 236, 218), (212, 160, 147)), (0, 0), wrist.shape_mask(body))
    pen = ImageDraw.Draw(image)
    map_line(pen, body, (170, 126, 116), 2)
    heart = vascular.curve((285, 194),
        ((261, 168), (225, 190), (237, 219)),
        ((245, 250), (284, 270), (326, 294)),
        ((349, 268), (371, 231), (342, 201)),
        ((323, 183), (300, 188), (285, 194)))
    heart_map = [point_map(p) for p in heart]
    wrist.flat_overlay(image, (113, 65, 63), heart_map, 124)
    pen = ImageDraw.Draw(image)
    map_line(pen, heart_map, (172, 98, 92), 2)

    # The inactive branches stay subdued while the instrument follows the right side.
    for branches in (
        vascular.BODY_LEFT_SUBCLAVIAN,
        vascular.BODY_CAROTIDS[0],
        vascular.BODY_CAROTIDS[1],
        vascular.FEMORAL[-37:],
    ):
        map_line(pen, (point_map(p) for p in branches), (160, 105, 102), 8)
    mapped_vessel(pen, vascular.RADIAL, 13)
    x, y = ROUTE.at(0)
    pen.ellipse((x-11, y-11, x+11, y+11), fill=(218, 244, 225), outline=GREEN, width=3)
    end_x, end_y = ROUTE.at(ROUTE_LENGTH)
    pen.ellipse((end_x-9, end_y-9, end_x+9, end_y+9), outline=GREEN, width=3)
    pen.text((87, 744), "Patient’s right", font=wrist.font(26, "semibold"), fill=GREEN)
    pen.line((76, 852, 1522, 852), fill=(168, 190, 177), width=2)
    return image


MAP_PHASES = (
    ("Radial artery", "Starts at the right wrist.", .03),
    ("Brachial artery", "The wire and catheter pass up the arm.", .30),
    ("Axillary and subclavian arteries", "The route continues through the shoulder.", .58),
    ("Brachiocephalic trunk", "The instruments enter the aortic arch.", .79),
    ("Aortic root", "The coronary openings are just above the aortic valve.", 1.0),
)
MAP_MOVES = ((0.0, .03), (3.7, .29), (7.25, .57), (10.65, .76), (14.4, .96), (16.2, 1.0))


def interpolate_map(t):
    for (start, a), (end, b) in zip(MAP_MOVES, MAP_MOVES[1:]):
        if t < end:
            return a + (b - a) * ease_time(t, start, end)
    return 1.0


def route_frame(t):
    image = map_base().copy()
    pen = ImageDraw.Draw(image)
    progress = interpolate_map(t)
    active = ROUTE_LENGTH * progress
    guide = vascular.trace(ROUTE.points, min(1.0, progress + .032))
    catheter_path = vascular.trace(ROUTE.points, progress)
    map_line(pen, catheter_path, (11, 69, 63), 11)
    map_line(pen, catheter_path, (95, 204, 175), 7)
    map_line(pen, guide, (247, 211, 146), 3)
    x, y = guide[-1]
    pen.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(251, 236, 186), outline=(134, 84, 49), width=1)
    pen.text((805, 275), "Right wrist to aortic root", font=wrist.font(39, "semibold"), fill=GREEN)
    segment = min(4, sum(progress >= p for p in (.17, .42, .68, .89)))
    for index, (label, line, _) in enumerate(MAP_PHASES):
        y_row = 352 + 67 * index
        ink = GREEN if index == segment else (97, 116, 108)
        if index == segment:
            pen.rounded_rectangle((780, y_row - 5, 1470, y_row + 51), 13, fill=(207, 231, 217))
        pen.text((806, y_row + 2), label, font=wrist.font(30, "semibold"), fill=ink)
    _, current, _ = MAP_PHASES[segment]
    pen.text((805, 738), current, font=wrist.font(25), fill=MUTED)
    return image


def prep_wipe(pen, t):
    center = 605 + 67 * sin(t * 2.6)
    pen.ellipse((center - 35, 462, center + 35, 486), fill=(68, 103, 89, 112))
    pen.rounded_rectangle((center - 27, 455, center + 26, 481), 7,
                          fill=(248, 250, 240, 255), outline=(129, 161, 142, 245), width=2)
    pen.line((center - 19, 463, center + 17, 465), fill=(213, 225, 206, 255), width=2)


def prep_drape(pen, fraction):
    left = 1248 - 970 * fraction
    pen.polygon([(left, 430), (1518, 384), (1518, 429), (left, 513)],
                fill=(42, 133, 115, 198))
    if fraction > .56:
        pen.ellipse((560, 443, 712, 500), fill=(228, 173, 152, 251),
                    outline=(53, 110, 94, 232), width=4)
    pen.line((left, 430, 1518, 384), fill=(135, 190, 161, 246), width=3)


def local_anaesthetic(pen, progress):
    # The tip remains in the tissue above the artery. This is a separate tool from the access needle.
    tip = 298 + 77 * progress
    wrist.tube(pen, tip - 101, tip, 2.7, (102, 127, 117, 255), taper=8)
    wrist.tube(pen, tip - 100, tip - 3, 1, (238, 246, 224, 247), shift=-1)
    wrist.tube(pen, tip - 113, tip - 94, 7, (22, 104, 85, 255))
    wrist.tube(pen, tip - 183, tip - 107, 13, (138, 183, 165, 255))
    wrist.tube(pen, tip - 176, tip - 111, 10, (220, 243, 226, 255))
    wrist.tube(pen, tip - 163, tip - 115, 7, (109, 189, 180, 185))
    wrist.tube(pen, tip - 204, tip - 155, 3, (127, 169, 151, 255))
    wrist.tube(pen, tip - 204, tip - 199, 12, (133, 170, 151, 255))
    return wrist.PATH.at(tip)


def ultrasound_frame(pen, time):
    pos = 633 + 18 * sin(time * 1.25)
    pen.rounded_rectangle((pos - 36, 468, pos + 36, 490), 7,
                          fill=(34, 85, 75, 255))
    pen.rounded_rectangle((pos - 35, 395, pos + 34, 476), 21,
                          fill=(221, 238, 226, 255), outline=(86, 136, 118, 255), width=3)
    pen.rounded_rectangle((pos - 20, 385, pos + 20, 436), 15,
                          fill=(231, 244, 234, 255), outline=(107, 146, 127, 255), width=2)
    pen.line((pos - 23, 476, pos + 23, 476), fill=(145, 207, 179, 255), width=3)
    pen.rounded_rectangle((878, 234, 1190, 446), 15,
                          fill=(40, 63, 58, 255), outline=(79, 126, 103, 255), width=2)
    pen.rounded_rectangle((891, 249, 1177, 405), 9, fill=(47, 61, 55, 255))
    pen.polygon([(1034, 260), (916, 388), (1152, 388)], fill=(113, 120, 107, 255))
    for shift in (0, 12, 25):
        pen.arc((922 + shift, 269 + shift, 1146 - shift, 411 - shift), 20, 160,
                fill=(170, 176, 155, 211), width=2)
    pen.ellipse((1002, 321, 1070, 358), fill=(33, 51, 44, 255),
                outline=(203, 215, 191, 255), width=3)
    pen.text((1034, 419), "Ultrasound illustration", font=wrist.font(22, "semibold"),
             anchor="mm", fill=(226, 243, 230, 255))


def prep_frame(t):
    base = plate(4, True)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    focus = (640, 487)
    if t < 3.72:
        title, line, label = "Thumb side of the right wrist", "Locate the radial artery.", "Access site"
        radius = 13 + 3 * sin(t * 2.8)
        x, y = focus
        d.ellipse((x-radius, y-radius, x+radius, y+radius),
                  fill=(164, 214, 181, 118), outline=(21, 103, 73, 255), width=3)
    elif t < 9.16:
        ultrasound_frame(d, t - 3.72)
        title, line, label = "Locate the artery on ultrasound", "The team identifies the vessel before access.", None
    elif t < 13.9:
        if t < 11.32:
            prep_wipe(d, t - 9.16)
            title, line, label = "Clean the skin", "The team prepares the wrist.", None
        else:
            prep_drape(d, ease_time(t, 11.32, 12.45))
            title, line, label = "Position the sterile drape", "The opening exposes the intended access site.", None
    else:
        prep_drape(d, 1.0)
        focus = local_anaesthetic(d, ease_time(t, 13.94, 16.0))
        title, line, label = "Local anaesthetic", "The medicine numbs the skin and tissue at the site.", "Needle in tissue"
    image = composite(base, layer)
    pen = ImageDraw.Draw(image)
    if label:
        wrist.locator(pen, 813, 361, label, focus)
    footer(pen, title, line)
    return image


def wrist_band(pen, lift, pressure):
    y = lift
    pen.polygon([(590, 389+y), (671, 378+y), (691, 466+y), (683, 701+y),
                 (629, 715+y), (612, 699+y), (608, 501+y)],
                fill=(66, 164, 139, 104), outline=(40, 112, 95, 220), width=3)
    pen.line([(603, 393+y), (659, 387+y), (680, 468+y), (675, 692+y)],
             fill=(195, 234, 208, 190), width=3, joint="curve")
    pen.rounded_rectangle((603, 375+y, 671, 397+y), 7,
                          fill=(28, 112, 96, 255), outline=(22, 87, 77, 255), width=2)
    pen.rounded_rectangle((611, 382+y, 658, 390+y), 3, fill=(133, 206, 176, 255))
    depth = 10 + 22 * pressure
    pen.ellipse((600, 472+y, 674, 472+y + depth), fill=(91, 185, 159, 180),
                outline=(24, 112, 86, 255), width=3)
    pen.arc((609, 474+y, 666, 474+y + depth), 199, 344, fill=(220, 247, 223, 225), width=3)


def dressing(pen):
    pen.rounded_rectangle((597, 469, 661, 489), 4, fill=(246, 230, 191, 255),
                          outline=(166, 139, 101, 215), width=2)
    pen.rounded_rectangle((618, 472, 641, 486), 3, fill=(252, 249, 234, 255))


def closure_frame(t):
    base = plate(20, True)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    leave = ease_time(t, 2.02, 5.35)
    if leave < 1:
        nose = SHEATH_NOSE - (SHEATH_NOSE + 188) * leave
        wrist.assembly(layer, nose, inner=False)
    place = ease_time(t, .35, 2.10)
    wrist_band(d, -163 * (1 - place), .53 + .47 * ease_time(t, 2.0, 5.15))
    result = composite(base, layer)
    pen = ImageDraw.Draw(result)
    if place > .98:
        wrist.locator(pen, 822, 373, "Compression pad", (639, 486))
    footer(pen, "Pressure over the puncture", "The band controls bleeding as staff remove the sheath.")
    return result


def band_check_frame(t):
    base = plate(21, True)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    pressure = 1 - ease_time(t, 3.75, 6.28)
    removal = ease_time(t, 6.55, 8.0)
    if removal > .61:
        dressing(d)
    if removal < .99:
        wrist_band(d, -187 * removal, pressure)
    result = composite(base, layer)
    pen = ImageDraw.Draw(result)
    if t < 3.75:
        wrist.locator(pen, 833, 374, "Access site", (638, 485))
        title, line = "Check the site and hand circulation", "Staff check the wrist while the band is in place."
    elif removal < .7:
        wrist.locator(pen, 819, 366, "Compression pad", (639, 486 - 187 * removal))
        title, line = "Reduce pressure gradually", "The team watches for bleeding as the pressure changes."
    else:
        wrist.locator(pen, 816, 372, "Dressing", (630, 481))
        title, line = "Remove the band when safe", "Staff cover the site after the band comes off."
    footer(pen, title, line)
    return result


def monitoring_panel(image, t):
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((111, 277, 751, 626), 22, fill=(39, 76, 65), outline=(30, 69, 57), width=3)
    pen.rounded_rectangle((136, 303, 726, 600), 13, fill=(27, 53, 46))
    waveform = [(157, 484), (220, 484), (235, 477), (252, 487), (277, 487),
                (291, 457), (307, 520), (322, 433), (336, 484), (395, 484),
                (413, 474), (432, 484), (503, 484), (522, 476), (535, 487),
                (553, 487), (568, 460), (584, 516), (600, 434), (617, 484),
                (681, 484)]
    pen.line(waveform, fill=(154, 227, 183), width=4, joint="curve")
    signal_x = 160 + (t * 97) % 520
    pen.line((signal_x, 430, signal_x, 531), fill=(106, 176, 140), width=1)
    pen.text((159, 333), "Recovery monitor", font=wrist.font(36, "semibold"), fill=(233, 250, 239))
    pen.text((160, 380), "Pulse and blood pressure", font=wrist.font(24), fill=(184, 223, 198))


def recovery_frame(t):
    image = plate(22, False).copy()
    pen = ImageDraw.Draw(image)
    if t < 8.98:
        monitoring_panel(image, t)
        wrist.wrist_locator(image)
        pen.text((865, 428), "Wrist and hand", font=wrist.font(42, "semibold"), fill=GREEN)
        pen.text((866, 491), "Staff check the access site", font=wrist.font(28), fill=MUTED)
        pen.text((866, 535), "and may check circulation.", font=wrist.font(28), fill=MUTED)
        footer(pen, "Checks after the test", "The team monitors your vital signs and wrist.")
        return image
    pen.rounded_rectangle((107, 285, 782, 693), 18, fill=(241, 248, 239),
                          outline=(159, 188, 170), width=2)
    if t < 15.22:
        pen.text((144, 325), "Observation", font=wrist.font(47, "semibold"), fill=GREEN)
        pen.text((145, 411), "Some patients go home the same day.", font=wrist.font(28), fill=INK)
        pen.text((145, 473), "Others need more time in observation.", font=wrist.font(28), fill=INK)
        pen.text((866, 437), "Your team decides when", font=wrist.font(36, "semibold"), fill=GREEN)
        pen.text((866, 489), "it is safe to leave.", font=wrist.font(36, "semibold"), fill=GREEN)
        footer(pen, "Recovery time varies", "Follow the plan from your treating team.")
        return image

    pen.text((147, 324), "Before you go home", font=wrist.font(46, "semibold"), fill=GREEN)
    for index, question in enumerate(("What did the angiogram show?", "How should I care for my wrist?",
                                      "When can I lift or drive?", "Who should I contact?")):
        y = 411 + 60 * index
        pen.ellipse((148, y + 14, 157, y + 23), fill=GREEN)
        pen.text((180, y), question, font=wrist.font(29), fill=INK)
    pen.text((859, 426), "Ask for written", font=wrist.font(40, "semibold"), fill=GREEN)
    pen.text((859, 478), "discharge instructions.", font=wrist.font(40, "semibold"), fill=GREEN)
    footer(pen, "Your discharge plan", "Check the instructions before returning to your usual activities.")
    return image


def read_scenes():
    source = json.loads((EPISODE / "production" / "scenes.json").read_text(encoding="utf-8"))["radial"]
    timing = json.loads((REVISION / "radial-alexander-scene-timing.json").read_text(encoding="utf-8"))["timing"]
    for narr, scene in zip(timing, source):
        if narr["scene"] != scene["title"] or narr["script_tokens"] != narr["matched_tokens"]:
            raise ValueError(f"Unexpected scene timing at {scene['title']}")
    return timing


def render_scene(scene, draw_frame, timing):
    start = timing[scene - 1]["narration_start_sec"]
    end = timing[scene]["narration_start_sec"]
    begin_frame, end_frame = round(start * FPS), round(end * FPS)
    count = end_frame - begin_frame
    path = OUT / f"R{scene:02d}-{SCENE_NAMES[scene]}.mp4"
    cmd = [
        str(wrist.FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-movflags", "+faststart",
        str(path),
    ]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        for n in range(count):
            process.stdin.write(draw_frame(n / FPS).tobytes())
        process.stdin.close()
        if process.wait():
            raise RuntimeError(f"Render failed: {path.name}")
    subprocess.run([str(wrist.FFMPEG), "-hide_banner", "-loglevel", "error", "-nostdin",
                    "-xerror", "-i", str(path), "-f", "null", "NUL"], check=True)
    print(f"R{scene:02d}: {count} frames, {count/FPS:.3f}s, {path.name}", flush=True)
    return {"scene": scene, "start_frame": begin_frame, "end_frame": end_frame, "frames": count,
            "timeline_start_sec": start, "timeline_end_sec": end, "file": path.name}


def make_contact_sheet(scenes, draws):
    thumbs = []
    for scene in scenes:
        for when in {
            4: (2.0, 7.0, 12.8, 16.5),
            12: (1.7, 6.0, 13.5),
            20: (2.1, 4.2, 7.4),
            21: (2.1, 6.4, 8.1),
            22: (2.0, 11.3, 17.5),
        }.get(scene, (2.1, 6.4)):
            shot = draws[scene](when).resize((520, 292), Image.Resampling.LANCZOS)
            thumbs.append((scene, when, shot))
    rows = (len(thumbs) + 2) // 3
    sheet = Image.new("RGB", (1600, rows * 322), (224, 235, 228))
    d = ImageDraw.Draw(sheet)
    for i, (scene, when, shot) in enumerate(thumbs):
        x, y = 10 + 530 * (i % 3), 8 + 322 * (i // 3)
        sheet.paste(shot, (x, y))
        d.text((x + 6, y + 296), f"R{scene:02d} · {when:.1f}s", font=wrist.font(17), fill=MUTED)
    sheet.save(OUT / ("radial-visual-check-" + "-".join(f"{n:02d}" for n in scenes) + ".jpg"), quality=93)


def run(scenes, still_only=False):
    draws = {scene: (lambda t, n=scene: tools_at_wrist(n, t)) for scene in (10, 11, 19)}
    draws.update({4: prep_frame, 12: route_frame, 20: closure_frame, 21: band_check_frame, 22: recovery_frame})
    make_contact_sheet(scenes, draws)
    if still_only:
        return
    timing = read_scenes()
    records = [render_scene(scene, draws[scene], timing) for scene in scenes]
    tag = "-".join(f"{scene:02d}" for scene in scenes)
    (OUT / f"timing-R{tag}.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scenes", type=int, nargs="+")
    cli.add_argument("--stills-only", action="store_true")
    args = cli.parse_args()
    run(args.scenes, args.stills_only)
