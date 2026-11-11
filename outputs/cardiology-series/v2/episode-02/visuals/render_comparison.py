"""Render the native 1440p picture scenes for Wrist versus Groin Access."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import importlib.util
import json
from functools import lru_cache
from math import cos, hypot, sin
from pathlib import Path
from random import Random
import shutil
import subprocess
import sys

import skia

from tools.elysian_video import access as wrist
from tools.elysian_video.__main__ import FPS, HEIGHT, LEGACY_FFMPEG, ROOT, WIDTH
from tools.elysian_video.encode import encode_scene


OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "outputs/cardiology-series/episode-01/production/vascular_art.py"
STENT = OUT.parents[1] / "prototype/render_stent_preview.py"
INK, TEAL, JADE, PALE = "#163831", "#26685e", "#479485", "#edf8ec"
LIGHT = "#f7fff5"
RED, WARN = "#a75e67", "#802f36"
SKIN, SHADE = "#ddaf92", "#a6776b"


def local_module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anatomy = local_module("wrist_groin_geometry", SOURCE)
balloon_art = local_module("wrist_groin_balloon", STENT)
solid, gradient, line, polygon = wrist.solid, wrist.grad, wrist.line, wrist.path
curve = anatomy.curve
logo = wrist.LOGO


def box(x, y, w, h):
    return skia.Rect.MakeXYWH(x, y, w, h)


def rectangle(c, x, y, w, h, fill, radius=0):
    paint = solid(fill) if isinstance(fill, str) else fill
    if radius:
        c.drawRoundRect(box(x, y, w, h), radius, radius, paint)
    else:
        c.drawRect(box(x, y, w, h), paint)


def ellipse(c, x, y, rx, ry, fill, alpha=255):
    paint = solid(fill, alpha) if isinstance(fill, str) else fill
    c.drawOval(box(x-rx, y-ry, rx*2, ry*2), paint)


def shape(c, points, fill, edge=None, width=2):
    c.drawPath(polygon(points, True), solid(fill) if isinstance(fill, str) else fill)
    if edge:
        line(c, (*points, points[0]), edge, width)


def easing(x, a=0, b=1):
    return wrist.smooth((x-a)/(b-a))


def lerp(a, b, p):
    return a+(b-a)*p


def words(c, value, x, y, size=34, fill=INK, *, title=False, align="left", alpha=255):
    f = skia.Font(wrist.HEADING if title else wrist.BOLD, size)
    f.setEdging(skia.Font.kAntiAlias)
    width = f.measureText(value)
    x -= width/2 if align == "center" else width if align == "right" else 0
    if x < -2 or x+width > 1282:
        raise ValueError(f"Text outside frame: {value!r} at {x:.1f} ({width:.1f} wide)")
    c.drawString(value, x, y, f, solid(fill, alpha))


def brand(c, x=63, y=51, *, dark=False):
    c.drawImageRect(logo, box(x, y, 55, 55), skia.SamplingOptions(skia.FilterMode.kLinear))
    words(c, "Elysian Biomedical LLP", x+69, y+35, 26, LIGHT if dark else INK)


def note(c, label, x, y, *, dark=False, align="left"):
    font = skia.Font(wrist.BOLD, 32)
    w = font.measureText(label)
    start = x if align=="left" else x-w if align=="right" else x-w/2
    rectangle(c, start-14, y-35, w+28, 48, solid("#123e37", 235) if dark else solid("#f6fbf1", 245), 10)
    words(c, label, x, y, 32, LIGHT if dark else INK, align=align)


def marker(c, point, label, x, y, *, dark=False, align="left"):
    tone = "#e9fff1" if dark else "#28685b"
    line(c, (point, (point[0], y+12), (x, y+12)), tone, 2.4)
    ellipse(c, *point, 7, 7, tone)
    note(c, label, x, y, dark=dark, align=align)


@lru_cache(maxsize=3)
def background(tone):
    palettes = {
        "paper": ["#f8fcf2", "#e7f4e8", "#b5d4c5"],
        "forest": ["#102f30", "#23514b", "#0c2e2d"],
        "xray": ["#93a19e", "#dce1d5", "#687d7a"],
    }
    surface = skia.Surface(WIDTH, HEIGHT)
    canvas = surface.getCanvas()
    canvas.scale(2,2)
    rectangle(canvas, 0, 0, 1280, 720, gradient(0, 0, 1200, 720, palettes[tone], [0,.52,1]))
    rng = Random(27)
    for _ in range(2600):
        x, y = rng.random()*1280, rng.random()*720
        ellipse(canvas,x,y,.9,.9, "#fbfff2", rng.randrange(8,22))
    return surface.makeImageSnapshot()


def field(c, tone="paper"):
    c.drawImageRect(background(tone),box(0,0,1280,720),skia.SamplingOptions())


def beat(row, index):
    frame = row["start_frame"]+index
    for j, event in enumerate(row["visual_events"]):
        if frame < event["end_frame"]:
            return j, (frame-event["start_frame"])/max(1,event["end_frame"]-event["start_frame"]-1), index/FPS
    raise ValueError(f"Frame outside {row['id']}: {index}")


@lru_cache(maxsize=80)
def arc_lengths(points):
    lengths=[0.]
    for a,b in zip(points,points[1:]):
        lengths.append(lengths[-1]+hypot(b[0]-a[0],b[1]-a[1]))
    return tuple(lengths)


def path_part(points, f):
    if f<=0:
        return points[:1]
    if f>=1:
        return points
    lengths=arc_lengths(points)
    distance=lengths[-1]*f
    index=bisect_right(lengths,distance)-1
    a,b=points[index:index+2]
    p=(distance-lengths[index])/(lengths[index+1]-lengths[index])
    return points[:index+1]+((lerp(a[0],b[0],p),lerp(a[1],b[1],p)),)


def artery(c, pts, width, tint=RED, alpha=255):
    line(c, pts, "#693f4b", width+5, alpha)
    line(c, pts, tint, width, alpha)
    line(c, tuple((x-1.1,y-2.2) for x,y in pts), "#dc9893", max(1.5,width*.18), round(alpha*.85))


HEART = curve((288,192),((269,173),(240,179),(238,207)),((231,234),(267,257),(291,273)),
              ((318,292),(332,306),(350,278)),((377,247),(381,212),(353,202)),((337,186),(311,184),(288,192)))


def body(c, x, y, scale, routes, t, *, mask=True):
    c.save()
    c.translate(x,y)
    c.scale(scale,scale)
    c.translate(-293,-282)
    shape(c, anatomy.BODY, gradient(50,40,498,510,["#dce9e1","#b7d4c6","#8ab6a7"]), "#82ad9e", 2)
    for side in (-1,1):
        for j in range(7):
            yy=159+j*19
            ribs=curve((293,yy+18),((293+side*26,yy-3),(293+side*62,yy-13),(293+side*(83+j*.8),yy+1)))
            line(c,ribs,"#e4f3e9",2.1,112)
    if mask:
        drape=curve((170,412),((230,402),(343,405),(416,417)),((426,443),(438,492),(442,560)),
                    ((378,582),(231,581),(159,556)),((161,500),(158,456),(170,412)))
        shape(c,drape,gradient(169,410,423,550,["#9ebfb0","#67a396","#356f63"]),"#79a99a")
        for i in range(5):
            points=curve((183+i*49,430),((188+i*48,457),(183+i*48,510),(184+i*48,548)))
            line(c,points,"#c5e2d2",2.4,89)
        ellipse(c,222,483,15,12,"#e8b197")
    shape(c,HEART,gradient(250,190,361,286,["#db8982","#ad606b","#813e55"]),"#743e50")
    artery(c, anatomy.FEMORAL, 12, "#ae6871", 170)
    artery(c, anatomy.RADIAL, 9, "#ad6d74", 170)
    artery(c, anatomy.BODY_OTHER_ILIAC, 8, "#ad6d74", 110)
    for which, progress in routes:
        pts=anatomy.RADIAL if which=="wrist" else anatomy.FEMORAL
        active=path_part(pts, progress)
        line(c,active,"#206d61",14,225)
        line(c,active,"#9df1cc",5.6,255)
        if len(active)>1:
            ellipse(c,*active[-1],5.8+sin(t*5)*.7,5.8+sin(t*5)*.7,"#e9ffdc")
        ellipse(c,*pts[0],8.5,8.5,"#fff6d6")
    c.restore()
    return ((x+(60-293)*scale,y+(397-282)*scale),
            (x+(222-293)*scale,y+(483-282)*scale),
            (x+(286-293)*scale,y+(199-282)*scale))


def wrist_surface(c, scale, x, y, pressure=None, *, bruise=False, cool=False):
    c.save()
    c.translate(x,y)
    c.scale(scale,scale)
    wrist_shape=curve((-130,173),((34,155),(152,138),(234,151)),((278,130),(328,77),(348,89)),
        ((365,99),(334,149),(329,166)),((373,164),(446,134),(461,152)),
        ((466,164),(425,182),(384,193)),((430,178),(482,179),(484,194)),
        ((489,206),(434,220),(394,225)),((448,216),(471,222),(469,235)),
        ((464,248),(416,252),(381,254)),((408,253),(429,263),(421,275)),
        ((411,290),(369,285),(335,292)),((292,310),(251,289),(222,279)),
        ((151,293),(33,304),(-133,295)))
    tones=["#f6d7bd","#d2a18b","#ba8377"] if not cool else ["#eed6c7","#d6bcb4","#bb9e9d"]
    shape(c,wrist_shape,gradient(70,120,210,303,tones),SHADE,2.5)
    shape(c,curve((-140,167),((-39,146),(52,149),(124,148)),((131,183),(136,242),(126,292)),
                    ((49,303),(-35,308),(-140,303))),gradient(-100,153,135,303,["#9dc5b6","#5d9d8f","#36766c"]),"#608c80")
    artery(c,curve((164,190),((203,187),(225,184),(270,169)),((293,158),(310,150),(323,148))),8,"#ad6571",190)
    if bruise:
        for j in range(5):
            ellipse(c,221,184,17+j*1.7,12+j*.8,"#8b596f",23)
    ellipse(c,221,184,5.2,5.2,"#fff5da",220)
    if pressure is not None:
        rectangle(c,205,150,29,134,solid("#398b80",142),9)
        rectangle(c,198,152,44,24,"#2f7c71",8)
        ellipse(c,220,173,19,7+5*pressure,"#96d9c3")
    c.restore()


def groin_surface(c,x,y,scale, *, bruise=False):
    c.save()
    c.translate(x,y)
    c.scale(scale,scale)
    edge=curve((-268,25),((-199,-122),(-104,-141),(130,-122)),((271,-117),(337,-34),(335,91)),
               ((318,190),(225,233),(71,239)),((-96,232),(-249,192),(-268,25)))
    shape(c,edge,gradient(-270,-142,330,246,["#a8cdbb","#588f80","#2e6860"]),"#5b9989")
    for i in range(8):
        a=-224+i*65
        line(c,curve((a,-91),((a+12,-9),(a-22,138),(a+19,196))),"#a8cfba",2.8,95)
    ellipse(c,0,17,45,33,"#22564b")
    ellipse(c,0,17,39,27,gradient(-40,-10,30,42,["#f0c4a3","#c28a76"]))
    if bruise:
        for i in range(4):
            ellipse(c,0,17,14+i*2,8+i*1.3,"#865267",29)
    else:
        line(c,((-15,34),(-5,17),(2,-4)),"#9b5d67",6,180)
    c.restore()


def pulse(c,x,y,t,tone=JADE):
    r=14+16*(t%1.3)/1.3
    paint=solid(tone,round(150*(1-(t%1.3)/1.3)))
    paint.setStrokeWidth(2)
    paint.setStyle(skia.Paint.kStroke_Style)
    c.drawCircle(x,y,r,paint)
    ellipse(c,x,y,5,5,tone)


def p01(c, row, n):
    j,p,t=beat(row,n)
    field(c)
    if j==2:
        wrist_surface(c,1.3+p*.12,26+p*46,93,pressure=.52)
        groin_surface(c,970-p*28,353,1.05+p*.14)
        pulse(c,313+p*30,361,t)
        pulse(c,970-p*28,371,t+.28)
        note(c,"The choice can affect recovery",640,661,align="center")
        return
    a=easing(t,0,4.5)
    b=easing(t,.65,5.0)
    scale=.91+t*.0134
    body(c,330+t*1.3,395,scale,[("wrist",a)],t)
    body(c,954-t*1.3,395,scale,[("groin",b)],t)
    if t<5:
        words(c,"Wrist or groin?",640,86,68,INK,title=True,align="center")
    else:
        words(c,"Wrist versus groin access",640,66,50,INK,title=True,align="center")
        words(c,"Why the team chooses a route",640,105,30,TEAL,align="center")
    note(c,"Right wrist",302,659,align="center")
    note(c,"Right groin",1000,659,align="center")


def p02(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j==0:
        c.save()
        c.translate(0,lerp(68,5,p))
        wrist_surface(c,2.2,105,44)
        c.restore()
        marker(c,(591,449+lerp(68,5,p)),"Radial artery",880,205)
    elif j==1:
        scale=1.82+p*.24
        x=616+p*48
        y=367-p*49
        groin_surface(c,x,y,scale)
        point=(x,y+17*scale)
        marker(c,point,"Common femoral artery",725,180)
        pulse(c,*point,t)
    else:
        a=easing(p,0,.53)
        b=easing(p,.43,1)
        scale=.98+p*.11
        left=body(c,315+p*20,381-p*44,scale,[("wrist",a)],t)
        right=body(c,965-p*20,381-p*44,scale,[("groin",b)],t)
        pulse(c,*left[2],t)
        pulse(c,*right[2],t+.25)
        note(c,"Both routes reach the aortic root",640,678,align="center")


def xray(c,t,p):
    field(c,"xray")
    for j in range(9):
        for side in (-1,1):
            y=91+j*67
            pts=curve((646,y+33),((640+side*193,y-80),(641+side*411,y-85),(640+side*640,y-10)))
            line(c,pts,"#eaf0e3",12-j*.75,69)
    c.save()
    c.translate(353+18*sin(t*.85),-32+5*cos(t))
    c.scale(2.45,2.46)
    for i,(pts,width) in enumerate(anatomy.ANGIO_LEFT):
        offset=0 if i==0 else .16 if i<3 else .38
        fraction=easing(p,offset,min(1,offset+.57))
        part=path_part(pts,fraction)
        line(c,part,"#354341",width+3,150)
        line(c,part,"#1c2829",width,255)
        line(c,tuple((x-.5,y-.8) for x,y in part),"#72807a",max(1,width*.19),154)
    c.restore()
    note(c,"Simulated angiogram",65,669,dark=True)


def treatment(c,t,p,place=False):
    field(c,"forest")
    c.save()
    zoom=1.12 if place else 1+.12*p
    c.translate(640,392)
    c.scale(zoom,zoom)
    c.translate(-640,-392)
    advance=easing(p,.02,.40)
    inflation=easing(p,.42,.62)
    deflation=easing(p,.67,.80)
    withdraw=easing(p,.84,.98)
    expansion=inflation*.88 if place else 0
    balloon_x=lerp(-232,balloon_art.LESION,advance)-withdraw*1050
    radius=11+98*inflation*(1-deflation)
    lumen=balloon_art.artery(c,expansion)
    state=balloon_art.Motion(1130,balloon_x,radius,0,0,expansion,
                            .8-.7*inflation*(1-deflation) if place else .8)
    balloon_art.blood_flow(c,t,state,lumen)
    if place:
        balloon_art.wire(c,lerp(1125,180,withdraw))
        if balloon_x+balloon_art.BALLOON_HALF>-90:
            balloon_art.balloon(c,balloon_x,radius)
    else:
        balloon_art.wire(c,lerp(-50,1125,p))
    c.restore()
    note(c,"PCI treatment example",57,104,dark=True)
    if place:
        note(c,"Balloon opens a narrowing",1220,675,dark=True,align="right")


def p03(c,row,n):
    j,p,t=beat(row,n)
    if j==0:
        xray(c,t,easing(p,0,.70))
    elif j==1:
        treatment(c,t,p)
    elif j==2:
        treatment(c,t,p,True)
    else:
        field(c)
        scale=.96+p*.14
        left=body(c,329+p*12,391-p*37,scale,[("wrist",easing(p,0,.82))],t)
        body(c,951-p*12,391-p*37,scale,[] if j==4 else [("groin",easing(p,.14,1))],t)
        if j==4:
            pulse(c,*left[0],t)
        note(c,"Wrist access is common when suitable" if j==4 else "Either arterial route can be used",
             640,672,align="center")


def glove(c,x,y,scale,side=1):
    c.save()
    c.translate(x,y)
    c.scale(scale*side,scale)
    points=curve((-165,-5),((-113,-36),(-84,-58),(-55,-48)),((-34,-61),(-17,-64),(7,-53)),
        ((48,-45),(90,-36),(128,-36)),((158,-37),(174,-23),(161,-12)),
        ((151,0),(117,1),(105,1)),((137,1),(164,10),(153,23)),
        ((141,35),(87,32),(79,34)),((104,41),(102,52),(82,54)),
        ((49,54),(10,47),(-6,50)),((-71,59),(-106,49),(-164,43)))
    shape(c,points,gradient(-10,-62,10,62,["#b8e0cc","#73b9a7","#318274"]),"#276d62",2.4)
    c.restore()


FEMORAL_MAIN = curve((160,496),((341,482),(502,498),(657,487)),
                     ((833,478),(978,468),(1135,437)))
FEMORAL_BRANCH = curve((455,489),((402,500),(354,522),(291,555)),
                       ((234,586),(203,598),(171,605)))


def femoral_closure(c,t,p):
    rectangle(c,0,184,1280,450,gradient(0,188,1270,620,["#a9ccbb","#6aa89a","#2f7165"]))
    for i in range(10):
        x=i*147-30
        line(c,curve((x,186),((x+18,299),(x-14,477),(x+25,625))),"#c9e3d1",2.8,80)
    window=skia.RRect.MakeRectXY(box(84,246,1114,367),65,65)
    c.drawRRect(window,solid("#3e7060"))
    c.save()
    c.clipRRect(window,doAntiAlias=True)
    rectangle(c,84,260,1114,364,gradient(84,259,1110,590,["#e5b799","#d18e7e","#8e555a"]))
    border=curve((80,366),((330,349),(566,371),(818,353)),((944,344),(1072,345),(1199,328)))
    lower=(*border,(1201,619),(80,620))
    shape(c,lower,gradient(86,355,1190,619,["#cd8c79","#ab6a68","#754350"]))
    line(c,border,"#f7c9a5",5,188)
    artery(c,FEMORAL_BRANCH,35,"#985765")
    artery(c,FEMORAL_MAIN,62,"#bd7379")
    line(c,FEMORAL_MAIN,"#6c3548",42)
    for i in range(29):
        dot=path_part(FEMORAL_MAIN,((t*.093+i*.074)%1))[-1]
        ellipse(c,dot[0],dot[1]+((i*19)%30-15),5.4,2.8,"#e88c86",129)
    c.restore()
    if p<.60:
        pressure=easing(p,0,.57)
        glove(c,768,272-58*(1-pressure),1.11,-1)
        return (612,291),"Firm hand pressure"
    stitch=curve((598,455),((595,430),(615,424),(628,450)),
                 ((630,465),(616,469),(607,452)))
    line(c,path_part(stitch,easing(p,.60,.96)),"#f7d391",5.5)
    ellipse(c,607,452,4.7,4.7,"#ffe2b4")
    return (608,449),"Closure stitch example"


def p07(c,row,n):
    j,p,t=beat(row,n)
    field(c)
    if j<2:
        c.save()
        c.translate(0,-173)
        c.scale(1,1.48)
        wrist.vessel(c)
        wrist.flow(c,t)
        pressure=easing(p,.02,.85) if j==0 else 1-.58*easing(p)
        ellipse(c,334,432,37,153,"#5bbaa7",round(72+62*pressure))
        rectangle(c,306,270,58,37,"#276c60",8)
        ellipse(c,334,304,25,6+13*pressure,"#a0ddc9")
        if j==1:
            glove(c,279,263-28*easing(p,0,.4),.48,-1)
        c.restore()
        marker(c,(334,282),"Wrist pressure band" if j==0 else "Site and hand checks",455,168)
        return
    if j==2:
        target,label=femoral_closure(c,t,p)
        marker(c,target,label,420,128)
        return
    wrist_surface(c,1.31+.17*p,1+34*p,117,pressure=.43)
    groin_surface(c,963-27*p,359,.85+.12*p)
    pulse(c,291+70*p,362,t)
    pulse(c,963-27*p,372,t+.32)
    note(c,"Staff check both sites for bleeding",640,665,align="center")


CORE = {"P01":p01,"P02":p02,"P03":p03,"P07":p07}


def ffmpeg_path(value):
    if value:
        return value
    return shutil.which("ffmpeg") or str(LEGACY_FFMPEG)


def render(rows, selected, ffmpeg, still_only=False, replace=False):
    overlay=CORE.copy()
    if any(id not in CORE for id in selected):
        overlay.update(local_module("wrist_groin_editorial",OUT/"comparison_editorial.py").SCENES)
    lookup={row["id"]:row for row in rows}
    for id in selected:
        row=lookup[id]
        draw=overlay[id]
        frames=row["duration_frames"]
        if still_only:
            surface=skia.Surface(WIDTH,HEIGHT)
            canvas=surface.getCanvas()
            canvas.scale(2,2)
            for index in range(0,frames,max(1,frames//8)):
                draw(canvas,row,index)
                surface.makeImageSnapshot().save(str(OUT/f"{id}-{index:04}.png"))
            continue
        target=OUT/f"{id}.mp4"
        temp=OUT/f"{id}.partial.mp4"
        if replace or not target.is_file():
            def draw_current(canvas,index):
                draw(canvas,row,index)
                if index and index%150==0:
                    print(f"{id}: drawing {index}/{frames}",flush=True)
            encode_scene(temp,frames,draw_current,preset="fast",threads=2)
            subprocess.run([ffmpeg,"-v","error","-threads","1","-xerror","-i",str(temp),"-f","null","-"],check=True)
            temp.replace(target)
        override={id:{"path":target.relative_to(ROOT).as_posix(),"in_sec":0,"out_sec":frames/FPS,
                      "native_composition":True,"reference_only":False}}
        path=OUT/f"{id.lower()}-overrides.json"
        path.write_text(json.dumps(override,indent=2)+"\n",encoding="utf-8")
        print(f"{id}: {frames} frames ready",flush=True)


if __name__=="__main__":
    sys.modules.setdefault("render_comparison",sys.modules[__name__])
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenes",nargs="*")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--still-only",action="store_true")
    parser.add_argument("--replace",action="store_true")
    args=parser.parse_args()
    timeline=json.loads((OUT.parent/"timeline.json").read_text(encoding="utf-8-sig"))
    render(timeline["scenes"],args.scenes or [r["id"] for r in timeline["scenes"]],
           ffmpeg_path(args.ffmpeg),args.still_only,args.replace)
