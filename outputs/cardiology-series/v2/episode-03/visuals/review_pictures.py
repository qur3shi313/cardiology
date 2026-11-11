"""Decode the silent Episode 03 pictures and sample them at phone size."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import av
from PIL import Image, ImageDraw

from render_devices import BASE, FPS, HEIGHT, WIDTH


HERE = Path(__file__).resolve().parent
PHONE = (390, 219)
KEY_TIMES = {
    1: (3, 6.3, 8.3, 10.7, 12.5, 14.4),
    2: (3.7, 7.7, 11.8),
    3: (3.7, 6.1, 8.8, 11.3),
    4: (3.7, 6, 8, 11.8),
    5: (3.8, 6.3, 9.9),
    6: (2.8, 4.7, 8.5, 12.4, 14.4),
    7: (2.4, 3.7, 6.4, 9.3, 12),
    8: (2.6, 5.5, 9.7, 11.9),
    9: (3, 7.4, 10.7, 13.3),
    10: (3.9, 7.3, 8.8, 10.4),
    11: (1.7, 3.2, 4.6, 8.3, 10.8),
    12: (4.5,),
}


def file_hash(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def review(index):
    source = HERE/f'P{index:02d}.mp4'
    expected = BASE[index]*FPS
    intervals = [*range(0,BASE[index],5), *KEY_TIMES[index]]
    requested = {min(expected-1,round(time*FPS)) for time in intervals} | {expected-1}
    pictures = []
    with av.open(str(source)) as container:
        stream = container.streams.video[0]
        stream.thread_count = 1
        actual = 0
        for frame in container.decode(stream):
            if actual in requested:
                phone = frame.reformat(width=PHONE[0], height=PHONE[1], format='rgb24').to_image()
                pictures.append((f'P{index:02d} · {actual/FPS:.2f} s', phone))
            actual += 1
        stats = {
            'file': source.name,
            'sha256': file_hash(source),
            'frames': actual,
            'fps': str(stream.average_rate),
            'size': [stream.width,stream.height],
            'codec': stream.codec_context.name,
            'pixel_format': stream.format.name,
            'audio_streams': len(container.streams.audio),
            'samples': len(pictures),
        }
        if (actual != expected or stream.average_rate != Fraction(FPS,1)
                or stats['size'] != [WIDTH,HEIGHT] or stats['codec'] != 'h264'
                or stats['pixel_format'] != 'yuv420p' or stats['audio_streams']):
            raise ValueError(f'Unexpected decoded picture metadata in {source.name}: {stats}')
    return stats, pictures


def sheet(destination, frames):
    columns = 3
    height = PHONE[1]+22
    size = (PHONE[0]*columns, height*((len(frames)+columns-1)//columns))
    contact = Image.new('RGB',size,'#163c35')
    pen = ImageDraw.Draw(contact)
    for i,(label,image) in enumerate(frames):
        x,y = (i%columns)*PHONE[0],(i//columns)*height
        contact.paste(image,(x,y))
        pen.text((x+8,y+PHONE[1]+3),label,fill='#edf8ed')
    contact.save(destination,quality=91)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('pictures',nargs='*',type=int)
    args = cli.parse_args()
    ids = args.pictures or list(BASE)
    if len(set(ids))!=len(ids) or any(i not in BASE for i in ids):
        cli.error('Select distinct episode pictures from 1 to 12')
    stats, frames = [], []
    for index in ids:
        result, samples = review(index)
        stats.append(result)
        frames.extend(samples)
        print(f'{result["file"]} {result["frames"]} frames decoded',flush=True)
    for start in range(0,len(frames),15):
        sheet(HERE/f'visual-review-{start//15+1}.jpg',frames[start:start+15])
    (HERE/'visual-decode.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
