"""Render an original silent cutaway of balloon-expandable coronary stenting."""

from functools import lru_cache
from math import cos, exp, pi, sin
from pathlib import Path
from random import Random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps


OUT = Path(__file__).resolve().parent
WRIST = OUT.parents[1] / "episode-01/revision/wrist-proof"
sys.dont_write_bytecode = True
sys.path.insert(0, str(WRIST))
from render_wrist_proof import FFMPEG, GREEN, INK, LOGO, MUTED, font, smooth


W, H, FPS = 1600, 900, 24
TOTAL = 22
STOPS = (0, 4.50, 8.75, 13.15, 18.25, TOTAL)
MARKS = (3.85, 8.40, 12.62, 15.65, 16.74, 20.80)
TEXT = (
    ("The guidewire crosses the narrowing", "The fine wire passes through the channel that remains open."),
    ("The balloon carries the stent", "The folded balloon and collapsed stent move together over the wire."),
    ("The balloon expands the stent", "The balloon opens the mesh and widens the treated part of the artery."),
    ("The balloon deflates and comes out", "The expanded mesh stays in position as the balloon withdraws."),
    ("The stent stays in the artery", "The mesh helps hold the treated segment open."),
)
MIN_X, MAX_X = 110, 1490
TARGET = 834
STENT_HALF = 176
BALLOON_HALF = 203
DEVICE_COLOR = "#71c0b8"


def blend(a, b, amount):
    return tuple(round(x+(y-x)*amount) for x, y in zip(a, b))


def stroke(draw, points, fill, width=1):
    if len(points) > 1:
        draw.line(points, fill=fill, width=width, joint="curve")


def center(x):
    return 491 + 16*sin((x-370)/249) + 8*sin((x+25)/510)


def treatment(x):
    return smooth((x-(TARGET-STENT_HALF-37))/37) * smooth(((TARGET+STENT_HALF+37)-x)/37)


def plaque_profile(x):
    return exp(-abs((x-TARGET)/157)**3.15)


def lumen_radius(x, expansion, side):
    narrowed = 81 - plaque_profile(x)*(59 if side == -1 else 44)
    return narrowed+(77-narrowed)*treatment(x)*expansion


def surface(xs, expansion, offset):
    return tuple((x, center(x)+offset(x, expansion)) for x in xs)


def body(draw, upper, lower, color):
    draw.polygon(upper+lower[::-1], fill=color)


def leader(draw, text, origin, target):
    x, y = origin
    width = draw.textlength(text, font=font(25, "semibold"))
    start = (x+width+13, y+17) if target[0] > x+width else (x-11, y+17)
    mid = (start[0]+22 if target[0] > start[0] else start[0]-22, y+17)
    stroke(draw, (start, mid, target), "#426c59", 2)
    tx, ty = target
    draw.ellipse((tx-4, ty-4, tx+4, ty+4), fill="#f7f2d7", outline="#487663", width=2)
    draw.text(origin, text, fill=INK, font=font(25, "semibold"))


@lru_cache(maxsize=1)
def background():
    image = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(image)
    for row in range(H):
        draw.line((0, row, W, row), fill=blend((246, 251, 245), (219, 234, 225), row/H))
    draw.rounded_rectangle((76, 57, 126, 107), 8, fill="white")
    logo = ImageOps.fit(Image.open(LOGO).convert("RGB"), (48, 48), method=Image.Resampling.LANCZOS)
    image.paste(logo, (77, 58))
    draw.text((144, 62), "Elysian Biomedical LLP", fill=GREEN, font=font(24, "semibold"))
    draw.text((144, 93), "Cardiology Education Series", fill=MUTED, font=font(18))
    draw.text((1521, 66), "CORONARY ANGIOPLASTY", fill=GREEN, font=font(20, "semibold"), anchor="rt")
    stroke(draw, ((76, 128), (1522, 128)), "#b3ccbf", 2)
    draw.text((76, 151), "Coronary angioplasty and stenting", font=font(58, "heading"), fill=INK)
    draw.rounded_rectangle((76, 257, 1522, 712), 22, fill="#f1f8f0", outline="#bfd5c6", width=2)
    draw.rounded_rectangle((102, 280, 353, 322), 8, fill="#deece2")
    draw.text((119, 289), "Illustrative artery cutaway", font=font(22, "semibold"), fill=GREEN)
    return image


@lru_cache(maxsize=31)
def arterial_layer(index):
    expansion = index/30
    image = background().copy()
    draw = ImageDraw.Draw(image)
    xs = tuple(range(MIN_X, MAX_X+1, 4))
    upper_wall = surface(xs, expansion, lambda x, p: -111 - 9*treatment(x)*p)
    lower_wall = surface(xs, expansion, lambda x, p: 111 + 7*treatment(x)*p)
    shadow = tuple((x, y+14) for x, y in upper_wall)
    bottom_shadow = tuple((x, y+15) for x, y in lower_wall)
    body(draw, shadow, bottom_shadow, "#dce9de")
    body(draw, upper_wall, lower_wall, "#a75f64")
    for i in range(26):
        upper = surface(xs, expansion, lambda x, p: -108+i*.96 - 9*treatment(x)*p)
        lower = surface(xs, expansion, lambda x, p: 108-i*.96 + 7*treatment(x)*p)
        body(draw, upper, lower, blend((189, 106, 104), (123, 57, 70), i/25))
    upper_lumen = surface(xs, expansion, lambda x, p: -lumen_radius(x, p, -1))
    lower_lumen = surface(xs, expansion, lambda x, p: lumen_radius(x, p, 1))
    body(draw, upper_lumen, lower_lumen, "#632c41")
    for i in range(1, 22):
        fraction = i/22
        upper = tuple((x, y+(center(x)-y)*fraction) for x, y in upper_lumen)
        lower = tuple((x, y+(center(x)-y)*fraction) for x, y in lower_lumen)
        body(draw, upper, lower, blend((106, 43, 59), (149, 75, 78), fraction*.84))
    lesion_xs = tuple(range(601, 1069, 3))
    for side in (-1, 1):
        inner = surface(lesion_xs, expansion, lambda x, p: side*lumen_radius(x, p, side))
        outer = surface(lesion_xs, expansion,
                        lambda x, p: side*(lumen_radius(x, p, side)
                                           +(25 if side == -1 else 17)*plaque_profile(x)
                                           +(81-lumen_radius(x, p, side))*.50))
        body(draw, outer, inner, "#d8a76e" if side == -1 else "#c69164")
        stroke(draw, inner, "#e9be8f", 3)
        for x in range(664, 1014, 17):
            noise = Random(x+side)
            for _ in range(4):
                at = x+noise.uniform(-7, 7)
                thickness = ((25 if side == -1 else 17)*plaque_profile(at)
                             +(81-lumen_radius(at, expansion, side))*.50)
                y = center(at)+side*(lumen_radius(at, expansion, side)+thickness*noise.uniform(.19, .73))
                draw.ellipse((at-1, y-1, at+1, y+1), fill="#a77055")
    stroke(draw, upper_wall, "#d89083", 3)
    stroke(draw, lower_wall, "#975965", 3)
    return image


def guidewire(draw, tip):
    if tip <= MIN_X+5:
        return
    tip = min(MAX_X-5, tip)
    points = []
    for x in range(MIN_X, round(tip)+1, 4):
        hook = 12*smooth((x-tip+39)/39)
        points.append((x, center(x)-hook))
    stroke(draw, points, "#342838", 7)
    stroke(draw, points, "#f5d59c", 4)
    x, y = points[-1]
    draw.ellipse((x-2, y-2, x+2, y+2), fill="#ffeac2")


def stent_paths(x0, radius, front):
    rays = 20
    period = 2*pi/rays
    ring_centers = tuple(x0 + dx for dx in range(-153, 154, 34))
    lines = []
    for index, x in enumerate(ring_centers):
        phase = (index % 2)*period*.50
        nodes = []
        for j in range(rays+1):
            theta = phase+j*period
            xx = x + (8 if j % 2 else -8)
            nodes.append(((xx, center(xx)+radius*sin(theta)), theta))
        for (a, ta), (b, tb) in zip(nodes, nodes[1:]):
            if (cos((ta+tb)*.5) >= 0) == front:
                lines.append((a, b))
        if index+1 < len(ring_centers):
            for j in (0, 4, 8, 12, 16):
                theta = phase+j*period
                if (cos(theta) >= 0) == front:
                    xa, xb = x+8, ring_centers[index+1]-8
                    y = radius*sin(theta)
                    lines.append(((xa, center(xa)+y), (xb, center(xb)+y)))
    return lines


def stent(draw, x0, radius, front):
    for a, b in stent_paths(x0, radius, front):
        if MIN_X <= a[0] <= MAX_X and MIN_X <= b[0] <= MAX_X:
            stroke(draw, (a, b), "#35454f" if front else "#58616a", 6 if front else 3)
            if front:
                stroke(draw, (a, b), "#d2ddd9", 3)


def balloon(image, x0, radius):
    draw = ImageDraw.Draw(image, "RGBA")
    left, right = x0-BALLOON_HALF, x0+BALLOON_HALF
    if right <= MIN_X:
        return
    end = min(MAX_X, round(right))
    shaft = tuple((x, center(x)) for x in range(MIN_X, end+1, 4))
    stroke(draw, shaft, "#154d50", 15)
    stroke(draw, shaft, DEVICE_COLOR, 10)
    stroke(draw, tuple((x, y-2) for x, y in shaft), "#dcf0e3", 2)
    xs = tuple(range(max(MIN_X, round(left)), end+1, 3))
    if len(xs) < 2:
        return

    def width(x):
        shoulder = smooth((x-left)/40)*smooth((right-x)/40)
        return 4+max(0, radius-4)*shoulder

    upper = tuple((x, center(x)-width(x)) for x in xs)
    lower = tuple((x, center(x)+width(x)) for x in xs)
    body(draw, upper, lower, (136, 213, 201, 170))
    stroke(draw, upper, "#287773", 3)
    stroke(draw, lower, "#246563", 3)
    stroke(draw, tuple((x, center(x)-width(x)*.55) for x in xs), "#bce5d5", 3)


def stage_at(t):
    return next((i for i in range(4) if t < STOPS[i+1]), 4)


def frame(t):
    index = stage_at(t)
    inflated = smooth((t-9.25)/2.9)
    deflated = smooth((t-13.48)/2.05)
    contracted = inflated*(1-deflated)
    advanced = smooth((t-4.56)/3.29)
    removed = smooth((t-15.88)/2.22)
    x0 = -BALLOON_HALF+MIN_X + (TARGET+BALLOON_HALF-MIN_X)*advanced
    x0 -= (TARGET+BALLOON_HALF-MIN_X)*removed
    wire_in = smooth((t-.52)/2.66)
    wire_out = smooth((t-18.76)/1.45)
    wire_tip = MIN_X+(1325-MIN_X)*wire_in*(1-wire_out)
    shaft_on_screen = t > 4.56 and removed < 1
    stent_x = TARGET if t >= 9.25 else x0
    mesh_radius = 12+(76-12)*inflated
    balloon_radius = 9+(72-9)*contracted
    image = arterial_layer(round(inflated*30)).copy()
    draw = ImageDraw.Draw(image)
    if t > 4.56:
        stent(draw, stent_x, mesh_radius, False)
    if shaft_on_screen:
        balloon(image, x0, balloon_radius)
    guidewire(draw, wire_tip)
    if t > 4.56:
        stent(draw, stent_x, mesh_radius, True)
    if index == 0:
        leader(draw, "Plaque", (1001, 345), (TARGET+33, center(TARGET)-43))
        if t > 1.7:
            leader(draw, "Guidewire", (1020, 634), (min(wire_tip-12, 1216), center(min(wire_tip-12, 1216))))
    elif index == 1 and advanced > .35:
        leader(draw, "Collapsed stent", (1075, 345), (x0+125, center(x0+125)-11))
        leader(draw, "Folded balloon", (373, 632), (x0-185, center(x0-185)+6))
    elif index == 2:
        leader(draw, "Balloon", (452, 631), (TARGET-183, center(TARGET-183)+balloon_radius*.62))
        leader(draw, "Expanding mesh", (1090, 343), (TARGET+100, center(TARGET+100)-mesh_radius*.89))
    elif index == 3:
        leader(draw, "Stent stays in place", (1057, 343), (TARGET+100, center(TARGET+100)-mesh_radius*.88))
    elif index == 4:
        leader(draw, "Expanded stent", (1065, 343), (TARGET+110, center(TARGET+110)-mesh_radius*.87))
    heading, detail = TEXT[index]
    draw.text((77, 751), heading, font=font(34, "semibold"), fill=GREEN)
    draw.text((77, 802), detail, font=font(25), fill=MUTED)
    stroke(draw, ((77, 866), (1521, 866)), "#a4bfae", 2)
    stroke(draw, ((77, 866), (77+1444*t/TOTAL, 866)), "#427b66", 4)
    for stop in STOPS[1:-1]:
        x = 77+1444*stop/TOTAL
        stroke(draw, ((x, 861), (x, 871)), "#81a591", 2)
    return image


def render():
    target = OUT / "coronary-angioplasty-stent-prototype.mp4"
    command = [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
               "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
               str(target)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    with process.stdin as pipe:
        for index in range(FPS*TOTAL):
            pipe.write(frame(index/FPS).tobytes())
    if process.wait():
        raise RuntimeError("Could not encode the prototype")
    subprocess.run([str(FFMPEG), "-v", "error", "-xerror", "-i", str(target),
                    "-f", "null", "-"], check=True)
    print("22 seconds, 1920x1080, 24 fps, video fully decoded", flush=True)
    return target


def contact_sheet(target):
    width, height = 512, 288
    select = "+".join(f"eq(n\\,{round(mark*FPS)})" for mark in MARKS)
    raw = subprocess.run([str(FFMPEG), "-v", "error", "-i", str(target),
                          "-vf", f"select={select},scale={width}:{height}", "-fps_mode", "vfr",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True,
                         capture_output=True).stdout
    stride = width*height*3
    assert len(raw) == len(MARKS)*stride
    sheet = Image.new("RGB", (1586, 637), "#dcebe1")
    draw = ImageDraw.Draw(sheet)
    for i, at in enumerate(MARKS):
        x, y = 10+(i%3)*525, 9+(i//3)*313
        panel = Image.frombytes("RGB", (width, height), raw[i*stride:(i+1)*stride])
        sheet.paste(panel, (x, y))
        draw.text((x+7, y+291), f"{at:.2f} s", font=font(16), fill=MUTED)
    sheet.save(OUT / "stent-prototype-decoded-contact-sheet.jpg", quality=94)


if __name__ == "__main__":
    contact_sheet(render())
