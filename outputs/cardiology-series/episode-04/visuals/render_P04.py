"""Render the transfemoral TAVI guidewire route and its decoded scene still."""

from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
from random import Random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageOps


HERE = Path(__file__).resolve().parent
SERIES = HERE.parents[1]
EPISODE_ONE = SERIES / "episode-01"
sys.dont_write_bytecode = True
sys.path.insert(0, str(EPISODE_ONE / "production"))
sys.path.insert(0, str(EPISODE_ONE / "revision" / "wrist-proof"))
import render_wrist_proof as wrist
import vascular_art as vessels


W, H, FPS, DURATION = 1600, 900, 24, 21
INK, GREEN, MUTED = wrist.INK, wrist.GREEN, wrist.MUTED
font, curve = wrist.font, vessels.curve

# Separate the posterior descending aorta from the LV in this cutaway projection.
FEMORAL_PATH = tuple(
    (x+44*wrist.smooth((i-44)/10)*wrist.smooth((79-i)/15), y)
    for i, (x, y) in enumerate(vessels.FEMORAL)
)
ROOT = curve(FEMORAL_PATH[-1], ((286, 205), (287, 210), (290, 217)))
LV_PATH = curve((290, 217), ((294, 226), (301, 236), (306, 252)),
                ((311, 267), (318, 273), (329, 269)),
                ((341, 265), (345, 253), (337, 248)),
                ((333, 245), (328, 245), (325, 249)))
WIRE = wrist.Track(FEMORAL_PATH + ROOT[1:] + LV_PATH[1:])
VALVE_STATION = len(FEMORAL_PATH) + len(ROOT) - 5
WAYPOINTS = (
    (0.0, 0, "Right common femoral artery"),
    (4.8, 6, "Right common femoral artery"),
    (6.8, 14, "Right external iliac artery"),
    (8.0, 22, "Right common iliac artery"),
    (9.2, 32, "Abdominal aorta"),
    (11.2, 49, "Descending thoracic aorta"),
    (12.8, 67, "Aortic arch"),
    (14.3, 81, "Ascending aorta"),
    (16.6, VALVE_STATION, "Native aortic valve"),
    (18.9, len(WIRE.points)-1, "Left ventricle"),
)
HEART = curve((286, 190), ((267, 171), (237, 182), (235, 209)),
              ((232, 244), (262, 256), (290, 274)),
              ((305, 286), (316, 302), (330, 296)),
              ((357, 283), (369, 244), (363, 222)),
              ((354, 197), (323, 180), (286, 190)))
LV = curve((292, 218), ((304, 203), (325, 203), (339, 215)),
           ((361, 229), (358, 251), (345, 274)),
           ((335, 291), (326, 290), (314, 279)),
           ((296, 261), (284, 236), (292, 218)))
CFA_DISTAL = curve((222, 483), ((220, 495), (218, 508), (217, 517)),
                   ((216, 525), (213, 533), (211, 542)))
DEEP_FEMORAL = curve((217, 517), ((225, 523), (232, 529), (231, 539)))
ARTERIAL = FEMORAL_PATH + ROOT[1:]
ARCH_BRANCHES = (
    curve(FEMORAL_PATH[81], ((285, 133), (272, 119), (265, 115))),
    curve((265, 115), ((267, 105), (271, 91), (270, 76))),
    curve((265, 115), ((240, 114), (208, 128), (177, 145))),
    curve(FEMORAL_PATH[76], ((313, 121), (312, 92), (313, 76))),
    curve(FEMORAL_PATH[72], ((350, 133), (378, 127), (404, 140))),
)
VALVE_LEAFLETS = (
    curve((277, 211), ((280, 212), (283, 216), (286, 217))),
    curve((299, 210), ((296, 210), (295, 216), (293, 217))),
)


def stroke(draw, points, fill, width=1):
    if len(points) > 1:
        draw.line(points, fill=fill, width=width, joint="curve")


def point_map(point):
    x, y = point
    return 95+x*1.17, 252+y*.85


def point_xray(point):
    x, y = point
    return 325+(x-302)*3.65, 13+(y-125)*1.86


def mapped(points, projection=point_map):
    return tuple(map(projection, points))


def dot(draw, point, radius, fill, border=None):
    x, y = point
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill, outline=border, width=2)


def badge(draw, x, y, text):
    face = font(22, "semibold")
    draw.rounded_rectangle((x, y, x+draw.textlength(text, font=face)+31, y+39), 8,
                           fill="#dfede3")
    draw.text((x+15, y+7), text, font=face, fill=GREEN)


def leader(draw, label, position, target, *, tone=GREEN):
    x, y = position
    tx, ty = target
    face = font(22, "semibold")
    width = draw.textlength(label, font=face)
    if tx > x + width:
        begin, knee = (x+width+9, y+14), (x+width+31, y+14)
    else:
        begin, knee = (x-8, y+14), (x-30, y+14)
    stroke(draw, (begin, knee, target), tone, 2)
    dot(draw, target, 3.2, "#eff1da", tone)
    draw.text(position, label, fill=tone, font=face)


def vessel(draw, points, size, color="#bd6767"):
    line = mapped(points)
    stroke(draw, line, "#8d515b", size+4)
    stroke(draw, line, color, size)
    stroke(draw, tuple((x-1, y-1) for x, y in line), "#da9285", 2)


@lru_cache(maxsize=1)
def base():
    image = wrist.vertical_gradient((246, 251, 245), (219, 234, 225))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 57, 126, 107), 8, fill="white")
    logo = ImageOps.fit(Image.open(wrist.LOGO).convert("RGB"), (48, 48), method=Image.Resampling.LANCZOS)
    image.paste(logo, (77, 58))
    draw.text((144, 62), "Elysian Biomedical LLP", fill=GREEN, font=font(24, "semibold"))
    draw.text((144, 93), "Cardiology Education Series", fill=MUTED, font=font(18))
    draw.text((1521, 66), "AORTIC VALVE REPLACEMENT", fill=GREEN, font=font(20, "semibold"), anchor="rt")
    stroke(draw, ((76, 128), (1522, 128)), "#b3ccbf", 2)
    draw.text((76, 151), "The route from groin to valve", font=font(58, "heading"), fill=INK)
    for box in ((76, 248, 813, 730), (835, 248, 1522, 730)):
        draw.rounded_rectangle(box, 20, fill="#f1f8f0", outline="#bfd5c6", width=2)

    body = mapped(vessels.BODY)
    draw.polygon(tuple((x+5, y+5) for x, y in body), fill="#dfe8dc")
    draw.polygon(body, fill="#e7bbad")
    stroke(draw, body, "#ba8a83", 2)
    for side in (-1, 1):
        for i in range(5):
            y = 150+21*i
            rib = curve((292, y+24), ((292+25*side, y+8), (292+65*side, y-15), (292+95*side, y+6)))
            stroke(draw, mapped(rib), "#d9a59a", 2)
    silhouette = mapped(HEART)
    draw.polygon(silhouette, fill="#ad656e")
    stroke(draw, silhouette, "#9a5961", 2)
    cavity = mapped(LV)
    draw.polygon(cavity, fill="#7c4053")
    stroke(draw, cavity, "#dd9f92", 3)
    for path in ARCH_BRANCHES:
        vessel(draw, path, 6, "#b97c7c")
    vessel(draw, vessels.BODY_OTHER_ILIAC, 7, "#b97c7c")
    vessel(draw, CFA_DISTAL, 8)
    vessel(draw, DEEP_FEMORAL, 5)
    vessel(draw, ARTERIAL[:33], 9)
    vessel(draw, ARTERIAL[32:54], 13)
    vessel(draw, ARTERIAL[53:], 18)
    for leaflet in VALVE_LEAFLETS:
        stroke(draw, mapped(leaflet), "#f0c397", 4)
    # The local entry sheath is anchored above the femoral division.
    sheath_track = curve((209, 494), ((213, 489), (217, 487), (222, 483)),
                         ((224, 477), (224, 474), (226, 469)))
    stroke(draw, mapped(sheath_track), "#2b5e55", 11)
    stroke(draw, mapped(sheath_track), "#91cabe", 6)
    stroke(draw, mapped(((205, 496), (212, 490))), "#437e70", 16)
    leader(draw, "Sheath stays at groin", (424, 647), point_map((219, 487)))
    badge(draw, 99, 267, "Patient’s right")
    badge(draw, 858, 267, "Simulated X-ray")
    stroke(draw, ((77, 865), (1521, 865)), "#a4bfae", 2)
    draw.text((77, 757), "Groin artery to aortic valve", font=font(34, "semibold"), fill=GREEN)
    draw.text((77, 807), "The guidewire crosses the narrowed native valve and rests inside the left ventricle.",
              font=font(25), fill=MUTED)
    return image


@lru_cache(maxsize=1)
def xray_background():
    width, height = 632, 360
    image = Image.new("L", (width, height))
    noise = Random(51)
    image.putdata([146+noise.randint(-17, 17) for _ in range(width*height)])
    image = image.filter(ImageFilter.GaussianBlur(.92))
    body = Image.new("L", (width, height), 177)
    draw = ImageDraw.Draw(body)
    draw.ellipse((26, -6, 274, 337), fill=150)
    draw.ellipse((366, 0, 617, 341), fill=148)
    for i in range(7):
        y = 10+44*i
        rib = curve((-20, y+26), ((81, y+1), (174, y-12), (294, y+13)),
                    ((395, y+37), (524, y+5), (657, y+58)))
        stroke(draw, rib, 189, 8)
    stroke(draw, curve((304, 0), ((299, 90), (304, 235), (316, 367))), 184, 28)
    silhouette = mapped(HEART, point_xray)
    draw.polygon(silhouette, fill=177)
    image = Image.blend(image, body.filter(ImageFilter.GaussianBlur(9)), .66)
    return image.convert("RGB")


def trace_to(time):
    for (begin, a, label), (end, b, _) in zip(WAYPOINTS, WAYPOINTS[1:]):
        if time < end:
            amount = wrist.smooth((time-begin)/(end-begin))
            length = WIRE.distance[a] + (WIRE.distance[b]-WIRE.distance[a])*amount
            return length, label
    return WIRE.distance[-1], WAYPOINTS[-1][2]


def visible_wire(length):
    if length <= 0:
        return WIRE.points[:1]
    index = bisect_right(WIRE.distance, length)
    return tuple(WIRE.points[:index]) + (WIRE.at(length),)


def xray_image(points, time):
    image = xray_background().copy()
    draw = ImageDraw.Draw(image)
    # A pale outline locates the modeled aorta without simulated contrast.
    stroke(draw, mapped(ARTERIAL[50:], point_xray), "#bec2c0", 5)
    stroke(draw, mapped(LV, point_xray), "#a4adab", 2)
    for leaflet in VALVE_LEAFLETS:
        stroke(draw, mapped(leaflet, point_xray), "#a0a9a7", 3)
    visible = mapped(points[50:], point_xray)
    if len(visible) > 1:
        stroke(draw, visible, "#303635", 4)
        dot(draw, visible[-1], 3, "#333936", "#dde5db")
    if time >= 14.9:
        leader(draw, "Native aortic valve", (23, 158), point_xray((291, 216)), tone="#364d48")
        leader(draw, "Left ventricle", (441, 307), point_xray((342, 260)), tone="#364d48")
    return image


def frame(time):
    image = base().copy()
    length, label = trace_to(time)
    points = visible_wire(length)
    draw = ImageDraw.Draw(image)
    if len(points) > 1:
        route = mapped(points)
        stroke(draw, route, "#674933", 5)
        stroke(draw, route, "#f7d891", 3)
        dot(draw, route[-1], 4, "#f4d899", "#715343")
    image.paste(xray_image(points, time), (857, 316))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((856, 315, 1490, 677), 7, outline="#9db4a8", width=2)
    draw.text((857, 691), label, fill=GREEN, font=font(24, "semibold"))
    stroke(draw, ((1306, 705), (1348, 705)), "#674933", 5)
    stroke(draw, ((1306, 705), (1348, 705)), "#f7d891", 3)
    draw.text((1361, 692), "Guidewire", fill=MUTED, font=font(22))
    return image


def render():
    ffmpeg = str(wrist.FFMPEG)
    target = HERE / "P04.mp4"
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
        "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-threads", "2", "-preset", "veryfast", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    prior = None
    try:
        with process.stdin as pipe:
            for i in range(FPS*DURATION):
                time = min(i/FPS, 19)
                if prior != time:
                    raw = frame(time).tobytes()
                    prior = time
                pipe.write(raw)
    finally:
        status = process.wait()
        if status:
            raise RuntimeError(f"Could not render P04, encoder status {status}")
    subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(target),
                    "-map", "0:v:0", "-f", "null", "-"], check=True)
    subprocess.run([ffmpeg, "-v", "error", "-y", "-ss", "19.65", "-i", str(target),
                    "-frames:v", "1", str(HERE/"P04.png")], check=True)
    print("P04 · 21.00s · 1920x1080 · silent · full decode passed", flush=True)


if __name__ == "__main__":
    render()
