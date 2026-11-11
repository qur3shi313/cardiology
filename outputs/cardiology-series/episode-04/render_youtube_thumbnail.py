"""Draw the original 1280×720 TAVI thumbnail at twice delivery resolution."""

from math import cos, pi, sin, sqrt
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FONTS = ROOT / 'outputs/website-v2/elysian-corporate/assets/fonts'
WIDTH, HEIGHT, SS = 1280, 720, 2
TILT = pi / 4.8
SCALE, CX, CY = 187, 940, 397
TAU = 2 * pi


def clamp(value, lo=0, hi=1):
    return max(lo, min(value, hi))


def blend(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def coord(x, y):
    return round(x * SS), round(y * SS)


def view(point):
    x, y, z = point
    depth = y * cos(TILT) + z * sin(TILT)
    vertical = z * cos(TILT) - y * sin(TILT)
    perspective = 1 + .075 * depth
    return coord(CX + SCALE * x * perspective, CY - SCALE * vertical * perspective), depth


def font(name, size):
    file = {'title': 'josefin-sans-variable.ttf', 'text': 'fira-sans-semibold.ttf'}[name]
    selected = ImageFont.truetype(str(FONTS / file), size * SS)
    if name == 'title':
        selected.set_variation_by_axes([690])
    return selected


def backdrop():
    y, x = np.ogrid[:HEIGHT * SS, :WIDTH * SS]
    x = x / SS
    y = y / SS
    cool = np.exp(-(((x - 1210) / 610) ** 2 + ((y - 625) / 450) ** 2))
    pink = np.exp(-(((x - 865) / 390) ** 2 + ((y - 210) / 300) ** 2))
    glint = np.exp(-(((x - 1100) / 265) ** 2 + ((y - 150) / 260) ** 2))
    rgb = []
    for base, drop, warm, shine in zip((250, 252, 248), (31, 18, 20), (2, -14, -11), (9, 8, 8)):
        rgb.append(np.clip(base - drop * cool + warm * pink + shine * glint, 0, 255))
    return Image.fromarray(np.uint8(np.stack(rgb, axis=2)), 'RGB')


def radius(z):
    return .93 + .10 * ((z + .76) / 1.58) + .045 * cos(z * 4)


def cylinder(theta, z, offset=0):
    r = radius(z) + offset
    return r * cos(theta), r * sin(theta), z


def metal_segments():
    rows = [-.77, -.44, -.10, .24, .58, .84]
    count = 26
    step = TAU / count
    for k, (low, high) in enumerate(zip(rows, rows[1:])):
        shift = (k % 2) * step / 2
        for i in range(count):
            theta = i * step + shift
            a = cylinder(theta, low)
            for side in (-1, 1):
                b = cylinder(theta + side * step / 2, high)
                yield a, b, theta + side * step / 4
    for z in (rows[0], rows[-1]):
        for i in range(130):
            theta = i * TAU / 130
            yield cylinder(theta, z), cylinder(theta + TAU / 130, z), theta


def draw_frame(draw, front):
    segments = []
    for a, b, theta in metal_segments():
        va, da = view(a)
        vb, db = view(b)
        if (sin(theta) >= 0) != front:
            continue
        segments.append(((da + db) * .5, va, vb, theta))
    for depth, a, b, theta in sorted(segments):
        gloss = clamp(.58 + .36 * cos(theta - 2.15) + .12 * cos(theta * 3.0))
        edge = blend((49, 66, 72), (154, 169, 173), gloss)
        steel = blend((96, 118, 123), (244, 246, 239), gloss)
        highlight = blend((139, 160, 162), (252, 252, 245), gloss)
        width = round((3.2 if front else 2.5) * SS + .75 * depth)
        draw.line((a, b), fill=edge, width=width + 2)
        draw.line((a, b), fill=steel, width=width)
        if gloss > .47:
            draw.line(((a[0]-1, a[1]-1), (b[0]-1, b[1]-1)), fill=highlight, width=2)


def collar(draw, front):
    segments = 84
    for i in range(segments):
        theta = TAU * (i + .5) / segments
        if (sin(theta) >= 0) != front:
            continue
        a, b = i * TAU / segments, (i + 1) * TAU / segments
        points = [view(cylinder(angle, z, -.027))[0] for angle, z in ((a,-.73),(b,-.73),(b,-.22),(a,-.22))]
        light = clamp(.54 + .34 * cos(theta - 2.16))
        shade = blend((130, 130, 120), (226, 222, 203), light)
        draw.polygon(points, fill=shade)
        for z in (-.61, -.50, -.38):
            line = [view(cylinder(angle, z, -.026))[0] for angle in (a, b)]
            draw.line(line, fill=blend(shade, (246, 237, 211), .19), width=1)


def leaflet_point(theta, radial, mid):
    # The three free edges curve outward toward the commissures in this open view.
    shoulder = min(1, abs(theta - mid) / (pi / 3))
    inner = .49 + .44 * shoulder ** 2.6
    r = inner + (.987 - inner) * radial
    free_edge = .57 + .18 * shoulder ** 1.9
    attachment = .27 + .48 * shoulder ** 1.7
    z = free_edge + (attachment - free_edge) * radial - .17 * sin(pi * radial) * (1 - shoulder)
    return r * cos(theta), r * sin(theta), z


def leaflet_faces():
    count = 30
    for sector in range(3):
        mid = 1.37 + sector * TAU / 3
        left = mid - pi / 3
        for i in range(count):
            a, b = left + i * TAU / (3 * count), left + (i + 1) * TAU / (3 * count)
            theta = (a + b) / 2
            for j in range(27):
                u, v = j / 27, (j + 1) / 27
                points = [leaflet_point(angle, radial, mid) for angle, radial in ((a,u),(b,u),(b,v),(a,v))]
                projected = [view(p) for p in points]
                belly = sin(pi * (u + v) * .5)
                incidence = .59 + .22 * cos(theta - 2.1) + .11 * cos(theta * 2) - .20 * belly
                tissue = blend((152, 113, 94), (255, 237, 205), clamp(incidence + .22))
                grain = 1.5 * sin(i * 8.1 + j * 15.7 + sector * 2)
                shade = tuple(round(clamp(channel + grain, 0, 255)) for channel in tissue)
                yield sum(depth for _, depth in projected) / 4, [xy for xy, _ in projected], shade


def leaflets(draw):
    for _, vertices, shade in sorted(leaflet_faces(), key=lambda face: face[0]):
        draw.polygon(vertices, fill=shade)
    for sector in range(3):
        mid = 1.37 + sector * TAU / 3
        free = [view(leaflet_point(mid - pi/3 + i*TAU/96, 0, mid))[0] for i in range(33)]
        draw.line(free, fill='#9c7a65', width=4, joint='curve')
        draw.line([(x,y-2) for x,y in free], fill='#f7ddb8', width=2, joint='curve')


def scene():
    image = backdrop()
    shadow = Image.new('RGBA', image.size)
    shade = ImageDraw.Draw(shadow)
    shade.ellipse((*coord(732, 573), *coord(1165, 654)), fill=(44, 80, 76, 62))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24 * SS))
    image.paste(shadow, (0, 0), shadow)
    draw = ImageDraw.Draw(image)
    collar(draw, False)
    draw_frame(draw, False)
    leaflets(draw)
    collar(draw, True)
    draw_frame(draw, True)

    logo_size = 63 * SS
    logo = Image.open(ROOT / 'work/company-logo-original-686.jpg').convert('RGB')
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    mask = Image.new('L', (logo_size, logo_size))
    ImageDraw.Draw(mask).ellipse((0, 0, logo_size-1, logo_size-1), fill=255)
    image.paste(logo, coord(53, 48), mask)
    draw.text(coord(132, 70), 'Elysian Biomedical LLP', font=font('text', 27), fill='#004b3d', anchor='lt')
    draw.rounded_rectangle((*coord(58, 187), *coord(151, 194)), radius=4 * SS, fill='#00835b')
    draw.text(coord(53, 226), 'TAVI', font=font('title', 155), fill='#004b3d', anchor='lt')
    draw.text(coord(59, 389), 'A new aortic', font=font('title', 68), fill='#273933', anchor='lt')
    draw.text(coord(59, 468), 'valve', font=font('title', 68), fill='#273933', anchor='lt')
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


if __name__ == '__main__':
    output = HERE / 'tavi-youtube-thumbnail.png'
    scene().save(output, optimize=True)
    print(output)
