"""Reframe the wrist-compression beat without the inherited footer."""

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import av
import skia

from tools.elysian_video.__main__ import FPS, HEIGHT, WIDTH
from tools.elysian_video.encode import encode_scene


def render():
    visuals = Path(__file__).resolve().parent
    episode = visuals.parent
    spec = spec_from_file_location('pci_motion', episode / 'motion_repair.py')
    motion = module_from_spec(spec)
    spec.loader.exec_module(motion)
    timeline = json.loads((episode / 'timeline.json').read_text(encoding='utf-8-sig'))
    scene = next(scene for scene in timeline['scenes'] if scene['id'] == 'P12')
    frames = scene['end_frame'] - scene['start_frame']
    target = visuals / 'P12-motion-wrist-clean.mp4'
    pending = target.with_suffix('.part.mp4')

    def draw(canvas, index):
        time = index / FPS
        if not 4.85 <= time < 9.6:
            motion.remove_equipment(canvas, time, frames / FPS)
            return

        # The earlier wrist composition starts its own footer at y=582.
        # Enlarge just the artwork field so no portion of that footer is visible.
        scale = (640 - 152) / (582 - 152)
        canvas.save()
        canvas.clipRect(skia.Rect.MakeLTRB(0, 152, 1280, 640))
        canvas.translate(640, 152)
        canvas.scale(scale, scale)
        canvas.translate(-640, -152)
        progress = .34 + .66 * motion.e(time, 4.9, 9.57)
        motion.ink.scene(canvas, 'P35', progress, time)
        canvas.restore()
        motion.frame(canvas, 'Pressure at the wrist', 'A compression band helps control bleeding')

    encode_scene(pending, frames, draw, preset='ultrafast', threads=1)
    with av.open(str(pending)) as media:
        stream = media.streams.video[0]
        if (stream.width, stream.height, stream.frames) != (WIDTH, HEIGHT, frames):
            raise ValueError('The wrist-compression repair has the wrong picture format or duration')
        stream.codec_context.thread_count = 1
        if sum(1 for _ in media.decode(stream)) != frames:
            raise ValueError('The wrist-compression repair did not decode to the full scene length')
    pending.replace(target)
    print(target, flush=True)


if __name__ == '__main__':
    render()
