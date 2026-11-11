"""Create silent, narration-length femoral angiography scene groups and decoded contact sheets."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


OUT = Path(__file__).resolve().parent
REVISION = OUT.parent
EPISODE = REVISION.parent
sys.dont_write_bytecode = True


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proof = load_module("femoral_proof", REVISION / "femoral-proof/render_femoral_proof.py")
anatomy = load_module("vascular_reference", EPISODE / "production/vascular_art.py")
scene_index = proof.scenes
timing = json.loads((REVISION / "femoral-alexander-scene-timing.json").read_text(encoding="utf-8-sig"))
timing_index = {row["scene"]: row for row in timing["timing"]}
W, H = proof.W, proof.H
FPS = 24
FFMPEG = str(proof.wrist_art.FFMPEG)
INK, GREEN, MUTED = proof.INK, proof.GREEN, proof.MUTED
font, gradient, overlay = proof.font, proof.gradient, proof.overlay
curve, smooth, tube, wire = proof.curve, proof.smooth, proof.tube, proof.wire
PATH, ENTRY, WORKING = proof.PATH, proof.ENTRY, proof.WORKING
LONG_TIP = PATH.distance[-1] - 20
CATH_TIP = LONG_TIP - 116


@lru_cache(maxsize=1)
def chrome():
    image = gradient((244, 250, 245), (220, 233, 226))
    overlay(image, (255, 255, 251), [(0, 0), (1200, 0), (1030, 697), (0, 663)], 112, 105)
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((76, 57, 126, 107), 9, fill=(255, 255, 255))
    brand = ImageOps.fit(Image.open(proof.wrist_art.LOGO).convert("RGB"), (46, 46), method=Image.Resampling.LANCZOS)
    image.paste(brand, (78, 59))
    pen.text((144, 62), "Elysian Biomedical LLP", font=font(24, "semibold"), fill=GREEN)
    pen.text((144, 93), "Cardiology Education Series", font=font(18), fill=MUTED)
    pen.text((1518, 65), "RIGHT GROIN", font=font(21, "semibold"), fill=GREEN, anchor="rt")
    pen.text((1518, 94), "Anatomical illustration", font=font(17), fill=MUTED, anchor="rt")
    pen.line((77, 128, 1522, 128), fill=(179, 204, 191), width=1)
    return image


@lru_cache(maxsize=1)
def cutaway():
    image = proof.background().copy()
    title = (65, 143, 1226, 211)
    image.paste(chrome().crop(title), title[:2])
    return image


def composite_tools(base, layer):
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), proof.tool_alpha()))
    return Image.alpha_composite(base, layer).convert("RGB")


def draw_catheter(pen, start, end):
    tube(pen, start, end, 9.3, (39, 70, 69, 254), taper=12)
    tube(pen, start, end, 7.1, (194, 220, 215, 242), taper=9)
    tube(pen, start, end - 2, 1.35, (251, 253, 239, 245), shift=-3.1)
    tube(pen, end - 12, end, 5.1, (106, 165, 150, 254), taper=8)


def titles(image, stage, detail=None):
    pen = ImageDraw.Draw(image)
    scene = scene_index[stage]
    pen.text((76, 151), scene["title"], font=font(57, "heading"), fill=INK)
    pen.text((76, 823), detail or scene["detail"], font=font(23), fill=MUTED)
    pen.line((77, 864, 1522, 864), fill=(179, 204, 191), width=1)
    return pen


def tool_frame(stage, progress):
    layer = Image.new("RGBA", (W, H))
    pen = ImageDraw.Draw(layer)
    proof.introducer(pen, WORKING, working=True)
    if stage == "long_wire":
        end = -66 + (LONG_TIP + 66) * progress
        wire(pen, -63, end, hook=True)
    else:
        end = -79 + (CATH_TIP + 79) * progress
        draw_catheter(pen, end - 1900, end)
        wire(pen, -63, LONG_TIP, hook=True)
    image = composite_tools(cutaway(), layer)
    pen = titles(image, stage)
    if stage == "long_wire" and progress > .63:
        proof.locator(pen, 1036, 405, "Long diagnostic guidewire", PATH.at(end - 9))
    if stage == "catheter" and progress > .53:
        proof.locator(pen, 950, 400, "Diagnostic catheter", PATH.at(end - 18))
        proof.locator(pen, 815, 346, "Working sheath stays", PATH.at(WORKING - 44))
    return image


def map_point(point):
    x, y = point
    return 187 + x * 1.24, 195 + y * 1.05


def map_path(path):
    return [map_point(point) for point in path]


ACTIVE = map_path(anatomy.FEMORAL)
BODY = map_path(anatomy.BODY)
HEART = map_path(anatomy.curve((289, 199), ((263, 162), (225, 195), (237, 225)),
                               ((248, 257), (289, 283), (328, 294)),
                               ((359, 269), (376, 217), (338, 193)),
                               ((321, 182), (306, 186), (289, 199))))
VASCULAR_LABELS = (
    ((223, 477), "Right common femoral artery", 742),
    ((244, 407), "Right external iliac artery", 661),
    ((273, 383), "Right common iliac artery", 603),
    ((314, 335), "Abdominal aorta", 539),
    ((322, 241), "Descending thoracic aorta", 467),
    ((310, 145), "Aortic arch", 318),
    ((286, 199), "Aortic root", 392),
)


@lru_cache(maxsize=1)
def map_background():
    image = chrome().copy()
    overlay(image, (65, 88, 71), [(x + 10, y + 12) for x, y in BODY], 42, 18)
    image.paste(gradient((247, 224, 207), (214, 167, 153)), (0, 0), proof.mask(BODY))
    pen = ImageDraw.Draw(image)
    pen.line(BODY, fill=(183, 144, 131), width=2, joint="curve")
    for side in (-1, 1):
        clavicle = anatomy.curve((293, 130), ((293 + side * 37, 109), (293 + side * 71, 106), (293 + side * 115, 118)))
        pen.line(map_path(clavicle), fill=(217, 167, 148), width=3, joint="curve")
        for rib in range(7):
            y = 156 + 18 * rib
            rib_path = anatomy.curve((294, y + 20), ((294 + side * 26, y + 10),
                                    (294 + side * 67, y - 16), (294 + side * 97, y + 6)))
            pen.line(map_path(rib_path), fill=(228, 181, 165), width=2, joint="curve")
    pen.polygon(HEART, fill=(189, 104, 105))
    pen.line(HEART, fill=(163, 89, 97), width=2, joint="curve")
    for path, width in ((anatomy.BODY_OTHER_ILIAC, 17), (anatomy.BODY_LEFT_SUBCLAVIAN, 11),
                        (anatomy.BODY_CAROTIDS[0], 9), (anatomy.BODY_CAROTIDS[1], 9)):
        pen.line(map_path(path), fill=(172, 93, 99), width=width + 3, joint="curve")
        pen.line(map_path(path), fill=(198, 117, 112), width=width, joint="curve")
    for a, b, c in ((0, 32, 15), (31, 55, 20), (54, len(ACTIVE), 28)):
        section = ACTIVE[a:b]
        pen.line(section, fill=(132, 62, 70), width=c + 6, joint="curve")
        pen.line(section, fill=(192, 91, 95), width=c, joint="curve")
        pen.line([(x - 3, y) for x, y in section], fill=(223, 133, 122), width=2, joint="curve")
    for point, label, y in VASCULAR_LABELS:
        x, py = map_point(point)
        pen.line(((x, py), (850, y), (916, y)), fill=(121, 151, 132), width=2, joint="curve")
        pen.ellipse((x - 5, py - 5, x + 5, py + 5), fill=(237, 239, 216), outline=(76, 111, 93), width=2)
        pen.text((935, y), label, font=font(24, "semibold"), fill=GREEN, anchor="lm")
    x, y = ACTIVE[0]
    pen.ellipse((x - 15, y - 15, x + 15, y + 15), outline=(43, 121, 92), width=4)
    pen.text((174, 764), "Patient’s right", font=font(19, "semibold"), fill=GREEN)
    pen.line((1165, 800, 1204, 800), fill=(43, 94, 80), width=8)
    pen.line((1165, 800, 1204, 800), fill=(193, 225, 206), width=5)
    pen.text((1216, 800), "Catheter", font=font(18), fill=INK, anchor="lm")
    pen.line((1322, 800, 1361, 800), fill=(108, 77, 42), width=6)
    pen.line((1322, 800, 1361, 800), fill=(241, 208, 132), width=3)
    pen.text((1373, 800), "Guidewire", font=font(18), fill=INK, anchor="lm")
    return image


def travel_frame(progress):
    image = map_background().copy()
    pen = titles(image, "route")
    wire_fraction = .115 + .885 * progress
    catheter_fraction = .053 + .905 * progress
    wire_path = anatomy.trace(ACTIVE, wire_fraction)
    catheter_path = anatomy.trace(ACTIVE, catheter_fraction)
    pen.line(catheter_path, fill=(33, 77, 69), width=10, joint="curve")
    pen.line(catheter_path, fill=(177, 218, 197), width=7, joint="curve")
    pen.line(wire_path, fill=(104, 69, 43), width=5, joint="curve")
    pen.line(wire_path, fill=(253, 222, 151), width=3, joint="curve")
    x, y = wire_path[-1]
    pen.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(250, 226, 155), outline=(110, 76, 41), width=1)
    return image


def long_route_frame(stage, progress):
    return travel_frame(progress) if stage == "route" else tool_frame(stage, progress)


def alignment(stages):
    beats = [timing_index[scene_index[stage]["title"]] for stage in stages]
    start, end = beats[0]["narration_start_sec"], beats[-1]["narration_end_sec"]
    assert all(row["script_tokens"] == row["matched_tokens"] for row in beats)
    markers = [row["narration_start_sec"] - start for row in beats] + [end - start]
    return start, end, [round(marker * FPS) for marker in markers]


def render_group(stem, stages, drawer, sample_points=None):
    video = OUT / f"{stem}.mp4"
    stills = OUT / f"{stem}-decoded.jpg"
    start, end, markers = alignment(stages)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-movflags", "+faststart", str(video)]
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as runner:
        for stage, a, b in zip(stages, markers, markers[1:]):
            latest_step, pixels = None, None
            for number in range(a, b):
                position = (number - a) / (b - a)
                motion = round(smooth((position - .015) / .86) * 250) / 250
                if motion != latest_step:
                    latest_step, pixels = motion, drawer(stage, motion).tobytes()
                runner.stdin.write(pixels)
        runner.stdin.close()
        if runner.wait():
            raise RuntimeError(f"Could not encode {video.name}")
    checks = sample_points or [(i, fraction) for i in range(len(stages)) for fraction in (.52, .92)]
    validate(video, stills, markers, checks)
    print(f"{video.name} {markers[-1] / FPS:.3f}s; Alexander alignment {start:.3f}–{end:.3f}s", flush=True)


def validate(video, stills, markers, checks):
    report = subprocess.run([FFMPEG, "-hide_banner", "-xerror", "-i", str(video), "-f", "null", "-"],
                            check=True, capture_output=True, text=True).stderr
    assert "1920x1080" in report and "Audio:" not in report and "Video: h264" in report, report
    counts = [markers[i] + round((markers[i + 1] - markers[i]) * p) for i, p in checks]
    select = "+".join(f"eq(n\\,{i})" for i in counts)
    width, height = 520, 292
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(video), "-vf", f"select={select},scale={width}:{height}",
                          "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    frame_size = width * height * 3
    assert len(raw) == frame_size * len(checks), (len(raw), frame_size * len(checks))
    sheet = Image.new("RGB", (1600, 15 + 310 * ((len(checks) + 2) // 3)), (224, 236, 228))
    pen = ImageDraw.Draw(sheet)
    for i, number in enumerate(counts):
        x, y = 10 + (i % 3) * 530, 12 + (i // 3) * 310
        panel = Image.frombytes("RGB", (width, height), raw[i * frame_size:(i + 1) * frame_size])
        sheet.paste(panel, (x, y))
        pen.text((x + 8, y + 295), f"{number / FPS:05.2f}s", font=font(14), fill=MUTED)
    sheet.save(stills, quality=94)


if __name__ == "__main__":
    render_group("femoral-f14-f16-diagnostic-route", ("long_wire", "catheter", "route"), long_route_frame,
                 [(0, .52), (0, .92), (1, .52), (1, .92), (2, .33), (2, .92)])
