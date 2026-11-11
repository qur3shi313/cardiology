"""Assemble an episode once every authored picture is present."""
import argparse
from pathlib import Path
import time

from .__main__ import SERIES, LEGACY_FFMPEG, load_timeline, render_episode
from .finish import finish
from .qa import check_master


def ready(episode):
    try:
        timeline=load_timeline(episode)
    except FileNotFoundError:
        return False
    return all(not scene['footage'].get('reference_only') for scene in timeline['scenes'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode',choices=tuple(f'episode-{i:02}' for i in range(1,21)))
    parser.add_argument('--wait-minutes',type=float,default=75)
    parser.add_argument('--ffmpeg',default=LEGACY_FFMPEG,type=Path)
    args=parser.parse_args()
    episode=SERIES/args.episode
    deadline=time.monotonic()+args.wait_minutes*60
    print(f'{args.episode}: waiting for all reviewed scene files',flush=True)
    while not ready(episode):
        if time.monotonic()>=deadline:
            raise SystemExit(f'{args.episode}: authoring is incomplete; assembly has not started')
        time.sleep(15)
    print(f'{args.episode}: all picture sources present; assembling the complete film',flush=True)
    render_episode(args.ffmpeg.resolve(),episode,1,'slow')
    if args.episode=='episode-01' or (episode/'finish-config.json').is_file():
        finish(episode,args.ffmpeg.resolve())
    master=episode/'delivery'/f'{episode.name}-1440p.mp4'
    status=check_master(master,str(args.ffmpeg.resolve()),episode)
    if status:
        print(f'{args.episode}: check QA.json and complete visual review before any release.',flush=True)
    return status


if __name__=='__main__':
    raise SystemExit(main())
