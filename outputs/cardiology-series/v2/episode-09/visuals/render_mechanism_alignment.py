"""Align the three illustrated causes with the locked English caption cues."""
import argparse
import json
from pathlib import Path
import re

from tools.elysian_video import restenosis
from tools.elysian_video.__main__ import FPS
from tools.elysian_video.encode import encode_scene


HERE = Path(__file__).resolve().parent


def cue_start(srt, beginning):
    for block in re.split(r'\n\s*\n', srt.strip()):
        _, timing, *lines = block.splitlines()
        if ' '.join(lines).startswith(beginning):
            hours, minutes, seconds, milliseconds = re.split(r'[:,]', timing.split(' --> ')[0])
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    raise ValueError(f'Missing locked caption cue: {beginning}')


def phase_frames():
    timeline = json.loads((HERE.parent / 'timeline.json').read_text(encoding='utf-8-sig'))
    scene = next(row for row in timeline['scenes'] if row['id'] == 'P03')
    srt = (HERE.parent / timeline['caption_file']).read_text(encoding='utf-8-sig')
    switch = [round(cue_start(srt, phrase) * FPS) - scene['start_frame'] for phrase in
              ('Tissue may grow inside a stent', 'New plaque can also develop in tissue')]
    stops = [0, *switch, scene['end_frame'] - scene['start_frame']]
    if not 0 < stops[1] < stops[2] < stops[3]:
        raise ValueError('Mechanism cue order does not match the locked scene')
    return stops


def draw(canvas, index, stops):
    stage = (index >= stops[1]) + (index >= stops[2])
    fraction = (index - stops[stage]) / (stops[stage + 1] - stops[stage])
    restenosis.draw(canvas, 'P03', (stage + fraction) / 3, index / FPS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    stops = phase_frames()
    print(f'Underexpansion, tissue growth and new plaque boundaries: {stops}', flush=True)
    if args.check_only:
        return
    temporary = HERE / 'P03-mechanisms-cue-aligned.part.mp4'
    final = HERE / 'P03-mechanisms-cue-aligned.mp4'
    encode_scene(temporary, stops[-1], lambda canvas, index: draw(canvas, index, stops),
                 preset='veryfast', threads=2)
    temporary.replace(final)
    print(final, flush=True)


if __name__ == '__main__':
    main()
