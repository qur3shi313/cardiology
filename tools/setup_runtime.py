"""Prepare the FFmpeg executable path shared by the existing episode renderers."""

import argparse
from pathlib import Path
import re
import shutil
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'work/video-runtime/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
ENCODERS = ('libx264', 'aac', 'mov_text')


def verify_encoders(executable: Path) -> None:
    result = subprocess.run(
        [str(executable), '-hide_banner', '-encoders'],
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    missing = [encoder for encoder in ENCODERS if not re.search(rf'^\s*\S+\s+{encoder}\s', result.stdout, re.M)]
    if missing:
        raise SystemExit('FFmpeg is missing these encoders: ' + ', '.join(missing))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, help='Use a compatible executable already installed on this machine.')
    args = parser.parse_args()
    if args.ffmpeg is not None:
        source = args.ffmpeg.resolve(strict=True)
    else:
        import imageio_ffmpeg

        source = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve(strict=True)
    verify_encoders(source)

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if source != DESTINATION.resolve():
        candidate = DESTINATION.with_suffix('.setup-tmp')
        shutil.copy2(source, candidate)
        candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR)
        candidate.replace(DESTINATION)
    print(f'FFmpeg ready at {DESTINATION.relative_to(ROOT).as_posix()}')


if __name__ == '__main__':
    main()
