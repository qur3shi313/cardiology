"""Assemble approved scene pictures, narration, and captions into a complete film."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SERIES = ROOT / 'outputs/cardiology-series/v2'
FONTS = ROOT / 'outputs/website-v2/elysian-corporate/assets/fonts'
WIDTH, HEIGHT, FPS = 2560, 1440, 30
LEGACY_FFMPEG = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'


@dataclass(frozen=True)
class Media:
    path: Path
    start: float
    end: float


def run(exe, *args, **options):
    options.setdefault('check',True)
    return subprocess.run([str(exe), '-hide_banner', *map(str, args)], **options)


def read_media(spec):
    path = (ROOT / spec['path']).resolve(strict=True)
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f'Media must be a file in the project: {path}')
    start, end = float(spec['in_sec']), float(spec['out_sec'])
    if not 0 <= start < end:
        raise ValueError(f'Invalid source interval for {path.name}')
    return Media(path, start, end)


def load_timeline(episode):
    data = json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    overrides = {}
    override_paths = [episode/'picture-overrides.json', *sorted((episode/'visuals').glob('*-overrides.json'))]
    for override_path in override_paths:
        if override_path.is_file():
            new = json.loads(override_path.read_text(encoding='utf-8-sig'))
            if set(new) & set(overrides):
                raise ValueError(f'Conflicting picture decisions in {override_path.name}')
            overrides.update(new)
    if data['fps'] != FPS:
        raise ValueError(f'Timeline must use {FPS} frames per second')
    end, identifiers = 0, set()
    for scene in data['scenes']:
        ident = scene['id']
        if ident in identifiers or scene['start_frame'] != end or scene['end_frame'] <= end:
            raise ValueError(f'Invalid or overlapping scene: {ident}')
        identifiers.add(ident)
        end = scene['end_frame']
        if ident in overrides:
            scene['footage'] = overrides[ident]
        read_media(scene['footage'])
        if scene.get('audio'):
            read_media(scene['audio'])
    if end != data['duration_frames'] or set(overrides)-identifiers:
        raise ValueError('Timeline duration or picture overrides do not match its scene list')
    return data


def title_layer(path, label, category, subline=None):
    image = Image.new('RGBA', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    regular = FONTS/'fira-sans-regular.ttf'
    bold = FONTS/'fira-sans-semibold.ttf'
    title_font = ImageFont.truetype(str(bold), 92)
    note_font = ImageFont.truetype(str(regular), 49)
    left, top = 89, 72
    if draw.textlength(label,font=title_font)>WIDTH-2*left-112:
        raise ValueError(f'Scene label exceeds the readable title width: {label}')
    for y in range(355):
        shade = round(248*(1-y/355)**.9)
        draw.line((0,y,WIDTH,y),fill=(12,28,26,shade))
    draw.text((left,top),label,font=title_font,fill='#ffffff',anchor='lt')
    draw.text((left,top+111),category,font=note_font,fill='#e5f4e8',anchor='lt')
    logo = Image.open(ROOT/'work/company-logo-original-686.jpg').convert('RGBA').resize((105,105),Image.Resampling.LANCZOS)
    image.alpha_composite(logo,(WIDTH-181,63))
    if subline:
        sw=draw.textlength(subline,font=note_font)
        draw.rounded_rectangle((left-25,HEIGHT-151,left+sw+26,HEIGHT-67),radius=22,fill=(12,41,36,239))
        draw.text((left,HEIGHT-133),subline,font=note_font,fill='#ffffff',anchor='lt')
    image.save(path)


def picture(exe, scene, work, quality):
    spec = scene['footage']
    source = read_media(spec)
    frames = scene['end_frame']-scene['start_frame']
    duration = frames/FPS
    ratio = duration/(source.end-source.start)
    if spec.get('reference_only'):
        raise ValueError(f'{scene["id"]} needs a selected or newly rendered picture')
    chain = [f'setpts={ratio:.10f}*(PTS-STARTPTS)',f'fps={FPS}']
    if crop := spec.get('crop'):
        x,y,w,h = map(int,crop)
        if min(x,y)<0 or min(w,h)<2 or any(v%2 for v in (x,y,w,h)):
            raise ValueError(f'Crop coordinates and dimensions must be even for {scene["id"]}')
        chain.append(f'crop={w}:{h}:{x}:{y}')
    if spec.get('fill',False):
        chain.extend([f'scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:force_divisible_by=2:flags=lanczos',
                      f'crop={WIDTH}:{HEIGHT}'])
    else:
        chain.extend([f'scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos',
                      f'pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0xe8f0e8'])
    chain.extend(['setsar=1','tpad=stop_mode=clone:stop_duration=0.15','format=yuv420p'])
    arguments=['-ss',f'{source.start:.6f}','-t',f'{source.end-source.start:.6f}','-i',source.path]
    if label := spec.get('label'):
        overlay=work/f'{scene["id"]}-label.png'
        title_layer(overlay,label,spec.get('category','Illustrated educational sequence'),spec.get('subline'))
        enabled = f":enable='gte(t,{float(spec['label_onset_sec']):.5f})'" if 'label_onset_sec' in spec else ''
        arguments.extend(['-i',overlay,'-filter_complex_threads',2,'-filter_complex',
                          '[0:v]'+','.join(chain)+'[picture];[picture][1:v]overlay=0:0:repeatlast=1'+enabled+',format=yuv420p[out]',
                          '-map','[out]'])
    else:
        arguments.extend(['-filter_threads',2,'-vf',','.join(chain),'-map','0:v:0'])
    target=work/f'{scene["id"]}.mp4'
    run(exe,'-v','error','-y',*arguments,'-an','-frames:v',frames,'-c:v','libx264','-preset',quality,
        '-crf',16,'-profile:v','high','-pix_fmt','yuv420p','-threads',4,'-g',60,'-bf',2,
        '-video_track_timescale',30000,target)
    return target


def narration(exe, scene, work):
    duration = (scene['end_frame']-scene['start_frame'])/FPS
    target = work/f'{scene["id"]}.wav'
    if spec := scene.get('audio'):
        source = read_media(spec)
        arguments = ['-ss',f'{source.start:.7f}','-t',f'{source.end-source.start:.7f}','-i',source.path]
    else:
        arguments = ['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
    run(exe,'-v','error','-y',*arguments,'-af',f'apad,atrim=duration={duration:.9f}',
        '-ac','2','-ar','48000','-c:a','pcm_s24le',target)
    return target


def concat_list(work, name, files):
    path=work/name
    path.write_text(''.join(f"file '{p.name}'\n" for p in files),encoding='utf-8')
    return path


def normalized_voice(exe, work, list_path):
    chain='highpass=f=65,loudnorm=I=-14:TP=-1.25:LRA=7'
    measurement=run(exe,'-nostats','-f','concat','-safe',0,'-i',list_path,
                    '-af',chain+':print_format=json','-f','null','-',capture_output=True,
                    text=True,encoding='utf-8',errors='replace')
    stats=json.loads(re.findall(r'\{[^{}]+\}',measurement.stderr)[-1])
    known=':'.join(f'measured_{key}={stats["input_"+key]}' for key in ('i','tp','lra','thresh'))
    target=work/'normalized.m4a'
    run(exe,'-v','error','-y','-f','concat','-safe',0,'-i',list_path,
        '-af',f'{chain}:{known}:offset={stats["target_offset"]}:linear=true',
        '-ac','2','-ar','48000','-c:a','aac','-b:a','320k',target)
    return target


def render_episode(exe, episode, jobs, quality):
    timeline = load_timeline(episode)
    captions = next((path for path in (episode/'captions.en.srt', episode/f'{episode.name}.en.srt')
                     if path.is_file()),episode/'captions.en.srt')
    if not captions.is_file():
        raise FileNotFoundError(captions)
    incomplete = [scene['id'] for scene in timeline['scenes'] if scene['footage'].get('reference_only')]
    if incomplete:
        raise ValueError('Picture decisions still needed: '+', '.join(incomplete))
    output = episode/'delivery'
    output.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='elysian-film-') as temporary:
        work = Path(temporary)
        scenes = timeline['scenes']
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            picture_jobs=[pool.submit(picture,exe,scene,work,quality) for scene in scenes]
            voice_jobs=[pool.submit(narration,exe,scene,work) for scene in scenes]
            pictures=[]
            for scene,job in zip(scenes,picture_jobs):
                pictures.append(job.result())
                print(f'Rendered {scene["id"]} {scene["title"]}',flush=True)
            voices=[job.result() for job in voice_jobs]
        voice = normalized_voice(exe,work,concat_list(work,'voice.txt',voices))
        picture_list = concat_list(work,'picture.txt',pictures)
        temporary_master = work/'master.mp4'
        run(exe,'-v','error','-y','-f','concat','-safe',0,'-i',picture_list,'-i',voice,'-i',captions,
            '-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-c:a','copy','-c:s','mov_text',
            '-metadata:s:a:0','language=eng','-metadata:s:s:0','language=eng','-movflags','+faststart',temporary_master)
        run(exe,'-v','error','-xerror','-i',temporary_master,'-map','0:v:0','-map','0:a:0','-f','null','-')
        master=output/f'{episode.name}-1440p.mp4'
        shutil.copy2(temporary_master,master)
        run(exe,'-v','error','-y','-i',master,'-map','0','-vf','scale=1920:1080:flags=lanczos',
            '-c:v','libx264','-preset',quality,'-crf',16,'-profile:v','high','-g',60,'-bf',2,'-threads',6,
            '-c:a','copy','-c:s','copy','-movflags','+faststart',output/f'{episode.name}-1080p.mp4')
        print(f'Complete master: {master}',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('validate','render'))
    parser.add_argument('episode',help='Episode directory name in the v2 series')
    parser.add_argument('--ffmpeg',default=os.environ.get('ELYSIAN_FFMPEG') or shutil.which('ffmpeg') or LEGACY_FFMPEG)
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--preset',default='slow',choices=('slow','medium'))
    args=parser.parse_args()
    if not re.fullmatch(r'episode-\d{2}',args.episode) or args.jobs<1:
        parser.error('Use episode-NN and a positive job count')
    episode=SERIES/args.episode
    if args.action=='validate':
        data=load_timeline(episode)
        print(f'{len(data["scenes"])} scenes, {data["duration_frames"]/FPS:.2f} seconds')
    else:
        render_episode(args.ffmpeg,episode,args.jobs,args.preset)


if __name__=='__main__':
    main()
