"""Render the clinical visuals for scenes P04 through P12."""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import cos, sin, tau
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent
EPISODE = OUT.parents[1]
PRIOR = EPISODE.parent / "episode-01" / "revision"
sys.dont_write_bytecode = True
for path in (
    EPISODE / "prototype",
    PRIOR / "shared-coronary-scenes",
    PRIOR / "radial-route-scenes",
    PRIOR / "femoral-route-scenes",
):
    sys.path.insert(0, str(path))

import render_stent_prototype as art
import render_shared_coronary as coronary
import render_radial_scenes as radial
import render_recovery as femoral


W, H, FPS = art.W, art.H, 24
FFMPEG = str(art.FFMPEG)
SCENES = {
    "P04": (21, "The guide catheter"),
    "P05": (20, "Crossing the narrowing"),
    "P06": (20, "Preparing the narrowing"),
    "P07": (16, "Keeping the wire in place"),
    "P08": (21, "How the stent arrives"),
    "P09": (19, "Expanding the stent"),
    "P10": (19, "The medicine coating"),
    "P11": (21, "Checking the result"),
    "P12": (18, "Removing the equipment"),
}
PARKED_WIRE = 1325
PREPARATION = .67
RECOIL = .52
GREEN, INK, MUTED = art.GREEN, art.INK, art.MUTED
font, stroke, center = art.font, art.stroke, art.center
smooth, trace, curve = art.smooth, coronary.trace, coronary.curve
LAD = coronary.LAD


def ease(progress, start, end):
    return smooth((progress-start)/(end-start))


@lru_cache(maxsize=9)
def plate(scene):
    original = art.background()
    image = original.copy()
    clean = original.crop((0, 235, W, 249)).resize((W, 104), Image.Resampling.BILINEAR)
    image.paste(clean, (0, 136))
    draw = ImageDraw.Draw(image)
    draw.text((76, 151), SCENES[scene][1], font=font(58, "heading"), fill=INK)
    return image


def cutaway(scene, expansion):
    image = art.arterial_layer(round(expansion*30)).copy()
    image.paste(plate(scene).crop((0, 0, W, 256)), (0, 0))
    return image


def panel(draw, box):
    draw.rounded_rectangle(box, 18, fill="#f4f9f2", outline="#bdd4c5", width=2)


def footer(image, heading, detail):
    draw = ImageDraw.Draw(image)
    draw.text((77, 749), heading, font=font(33, "semibold"), fill=GREEN)
    draw.text((77, 804), detail, font=font(24), fill=MUTED)
    stroke(draw, ((77, 863), (1521, 863)), "#a4bfae", 2)
    return image


def tag(draw, xy, words):
    coronary.tag(draw, xy, words)


def route_map(progress):
    image = radial.map_base().copy()
    route = trace(radial.ROUTE.points, progress)
    draw = ImageDraw.Draw(image)
    stroke(draw, route, "#28615b", 9)
    stroke(draw, route, "#8fcebf", 5)
    if len(route) > 1:
        x, y = route[-1]
        draw.ellipse((x-5, y-5, x+5, y+5), fill="#edf8e6", outline="#34705d")
    x, y = radial.ROUTE.at(0)
    draw.line((x-9, y+17, x+6, y-18), fill="#245e55", width=10)
    draw.line((x-9, y+17, x+6, y-18), fill="#98cbbb", width=5)
    return image.crop((76, 243, 779, 792))


def guide_scene(p):
    image = plate("P04").copy()
    draw = ImageDraw.Draw(image)
    panel(draw, (77, 257, 735, 711))
    panel(draw, (758, 257, 1522, 711))
    route = route_map(ease(p, .08, .62)).resize((563, 439), Image.Resampling.LANCZOS)
    image.paste(route, (102, 270))
    root_image = coronary.root_base("reach-left-opening").copy()
    root_draw = ImageDraw.Draw(root_image)
    movement = ease(p, .59, .84)
    neutral = coronary.mix(coronary.NEUTRAL_TIP, coronary.LEFT_ENTRY, movement)
    guide = trace(coronary.tool_path(neutral), ease(p, .50, .68))
    coronary.root_tools(root_draw, guide, ())
    root = root_image.crop((776, 258, 1556, 729)).resize((706, 449), Image.Resampling.LANCZOS)
    image.paste(root, (784, 260))
    draw = ImageDraw.Draw(image)
    tag(draw, (102, 278), "Right wrist access")
    tag(draw, (798, 274), "Aortic root and coronary openings")
    tag(draw, (104, 618), "Sheath stays at the wrist")
    return footer(image, "Guide catheter at the coronary opening",
                  "The wrist is shown here. The team can also use an artery at the groin.")


@lru_cache(maxsize=1)
def heart_locator():
    image = plate("P05").copy()
    draw = ImageDraw.Draw(image)
    panel(draw, (77, 257, 1522, 711))
    xy, transform, _, _, ostium = coronary.base_heart(draw, "left")
    target = xy(LAD[31])
    art.leader(draw, "Guide catheter", (552, 400), ostium)
    art.leader(draw, "Focal narrowing in the LAD", (548, 547), target)
    draw.text((902, 429), "Left anterior descending artery", font=font(30, "semibold"), fill=GREEN)
    draw.text((902, 482), "The close-up follows this artery.", font=font(24), fill=MUTED)
    return image, transform


def draw_delivery(image, x, radius, wire_tip, mesh_x=None, mesh_radius=12, show_balloon=True):
    pen = ImageDraw.Draw(image)
    if mesh_x is not None:
        art.stent(pen, mesh_x, mesh_radius, False)
    if show_balloon:
        art.balloon(image, x, radius)
    art.guidewire(pen, wire_tip)
    if mesh_x is not None:
        art.stent(pen, mesh_x, mesh_radius, True)


def cross_scene(p):
    if p < .19:
        base, transform = heart_locator()
        image = base.copy()
        pen = ImageDraw.Draw(image)
        guide_root = curve((303, 145), ((301, 180), (301, 193), (307, 209)),
                           ((310, 217), (321, 220), coronary.LEFT_MAIN[0]))
        wire = guide_root+coronary.LEFT_MAIN[1:]+LAD[1:22]
        stroke(pen, transform(trace(wire, ease(p, .03, .19))), "#f3d49c", 3)
        return footer(image, "The wire enters through the guide catheter",
                      "The guide catheter rests at the opening of the coronary artery.")
    image = cutaway("P05", 0)
    tip = art.MIN_X + (PARKED_WIRE-art.MIN_X)*ease(p, .18, .57)
    pen = ImageDraw.Draw(image)
    art.guidewire(pen, tip)
    art.leader(pen, "Plaque", (1015, 342), (art.TARGET+40, center(art.TARGET+40)-43))
    if p > .39:
        art.leader(pen, "Soft wire tip", (1077, 639), (tip-5, center(tip-5)-9))
    return footer(image, "Coronary guidewire crosses the narrowing",
                  "The wire stays in the same artery and reaches beyond the treated spot.")


def flow(draw, phase, visible, *, blocked=False):
    if visible < .12:
        return
    color = art.blend((136, 66, 73), (226, 139, 122), visible)
    for offset in range(10):
        x = 168+(offset*132+phase*150)%1260
        if blocked and abs(x-art.TARGET) < art.BALLOON_HALF+18:
            continue
        y = center(x)+18
        stroke(draw, ((x-14, y), (x+10, y), (x+5, y-4)), color, 2)


def prep_scene(p):
    amount = ease(p, .40, .72)
    at = art.MIN_X-art.BALLOON_HALF+(art.TARGET-art.MIN_X+art.BALLOON_HALF)*ease(p, .05, .39)
    image = cutaway("P06", PREPARATION*amount)
    draw_delivery(image, at, 8+44*amount, PARKED_WIRE)
    pen = ImageDraw.Draw(image)
    flow(pen, p*2.4, 1-ease(p, .40, .68), blocked=amount > .12)
    tag(pen, (1093, 282), "Preparation balloon")
    if p >= .40:
        art.leader(pen, "Plaque stays in the wall", (1061, 340), (art.TARGET+65, center(art.TARGET+65)-62))
    return footer(image, "A separate balloon may prepare the artery",
                  "The folded balloon follows the wire, opens at the narrowing, and temporarily reduces flow.")


def prep_withdraw(p):
    deflated = ease(p, .06, .34)
    withdrawal = ease(p, .37, .70)
    expansion = PREPARATION+(RECOIL-PREPARATION)*deflated
    at = art.TARGET-(art.TARGET-art.MIN_X+art.BALLOON_HALF)*withdrawal
    image = cutaway("P07", expansion)
    draw_delivery(image, at, 52-44*deflated, PARKED_WIRE, show_balloon=withdrawal < 1)
    pen = ImageDraw.Draw(image)
    art.leader(pen, "Guidewire stays", (1080, 340), (1193, center(1193)))
    if p > .67:
        tag(pen, (1042, 282), "Preparation depends on the narrowing")
    return footer(image, "Balloon out · Guidewire stays",
                  "The preparation balloon deflates before it is pulled back over the stationary wire.")


def nested_delivery(p):
    image = cutaway("P08", RECOIL)
    advance = ease(p, .20, .73)
    at = art.MIN_X-art.BALLOON_HALF+(art.TARGET-art.MIN_X+art.BALLOON_HALF)*advance
    draw_delivery(image, at, 9, PARKED_WIRE, at)
    pen = ImageDraw.Draw(image)
    if p < .33:
        pen.rounded_rectangle((929, 275, 1497, 407), 14, fill="#ecf6ea", outline="#a8c8b5", width=2)
        pen.text((948, 289), "Enlarged side-on detail", font=font(20, "semibold"), fill=GREEN)
        pen.rounded_rectangle((1001, 338, 1200, 381), 12, fill="#6cb4ac", outline="#357b71", width=2)
        pen.line((948, 359, 1230, 359), fill="#d6a76e", width=5)
        for x in range(1010, 1200, 23):
            stroke(pen, ((x, 336), (x+11, 345), (x, 354), (x+11, 365), (x, 383)), "#53666c", 3)
        for y, color, caption in ((321, "#53666c", "Collapsed mesh"), (345, "#6cb4ac", "Folded balloon and shaft"),
                                  (369, "#d6a76e", "Guidewire through shaft")):
            pen.rectangle((1241, y+2, 1251, y+12), fill=color)
            pen.text((1261, y), caption, font=font(17, "semibold"), fill=INK)
    elif advance > .70:
        art.leader(pen, "Stent and delivery balloon", (1042, 340), (at+108, center(at+108)-9))
    return footer(image, "Stent mounted on its delivery balloon",
                  "The folded assembly moves together over the wire and stops across the narrowing.")


def deploy_scene(p):
    inflate = ease(p, .06, .34)
    deflate = ease(p, .43, .65)
    withdraw = ease(p, .68, .89)
    expansion = RECOIL+(1-RECOIL)*inflate
    radius = 9+64*inflate*(1-deflate)
    position = art.TARGET-(art.TARGET-art.MIN_X+art.BALLOON_HALF)*withdraw
    image = cutaway("P09", expansion)
    draw_delivery(image, position, radius, PARKED_WIRE, art.TARGET, 12+64*inflate,
                  show_balloon=withdraw < 1)
    pen = ImageDraw.Draw(image)
    if deflate > .05:
        art.leader(pen, "Stent stays in place", (1052, 340), (art.TARGET+97, center(art.TARGET+97)-69))
    else:
        art.leader(pen, "Balloon expands the mesh", (1035, 340), (art.TARGET+110, center(art.TARGET+110)-12-57*inflate))
    if p < .40:
        return footer(image, "The balloon opens the mesh against the artery wall",
                      "The expanding stent supports a wider passage at the treated spot.")
    if p < .68:
        return footer(image, "The balloon deflates in place",
                      "The mesh stays expanded against the artery wall while the balloon folds down.")
    return footer(image, "Balloon out · Stent stays",
                  "The balloon deflates before it moves. The guidewire remains across the treated segment.")


def coating_scene(p):
    image = plate("P10").copy()
    pen = ImageDraw.Draw(image)
    panel(pen, (76, 257, 755, 712))
    panel(pen, (775, 257, 1522, 712))
    scaffold = art.arterial_layer(30).copy()
    screen = ImageDraw.Draw(scaffold)
    art.stent(screen, art.TARGET, 76, False)
    art.stent(screen, art.TARGET, 76, True)
    crop = scaffold.crop((410, 353, 1277, 630))
    image.paste(crop.resize((631, 201), Image.Resampling.LANCZOS), (101, 383))
    pen = ImageDraw.Draw(image)
    tag(pen, (99, 279), "Stent in the artery")
    tag(pen, (797, 279), "Enlarged stent strut")
    pen.rounded_rectangle((815, 508, 1477, 627), 21, fill="#b06a68")
    pen.rounded_rectangle((815, 510, 1477, 537), 12, fill="#d69182")
    pen.rounded_rectangle((1051, 447, 1223, 523), 20, fill="#70b7a5", outline="#4c8d7d", width=2)
    pen.rounded_rectangle((1060, 456, 1214, 511), 14, fill="#b5c6c2", outline="#4e686a", width=3)
    pen.line((1082, 468, 1189, 468), fill="#e6eee1", width=4)
    release = ease(p, .19, .69)
    for row, count in enumerate((8, 7, 5)):
        for index in range(count):
            x = 1018+index*32+row*11
            y = 528+row*16
            threshold = .19+row*.19+index*.039
            if release >= threshold:
                radius = 3 if row < 2 else 2
                pen.ellipse((x-radius, y-radius, x+radius, y+radius), fill="#9dd3ba")
    art.leader(pen, "Medicine coating", (1248, 395), (1222, 477))
    pen.ellipse((839, 652, 850, 663), fill="#74b29b")
    pen.text((864, 643), "Conceptual view of medicine release into nearby tissue", font=font(21), fill=MUTED)
    return footer(image, "Drug-eluting stent",
                  "The coating gradually releases medicine that helps reduce tissue growth around the stent.")


@lru_cache(maxsize=1)
def final_base():
    image = plate("P11").copy()
    before = coronary.gray_vessels("left", 1, angle=-16, narrow=True, callout=True)
    image.paste(before, (88, 283))
    pen = ImageDraw.Draw(image)
    tag(pen, (103, 300), "Before treatment")
    return image


def final_check(p):
    image = final_base().copy()
    contrasted = ease(p, .07, .45)
    after = coronary.gray_vessels("left", contrasted, angle=-16, narrow=False)
    image.paste(after, (821, 283))
    pen = ImageDraw.Draw(image)
    tag(pen, (836, 300), "After treatment")
    if p > .40:
        x, y = coronary.project(coronary.ANGIO_LEFT[1][0][round((len(coronary.ANGIO_LEFT[1][0])-1)*.47)], -16)
        x, y = 821+106+x*2.07, 283+7+y*1.35
        pen.ellipse((x-22, y-22, x+22, y+22), outline="#ffce8e", width=3)
    if p > .72:
        pen.rounded_rectangle((1256, 294, 1494, 465), 14, fill="#24383b", outline="#7d9c91", width=2)
        pen.text((1272, 306), "Internal imaging illustration", font=font(17, "semibold"), fill="#e4f0e5")
        center_x, center_y = 1375, 391
        for radius, color in ((62, "#919396"), (52, "#626669"), (45, "#23282b")):
            pen.ellipse((center_x-radius, center_y-radius, center_x+radius, center_y+radius), fill=color)
        for i in range(10):
            angle = i*tau/10
            x, y = center_x+44*cos(angle), center_y+44*sin(angle)
            pen.ellipse((x-3, y-3, x+3, y+3), fill="#eff2e8")
        pen.ellipse((1367, 383, 1383, 399), fill="#9ea1a0")
    return footer(image, "Final contrast check",
                  "The same simulated view shows a wider channel here. Internal imaging can also check stent expansion.")


@lru_cache(maxsize=1)
def recovery_heart():
    image = plate("P12").copy()
    pen = ImageDraw.Draw(image)
    panel(pen, (77, 256, 1522, 710))
    xy, _, _, _, _ = coronary.base_heart(pen, "left", show_catheter=False)
    xx, yy = xy(LAD[31])
    location = tuple(xy(point) for point in LAD[26:37])
    stroke(pen, location, "#e7ded2", 10)
    stroke(pen, location, "#7c8e88", 5)
    art.leader(pen, "Stent stays in the heart", (503, 579), (xx, yy))
    return image, (xx, yy)


def removal_scene(p):
    base, _ = recovery_heart()
    image = base.copy()
    pen = ImageDraw.Draw(image)
    if p < .47:
        root_image = coronary.root_base("reach-left-opening").copy()
        root_draw = ImageDraw.Draw(root_image)
        wire = coronary.tool_path(coronary.LEFT_ENTRY)
        catheter = coronary.tool_path(coronary.LEFT_ENTRY)
        wire = trace(wire, 1-ease(p, .03, .22))
        catheter = trace(catheter, 1-ease(p, .20, .45))
        coronary.root_tools(root_draw, catheter, wire)
        crop = root_image.crop((778, 269, 1556, 727))
        image.paste(crop.resize((704, 439), Image.Resampling.LANCZOS), (792, 267))
        return footer(image, "Guidewire and guide catheter come out",
                      "The expanded stent remains fixed at the treated spot.")
    progress = ease(p, .49, .81)
    wrist = radial.closure_frame(5.35*progress).crop((74, 330, 1519, 723))
    groin = femoral.closure_frame("remove", progress).crop((82, 265, 1515, 697))
    image.paste(wrist.resize((703, 192), Image.Resampling.LANCZOS), (791, 307))
    image.paste(groin.resize((703, 205), Image.Resampling.LANCZOS), (791, 506))
    pen = ImageDraw.Draw(image)
    tag(pen, (802, 265), "Wrist pressure band")
    tag(pen, (802, 472), "Groin pressure example")
    return footer(image, "Wrist pressure band · Groin closure",
                  "After sheath removal, staff control bleeding with pressure or a closure device, as appropriate.")


FRAMES = dict(zip(SCENES, (guide_scene, cross_scene, prep_scene, prep_withdraw, nested_delivery,
                           deploy_scene, coating_scene, final_check, removal_scene)))


def encode(scene):
    duration, _ = SCENES[scene]
    count = duration*FPS
    target = OUT / f"{scene}.mp4"
    command = [
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
        "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
        "-threads", "2", "-preset", "ultrafast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(target),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    previous = -1
    try:
        with process.stdin as pipe:
            for index in range(count):
                key = round(240*index/(count-1))
                if key != previous:
                    raw = FRAMES[scene](key/240).tobytes()
                    previous = key
                pipe.write(raw)
    finally:
        code = process.wait()
        if code:
            raise RuntimeError(f"{scene} encoding failed with status {code}")
    subprocess.run([FFMPEG, "-v", "error", "-xerror", "-threads", "2", "-i", str(target),
                    "-f", "null", "-"], check=True)
    print(f"{scene}.mp4, {duration}s, 1920x1080, silent, full decode passed", flush=True)


def contact_sheet():
    samples = {
        "P04": .87, "P05": .75, "P06": .83, "P07": .82, "P08": .83,
        "P09": .52, "P10": .83, "P11": .82, "P12": .91,
    }
    width, height = 480, 270
    result = Image.new("RGB", (1480, 894), "#dcebe1")
    pen = ImageDraw.Draw(result)
    for index, (scene, point) in enumerate(samples.items()):
        x, y = 10+(index%3)*490, 8+(index//3)*294
        raw = subprocess.run(
            [FFMPEG, "-v", "error", "-ss", str(point*SCENES[scene][0]), "-i", str(OUT/f"{scene}.mp4"),
             "-frames:v", "1", "-vf", f"scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            check=True, capture_output=True,
        ).stdout
        result.paste(Image.frombytes("RGB", (width, height), raw), (x, y))
        pen.text((x+6, y+273), f"{scene} · {SCENES[scene][1]}", font=font(15), fill=MUTED)
    result.save(OUT/"clinical-decoded-contact-sheet.jpg", quality=94)


if __name__ == "__main__":
    jobs = sys.argv[1:] or list(SCENES)
    for scene in jobs:
        FRAMES[scene](.05)
        FRAMES[scene](.85)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(encode, jobs))
    if all((OUT/f"{scene}.mp4").is_file() for scene in SCENES):
        contact_sheet()
