"""Render original long-axis aortic valve cutaways for the TAVI episode."""
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
import json
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / 'episode-01' / 'revision'))
from render_editorial_cards import DEEP, INK, LINE, MUTED, ROOT, font, gradient, heart, write

FFMPEG = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
OUT = HERE / 'visuals'
W, H = 1920, 1080
CENTER, ANNULUS = 1270, 648
TISSUE, EDGE, CALCIUM, FLOW = '#df9c99', '#a96065', '#fff0c5', '#287c73'


def phase(t, start, end):
    fraction = min(1., max(0., (t-start)/(end-start)))
    return fraction*fraction*(3-2*fraction)


def beat(t):
    return max(0., sin((t % 2.65)/2.65*2*pi))**.65


def curve(*points, steps=28):
    a,b,c,d=points
    def xy(t,k):
        r=1-t
        return r**3*a[k]+3*r*r*t*b[k]+3*r*t*t*c[k]+t**3*d[k]
    return [(xy(i/steps,0),xy(i/steps,1)) for i in range(steps+1)]


def line(draw, points, fill, width):
    draw.line(points,fill=fill,width=width,joint='curve')


def arrow(draw, x, y, size=16, color=FLOW):
    line(draw,[(x,y+size*1.7),(x,y)],color,max(2,size//3))
    draw.polygon([(x,y-2),(x-size,y+size),(x+size,y+size)],fill=color)


def tag(draw, x, y, label):
    length=draw.textlength(label,font=font(27,'bold'))
    draw.rounded_rectangle((x,y,x+length+40,y+52),radius=12,fill='#dceee3')
    write(draw,x+20,y+11,label,27,'bold',DEEP)


def panel(draw, rect):
    draw.rounded_rectangle(rect,31,fill='#f8fcf8',outline=LINE,width=2)


@lru_cache(maxsize=18)
def base(title, takeaway):
    im=gradient((249,252,248),(226,240,231)).copy()
    logo=Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGB').resize((75,75),Image.Resampling.LANCZOS)
    im.paste(logo,(68,41))
    d=ImageDraw.Draw(im)
    write(d,162,49,'Elysian Biomedical LLP',33,'bold',DEEP)
    write(d,164,88,'Cardiology Education Series',24,'body',MUTED)
    d.text((1848,51),'EPISODE 04',fill=DEEP,font=font(27,'bold'),anchor='rt')
    d.line((69,137,1850,137),fill=LINE,width=2)
    write(d,69,177,title,70,'title')
    panel(d,(70,290,665,928))
    panel(d,(693,290,1850,928))
    d.line((69,968,1850,968),fill=LINE,width=2)
    write(d,69,992,takeaway,32,'bold',DEEP)
    return im


def side(d, label, title, copy):
    tag(d,109,326,label)
    used=write(d,108,426,title,55,'title',DEEP,504)
    write(d,110,447+used,copy,37,'body',INK,485)


@lru_cache(maxsize=1)
def root_cutaway():
    im=Image.new('RGBA',(W,H))
    d=ImageDraw.Draw(im)
    left=curve((1082,365),(1086,436),(1075,477),(1052,515))
    left+=curve((1052,515),(1007,583),(1033,618),(1110,648))
    left+=curve((1110,648),(1115,688),(1070,752),(1031,824))
    right=[(CENTER*2-x,y) for x,y in left]
    shape=left+right[::-1]
    shadow=Image.new('RGBA',im.size)
    ImageDraw.Draw(shadow).polygon([(x+6,y+8) for x,y in shape],fill=(117,68,69,70))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    d.polygon(shape,fill='#f8ded8')
    for wall,sign in [(left,-1),(right,1)]:
        line(d,wall,'#a45b62',39)
        line(d,wall,TISSUE,29)
        line(d,[(x-sign*6,y) for x,y in wall],'#f4b6a9',8)
    for sign in (-1,1):
        x=CENTER+sign*211
        branch=curve((x,511),(x+sign*39,487),(x+sign*89,492),(x+sign*131,458))
        line(d,branch,EDGE,20)
        line(d,branch,'#e6a49d',13)
        d.ellipse((x-10,499,x+10,522),fill='#92535d',outline='#f3c2b4',width=3)
    d.line((1081,824,1459,824),fill='#edb4ad',width=3)
    return im


def leaflet(d, sign, position, narrowed, installed, device_radius=0):
    center=CENTER
    start_x=center+sign*(112 if installed else 159)
    extent=round((35 if narrowed else 99)*position)
    if device_radius:
        extent=max(extent,device_radius+4)
        position=max(position,phase(extent,20,130))
    tip_x=center+sign*extent
    tip_y=ANNULUS-18-round((87 if narrowed else 120)*position)
    cusp=curve((start_x,ANNULUS),(start_x-sign*12,ANNULUS-12),
               (tip_x+sign*37,tip_y+52),(tip_x,tip_y))
    line(d,cusp,'#96676c',20)
    line(d,cusp,'#e6bbab' if narrowed else '#f9e9cd',12)
    line(d,[(x,y-3) for x,y in cusp],'#fff1d9',3)
    if narrowed:
        for index, radius in ((5,13),(10,18),(16,15),(21,10)):
            x,y=cusp[index]
            d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=CALCIUM,outline='#b58b73',width=3)


def frame_mesh(d, half_width, y):
    for level in range(4):
        y0=y-87+level*46
        for sign in (-1,1):
            x=CENTER+sign*half_width
            offset=sign*max(4,round(half_width*.16))
            strut=[(x,y0),(x-offset,y0+22),(x,y0+46)]
            line(d,strut,'#495961',10)
            line(d,[(a-1,b-2) for a,b in strut],'#c3d3d5',4)
    for y0 in (y-87,y+97):
        d.arc((CENTER-half_width,y0-11,CENTER+half_width,y0+11),0,180,fill='#7c9396',width=5)


def wire(d, withdrawal=0.):
    path=curve((1457,366),(1310,403),(1280,499),(CENTER,586))
    path+=curve((CENTER,586),(1268,675),(1256,735),(1294,807))
    path=path[:round(len(path)*(1-withdrawal))]
    if len(path)<2:
        return
    line(d,path,'#6c7779',5)
    line(d,[(x-1,y-1) for x,y in path],'#fff9e1',2)


def delivery(d, center_y, radius):
    path=curve((1457,366),(1325,410),(1285,max(405,center_y-161)),(CENTER,center_y-86))
    line(d,path,'#587786',16)
    line(d,[(x-2,y-2) for x,y in path],'#a5cbce',6)
    outline=(CENTER-radius,center_y-91,CENTER+radius,center_y+102)
    d.rounded_rectangle(outline,max(2,min(radius,32)),fill='#bad8dd',outline='#5b8f9d',width=3)
    line(d,[(CENTER,center_y-87),(CENTER,center_y+98)],'#86acb5',4)


def flow(d, t, narrow=False):
    width=12 if narrow else 35
    for i in range(4):
        y=784-(((t*.72+i/4)%1)*384)
        arrow(d,CENTER+(i%2*2-1)*width,y,10 if narrow else 14)


def cutaway(im, t, state, y=620, size=0., hardware=False, moving_valve=True):
    layer=root_cutaway()
    im.paste(layer,(0,0),layer)
    d=ImageDraw.Draw(im)
    tag(d,723,317,'Aortic valve cutaway')
    write(d,1552,415,'Aorta',34,'bold',MUTED)
    write(d,1544,781,'Left ventricle',34,'bold',MUTED)
    write(d,727,477,'Coronary opening',28,'body',MUTED)
    line(d,[(726,514),(984,514),(1053,510)],'#55756b',3)
    if state in ('old','device'):
        for sign in (-1,1):
            occupied=round(21+109*size) if hardware and y>=570 else 0
            leaflet(d,sign,beat(t),True,False,occupied)
    if hardware:
        wire(d)
        delivery(d,y,round(13+110*size))
        frame_mesh(d,round(21+109*size),y)
    if state=='implanted':
        for sign in (-1,1):
            x=CENTER+sign*143
            folded=curve((x,648),(x-sign*2,617),(x-sign*13,556),(x+sign*4,532))
            line(d,folded,EDGE,15)
            for vx,vy in folded[8::7]:
                d.ellipse((vx-8,vy-8,vx+8,vy+8),fill=CALCIUM,outline='#b58b73',width=2)
        frame_mesh(d,130,620)
        for sign in (-1,1):
            leaflet(d,sign,beat(t) if moving_valve else 0.,False,True)
    if not hardware and moving_valve and beat(t)>.38:
        flow(d,t,state=='old')
    return d


@lru_cache(maxsize=1)
def opening_heart():
    im=Image.new('RGB',(W,H),'#f8fcf8')
    heart(im,923,323,1.28)
    return im.crop((695,315,1848,917))


def image_for(scene,t):
    if scene=='P01':
        im=base('A new valve through a catheter','Transcatheter aortic valve implantation').copy()
        if t<6:
            im.paste(opening_heart(),(695,315))
            d=ImageDraw.Draw(im)
            d.ellipse((1122,548,1154,580),outline=DEEP,width=5)
            line(d,[(1154,564),(1441,564),(1492,445)],DEEP,4)
            write(d,1500,408,'Aortic valve',34,'bold',DEEP)
            for i in range(3):
                progress=(t*.67+i/3)%1
                arrow(d,1138+round(14*progress**3),550-round(117*progress),8)
        else:
            d=cutaway(im,t,'old')
        side(d,'TAVI / TAVR','A new valve','A replacement valve is placed inside the narrowed aortic valve.')
        return im
    if scene=='P02':
        im=base('Why the aortic valve narrows','Calcium can stiffen the valve’s leaflets').copy()
        d=cutaway(im,t,'old')
        side(d,'AORTIC STENOSIS','Less room for blood to flow','Stiff leaflets open less when the heart pumps.')
        d.ellipse((127,686,292,851),fill='#e8b7b0',outline='#a96065',width=5)
        gap=round(15+50*beat(t))
        d.ellipse((210-gap,768-gap,210+gap,768+gap),fill='#f8fcf8',outline='#a96065',width=4)
        write(d,312,739,'Healthy valve',30,'bold',DEEP)
        write(d,313,779,'Opening in one beat',23,'body',MUTED)
        return im
    if scene=='P05':
        im=base('How the new valve travels','The delivery system moves over the guidewire').copy()
        y=round(493+127*phase(t,8,16))
        d=cutaway(im,t,'device',y=y,hardware=t>=5)
        side(d,'DELIVERY SYSTEM','Valve on a folded balloon','Tissue leaflets sit inside a metal frame. The frame travels compressed.')
        if t<5:
            d.rounded_rectangle((1480,542,1817,719),23,fill='#e3eee9',outline=LINE,width=2)
            d.ellipse((1511,565,1634,685),fill='#e0b5a5',outline='#61787e',width=8)
            for i in range(3):
                angle=pi*.5+2*pi*i/3
                x,y0=1572+54*cos(angle),625-54*sin(angle)
                line(d,[(1572,625),(x,y0)],'#fff1d7',8)
            write(d,1661,579,'Tissue\nleaflets',27,'bold',DEEP)
        return im
    if scene=='P06':
        im=base('Opening the replacement valve','The expanded frame stays at the original valve opening').copy()
        if t<11.8:
            expansion=phase(t,1.8,8.6)
            d=cutaway(im,t,'device',y=620,size=expansion,hardware=True)
            side(d,'BALLOON EXPANSION','The frame opens','The balloon expands the metal frame and presses the old leaflets aside.')
        else:
            d=cutaway(im,t,'implanted',moving_valve=t>=19)
            if t<19:
                devices=Image.new('RGBA',(W,H))
                device_draw=ImageDraw.Draw(devices)
                wire(device_draw,phase(t,16.8,18.7))
                center=round(620-386*phase(t,14,18.5))
                if center+102>366:
                    delivery(device_draw,center,round(10+112*(1-phase(t,11.8,14))))
                visible=devices.crop((0,366,W,H))
                im.paste(visible,(0,366),visible)
                side(d,'DELIVERY SYSTEM OUT','The balloon deflates','The team withdraws the delivery system. The expanded frame remains seated.')
            else:
                side(d,'IMPLANTED VALVE','The new leaflets move','The tissue leaflets open as the heart pumps and close between beats.')
        return im
    if scene=='P07':
        im=base('Checking the result','The team checks the valve, heart rhythm and access site').copy()
        d=cutaway(im,t,'implanted')
        if t<10.7:
            side(d,'IMAGING','Check flow and valve function','Imaging helps the team see how the valve works and check for flow around the frame.')
            d.rounded_rectangle((741,673,1015,797),18,fill='#253d40')
            for i in range(3):
                x=764+i*75
                line(d,[(x,742),(x+17,742),(x+24,725),(x+30,765),(x+39,718),(x+49,742),(x+73,742)],'#9fdbbf',3)
        else:
            side(d,'ACCESS SITE','Close the groin artery','After the equipment is removed, the team closes the access site and checks the dressing.')
            d.rounded_rectangle((760,664,1004,799),24,fill='#eec2a8')
            d.rounded_rectangle((815,688,952,776),14,fill='#fff6e9',outline='#d7c3ae',width=3)
            d.rounded_rectangle((850,710,918,753),8,fill='#eee3ce')
        return im
    im=base('A new valve and ongoing follow-up','Follow-up checks how the replacement valve is working').copy()
    d=cutaway(im,t,'implanted')
    side(d,'AFTER TAVI','A new path for flow','The new valve helps blood move from the left ventricle into the aorta.')
    return im


def render(scene):
    scene_id=scene['id']
    seconds=scene['target_end_sec']-scene['target_start_sec']
    rate=16
    output=OUT/f'{scene_id}.mp4'
    image_for(scene_id,seconds*.75).save(OUT/f'{scene_id}.png')
    command=[str(FFMPEG),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
             '-framerate',str(rate),'-i','pipe:0','-an','-vf','fps=24','-c:v','libx264','-preset','veryfast',
             '-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        for index in range(seconds*rate):
            encoder.stdin.write(image_for(scene_id,index/rate).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError(f'Encoding failed for {scene_id}')
    print(f'{scene_id}: {seconds}s, {output.stat().st_size:,} bytes',flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    selected={'P01','P02','P05','P06','P07','P11'}
    for scene in json.loads((HERE/'scenes.json').read_text(encoding='utf-8')):
        if scene['id'] in selected and (len(sys.argv)==1 or scene['id'] in sys.argv[1:]):
            render(scene)
