"""Draw and encode the reusable, silent coronary scenes for the narrated revision."""

from functools import lru_cache
from math import cos, hypot, radians, sin
from pathlib import Path
from random import Random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter


OUT = Path(__file__).resolve().parent
REVISION = OUT.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REVISION / "wrist-proof"))
sys.path.insert(0, str(REVISION.parent / "production"))
from render_wrist_proof import FFMPEG, GREEN, INK, LOGO, MUTED, font, smooth
from vascular_art import ANGIO_LEFT, ANGIO_RIGHT, LAD, LCX, LEFT_MAIN, LEFT_TWIGS
from vascular_art import MYOCARDIUM, RCA, RCA_TWIGS, curve, trace


W, H = 1600, 900
FPS = 24
SCENES = {
    "left-contrast": (23.54, "Left coronary contrast run"),
    "right-contrast": (15.44, "Right coronary contrast run"),
    "reading-the-result": (25.09, "Reading the result"),
    "deciding-the-next-step": (24.99, "Deciding the next step"),
    "reach-left-opening": (11.16, "Reach the coronary opening"),
    "radial-reposition": (11.79, "Reposition the catheter"),
    "femoral-left-withdrawal": (13.50, "Withdraw the left diagnostic catheter"),
    "femoral-right-advance": (10.36, "Advance the right diagnostic catheter"),
}
GOLD = "#ffce8e"
CORAL = "#ab6263"
CREAM = "#f8fbf6"
PALE = "#e8f1e9"


def clamp(value):
    return max(0.0, min(1.0, value))


def mix(first, second, fraction):
    return tuple(round(a + (b-a)*fraction) for a, b in zip(first, second))


def stroke(draw, path, color, width):
    if len(path) > 1:
        draw.line(path, fill=color, width=width, joint="curve")


def tag(draw, position, label, *, light=True):
    x, y = position
    face = font(22, "semibold")
    right = x + draw.textlength(label, font=face) + 36
    draw.rounded_rectangle((x, y, right, y+41), radius=8,
                           fill="#e1eee6" if light else "#233638")
    draw.text((x+18, y+8), label, font=face, fill=GREEN if light else "#eff6ef")


def label(draw, text, position, point):
    x, y = position
    tx, ty = point
    length = draw.textlength(text, font=font(25, "semibold"))
    start = (x+length+12, y+16) if x < tx else (x-11, y+16)
    knee = (start[0]+19 if start[0] < tx else start[0]-19, y+16)
    stroke(draw, (start, knee, point), "#466b5a", 2)
    draw.ellipse((tx-4, ty-4, tx+4, ty+4), fill="#fbf4da", outline="#326957", width=2)
    draw.text(position, text, font=font(25, "semibold"), fill=INK)


@lru_cache(maxsize=4)
def background(name):
    image = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(image)
    for row in range(H):
        draw.line((0, row, W, row), fill=mix((246, 251, 246), (220, 234, 226), row/H))
    logo = Image.open(LOGO).convert("RGB").resize((48, 48), Image.Resampling.LANCZOS)
    draw.rounded_rectangle((76, 57, 126, 107), 8, fill="white")
    image.paste(logo, (77, 58))
    draw.text((144, 62), "Elysian Biomedical LLP", fill=GREEN, font=font(24, "semibold"))
    draw.text((144, 93), "Cardiology Education Series", fill=MUTED, font=font(18))
    draw.text((1522, 66), "CORONARY ANGIOGRAPHY", fill=GREEN, font=font(20, "semibold"), anchor="rt")
    stroke(draw, ((76, 128), (1522, 128)), "#b3ccbf", 2)
    draw.text((76, 151), SCENES[name][1], font=font(57, "heading"), fill=INK)
    return image


def base_heart(draw, side, *, show_catheter=True):
    def xy(point):
        x, y = point
        return (130 + (x-150)*1.20, 313 + (y-58)*.97)

    def path(points):
        return tuple(map(xy, points))

    draw.ellipse((112, 692, 590, 740), fill="#dce9df")
    desc = curve((397, 166), ((397, 261), (389, 370), (371, 449)))
    stroke(draw, path(desc), "#9d666d", 30)
    stroke(draw, path(desc), "#ad797b", 22)
    aorta = curve((306, 229), ((298, 182), (300, 132), (322, 108)),
                  ((358, 63), (392, 100), (397, 166)))
    branches = (
        curve((320, 110), ((318, 94), (294, 72), (282, 69))),
        curve((351, 91), ((346, 75), (346, 67), (345, 58))),
        curve((378, 102), ((383, 91), (391, 83), (398, 78))),
    )
    for branch in branches:
        stroke(draw, path(branch), "#914a57", 21)
        stroke(draw, path(branch), "#c67676", 14)
    stroke(draw, path(aorta), "#954f5a", 48)
    stroke(draw, path(aorta), "#c97775", 42)
    stroke(draw, path(aorta), "#e49a8c", 27)
    stroke(draw, path(aorta), "#8d4a57", 17)
    muscle = path(MYOCARDIUM)
    draw.polygon(muscle, fill="#ac6269")
    stroke(draw, muscle, "#894f5d", 3)
    for step in range(11):
        ratio = 1-(step+1)*.039
        inset = tuple((x*ratio+316*(1-ratio), y*ratio+540*(1-ratio)) for x, y in muscle)
        draw.polygon(inset, fill=mix((172, 98, 105), (215, 137, 130), (step+1)/12))
    for index in range(15):
        x = 204+index*13
        y = 502 + abs(x-305)*.09
        stroke(draw, curve((x, y), ((x-17, y+29), (x-8, y+94), (x+32, y+141))),
               "#c07e7d", 1)
    root = path(curve((293, 238), ((289, 226), (294, 205), (307, 203)),
                      ((328, 201), (339, 217), (330, 236)),
                      ((320, 242), (305, 243), (293, 238))))
    draw.polygon(root, fill="#b77578")
    stroke(draw, root, "#e0a096", 3)
    vx, vy = xy((312, 238))
    draw.ellipse((vx-22, vy-6, vx+20, vy+8), fill="#744554", outline="#e8a89a", width=2)
    active = (LEFT_MAIN, LAD, LCX) if side == "left" else (RCA,)
    inactive = (RCA,) if side == "left" else (LEFT_MAIN, LAD, LCX)
    twigs = LEFT_TWIGS if side == "left" else RCA_TWIGS
    for vessel in RCA_TWIGS + LEFT_TWIGS:
        stroke(draw, path(vessel), "#a97173", 4)
    for vessel in inactive:
        stroke(draw, path(vessel), "#975c66", 9)
        stroke(draw, path(vessel), "#d49a8e", 4)
    for vessel in active:
        stroke(draw, path(vessel), "#7c4a55", 13)
        stroke(draw, path(vessel), "#be7370", 8)
    ostium = LEFT_MAIN[0] if side == "left" else RCA[0]
    catheter = path(curve((303, 143), ((301, 180), (301, 193), (307, 209)),
                          ((310, 217), ((321 if side == "left" else 300), 220), ostium)))
    if show_catheter:
        stroke(draw, catheter, "#164f50", 12)
        stroke(draw, catheter, "#86c9c0", 8)
        stroke(draw, catheter, "#e8f3e6", 3)
    return xy, path, active, twigs, catheter[-1]


@lru_cache(maxsize=2)
def contrast_base(side):
    image = background(f"{side}-contrast").copy()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 250, 739, 765), 22, fill="#f2f8f0", outline="#bfd5c6", width=2)
    draw.rounded_rectangle((770, 250, 1521, 765), 22, fill="#dcebe1", outline="#bfd5c6", width=2)
    xy, path, active, twigs, ostium = base_heart(draw, side)
    tag(draw, (99, 269), "Coronary anatomy")
    tag(draw, (791, 269), "Simulated fluoroscopy")
    draw.text((1491, 282), "Contrast appears dark", font=font(22), fill=MUTED, anchor="rt")
    label(draw, "Catheter tip", (500, 360), ostium)
    if side == "left":
        label(draw, "Left main", (503, 414), xy(LEFT_MAIN[10]))
        label(draw, "Circumflex", (539, 507), xy(LCX[25]))
        label(draw, "LAD", (482, 678), xy(LAD[39]))
    else:
        label(draw, "Right coronary artery", (432, 662), xy(RCA[42]))
    return image, path, active, twigs, ostium


def project(point, angle):
    x, y = point
    depth = 25*sin(y/55) + (x-100)*.17
    theta = radians(angle)
    return (x*cos(theta) + depth*sin(theta) + 120*(1-cos(theta)),
            y + .15*depth*sin(theta))


@lru_cache(maxsize=5)
def gray_background(angle):
    width, height = 690, 415
    texture = Image.new("L", (width, height))
    noise = Random(254)
    texture.putdata([128+noise.randint(-17, 17) for _ in range(width*height)])
    texture = texture.filter(ImageFilter.GaussianBlur(.95))
    image = Image.new("L", (width, height))
    draw = ImageDraw.Draw(image)
    for row in range(height):
        level = round(170 + 13*sin(row/82) - row*.032)
        draw.line((0, row, width, row), fill=level)
    lung_layer = Image.new("L", (width, height), 171)
    lung = ImageDraw.Draw(lung_layer)
    lung.ellipse((72+angle, -12, 340+angle, 402), fill=151)
    lung.ellipse((354+angle, -5, 610+angle, 398), fill=149)
    lung.ellipse((186+angle, 91, 530+angle, 406), fill=192)
    for index in range(8):
        y = 24+index*43
        stroke(lung, curve((-25, y+46), ((130, y+9), (260, y-26), (424, y+2)),
                           ((553, y+23), (620, y+37), (719, y+61))), 199, 8)
    stroke(lung, curve((348+angle, 0), ((333+angle, 122), (342+angle, 269), (357+angle, 421))), 198, 27)
    image = Image.blend(image, lung_layer.filter(ImageFilter.GaussianBlur(8)), .51)
    image = Image.blend(image, texture, .18)
    return image.convert("RGB")


@lru_cache(maxsize=4)
def flow_geometry(vessels):
    geometry = []
    for vessel in vessels:
        lengths = [0.0]
        for a, b in zip(vessel, vessel[1:]):
            lengths.append(lengths[-1] + hypot(a[0]-b[0], a[1]-b[1]))
        entry = 0.0
        if geometry:
            vx, vy = vessel[0]
            _, entry = min(
                (hypot(vx-x, vy-y), parent_entry+distance)
                for parent, parent_entry, parent_lengths in geometry
                for (x, y), distance in zip(parent, parent_lengths)
            )
        geometry.append((vessel, entry, lengths))
    total = max(entry+lengths[-1] for _, entry, lengths in geometry)
    return geometry, total


def flow_sections(vessels, fill):
    geometry, total = flow_geometry(vessels)
    head = total*fill
    return tuple(trace(vessel, clamp((head-entry)/lengths[-1]))
                 for vessel, entry, lengths in geometry)


def gray_vessels(side, fill, *, opacity=1, angle=0, narrow=False, callout=False, view=""):
    image = gray_background(angle).copy()
    draw = ImageDraw.Draw(image)
    tree = ANGIO_LEFT if side == "left" else ANGIO_RIGHT

    def xy(point):
        x, y = project(point, angle)
        return (106+x*2.07, 7+y*1.35)

    if fill > 0 and opacity > 0:
        sections = flow_sections(tuple(vessel for vessel, _ in tree), fill)
        for index, ((vessel, initial_width), drawn) in enumerate(zip(tree, sections)):
            for segment, (a, b) in enumerate(zip(drawn, drawn[1:])):
                location = segment / max(1, len(vessel)-1)
                width = initial_width * (1-location*.54) * 1.64
                if narrow and index == 1:
                    constriction = clamp(1 - abs(location-.47)/.09)
                    width *= 1 - constriction*.78
                tone = 33 + int(location*16) + (7 if index > 2 else 0)
                p1, p2 = xy(a), xy(b)
                gray = image.getpixel(tuple(map(round, p2)))
                stroke(draw, (p1, p2), mix(gray, (92, 92, 92), opacity), max(2, round(width)+2))
                stroke(draw, (p1, p2), mix(gray, (tone, tone, tone), opacity), max(1, round(width)))
    px, py = xy(tree[0][0][0])
    catheter = curve((px-55, -8), ((px-63, 15), (px-17, py-15), (px, py)))
    stroke(draw, catheter, "#333637", 5)
    stroke(draw, catheter, "#686a6b", 2)
    if callout:
        stenosis = tree[1][0][round((len(tree[1][0])-1)*.47)]
        x, y = xy(stenosis)
        draw.ellipse((x-20, y-20, x+20, y+20), outline="#ffce8e", width=3)
        stroke(draw, ((x+18, y-9), (x+65, y-41), (x+106, y-41)), "#ffce8e", 2)
        draw.text((x+113, y-52), "Narrowing", fill="#fff1d3", font=font(19, "semibold"),
                  stroke_width=1, stroke_fill="#282e30")
    if view:
        tag(draw, (15, 15), view, light=False)
    return image


def pulse(p):
    if p < .10:
        return 0.0, 0.0
    if p < .48:
        return smooth((p-.10)/.25), 1-smooth((p-.39)/.09)
    return smooth((p-.48)/.23), 1-smooth((p-.83)/.13)


def draw_contrast(name, p):
    side = name.split("-")[0]
    template, path, active, twigs, ostium = contrast_base(side)
    image = template.copy()
    draw = ImageDraw.Draw(image)
    fill, opacity = pulse(p)
    if fill > 0 and opacity > 0:
        colors = mix((187, 108, 108), (255, 218, 158), opacity)
        for index, section in enumerate(flow_sections(active+twigs, fill)):
            stroke(draw, path(section), colors, 7 if index < len(active) else 4)
        x, y = ostium
        draw.ellipse((x-5, y-5, x+5, y+5), fill=GOLD)

    first_angle = -21 if side == "right" else 4
    second_angle = 29 if side == "right" else 4
    angle = first_angle if p < .47 else second_angle
    film = gray_vessels(side, fill, opacity=opacity, angle=angle)
    image.paste(film, (800, 324))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((799, 323, 1490, 740), 6, outline="#62766c", width=2)
    if side == "left":
        caption = "The left main fills first, followed by the LAD and circumflex."
    elif p < .43:
        caption = "Contrast is injected separately at the right coronary opening."
    else:
        caption = "The X-ray arm changes angle between views."
        draw_c_arm(draw, (1100, 815), smooth((p-.43)/.25))
    draw.text((78, 808), caption, fill=INK, font=font(29, "semibold"))
    return image


def draw_c_arm(draw, center, p):
    x, y = center
    draw.ellipse((x-26, y-14, x+26, y+14), fill="#becfcb", outline="#6d8c82", width=2)
    angle = radians(-54 + p*108)
    points = tuple((x+48*cos(angle+radians(i)), y+33*sin(angle+radians(i))) for i in range(-96, 97, 4))
    stroke(draw, points, "#397167", 5)
    for hx, hy in (points[0], points[-1]):
        draw.rounded_rectangle((hx-7, hy-6, hx+7, hy+6), 3, fill="#497e72")
    draw.text((x+69, y-11), "Imaging arm", fill=MUTED, font=font(19, "semibold"))


def draw_stenosis(p):
    image = background("reading-the-result").copy()
    draw = ImageDraw.Draw(image)
    for x, angle, label_text, ready in ((77, -16, "View 1", True), (813, 32, "View 2", p >= .29)):
        image.paste(gray_vessels("left", 1 if ready else 0, angle=angle, narrow=True,
                                 callout=ready, view=label_text if ready else ""), (x, 282))
        draw.rounded_rectangle((x-1, 281, x+690, 698), 8, outline="#687b71", width=2)
    tag(draw, (77, 226), "Simulated angiograms")
    if p < .29:
        note = "A thinner contrast-filled channel marks the narrowing."
    elif p < .52:
        note = "A thinner contrast-filled channel marks the same spot in both views."
    elif p < .76:
        note = "Pressure measurements or imaging inside the artery can clarify some findings."
    else:
        note = "If symptoms persist, the team may look for other causes."
    draw.text((77, 750), note, fill=INK, font=font(29, "semibold"))
    return image


def draw_options(p):
    image = background("deciding-the-next-step").copy()
    draw = ImageDraw.Draw(image)
    draw.text((78, 232), "Findings, symptoms and urgency guide the decision.", fill=INK, font=font(33))
    items = (
        ("Medicines", "Manage symptoms and cardiovascular risk."),
        ("Further testing", "Clarify what a narrowing means."),
        ("Angioplasty", "A balloon widens a narrowed artery. A stent may be placed."),
        ("Bypass review", "Discuss surgery when appropriate."),
    )
    for index, (heading, detail) in enumerate(items):
        x = 77 + (index % 2)*737
        y = 307 + (index // 2)*205
        visible = p >= (.04 + index*.12)
        draw.rounded_rectangle((x, y, x+706, y+165), 18,
                               fill="#f3f9f2" if visible else "#e8f1e8", outline="#b8d0c0", width=2)
        if visible:
            draw.rectangle((x+29, y+34, x+33, y+119), fill="#80a992")
            draw.text((x+54, y+39), heading, fill=GREEN, font=font(36, "semibold"))
            draw.text((x+54, y+96), detail, fill=MUTED, font=font(24))
    if p >= .75:
        draw.text((77, 788), "In this example, the procedure ends after imaging.", fill=INK,
                  font=font(29, "semibold"))
    return image


NEUTRAL_TIP = (1142, 518)
LEFT_ENTRY = (1253, 516)
RIGHT_ENTRY = (1067, 521)
WIRE_END = (1145, 577)


def tool_path(tip, shaping=0):
    tx, ty = tip
    return curve((1146, 340), ((1143, 371), (1140, 409), (1136, 453)),
                 ((1134, 500+shaping), (tx+(1142-tx)*.36, ty+shaping), tip))


@lru_cache(maxsize=1)
def groin_still():
    sys.path.insert(0, str(REVISION / "femoral-proof"))
    from render_femoral_proof import frame as femoral_frame
    image = femoral_frame(20.8).crop((102, 325, 1516, 709))
    return image.resize((614, 167), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def root_base(name):
    image = background(name).copy()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((76, 250, 739, 765), 22, fill="#f2f8f0", outline="#bfd5c6", width=2)
    draw.rounded_rectangle((770, 250, 1521, 765), 22, fill="#f1f7ef", outline="#bfd5c6", width=2)
    if name == "femoral-left-withdrawal":
        tag(draw, (99, 270), "Right groin")
        draw.text((100, 351), "The working sheath stays in place", fill=INK, font=font(29, "semibold"))
        image.paste(groin_still(), (101, 421))
        draw.text((101, 641), "The left catheter leaves through this sheath.", fill=MUTED, font=font(24))
    else:
        xy, _, _, _, _ = base_heart(draw, "left", show_catheter=False)
        tag(draw, (99, 270), "Aortic root")
        x, y = xy((309, 218))
        draw.ellipse((x-30, y-30, x+30, y+30), outline="#276557", width=3)
        stroke(draw, ((x+31, y-5), (568, 457), (696, 457)), "#759986", 2)
    tag(draw, (792, 270), "Enlarged view")
    root = curve(
        (1086, 331),
        ((1087, 380), (1094, 443), (1074, 466)),
        ((1035, 512), (1030, 558), (1050, 597)),
        ((1076, 659), (1125, 681), (1157, 680)),
        ((1208, 678), (1256, 651), (1276, 595)),
        ((1293, 544), (1281, 497), (1253, 468)),
        ((1229, 440), (1233, 378), (1232, 331)),
    )
    draw.polygon(root, fill="#af686c")
    stroke(draw, root, "#8a4f5b", 3)
    lumen = curve(
        (1111, 334),
        ((1111, 393), (1120, 450), (1095, 482)),
        ((1066, 522), (1060, 565), (1075, 595)),
        ((1097, 639), (1133, 650), (1157, 650)),
        ((1201, 649), (1233, 627), (1250, 591)),
        ((1269, 545), (1247, 503), (1229, 477)),
        ((1205, 443), (1210, 390), (1206, 334)),
    )
    draw.polygon(lumen, fill="#dca396")
    stroke(draw, lumen, "#edbcab", 3)
    for start, end in ((RIGHT_ENTRY, (970, 544)), (LEFT_ENTRY, (1347, 547))):
        xs, ys = start
        ex, ey = end
        branch = curve(start, ((xs+(ex-xs)*.44, ys-8), ((xs+ex)*.5, ey+6), end))
        stroke(draw, branch, "#9d5762", 29)
        stroke(draw, branch, "#dca396", 16)
        draw.ellipse((xs-11, ys-11, xs+11, ys+11), fill="#89505b", outline="#efd0b9", width=2)
    valve = curve((1071, 604), ((1109, 596), (1120, 614), (1158, 629)),
                  ((1193, 614), (1218, 601), (1258, 603)))
    stroke(draw, valve, "#834958", 11)
    stroke(draw, valve, "#efb49c", 5)
    label(draw, "Right coronary opening", (793, 440), RIGHT_ENTRY)
    label(draw, "Left coronary opening", (1286, 440), LEFT_ENTRY)
    label(draw, "Aortic valve", (1307, 658), (1217, 609))
    return image


def root_tools(draw, catheter, wire):
    if len(catheter) > 1:
        stroke(draw, catheter, "#164f50", 15)
        stroke(draw, catheter, "#8fcdc4", 10)
        stroke(draw, catheter, "#edf5df", 3)
        x, y = catheter[-1]
        draw.ellipse((x-5, y-5, x+5, y+5), fill="#dceee4", outline="#245c55", width=1)
    if len(wire) > 1:
        stroke(draw, wire, "#805a3d", 5)
        stroke(draw, wire, "#f5d493", 3)


def draw_root(name, p):
    image = root_base(name).copy()
    draw = ImageDraw.Draw(image)
    wire = ()
    if name == "reach-left-opening":
        tip = mix(NEUTRAL_TIP, LEFT_ENTRY, smooth((p-.46)/.37))
        catheter = tool_path(tip)
        if p < .45:
            wire = trace(tool_path(WIRE_END), 1-smooth((p-.08)/.37))
        caption = "The long guidewire withdraws through the catheter." if p < .45 else "The curved tip sits at the left coronary opening, above the valve."
    elif name == "radial-reposition":
        if p < .50:
            tip = mix(LEFT_ENTRY, NEUTRAL_TIP, smooth((p-.10)/.40))
        else:
            tip = mix(NEUTRAL_TIP, RIGHT_ENTRY, smooth((p-.51)/.39))
        catheter = tool_path(tip)
        caption = "The same catheter comes back into the aortic root." if p < .50 else "The same tip turns toward the right coronary opening."
    elif name == "femoral-left-withdrawal":
        neutral = mix(LEFT_ENTRY, NEUTRAL_TIP, smooth((p-.08)/.28))
        catheter = trace(tool_path(neutral), 1-smooth((p-.36)/.41))
        caption = "The left diagnostic catheter leaves the coronary opening and is withdrawn."
    else:
        wire = trace(tool_path(WIRE_END), smooth((p-.03)/.25) * (1-smooth((p-.54)/.21)))
        tip = mix(NEUTRAL_TIP, RIGHT_ENTRY, smooth((p-.76)/.21))
        catheter = trace(tool_path(tip, -8), smooth((p-.20)/.35))
        caption = "A different catheter follows the guidewire toward the aortic root." if p < .54 else "The guidewire comes out before the tip sits at the right opening."
    root_tools(draw, catheter, wire)
    draw.text((77, 810), caption, fill=INK, font=font(29, "semibold"))
    return image


def frame(name, p):
    if name.endswith("-contrast"):
        return draw_contrast(name, p)
    if name == "reading-the-result":
        return draw_stenosis(p)
    if name == "deciding-the-next-step":
        return draw_options(p)
    return draw_root(name, p)


def encode(name):
    duration, _ = SCENES[name]
    count = round(duration*FPS)
    target = OUT / f"{name}.mp4"
    command = [
        str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
        "-framerate", str(FPS), "-i", "-", "-an", "-vf", "scale=1920:1080:flags=lanczos",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(target),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    last_key = -1
    try:
        with process.stdin as pipe:
            for index in range(count):
                key = round(150*index/max(1, count-1))
                if key != last_key:
                    raw = frame(name, key/150).tobytes()
                    last_key = key
                pipe.write(raw)
    finally:
        if process.wait():
            raise RuntimeError(f"Encoding failed for {name}")
    subprocess.run([str(FFMPEG), "-v", "error", "-xerror", "-i", str(target),
                    "-f", "null", "-"], check=True)
    print(f"{target.name} | {count/FPS:.2f}s | 1920×1080 | decoded", flush=True)


def contact_sheet():
    samples = (
        ("left-contrast", .24), ("left-contrast", .37), ("left-contrast", .76),
        ("right-contrast", .33), ("right-contrast", .59), ("right-contrast", .77),
        ("reading-the-result", .22), ("reading-the-result", .46), ("deciding-the-next-step", .86),
    )
    result = Image.new("RGB", (1600, 944), "#dcebe1")
    draw = ImageDraw.Draw(result)
    for index, (name, p) in enumerate(samples):
        x = 9+(index % 3)*530
        y = 9+(index // 3)*312
        result.paste(frame(name, p).resize((520, 292), Image.Resampling.LANCZOS), (x, y))
        draw.text((x+8, y+293), f"{name.replace('-', ' ')}  ·  {p*100:.0f}%",
                  fill=MUTED, font=font(14))
    result.save(OUT / "shared-coronary-contact-sheet.jpg", quality=94)
    root_samples = (
        ("reach-left-opening", .08), ("reach-left-opening", .90),
        ("radial-reposition", .48), ("radial-reposition", .91),
        ("femoral-left-withdrawal", .20), ("femoral-left-withdrawal", .86),
        ("femoral-right-advance", .46), ("femoral-right-advance", .97),
    )
    root_sheet = Image.new("RGB", (1582, 906), "#dcebe1")
    marks = ImageDraw.Draw(root_sheet)
    for index, (name, p) in enumerate(root_samples):
        x = 9+(index % 4)*394
        y = 15+(index // 4)*312
        root_sheet.paste(frame(name, p).resize((378, 213), Image.Resampling.LANCZOS), (x, y))
        marks.text((x+7, y+217), f"{name.replace('-', ' ')}  ·  {p*100:.0f}%",
                   fill=MUTED, font=font(14))
    root_sheet.crop((0, 0, 1582, 571)).save(OUT / "root-transfer-contact-sheet.jpg", quality=94)


if __name__ == "__main__":
    for scene in sys.argv[1:] or SCENES:
        encode(scene)
    contact_sheet()
