"""Render a reusable right-wrist cutaway of three catheterization devices."""

from functools import lru_cache
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps


HERE = Path(__file__).resolve().parent
SERIES = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(SERIES / "episode-01" / "revision" / "wrist-proof"))
import render_wrist_proof as wrist


W, H, FPS, DURATION = 1600, 900, 24, 20
font = wrist.font
INK, GREEN, MUTED = wrist.INK, wrist.GREEN, wrist.MUTED
SOURCE = (96, 312, 1538, 735)
PICTURE = (96, 287, 1504, 700)
SHEATH_NOSE = wrist.ASSEMBLY_NOSE
WIRE_END = wrist.PATH.distance[-1]-95
CATHETER_END = WIRE_END-182
COLORS = ("#50a091", "#d5a266", "#7ebbb0")


def stroke(draw, points, color, width=1):
    draw.line(points, fill=color, width=width, joint="curve")


def project(xy):
    x, y = xy
    left, top, right, bottom = SOURCE
    px, py, qx, qy = PICTURE
    return px+(x-left)*(qx-px)/(right-left), py+(y-top)*(qy-py)/(bottom-top)


def ease(t, start, end):
    return wrist.smooth((t-start)/(end-start))


@lru_cache(maxsize=1)
def base():
    image = wrist.vertical_gradient((246, 251, 245), (219, 234, 225))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 57, 126, 107), 8, fill="white")
    logo = ImageOps.fit(Image.open(wrist.LOGO).convert("RGB"), (48, 48), method=Image.Resampling.LANCZOS)
    image.paste(logo, (77, 58))
    draw.text((144, 62), "Elysian Biomedical LLP", fill=GREEN, font=font(24, "semibold"))
    draw.text((144, 93), "Cardiology Education Series", fill=MUTED, font=font(18))
    draw.text((1521, 66), "CARDIAC CATHETERIZATION", fill=GREEN, font=font(20, "semibold"), anchor="rt")
    stroke(draw, ((76, 128), (1522, 128)), "#b3ccbf", 2)
    draw.text((76, 150), "Sheath, guidewire and catheter", font=font(59, "heading"), fill=INK)
    draw.text((77, 226), "Right wrist and radial artery", font=font(26, "semibold"), fill=GREEN)
    draw.rounded_rectangle((76, 268, 1522, 714), 22, fill="#f0f7ef", outline="#bad3c3", width=2)
    palm = wrist.background().crop((1249, 158, 1519, 313))
    image.paste(palm.resize((185, 106), Image.Resampling.LANCZOS), (1325, 144))
    return image


def catheter(draw, end):
    start = end-1620
    wrist.tube(draw, start, end, 11.4, (27, 79, 75, 255), taper=12)
    wrist.tube(draw, start, end, 8.9, (132, 197, 183, 246), taper=9)
    wrist.tube(draw, start, end-2, 2.3, (221, 244, 223, 246), shift=-4.4)
    tip_x, tip_y = wrist.PATH.at(end)
    draw.ellipse((tip_x-2, tip_y-2, tip_x+2, tip_y+2), fill=(30, 85, 75, 255))


def leader(draw, label, at, target):
    x, y = at
    face = font(29, "semibold")
    tx, ty = target
    width = draw.textlength(label, font=face)
    if x+width+10 < tx:
        start, elbow = (x+width+11, y+18), (x+width+40, y+18)
    else:
        start, elbow = (x-10, y+18), (x-40, y+18)
    stroke(draw, (start, elbow, target), "#527767", 2)
    draw.ellipse((tx-4, ty-4, tx+4, ty+4), fill="#f6efd5", outline="#527767", width=2)
    draw.text(at, label, font=face, fill=GREEN)


def role_cards(draw, t):
    items = (
        ("Sheath", "Stays at the wrist entry", 0),
        ("Guidewire", "Leads ahead inside the artery", 2.3),
        ("Catheter", "Slides over the guidewire", 9.1),
    )
    for i, (title, detail, since) in enumerate(items):
        x = 76+i*486
        active = t >= since
        draw.rounded_rectangle((x, 738, x+469, 865), 17,
                               fill="#f5faf3" if active else "#e7f0e7",
                               outline="#b5ccbe", width=2)
        draw.rounded_rectangle((x+19, 758, x+26, 844), 3,
                               fill=COLORS[i] if active else "#a5bbae")
        draw.text((x+44, 756), title, font=font(36, "semibold"), fill=GREEN if active else MUTED)
        draw.text((x+44, 814), detail, font=font(27), fill=MUTED)


def frame(t):
    skin = wrist.background()
    tools = Image.new("RGBA", (W, H))
    wrist.assembly(tools, SHEATH_NOSE, inner=False)
    pen = ImageDraw.Draw(tools)
    wire_tip = -95+(WIRE_END+95)*ease(t, 2.1, 7.65)
    catheter_tip = -110+(CATHETER_END+110)*ease(t, 9.1, 15.25)
    if t > 9.1:
        catheter(pen, catheter_tip)
    if t > 2.1:
        wrist.wire(pen, wire_tip-1680, wire_tip)
    skin = Image.alpha_composite(skin.convert("RGBA"), tools).convert("RGB")
    picture = skin.crop(SOURCE).resize((PICTURE[2]-PICTURE[0], PICTURE[3]-PICTURE[1]),
                                      Image.Resampling.LANCZOS)
    image = base().copy()
    image.paste(picture, PICTURE[:2])
    draw = ImageDraw.Draw(image)
    leader(draw, "Sheath", (162, 304), project(wrist.PATH.uv(SHEATH_NOSE-211, -16)))
    if wire_tip >= SHEATH_NOSE+80:
        leader(draw, "Guidewire tip", (1246, 325), project(wrist.PATH.at(wire_tip-7)))
    if catheter_tip >= SHEATH_NOSE+44:
        leader(draw, "Catheter tip", (754, 383), project(wrist.PATH.uv(catheter_tip-12, -7)))
    # Extend the existing radial-artery leader into the new frame layout.
    stroke(draw, ((1229, 699), (1252, 716), (1290, 716)), "#656c5d", 2)
    draw.text((1298, 702), "Radial artery", font=font(23, "semibold"), fill=GREEN)
    role_cards(draw, t)
    return image


def render():
    ffmpeg = str(wrist.FFMPEG)
    target = HERE / "device-roles-overview.mp4"
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
        "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
        "-threads", "2", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(target),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    previous = -1
    try:
        with process.stdin as pipe:
            for index in range(FPS*DURATION):
                time = index/FPS
                if time <= 2.1:
                    time = 0
                elif 7.65 <= time <= 9.1:
                    time = 8
                elif time >= 15.25:
                    time = 15.3
                if time != previous:
                    raw = frame(time).tobytes()
                    previous = time
                pipe.write(raw)
    finally:
        if process.wait():
            raise RuntimeError("Could not encode the device overview")
    subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(target), "-map", "0:v:0",
                    "-f", "null", "-"], check=True)
    subprocess.run([ffmpeg, "-v", "error", "-y", "-ss", "17.25", "-i", str(target),
                    "-frames:v", "1", str(HERE/"device-roles-overview.png")], check=True)
    print("Device overview · 20.00s · 1920x1080 · 24 fps · silent · full decode passed", flush=True)


if __name__ == "__main__":
    render()
