"""Render wrist versus groin access scenes P01, P02, P03 and P06."""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps


HERE = Path(__file__).resolve().parent
SERIES = HERE.parents[1]
EPISODE_ONE = SERIES / "episode-01"
REVISION = EPISODE_ONE / "revision"
sys.dont_write_bytecode = True
for directory in (
    EPISODE_ONE / "production",
    REVISION / "wrist-proof",
    REVISION / "femoral-route-scenes",
    REVISION / "shared-coronary-scenes",
    SERIES / "episode-02" / "prototype",
):
    sys.path.insert(0, str(directory))

import render_wrist_proof as wrist
import vascular_art as vessels
import render_route as femoral
import render_shared_coronary as coronary
import render_stent_prototype as stent


W, H, FPS = 1600, 900, 24
GREEN, INK, MUTED = wrist.GREEN, wrist.INK, wrist.MUTED
font, curve, trace = wrist.font, vessels.curve, vessels.trace
SCENES = {
    "P01": ("Wrist vs groin access", 15, 12.5),
    "P02": ("Two routes to the heart", 19, 6.6),
    "P03": ("An angiogram or a treatment", 19, 10.6),
    "P06": ("If the team changes route", 18, 15.1),
}
ROUTES = {"wrist": vessels.RADIAL, "groin": vessels.FEMORAL}
SITES = {"wrist": "Right wrist", "groin": "Right groin"}
ARTERIES = {"wrist": "Radial artery", "groin": "Common femoral artery"}
SHELL, CATHETER, CATHETER_LIGHT = "#28615b", "#77bcae", "#d9f0e3"
CUTAWAY = (122, 320, 1532, 711)
HEART = curve((288, 192), ((271, 170), (240, 181), (238, 204)),
              ((235, 242), (264, 254), (289, 272)),
              ((314, 293), (329, 301), (344, 286)),
              ((365, 267), (378, 233), (364, 211)),
              ((351, 190), (320, 179), (288, 192)))
FEMORAL_DISTAL = curve((222, 483), ((218, 497), (216, 507), (215, 515)),
                       ((214, 525), (212, 533), (210, 541)))
FEMORAL_BRANCH = curve((215, 515), ((225, 523), (230, 530), (232, 541)))


def ease(t, begin, end):
    return wrist.smooth((t-begin)/(end-begin))


def stroke(draw, path, color, width=1):
    if len(path) > 1:
        draw.line(path, fill=color, width=width, joint="curve")


def point(draw, xy, radius, fill, outline=None):
    x, y = xy
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill, outline=outline, width=2)


def card(draw, box):
    draw.rounded_rectangle(box, 20, fill="#f1f8f0", outline="#bfd5c6", width=2)


def badge(draw, xy, label, *, tint="#dfede3"):
    x, y = xy
    face = font(22, "semibold")
    draw.rounded_rectangle((x, y, x+draw.textlength(label, font=face)+29, y+39), 8, fill=tint)
    draw.text((x+14, y+7), label, font=face, fill=GREEN)


def leader(draw, label, xy, at):
    x, y = xy
    target_x, _ = at
    font_face = font(23, "semibold")
    right = x+draw.textlength(label, font=font_face)
    anchor = (right+10, y+15) if x < target_x else (x-10, y+15)
    elbow = (anchor[0]+(24 if anchor[0] < target_x else -24), y+15)
    stroke(draw, (anchor, elbow, at), "#507765", 2)
    point(draw, at, 4, "#f6ead7", "#507765")
    draw.text(xy, label, font=font_face, fill=GREEN)


@lru_cache(maxsize=4)
def chrome(scene):
    image = wrist.vertical_gradient((246, 251, 245), (219, 234, 225))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 57, 126, 107), 8, fill="white")
    logo = ImageOps.fit(Image.open(wrist.LOGO).convert("RGB"), (48, 48), method=Image.Resampling.LANCZOS)
    image.paste(logo, (77, 58))
    draw.text((144, 62), "Elysian Biomedical LLP", fill=GREEN, font=font(24, "semibold"))
    draw.text((144, 93), "Cardiology Education Series", fill=MUTED, font=font(18))
    draw.text((1521, 66), "EPISODE 05", fill=GREEN, font=font(20, "semibold"), anchor="rt")
    stroke(draw, ((76, 128), (1522, 128)), "#b3ccbf", 2)
    draw.text((76, 151), SCENES[scene][0], font=font(58, "heading"), fill=INK)
    return image


def footer(image, heading, detail):
    draw = ImageDraw.Draw(image)
    draw.text((76, 754), heading, font=font(34, "semibold"), fill=GREEN)
    draw.text((76, 806), detail, font=font(25), fill=MUTED)
    stroke(draw, ((77, 866), (1522, 866)), "#a4bfae", 2)
    return image


def map_at(x, point_value):
    px, py = point_value
    return x+73+px*.93, 288+py*.73


def map_points(x, path):
    return tuple(map_at(x, p) for p in path)


@lru_cache(maxsize=4)
def comparison_base(scene):
    image = chrome(scene).copy()
    draw = ImageDraw.Draw(image)
    for x, route in ((76, "wrist"), (819, "groin")):
        card(draw, (x, 248, x+703, 724))
        outline = map_points(x, vessels.BODY)
        draw.polygon(tuple((a+5, b+6) for a, b in outline), fill="#dbe9de")
        draw.polygon(outline, fill="#e6bbaa")
        stroke(draw, outline, "#bd8e80", 2)
        heart = map_points(x, HEART)
        draw.polygon(heart, fill="#ba7477")
        stroke(draw, heart, "#a7646b", 2)
        for path in (vessels.RADIAL, vessels.FEMORAL, vessels.BODY_LEFT_SUBCLAVIAN,
                     *vessels.BODY_CAROTIDS, vessels.BODY_OTHER_ILIAC, FEMORAL_DISTAL, FEMORAL_BRANCH):
            stroke(draw, map_points(x, path), "#bc827e", 6)
        stroke(draw, map_points(x, ROUTES[route]), "#8e4e57", 10)
        stroke(draw, map_points(x, ROUTES[route]), "#c97a75", 7)
        badge(draw, (x+22, 269), SITES[route])
        draw.text((x+24, 677), "Patient’s right", font=font(20, "semibold"), fill=GREEN)
        leader(draw, "Aortic root", (x+492, 403), map_at(x, ROUTES[route][-1]))
    return image


def comparison(scene, progress):
    image = comparison_base(scene).copy()
    draw = ImageDraw.Draw(image)
    for x, route in ((76, "wrist"), (819, "groin")):
        path = map_points(x, ROUTES[route])
        live = trace(path, progress)
        stroke(draw, live, SHELL, 6)
        stroke(draw, live, CATHETER_LIGHT, 3)
        point(draw, live[-1], 4, CATHETER_LIGHT, SHELL)
        point(draw, path[0], 8, None, "#338773")
        if progress >= .98:
            point(draw, path[-1], 10, None, "#367969")
    return image


def opening(t):
    image = comparison("P01", ease(t, 1.0, 9.6))
    return footer(image, "Two routes to the heart",
                  "A catheter can enter through an artery at the wrist or the groin.")


@lru_cache(maxsize=2)
def access_background(route):
    if route == "wrist":
        return wrist.background().convert("RGB")
    return femoral.proof.background().convert("RGB")


def cutaway(route, progress):
    image = access_background(route).copy()
    tools = Image.new("RGBA", (W, H))
    pen = ImageDraw.Draw(tools)
    if route == "wrist":
        wrist.assembly(tools, wrist.ASSEMBLY_NOSE, inner=False)
        end = -72 + (wrist.PATH.distance[-1]-44+72)*progress
        tube = wrist.tube
    else:
        femoral.proof.introducer(pen, femoral.WORKING, working=True)
        end = -72 + (femoral.CATH_TIP+72)*progress
        tube = femoral.tube
    if end > -70:
        start = end-1580
        tube(pen, start, end, 10, (31, 76, 69, 255), taper=11)
        tube(pen, start, end, 7.0, (119, 188, 174, 255), taper=9)
        tube(pen, start, end-2, 1.6, (219, 242, 228, 255), shift=-3)
    tools.paste((0, 0, 0, 0), (0, 0, W, 309))
    return Image.alpha_composite(image.convert("RGBA"), tools).convert("RGB").crop(CUTAWAY)


@lru_cache(maxsize=2)
def site_locator(route):
    source = access_background(route)
    return source.crop((1249, 158, 1519, 313)).resize((142, 81), Image.Resampling.LANCZOS)


def paired_cutaways(t):
    image = chrome("P02").copy()
    draw = ImageDraw.Draw(image)
    for x, route in ((76, "wrist"), (819, "groin")):
        card(draw, (x, 248, x+703, 724))
        badge(draw, (x+25, 271), SITES[route])
        image.paste(site_locator(route), (x+531, 270))
        frame = cutaway(route, ease(t, 2.4, 8.0)).resize((667, 185), Image.Resampling.LANCZOS)
        image.paste(frame, (x+18, 378))
        draw.text((x+25, 610), ARTERIES[route], font=font(31, "semibold"), fill=GREEN)
        description = "Palm up, on the thumb side" if route == "wrist" else "At the upper thigh, above the artery’s split"
        draw.text((x+25, 660), description, font=font(22), fill=MUTED)
    return footer(image, "The skin is numbed before access",
                  "The thin catheter travels inside the artery from the chosen access site.")


def routes(t):
    if t < 9.3:
        return paired_cutaways(t)
    if t < 16.1:
        image = comparison("P02", ease(t, 9.3, 14.3))
    else:
        image = chrome("P02").copy()
        pen = ImageDraw.Draw(image)
        card(pen, (76, 248, 719, 724))
        card(pen, (747, 248, 1522, 724))
        badge(pen, (101, 273), "The same destination")
        pen.text((103, 401), "Aortic root", font=font(44, "semibold"), fill=GREEN)
        pen.text((103, 468), "Reached from either access site", font=font(27), fill=MUTED)
        for y, route in ((530, "wrist"), (588, "groin")):
            point(pen, (116, y+14), 6, CATHETER, SHELL)
            pen.text((138, y), SITES[route], font=font(25, "semibold"), fill=GREEN)
        source = coronary.root_base("reach-left-opening").copy()
        coronary.root_tools(ImageDraw.Draw(source), coronary.tool_path(coronary.LEFT_ENTRY), ())
        crop = source.crop((777, 258, 1561, 729)).resize((730, 438), Image.Resampling.LANCZOS)
        image.paste(crop, (766, 266))
    return footer(image, "Both catheters reach the aortic root",
                  "The tip can sit at a coronary opening above the aortic valve.")


def diagnostic_and_treatment(t):
    if t < 6.6:
        image = chrome("P03").copy()
        draw = ImageDraw.Draw(image)
        card(draw, (76, 248, 1521, 724))
        badge(draw, (103, 273), "Diagnostic test")
        draw.text((104, 401), "Coronary angiogram", font=font(46, "semibold"), fill=GREEN)
        draw.text((105, 471), "Contrast outlines the arteries on X-ray.", font=font(27), fill=MUTED)
        draw.text((105, 520), "A narrowing changes the width of the channel.", font=font(25), fill=MUTED)
        film = coronary.gray_vessels("left", ease(t, .25, 2.1), angle=-16, narrow=True, callout=t >= 2.5)
        image.paste(film, (790, 290))
        badge(draw, (806, 306), "Simulated coronary X-ray")
        return footer(image, "An angiogram shows the arteries",
                      "The contrast image shows the narrowing and branches farther downstream.")
    if t < 14.2:
        image = chrome("P03").copy()
        draw = ImageDraw.Draw(image)
        card(draw, (76, 248, 1521, 724))
        p = ease(t, 8.3, 11.2)
        artery = stent.arterial_layer(round(20*p)).copy()
        x = stent.MIN_X-stent.BALLOON_HALF+(stent.TARGET-stent.MIN_X+stent.BALLOON_HALF)*ease(t, 6.7, 8.3)
        stent.balloon(artery, x, 8+46*p)
        stent.guidewire(ImageDraw.Draw(artery), 1325)
        image.paste(artery.crop((93, 340, 1505, 672)), (93, 351))
        badge(draw, (103, 270), "Catheter-based treatment")
        draw.text((108, 690), "Balloon angioplasty example", font=font(22, "semibold"), fill=GREEN)
        return footer(image, "PCI treats a narrowing",
                      "A balloon can widen one narrowed section. The team may also place a stent.")
    return footer(comparison("P03", 1), "Either route can be used",
                  "Wrist access is common for planned angiography when it is suitable.")


def access_single(route, progress, *, pause=False):
    image = chrome("P06").copy()
    draw = ImageDraw.Draw(image)
    card(draw, (76, 248, 1521, 725))
    badge(draw, (105, 273), SITES[route])
    image.paste(site_locator(route), (1335, 265))
    frame = cutaway(route, progress).resize((1374, 381), Image.Resampling.LANCZOS)
    image.paste(frame, (107, 325))
    if pause:
        badge(draw, (1093, 302), "Catheter pauses", tint="#f2ebd9")
        _, y = wrist.PATH.at(-72 + (wrist.PATH.distance[-1]+28)*progress)
        x, _ = wrist.PATH.at(-72 + (wrist.PATH.distance[-1]+28)*progress)
        point(draw, (107+(x-CUTAWAY[0])*1374/1410, 325+(y-CUTAWAY[1])*381/391),
              14, None, "#b88255")
    return image


@lru_cache(maxsize=1)
def bedside():
    image = chrome("P06").copy()
    draw = ImageDraw.Draw(image)
    card(draw, (76, 248, 1521, 724))
    badge(draw, (105, 271), "Bedside checks after the procedure")
    draw.ellipse((268, 642, 1385, 687), fill="#e1ece3")
    draw.rounded_rectangle((315, 545, 1376, 602), 14, fill="#c4d9d0", outline="#a0bfb1", width=2)
    draw.rounded_rectangle((313, 590, 1377, 609), 6, fill="#a6bfb8")
    for x in (381, 1308):
        draw.rounded_rectangle((x, 602, x+20, 671), 7, fill="#a6bfb8")
    draw.rounded_rectangle((357, 486, 546, 550), 13, fill="#e9eee0", outline="#c7d5c6", width=2)
    draw.ellipse((402, 458, 486, 532), fill="#c98b75", outline="#a57262", width=2)
    draw.arc((402, 457, 482, 515), 145, 300, fill="#694c4b", width=13)
    gown = curve((477, 527), ((488, 501), (521, 485), (553, 488)),
                 ((621, 483), (700, 500), (779, 522)),
                 ((824, 539), (888, 546), (951, 551)),
                 ((882, 572), (570, 565), (477, 551)),
                 ((468, 546), (469, 538), (477, 527)))
    draw.polygon(gown, fill="#7cb0a4")
    stroke(draw, gown, "#62968c", 2)
    leg = curve((802, 527), ((899, 513), (989, 521), (1050, 527)),
                ((1161, 532), (1195, 550), (1255, 549)),
                ((1280, 547), (1280, 519), (1291, 513)),
                ((1303, 508), (1307, 539), (1311, 554)),
                ((1297, 569), (1186, 565), (1134, 565)),
                ((1031, 565), (906, 569), (810, 554)))
    draw.polygon(leg, fill="#d7aaa0")
    stroke(draw, leg, "#b88273", 2)
    draw.polygon(((764, 514), (890, 511), (884, 566), (766, 567)), fill="#9ec4b4")
    draw.rounded_rectangle((855, 532, 893, 551), 5, fill="#f1ecdb", outline="#a8b9a8", width=2)
    draw.rounded_rectangle((552, 554, 797, 575), 6, fill="#d4e6da")
    arm = curve((548, 520), ((590, 525), (625, 545), (678, 549)),
                ((714, 549), (753, 540), (790, 546)),
                ((812, 552), (811, 563), (792, 567)),
                ((734, 569), (650, 568), (602, 558)),
                ((568, 551), (542, 542), (548, 520)))
    draw.polygon(arm, fill="#d49e88")
    stroke(draw, arm, "#b88576", 2)
    draw.rounded_rectangle((748, 544, 766, 567), 4, fill="#65ad9b", outline="#478e7e", width=2)
    draw.ellipse((658, 333, 716, 391), fill="#c49180", outline="#966c5f", width=2)
    draw.arc((659, 331, 715, 378), 181, 325, fill="#514548", width=10)
    draw.rounded_rectangle((632, 389, 734, 488), 22, fill="#74aa9a", outline="#55887e", width=2)
    draw.line(((654, 409), (688, 468), (750, 535)), fill="#7ab2a3", width=23, joint="curve")
    draw.ellipse((739, 526, 766, 547), fill="#bfdfce", outline="#77a797", width=2)
    draw.line(((714, 411), (798, 463), (867, 526)), fill="#82b6a6", width=23, joint="curve")
    draw.ellipse((853, 517, 880, 538), fill="#bfdfce", outline="#77a797", width=2)
    leader(draw, "Wrist site", (446, 623), (756, 552))
    leader(draw, "Groin site", (1047, 447), (875, 540))
    return image


def route_change(t):
    if t < 6.5:
        motion = .72*ease(t, .45, 3.35)
        image = access_single("wrist", motion, pause=t >= 3.35)
        return footer(image, "The team pauses at the first site",
                      "A tight wrist artery or a difficult path can prompt a change.")
    if t < 11.7:
        image = access_single("groin", .84*ease(t, 6.7, 10.5))
        return footer(image, "The team may change access sites",
                      "In this example, the team switches to the groin. The other wrist is another possible option.")
    image = bedside().copy()
    draw = ImageDraw.Draw(image)
    if t < 14.6:
        point(draw, (756, 552), 15, None, "#529686")
    else:
        point(draw, (875, 540), 15, None, "#529686")
    return footer(image, "Staff check both sites if both were used",
                  "The team checks circulation and explains how to look after each site.")


FRAMES = {"P01": opening, "P02": routes, "P03": diagnostic_and_treatment, "P06": route_change}


def encode(scene):
    _, duration, still_at = SCENES[scene]
    target = HERE / f"{scene}.mp4"
    ff = str(wrist.FFMPEG)
    args = [
        ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
        "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
        "-threads", "2", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(target),
    ]
    process = subprocess.Popen(args, stdin=subprocess.PIPE)
    previous = None
    try:
        with process.stdin as pipe:
            for index in range(duration*FPS):
                stamp = index/FPS
                if scene == "P01":
                    stamp = min(stamp, 10)
                elif scene == "P02":
                    if stamp < 2.4:
                        stamp = 0
                    elif 8.0 <= stamp < 9.3:
                        stamp = 8.0
                    elif 14.3 <= stamp < 16.1:
                        stamp = 14.3
                    elif stamp >= 16.1:
                        stamp = 16.2
                elif scene == "P03":
                    stamp = min(stamp, 14.3)
                elif scene == "P06":
                    stamp = min(stamp, 14.7)
                if stamp != previous:
                    raw = FRAMES[scene](stamp).tobytes()
                    previous = stamp
                pipe.write(raw)
    finally:
        if process.wait():
            raise RuntimeError(f"Encoding failed for {scene}")
    subprocess.run([ff, "-v", "error", "-xerror", "-i", str(target), "-map", "0:v:0",
                    "-f", "null", "-"], check=True)
    subprocess.run([ff, "-v", "error", "-y", "-ss", str(still_at), "-i", str(target),
                    "-frames:v", "1", str(HERE/f"{scene}.png")], check=True)
    print(f"{scene} · {duration}s · 1920x1080 · 24fps · silent · full decode passed", flush=True)


if __name__ == "__main__":
    scenes = sys.argv[1:] or list(SCENES)
    for name in scenes:
        FRAMES[name](SCENES[name][2])
    with ThreadPoolExecutor(max_workers=3) as workers:
        list(workers.map(encode, scenes))
