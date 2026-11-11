"""Render closure, recovery, emergency and source visuals for Episode 05."""
from __future__ import annotations

from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
OUT = HERE / "visuals"
REVISION = HERE.parent / "episode-01/revision"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "episode-04"))
sys.path.insert(0, str(REVISION / "femoral-route-scenes"))
from render_recovery import closure_stitch, gloved_pressure, recovery_background
from render_route import cutaway as groin_cutaway
from render_tavi_editorial import (
    DEEP, FFMPEG, H, INK, JADE, LINE, MINT, MUTED, PALE, W, WARN, check,
    crossfade, curve, ease, font, gradient, groin_locator, leader, logo, panel, shape, tag, urgent_icon, write,
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


radial = load("episode05_radial", REVISION / "radial-route-scenes/render_radial_scenes.py")
SCENES = {s["id"]: s for s in json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))}
FRAME = (70, 290, 1850, 928)


@lru_cache(maxsize=20)
def base(id, takeaway):
    image = gradient((249, 252, 248), (226, 240, 231)).copy()
    image.paste(logo(), (68, 41))
    d = ImageDraw.Draw(image)
    write(d, 162, 49, "Elysian Biomedical LLP", 33, "bold", DEEP)
    write(d, 164, 88, "Cardiology Education Series", 24, "body", MUTED)
    d.text((1848, 51), "EPISODE 05", fill=DEEP, font=font(27, "bold"), anchor="rt")
    d.line((69, 137, 1850, 137), fill=LINE, width=2)
    write(d, 69, 174, SCENES[id]["title"], 72, "title")
    d.line((69, 968, 1850, 968), fill=LINE, width=2)
    write(d, 69, 992, takeaway, 32, "bold", DEEP)
    return image


def fit(image, art, box):
    x0, y0, x1, y1 = box
    scale = min((x1-x0)/art.width, (y1-y0)/art.height)
    size = round(art.width*scale), round(art.height*scale)
    fitted = art.resize(size, Image.Resampling.LANCZOS)
    at = (x0 + (x1-x0-size[0])//2, y0 + (y1-y0-size[1])//2)
    image.paste(fitted, at)
    return lambda x,y: (at[0]+x*scale, at[1]+y*scale)


@lru_cache(maxsize=15)
def wrist_art(pressure):
    back = radial.wrist.background().convert("RGBA")
    layer = Image.new("RGBA", back.size)
    radial.wrist_band(ImageDraw.Draw(layer), 0, pressure)
    return Image.alpha_composite(back, layer).convert("RGB").crop((83, 315, 1539, 747))


@lru_cache(maxsize=15)
def groin_art(kind, progress):
    back = groin_cutaway().copy()
    layer = Image.new("RGBA", back.size)
    d = ImageDraw.Draw(layer)
    if kind == "pressure":
        gloved_pressure(d, progress)
    elif kind == "stitch":
        closure_stitch(d, progress)
    return Image.alpha_composite(back, layer).convert("RGB").crop((88, 259, 1536, 752))


@lru_cache(maxsize=45)
def closure_frame(wrist_pressure, groin_kind, groin_step, check_sites):
    image = base("P07", "Staff check for bleeding at either access site.").copy()
    d = ImageDraw.Draw(image)
    panel(d, (70, 290, 932, 928))
    panel(d, (988, 290, 1850, 928))
    tag(d, 112, 333, "Wrist access")
    tag(d, 1030, 333, "Groin access")
    w = fit(image, wrist_art(wrist_pressure), (112, 421, 889, 737))
    g = fit(image, groin_art(groin_kind, groin_step), (1028, 416, 1809, 747))
    d = ImageDraw.Draw(image)
    write(d, 112, 765, "Pressure band", 36, "bold", DEEP)
    write(d, 112, 820, "Staff ease the pressure gradually.", 28, color=MUTED)
    leader(d, (326, 786), w(555, 171))
    if groin_kind == "stitch":
        write(d, 1030, 765, "Closure stitch example", 36, "bold", DEEP)
        write(d, 1031, 820, "An alternative to hand pressure.", 28, color=MUTED)
        leader(d, (1440, 785), g(653, 295))
    elif groin_kind == "pressure":
        write(d, 1030, 765, "Firm hand pressure", 36, "bold", DEEP)
        write(d, 1031, 820, "The team may use a closure device.", 28, color=MUTED)
        leader(d, (1421, 786), g(650, 153))
    else:
        write(d, 1030, 765, "Pressure or a closure device", 36, "bold", DEEP)
    if check_sites:
        check(d, 870, 354)
        check(d, 1787, 354)
    return image


def p07(t):
    pressure = round((1-ease((t-3.8)/5.4))*9)/9
    if t < 8.4:
        return closure_frame(pressure, "none", 0, False)
    if t < 15.9:
        return closure_frame(pressure, "pressure", round(ease((t-8.4)/2)*9)/9, False)
    if t < 16.6:
        return crossfade(closure_frame(0, "pressure", 1, False), closure_frame(0, "stitch", 0, False), ease((t-15.9)/.7))
    return closure_frame(0, "stitch", round(ease((t-16.6)/2)*9)/9, t >= 21.3)


def seated_patient(d):
    d.ellipse((123, 765, 835, 822), fill="#e4efe5")
    d.line(((280, 547), (291, 725), (516, 730)), fill="#7daa9c", width=27, joint="curve")
    d.line(((322, 691), (329, 816)), fill="#7daa9c", width=17)
    d.line(((534, 705), (536, 812)), fill="#7daa9c", width=17)
    d.rounded_rectangle((268, 535, 358, 698), 25, fill="#bed6c7", outline="#84ac9c", width=2)
    d.rounded_rectangle((303, 675, 559, 730), 18, fill="#bbd6c7", outline="#84ac9c", width=2)
    leg = curve((381, 636), ((428, 621), (480, 641), (529, 661)), ((556, 670), (594, 678), (614, 701)),
                ((620, 729), (606, 758), (616, 777)), ((634, 782), (666, 782), (680, 795)),
                ((685, 807), (668, 816), (628, 815)), ((601, 815), (587, 804), (582, 782)),
                ((574, 749), (573, 725), (563, 722)), ((474, 727), (410, 725), (381, 701)))
    shape(d, leg, "#a6bcad", "#748b80")
    gown = curve((351, 530), ((369, 499), (413, 499), (442, 518)), ((475, 549), (484, 595), (477, 629)),
                 ((475, 645), (476, 670), (481, 681)), ((451, 695), (405, 694), (372, 681)),
                 ((349, 635), (329, 561), (351, 530)))
    shape(d, gown, "#7aab9d", "#5b9588")
    head = curve((366, 506), ((337, 482), (340, 442), (371, 420)), ((396, 402), (433, 411), (442, 435)),
                 ((455, 444), (466, 453), (456, 463)), ((456, 485), (440, 502), (428, 504)),
                 ((424, 516), (430, 530), (435, 534)), ((404, 551), (382, 534), (366, 506)))
    shape(d, head, "#dbab95", "#a97869")
    d.arc((338, 409, 454, 505), 171, 333, fill="#675850", width=17)
    d.rounded_rectangle((419, 627, 674, 661), 13, fill="#acd0be", outline="#75a293", width=2)
    arm = curve((416, 559), ((447, 551), (474, 580), (501, 606)), ((552, 603), (601, 599), (637, 604)),
                ((668, 607), (682, 620), (665, 634)), ((628, 642), (554, 640), (499, 642)),
                ((471, 646), (446, 617), (416, 594)))
    shape(d, arm, "#dbab95", "#a97869")
    d.rounded_rectangle((615, 601, 643, 640), 6, fill="#6daea0", outline="#497c70", width=2)
    d.rounded_rectangle((618, 602, 642, 612), 4, fill="#c3e5d3", outline="#79a896", width=1)
    return 630, 618


@lru_cache(maxsize=2)
def mobility_scene(ready):
    detail = "Wait until staff tell you it is safe to get up." if ready else "The team tells you when it is safe to get up."
    image = base("P08", detail).copy()
    d = ImageDraw.Draw(image)
    panel(d, (70, 290, 932, 928))
    panel(d, (988, 290, 1850, 928))
    tag(d, 112, 333, "Wrist access")
    tag(d, 1027, 333, "Groin access")
    point = seated_patient(d)
    write(d, 112, 851, "Often able to sit up sooner", 32, "bold", DEEP)
    write(d, 709, 614, "Wrist band", 25, "bold", DEEP)
    leader(d, (697, 626), point)
    art = recovery_background().crop((95, 317, 1479, 739))
    track = fit(image, art, (1018, 436, 1813, 745))
    d = ImageDraw.Draw(image)
    d.text((1440, 756), "May need to lie flat with the leg straight", font=font(32, "bold"), fill=DEEP, anchor="mm")
    if ready:
        d.rounded_rectangle((1065, 813, 1778, 877), 15, fill=MINT)
        d.ellipse((1082, 825, 1110, 853), fill="#d8ac94", outline="#9a7463", width=2)
        d.arc((1081, 824, 1111, 854), 169, 342, fill="#685650", width=5)
        d.rounded_rectangle((1078, 850, 1115, 868), 7, fill="#68a395")
        d.line(((1110, 861), (1124, 847), (1136, 845)), fill="#539181", width=5, joint="curve")
        d.text((1148, 845), "Staff let you know when you can walk", font=font(30, "bold"), fill=INK, anchor="lm")
    else:
        label_at = track(655, 200)
        write(d, 1070, 449, "Groin dressing", 24, "bold", DEEP)
        leader(d, (1271, 461), label_at)
    return image


def p08(t):
    return crossfade(mobility_scene(False), mobility_scene(True), ease((t-15.0)/.8))


def discharge_sheet(d, x, y):
    panel(d, (x, y+22, x+605, y+438), fill="#c4decf", outline="#83aa9a", radius=22)
    panel(d, (x+22, y+40, x+582, y+416), fill="#fbfcf4", outline="#99bfaf", radius=14)
    d.rounded_rectangle((x+208, y, x+398, y+53), 10, fill="#6da393")
    write(d, x+66, y+91, "Your discharge plan", 37, "title", DEEP)
    for i, name in enumerate(("Dressing care", "Medicines", "Lifting, driving and work", "Who to call")):
        yy = y+172+63*i
        check(d, x+85, yy)
        d.text((x+129, yy), name, font=font(29, "bold"), fill=INK, anchor="lm")


def car(d, x, y):
    body = curve((x, y+111), ((x+22,y+92),(x+66,y+87),(x+103,y+82)),
                 ((x+123,y+55),(x+147,y+31),(x+184,y+28)),
                 ((x+234,y+24),(x+268,y+41),(x+297,y+76)),
                 ((x+335,y+84),(x+351,y+106),(x+348,y+133)),
                 ((x+344,y+150),(x+317,y+156),(x+272,y+155)),
                 ((x+181,y+157),(x+97,y+157),(x+24,y+148)),
                 ((x+6,y+143),(x-3,y+128),(x,y+111)))
    shape(d, body, "#82b4a2", "#477d6d", 3)
    glass = ((x+123,y+80),(x+158,y+43),(x+204,y+41),(x+211,y+79))
    shape(d, glass, "#e3f1e5", "#649588", 2)
    shape(d, ((x+224,y+43),(x+258,y+56),(x+280,y+78),(x+228,y+79)), "#e3f1e5", "#649588", 2)
    for xx in (x+83,x+274):
        d.ellipse((xx-24,y+126,xx+24,y+173), fill="#3d5852", outline="#365d55", width=3)
        d.ellipse((xx-10,y+139,xx+10,y+158), fill="#bacfc2")


@lru_cache(maxsize=2)
def home_scene(plan):
    takeaway = "Ask for written instructions before you leave." if plan else "Your team decides when you are ready to go home."
    image = base("P09", takeaway).copy()
    d = ImageDraw.Draw(image)
    panel(d, FRAME)
    if plan:
        discharge_sheet(d, 149, 369)
        d.ellipse((1042, 363, 1667, 816), fill=MINT)
        car(d, 1164, 502)
        write(d, 1109, 724, "Plan your ride home", 38, "bold", DEEP)
    else:
        panel(d, (127, 365, 910, 796), fill="#f0f8ef")
        panel(d, (1006, 365, 1794, 796), fill="#f0f8ef")
        car(d, 324, 496)
        fit(image, recovery_background().crop((120, 323, 1470, 738)), (1050, 443, 1749, 697))
        d = ImageDraw.Draw(image)
        d.text((519, 721), "Possible same-day discharge", font=font(37, "bold"), fill=DEEP, anchor="mm")
        d.text((1398, 722), "More monitoring if needed", font=font(37, "bold"), fill=DEEP, anchor="mm")
    return image


def p09(t):
    return crossfade(home_scene(False), home_scene(True), ease((t-8.4)/.8))


def wrist_skin(d, x, y, scale=1, bruise=False, cool=False):
    hand = curve((0, 65), ((83, 50), (113, 58), (145, 53)), ((164, 45), (175, 22), (190, 10)),
                 ((214, -10), (230, -1), (219, 14)), ((208, 29), (202, 41), (196, 52)),
                 ((231, 53), (272, 47), (306, 52)), ((322, 56), (322, 71), (302, 75)),
                 ((317, 78), (321, 87), (311, 95)), ((300, 103), (278, 103), (263, 103)),
                 ((280, 108), (274, 122), (257, 124)), ((236, 128), (212, 129), (196, 129)),
                 ((178, 145), (161, 148), (128, 143)), ((75, 138), (22, 138), (0, 143)))
    points = [(x+a*scale,y+b*scale) for a,b in hand]
    shape(d, points, "#d3b2a5" if cool else "#b78067", "#805b50", 3)
    d.line(((x+145*scale,y+66*scale),(x+157*scale,y+93*scale),(x+147*scale,y+125*scale)), fill="#956555", width=2, joint="curve")
    if bruise:
        d.ellipse((x+104*scale,y+60*scale,x+132*scale,y+78*scale), fill="#926677")
        d.rounded_rectangle((x+110*scale,y+66*scale,x+126*scale,y+79*scale), 3, fill="#faedd0", outline="#997855", width=1)


def swelling_icon(d, x, y, urgent=False):
    dark = WARN if urgent else JADE
    d.ellipse((x-41,y-41,x+41,y+41), fill="#f3e0d5" if urgent else MINT)
    contour = curve((x-28,y+9), ((x-15,y+9),(x-14,y-14),(x,y-14)),
                    ((x+15,y-14),(x+15,y+9),(x+28,y+9)))
    d.line(contour, fill=dark, width=4, joint="curve")
    d.line((x,y-19,x,y-28), fill=dark, width=3)


@lru_cache(maxsize=2)
def care_team(alert):
    footer = "Contact your care team promptly if symptoms worsen." if alert else "A small bruise and mild soreness can happen."
    image = base("P10", footer).copy()
    d = ImageDraw.Draw(image)
    panel(d, FRAME)
    if alert:
        write(d, 128, 348, "Contact your care team", 50, "title", DEEP)
        for i, (icon, phrase) in enumerate((("swelling", "Increasing pain, redness or swelling"),
                                             ("fluid", "Fluid draining from the site"), ("fever", "Fever"))):
            yy = 519+i*120
            if icon == "fever":
                d.ellipse((129,yy-40,209,yy+40), fill=MINT)
                d.rounded_rectangle((162,yy-30,176,yy+19), 7, outline=JADE, width=4)
                d.ellipse((157,yy+12,181,yy+34), fill=JADE)
            elif icon == "fluid":
                d.ellipse((127,yy-41,209,yy+41), fill=MINT)
                drop = curve((168,yy-24), ((154,yy-7),(149,yy-4),(149,yy+7)),
                             ((149,yy+27),(187,yy+27),(187,yy+7)), ((187,yy-4),(182,yy-7),(168,yy-24)))
                shape(d, drop, "#77aa9c", JADE)
            else:
                swelling_icon(d, 168, yy)
            d.text((239, yy), phrase, font=font(40, "bold"), fill=INK, anchor="lm")
    else:
        for x, name in ((122,"Wrist"),(1003,"Groin")):
            panel(d, (x, 361, x+794, 835), fill="#eff7ee")
            tag(d, x+36, 399, name)
        wrist_skin(d, 269, 531, 1.44, bruise=True)
        px, py = groin_locator(d, 1135, 472, 1.38)
        d.ellipse((px-45,py+20,px-16,py+36), fill="#c98c96")
        leader(d, (447, 740), (439, 636))
        write(d, 465, 727, "Small bruise", 30, "bold", DEEP)
        leader(d, (1448, 794), (px-28, py+28))
        write(d, 1463, 777, "Small bruise", 30, "bold", DEEP)
    return image


def p10(t):
    return crossfade(care_team(False), care_team(True), ease((t-4.8)/.8))


@lru_cache(maxsize=2)
def urgent(whole_limb):
    image = base("P11", "Call your local emergency number.").copy()
    d = ImageDraw.Draw(image)
    panel(d, FRAME, fill="#fff8f1", outline="#d9c2b4")
    write(d, 125, 348, "Get emergency help", 54, "title", WARN)
    if whole_limb:
        rows = (("arm", "Suddenly cold, pale or numb hand or foot"), ("chest", "Severe chest pain"),
                ("breathing", "Sudden trouble breathing"))
        wrist_skin(d, 1283, 473, 1.18, cool=True)
        write(d, 1313, 688, "On the side used", 27, "bold", WARN)
        write(d, 1313, 730, "for the procedure", 27, "bold", WARN)
    else:
        rows = (("bleeding", "Heavy bleeding or bleeding that won’t stop"), ("swelling", "Swelling that grows quickly"))
        fit(image, groin_art("pressure", 1), (1128, 462, 1779, 755))
        d = ImageDraw.Draw(image)
        write(d, 1282, 770, "Apply firm pressure if bleeding", 27, "bold", WARN)
    for i, (icon, text) in enumerate(rows):
        y = 503+i*128
        if icon == "swelling":
            swelling_icon(d, 170, y, urgent=True)
        else:
            urgent_icon(d, 170, y, icon)
        d.text((242, y), text, font=font(38, "bold"), fill=INK, anchor="lm")
    return image


def p11(t):
    return urgent(t >= 12.3)


@lru_cache(maxsize=1)
def sources():
    image = base("P12", "Full references and links to the angiogram films are in the description.").copy()
    d = ImageDraw.Draw(image)
    panel(d, FRAME)
    write(d, 125, 346, "Wrist vs groin access", 46, "title", DEEP)
    d.line((125, 418, 1794, 418), fill=LINE, width=2)
    for i, entry in enumerate(("ACC/AHA/SCAI · Acute coronary syndromes and coronary revascularization",
                                "European Society of Cardiology · Acute and chronic coronary syndromes",
                                "SCAI · Catheterization laboratory best practices",
                                "NHS and Interior Health · Patient recovery and emergency guidance")):
        write(d, 126, 464+57*i, entry, 32, "bold", INK)
    d.line((125, 711, 1794, 711), fill=LINE, width=2)
    write(d, 126, 759, "Original educational animation", 30, "bold", DEEP)
    write(d, 126, 815, "Alexander synthetic English narration via ElevenLabs", 28, color=MUTED)
    return image


FUNCTIONS = {"P07": p07, "P08": p08, "P09": p09, "P10": p10, "P11": p11, "P12": lambda t: sources()}
KEY_TIMES = {"P07": 12, "P08": 16, "P09": 15, "P10": 9, "P11": 15, "P12": 0}


def render(id):
    scene = SCENES[id]
    seconds = scene["target_end_sec"] - scene["target_start_sec"]
    key = OUT / f"{id}.png"
    video = OUT / f"{id}.mp4"
    draw = FUNCTIONS[id]
    draw(KEY_TIMES[id]).save(key, optimize=True)
    with Image.open(key) as verified:
        assert verified.size == (W,H)
        verified.verify()
    rate = 12 if id in ("P07", "P08", "P09", "P10") else 4
    command = [str(FFMPEG), "-y", "-v", "error"]
    tail = ["-an", "-vf", "fps=24", "-c:v", "libx264", "-threads", "3", "-preset", "veryfast", "-crf", "17",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)]
    if id == "P12":
        subprocess.run(command + ["-loop", "1", "-framerate", "24", "-i", str(key), "-t", str(seconds)] + tail, check=True)
    else:
        command += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", str(rate), "-i", "-"]
        with subprocess.Popen(command + tail, stdin=subprocess.PIPE) as encoder:
            last, pixels = None, None
            for n in range(seconds*rate):
                image = draw(n/rate)
                if image is not last:
                    last, pixels = image, image.tobytes()
                encoder.stdin.write(pixels)
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError(f"Could not encode {video.name}")
    metadata = subprocess.run([str(FFMPEG), "-hide_banner", "-xerror", "-i", str(video), "-f", "null", "-"],
                              capture_output=True, text=True, check=True).stderr
    assert "1920x1080" in metadata and "Video: h264" in metadata and "Audio:" not in metadata
    assert f"00:00:{seconds:02}.00" in metadata and "24 fps" in metadata
    print(f"{id} {seconds}s, silent 1080p24 H.264 and PNG verified", flush=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for id in sys.argv[1:] or FUNCTIONS:
        render(id)
