"""Record a separately confirmed YouTube Short from the exact approved package."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re

from .__main__ import SERIES
from .record_studio import load, save
from .repo_release import hash_file


def record(number, video, native_time, title, package=None):
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
        raise ValueError('Use the exact confirmed Short ID.')
    ledger = SERIES/'schedule.json'
    schedule = load(ledger)
    row = next(item for item in schedule['targets'] if item['topic']==number)
    episode = SERIES/row['episode']
    target = datetime.fromisoformat(row['target'])
    when = datetime.fromisoformat(native_time)
    if not row.get('studio_verified') or when.utcoffset()!=timedelta(hours=5) or when.date()!=target.date():
        raise ValueError('The Short must share the verified film’s Pakistan release date.')
    if any(item.get('video_id')==video or
           (item['topic']!=number and item.get('short',{}).get('video_id')==video)
           for item in schedule['targets']):
        raise ValueError('This video ID is already recorded for another release.')
    if row.get('short') and row['short'].get('video_id')!=video:
        raise ValueError('Refusing to replace a verified companion Short.')
    source = package.resolve() if package else episode.resolve()
    if source.name!=episode.name or not source.is_relative_to(SERIES.resolve()):
        raise ValueError('The package must be the matching episode in the series.')
    qa = load(source/'QA.json')
    a = qa.get('deliverables',{}).get('short',{})
    if (qa.get('status')!='pass' or qa.get('errors') or
        qa.get('sha256')!=row.get('master_sha256') or not a.get('full_decode') or
        (a.get('width'),a.get('height'))!=(1080,1920) or
        not 0<a.get('duration_seconds',0)<=45 or
        hash_file(source/'delivery'/a['file'])!=a.get('sha256')):
        raise ValueError('The exact Short is not bound to the verified long film and passing package.')
    short = {'title':title,'status':'scheduled','studio_verified':True,
             'video_id':video,'watch_url':'https://www.youtube.com/shorts/'+video,
             'target':when.isoformat(),'timezone':'Asia/Karachi','sha256':a['sha256'],
             'duration_seconds':a['duration_seconds'],'captions':'English burned into picture',
             'studio_checks':'complete_no_issues'}
    meta_path = episode/'youtube-metadata.json'
    fields = load(meta_path)
    fields['short'] = short
    row['short'] = short
    save(meta_path,fields)
    save(ledger,schedule)
    return short


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('episode',type=int,choices=range(1,21))
    cli.add_argument('video')
    cli.add_argument('native_time')
    cli.add_argument('title')
    cli.add_argument('--package',type=Path)
    args = cli.parse_args()
    item = record(args.episode,args.video,args.native_time,args.title,args.package)
    print(f"{item['watch_url']} scheduled for {item['target']}.")


if __name__=='__main__':
    main()
