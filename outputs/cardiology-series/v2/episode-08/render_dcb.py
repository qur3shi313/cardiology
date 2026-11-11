"""Create the continuous picture sequence for coronary drug-coated balloons."""

from argparse import ArgumentParser
from bisect import bisect_right
from functools import lru_cache
import json
from math import cos, pi, sin
from pathlib import Path

import skia

from tools.elysian_video import access, angiogram, stent
from tools.elysian_video.__main__ import FPS, HEIGHT, ROOT, WIDTH
from tools.elysian_video.encode import encode_scene


EPISODE = Path(__file__).resolve().parent
VISUALS = EPISODE/'visuals'
DARK, GREEN, LIGHT = '#123c36', '#004b3d', '#f2fcf2'
CREAM = '#fff0cd'
CENTER = stent.LESION
X0, X1 = -85, 1365
XS = range(X0,X1+1,8)
PREPARED, TREATED = .56, .68
RADIUS = 111
solid, gradient, line, polygon = access.solid, access.grad, access.line, access.path
curve = angiogram.art.curve


def ease(p,start,end):
    return access.smooth((p-start)/(end-start))


def mix(a,b,p):
    return a+(b-a)*p


def box(x,y,w,h):
    return skia.Rect.MakeXYWH(x,y,w,h)


def block(c,x,y,w,h,r,tone):
    brush = solid(tone) if isinstance(tone,str) else tone
    c.drawRoundRect(box(x,y,w,h),r,r,brush)


def ellipse(c,x,y,rx,ry,tone,alpha=255):
    brush=solid(tone,alpha) if isinstance(tone,str) else tone
    c.drawOval(box(x-rx,y-ry,rx*2,ry*2),brush)


def text(c,label,x,y,size=30,tone=GREEN,*,heading=False):
    font=skia.Font(access.HEADING if heading else access.BOLD,size)
    font.setEdging(skia.Font.kAntiAlias)
    if x<0 or x+font.measureText(label)>1277:
        raise ValueError(f'Label does not fit: {label}')
    c.drawString(label,x,y,font,solid(tone))


def title(c,label,*,dark=False):
    c.drawImageRect(access.LOGO,box(53,29,51,51),skia.SamplingOptions(skia.FilterMode.kLinear))
    tone=LIGHT if dark else GREEN
    text(c,'Elysian Biomedical LLP',120,63,27,tone)
    text(c,label,54,139,48,tone,heading=True)


def tag(c,label,x=54,y=665,*,dark=False):
    w=skia.Font(access.BOLD,30).measureText(label)
    shade=solid(DARK,246) if dark else solid('#f4fbf1',247)
    block(c,x-12,y-35,w+24,49,9,shade)
    text(c,label,x,y,30,LIGHT if dark else GREEN)


def marker(c,label,x,y,target):
    tx,ty=target
    w=skia.Font(access.BOLD,30).measureText(label)
    start=x-12 if tx<x else x+w+12
    elbow=start-28 if tx<x else start+28
    line(c,[(start,y-13),(elbow,y-13),(tx,ty)],'#1b5e50',2.6)
    ellipse(c,tx,ty,5,5,'#174b42')
    ellipse(c,tx,ty,2.4,2.4,CREAM)
    tag(c,label,x,y)


def snapshot(draw):
    surface=skia.Surface(WIDTH,HEIGHT)
    canvas=surface.getCanvas()
    canvas.scale(2,2)
    draw(canvas)
    return surface.makeImageSnapshot()


def paint_image(c,image,*,scale=1,centre=(CENTER,392)):
    c.save()
    if scale!=1:
        x,y=centre
        c.translate(x*(1-scale),y*(1-scale))
        c.scale(scale,scale)
    c.drawImageRect(image,box(0,0,1280,720),skia.SamplingOptions(
        skia.FilterMode.kNearest if scale==1 else skia.FilterMode.kLinear))
    c.restore()


@lru_cache(maxsize=2)
def field(dark=False):
    colors=['#122d2a','#1f4e45','#102925'] if dark else ['#f9fcf2','#deede3','#a6c8b9']
    return snapshot(lambda c:c.drawRect(box(0,0,1280,720),
                                        gradient(80,0,1125,720,colors)))


@lru_cache(maxsize=3)
def vessel_plate(case):
    def draw(c):
        paint_image(c,field())
        stent.artery(c,1)
        if case=='underexpanded':
            narrowed_mesh(c)
        elif case=='expanded':
            stent.stent(c,CENTER,113,False)
            stent.stent(c,CENTER,113,True)
    return snapshot(draw)


def narrowed_mesh(c):
    """A separately labelled example of focal stent underexpansion."""
    rings=[]
    for i in range(11):
        x=CENTER-158+31.6*i
        ring=[]
        for j in range(17):
            theta=(j+(i%2)*.5)*pi/8
            at=x+(-1)**j*9
            radius=113-44*stent.plaque(at)
            ring.append((at,stent.center(at)+radius*sin(theta),theta))
        rings.append(ring)
    for i,ring in enumerate(rings):
        for a,b in zip(ring,ring[1:]):
            front=cos((a[2]+b[2])*.5)>=0
            line(c,[a[:2],b[:2]],'#41454c' if front else '#778c87',5.7 if front else 2.3)
            if front:
                line(c,[a[:2],b[:2]],'#d9e1d6',3.0)
        if i+1<len(rings):
            for j in (0,4,8,12):
                line(c,[ring[j][:2],rings[i+1][j][:2]],'#b0beb0',2.5,198)


def lumen_radius(x,gain):
    scar=stent.plaque(x)
    return RADIUS-62*scar*(1-gain)


def scar_tissue(c,gain):
    xs=list(range(CENTER-182,CENTER+183,6))
    for side,palette in ((-1,['#e8a490','#ce7e79','#a85766']),
                         (1,['#e6a392','#c27678','#965465'])):
        inner=[(x,stent.center(x)+side*lumen_radius(x,gain)) for x in xs]
        rim=[(x,stent.center(x)+side*RADIUS) for x in xs]
        region=stent.enclosed(inner,rim)
        y=stent.center(CENTER)
        c.drawPath(region,gradient(CENTER-63,y+side*65,CENTER+62,y+side*RADIUS,palette))
        line(c,inner,'#ffd0a7',2.8,192)


def blood(c,t,gain,slow):
    for j in range(26):
        x=(j*81+t*(53+(j%5)*5)*slow)%1350-22
        q=((j*37)%119-59)/64
        y=stent.center(x)+q*lumen_radius(x,gain)
        ellipse(c,x,y,5.5+j%3,1.8+j%2*.4,'#ed9a8c',69+j%4*10)


def coated_balloon(c,x,radius,coated):
    left,right=x-171,x+171
    if right<=X0:
        return
    shaft=[(at,stent.center(at)) for at in range(X0,round(right)+1,8)]
    line(c,shaft,'#224e55',13)
    line(c,shaft,'#8ebcbc',7)
    line(c,shaft,'#c9e7d6',2.0)
    xs=list(range(round(left),round(right)+1,6))
    outline=lambda at:4+(radius-4)*ease(at,left,left+40)*ease(right-at,0,40)
    upper=[(at,stent.center(at)-outline(at)) for at in xs]
    lower=[(at,stent.center(at)+outline(at)) for at in xs]
    y=stent.center(x)
    brush=gradient(x,y-radius,x,y+radius,['#9bcbbb','#538e8a','#a7e0d3'] if coated
                   else ['#d4f2ed','#79afb4','#b2d9d5'])
    c.drawPath(stent.enclosed(upper,lower),brush)
    line(c,upper,'#9ef1c8' if coated else '#e5f7ee',3.8 if coated else 2.5)
    line(c,lower,'#45a889' if coated else '#4d8b92',3.3 if coated else 2.5)
    if coated:
        for at in range(round(left+51),round(right-47),21):
            for side in (-1,1):
                ellipse(c,at,stent.center(at)+side*outline(at),3.3,2.4,'#e1f4a8',229)


def transfer(c,t,gain,amount):
    if amount<=0:
        return
    for i in range(24):
        x=CENTER-85+(i*29)%170
        p=(t*.48+i*.111)%1
        side=-1 if i%2 else 1
        y=stent.center(x)+side*(lumen_radius(x,gain)+13*p)
        ellipse(c,x,y,2.6,2.6,'#d9e9a4',round(172*(1-p)*amount))


def cutaway(c,t,gain,*,case='expanded',wire=None,balloon=None,drug=0,zoom=1):
    c.save()
    if zoom!=1:
        c.translate(CENTER*(1-zoom),388*(1-zoom))
        c.scale(zoom,zoom)
    paint_image(c,vessel_plate(case))
    scar_tissue(c,gain)
    blood(c,t,gain,.18 if balloon and balloon[1]>62 else 1)
    if wire is not None:
        stent.wire(c,wire)
    if balloon:
        coated_balloon(c,*balloon)
    transfer(c,t,gain,drug)
    c.restore()


def zoomed(x,y,scale):
    return CENTER+(x-CENTER)*scale,388+(y-388)*scale


def contrast(c,p,t,*,wider=False,label=None):
    paint_image(c,angiogram.radiograph_plate())
    branches,total=angiogram.tree('left')
    distance=ease(p,0,.45)*total
    alpha=round(246*(1-ease(p,.74,.99)))
    for i,(points,lengths,entry,thickness) in enumerate(branches):
        visible=distance-entry
        if visible<=0:
            continue
        limit=min(len(points),max(2,bisect_right(lengths,visible)))
        mapped=[(222+3.48*x,101+1.88*y) for x,y in points[:limit]]
        if i==1:
            for j,(a,b) in enumerate(zip(mapped,mapped[1:])):
                q=j/(len(points)-1)
                stenosis=max(0,1-abs(q-.47)/.09)
                width=max(2.4,thickness*2.18*(1-.48*q)*(1-(.23 if wider else .68)*stenosis))
                line(c,[a,b],'#222828',width,alpha)
        else:
            line(c,mapped,'#1b2725',max(2.7,thickness*1.85),alpha)
    root=branches[0][0][0]
    x,y=222+3.48*root[0],101+1.88*root[1]
    guide=curve((x-150,146),((x-104,143),(x-57,y-22),(x,y)))
    line(c,guide,'#535d58',4.5,209)
    text(c,'Simulated coronary X-ray',54,69,31,LIGHT)
    if label:
        tag(c,label,dark=True)


@lru_cache(maxsize=1)
def heart_plate():
    def draw(c):
        paint_image(c,field())
        heart=curve((657,233),((589,155),(453,134),(398,254)),((333,380),(509,537),(667,602)),
                    ((784,631),(900,506),(920,397)),((954,280),(820,208),(760,224)),
                    ((711,226),(688,221),(657,233)))
        c.drawPath(polygon(heart,True),gradient(413,187,907,605,['#e7a29b','#b96e75','#7b4057']))
        root=curve((672,247),((693,204),(688,167),(697,135)),((718,88),(764,100),(795,131)))
        line(c,root,'#9c4d64',67)
        line(c,root,'#d78884',53)
        line(c,root,'#eda79c',10)
    return snapshot(draw)


def heart(c,p,t):
    paint_image(c,heart_plate())
    branch=curve((675,240),((643,267),(624,310),(644,341)),((661,383),(691,427),(703,510)))
    second=curve((638,300),((589,292),(544,321),(509,373)),((485,405),(457,432),(443,452)))
    for points in (branch,second):
        line(c,points,'#85465a',16)
        line(c,angiogram.art.trace(points,ease(p,0,.87)),'#f3c4a3',8)
    title(c,'Coronary arteries supply the heart')
    marker(c,'Coronary artery',910,329,(650,344))


@lru_cache(maxsize=1)
def inside_plate():
    def draw(c):
        paint_image(c,field(True))
        cx,cy=680,392
        for r,shade in ((212,'#a5747d'),(191,'#e0a291'),(173,'#8f5362'),(138,'#263133')):
            ellipse(c,cx,cy,r,r,shade)
        for i in range(16):
            theta=2*pi*i/16
            ellipse(c,cx+165*cos(theta),cy+165*sin(theta),5.1,5.1,'#dfd7c9')
        plaque=curve((550,357),((569,298),(611,273),(670,266)),((697,296),(673,334),(632,361)),
                     ((587,395),(589,418),(564,428)))
        c.drawPath(polygon(plaque,True),gradient(554,275,689,420,['#dbad94','#9b6262','#724c50']))
        title(c,'A view from inside the artery',dark=True)
        tag(c,'Illustrated cross-section',dark=True)
    return snapshot(draw)


def inside(c,p,t):
    paint_image(c,inside_plate())
    a=t*2.4
    line(c,[(680,392),(680+129*cos(a),392+129*sin(a))],'#b6dfc9',3.7,151)
    ellipse(c,680,392,19,19,'#9bbaaf')
    ellipse(c,680,392,10,10,'#203833')


def hook(c,p,t):
    if p>.81:
        contrast(c,(p-.81)/.19,t,label='The team checks the blood flow')
        return
    zoom=1+.12*ease(p,0,.36)
    cutaway(c,t,0,zoom=zoom)
    if p>.28:
        title(c,'Coronary drug-coated balloons')
    marker(c,'Original stent',825,222,zoomed(763,stent.center(763)-113,zoom))
    tag(c,'Narrowing inside a stent')


def narrowing(c,p,t):
    if p<.18:
        heart(c,p/.18,t)
    elif p<.61:
        zoom=1+.12*ease(p,.21,.59)
        cutaway(c,t,0,zoom=zoom)
        title(c,'In-stent restenosis')
        marker(c,'Tissue narrows the channel',765,222,zoomed(CENTER,stent.center(CENTER)-54,zoom))
    else:
        alternate=p<.81
        cutaway(c,t,.28 if alternate else 0,case='underexpanded' if alternate else 'expanded')
        title(c,'A separate cause' if alternate else 'Why the cause matters')
        tag(c,'The stent opened incompletely' if alternate else 'The findings guide treatment')


def imaging_and_wire(c,p,t):
    if p<.25:
        contrast(c,p/.25,t,label='Narrowing in the treated segment')
    elif p<.55:
        inside(c,(p-.25)/.30,t)
    else:
        tip=mix(-44,1171,ease(p,.57,.91))
        cutaway(c,t,0,wire=tip if tip>X0 else None)
        title(c,'The guidewire crosses the narrowing')
        if tip>320:
            marker(c,'Guidewire tip',842,213,(tip,stent.center(tip)-9))


def preparation(c,p,t):
    advance=ease(p,.16,.31)
    inflate=ease(p,.31,.46)
    collapse=ease(p,.47,.55)
    retract=ease(p,.55,.65)
    position=mix(-260,CENTER,advance)-858*retract
    radius=mix(9,83,inflate*(1-collapse))
    cutaway(c,t,PREPARED*inflate,wire=1171,
            balloon=(position,radius,False) if position+171>X0 else None,
            zoom=1+.09*ease(p,.72,.99))
    title(c,'Prepare the narrowed segment')
    if p<.64:
        tag(c,'Plain preparation balloon')
    else:
        tag(c,'The guidewire stays in place')


def delivery(c,p,t):
    advance=ease(p,.03,.20)
    inflation=ease(p,.35,.65)
    position=mix(-258,CENTER,advance)
    radius=mix(10,91,inflation)
    gain=mix(PREPARED,TREATED,inflation)
    cutaway(c,t,gain,wire=1171,balloon=(position,radius,True),
            drug=ease(p,.64,.76))
    title(c,'How the balloon coating delivers medicine')
    if .20<p<.35:
        marker(c,'Medicine on the outside',801,216,(CENTER+96,stent.center(CENTER+96)-radius))
    else:
        tag(c,'Coated balloon' if p<.35 else 'Contact with the wall' if p<.64 else 'Local medicine transfer')


def final_check(c,p,t):
    if p<.35:
        collapse=ease(p,.01,.085)
        pull=ease(p,.085,.18)
        position=CENTER-879*pull
        cutaway(c,t,TREATED,wire=1171,
                balloon=(position,mix(91,9,collapse),True) if position+171>X0 else None)
        title(c,'The original stent stays')
        tag(c,'The balloon comes out')
    elif p<.53:
        contrast(c,(p-.35)/.18,t,label='Before treatment')
    elif p<.78:
        contrast(c,(p-.53)/.25,t,wider=True,label='After treatment · Same view')
    else:
        cutaway(c,t,TREATED,zoom=1+.12*ease(p,.78,1))
        title(c,'The final images guide the next step')
        tag(c,'The team checks the opening and flow')


def selection(c,p,t):
    if p<.56:
        cutaway(c,t,TREATED,zoom=1+.10*ease(p,0,.50))
        title(c,'Selected cases of in-stent restenosis')
        tag(c,'US FDA approval example · 2024' if p>.23 else 'An original stent remains')
    elif p<.86:
        cutaway(c,t,.11,case='unstented',zoom=1+.12*ease(p,.56,.85))
        title(c,'A separate small-vessel study')
        tag(c,'Research in selected previously unstented vessels')
    else:
        paint_image(c,field())
        title(c,'Approved uses vary')
        ellipse(c,646,393,194,176,gradient(460,234,818,529,['#c4e5d3','#83baa9','#4d9083']))
        for i in range(4):
            xs=range(470,825,12)
            line(c,[(x,300+i*59+(1-((x-646)/194)**2)*15) for x in xs],'#e2f5de',2.5,177)
        for width in (52,111,168):
            path=[(646+width*cos(pi*k/22),393+174*sin(pi*k/22)) for k in range(45)]
            line(c,path,'#ddf4db',2.5,156)
        text(c,'By country and device',54,661,33,GREEN)


@lru_cache(maxsize=1)
def recovery_plate():
    def draw(c):
        paint_image(c,field())
        block(c,117,430,1041,69,27,'#a1bcaf')
        block(c,150,495,946,94,15,'#6a9c8b')
        block(c,207,339,283,106,48,'#e8f0e6')
        ellipse(c,386,378,76,61,'#74a397')
        torso=curve((435,363),((514,348),(631,370),(676,393)),((740,410),(877,395),(1049,408)),
                     ((1121,415),(1122,474),(1042,480)),((804,478),(602,470),(433,452)))
        c.drawPath(polygon(torso,True),gradient(429,351,1048,489,['#bddbd0','#70ae9e','#3e8174']))
        for x in (543,629,713,797,883,970):
            line(c,[(x,401),(x-17,467)],'#b5ded0',3,128)
        block(c,832,197,229,149,13,'#28544e')
        block(c,843,208,207,128,9,'#426e61')
        block(c,931,344,23,60,7,'#688f82')
    return snapshot(draw)


def recovery(c,p,t):
    if p<.34:
        paint_image(c,recovery_plate())
        title(c,'The team monitors recovery')
        path=curve((861,269),((881,269),(889,271),(906,269)),((914,268),(922,242),(931,251)),
                   ((941,272),(950,286),(961,270)),((976,262),(997,275),(1029,270)))
        line(c,angiogram.art.trace(path,.36+.64*ease(p,0,.29)),'#e4f8d6',4)
        tag(c,'Access-site and circulation checks')
    elif p<.76:
        paint_image(c,field())
        title(c,'Follow your own discharge instructions')
        angiogram.icon(c,'list',ease(p,.34,.73),t)
        text(c,'Medicine plan',54,341,39,GREEN,heading=True)
        text(c,'Ask before changing medicines',54,413,31,GREEN)
    else:
        paint_image(c,field(True))
        title(c,'Get emergency help',dark=True)
        text(c,'Severe or persistent chest pain',55,337,42,LIGHT)
        text(c,'Bleeding that won’t stop',55,414,42,LIGHT)
        line(c,[(55,477),(55+568*ease(p,.77,1),477)],'#83c4ad',5)


def recap(c,p,t):
    if p<.69:
        zoom=1+.17*ease(p,.13,.64)
        cutaway(c,t,TREATED,zoom=zoom)
        title(c,'What stays in the artery?')
        marker(c,'Original stent',841,224,zoomed(767,stent.center(767)-113,zoom))
        tag(c,'The balloon has been removed')
    else:
        contrast(c,(p-.69)/.31,t,wider=True,label='Final images guide the next step')


@lru_cache(maxsize=1)
def source_plate():
    def draw(c):
        paint_image(c,field(True))
        title(c,'Cardiology Education Series',dark=True)
        text(c,'Clinical sources',54,240,39,LIGHT)
        text(c,'SCAI · US FDA · BASKET-SMALL 2 · NHS',54,296,29,'#c5ebd6')
        text(c,'Original animation · Simulated imaging · Synthetic narration',54,346,27,'#c5ebd6')
        text(c,'Next episode',54,459,34,LIGHT)
        text(c,'Why a stent can narrow again',54,516,42,'#c5ebd6',heading=True)
    return snapshot(draw)


def credits(c,p,t):
    paint_image(c,source_plate())
    line(c,[(54,556),(54+559*ease(p,.03,.95),556)],'#88c9b0',3)


PICTURES=(hook,narrowing,imaging_and_wire,preparation,delivery,final_check,
          selection,recovery,recap,credits)


def thumbnail():
    surface=skia.Surface(1280,720)
    c=surface.getCanvas()
    paint_image(c,field())
    c.save()
    c.translate(0,60)
    cutaway(c,1.1,TREATED,wire=1169,balloon=(CENTER,91,True),drug=.8)
    c.restore()
    c.drawImageRect(access.LOGO,box(56,22,45,45),skia.SamplingOptions(skia.FilterMode.kLinear))
    text(c,'Elysian Biomedical LLP',117,53,27,GREEN)
    text(c,'Coronary drug-coated',57,131,79,GREEN,heading=True)
    text(c,'balloons',57,207,88,GREEN,heading=True)
    surface.makeImageSnapshot().save(str(EPISODE/'thumbnail.png'))


def render(indices,force):
    VISUALS.mkdir(exist_ok=True)
    timeline=json.loads((EPISODE/'timeline.json').read_text(encoding='utf-8-sig'))
    overrides={}
    for index,row in enumerate(timeline['scenes'],1):
        ident=row['id']
        frames=row['end_frame']-row['start_frame']
        out=VISUALS/f'{ident}-dcb.mp4'
        if index in indices and (force or not out.exists()):
            temp=out.with_suffix('.part.mp4')
            def frame(canvas,i):
                PICTURES[index-1](canvas,i/max(frames-1,1),i/FPS)
            encode_scene(temp,frames,frame,preset='fast',threads=2)
            temp.replace(out)
            print(f'{ident} encoded {frames} frames',flush=True)
        if out.exists():
            overrides[ident]={'path':out.relative_to(ROOT).as_posix(),'in_sec':0,
                              'out_sec':frames/FPS,'native_composition':True}
    (VISUALS/'dcb-overrides.json').write_text(json.dumps(overrides,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('pictures',nargs='*',type=int)
    parser.add_argument('--force',action='store_true')
    parser.add_argument('--thumbnail',action='store_true')
    args=parser.parse_args()
    ids=args.pictures or list(range(1,len(PICTURES)+1))
    if any(not 1<=i<=len(PICTURES) for i in ids):
        parser.error('Choose scene numbers from 1 to 10')
    if args.thumbnail:
        thumbnail()
    else:
        render(ids,args.force)
