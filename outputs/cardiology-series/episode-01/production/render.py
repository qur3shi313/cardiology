"""Render the two original diagnostic coronary angiography drafts and carousels."""

import argparse
import json
import math
from pathlib import Path
import subprocess
import wave
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageOps

from access_art import draw_access
from vascular_art import draw_vascular


HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent
ROOT = HERE.parents[3]
FFMPEG = ROOT / "work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
FONTS = ROOT / "outputs/reels-2026-11-03/assets/fonts"
LOGO = ROOT / "work/company-logo-original-686.jpg"
SIZE = (1280, 720)
FPS = 16
BG = (11, 34, 38)
INK = (247, 249, 245)
MUTED = (168, 203, 194)
MINT = (154, 218, 186)
AMBER = (250, 204, 136)
PANEL = (17, 55, 54)
ACCESS = {
    "site", "needle", "short_wire", "needle_out", "sheath_in", "short_out",
    "exchange_wire", "micro_out", "working_sheath", "working_dilator_out",
    "long_wire", "catheter", "catheter_out", "remove", "closure",
}
CORONARY_TRANSFER = {"radial_transfer", "femoral_left_out", "femoral_right_in"}
MOVING = (ACCESS - {"site"}) | {"route", "root", "left_contrast", "right_contrast"} | CORONARY_TRANSFER
VASCULAR = {"heart", "route", "root", "left_contrast", "right_contrast", "stenosis", "aftercare"} | CORONARY_TRANSFER
ART_BOX = (405, 130, 1220, 603)
MOTION_SECONDS = 3.5


@lru_cache
def font(size, role="body"):
    name = {
        "body": "fira-sans-regular.ttf",
        "bold": "fira-sans-semibold.ttf",
        "title": "josefin-sans-variable.ttf",
    }[role]
    face = ImageFont.truetype(str(FONTS / name), size)
    if role == "title":
        face.set_variation_by_axes([650])
    return face


def lines(draw, text, face, limit):
    words = text.split()
    wrapped = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=face) > limit:
            wrapped.append(current)
            current = word
        else:
            current = candidate
    if current:
        wrapped.append(current)
    return "\n".join(wrapped)


@lru_cache
def backdrop(width, height):
    image = Image.new("RGB", (width, height), BG)
    pen = ImageDraw.Draw(image)
    for row in range(height):
        t = row / max(1, height - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip((12, 40, 42), (8, 27, 35)))
        pen.line((0, row, width, row), fill=color)
    return image


@lru_cache
def logo(size):
    return ImageOps.fit(Image.open(LOGO).convert("RGB"), (size, size), method=Image.Resampling.LANCZOS)


def masthead(image, route, x, y, *, portrait=False):
    draw = ImageDraw.Draw(image)
    size = 68 if portrait else 54
    mark = Image.new("L", (size, size))
    ImageDraw.Draw(mark).rounded_rectangle((0, 0, size - 1, size - 1), 12, fill=255)
    image.paste(logo(size), (x, y), mark)
    name = "Elysian Biomedical LLP"
    draw.text((x + size + 17, y + 3), name, fill=INK, font=font(28 if portrait else 24, "bold"))
    draw.text(
        (x + size + 17, y + (37 if portrait else 30)), "Cardiology Education Series",
        fill=MINT, font=font(22 if portrait else 18),
    )
    if not portrait:
        route_name = "RIGHT WRIST  /  RADIAL" if route == "radial" else "RIGHT GROIN  /  FEMORAL"
        draw.text((1220, y + 14), route_name, fill=MINT, font=font(18, "bold"), anchor="rt")


def artwork(image, box, route, stage, progress):
    if stage in ACCESS:
        draw_access(image, box, route, stage, progress)
    elif stage in VASCULAR:
        draw_vascular(image, box, route, stage, progress)
    else:
        information_panel(image, box, route, stage)


def information_panel(image, box, route, stage):
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, 26, fill=PANEL, outline=(60, 113, 107), width=2)
    if stage == "result":
        entries = [
            ("01", "Medicines", "Manage symptoms and cardiovascular risk."),
            ("02", "More tests", "Clarify what a narrowing means."),
            ("03", "Angioplasty", "Treat a narrowing when appropriate."),
            ("04", "Bypass review", "Consider surgery for selected findings."),
        ]
    elif stage == "home":
        entries = [
            ("01", "Follow your discharge plan", "Dressing, activity, medicines and follow-up."),
            ("02", "Watch the access site", "A small bruise or mild soreness can occur."),
            ("03", "Contact your care team", "Increasing redness, pain, drainage or fever."),
        ]
    elif stage == "urgent":
        limb = "Hand" if route == "radial" else "Foot"
        entries = [
            ("01", "Heavy or persistent bleeding", "Or swelling that grows quickly."),
            ("02", f"{limb} suddenly cold or numb", "On the side used for access."),
            ("03", "New chest pressure or sudden breathlessness", "Call local emergency services."),
        ]
    else:
        entries = [
            ("01", "American Heart Association", "Coronary angiogram and acute coronary syndromes"),
            ("02", "SCAI", "Radial and femoral arterial access"),
            ("03", "Guy’s and St Thomas’ NHS", "Coronary angiography and recovery"),
        ]
    y = y0 + 39
    spacing = (y1 - y0 - 55) / len(entries)
    for numeral, heading, description in entries:
        draw.ellipse((x0 + 34, y + 5, x0 + 76, y + 47), outline=MINT, width=2)
        draw.text((x0 + 55, y + 25), numeral, fill=MINT, font=font(16, "bold"), anchor="mm")
        draw.text((x0 + 95, y), heading, fill=INK, font=font(26, "bold"))
        draw.text((x0 + 95, y + 34), description, fill=MUTED, font=font(21))
        y += spacing


def video_frame(route, scene, index, count, progress):
    canvas = backdrop(*SIZE).copy()
    draw = ImageDraw.Draw(canvas)
    masthead(canvas, route, 60, 35)
    draw.line((60, 106, 1220, 106), fill=(53, 94, 89), width=2)
    draw.text((60, 151), f"{index + 1:02} / {count:02}", fill=MINT, font=font(19, "bold"))
    heading = lines(draw, scene["title"], font(50, "title"), 322)
    draw.multiline_text((60, 190), heading, font=font(50, "title"), fill=INK, spacing=2)
    heading_box = draw.multiline_textbbox((60, 190), heading, font=font(50, "title"), spacing=2)
    detail = lines(draw, scene["detail"], font(25), 300)
    draw.multiline_text((60, heading_box[3] + 27), detail, fill=MUTED, font=font(25), spacing=6)
    artwork(canvas, ART_BOX, route, scene["stage"], progress)
    draw.line((60, 633, 1220, 633), fill=(53, 94, 89), width=2)
    draw.text((60, 654), "Coronary angiography", fill=MINT, font=font(19, "bold"))
    draw.text((1220, 654), "Illustrated educational walkthrough", fill=MUTED, font=font(18), anchor="rt")
    return canvas


def pcm_data(path):
    with wave.open(str(path), "rb") as source:
        spec = source.getparams()[:3]
        return spec, source.readframes(source.getnframes())


def silence(spec, seconds):
    channels, width, sample_rate = spec
    return bytes(round(sample_rate * seconds) * channels * width)


def subtitle_time(seconds):
    millis = round(seconds * 1000)
    whole, ms = divmod(millis, 1000)
    hours, rest = divmod(whole, 3600)
    minutes, sec = divmod(rest, 60)
    return f"{hours:02}:{minutes:02}:{sec:02},{ms:03}"


def subtitle_chunks(text, max_words=11):
    import re
    chunks = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        words = sentence.split()
        while len(words) > max_words:
            cutoff = max_words
            if len(words) - cutoff < 4:
                cutoff = math.ceil(len(words) / 2)
            chunks.append(" ".join(words[:cutoff]))
            words = words[cutoff:]
        if words:
            chunks.append(" ".join(words))
    return chunks


def mux_video(route, scenes):
    import os
    import tempfile
    name = f"elysian-coronary-angiography-{route}"
    spec, _ = pcm_data(HERE / "audio" / f"{route}-00.wav")
    sample_bytes_per_second = spec[0] * spec[1] * spec[2]
    chapters, subtitles = [], []
    offset = 0.0
    with tempfile.TemporaryDirectory(prefix=f"render-{route}-", dir=HERE) as temp:
        temp_path = Path(temp)
        narration = temp_path / "voice.wav"
        video = temp_path / "visual.mp4"
        log = temp_path / "ffmpeg.log"
        with wave.open(str(narration), "wb") as sound, log.open("wb") as diagnostics:
            sound.setnchannels(spec[0])
            sound.setsampwidth(spec[1])
            sound.setframerate(spec[2])
            cmd = [
                str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "1280x720",
                "-framerate", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-threads", "3",
                "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", str(video),
            ]
            with subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=diagnostics) as encoder:
                for index, scene in enumerate(scenes):
                    speech = scene["voice"]
                    lead = 0.48 if speech else 0
                    pcm = b""
                    if speech:
                        clip_spec, pcm = pcm_data(HERE / "audio" / f"{route}-{index:02}.wav")
                        if clip_spec != spec:
                            raise ValueError(f"Unexpected audio format for {route} scene {index}")
                    voice_duration = len(pcm) / sample_bytes_per_second
                    duration = math.ceil((lead + voice_duration + scene["hold"]) * FPS) / FPS
                    sound.writeframesraw(silence(spec, lead) + pcm + silence(spec, duration - lead - voice_duration))
                    chapters.append({"time": round(offset, 3), "duration": duration, **scene})
                    if speech:
                        chunks = subtitle_chunks(speech)
                        weights = [len(part.split()) for part in chunks]
                        current = offset + lead
                        for weight, part in zip(weights, chunks):
                            end = current + voice_duration * weight / sum(weights)
                            subtitles.append(f"{len(subtitles) + 1}\n{subtitle_time(current)} --> {subtitle_time(end)}\n{part}")
                            current = end
                    moving = scene["stage"] in MOVING
                    motion = min(MOTION_SECONDS, duration - 0.25)
                    final = video_frame(route, scene, index, len(scenes), 1).tobytes()
                    motion_frames = max(1, round(motion * FPS))
                    for frame in range(round(duration * FPS)):
                        if moving and frame < motion_frames:
                            progress = frame / max(1, motion_frames - 1)
                            pixels = video_frame(route, scene, index, len(scenes), progress).tobytes()
                        else:
                            pixels = final
                        encoder.stdin.write(pixels)
                    offset += duration
                    print(f"{route} {index + 1:02}/{len(scenes):02} {scene['title']}", flush=True)
                encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError(f"Video encode failed: {log.read_text(errors='replace')}")
        srt = EPISODE / f"{name}.en.srt"
        srt.write_text("\n\n".join(subtitles) + "\n", encoding="utf-8")
        final = EPISODE / f"{name}.mp4"
        delivery = temp_path / "delivery.mp4"
        subprocess.run([
            str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video), "-i", str(narration), "-i", str(srt),
            "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text",
            "-metadata:s:s:0", "language=eng", "-metadata", f"title=Coronary angiography through the {'wrist' if route == 'radial' else 'groin'}",
            "-movflags", "+faststart", str(delivery),
        ], check=True)
        os.replace(delivery, final)
        (EPISODE / f"{route}-timing.json").write_text(
            json.dumps({"route": route, "duration_seconds": offset, "chapters": chapters}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Complete: {final.name} ({offset:.2f} seconds)", flush=True)


def make_carousel(route):
    radial = route == "radial"
    slides = [
        ("Coronary\nangiography", "Through the right wrist" if radial else "Through the right groin", "route"),
        (
            "The short sheath\nstays at the wrist" if radial else "How the team places\nthe groin sheath",
            "A short access wire guides the sheath and dilator." if radial else "A temporary introducer lets the team exchange wires before the working sheath goes in.",
            "sheath_in" if radial else "working_sheath",
        ),
        ("Contrast outlines\nthe coronary arteries", "The team takes separate X-ray views of the left and right arteries.", "left_contrast"),
        (
            "Wrist recovery" if radial else "Groin recovery",
            "Staff monitor the puncture while a wrist compression band controls bleeding." if radial else "Staff monitor the puncture after pressure or closure and tell you when it is safe to get up.",
            "closure",
        ),
    ]
    directory = EPISODE / "post-art" / route
    directory.mkdir(parents=True, exist_ok=True)
    for index, (heading, deck, stage) in enumerate(slides, start=1):
        frame = backdrop(1080, 1350).copy()
        draw = ImageDraw.Draw(frame)
        masthead(frame, route, 70, 66, portrait=True)
        draw.line((70, 161, 1010, 161), fill=(57, 112, 103), width=2)
        draw.multiline_text((70, 212), heading, fill=INK, font=font(86, "title"), spacing=0)
        draw.multiline_text((70, 434), lines(draw, deck, font(35), 930), fill=MINT, font=font(35), spacing=7)
        artwork(frame, (70, 558, 1010, 1110), route, stage, 1)
        draw.line((70, 1175, 1010, 1175), fill=(57, 112, 103), width=2)
        draw.text((70, 1208), "Diagnostic coronary angiography", fill=INK, font=font(28, "bold"))
        draw.text((70, 1250), "Original schematic illustration", fill=MUTED, font=font(25))
        frame.save(directory / f"slide-{index:02}.png", optimize=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("route", choices=["radial", "femoral"])
    parser.add_argument("--images-only", action="store_true")
    args = parser.parse_args()
    scenes = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))[args.route]
    make_carousel(args.route)
    if not args.images_only:
        mux_video(args.route, scenes)


if __name__ == "__main__":
    main()

