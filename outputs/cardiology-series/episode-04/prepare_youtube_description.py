"""Append upload chapters using the final rendered scene timing."""

import argparse
import json
from math import floor
from pathlib import Path
import sys


def description_for(metadata, timing):
    scenes = timing['scenes']
    names = metadata['chapter_titles']
    ids = [scene['id'] for scene in scenes]
    if ids != [*names, 'P12']:
        raise ValueError('Assembly scenes differ from the TAVI storyboard. Review before adding chapters.')
    starts = [scene['start_seconds'] for scene in scenes]
    duration = timing['video_seconds']
    if starts[0] != 0 or duration <= starts[-1] or starts != sorted(set(starts)):
        raise ValueError('Assembly scene starts or final duration are invalid.')

    chapters = []
    for scene in scenes:
        scene_id = scene['id']
        if scene_id not in names:
            continue
        seconds = floor(scene['start_seconds'] + 1e-8)
        if duration - seconds < 10 or chapters and seconds - chapters[-1][0] < 10:
            continue
        chapters.append((seconds, names[scene_id]))

    if len(chapters) < 3:
        raise ValueError('The assembled timeline does not support three 10-second chapters.')
    lines = [f'{seconds // 60:02d}:{seconds % 60:02d} {name}' for seconds, name in chapters]
    description = '\n'.join([metadata['description'], '', 'Chapters', *lines])
    if len(description) > 5000 or len(metadata['title']) > 100:
        raise ValueError('The upload metadata exceeds YouTube field lengths.')
    return description


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('timing', type=Path, help='Final assembly timing.json')
    args = parser.parse_args()
    metadata_path = Path(__file__).with_name('youtube-metadata.json')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    timing = json.loads(args.timing.read_text(encoding='utf-8-sig'))
    sys.stdout.reconfigure(encoding='utf-8')
    print(description_for(metadata, timing))


if __name__ == '__main__':
    main()
