"""Draw cardiac surgery YouTube thumbnails from the original episode art."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw
import skia

from . import cabg_graft as graft, cabg_icu, cabg_routes
from .finish import logo, title


def opener(canvas):
    canvas.translate(-250, -80)
    canvas.scale(1.03, 1.03)
    graft.studio_light(canvas)
    graft.draw_anatomy(canvas)
    graft.vessel(canvas, graft.FREE_GRAFT, 19, graft.GRAFT)
    path = graft.AORTA[5:17] + graft.FREE_GRAFT[1:] + graft.LAD[graft.GRAFT_INDEX + 1:]
    graft.graft_pulses(canvas, path, 1.15)


def graft_detail(canvas):
    canvas.translate(-243, -167)
    graft.studio_light(canvas)
    route = cabg_routes.CUT_GRAFT_FLOW
    crossing = graft.distances(route)[len(cabg_routes.CUT_GRAFT) - 1]
    cabg_routes.distal_join(canvas, crossing / 234, labels=False, branch=False, marker_offset=0)


def intensive_care(canvas):
    canvas.translate(-25, 18)
    canvas.scale(.70, .70)
    cabg_icu.bedside(canvas, .65, awake=True, with_staff=True, breathing_focus=True)


def draw_cover(output, episode=1):
    treatments = {
        1: (opener, ('Why choose', 'bypass?'), 82),
        2: (graft_detail, ('How bypass', 'works'), 82),
        3: (intensive_care, ('After bypass', 'surgery'), 76),
    }
    draw, headings, font_size = treatments[episode]
    surface = skia.Surface(1280, 720)
    draw(surface.getCanvas())
    plate = Image.fromarray(surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType))

    cover = Image.new('RGBA', (1280, 720), '#102b29')
    cover.alpha_composite(plate.crop((0, 0, 740, 590)), (540, 69))
    cover.alpha_composite(logo(77), (62, 55))
    pen = ImageDraw.Draw(cover)
    title(pen, 'Elysian Biomedical LLP', (157, 76), 33, '#e4f3eb', 455)
    for index, heading in enumerate(headings):
        title(pen, heading, (57, 208 + 103 * index), font_size, '#f5fff7', 470)
    title(pen, 'CARDIAC SURGERY EDUCATION', (63, 585), 29, '#a0d3be', 493)
    cover.convert('RGB').save(output, quality=96, subsampling=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--episode', type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    draw_cover(args.output, args.episode)
