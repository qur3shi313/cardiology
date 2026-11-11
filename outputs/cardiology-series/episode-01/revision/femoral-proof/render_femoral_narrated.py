"""Time the validated silent femoral proof to the approved Alexander narration."""
from __future__ import annotations

import json
from math import ceil
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
from render_femoral_proof import FPS, STAGES, STOPS, VIDEO, font, scenes, wrist_art


OUT = Path(__file__).resolve().parent
VOICE = OUT.parent / "femoral-alexander-part-1.mp3"
TIMING = OUT.parent / "femoral-alexander-scene-timing.json"
TARGET = OUT / "femoral-access-alexander-review.mp4"
PREVIEW = OUT / "femoral-access-alexander-decoded-check.jpg"
FFMPEG = str(wrist_art.FFMPEG)


def alignment():
    report = json.loads(TIMING.read_text(encoding="utf-8-sig"))
    index = {row["scene"]: row for row in report["timing"]}
    beats = [index[scenes[stage]["title"]] for stage in STAGES]
    assert all(beat["part"] == 1 for beat in beats)
    assert all(beat["script_tokens"] == beat["matched_tokens"] for beat in beats)
    start = beats[0]["narration_start_sec"]
    end = beats[-1]["narration_end_sec"]
    return start, end, [beat["narration_start_sec"] - start for beat in beats] + [end - start]


def render(start, end, marks):
    source_marks = [ceil(t * FPS) for t in STOPS]
    target_marks = [round(t * FPS) for t in marks]
    filters = []
    for i, (a, b) in enumerate(zip(source_marks, source_marks[1:])):
        count = target_marks[i + 1] - target_marks[i]
        stretch = count / (b - a)
        filters.append(f"[0:v]trim=start_frame={a}:end_frame={b},settb=AVTB,"
                       f"setpts=(PTS-STARTPTS)*{stretch:.12f},fps={FPS},tpad=stop_mode=clone:stop_duration=1,"
                       f"trim=end_frame={count},setpts=PTS-STARTPTS[v{i}]")
    filters.append("".join(f"[v{i}]" for i in range(len(STAGES))) + f"concat=n={len(STAGES)}:v=1:a=0[v]")
    filters.append(f"[1:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS[a]")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(VIDEO), "-i", str(VOICE),
                    "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-preset", "fast", "-crf", "17", "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", str(TARGET)], check=True)
    return target_marks


def validate_and_sheet(marks):
    probe = subprocess.run([FFMPEG, "-hide_banner", "-xerror", "-i", str(TARGET), "-f", "null", "-"],
                           check=True, text=True, capture_output=True).stderr
    duration_match = re.search(r"Duration: 00:00:([\d.]+)", probe)
    assert duration_match and abs(float(duration_match.group(1)) - marks[-1]) <= .045, probe
    assert "Video: h264" in probe and "1920x1080" in probe and "Audio: aac" in probe, probe

    timecodes = [mark - .26 for mark in marks[1:]]
    frames = [round(t * FPS) for t in timecodes]
    select = "+".join(f"eq(n\\,{frame})" for frame in frames)
    width, height = 520, 292
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(TARGET), "-vf", f"select={select},scale={width}:{height}",
                          "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    step = width * height * 3
    assert len(raw) == step * len(timecodes), (len(raw), step * len(timecodes))
    sheet = Image.new("RGB", (1600, 637), (224, 236, 228))
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        x, y = 10 + (i % 3) * 530, 12 + (i // 3) * 310
        panel = Image.frombytes("RGB", (width, height), raw[i * step:(i + 1) * step])
        sheet.paste(panel, (x, y))
        draw.text((x + 8, y + 294), f"{frame / FPS:05.2f}s", font=font(14), fill=wrist_art.MUTED)
    sheet.save(PREVIEW, quality=94)
    print(f"{TARGET.name}: {float(duration_match.group(1)):.2f}s, H.264 1920x1080 / AAC; {len(timecodes)} frames decoded")


if __name__ == "__main__":
    start, end, marks = alignment()
    target_marks = render(start, end, marks)
    validate_and_sheet(marks)
    print("Visual boundaries (seconds): " + ", ".join(f"{mark / FPS:.3f}" for mark in target_marks))
