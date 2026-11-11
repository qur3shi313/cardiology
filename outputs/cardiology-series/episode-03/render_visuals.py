"""Render the original silent 1080p visuals for Episode 03."""

from functools import lru_cache
from math import cos, exp, pi, sin
from pathlib import Path
import json
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / 'episode-01' / 'revision'))
from render_editorial_cards import DEEP, INK, LINE, MUTED, ROOT, font, gradient, heart, write
sys.path.insert(0, str(HERE.parent / 'episode-01' / 'revision' / 'radial-route-scenes'))
from render_radial_scenes import composite, plate, wrist_band

W, H = 1920, 1080
OUT = HERE / 'visuals'
FFMPEG = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
ASSET = ROOT / 'work/company-logo-original-686.jpg'
PANEL = (70, 290, 1850, 928)
X0, X1, CENTER = 188, 1732, 960
CORAL, OCHRE, JADE, SAGE = '#b06e6c', '#d5a27e', '#2b8f74', '#bde8c9'


def smooth(value):
    t = min(1., max(0., value))
    return t*t*(3.-2.*t)


def phase(time, start, stop):
    return smooth((time-start)/(stop-start))


def blend(a, b, t):
    return tuple(round(x+(y-x)*t) for x, y in zip(a, b))


def text(draw, x, y, value, size, kind='body', color=INK, maxwidth=None):
    write(draw, x, y, value, size, kind, color, maxwidth)


def panel(draw, box, fill='#f8fcf8', outline='#c7dace'):
    draw.rounded_rectangle(box, 32, fill=fill, outline=outline, width=2)


def label(draw, x, y, value, color=DEEP, fill='#e2f0e6'):
    width = draw.textlength(value, font=font(27, 'bold'))
    draw.rounded_rectangle((x,y,x+width+38,y+49), 12, fill=fill)
    text(draw, x+19, y+10, value, 27, 'bold', color)


def leader(draw, origin, target):
    x, y = origin
    tx, ty = target
    draw.line((x,y,tx,y,tx,ty),fill='#476c60',width=3,joint='curve')
    draw.ellipse((tx-5,ty-5,tx+5,ty+5),fill='#fafff4',outline='#476c60',width=3)


@lru_cache(maxsize=15)
def base(title, takeaway):
    image = gradient((249, 252, 248), (226, 240, 231)).copy()
    draw = ImageDraw.Draw(image)
    logo = Image.open(ASSET).convert('RGB').resize((75, 75), Image.Resampling.LANCZOS)
    image.paste(logo, (68, 41))
    text(draw, 162, 49, 'Elysian Biomedical LLP', 33, 'bold', DEEP)
    text(draw, 164, 88, 'Cardiology Education Series', 24, 'body', MUTED)
    draw.text((1848, 51), 'EPISODE 03', fill=DEEP, font=font(27,'bold'), anchor='rt')
    draw.line((69,137,1850,137),fill=LINE,width=2)
    text(draw, 69, 174, title, 72, 'title')
    draw.line((69,968,1850,968),fill=LINE,width=2)
    text(draw, 69, 992, takeaway, 33, 'bold', DEEP)
    return image


def center(x):
    return 604+11*sin((x-430)/265)+8*sin((x-190)/550)


def tissue(x):
    return exp(-abs((x-CENTER)/208)**3.0)


def edge(x, side, expanded):
    growth = tissue(x)*(70 if side < 0 else 49)*(1-.67*expanded)
    return center(x)+side*(99-growth)


def envelope(draw, upper, lower, color):
    draw.polygon(upper+lower[::-1],fill=color)


def metal(draw):
    for side in (-1,1):
        for x in range(565, 1356, 61):
            nodes=[(x,center(x)+side*98),(x+31,center(x+31)+side*74),(x+61,center(x+61)+side*98)]
            draw.line(nodes,fill='#3e5962',width=10,joint='curve')
            draw.line(nodes,fill='#c7e1df',width=4,joint='curve')
        for x in (565, 1356):
            y=center(x)
            draw.arc((x-15,y-98,x+15,y+98),90,270,fill='#d1e5df',width=5)


@lru_cache(maxsize=25)
def anatomy(step):
    expanded=step/24
    image=Image.new('RGBA',(W,388))
    draw=ImageDraw.Draw(image)
    xs=list(range(X0,X1+1,4))
    middle=lambda x:center(x)-415
    for i in range(40):
        radius=141-i*1.15
        top=[(x,middle(x)-radius) for x in xs]
        bottom=[(x,middle(x)+radius) for x in xs]
        envelope(draw,top,bottom,blend((184,112,107),(118,59,73),i/39))
    draw.line([(x,middle(x)-141) for x in xs],fill='#cf8a80',width=4,joint='curve')
    draw.line([(x,middle(x)+141) for x in xs],fill='#955964',width=4,joint='curve')
    for i in range(30):
        radius=99-i*2.45
        envelope(draw,[(x,middle(x)-radius) for x in xs],[(x,middle(x)+radius) for x in xs],
                 blend((114,45,64),(166,80,84),i/29))
    view=Image.new('RGBA',(W,H))
    view.paste(image,(0,415))
    draw=ImageDraw.Draw(view)
    metal(draw)
    for side in (-1,1):
        band=list(range(681,1241,4))
        outer=[(x,center(x)+side*(98+2*tissue(x))) for x in band]
        inner=[(x,edge(x,side,expanded)) for x in band]
        envelope(draw,outer,inner,'#d5a286' if side<0 else '#bf866e')
        draw.line(inner,fill='#e9bfa4',width=3,joint='curve')
        for x in range(725, 1198, 23):
            thickness=abs(edge(x,side,expanded)-center(x)-side*99)
            y=edge(x,side,expanded)+side*thickness*.40
            draw.ellipse((x-2,y-2,x+2,y+2),fill='#9f6c62')
    return view.crop((0,415,W,803))


def vessel(image, expanded):
    layer=anatomy(round(24*max(0,min(1,expanded))))
    image.paste(layer,(0,415),layer)


def wire(draw, tip):
    points=[(x,center(x)-9*phase(x,tip-57,tip)) for x in range(X0,round(tip)+1,4)]
    if len(points)>1:
        draw.line(points,fill='#48343b',width=7,joint='curve')
        draw.line(points,fill='#f4d39a',width=4,joint='curve')


def balloon(image, at, inflation, coated):
    left,right=at-146,at+146
    if right<=X0:
        return
    draw=ImageDraw.Draw(image,'RGBA')
    xs=list(range(max(X0,round(left)),min(X1,round(right))+1,3))
    shaft=[(x,center(x)) for x in range(X0,min(X1,round(right))+1,3)]
    draw.line(shaft,fill='#2c6269',width=16,joint='curve')
    draw.line(shaft,fill='#b4dee0',width=10,joint='curve')
    if len(xs)<2:
        return
    upper=[]
    lower=[]
    expansion=(.88+.12*inflation) if coated else inflation*.88
    for x in xs:
        shape=phase(x,left,left+54)*phase(x,right,right-54)
        y=center(x)
        top=4+(abs(edge(x,-1,expansion)-y)-4)*inflation*shape
        bottom=4+(abs(edge(x,1,expansion)-y)-4)*inflation*shape
        upper.append((x,y-top))
        lower.append((x,y+bottom))
    envelope(draw,upper,lower,(157,219,191,193) if coated else (170,222,232,188))
    outline='#357f5c' if coated else '#4f8399'
    draw.line(upper,fill=outline,width=4,joint='curve')
    draw.line(lower,fill=outline,width=4,joint='curve')
    for x in (at-101,at+101):
        if X0<x<X1:
            y=center(x)
            draw.line((x,y-8,x,y+8),fill='#eef5ed',width=5)
    if coated:
        for group in (upper,lower):
            for x,y in group[7::8]:
                draw.ellipse((x-3,y-3,x+3,y+3),fill='#d1f2ae',outline='#247c56',width=1)


def deposit(draw, amount, expanded=1):
    if amount<=0:
        return
    for i,x in enumerate(range(850,1075,13)):
        for side in (-1,1):
            depth=7+amount*(8+(i%3)*3)
            y=edge(x,side,expanded)+side*depth
            size=2+amount*(2+(i%2)*2)
            draw.ellipse((x-size,y-size,x+size,y+size),fill='#a5d483' if i%2 else '#6baf71')


def section(image, name, expanded, tip=None, device=None, transfer=0):
    draw=ImageDraw.Draw(image)
    panel(draw,PANEL)
    label(draw,102,317,name)
    vessel(image,expanded)
    draw=ImageDraw.Draw(image)
    if tip is not None:
        wire(draw,tip)
    if device:
        balloon(image,*device)
    deposit(draw,transfer,expanded)
    return draw


def xray(draw, box, name, progress, expanded):
    x0,y0,x1,y1=box
    panel(draw,box,'#e9eeee','#bbcfca')
    text(draw,x0+31,y0+26,name,33,'bold',DEEP)
    px=x0+62
    py=y0+266
    width=x1-x0-130
    for i in range(4):
        cy=py+(i-1.5)*20
        draw.line((px,cy,x1-68,cy),fill='#dbe4e3',width=1)
    pts=[]
    for x in range(round(px),round(px+width),3):
        u=(x-px)/width
        y=py-27*sin(u*2.5)+19*sin(u*8.1)
        pts.append((x,y))
    branches=[(pts[int(len(pts)*.72)],(x1-105,py-99)),(pts[int(len(pts)*.61)],(x1-205,py+130))]
    for a,b in branches:
        draw.line((a,(a[0]+38,(a[1]+b[1])/2),b),fill='#cad6d5',width=10,joint='curve')
    count=max(2,round(len(pts)*progress))
    for i,(a,b) in enumerate(zip(pts[:count],pts[1:count])):
        u=i/(len(pts)-1)
        squeeze=exp(-abs((u-.51)/.091)**3)
        pen=round(21-15*squeeze*(1-.76*expanded))
        draw.line((a,b),fill='#34464a',width=pen)
        draw.ellipse((a[0]-pen/2,a[1]-pen/2,a[0]+pen/2,a[1]+pen/2),fill='#34464a')
    for i,(a,b) in enumerate(branches):
        if progress>(.74 if i==0 else .64):
            draw.line((a,(a[0]+38,(a[1]+b[1])/2),b),fill='#35474b',width=8,joint='curve')
    n=pts[int(len(pts)*.51)]
    draw.ellipse((n[0]-36,n[1]-36,n[0]+36,n[1]+36),outline='#598679',width=3)


def mini(draw, box, title, collapsed=False, new=False):
    x0,y0,x1,y1=box
    panel(draw,box)
    text(draw,x0+35,y0+35,title,41,'title')
    yy=(y0+y1)//2+40
    xx0,xx1=x0+60,x1-60
    draw.rounded_rectangle((xx0,yy-87,xx1,yy+87),43,fill='#ba7774')
    if collapsed:
        midpoint=(xx0+xx1)//2
        xs=list(range(xx0,xx1+1,3))
        radius=lambda x:51-26*exp(-abs((x-midpoint)/100)**2)
        envelope(draw,[(x,yy-radius(x)) for x in xs],[(x,yy+radius(x)) for x in xs],'#78384d')
    else:
        draw.rounded_rectangle((xx0,yy-51,xx1,yy+51),25,fill='#78384d')
    if not new:
        mid=(xx0+xx1)//2
        for side in (-1,1):
            nodes=[]
            for i,x in enumerate(range(xx0+52,xx1-50,19)):
                dent=26*exp(-abs((x-mid)/100)**2) if collapsed else 0
                nodes.append((x,yy+side*(49-dent-11*(i%2))))
            draw.line(nodes,fill='#c8dedc',width=5,joint='curve')
        if not collapsed:
            draw.ellipse((mid-94,yy-47,mid+91,yy+1),fill='#d4a388')
            draw.ellipse((mid-73,yy+11,mid+80,yy+48),fill='#c59079')
    else:
        mid=(xx0+xx1)//2
        draw.ellipse((mid-86,yy-50,mid+82,yy+2),fill='#d4a388')


@lru_cache(maxsize=1)
def opener():
    image=base('Coronary drug-coated balloons','A treatment option when an artery narrows inside a stent').copy()
    draw=ImageDraw.Draw(image)
    panel(draw,PANEL)
    heart(image,218,309,1.15)
    draw=ImageDraw.Draw(image)
    draw.ellipse((425,568,465,608),outline='#f6f9db',width=5)
    text(draw,900,427,'Inside a previously\nstented artery',61,'title',DEEP)
    text(draw,903,622,'Coronary in-stent restenosis',35,'body',MUTED)
    return image


@lru_cache(maxsize=1)
def wrist_recovery_inset():
    layer=Image.new('RGBA',(1600,900))
    wrist_band(ImageDraw.Draw(layer),0,1)
    return composite(plate(21,True),layer).crop((227,361,1092,730)).resize((654,279),Image.Resampling.LANCZOS)


def frame(id,t):
    if id=='P01':
        if t<5:
            return opener()
        else:
            image=base('Coronary drug-coated balloons','A treatment option when an artery narrows inside a stent').copy()
            draw=section(image,'Coronary artery cutaway',0)
            text(draw,1137,395,'Original stent',30,'bold',DEEP)
            leader(draw,(1260,444),(1275,512))
            text(draw,650,800,'Tissue narrows the open channel',35,'bold',DEEP)
            leader(draw,(935,796),(935,648))
    elif id=='P02':
        image=base('Why a stented artery can narrow','In-stent restenosis means the artery has narrowed again').copy()
        if t<15:
            draw=section(image,'In-stent tissue growth',0)
            text(draw,618,801,'The original stent remains in the artery wall',35,'bold',DEEP)
            leader(draw,(804,792),(740,518))
        else:
            draw=ImageDraw.Draw(image)
            mini(draw,(70,290,944,928),'Tissue growth inside a stent')
            mini(draw,(974,290,1850,928),'A stent that opened incompletely',True)
            text(draw,111,818,'The example in this episode',31,'bold',DEEP)
            text(draw,1014,818,'A separate cause',31,'bold',DEEP)
    elif id=='P03':
        image=base('Imaging and the guidewire','A coronary guidewire crosses the narrowing').copy()
        if t<12:
            draw=ImageDraw.Draw(image)
            xray(draw,(70,290,1270,928),'Simulated coronary angiogram',phase(t,0.4,4.5),0)
            panel(draw,(1300,290,1850,928))
            text(draw,1338,326,'Inside the artery',35,'title')
            if t>5:
                draw.ellipse((1412,425,1738,751),fill='#a47b77',outline='#764d51',width=7)
                draw.ellipse((1457,470,1693,706),fill='#6c374a',outline='#cbab97',width=17)
                draw.ellipse((1512,503,1685,704),fill='#cc9f83')
                draw.ellipse((1521,552,1633,678),fill='#3c2b39')
                for a in range(0,360,30):
                    q=a*pi/180;x=1575+112*cos(q);y=588+112*sin(q)
                    draw.ellipse((x-4,y-4,x+4,y+4),fill='#e5ece5')
                text(draw,1338,816,'Illustrative cross-section',26,'body',MUTED)
        else:
            tip=X0+(1470-X0)*phase(t,12.7,20.9)
            draw=section(image,'Coronary guidewire',0,tip)
            if t>20.9:
                text(draw,1150,800,'Wire tip beyond the narrowing',30,'bold',DEEP)
                leader(draw,(1415,796),(1460,601))
    elif id=='P04':
        image=base('Preparing the narrowed segment','The first balloon prepares the area for treatment').copy()
        infl=phase(t,7.5,10.5)*(1-phase(t,13.4,15.5))
        at=42+(CENTER-42)*phase(t,1.7,6.8)-(CENTER-42)*phase(t,16.3,19.8)
        expanded=max(infl*.88,.88*phase(t,7.5,10.5))
        state='Preparation balloon' if t<19.8 else 'Prepared channel'
        draw=section(image,state,expanded,1470,(at,infl,False))
        line='The guidewire stays in place' if t>=15.5 else 'A separate balloon opens the narrowed channel'
        text(draw,105,820,line,34,'bold',DEEP)
    elif id=='P05':
        image=base('How the coating delivers medicine','The outside coating transfers medicine at the treatment site').copy()
        infl=phase(t,8.8,13.4)
        at=42+(CENTER-42)*phase(t,1.7,7.2)
        expanded=.88+.12*infl
        draw=section(image,'Drug-coated balloon',expanded,1470,(at,infl,True),phase(t,14,20))
        if t>=8:
            text(draw,101,819,'Medicine coating',31,'bold',DEEP)
            leader(draw,(390,826),(885,edge(885,1,expanded)-2 if t>=13.4 else center(885)+7))
        if t>=16:
            text(draw,1103,818,'Local transfer into the tissue',31,'bold',DEEP)
            leader(draw,(1416,807),(1021,edge(1021,1,expanded)+16))
    elif id=='P06':
        image=base('Balloon out and final check','The team checks the treated area and downstream flow').copy()
        if t<10.3:
            infl=1-phase(t,.5,3.8)
            at=CENTER-(CENTER-42)*phase(t,4.1,8.2)
            draw=section(image,'Coated balloon withdrawal' if t<8.2 else 'Original stent remains',1,1470,(at,infl,True),1)
            text(draw,103,820,'The original stent stays in the artery',34,'bold',DEEP)
        else:
            draw=ImageDraw.Draw(image)
            xray(draw,(70,290,945,928),'Before treatment',1,0)
            xray(draw,(975,290,1850,928),'After treatment',phase(t,10.6,14.5),1)
            text(draw,110,821,'Simulated angiograms',29,'body',MUTED)
            text(draw,1016,821,'Wider channel in this example',29,'bold',DEEP)
    elif id=='P07':
        image=base('Where drug-coated balloons are used','Approved uses vary by country and device').copy()
        draw=ImageDraw.Draw(image)
        mini(draw,(70,290,944,928),'In-stent restenosis')
        mini(draw,(974,290,1850,928),'Previously unstented vessels',new=True)
        text(draw,108,783,'An option for selected cases',35,'bold',DEEP)
        text(draw,110,837,'U.S. approval example · 2024',26,'body',MUTED)
        text(draw,1014,783,'Studied in selected small vessels',35,'bold',DEEP)
        text(draw,1016,837,'Clinical research',26,'body',MUTED)
    elif id=='P08':
        image=base('Recovery and the medicine plan','Follow your cardiology team’s discharge instructions').copy()
        draw=ImageDraw.Draw(image)
        panel(draw,(70,290,808,928))
        label(draw,102,317,'Access-site care')
        image.paste(wrist_recovery_inset(),(110,470))
        text(draw,131,778,'Wrist compression band',33,'bold',DEEP)
        panel(draw,(838,290,1850,928))
        if t<19.5:
            text(draw,887,360,'Your discharge plan',48,'title')
            text(draw,887,478,'Take antiplatelet medicines as prescribed.',35,'bold',DEEP,845)
            text(draw,887,638,'Ask your cardiology team before\nchanging your medicines.',33,'body',MUTED)
        else:
            text(draw,887,360,'When to get emergency help',48,'title')
            text(draw,887,497,'Severe or persistent chest pain',37,'bold',DEEP)
            draw.line((887,575,1795,575),fill=LINE,width=2)
            text(draw,887,634,'Bleeding that won’t stop',37,'bold',DEEP)
    elif id=='P09':
        image=base('What stays in the artery','The coated balloon comes out. The original stent stays.').copy()
        draw=section(image,'Treated artery cutaway',1,transfer=1)
        text(draw,110,815,'The team uses the final images to guide next steps',34,'bold',DEEP)
    else:
        image=base('Clinical references','Full references are in the video description.').copy()
        draw=ImageDraw.Draw(image)
        panel(draw,PANEL)
        text(draw,115,347,'FDA approval record · 2024',46,'title')
        text(draw,115,426,'SCAI consensus on in-stent restenosis · 2023',39,'body',INK)
        text(draw,115,496,'DCB Academic Research Consortium position statement · 2025',39,'body',INK)
        text(draw,115,566,'Guy’s and St Thomas’ NHS recovery guidance · 2026',39,'body',INK)
        draw.line((115,650,1795,650),fill=LINE,width=2)
        text(draw,115,701,'Original animation with simulated angiograms',35,'bold',DEEP)
        text(draw,115,764,'Synthetic English narration',35,'body',MUTED)
    return image


def render(scene):
    id=scene['id']
    seconds=scene['target_end_sec']-scene['target_start_sec']
    rate=24 if id in ('P03','P04','P05','P06') else 2
    outfile=OUT/f'{id}.mp4'
    command=[str(FFMPEG),'-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
             '-framerate',str(rate),'-i','pipe:0','-an','-vf','fps=24','-c:v','libx264','-preset','veryfast',
             '-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(outfile)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        for i in range(seconds*rate):
            encoder.stdin.write(frame(id,i/rate).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError(f'Encoding failed for {id}')
    print(f'{id} {seconds}s {outfile.stat().st_size} bytes',flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    scenes=json.loads((HERE/'scenes.json').read_text(encoding='utf-8'))
    for scene in scenes:
        if len(sys.argv)==1 or scene['id'] in sys.argv[1:]:
            render(scene)
