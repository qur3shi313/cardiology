"""Keep the limb illustration clear of the emergency warning text."""

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import av

from tools.elysian_video.__main__ import FPS, HEIGHT, WIDTH
from tools.elysian_video.encode import encode_scene


def render():
    visuals = Path(__file__).resolve().parent
    episode = visuals.parent
    spec = spec_from_file_location('pci_motion', episode / 'motion_repair.py')
    motion = module_from_spec(spec)
    spec.loader.exec_module(motion)
    timeline = json.loads((episode / 'timeline.json').read_text(encoding='utf-8-sig'))
    scene = next(scene for scene in timeline['scenes'] if scene['id'] == 'P15')
    frames = scene['end_frame'] - scene['start_frame']
    target = visuals / 'P15-motion-emergency-clean.mp4'
    pending = target.with_suffix('.part.mp4')

    def draw(canvas, index):
        time = index / FPS
        if not 11.35 <= time < 14.44:
            motion.editorial(canvas, 'P15', time, frames / FPS)
            return

        # Retain the moving wrist, but keep its furthest edge left of x=665.
        progress = (time - 11.35) / (14.44 - 11.35)
        motion.field(canvas, True)
        motion.anatomy.wrist_surface(canvas, 1.31, 24 * motion.e(progress, 0, 1), 100, cool=True)
        motion.ink.text(canvas, 'Cold or numb hand or foot', 714, 359, 36, motion.LIGHT)
        motion.ink.text(canvas, 'on the accessed side', 714, 411, 36, motion.LIGHT)
        motion.frame(canvas, 'Get emergency help', 'Call your local emergency number', dark=True)

    encode_scene(pending, frames, draw, preset='ultrafast', threads=1)
    with av.open(str(pending)) as media:
        stream = media.streams.video[0]
        if (stream.width, stream.height, stream.frames) != (WIDTH, HEIGHT, frames):
            raise ValueError('The emergency warning repair has the wrong picture format or duration')
        stream.codec_context.thread_count = 1
        if sum(1 for _ in media.decode(stream)) != frames:
            raise ValueError('The emergency warning repair did not decode to the full scene length')
    pending.replace(target)
    print(target, flush=True)


if __name__ == '__main__':
    render()
