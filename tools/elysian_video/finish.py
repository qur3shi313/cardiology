"""Build the thumbnail and captioned vertical edit from a complete master."""
import argparse
import json
from pathlib import Path
import re
import shutil

from PIL import Image, ImageDraw, ImageFont

from .__main__ import ROOT, SERIES, FONTS, FPS, LEGACY_FFMPEG, run, scratch

def read_srt(path):
    def seconds(s):
        h,m,x=s.replace(',','.').split(':')
        return int(h)*3600+int(m)*60+float(x)
    for block in re.split(r'\n\s*\n',path.read_text(encoding='utf-8-sig').strip()):
        _, timing, *lines=block.splitlines()
        a,b=timing.split(' --> ')
        yield seconds(a),seconds(b),lines

def ass_stamp(t):
    cs=round(t*100)
    return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'

def caption_track(path,srt,a,b):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Fira Sans,49,&H00FFFFFF,&H00FFFFFF,&H2A071D1D,&H2A071D1D,-1,0,0,0,100,100,0,0,1,2.5,0,2,42,42,224,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    out=[header]
    for start,end,lines in read_srt(srt):
        lo,hi=max(a,start),min(b,end)
        if hi<=lo: continue
        safe=r'\N'.join(line.replace('{','(').replace('}',')') for line in lines)
        out.append(f'Dialogue: 0,{ass_stamp(lo-a)},{ass_stamp(hi-a)},Caption,,0,0,0,,{safe}\n')
    path.write_text(''.join(out),encoding='utf-8-sig')

def title(draw,label,where,size,tone,limit):
    font=ImageFont.truetype(str(FONTS/'fira-sans-semibold.ttf'),size)
    if draw.textlength(label,font=font)>limit: raise ValueError(f'Title does not fit: {label}')
    draw.text(where,label,font=font,fill=tone,anchor='lt')

def logo(size):
    return Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)

def thumbnail(ffmpeg,master,dest,seconds,lines):
    frame=dest.with_suffix('.frame.png')
    try:
        run(ffmpeg,'-v','error','-y','-ss',seconds,'-i',master,'-frames:v',1,
            '-vf','crop=1580:1000:545:303,scale=740:468:flags=lanczos',frame)
        out=Image.new('RGBA',(1280,720),'#102b29')
        visual=Image.open(frame).convert('RGBA')
        out.alpha_composite(visual,(540,154))
        out.alpha_composite(logo(77),(62,55))
        pen=ImageDraw.Draw(out)
        title(pen,'Elysian Biomedical LLP',(157,76),33,'#e4f3eb',455)
        for i,line in enumerate(lines):
            title(pen,line,(57,210+i*114),101,'#f5fff7',515)
        title(pen,'CORONARY ANGIOGRAPHY',(63,585),29,'#a0d3be',493)
        out.convert('RGB').save(dest,quality=96,subsampling=0)
    finally:
        if frame.is_file(): frame.unlink()

def short(ffmpeg,master,srt,dest,a,b):
    with scratch('elysian-short-') as temp:
        work=Path(temp)
        captions=work/'vertical.ass'
        caption_track(captions,srt,a,b)
        fontdir=work/'fonts'
        fontdir.mkdir()
        for name in ('fira-sans-regular.ttf','fira-sans-semibold.ttf'):
            shutil.copy2(FONTS/name,fontdir/name)
        overlay=Image.new('RGBA',(1080,1920))
        overlay.alpha_composite(logo(94),(68,106))
        pen=ImageDraw.Draw(overlay)
        title(pen,'Elysian Biomedical LLP',(180,127),45,'#e0f3e9',848)
        title(pen,'How contrast reveals',(67,292),87,'#f3fff5',960)
        title(pen,'the coronary arteries',(67,397),84,'#f3fff5',960)
        title(pen,'SIMULATED X-RAY',(71,1415),42,'#a9dcca',960)
        pen.line((70,1479,1010,1479),fill='#416a5e',width=3)
        graphic=work/'short-overlay.png'
        overlay.save(graphic)
        chain=('[0:v]crop=1580:1030:524:274,scale=1080:-2:flags=lanczos,'
               'pad=1080:1920:0:586:color=0x102a28,setsar=1[picture];'
               '[picture][1:v]overlay=0:0,ass=vertical.ass:fontsdir=fonts[out]')
        run(ffmpeg,'-v','error','-y','-ss',f'{a:.7f}','-t',f'{b-a:.7f}','-i',master,
            '-i',graphic,'-filter_complex_threads',2,'-filter_complex',chain,
            '-map','[out]','-map','0:a:0','-t',f'{b-a:.7f}','-r',FPS,'-c:v','libx264',
            '-preset','slow','-crf',16,'-g',60,'-bf',2,'-threads',5,'-c:a','aac','-b:a','320k',
            '-movflags','+faststart',dest,cwd=work)

def finish(episode,ffmpeg):
    episode=episode.resolve()
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    delivery=episode/'delivery'
    master=delivery/f'{episode.name}-1440p.mp4'
    if not master.is_file(): raise FileNotFoundError(master)
    spec=timeline['short']
    a,b=spec['start_frame']/FPS,spec['end_frame']/FPS
    if not 0<=a<b or b-a>45:
        raise ValueError('Use a positive Short duration of 45 seconds or less')
    if episode.name!='episode-01':
        raise ValueError('Set episode-specific crop, thumbnail and Short title first')
    srt=episode/timeline.get('caption_file','captions.en.srt')
    thumbnail(ffmpeg,master,delivery/f'{episode.name}-thumbnail.jpg',6.3,('Wrist','or groin?'))
    short(ffmpeg,master,srt,delivery/f'{episode.name}-short.mp4',a,b)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode',choices=('episode-01',))
    p.add_argument('--ffmpeg',default=LEGACY_FFMPEG,type=Path)
    args=p.parse_args()
    finish(SERIES/args.episode,args.ffmpeg.resolve())
