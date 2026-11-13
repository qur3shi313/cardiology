"""Archive and record the reviewed first Elysian cardiac surgery episode."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re
from urllib.parse import urlencode

from .__main__ import ROOT
from .record_studio import load, save
from .repo_release import GitHub, REPO_PATH, credential, files, hash_file


SERIES = ROOT / 'outputs/cardiac-surgery-series'
EPISODE = SERIES / 'episode-01'
CHANNEL_ID = 'UCEJkz6_una0fWFDmIUVQmfg'
LONG_TIME = '2026-12-01T09:10:00+05:00'
SHORT_TIME = '2026-12-01T09:25:00+05:00'
TITLE = 'Why the Heart Team may choose coronary bypass surgery'
TAG = 'cardiac-surgery-episode-01'


def package():
    qa = load(EPISODE / 'QA.json')
    sources = files(EPISODE, qa)
    expected = (
        'episode-01-1440p.mp4', 'episode-01-1080p.mp4', 'episode-01-short.mp4',
        'episode-01-thumbnail.jpg', 'captions.en.srt', 'chapters.txt', 'QA.json',
    )
    if tuple(path.name for path in sources) != expected:
        raise ValueError('Expected the complete seven-file Cardiac Surgery Episode 1 package')
    assets = []
    for path in sources:
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(EPISODE.resolve()) or not 0 < path.stat().st_size < 2 * 1024**3:
            raise ValueError(f'Invalid delivery asset: {path.name}')
        assets.append({'name': path.name, 'size': path.stat().st_size,
                       'digest': 'sha256:' + hash_file(path)})
    validated = qa.get('validation_inputs', {})
    if (validated.get('caption_sha256') != assets[4]['digest'].removeprefix('sha256:')
            or validated.get('timeline_sha256') != hash_file(EPISODE / 'timeline.json')):
        raise ValueError('The caption track or timeline differs from the reviewed package')
    return sources, assets


def same_asset(received, expected):
    return received.get('state') == 'uploaded' and all(
        received.get(key) == expected[key] for key in ('name', 'size', 'digest'))


def verify_assets(received, expected):
    by_name = {asset['name']: asset for asset in received}
    if (len(received) != len(expected)
            or any(not same_asset(by_name.get(asset['name'], {}), asset) for asset in expected)):
        raise RuntimeError('GitHub did not return all seven exact uploaded assets')
    return [{**asset, 'url': by_name[asset['name']]['browser_download_url']} for asset in expected]


def archive(repo):
    sources, expected = package()
    api = GitHub(credential(repo))

    def request(method, path, body=None):
        return api.request(method, 'api.github.com', REPO_PATH + path, body)

    releases = request('GET', '/releases?per_page=100')
    matches = [release for release in releases if release['tag_name'] == TAG]
    if len(matches) > 1:
        raise RuntimeError(f'GitHub returned multiple releases for {TAG}')
    if matches:
        release = matches[0]
    else:
        release = request('POST', '/releases', {
            'tag_name': TAG, 'target_commitish': 'main', 'name': TITLE,
            'draft': True, 'prerelease': False,
            'body': 'Complete Cardiac Surgery Education episode, captioned vertical edit, and reviewed media package.',
        })
    release_path = f"/releases/{release['id']}"
    assets_path = release_path + '/assets?per_page=100'
    received = request('GET', assets_path)
    prior = {asset['name']: asset for asset in received}
    if not set(prior).issubset({asset['name'] for asset in expected}):
        raise ValueError('The existing release contains unexpected assets')
    if release['draft']:
        for path, asset in zip(sources, expected):
            existing = prior.get(path.name)
            if existing and same_asset(existing, asset):
                continue
            if existing:
                if existing.get('state') != 'starter' or existing.get('digest'):
                    raise ValueError(f'Existing asset differs from the approved file: {path.name}')
                request('DELETE', f"/releases/assets/{existing['id']}")
            uploaded = api.request('POST', 'uploads.github.com',
                                   REPO_PATH + release_path + '/assets?' + urlencode({'name': path.name}),
                                   asset=path)
            if not same_asset(uploaded, asset):
                raise RuntimeError(f'GitHub could not verify the transfer: {path.name}')
            print(f'Verified {path.name}', flush=True)
        verify_assets(request('GET', assets_path), expected)
        release = request('PATCH', release_path, {'draft': False})
    if release.get('draft') is not False or release.get('prerelease'):
        raise RuntimeError('The exact GitHub release is not public')
    assets = verify_assets(request('GET', assets_path), expected)
    receipt = {'tag': TAG, 'release_url': release['html_url'], 'assets': assets}
    save(EPISODE / 'github-release.json', receipt)
    return receipt


def confirmed_time(value, expected):
    actual = datetime.fromisoformat(value)
    if actual.isoformat() != expected or actual.utcoffset() != timedelta(hours=5):
        raise ValueError(f'The Studio time must match {expected} in Asia/Karachi')
    return expected


def video_id(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        raise ValueError('Use the video ID from the native Studio confirmation')
    return value


def record_studio(channel, video, when, master_sha, *, short_video=None, short_time=None, short_sha=None):
    if channel != CHANNEL_ID:
        raise ValueError('The native confirmation must be for Elysian Biomedical LLP')
    video = video_id(video)
    when = confirmed_time(when, LONG_TIME)
    _, assets = package()
    if assets[0]['digest'] != 'sha256:' + master_sha:
        raise ValueError('The supplied Studio upload hash differs from the reviewed master')
    path = SERIES / 'schedule.json'
    schedule = load(path) if path.is_file() else {'schema_version': 1, 'timezone': 'Asia/Karachi', 'targets': []}
    previous = next((row for row in schedule['targets'] if row['episode'] == EPISODE.name), {})
    if previous.get('studio_verified') and (
            previous['video_id'] != video or previous['target'] != when
            or previous['master_sha256'] != master_sha):
        raise ValueError('An existing verified Studio release cannot be replaced by this recorder')
    used_ids = {
        native_id for existing in schedule['targets'] if existing['episode'] != EPISODE.name
        for native_id in (existing.get('video_id'), existing.get('short', {}).get('video_id'))
        if native_id
    }
    if video in used_ids:
        raise ValueError('The video ID is already verified for a different episode')
    row = {
        'episode': EPISODE.name, 'title': TITLE, 'channel_id': CHANNEL_ID,
        'video_id': video, 'watch_url': 'https://youtu.be/' + video,
        'target': when, 'timezone': 'Asia/Karachi', 'status': 'scheduled', 'studio_verified': True,
        'studio_checks': 'complete_no_issues', 'studio_subtitles': 'English published',
        'master_sha256': master_sha, 'assets': assets,
    }
    archive_path = EPISODE / 'github-release.json'
    if archive_path.is_file():
        receipt = load(archive_path)
        expected = {(asset['name'], asset['size'], asset['digest']) for asset in assets}
        remote = {(asset['name'], asset['size'], asset['digest']) for asset in receipt['assets']}
        if receipt['tag'] != TAG or len(receipt['assets']) != len(assets) or remote != expected:
            raise ValueError('The archive receipt does not match the exact seven-file package')
        row['github_release'] = receipt['release_url']
    if any(value is not None for value in (short_video, short_time, short_sha)):
        if None in (short_video, short_time, short_sha):
            raise ValueError('An optional Short requires its confirmed native ID, time, and exact hash')
        short_video = video_id(short_video)
        if (short_video == video or short_video in used_ids
                or previous.get('short', {}).get('video_id', short_video) != short_video):
            raise ValueError('The Short must have its own distinct confirmed ID')
        if assets[2]['digest'] != 'sha256:' + short_sha:
            raise ValueError('The supplied Short hash differs from the reviewed companion')
        row['short'] = {
            'video_id': short_video, 'watch_url': 'https://www.youtube.com/shorts/' + short_video,
            'target': confirmed_time(short_time, SHORT_TIME), 'timezone': 'Asia/Karachi',
            'status': 'scheduled', 'studio_verified': True, 'studio_checks': 'complete_no_issues',
            'sha256': short_sha, 'captions': 'English burned into picture',
        }
    elif previous.get('short'):
        row['short'] = previous['short']
    schedule['targets'] = sorted(
        [existing for existing in schedule['targets'] if existing['episode'] != EPISODE.name] + [row],
        key=lambda item: item['target'],
    )
    save(path, schedule)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    release_parser = actions.add_parser('archive', help='Archive the completed reviewed package on GitHub')
    release_parser.add_argument('--repo', type=Path, default=ROOT / 'work/github-cardiology')
    actions.add_parser('verify-package', help='Print the reviewed package hashes without network or writes')
    studio = actions.add_parser('record-studio', help='Record an already verified Studio schedule')
    studio.add_argument('--channel-id', required=True)
    studio.add_argument('--video-id', required=True)
    studio.add_argument('--time', required=True)
    studio.add_argument('--master-sha', required=True)
    studio.add_argument('--short-id')
    studio.add_argument('--short-time')
    studio.add_argument('--short-sha')
    args = parser.parse_args()
    if args.action == 'archive':
        print(archive(args.repo.resolve())['release_url'])
    elif args.action == 'verify-package':
        for asset in package()[1]:
            print(f"{asset['digest']}  {asset['name']}")
    else:
        row = record_studio(args.channel_id, args.video_id, args.time, args.master_sha,
                            short_video=args.short_id, short_time=args.short_time, short_sha=args.short_sha)
        print(f"{row['watch_url']} scheduled for {row['target']}.")


if __name__ == '__main__':
    main()
