"""Illustrate how clinical context changes coronary access selection."""

from functools import lru_cache
from math import pi, sin
from pathlib import Path
import json
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps


HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / 'episode-01' / 'revision'))
from render_editorial_cards import DEEP, INK, LINE, MUTED, ROOT, font, gradient, heart, write
sys.path.insert(0, str(HERE.parent / 'episode-01' / 'revision' / 'wrist-proof'))
from render_wrist_proof import background as wrist_background


W, H = 1920, 1080
OUT = HERE / 'visuals'
FFMPEG = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
PAPER = '#f8fcf8'
MOSS = '#dcece3'
ARTERY = '#b46667'
LUMEN = '#eeb6ac'
HARDWARE = '#327975'


def box(draw, rect, fill=PAPER, border=LINE, radius=31):
    draw.rounded_rectangle(rect, radius, fill=fill, outline=border, width=2)


def chip(draw, x, y, text):
    size=27
    end=x+draw.textlength(text,font=font(size,'bold'))+36
    box(draw,(x,y,end,y+46),MOSS,MOSS,12)
    write(draw,x+18,y+9,text,size,'bold',DEEP)


@lru_cache(maxsize=4)
def base(title,takeaway):
    image=gradient((249,252,248),(226,240,231)).copy()
    logo=Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGB')
    logo=ImageOps.fit(logo,(75,75),method=Image.Resampling.LANCZOS)
    mask=Image.new('L',(75,75))
    ImageDraw.Draw(mask).ellipse((0,0,74,74),fill=255)
    image.paste(logo,(68,41),mask)
    draw=ImageDraw.Draw(image)
    write(draw,162,49,'Elysian Biomedical LLP',33,'bold',DEEP)
    write(draw,164,88,'Cardiology Education Series',24,'body',MUTED)
    draw.text((1848,51),'EPISODE 05',fill=DEEP,font=font(27,'bold'),anchor='rt')
    draw.line((69,137,1850,137),fill=LINE,width=2)
    write(draw,69,177,title,70,'title')
    draw.line((69,968,1850,968),fill=LINE,width=2)
    write(draw,69,992,takeaway,32,'bold',DEEP)
    return image


@lru_cache(maxsize=1)
def wrist_art():
    return wrist_background().crop((85,327,1524,742)).resize((955,276),Image.Resampling.LANCZOS)


def pulse(draw,x,y,t):
    radius=10+14*(.5+.5*sin(t*pi*1.7))
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),outline='#70b3a0',width=3)
    draw.ellipse((x-6,y-6,x+6,y+6),fill=DEEP,outline='#eff8ef',width=2)


def card_line(draw,x,y,heading,text):
    draw.ellipse((x,y+15,x+12,y+27),fill='#368873')
    write(draw,x+34,y,heading,32,'bold',DEEP)
    write(draw,x+34,y+47,text,26,'body',MUTED,641)


def wrist_choice(t):
    image=base('Why the wrist is often chosen','The recommendation depends on why the procedure is being done.').copy()
    draw=ImageDraw.Draw(image)
    box(draw,(70,286,1067,923))
    box(draw,(1098,286,1850,923))
    chip(draw,107,324,'WRIST ACCESS')
    write(draw,106,411,'The radial artery',51,'title')
    art=wrist_art()
    image.paste(art,(90,513))
    draw=ImageDraw.Draw(image)
    pulse(draw,709,679,t)
    draw.line((709,699,746,842,1002,842),fill='#397a69',width=3,joint='curve')
    draw.text((998,854),'Radial artery cutaway',fill=MUTED,font=font(27,'bold'),anchor='rt')

    if t<20.55:
        chip(draw,1135,324,'ACUTE CORONARY SYNDROME')
        write(draw,1136,412,'During PCI',51,'title')
        card_line(draw,1136,514,'Lower bleeding risk','Wrist access is preferred when feasible.')
        if t>=7:
            card_line(draw,1136,641,'Fewer vessel complications','This comparison applies to PCI in this acute setting.')
        if t>=16.65:
            card_line(draw,1136,767,'Lower risk of death','2025 US guideline · acute coronary syndrome with PCI')
    else:
        chip(draw,1135,324,'STABLE CORONARY DISEASE')
        write(draw,1136,412,'During PCI',51,'title')
        card_line(draw,1136,540,'Less bleeding at the access site','The wrist is often favored when feasible.')
        card_line(draw,1136,685,'Fewer vessel complications','The team considers the individual situation.')
    return image


def tube(draw, x, y, length, radius, hardware_radius, t):
    wall=(x,y-radius,x+length,y+radius)
    draw.rounded_rectangle(wall,radius,fill=ARTERY,outline='#89515a',width=3)
    draw.rounded_rectangle((x+3,y-radius+8,x+length-3,y+radius-8),max(4,radius-8),fill=LUMEN)
    end=round(x+100+(length-164)*min(1.,max(0.,t/3.5)))
    draw.rounded_rectangle((x-27,y-hardware_radius,end,y+hardware_radius),hardware_radius,
                           fill=HARDWARE,outline='#275958',width=3)
    draw.line((x-12,y-1,end-6,y-1),fill='#a0c7b8',width=3)


@lru_cache(maxsize=1)
def heart_card():
    image=Image.new('RGB',(W,H),PAPER)
    heart(image,1167,396,.89)
    return image.crop((1170,397,1703,831))


def groin_choice(t):
    image=base('When the groin may be chosen','Equipment, artery anatomy and bypass history can affect the choice.').copy()
    draw=ImageDraw.Draw(image)
    box(draw,(70,286,682,923))
    box(draw,(713,286,1850,923))
    if t<8.8:
        chip(draw,111,324,'EQUIPMENT')
        write(draw,108,425,'Room for larger equipment',56,'title',DEEP,525)
        write(draw,111,589,'Some emergency heart-support devices need a larger access artery.',36,'body',INK,485)
        write(draw,763,346,'Access artery and equipment',46,'title')
        write(draw,766,455,'Radial artery at the wrist',30,'bold')
        tube(draw,825,544,882,35,10,t)
        write(draw,766,653,'Common femoral artery at the groin',30,'bold')
        tube(draw,825,755,882,65,22,t)
        write(draw,765,859,'Illustrated comparison, without a measurement scale',26,'body',MUTED)
    elif t<16.3:
        chip(draw,111,324,'ARTERY ANATOMY')
        write(draw,108,425,'A difficult path',56,'title',DEEP,520)
        write(draw,111,527,'The wrist artery may be small or difficult to pass through.',36,'body',INK,485)
        write(draw,763,346,'Example of a curved arterial path',46,'title')
        points=[]
        for i in range(141):
            fraction=i/140
            points.append((820+891*fraction,629+83*sin(3*pi*fraction)))
        for color,width in [('#8d515a',58),(ARTERY,51),(LUMEN,34)]:
            draw.line(points,fill=color,width=width,joint='curve')
        progress=round(18+55*min(1,max(0,(t-8.8)/3.4)))
        draw.line(points[:progress],fill=HARDWARE,width=13,joint='curve')
        x,y=points[progress-1]
        pulse(draw,x,y,t)
        write(draw,766,854,'The team can choose another access site.',30,'bold',DEEP)
    else:
        chip(draw,111,324,'BYPASS HISTORY')
        write(draw,108,425,'Previous or planned bypass',56,'title',DEEP,515)
        write(draw,111,591,'An existing graft or a plan to use a wrist artery as a graft can affect the route.',36,'body',INK,482)
        write(draw,763,346,'The team reviews the bypass plan',46,'title')
        image.paste(heart_card(),(1147,425))
        draw=ImageDraw.Draw(image)
        chip(draw,790,540,'PREVIOUS BYPASS')
        chip(draw,790,643,'POSSIBLE FUTURE GRAFT')
        draw.line((1139,566,1211,566,1323,609),fill='#448875',width=4,joint='curve')
        pulse(draw,1323,609,t)
        write(draw,765,858,'The access plan is tailored to the person and procedure.',29,'bold',DEEP)
    return image


def render(scene):
    ident=scene['id']
    seconds=scene['target_end_sec']-scene['target_start_sec']
    draw=wrist_choice if ident=='P04' else groin_choice
    rate=12
    output=OUT/f'{ident}.mp4'
    command=[str(FFMPEG),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}',
             '-framerate',str(rate),'-i','pipe:0','-an','-vf','fps=24','-c:v','libx264','-preset','veryfast',
             '-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        for index in range(seconds*rate):
            encoder.stdin.write(draw(index/rate).tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError(f'Encoding failed for {ident}')
    subprocess.run([str(FFMPEG),'-v','error','-xerror','-i',str(output),'-f','null','-'],check=True)
    draw(seconds*.52).save(OUT/f'{ident}.png')
    print(f'{ident}: {seconds}s, full decode passed',flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    for row in json.loads((HERE/'scenes.json').read_text(encoding='utf-8')):
        if row['id'] in {'P04','P05'}:
            render(row)
