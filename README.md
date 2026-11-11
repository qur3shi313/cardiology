# Elysian Biomedical Cardiology Education Series

Production repository for Elysian Biomedical LLP’s original interventional cardiology education videos. The series explains why a procedure is considered, what the clinical team does, how it checks the result, and what recovery may involve. The animations use illustrative anatomy and simulated medical imaging. The completed videos use synthetic English narration and timed English captions.

## Current rebuild

[Production status](outputs/cardiology-series/v2/PRODUCTION.md) · [20-episode plan](outputs/cardiology-series/v2/PLAN.md) · [Target release dates and verification status](outputs/cardiology-series/v2/schedule.json)

## Original release records

The first topic was split into two films. The video numbers below follow the YouTube release order. Releases are at 18:00 Pakistan time where scheduled. Status is from the verified project records on 11 November 2026. Scheduled watch pages may become available at release time.

| Video | Topic | YouTube | Review files |
| --- | --- | --- | --- |
| 1 · Episode 01A | Coronary angiography through the right wrist | [Published](https://youtu.be/YIw1bSATJqY) | [Revised master](outputs/cardiology-series/episode-01/revision/full-review/elysian-angiography-radial-revised.mp4) · [English captions](outputs/cardiology-series/episode-01/revision/radial-alexander.en.srt) |
| 2 · Episode 01B | Coronary angiography through the right groin | [Published](https://youtu.be/sFbJGjFIuHo) | [Revised master](outputs/cardiology-series/episode-01/revision/full-review/elysian-angiography-femoral-revised.mp4) · [English captions](outputs/cardiology-series/episode-01/revision/femoral-alexander.en.srt) |
| 3 · Episode 02 | Coronary angioplasty and stent placement | [Scheduled for 12 November](https://youtu.be/IUdtCju857U) | [Master](outputs/cardiology-series/episode-02/production/delivery/elysian-coronary-angioplasty-stent.mp4) · [English captions](outputs/cardiology-series/episode-02/production/delivery/elysian-coronary-angioplasty-stent.en.srt) |
| 4 · Episode 03 | Coronary drug-coated balloons | [Scheduled for 13 November](https://youtu.be/Zr13Qska-QU) | [Master](outputs/cardiology-series/episode-03/production/delivery/elysian-coronary-drug-coated-balloons.mp4) · [English captions](outputs/cardiology-series/episode-03/production/delivery/elysian-coronary-drug-coated-balloons.en.srt) |
| 5 · Episode 04 | Transcatheter aortic valve implantation (TAVI/TAVR) | [Scheduled for 14 November](https://youtu.be/V7NjFLTYhuE) | [Master](outputs/cardiology-series/episode-04/production/delivery/elysian-tavi-tavr.mp4) · [English captions](outputs/cardiology-series/episode-04/production/delivery/elysian-tavi-tavr.en.srt) |
| 6 · Episode 05 | Wrist vs groin access and how the team chooses | [Scheduled for 15 November](https://youtu.be/wTj-F4zotns) | [Delivered Canva export](outputs/cardiology-series/episode-05/production/delivery/wrist-vs-groin-canva-export.mp4) · [Matching English captions](outputs/cardiology-series/episode-05/production/delivery/wrist-vs-groin-canva-export.en.srt) |
| 7 · Episode 06 | What the sheath, guidewire, catheter and contrast each do | In production for 16 November | [Script](outputs/cardiology-series/episode-06/narration-script.md) · [Storyboard](outputs/cardiology-series/episode-06/scene-timing-brief.md) · [Clinical sources](outputs/cardiology-series/episode-06/SOURCES.md) · [First device animation](outputs/cardiology-series/episode-06/visuals/device-roles-overview.mp4) |

[Release queue and approved topic order](outputs/cardiology-series/production-queue.md) · [Reviewer guide](REVIEW-GUIDE.md)

## Local setup

The MP4s and SRTs can be reviewed with a player that supports separate subtitle files. Rendering and assembly use Python with Pillow and NumPy. Run these commands from the repository root to prepare the Windows FFmpeg path expected by the current scripts.

```bash
python -m pip install -r requirements.txt
python tools/setup_runtime.py
```

The helper locates FFmpeg through `imageio-ffmpeg`. To use a compatible system install, run `python tools/setup_runtime.py --ffmpeg /path/to/ffmpeg`. The renderers retain the workspace-relative layout used for the delivered masters. The original company logo is at `work/company-logo-original-686.jpg`. The minimal Fira Sans and Josefin Sans files are in the website and legacy font folders with their SIL Open Font License notices. Start with [the assembly script](outputs/cardiology-series/assemble-episode.py) and its `--help` output if reviewing the production pipeline.

## Review boundaries

Use the six delivery pairs in the table as the baseline. The Episode 01 original cuts, prototypes, silent clips and alternate assemblies are production history. The wrist-versus-groin Canva export is the version paired with its own adjusted captions. For Video 7, evaluate the script and storyboard alongside the rendered work available at this checkpoint.

The source notes record the clinical evidence used and the limits of each depicted example. Technical playback, transcript and visual checks support review. Independent clinician sign-off should be identified separately if obtained. Studio account proofs, private edit and collaboration links, browser records, and machine caches are excluded from this review snapshot.
