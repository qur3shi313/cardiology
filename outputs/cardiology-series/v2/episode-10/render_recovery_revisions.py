"""Targeted animation updates for the post-PCI recovery episode."""

import argparse
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
import json
from math import pi, sin
import os
from pathlib import Path

import skia

from tools.elysian_video import access, angiogram, restenosis, stent
from tools.elysian_video.__main__ import FPS, LEGACY_FFMPEG, SERIES
from tools.elysian_video.encode import encode_scene
from tools.elysian_video.qa import file_hash, freeze_report, invoke

_spec = spec_from_file_location('recovery_art', SERIES / 'episode-05' / 'render_recovery_repairs.py')
recovery_art = module_from_spec(_spec)
_spec.loader.exec_module(recovery_art)


def platelets_in_stent(canvas, elapsed):
    with_medicine = elapsed >= 5.53
    restenosis.lumen_view(canvas, elapsed, 'open', scaffold=False)
    stent.stent(canvas, stent.LESION, 116, False)
    canvas.save()
    canvas.clipPath(stent.artery_plate(1)[1], doAntiAlias=True)
    for index in range(26):
        x = (index * 89 + elapsed * (63 + 3 * (index % 7))) % 1360 - 40
        y = stent.center(x) + ((index * 41) % 151) - 75
        proximity = max(0, 1 - abs(x - stent.LESION) / 120)
        attraction = (.08 if with_medicine else .42) * proximity
        x += attraction * (stent.LESION + (index % 4 - 2) * 18 - x)
        y += attraction * (stent.center(stent.LESION) - 47 - y)
        shape = skia.Rect.MakeXYWH(x - 13, y - 8, 26, 16)
        canvas.drawOval(shape, access.solid('#f6d99d', 232))
        canvas.drawOval(skia.Rect.MakeXYWH(x - 5, y - 4, 10, 7), access.solid('#b87954', 223))
    canvas.restore()
    stent.stent(canvas, stent.LESION, 116, True)
    angiogram.header(canvas, 'The medicine plan after a stent', 'RECOVERY AFTER PCI')
    caption = 'Less likely to clump with antiplatelet medicines' if with_medicine else 'Platelets can gather near the stent'
    access.text(canvas, caption, 55, 673, 31, '#184c42')
    access.text(canvas, 'Illustrated examples', 962, 673, 25, '#276151', access.REGULAR)


def medicine_plan(canvas, elapsed):
    if elapsed < 11.05:
        platelets_in_stent(canvas, elapsed)
        return
    if elapsed < 16.1:
        restenosis.card(canvas, 'The medicine plan after a stent', 'Your plan is individual',
                        ('Reason for PCI, bleeding risk','and other medicines matter'),
                        'medicine', (elapsed - 11.05) / 5.05, elapsed)
    else:
        document_scene(canvas, 'The medicine plan after a stent', 'Check your discharge summary',
                       ('Ask which plan applies to you',),
                       ('Medicine plan', ('Your instructions', 'Your medicines', 'Who to contact')),
                       min(1, (elapsed - 16.1) / 5.86))


def closing_credits(canvas):
    access.rect(canvas, 0, 0, 1280, 720, access.grad(0, 0, 1280, 720, ['#eaf5ec', '#bfded0']))
    angiogram.header(canvas, 'Clinical sources', 'RECOVERY AFTER PCI')
    access.text(canvas, 'NHS · NHLBI · American Heart Association', 56, 232, 35, '#184f44')
    access.text(canvas, 'ACC / AHA clinical practice guidelines', 56, 291, 32, '#184f44')
    access.text(canvas, 'Original medical illustrations', 56, 389, 31, '#1d5147')
    access.text(canvas, 'Synthetic English narration', 56, 434, 31, '#1d5147')
    access.text(canvas, 'Next: How FFR and iFR help assess', 56, 541, 31, '#173e37')
    access.text(canvas, 'a coronary narrowing', 56, 581, 31, '#173e37')
    access.text(canvas, 'Follow your own care team’s advice', 56, 673, 29, '#27574d', access.REGULAR)


@lru_cache(maxsize=12)
def document_art(title, rows):
    surface = skia.Surface(670, 510)
    canvas = surface.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    angiogram.block(canvas, 12, 12, 635, 480, 33, access.solid('#78ad9b'))
    angiogram.block(canvas, 2, 2, 635, 480, 32, access.solid('#f4fcf0'))
    angiogram.block(canvas, 28, 27, 584, 97, 23, access.solid('#195449'))
    access.text(canvas, title, 58, 90, 42, '#f4fff2')
    for index, row in enumerate(rows):
        y = 151 + 99 * index
        angiogram.block(canvas, 28, y, 584, 82, 18, access.solid('#d7eadc'))
        access.line(canvas, [(54, y + 39), (68, y + 54), (93, y + 27)], '#267e66', 8)
        access.text(canvas, row, 111, y + 53, 34, '#204d43')
        access.line(canvas, [(112, y + 67), (558, y + 67)], '#81a991', 4)
    return surface.makeImageSnapshot()


def document_scene(canvas, title, heading, detail, page, progress):
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#e5f2e8'))
    angiogram.block(canvas, 540, 174, 694, 466, 26, access.solid('#285e53'))
    canvas.save()
    canvas.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(540, 174, 694, 466), 26, 26), doAntiAlias=True)
    scale = 1 + .18 * progress
    canvas.translate(654 - 185 * progress, 214 - 163 * progress)
    canvas.rotate(-13 + 17 * progress, 320, 255)
    canvas.scale(scale, scale)
    canvas.drawImage(document_art(*page), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))
    canvas.restore()
    angiogram.header(canvas, title, 'RECOVERY AFTER PCI')
    font = skia.Font(access.BOLD, 38)
    heading_size = min(38, int(38 * 465 / font.measureText(heading)))
    access.text(canvas, heading, 55, 321, heading_size, '#164c3f')
    for index, line in enumerate(detail):
        access.text(canvas, line, 55, 376 + 44 * index, 31, '#2b5a4e', access.REGULAR)
    access.text(canvas, 'Follow your own care team’s advice', 55, 674, 29, '#276353')


def before_medicine_change(canvas, elapsed):
    if elapsed < 7.38:
        document_scene(canvas, 'Ask before changing medicines', 'Before you leave',
                       ('Confirm which medicines', 'are new and whom to call'),
                       ('Medicine list', ('New medicines', 'Side effects', 'Missed doses')), elapsed / 7.38)
    elif elapsed < 12:
        document_scene(canvas, 'Ask before changing medicines', 'Planning another procedure?',
                       ('Tell that clinician about', 'your stent and medicines'),
                       ('Appointment', ('Surgery or dental work', 'Your stent', 'Current medicines')), (elapsed - 7.38) / 4.62)
    else:
        document_scene(canvas, 'Ask before changing medicines', 'Coordinate with your teams',
                       ('They can agree on what', 'to do before any change'),
                       ('Shared plan', ('Cardiology team', 'Procedure team', 'Agreed instructions')), (elapsed - 12) / 5.5)


def home_recovery(canvas, elapsed):
    if elapsed < 5.8:
        document_scene(canvas, 'Activity and the wound at home', 'Use your written instructions',
                       ('Ask when work and driving', 'can safely resume'),
                       ('At home', ('Dressing', 'Activity and lifting', 'Work and driving')), elapsed / 5.8)
    elif elapsed < 14:
        warning = elapsed >= 10.7
        progress = (elapsed - 10.7) / 3.3 if warning else (elapsed - 5.8) / 4.9
        recovery_art.image(canvas, recovery_art.arm_plate(warning), zoom=1 + .44 * progress, x=642, y=432)
        if not warning:
            recovery_art.gloved_check(canvas, progress)
        title = 'Contact your care team promptly' if warning else 'Activity and the wound at home'
        caption = ('Pain, swelling, redness, drainage or fever' if warning
                   else 'A small bruise or mild tenderness can occur')
        angiogram.header(canvas, title, 'RECOVERY AFTER PCI')
        recovery_art.tag(canvas, caption)
    elif elapsed < 17.65:
        document_scene(canvas, 'Contact your care team promptly', 'New or increasing symptoms',
                       ('Tell your care team what', 'has changed at the wound'),
                       ('Contact your team', ('Pain or swelling', 'Redness or drainage', 'Fever')), (elapsed - 14) / 3.65)
    else:
        document_scene(canvas, 'Activity and the wound at home', 'Return to activity varies',
                       ('Your recovery and the', 'reason for PCI matter'),
                       ('Recovery plan', ('What to do now', 'When to ask for help', 'Your next check')), (elapsed - 17.65) / 5.85)


def rehabilitation(canvas, progress, elapsed):
    access.rect(canvas, 0, 0, 1280, 720, access.solid('#e3f1e6'))
    angiogram.block(canvas, 540, 176, 704, 446, 26, access.solid('#285e53'))
    canvas.save()
    canvas.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(540, 176, 704, 446), 26, 26), doAntiAlias=True)
    for index in range(7):
        x = 520 + ((index * 135 - 160 * progress) % 850)
        access.line(canvas, [(x, 180), (x, 623)], '#a7cebc', 12, 122)
    access.rect(canvas, 540, 515, 704, 110, access.solid('#1b493f'))
    for index in range(9):
        x = 510 + ((index * 89 - 265 * progress) % 800)
        access.line(canvas, [(x, 591), (x + 47, 591)], '#a3d2b8', 9)
    x = 670 + 397 * progress
    gait = 52 * sin(elapsed * 2 * pi * .8)
    angiogram.dot(canvas, x, 261, 30, '#d1e9d8')
    for side, color in ((-1, '#8cbfb0'), (1, '#d1e9d8')):
        access.line(canvas, [(x, 420), (x + side * gait * .7, 485), (x + side * gait, 545)], color, 27)
        access.line(canvas, [(x, 326), (x - side * gait * .7, 371), (x - side * gait, 405)], color, 22)
    angiogram.block(canvas, x - 47, 300, 94, 145, 37, access.solid('#d4eada'))
    canvas.restore()
    angiogram.header(canvas, 'Rehabilitation and follow-up', 'RECOVERY AFTER PCI')
    access.text(canvas, 'Cardiac rehabilitation', 55, 320, 38, '#164c3f')
    access.text(canvas, 'Supervised exercise,', 55, 376, 31, '#2b5a4e', access.REGULAR)
    access.text(canvas, 'education and support', 55, 419, 31, '#2b5a4e', access.REGULAR)
    access.text(canvas, 'Ask how to join if it is recommended', 55, 674, 29, '#276353')


def follow_up(canvas, elapsed):
    if elapsed < 5.37:
        restenosis.lumen_view(canvas, elapsed, 'open')
        angiogram.header(canvas, 'Rehabilitation and follow-up', 'RECOVERY AFTER PCI')
        access.text(canvas, 'The treated segment is one part of coronary disease', 55, 674, 30, '#265d4e')
    elif elapsed < 11.98:
        document_scene(canvas, 'Rehabilitation and follow-up', 'The follow-up visit',
                       ('Discuss symptoms and', 'the prevention plan'),
                       ('Follow-up visit', ('Symptoms', 'Medicines', 'Prevention plan')), (elapsed - 5.37) / 6.61)
    else:
        rehabilitation(canvas, (elapsed - 11.98) / 9.52, elapsed - 11.98)


def take_home(canvas, elapsed):
    if elapsed < 4.91:
        document_scene(canvas, 'What to take home', 'The treatment result',
                       ('Ask what was treated', 'and what it means'),
                       ('Treatment result', ('What was treated', 'The result', 'Next steps')), elapsed / 4.91)
    elif elapsed < 9.33:
        document_scene(canvas, 'What to take home', 'The written recovery plan',
                       ('Know what to take and', 'whom to contact'),
                       ('Your plan', ('Medicines', 'Recovery', 'Contact details')), (elapsed - 4.91) / 4.42)
    else:
        document_scene(canvas, 'What to take home', 'Keep your own plan',
                       ('Planned and emergency PCI', 'can lead to different advice'),
                       ('Keep this plan', ('Your instructions', 'Follow-up', 'Who to contact')), (elapsed - 9.33) / 8.47)


SCENES = {
    'P03': ('medicine-plan-checked', medicine_plan),
    'P04': ('medicine-change', before_medicine_change),
    'P05': ('home-recovery', home_recovery),
    'P07': ('rehabilitation', follow_up),
    'P08': ('take-home', take_home),
    'P09': ('closing-credits', None),
}


def draw(canvas, ident, p, elapsed):
    animation = SCENES[ident][1]
    if animation is not None:
        animation(canvas, elapsed)
    else:
        closing_credits(canvas)


def render(folder, selected):
    if os.name == 'nt':
        import ctypes

        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise ctypes.WinError()

    folder.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((SERIES / 'episode-10' / 'timeline.json').read_text(encoding='utf-8-sig'))
    report = folder / 'source-evidence.json'
    evidence = json.loads(report.read_text(encoding='utf-8-sig')) if report.is_file() else {}
    for scene in timeline['scenes']:
        ident = scene['id']
        if ident not in selected:
            continue
        frames = scene['end_frame'] - scene['start_frame']
        target = folder / f'{ident}-{SCENES[ident][0]}-alternate.mp4'
        temporary = target.with_suffix('.part.mp4')
        if not target.exists():
            print(f'Rendering {ident}, {frames} frames', flush=True)
            encode_scene(temporary, frames, lambda canvas, index: draw(canvas, ident, 0, index / FPS),
                         preset='veryfast', threads=1)
            temporary.replace(target)
        result = invoke(str(LEGACY_FFMPEG), '-v', 'info', '-xerror', '-threads', 1, '-i', target,
                        '-map', '0:v:0', '-an', '-vf', 'freezedetect=n=0.001:d=2', '-f', 'null', '-')
        motion = freeze_report(result.stderr.decode('utf-8', 'replace'), frames / FPS)
        evidence[ident] = {'path': target.name, 'sha256': file_hash(target), 'frames': frames,
                           'duration_seconds': frames / FPS, 'full_decode': True, 'freeze': motion}
        print(f'{ident}: {motion["total_seconds"]:.3f}s measured holds', flush=True)
        report.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--scenes', nargs='+', choices=tuple(SCENES), default=tuple(SCENES))
    args = parser.parse_args()
    render(args.folder, args.scenes)
