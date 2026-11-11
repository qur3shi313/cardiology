"""Continuous, layered arterial-access illustration for the angiography film."""
from bisect import bisect_right
from math import cos, sin, pi, hypot
import argparse
from functools import lru_cache
import json
import skia

from .__main__ import ROOT, FONTS, LEGACY_FFMPEG, WIDTH, HEIGHT, FPS, SERIES
from .encode import encode_scene

def color(s, a=255):
    s = s.strip('#')
    return skia.ColorSetARGB(max(0,min(255,a)), *(int(s[i:i+2], 16) for i in (0,2,4)))

def solid(s, a=255):
    return skia.Paint(Color=color(s,a), AntiAlias=True)

def grad(x0,y0,x1,y1,tones,stops=None):
    p=skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(x0,y0), skia.Point(x1,y1)], [color(c) for c in tones], stops))
    return p

def path(points, close=False):
    p=skia.Path()
    p.moveTo(*points[0])
    for point in points[1:]:
        p.lineTo(*point)
    if close: p.close()
    return p

def line(c, points, shade, width, opacity=255):
    if len(points)<2: return
    p=solid(shade,opacity)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(width)
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    c.drawPath(path(points),p)

def heading_face():
    face=skia.Typeface.MakeFromFile(str(FONTS/'josefin-sans-variable.ttf'))
    args=skia.FontArguments()
    coord=skia.FontArguments.VariationPosition.Coordinate(int.from_bytes(b'wght','big'),630)
    coordinates=skia.FontArguments.VariationPosition.Coordinates([coord])
    args.setVariationDesignPosition(skia.FontArguments.VariationPosition(coordinates))
    return face.makeClone(args)

HEADING=heading_face()
BOLD=skia.Typeface.MakeFromFile(str(FONTS/'fira-sans-semibold.ttf'))
REGULAR=skia.Typeface.MakeFromFile(str(FONTS/'fira-sans-regular.ttf'))
LOGO=skia.Image.open(str(ROOT/'work/company-logo-original-686.jpg'))

def text(c,s,x,y,size,shade,face=BOLD,alpha=255):
    f=skia.Font(face,size)
    f.setEdging(skia.Font.kAntiAlias)
    if x+f.measureText(s)>1260: raise ValueError(f'Text too wide: {s}')
    c.drawString(s,x,y,f,solid(shade,alpha))

def rect(c,x,y,w,h,p):
    c.drawRect(skia.Rect.MakeXYWH(x,y,w,h),p)

def center(x):
    return 454 + 11*sin((x-315)/221) + 8*cos((x-490)/300)

def tissue_top(x):
    return 299 + 16*cos((x-180)/425)

def path_y(x):
    if x<510:
        return 303+(x-329)*.88
    if x<660:
        t=(x-510)/150
        u=1-t
        return u**3*462+3*u*u*t*492+3*u*t*t*(center(660)-1)+t**3*center(660)
    return center(x)

def xy(x,offset=0):
    slope=(path_y(x+0.1)-path_y(x-0.1))/.2
    factor=hypot(slope,1)
    return x-offset*slope/factor,path_y(x)+offset/factor

def smooth(x):
    x=min(1,max(0,x))
    return x*x*(3-2*x)

def shape(c,a,b,r,shade,taper=0,offset=0,alpha=255):
    a=max(a,-125)
    if b<=a: return
    xs=[a+(b-a)*i/max(1,round((b-a)/4)) for i in range(max(1,round((b-a)/4))+1)]
    def dr(x): return r*max(.05,min(1,(b-x)/taper)) if taper else r
    pts=[xy(x,offset-dr(x)) for x in xs]+[xy(x,offset+dr(x)) for x in reversed(xs)]
    c.drawPath(path(pts,True),solid(shade,alpha))

def tube(c,a,b,r,palette,taper=0,opacity=255):
    shade,light,highlight=palette
    shape(c,a,b,r,shade,taper,alpha=opacity)
    shape(c,a+2,b-2,r*.77,light,taper,offset=-r*.09,alpha=opacity)
    shape(c,a+3,b-3,r*.16,highlight,taper,offset=-r*.53,alpha=opacity)

NEEDLE=('#395352','#9eb9b4','#edf9ee')
WIRE=('#5e4a31','#ebd49b','#fff5d6')
SHEATH=('#103e3a','#5da698','#d8eee2')
DILATOR=('#a48861','#e0d2ad','#fff4d0')
CATHETER=('#214b5f','#6ba1b1','#e1f2e8')
STAGES={
    'P04':('Locate the radial artery','Thumb side of the wrist'),
    'P05':('The access needle enters','Needle tip'),
    'P06':('The short wire passes','Short access wire'),
    'P07':('The needle comes out','Access wire stays'),
    'P08':('The sheath passes over the wire','Sheath and dilator'),
    'P09':('The sheath stays at the wrist','Open sheath tip'),
    'P10':('The diagnostic wire advances','Long guidewire'),
    'P11':('The catheter follows the wire','Diagnostic catheter'),
    'P35':('The wrist band applies pressure','Compression pad'),
    'P36':('Staff check hand circulation','Band pressure eased'),
}

def vessel(c):
    xs=range(-20,1304,6)
    silhouette=lambda edge: [(x,edge(x)) for x in xs]
    top=silhouette(tissue_top)
    bottom=silhouette(lambda x:584+14*sin(x/370))
    c.drawPath(path(top+bottom[::-1],True),
               grad(500,283,500,620,['#f4bf9f','#d38c7c','#a25460','#773642'],[0,.36,.74,1]))
    for offset,shade,width in [(7,'#f6c4a8',9),(16,'#cf8579',5),(29,'#e3a38d',12)]:
        line(c,[(x,y+offset) for x,y in top],shade,width,175)
    for r,topc,low in [(47,'#bf676d','#7a303b'),(40,'#e18f8a','#9b454d'),
                       (31,'#ab515b','#663044'),(27,'#762e43','#4b2332')]:
        pts=silhouette(lambda x:center(x)-r)+silhouette(lambda x:center(x)+r)[::-1]
        c.drawPath(path(pts,True),grad(400,408,400,512,[topc,low]))
    line(c,silhouette(lambda x:center(x)-36),'#ef9d92',2.5,175)
    line(c,silhouette(lambda x:center(x)+33),'#ce7278',2.5,130)
    # Sterile drape on either side of the small access window, with the tissue
    # rendered only as the cutaway underneath it.
    for start,end in ((-30,295),(365,1305)):
        edge=[(x,tissue_top(x)+1) for x in range(start,end+1,4)]
        drape=[(x,y-28-8*sin(x/156)) for x,y in edge]
        c.drawPath(path(drape+edge[::-1],True),
                   grad(460,260,460,331,['#43796d','#8dbaab','#3a7164']))
        line(c,edge,'#1f514b',3.5)

MOTION_DOTS=[(i*47, (i*37)%33-16, 1.9+(i%4)*.43) for i in range(28)]
def flow(c,t):
    for k,(origin,y,r) in enumerate(MOTION_DOTS):
        x=((origin+t*(73+4*(k%5)))%1330)-20
        c.drawOval(skia.Rect.MakeXYWH(x-r*2,center(x)+y-r,r*4,r*2),
                   solid('#dd8290',70+(k%5)*9))

def sheath(c, tip, dilator=None):
    h=tip-382
    tube(c,h,tip,18,SHEATH)
    tube(c,h-51,h+7,23,SHEATH)
    if dilator is not None:
        tube(c,dilator-490,dilator,10.5,DILATOR,taper=27)
    else:
        u,v=xy(tip)
        c.drawOval(skia.Rect.MakeXYWH(u-3.5,v-10,7,20),solid('#17342e'))

def callout(c, label, tx, x, y, opacity):
    f=skia.Font(BOLD,36)
    w=f.measureText(label)
    a=round(opacity*255)
    start=tx if x<tx else tx+w+26
    line(c,[(start,197),(start+(-34 if x<tx else 34),197),(x,y)],
         '#24675b',2.4,a)
    c.drawCircle(x,y,6,solid('#24675b',a))
    c.drawCircle(x,y,2.5,solid('#f4f8ee',a))
    c.drawRoundRect(skia.Rect.MakeXYWH(tx-12,168,w+25,56),10,10,solid('#e5f2ea',a))
    text(c,label,tx,207,36,'#12483e',BOLD,a)

def background(c):
    rect(c,0,0,1280,720,grad(0,0,1110,720,['#fbfcf6','#e3efe7','#b4d3c5'],[0,.65,1]))
    rect(c,0,582,1280,138,grad(0,582,1280,720,['#0f3c36','#082b29']))
    c.drawImageRect(LOGO,skia.Rect.MakeXYWH(836,27,54,54),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(c,'Elysian Biomedical LLP',904,63,32,'#004b3d')
    text(c,'RIGHT WRIST',904,106,33,'#28685a')

@lru_cache(maxsize=1)
def access_plate():
    surface=skia.Surface(WIDTH,HEIGHT)
    c=surface.getCanvas()
    c.scale(2,2)
    background(c)
    vessel(c)
    return surface.makeImageSnapshot()

def scene(c,id,p,t):
    c.drawImageRect(access_plate(),skia.Rect.MakeWH(1280,720),
                    skia.SamplingOptions(skia.FilterMode.kNearest))
    flow(c,t)
    # Screen-space choreography for the same access tract in every wrist shot.
    # Needle, short wire, sheath, and diagnostic catheter are separate layers.
    q=smooth((p-.04)/.82)
    # The rigid needle stops on the straight access track just inside the
    # lumen. Only the flexible wire and over-wire devices follow the bend.
    entry, short, stop, long = 503, 797, 631, 1196
    needle_tip, wire_tip, sheath_tip, dilator_tip, cath_tip, band = (None,)*6
    mark=(329,322)
    if id=='P04':
        # Ultrasound beam and an arterial cross-section without a diagnostic claim.
        x=348
        c.drawPath(path([(x-15,268),(x+19,268),(x+91,431),(x-28,431)],True),solid('#b1ebd6',69))
        c.drawRoundRect(skia.Rect.MakeXYWH(x-28,249,75,30),8,8,solid('#235951'))
        for ring in range(2):
            radius=8+((t*26+ring*18)%36)
            pen=solid('#e4fff0',round((37-radius)*4))
            pen.setStyle(skia.Paint.kStroke_Style); pen.setStrokeWidth(2.0)
            c.drawCircle(x+25,430,radius,pen)
        mark=(x+25,430)
    elif id=='P05':
        needle_tip=142+(entry-142)*q; mark=xy(needle_tip)
    elif id=='P06':
        needle_tip=entry; wire_tip=130+(short-130)*q; mark=xy(wire_tip)
    elif id=='P07':
        wire_tip=short; needle_tip=entry-724*q; mark=xy(wire_tip)
    elif id=='P08':
        wire_tip=short; sheath_tip=152+(stop-152)*q; dilator_tip=sheath_tip+24; mark=xy(sheath_tip)
    elif id=='P09':
        sheath_tip=stop; dilator_tip=stop+24-790*q; wire_tip=short-940*q; mark=xy(stop)
    elif id=='P10':
        sheath_tip=stop; wire_tip=96+(long-96)*q; mark=xy(wire_tip)
    elif id=='P11':
        sheath_tip=stop; wire_tip=long; cath_tip=168+907*q; mark=xy(cath_tip)
    elif id=='P35':
        band=smooth(p/.43); sheath_tip=stop-830*smooth((p-.45)/.42); mark=(329,306)
    elif id=='P36':
        band=1-.5*smooth(p/.77); mark=(329,306)
    if sheath_tip is not None: sheath(c,sheath_tip,dilator_tip)
    if cath_tip is not None: tube(c,cath_tip-1430,cath_tip,9,CATHETER,taper=11)
    if wire_tip is not None: tube(c,wire_tip-1420,wire_tip,3.6,WIRE,taper=5)
    if needle_tip is not None:
        tube(c,needle_tip-430,needle_tip,6.7,NEEDLE,taper=24)
        tube(c,needle_tip-477,needle_tip-428,13,SHEATH)
    if band is not None:
        pressure=band
        c.drawOval(skia.Rect.MakeXYWH(297,278,75,304),solid('#57b5aa',round(95+52*pressure)))
        c.drawRoundRect(skia.Rect.MakeXYWH(306,274,59,34),8,8,solid('#236c60'))
        c.drawOval(skia.Rect.MakeXYWH(309,299,53,17+10*pressure),solid('#9fe3cf',202))
    title, label=STAGES[id]
    text(c,title,49,652,47,'#effbf2',HEADING)
    if p>.13:
        callout(c,label,765 if mark[0]<710 else 618,*mark,smooth((p-.13)/.13))
    text(c,'Arterial access  /  Clinical illustration',50,690,32,'#d8eee4',REGULAR)
    text(c,'Toward the heart',921,673,32,'#d8eee4',REGULAR)
    line(c,[(1176,666),(1224,666),(1213,656)],'#a1d4c6',3)
    line(c,[(1224,666),(1213,676)],'#a1d4c6',3)

def render(ffmpeg, folder, timeline):
    folder.mkdir(parents=True,exist_ok=True)
    layer={}
    for row in timeline['scenes']:
        ident=row['id']
        if ident not in STAGES: continue
        frames=row['end_frame']-row['start_frame']
        target=folder/f'{ident}-radial-cutaway.mp4'
        temp=folder/f'{ident}-radial-cutaway.part.mp4'
        if not target.exists():
            encode_scene(temp,frames,lambda c,f:scene(c,ident,f/max(1,frames-1),(row['start_frame']+f)/FPS))
            temp.replace(target)
        layer[ident]={'path':target.relative_to(ROOT).as_posix(),'in_sec':0,'out_sec':frames/FPS,
                      'reference_only':False,'native_composition':True}
        (folder/'radial-overrides.json').write_text(json.dumps(layer,indent=2)+'\n',encoding='utf-8')
        print(f'Assembled {ident} ({frames} frames)',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ffmpeg',default=LEGACY_FFMPEG)
    args=p.parse_args()
    ep=SERIES/'episode-01'
    render(args.ffmpeg,ep/'visuals',json.loads((ep/'timeline.json').read_text(encoding='utf-8-sig')))
