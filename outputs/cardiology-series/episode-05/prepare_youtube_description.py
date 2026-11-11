"""Append verified YouTube chapters using the finished episode timing."""

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def format_description(metadata, timing, storyboard):
    expected = [(scene['id'], scene['title']) for scene in storyboard]
    actual = [(scene['id'], scene['title']) for scene in timing['scenes']]
    if actual != expected or [scene_id for scene_id, _ in expected] != [*metadata['chapter_titles'], 'P12']:
        raise ValueError('The final timing does not match the Wrist vs Groin Access storyboard.')

    # Episode 04 uses the same 11 spoken scenes and silent P12 card structure.
    shared = HERE.parent / 'episode-04' / 'prepare_youtube_description.py'
    spec = spec_from_file_location('series_chapter_formatter', shared)
    module = module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module.description_for(metadata, timing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('timing', type=Path, help='Final master timing.json')
    args = parser.parse_args()
    metadata = json.loads((HERE / 'youtube-metadata.json').read_text(encoding='utf-8'))
    storyboard = json.loads((HERE / 'scenes.json').read_text(encoding='utf-8-sig'))
    timing = json.loads(args.timing.read_text(encoding='utf-8-sig'))
    sys.stdout.reconfigure(encoding='utf-8')
    print(format_description(metadata, timing, storyboard))


if __name__ == '__main__':
    main()
