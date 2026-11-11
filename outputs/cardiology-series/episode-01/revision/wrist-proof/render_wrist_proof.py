"""Create the radial-access motion study and a five-beat visual contact sheet."""
from __future__ import annotations

from bisect import bisect_right
from functools import lru_cache
from math import cos, hypot, pi, sin
from pathlib import Path
from random import Random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
FONT_DIR = ROOT / "outputs/website-v2/elysian-corporate/assets/fonts"
FFMPEG = ROOT / "work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
LOGO = ROOT / "work/company-logo-original-686.jpg"
VIDEO = OUT / "radial-access-motion-proof.mp4"
NARRATION = OUT.parent / "alexander-wrist-voice-take-1.mp3"
NARRATED_VIDEO = OUT / "radial-access-alexander-preview.mp4"
W, H, FPS = 1600, 900, 30
DURATION = 21
INK = (26, 51, 45)
MUTED = (67, 93, 85)
GREEN = (0, 75, 61)
STOPS = (0.0, 4.6, 8.3, 11.2, 16.15, 21.0)
MOTION_WINDOWS = ((.1, 3.45), (.07, 2.47), (.03, 1.8), (.04, 2.62), (.1, 2.81))
LABELS = (
    ("Access needle", "The needle tip enters the radial artery."),
    ("Short guidewire", "The wire passes through the needle."),
    ("Needle withdrawal", "The needle comes out over the wire."),
    ("Sheath and dilator", "The assembly advances over the wire."),
    ("Sheath in place", "The wire and dilator come out."),
)


def blend(a, b, p):
    return tuple(round(x + (y - x) * p) for x, y in zip(a, b))


def smooth(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def bezier(a, b, c, d, n=36):
    for i in range(n + 1):
        t = i / n
        q = 1 - t
        yield (
            q ** 3 * a[0] + 3 * q ** 2 * t * b[0] + 3 * q * t ** 2 * c[0] + t ** 3 * d[0],
            q ** 3 * a[1] + 3 * q ** 2 * t * b[1] + 3 * q * t ** 2 * c[1] + t ** 3 * d[1],
        )


def curve(start, segments):
    points = [start]
    for control1, control2, finish in segments:
        points.extend(list(bezier(points[-1], control1, control2, finish))[1:])
    return points


class Track:
    def __init__(self, points):
        self.points = points
        self.distance = [0.0]
        for a, b in zip(points, points[1:]):
            self.distance.append(self.distance[-1] + hypot(b[0] - a[0], b[1] - a[1]))

    def at(self, s):
        i = min(len(self.points) - 2, max(0, bisect_right(self.distance, s) - 1))
        p = (s - self.distance[i]) / (self.distance[i + 1] - self.distance[i])
        return blend(self.points[i], self.points[i + 1], p)

    @lru_cache(maxsize=8192)
    def basis(self, s):
        x, y = self.at(s)
        ax, ay = self.at(s - 2)
        bx, by = self.at(s + 2)
        magnitude = hypot(bx - ax, by - ay)
        if magnitude < 1:
            return x, y, 0, 1
        return x, y, -(by - ay) / magnitude, (bx - ax) / magnitude

    def uv(self, s, offset):
        x, y, nx, ny = self.basis(s)
        return x + nx * offset, y + ny * offset


NEEDLE_TIP = (756, 579)
PATH = Track([
    (346, 282), NEEDLE_TIP,
    *list(bezier(NEEDLE_TIP, (782, 598), (820, 612), (871, 613)))[1:],
    *list(bezier((871, 613), (1080, 616), (1290, 595), (1460, 590)))[1:],
])
NEEDLE_DISTANCE = PATH.distance[1]
WIRE_TIP = NEEDLE_DISTANCE + 235
WIRE_LENGTH = WIRE_TIP + 73
ASSEMBLY_NOSE = NEEDLE_DISTANCE + 151
VESSEL = curve((403, 632), [
    ((553, 625), (684, 604), (752, 604)),
    ((823, 604), (820, 614), (888, 613)),
    ((1070, 610), (1270, 599), (1517, 591)),
])
SKIN_EDGE = curve((105, 512), [
    ((202, 531), (240, 562), (320, 546)),
    ((410, 535), (453, 506), (538, 493)),
    ((644, 480), (714, 474), (825, 464)),
    ((1015, 449), (1214, 443), (1518, 432)),
])
UPPER = curve((105, 512), [
    ((100, 478), (144, 464), (183, 453)),
    ((239, 441), (266, 437), (300, 408)),
    ((338, 378), (377, 367), (448, 371)),
    ((525, 375), (566, 393), (650, 381)),
    ((837, 346), (1164, 321), (1523, 337)),
])
LOWER = curve((105, 512), [
    ((147, 566), (207, 624), (262, 635)),
    ((341, 659), (392, 692), (451, 697)),
    ((524, 719), (649, 718), (745, 730)),
    ((929, 753), (1255, 714), (1523, 691)),
])
BODY = UPPER + [(1523, 691)] + list(reversed(LOWER))
TOP = UPPER + [(1518, 432)] + list(reversed(SKIN_EDGE))
SECTION = SKIN_EDGE + [(1523, 691)] + list(reversed(LOWER))


@lru_cache(maxsize=16)
def font(size, style="regular"):
    filename = "josefin-sans-variable.ttf" if style == "heading" else f"fira-sans-{style}.ttf"
    face = ImageFont.truetype(str(FONT_DIR / filename), size)
    if style == "heading":
        face.set_variation_by_axes([640])
    return face


def vertical_gradient(top, bottom):
    gradient = Image.new("RGB", (1, H))
    gradient.putdata([blend(top, bottom, y / (H - 1)) for y in range(H)])
    return gradient.resize((W, H))


def shape_mask(points):
    mask = Image.new("L", (W, H))
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def flat_overlay(img, shade, points, opacity, blur=0):
    mask = shape_mask(points)
    if opacity < 255:
        mask = mask.point(lambda v: v * opacity // 255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    img.paste(shade, (0, 0, W, H), mask)


def tissue_texture(img):
    random = Random(112)
    fibers = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(fibers)
    for _ in range(2900):
        x = random.randrange(100, 1521)
        y = random.randrange(385, 733)
        long = random.uniform(1, 8)
        draw.line((x, y, x + long, y + random.uniform(-1.2, 2.2)),
                  fill=(255, 222, 197, random.randrange(8, 21)), width=1)
    fibers = fibers.filter(ImageFilter.GaussianBlur(.52))
    composite = Image.alpha_composite(img.convert("RGBA"), fibers).convert("RGB")
    img.paste(composite, (0, 0), shape_mask(BODY))


def wrist_locator(img):
    palm = curve((1500, 213), [
        ((1472, 210), (1439, 216), (1423, 214)),
        ((1410, 205), (1400, 199), (1383, 194)),
        ((1368, 190), (1339, 190), (1311, 184)),
        ((1300, 181), (1296, 187), (1308, 194)),
        ((1318, 198), (1337, 201), (1347, 204)),
        ((1334, 206), (1299, 202), (1283, 201)),
        ((1274, 200), (1272, 209), (1285, 211)),
        ((1309, 215), (1330, 217), (1346, 221)),
        ((1333, 224), (1300, 219), (1283, 221)),
        ((1276, 223), (1278, 232), (1289, 232)),
        ((1310, 233), (1337, 233), (1350, 237)),
        ((1334, 243), (1307, 238), (1298, 243)),
        ((1294, 249), (1301, 254), (1312, 254)),
        ((1335, 255), (1352, 256), (1368, 263)),
        ((1379, 267), (1390, 272), (1394, 281)),
        ((1404, 306), (1415, 305), (1418, 290)),
        ((1420, 279), (1410, 263), (1427, 258)),
        ((1446, 256), (1482, 261), (1500, 262)),
    ])
    # Palmar view of a right hand, with fingers pointing to the left.
    palm = [(x, 473 - y) for x, y in palm]
    flat_overlay(img, (79, 112, 92), [(x + 1, y + 4) for x, y in palm], 60, 8)
    img.paste(vertical_gradient((248, 229, 209), (225, 174, 152)), (0, 0), shape_mask(palm))
    pen = ImageDraw.Draw(img)
    pen.line(palm, fill=(174, 128, 109), width=1, joint="curve")
    pen.arc((1364, 217, 1409, 253), 199, 300, fill=(183, 141, 122), width=2)
    pen.arc((1381, 219, 1422, 258), 60, 155, fill=(199, 153, 131), width=1)
    pen.line((1442, 222, 1442, 193, 1498, 193), fill=(35, 114, 93), width=2)
    pen.ellipse((1437, 217, 1447, 227), fill=(22, 115, 88), outline=(245, 251, 244), width=2)
    pen.text((1502, 171), "Thumb side", font=font(16, "semibold"), fill=GREEN, anchor="rt")


@lru_cache(maxsize=1)
def background():
    image = vertical_gradient((244, 250, 245), (220, 233, 226))
    flat_overlay(image, (255, 255, 251),
                 [(0, 0), (1220, 0), (1025, 694), (0, 663)], 112, 105)
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((76, 57, 126, 107), 9, fill=(255, 255, 255))
    brand = ImageOps.fit(Image.open(LOGO).convert("RGB"), (46, 46), method=Image.Resampling.LANCZOS)
    image.paste(brand, (78, 59))
    pen.text((144, 62), "Elysian Biomedical LLP", font=font(24, "semibold"), fill=GREEN)
    pen.text((144, 93), "Cardiology Education Series", font=font(18), fill=MUTED)
    pen.text((1518, 65), "RIGHT WRIST", font=font(21, "semibold"), fill=GREEN, anchor="rt")
    pen.text((1518, 94), "Anatomical illustration", font=font(17), fill=MUTED, anchor="rt")
    pen.line((77, 128, 1522, 128), fill=(179, 204, 191), width=1)
    pen.text((76, 151), "How the sheath enters the wrist", font=font(57, "heading"), fill=INK)
    wrist_locator(image)

    shadow = [(x + 15, y + 26) for x, y in BODY]
    flat_overlay(image, (41, 67, 50), shadow, 48, 25)
    image.paste(vertical_gradient((244, 207, 176), (143, 82, 74)), (0, 0), shape_mask(BODY))
    image.paste(vertical_gradient((254, 225, 198), (181, 114, 102)), (0, 0), shape_mask(TOP))
    image.paste(vertical_gradient((222, 158, 138), (128, 73, 71)), (0, 0), shape_mask(SECTION))

    # Lighting on the palm and side wall. The section face remains a single plane.
    flat_overlay(image, (255, 228, 198),
                 [(173, 480), (390, 387), (672, 401), (1020, 348), (1455, 365),
                  (1400, 405), (903, 436), (608, 461), (342, 474)], 126, 24)
    flat_overlay(image, (103, 59, 59),
                 [(170, 566), (414, 647), (720, 658), (952, 661), (1454, 611),
                  (1494, 688), (1036, 720), (715, 718), (422, 691), (223, 641)], 91, 21)
    tissue_texture(image)
    pen = ImageDraw.Draw(image)
    pen.line(UPPER, fill=(216, 170, 145), width=2, joint="curve")
    pen.line(SKIN_EDGE, fill=(156, 94, 83), width=12, joint="curve")
    pen.line([(x, y - 3) for x, y in SKIN_EDGE], fill=(255, 205, 171), width=4, joint="curve")
    pen.line([(x, y + 5) for x, y in SKIN_EDGE], fill=(206, 143, 126), width=2, joint="curve")
    pen.line(LOWER, fill=(100, 59, 61), width=2, joint="curve")
    wall_stops = (
        (-49, (143, 75, 76)), (-43, (187, 102, 96)), (-37, (222, 130, 113)),
        (-30, (174, 73, 80)), (-23, (127, 45, 61)), (-8, (133, 56, 69)),
        (14, (101, 39, 54)), (25, (131, 54, 68)), (31, (172, 79, 83)),
        (38, (212, 109, 104)), (44, (163, 74, 80)), (49, (133, 63, 69)),
    )
    # Continuous polygons follow the wall curve without segmented stroke joints.
    for (lower, ca), (upper, cb) in zip(wall_stops, wall_stops[1:]):
        for offset in range(lower, upper):
            pen.polygon([(x, y + offset) for x, y in VESSEL] +
                        [(x, y + offset + 1) for x, y in reversed(VESSEL)],
                        fill=blend(ca, cb, (offset - lower) / (upper - lower)))
    # Narrow bevel to the exposed arterial wall at the proximal cross-section.
    pen.ellipse((1496, 545, 1537, 638), fill=(177, 81, 88), outline=(107, 50, 58), width=2)
    pen.ellipse((1500, 555, 1532, 628), fill=(112, 49, 63), outline=(219, 114, 109), width=2)
    pen.arc((1504, 563, 1527, 621), 91, 270, fill=(226, 130, 120), width=2)

    pen.line((1217, 627, 1273, 773, 1516, 773), fill=(101, 108, 93), width=2, joint="curve")
    pen.ellipse((1212, 622, 1222, 632), fill=(248, 230, 208), outline=(88, 65, 58), width=1)
    pen.text((1516, 786), "Radial artery", font=font(21, "semibold"), fill=INK, anchor="rt")
    pen.text((1516, 817), "Toward the elbow →", font=font(17), fill=MUTED, anchor="rt")
    return image


def tube(draw, a, b, radius, color, *, taper=0, shift=0):
    if b <= a:
        return
    count = max(2, round((b - a) / 5))
    stations = [a + (b - a) * i / count for i in range(count + 1)]
    sizes = [radius * (max(.05, min(1, (b - s) / taper)) if taper else 1) for s in stations]
    top = [PATH.uv(s, shift - r) for s, r in zip(stations, sizes)]
    bottom = [PATH.uv(s, shift + r) for s, r in reversed(list(zip(stations, sizes)))]
    draw.polygon(top + bottom, fill=color)


def wire(draw, start, end):
    tube(draw, start, end, 4.0, (105, 75, 44))
    tube(draw, start, end, 2.65, (245, 215, 152), shift=-.45)
    tube(draw, start, end, .75, (255, 243, 196), shift=-1.35)


def needle(draw, end, alpha=255):
    start = end - 294
    tube(draw, start, end, 8.4, (68, 88, 87, alpha), taper=26)
    tube(draw, start, end, 6.6, (169, 187, 179, alpha), taper=26, shift=-1)
    tube(draw, start, end - 4, 1.5, (247, 253, 237, alpha), shift=-4)
    tube(draw, end - 20, end, 2.5, (71, 91, 89, alpha), taper=9, shift=.5)
    tube(draw, start - 55, start + 19, 13.8, (18, 89, 83, alpha))
    tube(draw, start - 55, start + 17, 10.1, (47, 130, 116, alpha), shift=-2)
    tube(draw, start - 46, start + 12, 2.1, (140, 206, 177, alpha), shift=-6.4)
    tube(draw, start - 54, start - 45, 12, (11, 63, 57, alpha))


def opening(draw, at):
    outer = [PATH.uv(at + 4 * cos(a * pi / 16), 20.8 * sin(a * pi / 16)) for a in range(32)]
    inner = [PATH.uv(at + 2.7 * cos(a * pi / 16), 15.0 * sin(a * pi / 16)) for a in range(32)]
    draw.polygon(outer, fill=(132, 216, 188, 244))
    draw.polygon(inner, fill=(99, 43, 59, 255))


def assembly(layer, nose, *, inner=True, dilator_at=None):
    draw = ImageDraw.Draw(layer)
    tip = nose - 28
    hub = tip - 425
    tube(draw, hub, tip, 20.8, (9, 72, 66, 206))
    tube(draw, hub, tip, 17.5, (65, 170, 151, 158))
    tube(draw, hub, tip - 3, 11.6, (159, 222, 199, 113), shift=-1.5)
    tube(draw, hub + 10, tip - 4, 2.2, (219, 246, 224, 210), shift=-11)
    tube(draw, hub - 40, hub + 22, 24.8, (12, 79, 72, 255))
    tube(draw, hub - 35, hub + 18, 20, (29, 134, 116, 255), shift=-2)
    tube(draw, hub - 30, hub + 10, 3.1, (156, 215, 184, 255), shift=-12)
    tube(draw, hub - 43, hub - 35, 20.5, (5, 62, 55, 255))
    opening(draw, tip)

    if inner:
        ds = nose if dilator_at is None else dilator_at
        tube(draw, ds - 534, ds, 12.3, (190, 167, 131, 220), taper=32)
        tube(draw, ds - 534, ds, 10.7, (238, 227, 201, 227), taper=32, shift=-.55)
        tube(draw, ds - 529, ds - 7, 2, (255, 251, 234, 230), shift=-4.3, taper=20)
        tube(draw, ds - 542, ds - 494, 15.6, (215, 202, 168, 246))
        tube(draw, ds - 536, ds - 498, 2.3, (255, 248, 218, 245), shift=-8)
    return hub, tip


def locator(draw, x, y, text, anchor):
    ax, ay = anchor
    middle = y + 26
    face = font(34, "semibold")
    side = x if ax < x else x + draw.textlength(text, font=face)
    knee = side + (-33 if ax < x else 33)
    draw.line([(side, middle), (knee, middle), (ax, ay)], fill=(54, 103, 87), width=2, joint="curve")
    draw.ellipse((ax - 4, ay - 4, ax + 4, ay + 4), fill=(233, 244, 235), outline=(39, 92, 75), width=2)
    draw.text((x, y), text, fill=GREEN, font=face)


def frame(t):
    base = background().copy()
    stage = min(4, max(0, bisect_right(STOPS, t) - 1))
    delay, travel_time = MOTION_WINDOWS[stage]
    p = smooth((t - STOPS[stage] - delay) / travel_time)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    original_tip = NEEDLE_DISTANCE
    assembly_tip = ASSEMBLY_NOSE
    lead_in = -188
    wire_end = lead_in + (WIRE_TIP - lead_in) * p

    if stage == 0:
        needle_end = 232 + (original_tip - 232) * p
        needle(d, needle_end)
    elif stage == 1:
        wire(d, wire_end - WIRE_LENGTH, wire_end)
        needle(d, original_tip)
    elif stage == 2:
        wire(d, WIRE_TIP - WIRE_LENGTH, WIRE_TIP)
        needle_end = original_tip - 566 * p
        needle(d, needle_end, round(255 * (1 - smooth((p - .42) / .24))))
    elif stage == 3:
        nose = lead_in + (assembly_tip - lead_in) * p
        assembly(layer, nose)
        # The inner wire remains visible through the sectioned dilator.
        wire(d, WIRE_TIP - WIRE_LENGTH, WIRE_TIP)
    else:
        displacement = (WIRE_TIP - lead_in) * p
        ds = assembly_tip - displacement
        assembly(layer, assembly_tip, inner=ds > lead_in, dilator_at=ds)
        wire(d, WIRE_TIP - displacement - WIRE_LENGTH, WIRE_TIP - displacement)

    # Let tools leave the cutaway without crossing the title.
    layer.paste((0, 0, 0, 0), (0, 0, W, 209))
    for row in range(209, 227):
        strip = layer.crop((0, row, W, row + 1))
        strip.putalpha(strip.getchannel("A").point(lambda value: round(value * (row - 209) / 18)))
        layer.paste(strip, (0, row))
    result = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    pen = ImageDraw.Draw(result)
    if stage == 0 and p > .45:
        locator(pen, 829, 378, "Needle tip", PATH.at(needle_end - 5))
    elif stage == 1 and wire_end > original_tip + 15:
        locator(pen, 1004, 381, "Short guidewire", PATH.at(wire_end - 2))
    elif stage == 2:
        locator(pen, 1004, 383, "Wire stays", PATH.at(original_tip + 122))
    elif stage == 3 and p > .76:
        locator(pen, 844, 373, "Sheath", PATH.at(nose - 46))
        locator(pen, 1146, 398, "Dilator", PATH.at(nose - 13))
    elif stage == 4:
        locator(pen, 962, 382, "Open sheath tip", PATH.at(assembly_tip - 29))

    label, detail = LABELS[stage]
    pen.text((77, 751), label, font=font(42, "semibold"), fill=GREEN)
    pen.text((77, 804), detail, font=font(24), fill=MUTED)
    line_start, line_end, y = 77, 1522, 853
    pen.line((line_start, y, line_end, y), fill=(172, 193, 181), width=2)
    pen.line((line_start, y, line_start + (line_end - line_start) * t / DURATION, y), fill=(0, 115, 85), width=4)
    for stop in STOPS[1:-1]:
        x = line_start + (line_end - line_start) * stop / DURATION
        pen.line((x, y - 5, x, y + 5), fill=(128, 156, 142), width=2)
    return result


def stills():
    times = (4.28, 7.98, 10.98, 15.86, 20.82)
    panels = [frame(t) for t in times]
    panels[3].save(OUT / "radial-access-still.png")
    sheet = Image.new("RGB", (1600, 637), (224, 236, 228))
    for n, panel in enumerate(panels):
        thumb = panel.resize((520, 292), Image.Resampling.LANCZOS)
        x = 10 + (n % 3) * 530
        y = 12 + (n // 3) * 310
        sheet.paste(thumb, (x, y))
        ImageDraw.Draw(sheet).text((x + 8, y + 294), f"{times[n]:05.2f}s", font=font(14), fill=MUTED)
    sheet.save(OUT / "radial-access-motion-check.jpg", quality=93)


def render():
    cmd = [
        str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an",
        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-movflags", "+faststart", str(VIDEO),
    ]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as run:
        for f in range(DURATION * FPS):
            run.stdin.write(frame(f / FPS).tobytes())
        run.stdin.close()
        if run.wait():
            raise RuntimeError("FFmpeg failed")


def add_narration():
    # Each cut falls within a measured silent interval. Speech rate is preserved.
    cuts = (0.0, 6.98, 9.01, 11.99, 16.67)
    pads_ms = (350, 776, 965, 1896)
    slices = [
        f"[1:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,adelay={pad}:all=1[s{i}]"
        for i, (a, b, pad) in enumerate(zip(cuts, cuts[1:], pads_ms))
    ]
    tracks = "".join(f"[s{i}]" for i in range(len(pads_ms)))
    graph = ";".join(slices + [f"{tracks}concat=n=4:v=0:a=1,apad=whole_dur=21,atrim=end=21[voice]"])
    subprocess.run([
        str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(VIDEO), "-i", str(NARRATION), "-filter_complex", graph,
        "-map", "0:v:0", "-map", "[voice]", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(NARRATED_VIDEO),
    ], check=True)


if __name__ == "__main__":
    stills()
    if "--still-only" not in sys.argv:
        render()
        if "--narrate" in sys.argv:
            add_narration()
