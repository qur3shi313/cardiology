"""Render isolated Episode 11 pressure anatomy corrections without changing the active map."""
import argparse
import json
import re
from pathlib import Path

from tools.elysian_video import pressure
from tools.elysian_video.__main__ import FPS, LEGACY_FFMPEG, ROOT, SERIES
from tools.elysian_video.encode import encode_scene
from tools.elysian_video.qa import file_hash, freeze_report, invoke, metadata


EPISODE = SERIES / 'episode-11'
VISUALS = EPISODE / 'visuals'
EVIDENCE = Path(__file__).with_name('episode-11-pressure-continuity-qc.json')


def verify(path, expected_frames):
    ffmpeg = str(LEGACY_FFMPEG)
    fmt = metadata(invoke(ffmpeg, '-i', path, check=False).stderr.decode('utf-8', 'replace'))
    decoded = invoke(ffmpeg, '-v', 'info', '-xerror', '-threads', 2, '-filter_threads', 2,
                     '-progress', 'pipe:1', '-i', path, '-map', '0:v:0', '-an',
                     '-vf', 'freezedetect=n=0.001:d=2', '-f', 'null', '-')
    frames = int(re.findall(rb'^frame=(\d+)\s*$', decoded.stdout, re.MULTILINE)[-1])
    assert (fmt['width'], fmt['height'], fmt['fps'], fmt['codec'], fmt['audio_present']) == (
        2560, 1440, 30., 'h264', False)
    assert frames == expected_frames
    freeze = freeze_report(decoded.stderr.decode('utf-8', 'replace'), frames / FPS)
    if freeze['longest_seconds'] > 6 or freeze['percent'] > 15:
        raise ValueError(f'{path.name} exceeds source hold tolerance: {freeze}')
    return {'file': path.relative_to(ROOT).as_posix(), 'sha256': file_hash(path),
            'frames': frames, 'format': fmt, 'full_decode': True, 'motion': freeze}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenes', nargs='*', choices=('P03', 'P04', 'P05', 'P06', 'P08', 'P09'))
    parser.add_argument('--report', type=Path, default=EVIDENCE)
    args = parser.parse_args()
    selected = args.scenes or ('P03', 'P04', 'P05')
    timeline = json.loads((EPISODE / 'timeline.json').read_text(encoding='utf-8-sig'))
    report = json.loads(args.report.read_text(encoding='utf-8')) if args.report.is_file() else {}
    for scene in timeline['scenes']:
        ident = scene['id']
        if ident not in selected:
            continue
        frames = scene['end_frame'] - scene['start_frame']
        output = VISUALS / f'{ident}-pressure-continuity.mp4'
        staging = output.with_suffix('.part.mp4')
        print(f'{ident}: encoding {frames} frames', flush=True)

        def draw(canvas, index):
            pressure.draw(canvas, ident, index / (frames - 1), index / FPS)
            if index and index % 180 == 0:
                print(f'{ident}: {index}/{frames}', flush=True)

        encode_scene(staging, frames, draw, preset='veryfast', threads=2)
        report[ident] = verify(staging, frames)
        staging.replace(output)
        report[ident]['file'] = output.relative_to(ROOT).as_posix()
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(f'{ident}: passed at {report[ident]["sha256"]}', flush=True)


if __name__ == '__main__':
    main()
