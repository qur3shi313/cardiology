"""Create the wrist/groin thumbnail and narrated vertical film."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import sys

import av
import numpy as np
import skia
from PIL import Image, ImageDraw


EPISODE = Path(__file__).resolve().parent
OUT = EPISODE / "delivery"
sys.path.insert(0,str(EPISODE/"visuals"))
import render_comparison as art
import comparison_editorial as editorial


W,H,FPS=1080,1920,30
TITLE="#173b34"
THUMB=OUT/"episode-02-thumbnail.png"
SHORT=OUT/"episode-02-short.mp4"
MASTER=OUT/"episode-02-1440p.mp4"
SOURCE=art.ROOT/"outputs/cardiology-series/episode-05/production/scribe.json"
OLD_MASTER=SOURCE.parent/"delivery/wrist-vs-groin-canva-export.mp4"


def draw_thumbnail():
    surface=skia.Surface(1280,720)
    c=surface.getCanvas()
    art.field(c,"forest")
    art.body(c,947,371,1.16,[("wrist",1),("groin",1)],.55)
    art.ellipse(c,920,271,65,65,"#acefc5",24)
    art.pulse(c,867,603,.25,"#d8f2cf")
    c.drawImageRect(art.logo,art.box(79,71,76,76),skia.SamplingOptions(skia.FilterMode.kLinear))
    art.words(c,"Wrist or",72,317,121,art.LIGHT,title=True)
    art.words(c,"groin?",73,453,121,"#c5efd6",title=True)
    surface.makeImageSnapshot().save(str(THUMB))


def portrait_type(c,text,y,size=38,shade=TITLE):
    font=skia.Font(art.wrist.HEADING,size)
    font.setEdging(skia.Font.kAntiAlias)
    width=font.measureText(text)
    if width>500:
        raise ValueError(f"Portrait heading too wide: {text}")
    c.drawString(text,(540-width)/2,y,font,art.solid(shade))


def portrait_base(c,heading):
    art.rectangle(c,0,0,540,960,art.gradient(0,0,540,960,["#f3faef","#e1f1e4","#9ec3b5"],[0,.56,1]))
    portrait_type(c,heading,105)


def bypass(c,t,p):
    c.save()
    c.translate(274,379)
    c.scale(.95+p*.10,.95+p*.10)
    c.translate(-330,-286)
    art.artery(c,art.anatomy.AORTA,42)
    art.shape(c,art.anatomy.MYOCARDIUM,art.gradient(184,181,484,496,["#df968b","#ac6270","#784556"]))
    for path in (art.anatomy.LEFT_MAIN,art.anatomy.LAD,art.anatomy.LCX,art.anatomy.RCA):
        art.artery(c,path,11,"#c27977")
    graft=art.curve((323,130),((385,116),(415,175),(416,229)),((418,302),(398,340),(354,368)))
    art.artery(c,graft,11,"#c3a47b")
    art.line(c,art.path_part(graft,p),"#ffebae",4.5)
    c.restore()
    art.wrist_surface(c,.83,90+32*p,486)


def curve_close(c,t,p):
    c.save()
    c.clipRect(art.box(0,144,540,658),doAntiAlias=True)
    c.translate(273,508-46*p)
    c.rotate(-90)
    c.scale(.66,.66)
    c.translate(-622,-443)
    editorial.difficult_path(c,t,p)
    c.restore()


def short_picture(c,row,index):
    j,p,t=art.beat(row,index)
    if row["id"]=="P05":
        portrait_base(c,("Larger equipment","Arterial anatomy","Bypass history")[j])
        if j==0:
            art.groin_surface(c,265+17*p,318-27*p,.77+.08*p)
            x=235+32*p
            tool=art.curve((x-190,652),((x-141,613),(x-55,577),(x+116,522)))
            art.line(c,tool,"#235e56",43)
            art.line(c,tool,"#66a494",32)
            art.line(c,tuple((a,b-6) for a,b in tool),"#d2eddd",6,184)
            art.ellipse(c,x+116,522,10,15,"#284f4b")
            editorial.pictogram(c,"heart",423,640,.82)
        elif j==1:
            curve_close(c,t,p)
        else:
            bypass(c,t,p)
    else:
        portrait_base(c,("A difficult path","Another access site","Checking both sites")[j])
        if j==0:
            curve_close(c,t,p)
        elif j==1:
            _,g,_=art.body(c,271,456,.87+p*.07,[("groin",art.easing(p,.47,1))] if p>=.47 else [],t)
            if p<.47:
                art.pulse(c,271+(525-293)*(.87+p*.07),456+(397-282)*(.87+p*.07),t)
            else:
                art.pulse(c,*g,t)
        else:
            art.wrist_surface(c,.93,77+20*p,180,pressure=.52)
            art.groin_surface(c,276-20*p,625,.72+.08*p)
            art.pulse(c,283+20*p,353,t)
            art.pulse(c,276-20*p,638,t+.39)


def plain(value):
    return re.sub(r"[^\w]","",value.casefold())


def short_captions(timeline):
    spans=timeline["short"]
    beginning=spans["start_frame"]/FPS
    ending=spans["end_frame"]/FPS
    source=json.loads(SOURCE.read_text(encoding="utf-8-sig"))["words"]
    active=[]
    offset=0
    for row in timeline["scenes"]:
        words=row["narration"].split()
        if spans["start_frame"]<=row["start_frame"]<spans["end_frame"]:
            for w,timing in zip(words,source[offset:offset+len(words)],strict=True):
                assert plain(w)==plain(timing["text"]),(w,timing)
                active.append((w,max(0,timing["start"]-beginning),min(ending-beginning,timing["end"]-beginning)))
        offset+=len(words)
    assert offset==len(source) and active
    font=skia.Font(art.wrist.BOLD,26)
    cues=[]
    first=0
    while first<len(active):
        rows=[""]
        stop=first
        while stop<len(active):
            word,_,end=active[stop]
            phrase=" ".join(filter(None,(rows[-1],word)))
            if end-active[first][1]>3.6 and stop-first>=3:
                break
            if font.measureText(phrase)>457:
                if len(rows)==2:
                    break
                rows.append(word)
            else:
                rows[-1]=phrase
            stop+=1
            if word.endswith((".","?","!")):
                break
        assert stop>first and all(0<font.measureText(line)<=457 for line in rows)
        cues.append((active[first][1],active[stop-1][2],rows))
        first=stop
    assert " ".join(" ".join(row) for _,_,row in cues)==" ".join(word for word,_,_ in active)
    return cues


def captions_on_frame(c,cues,t):
    for a,b,lines in cues:
        if a<=t<b:
            font=skia.Font(art.wrist.BOLD,26)
            font.setEdging(skia.Font.kAntiAlias)
            h=51+33*(len(lines)-1)
            art.rectangle(c,31,816-h,478,h,art.solid("#102f2e",244),10)
            for i,text in enumerate(lines):
                c.drawString(text,(540-font.measureText(text))/2,816-h+33+i*33,font,art.solid("#f9fff4"))
            return


def encode_portrait(path,timeline,cues):
    start,stop=(timeline["short"][f"{name}_frame"] for name in ("start","end"))
    rows=[s for s in timeline["scenes"] if start<=s["start_frame"]<stop]
    pixels=np.empty((H,W,4),dtype=np.uint8)
    info=skia.ImageInfo.Make(W,H,skia.ColorType.kBGRA_8888_ColorType,skia.AlphaType.kPremul_AlphaType)
    surface=skia.Surface.MakeRasterDirect(info,pixels,W*4)
    canvas=surface.getCanvas()
    canvas.scale(2,2)
    clock=Fraction(1,FPS)
    with av.open(str(path),mode="w",options={"movflags":"+faststart"}) as container:
        stream=container.add_stream("libx264",rate=FPS)
        stream.width,stream.height=W,H
        stream.pix_fmt="yuv420p"
        stream.codec_context.thread_count=2
        stream.codec_context.gop_size=60
        stream.codec_context.max_b_frames=2
        stream.options={"preset":"slow","crf":"16","profile":"high"}
        for n,frame in enumerate(range(start,stop)):
            row=next(row for row in rows if row["start_frame"]<=frame<row["end_frame"])
            short_picture(canvas,row,frame-row["start_frame"])
            captions_on_frame(canvas,cues,n/FPS)
            picture=av.VideoFrame.from_ndarray(pixels,format="bgra")
            picture.pts,picture.time_base=n,clock
            for packet in stream.encode(picture):
                container.mux(packet)
            if n and n%180==0:
                print(f"Short: {n}/{stop-start} frames",flush=True)
        for packet in stream.encode():
            container.mux(packet)


def run(ffmpeg,*args,**options):
    return subprocess.run([ffmpeg,"-hide_banner",*map(str,args)],check=True,**options)


def voice_for_short(ffmpeg,path,timeline):
    start,stop=(timeline["short"][f"{name}_frame"]/FPS for name in ("start","end"))
    recording=art.ROOT/timeline["audio_master"]["path"]
    source=["-ss",f"{start:.7f}","-t",f"{stop-start:.7f}","-i",recording,"-map","0:a:0"]
    norm="highpass=f=65,loudnorm=I=-14:TP=-1.2:LRA=7"
    first=run(ffmpeg,*source,"-af",f"{norm}:print_format=json","-f","null","-",capture_output=True,text=True)
    stats=json.loads(re.findall(r"\{[^{}]+\}",first.stderr)[-1])
    measured=":".join(f"measured_{k}={stats['input_'+k]}" for k in ("i","tp","lra","thresh"))
    run(ffmpeg,"-v","error","-y",*source,"-af",f"{norm}:{measured}:offset={stats['target_offset']}:linear=true",
        "-ac","2","-ar","48000","-c:a","aac","-b:a","320k",path)


def build_short(ffmpeg,timeline):
    cues=short_captions(timeline)
    picture=OUT/".episode-02-short-picture.mp4"
    voice=OUT/".episode-02-short-voice.m4a"
    partial=OUT/"episode-02-short.partial.mp4"
    try:
        encode_portrait(picture,timeline,cues)
        voice_for_short(ffmpeg,voice,timeline)
        run(ffmpeg,"-v","error","-y","-i",picture,"-i",voice,"-map","0:v:0","-map","1:a:0",
            "-c","copy","-metadata:s:a:0","language=eng","-movflags","+faststart",partial)
        run(ffmpeg,"-v","error","-xerror","-i",partial,"-f","null","-")
        partial.replace(SHORT)
    finally:
        for scratch in (picture,voice,partial):
            scratch.unlink(missing_ok=True)
    print(SHORT,flush=True)


def phone_sheet(ffmpeg,source,destination,width,height,step):
    filterchain=f"select=not(mod(n\\,{FPS*step})),scale={width}:{height}:flags=lanczos"
    data=run(ffmpeg,"-v","error","-threads","1","-i",source,"-map","0:v:0","-an",
             "-vf",filterchain,"-fps_mode","passthrough","-pix_fmt","rgb24","-f","rawvideo","pipe:1",
             capture_output=True).stdout
    area=width*height*3
    assert data and len(data)%area==0
    count=len(data)//area
    columns=3
    gap_x,gap_y=width+12,height+27
    sheet=Image.new("RGB",(columns*gap_x,((count+columns-1)//columns)*gap_y),"#e8f3e9")
    labels=ImageDraw.Draw(sheet)
    for n in range(count):
        x,y=n%columns*gap_x+6,n//columns*gap_y+3
        sheet.paste(Image.frombytes("RGB",(width,height),data[n*area:(n+1)*area]),(x,y))
        seconds=n*step
        labels.text((x+4,y+height+5),f"{seconds//60:02d}:{seconds%60:02d}",fill="#143b32")
    sheet.save(destination,quality=93)
    return count


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("thumbnail","short","both","before","evidence"))
    parser.add_argument("--ffmpeg")
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.action in ("thumbnail","both"):
        draw_thumbnail()
        print(THUMB,flush=True)
    if args.action in ("short","both"):
        timeline=json.loads((EPISODE/"timeline.json").read_text(encoding="utf-8-sig"))
        build_short(art.ffmpeg_path(args.ffmpeg),timeline)
    if args.action in ("before","evidence"):
        ffmpeg=art.ffmpeg_path(args.ffmpeg)
        for source,name,width,height,step in [
            (OLD_MASTER,"episode-02-before-phone.jpg",390,220,5),
            (MASTER,"episode-02-1440p-phone.jpg",390,220,5),
            (SHORT,"episode-02-short-phone.jpg",390,694,3),
        ][:1 if args.action=="before" else 3]:
            path=OUT/name
            count=phone_sheet(ffmpeg,source,path,width,height,step)
            print(f"{path} ({count} decoded samples)",flush=True)
