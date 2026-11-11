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

def thumbnail(ffmpeg,master,dest,seconds,lines,crop=(1580,1000,545,303),eyebrow='CORONARY ANGIOGRAPHY'):
    frame=dest.with_suffix('.frame.png')
    try:
        w,h,x,y=crop
        run(ffmpeg,'-v','error','-y','-ss',seconds,'-i',master,'-frames:v',1,
            '-vf',f'crop={w}:{h}:{x}:{y},scale=740:-2:flags=lanczos',frame)
        out=Image.new('RGBA',(1280,720),'#102b29')
        visual=Image.open(frame).convert('RGBA')
        out.alpha_composite(visual,(540,(720-visual.height)//2+30))
        out.alpha_composite(logo(77),(62,55))
        pen=ImageDraw.Draw(out)
        title(pen,'Elysian Biomedical LLP',(157,76),33,'#e4f3eb',455)
        font_size=88
        while font_size>77:
            face=ImageFont.truetype(str(FONTS/'fira-sans-semibold.ttf'),font_size)
            if all(face.getlength(line)<=470 for line in lines): break
            font_size-=1
        for i,line in enumerate(lines):
            title(pen,line,(57,202+i*104),font_size,'#f5fff7',470)
        title(pen,eyebrow,(63,585),29,'#a0d3be',493)
        out.convert('RGB').save(dest,quality=96,subsampling=0)
    finally:
        if frame.is_file(): frame.unlink()

def short(ffmpeg,master,srt,dest,a,b,headings=('How contrast reveals','the coronary arteries'),
          crop=(1580,1030,524,274),eyebrow='SIMULATED X-RAY'):
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
        for i,line in enumerate(headings):
            title(pen,line,(67,292+i*105),84,'#f3fff5',960)
        title(pen,eyebrow,(71,1415),42,'#a9dcca',960)
        pen.line((70,1479,1010,1479),fill='#416a5e',width=3)
        graphic=work/'short-overlay.png'
        overlay.save(graphic)
        w,h,x,y=crop
        if (1080*h/w)>795:
            raise ValueError('Vertical framing covers the Short caption band')
        chain=(f'[0:v]crop={w}:{h}:{x}:{y},scale=1080:-2:flags=lanczos,'
               'pad=1080:1920:0:586:color=0x102a28,setsar=1[picture];'
               '[picture][1:v]overlay=0:0,ass=vertical.ass:fontsdir=fonts[out]')
        trim=('-ss',f'{a:.7f}','-t',f'{b-a:.7f}','-i',master)
        loudness='loudnorm=I=-14:TP=-1.5:LRA=7'
        measured=run(ffmpeg,'-v','info','-nostats',*trim,'-map','0:a:0',
                     '-af',loudness+':print_format=json','-f','null','-',
                     capture_output=True,text=True,encoding='utf-8',errors='replace')
        stats=json.loads(re.findall(r'\{[^{}]+\}',measured.stderr)[-1])
        known=':'.join(f'measured_{key}={stats["input_"+key]}' for key in ('i','tp','lra','thresh'))
        if stats['input_i']=='-inf':
            raise ValueError('The selected Short interval has no audible narration')
        run(ffmpeg,'-v','error','-y',*trim,'-i',graphic,'-filter_complex_threads',2,'-filter_complex',chain,
            '-map','[out]','-map','0:a:0','-t',f'{b-a:.7f}','-r',FPS,'-c:v','libx264',
            '-preset','slow','-crf',16,'-g',60,'-bf',2,'-threads',5,
            '-af',f'{loudness}:{known}:offset={stats["target_offset"]}:linear=true',
            '-ac','2','-ar','48000','-c:a','aac','-b:a','320k',
            '-movflags','+faststart',dest,cwd=work)

def finish(episode,ffmpeg):
    episode=episode.resolve()
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    delivery=episode/'delivery'
    master=delivery/f'{episode.name}-1440p.mp4'
    if not master.is_file(): raise FileNotFoundError(master)
    config_path=episode/'finish-config.json'
    if config_path.is_file():
        config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    elif episode.name=='episode-01':
        config={}
    else:
        raise ValueError('Set episode-specific thumbnail and Short layout first')
    spec=config.get('short') or timeline['short']
    a,b=(spec['seconds'] if 'seconds' in spec else
         (spec['start_frame']/FPS,spec['end_frame']/FPS))
    if not 0<=a<b or b-a>45:
        raise ValueError('Use a positive Short duration of 45 seconds or less')
    srt=episode/timeline.get('caption_file','captions.en.srt')
    thumb=delivery/f'{episode.name}-thumbnail.jpg'
    ts=config.get('thumbnail',{})
    if ts.get('artwork'):
        with Image.open(episode/ts['artwork']) as source:
            if source.size!=(1280,720):
                raise ValueError('An approved thumbnail must be 1280 × 720')
            source.convert('RGB').save(thumb,quality=96,subsampling=0)
    else:
        thumbnail(ffmpeg,master,thumb,ts.get('seconds',6.3),ts.get('title',('Wrist','or groin?')),
                  tuple(ts.get('crop',(1580,1000,545,303))),ts.get('eyebrow','CORONARY ANGIOGRAPHY'))
    kwargs={k:spec[k] for k in ('headings','crop','eyebrow') if k in spec}
    short(ffmpeg,master,srt,delivery/f'{episode.name}-short.mp4',a,b,**kwargs)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode',choices=tuple(f'episode-{i:02}' for i in range(1,21)))
    p.add_argument('--ffmpeg',default=LEGACY_FFMPEG,type=Path)
    args=p.parse_args()
    finish(SERIES/args.episode,args.ffmpeg.resolve())
