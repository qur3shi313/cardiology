"""Verify a finished episode's media and produce a phone-size review sheet."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageDraw


def invoke(ffmpeg, *arguments, check=True):
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostats', *map(str, arguments)], capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace').strip())
    return result


def metadata(log):
    video = next((line for line in log.splitlines() if 'Stream #' in line and 'Video:' in line), None)
    if not video:
        raise ValueError('FFmpeg found no video stream.')
    codec = re.search(r'Video:\s+([\w]+)', video)
    pixels = re.search(r'\b(\d{2,5})x(\d{2,5})\b', video)
    pixel_format = re.search(r'\b(?:yuva?[\w]+|nv\d+|p\d+(?:le|be)?|gbr\w+|[rb]gr?\w+|gray\w*)\b', video)
    frame_rate = re.search(r'([\d.]+)\s+fps\b', video)
    audio = next((line for line in log.splitlines() if 'Stream #' in line and 'Audio:' in line), '')
    return {
        'codec': codec.group(1) if codec else None,
        'width': int(pixels.group(1)) if pixels else None,
        'height': int(pixels.group(2)) if pixels else None,
        'pixel_format': pixel_format.group() if pixel_format else None,
        'fps': float(frame_rate.group(1)) if frame_rate else None,
        'audio_present': any('Stream #' in line and 'Audio:' in line for line in log.splitlines()),
        'audio_codec': (re.search(r'Audio:\s+(\w+)',audio).group(1) if audio else None),
        'audio_rate': (int(re.search(r'\b(\d+) Hz',audio).group(1)) if ' Hz' in audio else None),
        'audio_stereo': 'stereo' in audio,
    }


def freeze_report(log, duration):
    intervals = []
    start = None
    for event, seconds in re.findall(r'freeze_(start|end):\s*(-?[\d.]+)', log):
        if event == 'start':
            start = max(0., float(seconds))
        elif start is not None:
            intervals.append({'start_seconds': start, 'end_seconds': float(seconds), 'terminal': False})
            start = None
    if start is not None and start < duration:
        intervals.append({'start_seconds': start, 'end_seconds': duration, 'terminal': True})
    lengths = [max(0., interval['end_seconds'] - interval['start_seconds']) for interval in intervals]
    return {
        'noise': .001,
        'min_duration_seconds': 2,
        'total_seconds': round(sum(lengths), 6),
        'percent': round(100 * sum(lengths) / duration, 3),
        'longest_seconds': round(max(lengths, default=0.), 6),
        'intervals': intervals,
    }


def inspect_audio(ffmpeg, path):
    result = invoke(ffmpeg, '-v', 'info', '-xerror', '-i', path, '-map', '0:a:0', '-vn',
                    '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json', '-f', 'null', '-')
    log = result.stderr.decode('utf-8', 'replace')
    measurement = re.search(r'\{\s*"input_i"[\s\S]*?\}', log)
    if not measurement:
        raise RuntimeError('FFmpeg decoded audio without returning a loudnorm measurement.')
    raw = json.loads(measurement.group())
    integrated, peak = float(raw['input_i']), float(raw['input_tp'])
    return {
        'full_decode': True,
        'integrated_lufs': integrated if math.isfinite(integrated) else None,
        'true_peak_dbtp': peak if math.isfinite(peak) else None,
        'raw_loudnorm': raw,
    }


def speech_errors(audio, prefix=''):
    if not audio:
        return [prefix + 'Speech track is missing']
    loudness, peak = audio['integrated_lufs'], audio['true_peak_dbtp']
    errors = []
    if loudness is None or not -15 <= loudness <= -13:
        errors.append(prefix + 'Speech loudness outside -14 ± 1 LUFS')
    if peak is None or peak > -1:
        errors.append(prefix + 'True peak exceeds -1 dBTP or could not be measured')
    return errors


def contact_sheet(ffmpeg, path, duration, output):
    times = list(range(0, math.ceil(duration), 5))
    columns = min(3, len(times))
    def sample(seconds):
        result = invoke(ffmpeg, '-v', 'error', '-threads', 2, '-filter_threads', 2,
                        '-ss', seconds, '-i', path, '-map', '0:v:0',
                        '-frames:v', 1, '-vf', 'scale=390:-2:flags=lanczos', '-c:v', 'png',
                        '-f', 'image2pipe', 'pipe:1')
        if not result.stdout:
            raise RuntimeError(f'FFmpeg produced no contact-sheet frame at {seconds} seconds.')
        with Image.open(BytesIO(result.stdout)) as frame:
            return frame.convert('RGB')

    with ThreadPoolExecutor(max_workers=2) as pool:
        frames=list(pool.map(sample,times))

    height = frames[0].height + 27
    sheet = Image.new('RGB', (columns * 402, math.ceil(len(frames) / columns) * height), '#edf4ee')
    draw = ImageDraw.Draw(sheet)
    for index, (seconds, frame) in enumerate(zip(times, frames)):
        x, y = index % columns * 402 + 6, index // columns * height
        sheet.paste(frame, (x, y))
        draw.text((x + 6, y + frame.height + 5), f'{seconds // 60:02d}:{seconds % 60:02d}', fill='#183a2f')
    sheet.save(output, quality=93)
    return times


def file_hash(path):
    checksum=sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            checksum.update(data)
    return checksum.hexdigest()


def verify_captions(path, duration):
    errors=[]
    stamp=r'(\d+):(\d\d):(\d\d),(\d\d\d)'
    previous=0
    if not path.is_file():
        return {'file':path.name,'cue_count':0,'errors':['SRT missing']}
    blocks=re.split(r'\n\s*\n',path.read_text(encoding='utf-8-sig').strip())
    for index,block in enumerate(blocks,1):
        lines=block.splitlines()
        marker=re.fullmatch(stamp+r'\s+-->\s+'+stamp,lines[1]) if len(lines)>1 else None
        if not marker or lines[0]!=str(index) or len(lines) not in (3,4):
            errors.append(f'Cue {index}: invalid structure')
            continue
        h,m,s,ms,hh,mm,ss,mms=map(int,marker.groups())
        begin,end=3600*h+60*m+s+ms/1000,3600*hh+60*mm+ss+mms/1000
        if not previous<=begin<end<=duration+.034:
            errors.append(f'Cue {index}: overlapping or out-of-range timing')
        if any(len(line)>42 for line in lines[2:]):
            errors.append(f'Cue {index}: exceeds 42 characters per line')
        previous=end
    return {'file':path.name,'cue_count':len(blocks),'errors':errors}

def check_package(episode, master, ffmpeg, intended):
    package={}
    errors=[]
    stem=episode.name
    delivery=master.parent
    for suffix,width,height,max_sec in (('1080p',1920,1080,intended+.5),('short',1080,1920,45.05)):
        path=delivery/f'{stem}-{suffix}.mp4'
        if not path.is_file():
            errors.append(f'{suffix}: output is missing')
            continue
        result=invoke(ffmpeg,'-i',path,check=False)
        log=result.stderr.decode('utf-8','replace')
        fmt=metadata(log)
        match=re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)',log)
        seconds=None
        if match:
            h,m,s=match.groups()
            seconds=int(h)*3600+int(m)*60+float(s)
        package[suffix]={'file':path.name,'sha256':file_hash(path),'duration_seconds':seconds,**fmt}
        expected={'width':width,'height':height,'fps':30.,'codec':'h264','audio_present':True,
                  'audio_codec':'aac','audio_rate':48000,'audio_stereo':True}
        if any(fmt[k]!=v for k,v in expected.items()):
            errors.append(f'{suffix}: picture or voice format does not match')
        else:
            decoded=invoke(ffmpeg,'-v','error','-xerror','-threads',2,'-i',path,
                           '-map','0:v:0','-map','0:a:0','-f','null','-',check=False)
            package[suffix]['full_decode']=decoded.returncode==0
            if decoded.returncode:
                errors.append(f'{suffix}: picture or voice failed full decode')
            elif suffix=='short':
                speech=inspect_audio(ffmpeg,path)
                package[suffix]['audio']=speech
                errors.extend(speech_errors(speech,'Short: '))
        if seconds is None or seconds<=0 or seconds>max_sec or (suffix=='1080p' and abs(seconds-intended)>.5):
            errors.append(f'{suffix}: duration does not match')
    thumb=next((x for x in (delivery/f'{stem}-thumbnail.jpg',delivery/f'{stem}-thumbnail.png') if x.is_file()),None)
    if thumb:
        with Image.open(thumb) as photo:
            package['thumbnail']={'file':thumb.name,'sha256':file_hash(thumb),'size':list(photo.size)}
            if photo.size!=(1280,720):
                errors.append('Thumbnail is not 1280 × 720')
    else:
        errors.append('Thumbnail is missing')
    return package,errors


def caption_path(episode):
    return next((path for path in (episode/'captions.en.srt', episode/f'{episode.name}.en.srt')
                 if path.is_file()), episode/'captions.en.srt')


def validation_inputs(episode):
    captions = caption_path(episode)
    return {'timeline_sha256': file_hash(episode/'timeline.json'),
            'caption_file': captions.name,
            'caption_sha256': file_hash(captions) if captions.is_file() else None}


def apply_visual_review(report, episode):
    review_path = episode/'visual-review.json'
    review = json.loads(review_path.read_text(encoding='utf-8-sig')) if review_path.exists() else {}
    if review.get('master_sha256') != report['sha256']:
        review = {}
    report['human_visual_review'] = review or 'pending'
    report['halal_review'] = review.get('halal_review', 'pending')
    errors = list(report['mechanical_errors'])
    holds = review.get('intentional_holds', [])
    for interval in report['freeze']['intervals']:
        start, end = (interval[key+'_seconds'] for key in ('start', 'end'))
        if end-start > 6 and not any(h['start_seconds'] <= start+.10 and h['end_seconds'] >= end-.10
                                     and h.get('reason') for h in holds[:3]):
            errors.append(f'Unreviewed freeze longer than 6 seconds at {start:.3f}')
    for key in ('mobile_readability', 'art_coverage', 'device_motion', 'clinical_accuracy',
                'caption_alignment', 'voice_only', 'thumbnail', 'vertical_short', 'halal_review'):
        if review.get(key) != 'pass':
            errors.append(f'Required review pending: {key}')
    for asset in ('short', 'thumbnail'):
        reviewed_hash = review.get(asset+'_sha256')
        if reviewed_hash and reviewed_hash != report['deliverables'].get(asset, {}).get('sha256'):
            errors.append(f'The visual review covers a different {asset} output')
    report['errors'] = errors
    report['status'] = 'blocked' if errors else 'pass'


def save_report(report, episode):
    destination = episode/'QA.json'
    temporary = destination.with_suffix(f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(destination)
    print(destination)
    return int(report['status'] != 'pass')


def refresh_visual_review(path, episode):
    report_path = episode/'QA.json'
    if not report_path.is_file():
        raise ValueError('Run full media QA before refreshing the visual review.')
    report = json.loads(report_path.read_text(encoding='utf-8-sig'))
    if ('mechanical_errors' not in report or report.get('input') != path.name
            or report.get('validation_inputs') != validation_inputs(episode)
            or report.get('sha256') != file_hash(path)):
        raise ValueError('The saved QA does not cover these exact inputs. Run full media QA.')
    companions = report.get('deliverables', {})
    for key in ('1080p', 'short', 'thumbnail'):
        asset = companions.get(key, {})
        filename = asset.get('file', '')
        current = path.with_name(filename) if filename and Path(filename).name == filename else None
        if not current or not current.is_file() or asset.get('sha256') != file_hash(current):
            raise ValueError(f'The {key} output changed or is missing. Run full media QA.')
        if key == 'thumbnail' and current.suffix == '.png' and current.with_suffix('.jpg').is_file():
            raise ValueError('A new thumbnail takes precedence. Run full media QA.')
    apply_visual_review(report, episode)
    return save_report(report, episode)


def check_master(path, ffmpeg, episode):
    probe = invoke(ffmpeg, '-i', path, check=False)
    inputs = validation_inputs(episode)
    timeline=json.loads((episode/'timeline.json').read_text(encoding='utf-8-sig'))
    report = {'input': path.name, 'sha256':file_hash(path), 'validation_inputs': inputs,
              **metadata(probe.stderr.decode('utf-8', 'replace'))}
    video = invoke(ffmpeg, '-v', 'info', '-xerror', '-progress', 'pipe:1', '-i', path,
                   '-map', '0:v:0', '-an', '-vf', 'freezedetect=n=0.001:d=2', '-f', 'null', '-')
    decoded_times = re.findall(r'^out_time_us=(\d+)\s*$', video.stdout.decode(), re.MULTILINE)
    if not decoded_times or int(decoded_times[-1]) <= 0:
        raise RuntimeError('FFmpeg did not report a positive decoded video duration.')
    duration = int(decoded_times[-1]) / 1_000_000
    report['video_full_decode'] = True
    report['video_duration_seconds'] = duration
    decoded_frames=re.findall(rb'^frame=(\d+)\s*$',video.stdout,re.MULTILINE)
    report['video_frames']=int(decoded_frames[-1]) if decoded_frames else None
    report['freeze'] = freeze_report(video.stderr.decode('utf-8', 'replace'), duration)
    contributors=[]
    for scene in timeline['scenes']:
        a,b=(scene[key]/timeline['fps'] for key in ('start_frame','end_frame'))
        frozen=sum(max(0,min(b,x['end_seconds'])-max(a,x['start_seconds']))
                   for x in report['freeze']['intervals'])
        if frozen>=2:
            contributors.append({'scene':scene['id'],'title':scene['title'],
                                 'frozen_seconds':round(frozen,3),'scene_seconds':round(b-a,3)})
    report['freeze']['scene_contributors']=sorted(contributors,key=lambda x:x['frozen_seconds'],reverse=True)
    report['audio'] = inspect_audio(ffmpeg, path) if report['audio_present'] else None
    required = {'codec': 'h264', 'width': 2560, 'height': 1440, 'fps': 30.0, 'pixel_format': 'yuv420p',
                'audio_codec':'aac','audio_rate':48000,'audio_stereo':True}
    errors = [f'{key}: expected {expected}, got {report[key]}'
              for key, expected in required.items() if report[key] != expected]
    intended=timeline['duration_frames']/timeline['fps']
    report['expected_duration_seconds']=intended
    if abs(duration-intended)>.5:
        errors.append('Decoded video differs from the narration timeline by over 0.5 seconds')
    if report['video_frames']!=timeline['duration_frames']:
        errors.append('The decoded frame count differs from the locked scene timeline')
    report['audio_sources']=sorted({x['audio']['path'] for x in timeline['scenes'] if x.get('audio')})
    errors.extend(speech_errors(report['audio']))
    if report['freeze']['percent']>15:
        errors.append('More than 15 percent of the video is frozen')
    report['captions']=verify_captions(caption_path(episode),duration)
    errors.extend(report['captions']['errors'])
    report['deliverables'],pack_errors=check_package(episode,path,ffmpeg,intended)
    errors.extend(pack_errors)
    sheet = path.with_name(f'{path.stem}-phone.jpg')
    report['contact_sheet'] = {'file': sheet.name, 'frame_width_px': 390,
                               'sample_times_seconds': contact_sheet(ffmpeg, path, duration, sheet)}
    if inputs != validation_inputs(episode):
        raise RuntimeError('The timeline or captions changed during media QA. Run the check again.')
    report['mechanical_errors'] = errors
    apply_visual_review(report, episode)
    status = save_report(report, episode)
    print(sheet)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mp4', type=Path, help='Complete 1440p master to decode and inspect')
    parser.add_argument('--episode-dir', type=Path, help='Directory holding its exact timeline and SRT')
    parser.add_argument('--ffmpeg', default=None, help='FFmpeg executable, defaults to FFmpeg on PATH')
    parser.add_argument('--refresh-review', action='store_true',
                        help='Apply the visual review if the media and mechanical QA inputs are unchanged')
    args = parser.parse_args()
    if not args.mp4.is_file() or args.mp4.suffix.lower() != '.mp4':
        parser.error('Supply an existing MP4 file.')
    path = args.mp4.resolve()
    episode = (args.episode_dir or args.mp4.parent.parent).resolve()
    if args.refresh_review:
        try:
            return refresh_visual_review(path, episode)
        except ValueError as error:
            parser.error(str(error))
    ffmpeg = args.ffmpeg or shutil.which('ffmpeg')
    if not ffmpeg:
        parser.error('FFmpeg is unavailable. Supply its executable with --ffmpeg.')
    return check_master(path, ffmpeg, episode)


if __name__ == '__main__':
    raise SystemExit(main())
