"""Assemble an episode once every authored picture is present."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import time

from .__main__ import SERIES, LEGACY_FFMPEG, load_timeline, render_episode, picture_cache, read_media
from .finish import finish
from .qa import check_master, file_hash


def ready(episode):
    try:
        timeline=load_timeline(episode)
    except FileNotFoundError:
        return False
    return all(not scene['footage'].get('reference_only') for scene in timeline['scenes'])


@contextmanager
def exclusive_build(path):
    # OS locks release if a worker exits or crashes. The file itself can persist.
    with path.open('ab+') as lock:
        if lock.tell()==0:
            lock.write(b'\0')
            lock.flush()
        lock.seek(0)
        if os.name=='nt':
            import msvcrt
            def acquire(): msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            def release(): msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            def acquire(): fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            def release(): fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
        try:
            acquire()
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            lock.seek(0)
            release()


def build(episode, ffmpeg):
    delivery=episode/'delivery'
    delivery.mkdir(exist_ok=True)
    with exclusive_build(delivery/'.batch.lock') as acquired:
        if not acquired:
            print(f'{episode.name}: another worker already owns this film',flush=True)
            return 0
        timeline=load_timeline(episode)
        # The cache tokens include the exact picture bytes and locked timing.
        paths={episode/'timeline.json',episode/timeline.get('caption_file','captions.en.srt'),
               episode/'finish-config.json'}
        paths.update(read_media(scene['audio']).path for scene in timeline['scenes'] if scene.get('audio'))
        fingerprint={
            'picture_tokens':[picture_cache(scene,'slow').stem for scene in timeline['scenes']],
            'input_hashes':{str(p):file_hash(p) for p in sorted(paths) if p.is_file()},
        }
        master=delivery/f'{episode.name}-1440p.mp4'
        state=delivery/'.batch-completed.json'
        if state.is_file() and master.is_file() and (episode/'QA.json').is_file():
            prior=json.loads(state.read_text(encoding='utf-8'))
            if prior.get('fingerprint')==fingerprint and prior.get('master_mtime_ns')==master.stat().st_mtime_ns:
                print(f'{episode.name}: these exact pictures already have a complete assembly and QA record',flush=True)
                return int(json.loads((episode/'QA.json').read_text(encoding='utf-8')).get('status')!='pass')
        render_episode(ffmpeg,episode,1,'slow')
        if episode.name=='episode-01' or (episode/'finish-config.json').is_file():
            finish(episode,ffmpeg)
        status=check_master(master,str(ffmpeg),episode)
        temporary=state.with_suffix('.tmp')
        temporary.write_text(json.dumps({'fingerprint':fingerprint,'master_mtime_ns':master.stat().st_mtime_ns})+'\n',
                             encoding='utf-8')
        temporary.replace(state)
        return status


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
    status=build(episode,args.ffmpeg.resolve())
    if status:
        print(f'{args.episode}: check QA.json and complete visual review before any release.',flush=True)
    return status


if __name__=='__main__':
    raise SystemExit(main())
