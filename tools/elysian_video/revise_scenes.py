"""Rebuild selected native scenes and preserve the existing delivery inputs."""

import argparse
import json
import subprocess

from . import calcium, emergency, imaging, post_pci, pressure, restenosis, structural, valve_implant
from .__main__ import FPS, LEGACY_FFMPEG, ROOT, SERIES
from .batch import build
from .encode import encode_scene


REVISIONS = {
    9: (restenosis.draw, 'restenosis-overrides.json', ('P02', 'P03', 'P04', 'P06', 'P07', 'P08', 'P09')),
    10: (post_pci.draw, 'post-pci-overrides.json', ('P01', 'P04', 'P05', 'P07', 'P08', 'P09')),
    11: (pressure.draw, 'pressure-overrides.json', ('P02', 'P03', 'P04', 'P05', 'P06', 'P08', 'P09')),
    12: (imaging.draw, 'inside-imaging-overrides.json', ('P01', 'P02', 'P04', 'P05', 'P06', 'P07', 'P08')),
    13: (calcium.draw, 'calcium-overrides.json', ('P01', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08')),
    14: (emergency.emergency, 'clinical-picture-overrides.json', ('P01', 'P02', 'P03', 'P04', 'P05', 'P07')),
    15: (emergency.multiple, 'clinical-picture-overrides.json', ('P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08')),
    17: (structural.plan, 'structural-overrides.json', ('P01', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08')),
    18: (valve_implant.draw, 'tavi-overrides.json', ('P03', 'P04', 'P05', 'P08', 'P09', 'P12')),
    19: (structural.recovery, 'structural-overrides.json', ('P05', 'P07', 'P08')),
    20: (structural.compare, 'structural-overrides.json', ('P02', 'P04', 'P05', 'P06', 'P07', 'P08')),
}


def revise(number, ffmpeg):
    episode = SERIES / f'episode-{number:02}'
    draw, override_file, scenes = REVISIONS[number]
    visuals = episode / 'visuals'
    overrides = visuals / override_file
    replacements = json.loads(overrides.read_text(encoding='utf-8-sig'))
    timeline = json.loads((episode / 'timeline.json').read_text(encoding='utf-8-sig'))

    for scene in timeline['scenes']:
        ident = scene['id']
        if ident not in scenes:
            continue
        frames = scene['end_frame'] - scene['start_frame']
        target = visuals / f'{ident}-motion-revision.mp4'
        pending = visuals / f'{ident}-motion-revision.part.mp4'

        def frame(canvas, index):
            draw(canvas, ident, index / max(1, frames - 1), index / FPS)
            if index and index % 180 == 0:
                print(f'{ident}: {index}/{frames} frames', flush=True)

        print(f'Rebuilding {episode.name} {ident} ({frames} frames)', flush=True)
        encode_scene(pending, frames, frame, preset='veryfast', threads=2)
        subprocess.run(
            [str(ffmpeg), '-hide_banner', '-v', 'error', '-xerror', '-i', str(pending),
             '-map', '0:v:0', '-an', '-f', 'null', '-'],
            check=True,
        )
        pending.replace(target)
        replacements[ident]['path'] = target.relative_to(ROOT).as_posix()

    pending_map = overrides.with_suffix('.json.tmp')
    pending_map.write_text(json.dumps(replacements, indent=2) + '\n', encoding='utf-8')
    pending_map.replace(overrides)
    return build(episode, ffmpeg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episodes', nargs='+', type=int, choices=tuple(REVISIONS))
    args = parser.parse_args()
    statuses = [revise(number, LEGACY_FFMPEG.resolve()) for number in args.episodes]
    return any(statuses)


if __name__ == '__main__':
    raise SystemExit(main())
