"""Record a YouTube Studio release only after native confirmation was observed."""

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

from .__main__ import ROOT, SERIES
from .repo_release import hash_file


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, data):
    pending = path.with_suffix('.tmp')
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n',
                       encoding='utf-8', newline='\n')
    pending.replace(path)


def record(number, video, native_time, master_sha, thumbnail):
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
        raise ValueError('Use the confirmed YouTube video ID.')
    episode = SERIES/f'episode-{number:02}'
    ledger = SERIES/'schedule.json'
    schedule = load(ledger)
    row = next(r for r in schedule['targets'] if r['topic']==number)
    publish = datetime.fromisoformat(native_time)
    if row['target']!=publish.isoformat() or publish.utcoffset()!=timedelta(hours=5):
        raise ValueError('The confirmed native date and time must match the assigned Pakistan slot.')
    if any((r.get('video_id')==video and r['topic']!=number) for r in schedule['targets']):
        raise ValueError('This video is already associated with a different episode.')
    if row.get('studio_verified') and row.get('video_id')!=video:
        raise ValueError('Refusing to replace an existing verified release.')
    master = episode/'delivery'/f'{episode.name}-1440p.mp4'
    if hash_file(master)!=master_sha:
        raise ValueError('The current master differs from the reviewed upload.')
    thumb_sha = hash_file(thumbnail.resolve(strict=True))
    caption_sha = hash_file(episode/'captions.en.srt')
    qa_path = episode/'QA.json'
    qa = load(qa_path) if qa_path.is_file() else {}
    qa_pass = (qa.get('status')=='pass' and qa.get('sha256')==master_sha
               and not qa.get('errors')
               and qa.get('deliverables',{}).get('thumbnail',{}).get('sha256')==thumb_sha)
    url = 'https://youtu.be/'+video
    row.update(status='scheduled',studio_verified=True,watch_url=url,video_id=video,
               master_sha256=master_sha,master_bytes=master.stat().st_size,
               master_preflight_passed=True,companion_package_qa_pending=not qa_pass,
               qa_passed=qa_pass,studio_checks='complete_no_issues')
    for item in schedule['targets']:
        artifact = SERIES/item['episode']/'github-release.json'
        if item.get('studio_verified') and artifact.is_file():
            release = load(artifact)
            if any(a.get('digest')=='sha256:'+item.get('master_sha256','')
                   for a in release['assets']):
                item['github_release']=release['release_url']
    metadata = episode/'youtube-metadata.json'
    fields = load(metadata)
    if fields.get('planned_release')!=row['target']:
        raise ValueError('The native date and prepared episode metadata differ.')
    fields.update(studio_release_verified=True,watch_url=url,video_id=video,master_sha256=master_sha,
                  studio_checks='complete_no_issues',studio_subtitles='English published',
                  studio_subtitles_sha256=caption_sha,studio_thumbnail_sha256=thumb_sha,
                  studio_schedule_confirmation={'publish_at':row['target'],'timezone':'Asia/Karachi'})
    save(metadata,fields)
    save(ledger,schedule)
    checkpoint = SERIES/'RELEASE-CHECKPOINT.md'
    old = checkpoint.read_text(encoding='utf-8-sig')
    verified = [r for r in schedule['targets'] if r['studio_verified']]
    prefix = old.split('\n- ',1)[0]
    suffix = old[old.index('The older videos'):]
    lines = []
    for item in schedule['targets']:
        day = datetime.fromisoformat(item['target'])
        if not item.get('studio_verified'):
            state = 'Ready for Studio' if item.get('qa_passed') else 'In production'
            lines.append(f"- {day.day} {day:%B} · {state} · {item['title']}")
            continue
        state = 'Public' if item.get('status')=='published' else day.strftime('%H:%M PKT')
        lines.append(f"- {day.day} {day:%B} · {state} · [{item['title']}]({item['watch_url']})")
    checkpoint.write_text(prefix+'\n'+'\n'.join(lines)+'\n\n'+suffix,
                          encoding='utf-8',newline='\n')
    return row, len(verified)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('episode',type=int,choices=range(1,21))
    cli.add_argument('video',help='Exact ID shown in the native confirmation.')
    cli.add_argument('native_time',help='Exact release ISO time confirmed by Studio.')
    cli.add_argument('master_sha',help='SHA-256 of the exact reviewed file uploaded.')
    cli.add_argument('thumbnail',type=Path,help='Exact reviewed thumbnail uploaded.')
    args = cli.parse_args()
    row,count = record(args.episode,args.video,args.native_time,args.master_sha,args.thumbnail)
    print(f"{row['episode']} recorded for {row['target']}; {count} Studio confirmations.")


if __name__=='__main__':
    main()
