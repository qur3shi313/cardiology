"""Prepare and assemble the cardiac surgery films from timed narration."""

import argparse
import json
import re
from pathlib import Path

from . import timing
from .__main__ import FPS, LEGACY_FFMPEG, ROOT, run
from .batch import build, exclusive_build
from .encode import encode_scene


SERIES = ROOT / 'outputs/cardiac-surgery-series'
FIRST_EPISODE = SERIES / 'episode-01'
FFMPEG = LEGACY_FFMPEG.resolve()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def scene_rows(episode):
    script = (episode / 'narration-script.md').read_text(encoding='utf-8')
    headings = list(re.finditer(r'^## (P\d\d) · (.+)$', script, re.MULTILINE))
    rows = []
    for i, heading in enumerate(headings):
        ident, title = heading.groups()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(script)
        voice = script[heading.end():end].split('Leave the final eight seconds')[0].strip()
        rows.append({'id': ident, 'title': title, 'narration': ' '.join(voice.split()),
                     'visual_file': f'visuals/{ident}.mp4',
                     'target_start_sec': 0, 'target_end_sec': 1})
    count = 12 if episode == FIRST_EPISODE else 9
    if [row['id'] for row in rows] != [f'P{i:02}' for i in range(1, count + 1)]:
        raise ValueError(f'Expected all {count} scenes from the approved script')
    return rows


def combine_audio(first, second, output):
    run(FFMPEG, '-v', 'error', '-y', '-i', first, '-i', second,
        '-filter_complex',
        '[0:a]aresample=48000[a];[1:a]aresample=48000[b];[a][b]concat=n=2:v=0:a=1[out]',
        '-map', '[out]', '-ac', '1', '-c:a', 'flac', output)


def prepare(episode, first, first_words, second=None, second_words=None):
    audio_dir = episode / 'audio'
    audio_dir.mkdir(exist_ok=True)
    audio = audio_dir / 'alexander-cabg.flac'
    transcripts = [(first_words, 0)]
    if second is None:
        run(FFMPEG, '-v', 'error', '-y', '-i', first, '-ar', '48000', '-ac', '1', '-c:a', 'flac', audio)
    else:
        combine_audio(first, second, audio)
        transcripts.append((second_words, timing.measured_duration(first, FFMPEG)))
    transcript = []
    for source, shift in transcripts:
        words = json.loads(source.read_text(encoding='utf-8-sig'))['words']
        for word in words:
            transcript.append({**word, 'start': word['start'] + shift, 'end': word['end'] + shift})
    rows = scene_rows(episode)
    for word in transcript:
        normalized = word['text'].strip().lower().rstrip('.,?!')
        if normalized in {'cabbage', 'stem-ee', 'stemee'}:
            word['text'] = 'CABG' if normalized == 'cabbage' else 'STEMI'
    alignment = audio_dir / 'scribe-alignment.json'
    write_json(alignment, {'words': transcript})
    write_json(episode / 'scenes.json', rows)
    timeline = timing.prepare(episode, audio, alignment, FFMPEG)
    timeline['duration_frames'] += 8 * FPS
    timeline['scenes'][-1]['end_frame'] += 8 * FPS
    write_json(episode / 'timeline.json', timeline)
    print(f"{timeline['duration_frames'] / FPS:.3f} seconds, matched words "
          f"{timeline['voice_alignment']['matched_fraction']:.2%}", flush=True)
    return timeline


def scene_renderer(episode, ident):
    from . import cabg_core, cabg_graft, cabg_recovery
    from . import cabg_followthrough, cabg_icu, cabg_icu_followup, cabg_icu_monitor, cabg_routes

    if episode.name == 'episode-01':
        if ident <= 'P05':
            return cabg_core.draw, False
        if ident <= 'P08':
            return cabg_graft.draw, True
        return cabg_recovery.draw, False
    if episode.name == 'episode-02':
        return (cabg_routes.draw, True) if ident <= 'P05' else (cabg_followthrough.draw, False)
    if ident <= 'P03':
        return cabg_icu.draw, True
    if ident <= 'P06':
        return cabg_icu_monitor.draw, False
    return cabg_icu_followup.draw, True


def author(episode, selected):
    visuals = episode / 'visuals'
    visuals.mkdir(exist_ok=True)
    timeline = json.loads((episode / 'timeline.json').read_text(encoding='utf-8'))
    cues_path = episode / 'visual-cues.json'
    cues = json.loads(cues_path.read_text(encoding='utf-8')) if cues_path.is_file() else {}
    suffix = '-'.join(selected) if selected else 'all'
    with exclusive_build(visuals / f'.cabg-render-{suffix}.lock') as acquired:
        if not acquired:
            raise RuntimeError('Another CABG visual render is running')
        for row in timeline['scenes']:
            ident = row['id']
            if selected and ident not in selected:
                continue
            draw, has_cues = scene_renderer(episode, ident)
            frames = row['end_frame'] - row['start_frame']
            final = visuals / f'{ident}.mp4'
            pending = final.with_suffix('.part.mp4')

            def frame(canvas, index):
                position = index / max(1, frames - 1)
                if has_cues:
                    draw(canvas, ident, position, index / FPS, cues=cues.get(ident))
                else:
                    draw(canvas, ident, position, index / FPS)

            print(f'Authoring {ident}, {frames} frames', flush=True)
            encode_scene(pending, frames, frame, preset='veryfast', threads=3)
            run(FFMPEG, '-v', 'error', '-xerror', '-i', pending, '-an', '-f', 'null', '-')
            pending.replace(final)
    return 0


def assemble(episode):
    schedule = episode.parent / 'schedule.json'
    if schedule.is_file():
        entries = json.loads(schedule.read_text(encoding='utf-8-sig'))['targets']
        if any(row['episode'] == episode.name and row.get('studio_verified') for row in entries):
            print('The scheduled release is frozen. Use its recorded delivery package.', flush=True)
            return 0
    visuals = episode / 'visuals'
    timeline = json.loads((episode / 'timeline.json').read_text(encoding='utf-8'))
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
    return build(episode, FFMPEG, native_copy=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', choices=('episode-01', 'episode-02', 'episode-03'),
                        default=FIRST_EPISODE.name)
    actions = parser.add_subparsers(dest='action', required=True)
    timing_parser = actions.add_parser('prepare')
    for arg in ('first_audio', 'second_audio', 'first_words', 'second_words'):
        timing_parser.add_argument(arg, type=Path)
    single = actions.add_parser('prepare-single')
    single.add_argument('audio', type=Path)
    single.add_argument('words', type=Path)
    author_parser = actions.add_parser('render')
    author_parser.add_argument('scenes', nargs='*')
    actions.add_parser('assemble')
    args = parser.parse_args()
    episode = SERIES / args.episode
    if args.action == 'prepare':
        prepare(episode, args.first_audio, args.first_words, args.second_audio, args.second_words)
        return 0
    if args.action == 'prepare-single':
        prepare(episode, args.audio, args.words)
        return 0
    return author(episode, args.scenes) if args.action == 'render' else assemble(episode)


if __name__ == '__main__':
    raise SystemExit(main())
