"""Render the opening and diagnostic context for the angioplasty episode."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
from math import cos, pi, sin
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter


OUT = Path(__file__).resolve().parent
EPISODE = OUT.parents[1]
SERIES = EPISODE.parent
sys.dont_write_bytecode = True


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = load("angioplasty_prototype", EPISODE / "prototype/render_stent_prototype.py")
shared = load("episode_coronary", SERIES / "episode-01/revision/shared-coronary-scenes/render_shared_coronary.py")
W, H = proto.W, proto.H
FPS = 24
INK, GREEN, MUTED = proto.INK, proto.GREEN, proto.MUTED
font, smooth = proto.font, proto.smooth
LINE = "#b9d1c4"
WHITE = "#f6faf4"
MINT = "#e5f2e8"
PANEL = "#edf5ec"
GOLD = "#e8b983"
WARM = "#a75052"


@lru_cache(maxsize=1)
def masthead():
    original = Image.open(EPISODE / "assets/episode-02-opening.png").convert("RGB")
    return original.crop((0, 0, 1920, 171)).resize((1600, 143), Image.Resampling.LANCZOS)


@lru_cache(maxsize=20)
def background(title, detail=""):
    image = Image.new("RGB", (W, H))
    pen = ImageDraw.Draw(image)
    for y in range(H):
        pen.line((0, y, W, y), fill=proto.blend((248, 251, 246), (223, 239, 232), y / H))
    image.paste(masthead(), (0, 0))
    size = 58
    while pen.textlength(title, font=font(size, "heading")) > 1450:
        size -= 1
    pen.text((75, 151), title, font=font(size, "heading"), fill=INK)
    pen.line((76, 847, 1523, 847), fill=LINE, width=1)
    if detail:
        pen.text((76, 870), detail, font=font(19), fill=MUTED, anchor="lm")
    return image


def card(pen, rect, *, fill=WHITE, outline=LINE, radius=23):
    pen.rounded_rectangle(rect, radius, fill=fill, outline=outline, width=2)


def label(pen, point, text_at, label_text, *, accent=GREEN):
    x, y = text_at
    px, py = point
    near = x if px < x else x + pen.textlength(label_text, font=font(24, "semibold"))
    mid = near + (-27 if px < x else 27)
    pen.line(((px, py), (mid, y + 13), (near, y + 13)), fill="#527d68", width=2, joint="curve")
    pen.ellipse((px - 4, py - 4, px + 4, py + 4), fill="#f9eac3", outline="#426954", width=2)
    pen.text((x, y), label_text, font=font(24, "semibold"), fill=accent)


@lru_cache(maxsize=1)
def heart_source():
    layer = Image.new("RGBA", (W, H))
    xy, *_ = shared.base_heart(ImageDraw.Draw(layer), "left", show_catheter=False)
    crop = (110, 305, 596, 744)
    x, y = xy(shared.LAD[31])
    return layer.crop(crop), (x - crop[0], y - crop[1])


def heart(image, x, y, scale=1.0, *, target=True, treated=False):
    art, point = heart_source()
    image.paste(art.resize((round(art.width * scale), round(art.height * scale)), Image.Resampling.LANCZOS),
                (round(x), round(y)), art.getchannel("A").resize((round(art.width * scale), round(art.height * scale)), Image.Resampling.LANCZOS))
    px, py = x + point[0] * scale, y + point[1] * scale
    if target:
        pen = ImageDraw.Draw(image)
        radius = round(19 * scale)
        pen.ellipse((px - radius, py - radius, px + radius, py + radius), outline=GOLD, width=3)
        if treated:
            for off in (-5, 0, 5):
                pen.line((px - 4 + off*.2, py - 6 + off, px + 4 + off*.2, py - 6 + off), fill="#d5ece0", width=2)
    return px, py


ART_CROP = (104, 347, 1495, 649)


@lru_cache(maxsize=2)
def artery_source(treated):
    source = proto.arterial_layer(30 if treated else 0).copy()
    if treated:
        draw = ImageDraw.Draw(source)
        proto.stent(draw, proto.TARGET, 76, False)
        proto.stent(draw, proto.TARGET, 76, True)
    cut = source.crop(ART_CROP)
    empty = proto.background().crop(ART_CROP)
    difference = ImageChops.difference(cut, empty)
    alpha = ImageChops.lighter(ImageChops.lighter(difference.getchannel("R"), difference.getchannel("G")), difference.getchannel("B"))
    cut.putalpha(alpha.point(lambda v: min(255, v * 27)))
    return cut


def artery(image, rect, *, treated=False):
    x0, y0, x1, y1 = rect
    source = artery_source(treated)
    art = source.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    image.paste(art, (x0, y0), art)

    def position(x, y):
        return (x0 + (x - ART_CROP[0]) / source.width * (x1 - x0),
                y0 + (y - ART_CROP[1]) / source.height * (y1 - y0))

    return position


def pill(pen, pos, text, *, fill=MINT, ink=GREEN):
    x, y = pos
    width = pen.textlength(text, font=font(22, "semibold"))
    pen.rounded_rectangle((x, y, x + width + 33, y + 44), 9, fill=fill)
    pen.text((x + 16, y + 9), text, font=font(22, "semibold"), fill=ink)


def narrow_scene(title, footer, *, with_label=True):
    image = background(title, footer).copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 743))
    position = artery(image, (108, 361, 1490, 673))
    if with_label:
        label(pen, position(proto.TARGET, proto.center(proto.TARGET) - 8), (1005, 309), "Narrowed channel")
    return image, position


def blend_frames(a, b, amount):
    if amount <= 0:
        return a
    if amount >= 1:
        return b
    return Image.blend(a, b, amount)


@lru_cache(maxsize=16)
def opener(zoom):
    image = background("Coronary angioplasty and stents", "From the angiogram to treatment, the final X-ray check and recovery").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 762))
    scale = 1.03 + .14 * zoom
    x, y = 185 - round(15 * zoom), 280 - round(19 * zoom)
    point = heart(image, x, y, scale)
    label(pen, point, (806, 485), "Narrowed section in the LAD")
    return image


@lru_cache(maxsize=1)
def opener_detail():
    image, _ = narrow_scene("Coronary angioplasty and stents", "From the angiogram to treatment, the final X-ray check and recovery")
    return image


def p01(p):
    zoom = round(8 * smooth((p - .17) / .40)) / 8
    image = opener(zoom)
    return blend_frames(image, opener_detail(), smooth((p - .39) / .19))


@lru_cache(maxsize=2)
def plaque_scene(clot):
    image, position = narrow_scene("Why the artery narrows", "Plaque can build up in the artery wall and narrow the space for blood flow.", with_label=False)
    pen = ImageDraw.Draw(image)
    if clot:
        card(pen, (1035, 279, 1485, 546), fill="#f8f3e9", outline="#ccba9f", radius=17)
        pen.text((1057, 300), "A clot can form at plaque", font=font(24, "semibold"), fill=INK)
        pen.rounded_rectangle((1061, 367, 1459, 480), 20, fill="#b77073", outline="#9f6167", width=2)
        pen.rounded_rectangle((1061, 394, 1459, 453), 9, fill="#763c52")
        pen.polygon(((1161, 394), (1187, 406), (1224, 425), (1245, 433), (1261, 427), (1280, 411), (1319, 394)), fill="#dab07e")
        for x, y, r in ((1237, 430, 13), (1250, 423, 13), (1263, 428, 12), (1254, 437, 9), (1233, 436, 9)):
            pen.ellipse((x-r, y-r*.72, x+r, y+r*.72), fill="#7f344d", outline="#ac6571", width=2)
        pen.text((1059, 501), "Separate heart attack example", font=font(19), fill=MUTED)
        label(pen, position(proto.TARGET - 19, proto.center(proto.TARGET) - 42), (353, 334), "Plaque")
    else:
        label(pen, position(proto.TARGET + 28, proto.center(proto.TARGET) - 42), (1017, 307), "Plaque")
    return image


@lru_cache(maxsize=1)
def plaque_locator():
    image = background("Why the artery narrows", "Coronary arteries supply the heart muscle with oxygen-rich blood.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 743))
    point = heart(image, 178, 270, .99)
    label(pen, point, (761, 510), "Left anterior descending artery")
    return image


def p02(p):
    if p < .22:
        return blend_frames(plaque_locator(), plaque_scene(False), smooth((p - .13) / .09))
    show = smooth((p - .50) / .11) * (1 - smooth((p - .82) / .10))
    return blend_frames(plaque_scene(False), plaque_scene(True), show)


@lru_cache(maxsize=14)
def angio_scene(fill):
    image = background("From diagnosis to treatment", "Angiography shows where the artery narrows.").copy()
    pen = ImageDraw.Draw(image)
    card(pen, (76, 254, 1520, 763))
    film = shared.gray_vessels("left", fill, angle=-16, narrow=True, callout=fill > .96)
    film = film.resize((763, 460), Image.Resampling.LANCZOS)
    image.paste(film, (112, 275))
    pen.rounded_rectangle((111, 274, 876, 736), 7, outline="#537265", width=2)
    pill(pen, (933, 334), "Simulated angiogram")
    pen.text((933, 427), "Contrast outlines the artery", font=font(37, "heading"), fill=INK)
    pen.text((935, 484), "The channel narrows at one spot.", font=font(26), fill=MUTED)
    pen.text((935, 530), "The vessel beyond it remains visible.", font=font(26), fill=MUTED)
    return image


def option_icon(pen, cx, cy, option):
    if option == "medicines":
        pen.rounded_rectangle((cx - 30, cy - 30, cx + 30, cy + 34), 10, fill="#c5e2d3", outline="#568777", width=3)
        pen.rounded_rectangle((cx - 24, cy - 45, cx + 24, cy - 27), 5, fill="#6fa792", outline="#568777", width=2)
        pen.line((cx - 14, cy + 4, cx + 14, cy + 4), fill=GREEN, width=4)
        pen.line((cx, cy - 10, cx, cy + 18), fill=GREEN, width=4)
    else:
        path = [(cx - 56, cy + 29), (cx - 18, cy + 21), (cx + 11, cy + 6), (cx + 48, cy - 22)]
        pen.line(path, fill="#a95e63", width=20, joint="curve")
        pen.line(path, fill="#df9b89", width=9, joint="curve")
        if option == "angioplasty":
            pen.ellipse((cx - 33, cy - 9, cx + 32, cy + 30), outline="#337f6e", fill="#a7d8c9", width=3)
            pen.line((cx - 63, cy + 24, cx - 30, cy + 12, cx + 44, cy + 11), fill="#4e917e", width=3)
        else:
            pen.arc((cx - 51, cy - 40, cx + 51, cy + 36), 179, 349, fill="#3b8977", width=12)


@lru_cache(maxsize=1)
def options_scene():
    image = background("From diagnosis to treatment", "The care team uses the angiogram and clinical assessment to choose the next step.").copy()
    pen = ImageDraw.Draw(image)
    pen.text((87, 268), "Possible next steps", font=font(36, "semibold"), fill=GREEN)
    for i, name in enumerate(("Medicines", "Angioplasty", "Bypass surgery")):
        x = 85 + 491 * i
        card(pen, (x, 358, x + 447, 666))
        cx = x + 224
        pen.ellipse((cx - 82, 400, cx + 82, 564), fill=MINT)
        option_icon(pen, cx, 483, name.lower().split()[0])
        pen.text((cx, 612), name, font=font(38, "heading"), fill=INK, anchor="mm")
    pen.text((86, 723), "When appropriate, angioplasty can happen in the same session or be planned separately.", font=font(24), fill=MUTED)
    return image


def p03(p):
    fill = round(11 * (.16 + .84 * smooth((p - .02) / .32))) / 11
    return blend_frames(angio_scene(fill), options_scene(), smooth((p - .58) / .10))


def encode(scene, seconds, draw_frame):
    output = OUT / f"{scene}.mp4"
    cmd = [str(proto.FFMPEG), "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-movflags", "+faststart", str(output)]
    frames = seconds * FPS
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as worker:
        last_image, pixels = None, None
        for i in range(frames):
            image = draw_frame(i / (frames - 1))
            if image is not last_image:
                pixels = image.tobytes()
                last_image = image
            worker.stdin.write(pixels)
        worker.stdin.close()
        if worker.wait():
            raise RuntimeError(f"Could not encode {output.name}")
    report = subprocess.run([str(proto.FFMPEG), "-hide_banner", "-xerror", "-i", str(output), "-f", "null", "-"],
                            check=True, capture_output=True, text=True).stderr
    assert "1920x1080" in report and "Video: h264" in report and "Audio:" not in report, report
    print(f"{output.name} {seconds}s, fully decoded", flush=True)


if __name__ == "__main__":
    clips = {"P01": (15, p01), "P02": (18, p02), "P03": (24, p03)}
    for scene in sys.argv[1:] or clips:
        encode(scene, *clips[scene])
