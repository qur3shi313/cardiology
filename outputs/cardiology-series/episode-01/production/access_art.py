"""Animated cutaways for the wrist and groin access sequences."""

from bisect import bisect_left
from functools import lru_cache
from math import hypot, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont


SIZE = (960, 450)
INK = (227, 240, 241)
MUTED = (150, 181, 187)
TEAL = (119, 222, 205)
GOLD = (251, 202, 110)
SHEATH = (100, 225, 209)
MICRO = (112, 183, 249)


@lru_cache(maxsize=12)
def _font(size, bold=False):
    names = ("segoeuib.ttf", "DejaVuSans-Bold.ttf") if bold else ("segoeui.ttf", "DejaVuSans.ttf")
    for name in names:
        for candidate in (str(Path("C:/Windows/Fonts") / name), name):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _mix(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def _ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def _bezier(points, count=40):
    for index in range(count + 1):
        t = index / count
        a = 1 - t
        yield tuple(
            a ** 3 * start + 3 * a ** 2 * t * control1 + 3 * a * t ** 2 * control2 + t ** 3 * end
            for start, control1, control2, end in zip(*points)
        )


class _Track:
    def __init__(self, points):
        self.points = list(points)
        self.distances = [0.0]
        for first, second in zip(self.points, self.points[1:]):
            self.distances.append(self.distances[-1] + hypot(second[0] - first[0], second[1] - first[1]))

    def at(self, distance):
        if distance <= 0:
            x, y = self.points[0]
            next_x, next_y = self.points[1]
            step = self.distances[1]
            return x + (next_x - x) * distance / step, y + (next_y - y) * distance / step
        if distance >= self.distances[-1]:
            return self.points[-1]
        end = bisect_left(self.distances, distance)
        span = self.distances[end] - self.distances[end - 1]
        fraction = (distance - self.distances[end - 1]) / span
        return tuple(a + (b - a) * fraction for a, b in zip(self.points[end - 1], self.points[end]))

    def between(self, start, end):
        if end <= start:
            return []
        low = bisect_left(self.distances, start)
        high = bisect_left(self.distances, end)
        return [self.at(start), *self.points[low:high], self.at(end)]


@lru_cache(maxsize=2)
def _anatomy(route):
    femoral = route == "femoral"
    center = 273 if femoral else 257
    radius = 29 if femoral else 19
    surface = list(_bezier(((32, 157), (300, 114), (672, 143), (928, 139))))
    start, wall = (122, 63), (317, center - radius + 6)
    slope = (wall[1] - start[1]) / (wall[0] - start[0])
    before_wall = [(122 + 195 * n / 40, 63 + (wall[1] - 63) * n / 40) for n in range(40)]
    path = _Track([
        *before_wall,
        *list(_bezier((wall, (wall[0] + 20, wall[1] + 20 * slope), (391, center), (426, center))))[:-1],
        (426, center), (530, center), (679, center), (789, center - 1), (901, center - 4),
    ])
    wall_entry = path.distances[40]
    return center, radius, surface, path, wall_entry


def _strip(draw, surface, top, bottom, color):
    draw.polygon(
        [(x, y + top) for x, y in surface] + [(x, y + bottom) for x, y in reversed(surface)],
        fill=color,
    )


def _vessel(draw, main, branch, radius):
    for width, color in (
        (2 * radius + 12, (72, 38, 56)),
        (2 * radius + 5, (141, 62, 72)),
        (2 * radius, (183, 90, 91)),
        (2 * radius - 13, (111, 42, 59)),
        (2 * radius - 20, (132, 49, 65)),
    ):
        if branch:
            draw.line(branch, fill=color, width=max(4, round(width * .61)), joint="curve")
        draw.line(main, fill=color, width=width, joint="curve")
    draw.line([(x, y - radius + 5) for x, y in main], fill=(229, 129, 115), width=2, joint="curve")


@lru_cache(maxsize=2)
def _base(route):
    center, radius, surface, _, _ = _anatomy(route)
    art = Image.new("RGB", SIZE, (12, 24, 33))
    draw = ImageDraw.Draw(art)
    for y in range(SIZE[1]):
        tone = _mix((15, 33, 43), (10, 20, 29), y / SIZE[1])
        draw.line((0, y, SIZE[0], y), fill=tone)
    draw.rounded_rectangle((13, 12, 947, 438), 22, outline=(48, 77, 85), width=1)
    for y in range(31, 78):
        draw.line((42, y, 918, y), fill=_mix((18, 39, 49), (15, 33, 43), (y - 31) / 47))
    _strip(draw, surface, 0, 239, (75, 48, 61))
    for y in range(1, 238, 2):
        if y < 15:
            tone = _mix((241, 178, 151), (190, 113, 103), y / 15)
        elif y < 70:
            tone = _mix((180, 111, 98), (126, 73, 79), (y - 15) / 55)
        else:
            tone = _mix((102, 61, 77), (65, 46, 64), (y - 70) / 168)
        _strip(draw, surface, y, y + 2, tone)
    draw.line(surface, fill=(252, 191, 164), width=2, joint="curve")

    grain = Random(28 if route == "femoral" else 14)
    for _ in range(155):
        x = grain.randrange(47, 916)
        local_y = 148 - 12 * sin((x - 22) / 960 * 3.0)
        y = local_y + grain.randrange(25, 226)
        length = grain.randrange(8, 42)
        if y < 211:
            tone = grain.choice(((177, 108, 97), (144, 87, 88), (159, 95, 88)))
        else:
            tone = grain.choice(((91, 61, 77), (96, 65, 80), (77, 53, 70)))
        draw.arc((x, y, min(x + length, 923), y + 7), 18, 166, fill=tone, width=1)

    main = list(_bezier(((49, center + 8), (265, center - 6), (672, center + 2), (926, center - 5))))
    branch = list(_bezier(((185, center + 1), (142, center + 16), (100, center + 49), (57, center + 69)))) if route == "femoral" else None
    _vessel(draw, main, branch, radius)
    draw.line((34, 384, 926, 384), fill=(63, 74, 83), width=1)
    draw.text((181, 39), "Groin cutaway" if route == "femoral" else "Wrist cutaway", font=_font(26, True), fill=INK)
    artery = "Common femoral artery" if route == "femoral" else "Radial artery"
    _leader(draw, artery, (683, 405), (782, center + 7), elbow=(782, 373))
    if route == "femoral":
        _leader(draw, "Femoral artery branches", (43, 405), (112, center + 37), elbow=(112, 374))
    else:
        _leader(draw, "Skin surface", (43, 405), (66, 154), elbow=(42, 375))
    return art


def _leader(draw, label, text_at, target, elbow):
    draw.line((target, elbow, (elbow[0], text_at[1] - 7)), fill=(166, 181, 182), width=1)
    x, y = target
    draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=INK)
    draw.text(text_at, label, font=_font(17), fill=MUTED)


def _tube(draw, path, tip, length, color, width, hub=True, lumen=True):
    start = tip - length
    points = path.between(start, tip)
    draw.line(points, fill=(22, 46, 57), width=width + 4, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")
    if lumen:
        draw.line(points, fill=_mix(color, (28, 48, 62), .45), width=max(2, width // 3), joint="curve")
    if hub:
        anchor = path.at(start)
        draw.line((path.at(start - 13), path.at(start + 14)), fill=(31, 63, 75), width=width + 10)
        draw.line((path.at(start - 11), path.at(start + 11)), fill=color, width=width + 5)
        draw.ellipse((anchor[0] - 2, anchor[1] - 2, anchor[0] + 2, anchor[1] + 2), fill=(202, 235, 236))


def _needle(draw, path, tip):
    _tube(draw, path, tip - 4, 185, (188, 219, 226), 7, lumen=False)
    draw.line((path.at(tip - 10), path.at(tip)), fill=(238, 247, 243), width=3)


def _wire(draw, path, tip, start=-72, color=GOLD, j_tip=False, width=2):
    points = path.between(start, tip)
    if not points:
        return
    draw.line(points, fill=(63, 47, 46), width=width + 3, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")
    if j_tip and tip > path.distances[82]:
        x, y = points[-1]
        draw.arc((x - 13, y - 12, x + 1, y + 1), 270, 90, fill=color, width=2)


def _sheath(draw, path, tip, length, color, dilator_tip=None, sidearm=False):
    _tube(draw, path, tip, length, color, 16)
    if sidearm:
        x, y = path.at(tip - length)
        arm = [(x, y), (x + 12, y - 13), (x + 32, y - 17)]
        draw.line(arm, fill=(29, 63, 74), width=9, joint="curve")
        draw.line(arm, fill=color, width=5, joint="curve")
        draw.line(((x + 28, y - 16), (x + 37, y - 18)), fill=(166, 218, 213), width=8)
    if dilator_tip is not None:
        base = dilator_tip - length - 19
        draw.line(path.between(base, dilator_tip - 10), fill=(201, 235, 233), width=7, joint="curve")
        draw.line(path.between(dilator_tip - 10, dilator_tip), fill=(201, 235, 233), width=3, joint="curve")


def _closure(draw, route, progress, x):
    # The sheath is already clear when the dressing meets the skin.
    y = 142 - 39 * (1 - _ease(progress))
    if route == "radial":
        draw.rounded_rectangle((x - 94, y - 7, x + 95, y + 5), 5, fill=(64, 146, 157), outline=(149, 232, 215), width=2)
        draw.rounded_rectangle((x - 35, y - 19, x + 35, y + 10), 10, fill=(94, 185, 183), outline=(178, 239, 222), width=2)
        draw.rounded_rectangle((x - 17, y - 11, x + 17, y + 4), 5, fill=(148, 221, 205))
    else:
        draw.rounded_rectangle((x - 35, y - 5, x + 43, y + 8), 4, fill=(232, 228, 215), outline=(243, 236, 222), width=1)
        draw.rounded_rectangle((x - 12, y - 24, x + 88, y - 5), 9, fill=(104, 170, 182), outline=(168, 221, 219), width=2)
        draw.rounded_rectangle((x + 60, y - 36, x + 147, y - 13), 9, fill=(104, 170, 182), outline=(168, 221, 219), width=2)
        for offset in (-3, 18, 39):
            draw.line((x + offset, y - 45, x + offset, y - 29), fill=TEAL, width=2)
            draw.line(((x + offset - 4, y - 34), (x + offset, y - 29), (x + offset + 4, y - 34)), fill=TEAL, width=2)


def draw_access(image, box, route, stage, progress):
    """Draw one stage of the access sequence into an existing Pillow image."""
    femoral = route == "femoral"
    art = _base(route).copy()
    draw = ImageDraw.Draw(art)
    _, _, _, track, entry = _anatomy(route)
    t = _ease(progress)
    needle = short_wire = exchange = micro = micro_dilator = None
    working = working_dilator = long_wire = catheter = None
    sheath_tip = entry + 70
    micro_tip = entry + 48
    short_tip = entry + 195
    long_tip = track.distances[-1] - 9
    catheter_tip = long_tip - 24
    short_color = (241, 202, 111) if femoral else GOLD
    label = "Artery access site"

    if stage == "site":
        x, y = track.at(entry)
        ring = 11 + round(5 * t)
        draw.ellipse((x - ring, y - ring, x + ring, y + ring), outline=TEAL, width=2)
        draw.line((x - 8, y, x + 8, y), fill=TEAL, width=1)
        draw.line((x, y - 8, x, y + 8), fill=TEAL, width=1)
    elif stage == "needle":
        needle = entry - 91 + 96 * t
        label = "Micropuncture needle" if femoral else "Access needle"
    elif stage in ("short_wire", "needle_out"):
        needle = entry + 5 - (236 * t if stage == "needle_out" else 0)
        short_wire = short_tip if stage == "needle_out" else entry + 5 + (short_tip - entry - 5) * t
        label = "0.018-inch wire" if femoral else "Short guidewire"
        if stage == "needle_out":
            label = "Needle out, guidewire stays"
    elif stage in ("sheath_in", "short_out"):
        if femoral:
            micro = micro_tip if stage == "short_out" else entry - 99 + (micro_tip - entry + 99) * t
            micro_dilator = micro + 12 - (241 * t if stage == "short_out" else 0)
        else:
            working = sheath_tip if stage == "short_out" else entry - 99 + (sheath_tip - entry + 99) * t
            working_dilator = working + 12 - (258 * t if stage == "short_out" else 0)
        short_wire = short_tip - (short_tip + 104) * t if stage == "short_out" else short_tip
        label = "Small introducer and dilator" if femoral else "Sheath and dilator"
        if stage == "short_out":
            label = "Outer introducer stays in place" if femoral else "Sheath stays in place"
    elif stage in ("exchange_wire", "micro_out"):
        micro = micro_tip - (235 * t if stage == "micro_out" else 0)
        exchange = short_tip + 66 if stage == "micro_out" else entry - 23 + (short_tip + 66 - entry + 23) * t
        label = "Introducer out, exchange wire stays" if stage == "micro_out" else "0.035-inch exchange wire"
    elif stage in ("working_sheath", "working_dilator_out"):
        working = sheath_tip if stage == "working_dilator_out" else entry - 99 + (sheath_tip - entry + 99) * t
        working_dilator = working + 12 - (258 * t if stage == "working_dilator_out" else 0)
        exchange = short_tip + 66 - (short_tip + 169) * t if stage == "working_dilator_out" else short_tip + 66
        label = "Working sheath and dilator" if stage == "working_sheath" else "Working sheath stays in place"
    elif stage == "long_wire":
        working = sheath_tip
        long_wire = entry - 24 + (long_tip - entry + 24) * t
        label = "Long guidewire"
    elif stage == "catheter":
        working = sheath_tip
        catheter = entry - 34 + (catheter_tip - entry + 34) * t
        long_wire = long_tip
        label = "Diagnostic catheter"
    elif stage == "catheter_out":
        working = sheath_tip
        catheter = catheter_tip - (catheter_tip + 65) * t
        label = "Catheter withdrawal"
    elif stage in ("remove", "closure"):
        if stage == "remove":
            working = sheath_tip - (sheath_tip + 90) * _ease(progress / .57)
        label = "Direct pressure and dressing" if femoral else "Wrist pressure band"

    if needle is not None and needle > 0:
        _needle(draw, track, needle)
    if micro is not None and micro > -20:
        _sheath(draw, track, micro, 209, MICRO, micro_dilator)
    if working is not None and working > -20:
        _sheath(draw, track, working, 231, SHEATH, working_dilator, sidearm=True)
    if catheter is not None and catheter > -20:
        _tube(draw, track, catheter, 850, (212, 232, 238), 8, hub=False)
    if short_wire is not None:
        _wire(draw, track, short_wire, color=short_color, width=1 if femoral else 2)
    if exchange is not None:
        _wire(draw, track, exchange, j_tip=True, width=3)
    if long_wire is not None:
        _wire(draw, track, long_wire, j_tip=True, width=3)
    if stage == "closure" or (stage == "remove" and progress >= .57):
        # The skin contact point is above and lateral to the arterial puncture.
        first_x, first_y = track.points[0]
        wall_x, wall_y = track.points[40]
        contact_x = round(first_x + (wall_x - first_x) * (144 - first_y) / (wall_y - first_y))
        _closure(draw, route, 1 if stage == "closure" else (progress - .57) / .43, x=contact_x)

    draw.rounded_rectangle((526, 30, 913, 75), 13, fill=(18, 39, 48), outline=(68, 111, 119))
    draw.ellipse((545, 49, 552, 56), fill=TEAL)
    draw.text((565, 40), label, fill=INK, font=_font(20, True))
    x0, y0, x1, y1 = map(round, box)
    if x1 > x0 and y1 > y0:
        image.paste(art.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR), (x0, y0))
