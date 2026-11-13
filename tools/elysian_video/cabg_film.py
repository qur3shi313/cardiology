"""Prepare and assemble the first cardiac surgery film from timed narration."""

import argparse
import json
import re
from pathlib import Path

from . import timing
from .__main__ import FPS, LEGACY_FFMPEG, ROOT, run
from .batch import build, exclusive_build
from .encode import encode_scene


EPISODE = ROOT / 'outputs/cardiac-surgery-series/episode-01'
FFMPEG = LEGACY_FFMPEG.resolve()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def scene_rows():
    script = (EPISODE / 'narration-script.md').read_text(encoding='utf-8')
    headings = list(re.finditer(r'^## (P\d\d) · (.+)$', script, re.MULTILINE))
    rows = []
    for i, heading in enumerate(headings):
        ident, title = heading.groups()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(script)
        voice = script[heading.end():end].split('Leave the final eight seconds')[0].strip()
        rows.append({'id': ident, 'title': title, 'narration': ' '.join(voice.split()),
                     'visual_file': f'visuals/{ident}.mp4',
                     'target_start_sec': 0, 'target_end_sec': 1})
    if [row['id'] for row in rows] != [f'P{i:02}' for i in range(1, 13)]:
        raise ValueError('Expected all 12 scenes from the approved script')
    return rows


def combine_audio(first, second, output):
    run(FFMPEG, '-v', 'error', '-y', '-i', first, '-i', second,
        '-filter_complex',
        '[0:a]aresample=48000[a];[1:a]aresample=48000[b];[a][b]concat=n=2:v=0:a=1[out]',
        '-map', '[out]', '-ac', '1', '-c:a', 'flac', output)


def prepare(first, second, first_words, second_words):
    audio_dir = EPISODE / 'audio'
    audio_dir.mkdir(exist_ok=True)
    audio = audio_dir / 'alexander-cabg.flac'
    combine_audio(first, second, audio)
    first_duration = timing.measured_duration(first, FFMPEG)
    transcript = []
    for source, shift in ((first_words, 0), (second_words, first_duration)):
        words = json.loads(source.read_text(encoding='utf-8-sig'))['words']
        for word in words:
            transcript.append({**word, 'start': word['start'] + shift, 'end': word['end'] + shift})
    rows = scene_rows()
    for word in transcript:
        normalized = word['text'].strip().lower().rstrip('.,?!')
        if normalized in {'cabbage', 'stem-ee', 'stemee'}:
            word['text'] = 'CABG' if normalized == 'cabbage' else 'STEMI'
    alignment = audio_dir / 'scribe-alignment.json'
    write_json(alignment, {'words': transcript})
    write_json(EPISODE / 'scenes.json', rows)
    timeline = timing.prepare(EPISODE, audio, alignment, FFMPEG)
    timeline['duration_frames'] += 8 * FPS
    timeline['scenes'][-1]['end_frame'] += 8 * FPS
    write_json(EPISODE / 'timeline.json', timeline)
    print(f"{timeline['duration_frames'] / FPS:.3f} seconds, matched words "
          f"{timeline['voice_alignment']['matched_fraction']:.2%}", flush=True)
    return timeline


def author(selected):
    from . import cabg_core, cabg_graft, cabg_recovery

    visuals = EPISODE / 'visuals'
    visuals.mkdir(exist_ok=True)
    timeline = json.loads((EPISODE / 'timeline.json').read_text(encoding='utf-8'))
    cues_path = EPISODE / 'visual-cues.json'
    cues = json.loads(cues_path.read_text(encoding='utf-8')) if cues_path.is_file() else {}
    suffix = '-'.join(selected) if selected else 'all'
    with exclusive_build(visuals / f'.cabg-render-{suffix}.lock') as acquired:
        if not acquired:
            raise RuntimeError('Another CABG visual render is running')
        for row in timeline['scenes']:
            ident = row['id']
            if selected and ident not in selected:
                continue
            module = cabg_core if ident <= 'P05' else cabg_graft if ident <= 'P08' else cabg_recovery
            frames = row['end_frame'] - row['start_frame']
            final = visuals / f'{ident}.mp4'
            pending = final.with_suffix('.part.mp4')

            def frame(canvas, index):
                position = index / max(1, frames - 1)
                if module is cabg_graft:
                    module.draw(canvas, ident, position, index / FPS, cues=cues.get(ident))
                else:
                    module.draw(canvas, ident, position, index / FPS)

            print(f'Authoring {ident}, {frames} frames', flush=True)
            encode_scene(pending, frames, frame, preset='veryfast', threads=3)
            run(FFMPEG, '-v', 'error', '-xerror', '-i', pending, '-an', '-f', 'null', '-')
            pending.replace(final)
    return 0


def assemble():
    schedule = EPISODE.parent / 'schedule.json'
    if schedule.is_file():
        entries = json.loads(schedule.read_text(encoding='utf-8-sig'))['targets']
        if any(row['episode'] == EPISODE.name and row.get('studio_verified') for row in entries):
            print('The scheduled release is frozen. Use its recorded delivery package.', flush=True)
            return 0
    visuals = EPISODE / 'visuals'
    timeline = json.loads((EPISODE / 'timeline.json').read_text(encoding='utf-8'))
    overrides = {}
    for row in timeline['scenes']:
        ident = row['id']
        source = visuals / f'{ident}.mp4'
        if not source.is_file():
            raise FileNotFoundError(source)
        overrides[ident] = {'path': source.relative_to(ROOT).as_posix(), 'in_sec': 0,
                            'out_sec': (row['end_frame'] - row['start_frame']) / FPS,
                            'reference_only': False, 'native_composition': True}
    write_json(visuals / 'cabg-overrides.json', overrides)
    return build(EPISODE, FFMPEG, native_copy=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    timing_parser = actions.add_parser('prepare')
    for arg in ('first_audio', 'second_audio', 'first_words', 'second_words'):
        timing_parser.add_argument(arg, type=Path)
    author_parser = actions.add_parser('render')
    author_parser.add_argument('scenes', nargs='*')
    actions.add_parser('assemble')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.first_audio, args.second_audio, args.first_words, args.second_words)
        return 0
    return author(args.scenes) if args.action == 'render' else assemble()


if __name__ == '__main__':
    raise SystemExit(main())
