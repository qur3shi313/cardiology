"""Compare the two release candidates and generate decoded revision evidence."""

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from math import ceil, pi
import re
import subprocess

import av
from PIL import Image, ImageDraw

from rebuild import CHANGED, DELIVERY, EPISODE, FILM, LEGACY_FFMPEG, MASTER, ORIGINAL, digest
from elysian_video.qa import freeze_report, inspect_audio, invoke, metadata, speech_errors, verify_captions


def packet_identities(filename):
    packets = defaultdict(list)
    with av.open(str(filename)) as media:
        for packet in media.demux():
            if packet.size:
                packets[packet.stream.type].append((packet.pts, packet.dts, packet.duration,
                                                    sha256(bytes(packet)).hexdigest()))
    return packets


def verify_streams(rows):
    prior = packet_identities(ORIGINAL / 'delivery' / MASTER.name)
    revised = packet_identities(MASTER)
    differences = {}
    for row in rows:
        start, end = row['start_frame'], row['end_frame']
        ident = row['id']
        left, right = prior['video'][start:end], revised['video'][start:end]
        same_presentation_times = sorted((p[0], p[2]) for p in left) == sorted((p[0], p[2]) for p in right)
        differences[ident] = {
            'frames': end - start,
            'identical_payloads': sum(p[-1] == q[-1] for p, q in zip(left, right)),
            'timestamps_match': same_presentation_times,
        }
        if differences[ident]['timestamps_match'] is False:
            raise ValueError(f'{ident} timestamps changed')
        if ident not in CHANGED and left != right:
            raise ValueError(f'{ident} picture payload changed')
    for stream in ('audio', 'subtitle'):
        if prior[stream] != revised[stream] or not revised[stream]:
            raise ValueError(f'{stream} packets or timestamps changed')
    if len(prior['video']) != len(revised['video']) or len(revised['video']) != rows[-1]['end_frame']:
        raise ValueError('The master packet count differs from the exact timeline')
    return differences, len(revised['audio']), len(revised['subtitle'])


def sample_frame(path, seconds, width):
    frame = subprocess.run([str(LEGACY_FFMPEG), '-hide_banner', '-v', 'error', '-threads', '2',
                            '-filter_threads', '2', '-ss', f'{seconds:.6f}', '-i', str(path),
                            '-map', '0:v:0', '-frames:v', '1', '-vf', f'scale={width}:-2:flags=lanczos',
                            '-c:v', 'png', '-f', 'image2pipe', '-'], check=True, capture_output=True)
    with Image.open(BytesIO(frame.stdout)) as image:
        return image.convert('RGB')


def make_sheet(frames, path, columns):
    width, height = frames[0][1].size
    pitch_x, pitch_y = width + 12, height + 28
    sheet = Image.new('RGB', (pitch_x * columns, pitch_y * ceil(len(frames) / columns)), '#edf6ef')
    draw = ImageDraw.Draw(sheet)
    for index, (label, frame) in enumerate(frames):
        x, y = index % columns * pitch_x + 6, index // columns * pitch_y
        sheet.paste(frame, (x, y))
        draw.text((x + 2, y + height + 6), label, fill='#173f35')
    sheet.save(path, quality=93, subsampling=0)


def radiograph_bounds(frame):
    # Compare the pale imaging field with the surrounding dark background.
    w, h = frame.size
    row = [x for x in range(w) if min(frame.getpixel((x, round(.55 * h)))) > 82]
    col = [y for y in range(round(h * .19), h) if min(frame.getpixel((w // 2, y))) > 82]
    return round(100 * ((max(row) - min(row) + 1) * (max(col) - min(col) + 1)) / (w * h), 2)


def check_picture():
    scene_samples = {
        'P01': (.15, 2.7, 6.3),
        'P25': (227.4, 233.8, 239.5, 246.0),
        'P28': (276.1, 280.3, 285.3, 290.4),
        'P29': (292.5, 294.4, 296.9),
        'P40': (412.16, 415.1, 419.53),
    }
    phone_frames, coverage = [], {}
    for ident, times in scene_samples.items():
        if ident != 'P40':
            coverage[ident] = []
        for seconds in times:
            frame = sample_frame(MASTER, seconds, 390)
            phone_frames.append((f'{ident}  {seconds:.2f} s', frame))
            if ident != 'P40':
                area = radiograph_bounds(frame)
                if area < 65:
                    raise ValueError(f'{ident} radiograph sampled at {seconds:.2f} s covers only {area}%')
                coverage[ident].append({'seconds': seconds, 'bounds_percent': area})
    make_sheet(phone_frames, EPISODE / 'changed-scenes-phone.jpg', 3)
    return coverage


def check_short_and_thumbnail():
    short = DELIVERY / 'episode-01-short.mp4'
    thumb = DELIVERY / 'episode-01-thumbnail.jpg'
    short_frames = [(f'{t:.2f} s', sample_frame(short, t, 320))
                    for t in (.2, 3, 6, 8.8, 11.7, 14.7, 18.2, 22.6)]
    make_sheet(short_frames, EPISODE / 'short-phone.jpg', 4)
    with Image.open(thumb) as image:
        image.resize((320, 180), Image.Resampling.LANCZOS).save(EPISODE / 'thumbnail-phone.jpg', quality=96)
    return digest(short), digest(thumb)


def check_master_technical(rows):
    probe = invoke(LEGACY_FFMPEG, '-i', MASTER, check=False)
    media = metadata(probe.stderr.decode('utf-8', 'replace'))
    required = {'codec': 'h264', 'width': 2560, 'height': 1440, 'fps': 30.0, 'pixel_format': 'yuv420p',
                'audio_codec': 'aac', 'audio_rate': 48000, 'audio_stereo': True}
    if any(media[k] != v for k, v in required.items()):
        raise ValueError(f'Master format mismatch: {media}')
    video = invoke(LEGACY_FFMPEG, '-v', 'info', '-xerror', '-threads', 2, '-filter_threads', 2,
                   '-progress', 'pipe:1', '-i', MASTER, '-map', '0:v:0', '-an',
                   '-vf', 'freezedetect=n=0.001:d=2', '-f', 'null', '-')
    progress = video.stdout.decode()
    duration = int(re.findall(r'^out_time_us=(\d+)\s*$', progress, re.MULTILINE)[-1]) / 1_000_000
    frame_count = int(re.findall(r'^frame=(\d+)\s*$', progress, re.MULTILINE)[-1])
    if frame_count != rows[-1]['end_frame'] or abs(duration - frame_count / 30) > .5:
        raise ValueError('Decoded duration does not match the exact frame count')
    motion = freeze_report(video.stderr.decode('utf-8', 'replace'), duration)
    if motion['percent'] > 15 or any(x['end_seconds'] - x['start_seconds'] > 6 for x in motion['intervals']):
        raise ValueError(f'Master motion falls below the release thresholds: {motion}')
    audio = inspect_audio(LEGACY_FFMPEG, MASTER)
    captions = verify_captions(EPISODE / 'episode-01.en.srt', duration)
    issues = speech_errors(audio) + captions['errors']
    if issues:
        raise ValueError(issues)
    return {'metadata': media, 'full_video_decode': True, 'frame_count': frame_count,
            'duration_seconds': duration, 'freeze': motion, 'audio': audio, 'captions': captions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master-only', action='store_true')
    options = parser.parse_args()
    rows = json.loads((EPISODE / 'timeline.json').read_text(encoding='utf-8-sig'))['scenes']
    packets, voice_count, caption_count = verify_streams(rows)
    coverage = check_picture()
    _, _, width, height, radius = FILM
    evidence = {
        'master_sha256': digest(MASTER),
        'voice_packet_count_identical': voice_count,
        'embedded_caption_packets_identical': caption_count,
        'original_timeline_sha256': digest(ORIGINAL / 'timeline.json'),
        'timeline_sha256': digest(EPISODE / 'timeline.json'),
        'original_captions_sha256': digest(ORIGINAL / 'episode-01.en.srt'),
        'captions_sha256': digest(EPISODE / 'episode-01.en.srt'),
        'pictures': packets,
        'radiograph_bounds_percent': coverage,
        'radiograph_nominal_bounding_box_percent': round(100 * width * height / (1280 * 720), 2),
        'radiograph_nominal_area_after_corners_percent': round(
            100 * (width * height - (4 - pi) * radius ** 2) / (1280 * 720), 2),
        'changed_scenes_contact_sheet': 'changed-scenes-phone.jpg',
    }
    if options.master_only:
        evidence['master_technical'] = check_master_technical(rows)
    else:
        previous = EPISODE / 'master-preflight.json'
        if previous.is_file():
            prior = json.loads(previous.read_text(encoding='utf-8'))
            if prior['master_sha256'] == evidence['master_sha256']:
                evidence['master_technical'] = prior.get('master_technical')
        short_hash, thumbnail_hash = check_short_and_thumbnail()
        old_short = packet_identities(ORIGINAL / 'delivery' / 'episode-01-short.mp4')
        new_short = packet_identities(DELIVERY / 'episode-01-short.mp4')
        same_short_voice = old_short['audio'] == new_short['audio']
        evidence.update(short_sha256=short_hash, thumbnail_sha256=thumbnail_hash,
                        short_contact_sheet='short-phone.jpg', thumbnail_contact_sheet='thumbnail-phone.jpg',
                        short_voice_packets_identical_to_original=same_short_voice)
    target = EPISODE / ('master-preflight.json' if options.master_only else 'exact-rebuild-evidence.json')
    target.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
