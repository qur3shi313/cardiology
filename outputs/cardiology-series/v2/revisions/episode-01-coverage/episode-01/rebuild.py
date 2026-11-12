"""Rebuild the Episode 01 coverage revision from its exact prior release candidate."""

import argparse
import json
import os
from functools import lru_cache
from hashlib import sha256
from math import cos, pi
from pathlib import Path
from random import Random
import shutil
import sys


EPISODE = Path(__file__).resolve().parent
ROOT = next(p for p in EPISODE.parents if (p / 'tools/elysian_video').is_dir())
sys.path.insert(0, str(ROOT / 'tools'))

import skia

from elysian_video.__main__ import FPS, HEIGHT, LEGACY_FFMPEG, SERIES, WIDTH, picture, run, scratch
from elysian_video.access import BOLD, HEADING, LOGO, REGULAR, grad, line, rect, smooth, solid, text
from elysian_video.angiogram import IMAGING, block, contrast_paths, dot, header
from elysian_video.encode import encode_scene
from elysian_video.finish import finish


ORIGINAL = SERIES / 'episode-01'
ORIGINAL_HASH = 'c34bb7c5ef22a7d3d90d466cdbb8518fbefbe9e9b420228931c33c76c8006836'
DELIVERY = EPISODE / 'delivery'
VISUALS = EPISODE / 'visuals'
MASTER = DELIVERY / 'episode-01-1440p.mp4'
CHANGED = (*IMAGING, 'P40')
FILM = (18, 150, 1244, 551, 36)


def digest(file):
    with file.open('rb') as stream:
        value = sha256()
        for block_bytes in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block_bytes)
    return value.hexdigest()


@lru_cache(maxsize=1)
def radiograph_plate():
    surface = skia.Surface(WIDTH, HEIGHT)
    canvas = surface.getCanvas()
    canvas.scale(2, 2)
    rect(canvas, 0, 0, 1280, 720, grad(0, 0, 1210, 720, ['#102323', '#1b3432', '#0b1e20']))
    x, y, width, height, radius = FILM
    box = skia.Rect.MakeXYWH(x, y, width, height)
    canvas.clipRRect(skia.RRect.MakeRectXY(box, radius, radius), True)
    rect(canvas, x, y, width, height,
         grad(150, 149, 1220, 707, ['#85908a', '#c4cdc5', '#9aa6a0', '#667773']))
    canvas.drawOval(skia.Rect.MakeXYWH(380, 185, 550, 438), solid('#dce2d7', 112))
    for i in range(7):
        x, y = 62 + 18 * i, 174 + 69 * i
        line(canvas, [(x, y + 48), (320, y + 8), (618, y), (946, y + 22), (1224, y + 76)],
             '#dce2d8', 11, 41)
    random = Random(721)
    for _ in range(1430):
        dot(canvas, random.randrange(20, 1260), random.randrange(151, 702),
            random.choice([1, 1.5, 2]), '#38423d', random.randrange(8, 26))
    line(canvas, [(43, 683), (1236, 683)], '#b1cec1', 2, 100)
    return surface.makeImageSnapshot()


def draw_imaging(canvas, ident, progress, seconds):
    side, title = IMAGING[ident]
    canvas.drawImageRect(radiograph_plate(), skia.Rect.MakeWH(1280, 720),
                         skia.SamplingOptions(skia.FilterMode.kNearest))
    if ident == 'P01':
        contrast_paths(canvas, side, smooth(progress / .66),
                       round(245 - 49 * smooth((progress - .75) / .25)), 4, True)
        if seconds < 5:
            text(canvas, 'SIMULATED CORONARY X-RAY', 56, 64, 25, '#e1f0e8')
        else:
            header(canvas, title, 'SIMULATED X-RAY', True)
            block(canvas, 54, 588, 314, 48, 12, solid('#1a3934', 231))
            text(canvas, 'Wrist or groin access', 68, 621, 27, '#e7f2eb')
    elif ident == 'P29':
        spot = contrast_paths(canvas, side, smooth(progress / .53),
                              round(245 - 70 * smooth((progress - .58) / .42)), -13, True)
        if progress > .32:
            x, y = spot
            radius = 23 + 1.2 * cos(progress * 8 * pi)
            edge = solid('#ffedb9', 245)
            edge.setStyle(skia.Paint.kStroke_Style)
            edge.setStrokeWidth(3.6)
            canvas.drawCircle(x, y, radius, edge)
            line(canvas, [(x + radius, y - 12), (x + 111, y - 52)], '#ffedb9', 3)
            block(canvas, x + 111, y - 79, 165, 53, 11, solid('#253633', 240))
            text(canvas, 'Narrowing', x + 123, y - 44, 29, '#fff1cf')
        header(canvas, title, 'SIMULATED X-RAY', True)
    else:
        first = progress < .5
        phase = (progress if first else progress - .5) * 2
        angle = (-19 if first else 26) if side == 'right' else (7 if first else -14)
        contrast_paths(canvas, side, smooth((phase - .01) / .63),
                       round(245 * (1 - smooth((phase - .62) / .38))), angle, False)
        header(canvas, title, 'SIMULATED X-RAY', True)
        block(canvas, 54, 587, 294, 49, 11, solid('#132d2a', 229))
        text(canvas, 'First projection' if first else 'Second projection', 70, 620, 27, '#e6f3e9')


def draw_end(canvas, progress):
    rect(canvas, 0, 0, 1280, 720, grad(0, 0, 1240, 720, ['#edf6ee', '#d9ece3', '#c6e0d4']))
    canvas.drawImageRect(LOGO, skia.Rect.MakeXYWH(58, 44, 49, 49),
                         skia.SamplingOptions(skia.FilterMode.kLinear))
    text(canvas, 'Elysian Biomedical LLP', 123, 77, 24, '#246454')
    text(canvas, 'Cardiology Education Series', 60, 164, 48, '#133e34', HEADING)
    text(canvas, 'Know your result and recovery plan', 62, 222, 30, '#275b4f', REGULAR)
    block(canvas, 61, 264, 660, 166, 21, solid('#f5faf4', 246))
    text(canvas, 'NEXT EPISODE', 84, 305, 23, '#276c58', BOLD)
    text(canvas, 'Wrist versus groin access', 83, 354, 38, '#153f35', HEADING)
    text(canvas, 'and why the team chooses a route', 84, 399, 34, '#153f35', HEADING)
    text(canvas, 'Clinical sources', 62, 489, 24, '#246454', BOLD)
    text(canvas, 'AHA, NHS and SCAI', 62, 529, 31, '#173f36', HEADING)
    text(canvas, 'References in the description', 62, 568, 23, '#275b4f', REGULAR)
    # The quiet right column remains clear for native YouTube end elements.
    edge = 56 + 560 * smooth(progress)
    block(canvas, 62, 605, 630, 13, 6, solid('#bad8cc'))
    block(canvas, 62, 605, edge, 13, 6, solid('#31745f'))


def replacement(row):
    ident = row['id']
    frames = row['end_frame'] - row['start_frame']
    target = VISUALS / f'{ident}-revised.mp4'
    if not target.is_file():
        temporary = target.with_suffix('.part.mp4')

        def draw(canvas, frame):
            progress = frame / max(1, frames - 1)
            if ident == 'P40':
                draw_end(canvas, progress)
            else:
                draw_imaging(canvas, ident, progress, frame / FPS)

        print(f'Encoding {ident}, {frames} frames', flush=True)
        encode_scene(temporary, frames, draw, threads=3)
        temporary.replace(target)
    return {'path': target.relative_to(ROOT).as_posix(), 'in_sec': 0, 'out_sec': frames / FPS,
            'reference_only': False, 'native_composition': True}


def prepare():
    VISUALS.mkdir(exist_ok=True)
    DELIVERY.mkdir(exist_ok=True)
    for name in ('timeline.json', 'episode-01.en.srt', 'chapters.txt', 'finish-config.json',
                 'youtube-description.txt', 'youtube-metadata.json'):
        target = EPISODE / name
        if not target.is_file():
            shutil.copyfile(ORIGINAL / name, target)
    timeline = json.loads((EPISODE / 'timeline.json').read_text(encoding='utf-8-sig'))
    return timeline['scenes']


def write_scene_list(encodes, work):
    target = work / 'encoded-scenes.txt'
    lines = []
    for encoded in encodes:
        relative_path = Path(os.path.relpath(encoded, work)).as_posix()
        escaped_path = relative_path.replace("'", "'\\''")
        lines.append(f"file '{escaped_path}'\n")
    target.write_text(''.join(lines), encoding='utf-8')
    return target


def split_original(ffmpeg, source, rows, work):
    print('Recovering missing scene cache entries from the original master', flush=True)
    cuts = ','.join(str(row['start_frame']) for row in rows[1:])
    run(ffmpeg, '-v', 'error', '-y', '-i', source, '-map', '0:v:0', '-c', 'copy', '-f', 'segment',
        '-segment_frames', cuts, '-reset_timestamps', '1', '-video_track_timescale', '30000', work / 'old-%02d.mp4')
    return {row['id']: work / f'old-{i:02d}.mp4' for i, row in enumerate(rows)}


def render(ffmpeg, rows, work):
    old_master = ORIGINAL / 'delivery' / MASTER.name
    if digest(old_master) != ORIGINAL_HASH:
        raise RuntimeError('The original release candidate changed after review.')
    original_stamp = json.loads((old_master.parent / '.batch-completed.json').read_text())
    old_tokens = original_stamp['fingerprint']['picture_tokens']
    cache = ROOT / 'work/cardiology-v2-scratch/scene-cache'
    encoded_visuals = VISUALS / 'slow'
    encoded_visuals.mkdir(exist_ok=True)
    if len(old_tokens) != len(rows):
        raise RuntimeError('The original scene cache index does not match the timeline.')
    selections, encodes, recovered = {}, [], {}
    for row, token in zip(rows, old_tokens):
        ident = row['id']
        if ident in CHANGED:
            spec = replacement(row)
            selections[ident] = spec
            encoded = picture(ffmpeg, {**row, 'footage': spec}, encoded_visuals, 'slow')
        else:
            encoded = cache / f'{token}.mp4'
            if not encoded.is_file():
                if not recovered:
                    recovered = split_original(ffmpeg, old_master, rows, work)
                encoded = recovered[ident]
                if not encoded.is_file():
                    raise FileNotFoundError(f'Exact original scene {ident}: {encoded}')
        encodes.append(encoded)
    (EPISODE / 'picture-overrides.json').write_text(json.dumps(selections, indent=2) + '\n', encoding='utf-8')
    if not MASTER.is_file():
        picture_list = write_scene_list(encodes, work)
        temporary = MASTER.with_suffix('.part.mp4')
        print('Multiplexing revised pictures with the original voice and subtitles', flush=True)
        run(ffmpeg, '-v', 'error', '-y', '-f', 'concat', '-safe', 0, '-i', picture_list, '-i', old_master,
            '-map', '0:v:0', '-map', '1:a:0', '-map', '1:s:0', '-c', 'copy',
            '-movflags', '+faststart', temporary)
        temporary.replace(MASTER)
    return MASTER


def complete_delivery(ffmpeg, master):
    fallback = DELIVERY / 'episode-01-1080p.mp4'
    if not fallback.is_file():
        temporary = fallback.with_suffix('.part.mp4')
        print('Encoding 1080p delivery', flush=True)
        run(ffmpeg, '-v', 'error', '-y', '-threads', 2, '-filter_threads', 2, '-i', master,
            '-map', '0', '-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
            '-crf', 16, '-profile:v', 'high', '-g', 60, '-bf', 2, '-threads', 4,
            '-c:a', 'copy', '-c:s', 'copy', '-movflags', '+faststart', temporary)
        temporary.replace(fallback)
    if not all((DELIVERY / f'episode-01-{name}').is_file() for name in ('thumbnail.jpg', 'short.mp4')):
        finish(EPISODE, ffmpeg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    ffmpeg = os.environ.get('ELYSIAN_FFMPEG') or shutil.which('ffmpeg') or LEGACY_FFMPEG
    parser.add_argument('--ffmpeg', type=Path, default=Path(ffmpeg))
    args = parser.parse_args()
    with scratch('elysian-coverage-source-') as source_work:
        master = render(args.ffmpeg.resolve(), prepare(), Path(source_work))
    print(f'Master ready for exact visual review: {master}', flush=True)
    complete_delivery(args.ffmpeg.resolve(), master)
    print(f'Delivery encodes complete: {DELIVERY}', flush=True)


if __name__ == '__main__':
    main()
