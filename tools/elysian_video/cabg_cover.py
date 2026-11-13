"""Draw the cardiac surgery opener's YouTube thumbnail from its graft art."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw
import skia

from . import cabg_graft as graft
from .finish import logo, title


def draw_cover(output):
    surface = skia.Surface(1280, 720)
    canvas = surface.getCanvas()
    canvas.translate(-250, -80)
    canvas.scale(1.03, 1.03)
    graft.studio_light(canvas)
    graft.draw_anatomy(canvas)
    graft.vessel(canvas, graft.FREE_GRAFT, 19, graft.GRAFT)
    path = graft.AORTA[5:17] + graft.FREE_GRAFT[1:] + graft.LAD[graft.GRAFT_INDEX + 1:]
    graft.graft_pulses(canvas, path, 1.15)
    plate = Image.fromarray(surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType))

    cover = Image.new('RGBA', (1280, 720), '#102b29')
    cover.alpha_composite(plate.crop((0, 0, 740, 590)), (540, 69))
    cover.alpha_composite(logo(77), (62, 55))
    pen = ImageDraw.Draw(cover)
    title(pen, 'Elysian Biomedical LLP', (157, 76), 33, '#e4f3eb', 455)
    title(pen, 'Why choose', (57, 208), 82, '#f5fff7', 470)
    title(pen, 'bypass?', (57, 311), 82, '#f5fff7', 470)
    title(pen, 'CARDIAC SURGERY EDUCATION', (63, 585), 29, '#a0d3be', 493)
    cover.convert('RGB').save(output, quality=96, subsampling=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    draw_cover(parser.parse_args().output)
