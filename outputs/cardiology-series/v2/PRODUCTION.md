# Production and release status

The 20 dates in [the release ledger](schedule.json) are targets. A YouTube date is confirmed only when the complete episode and its companion Short pass review, the correct channel and slot are checked, and Studio reads back the scheduled date, time zone, visibility and watch URL. No v2 release is confirmed yet. The original uploads remain unchanged.

The first combined film is 6:59.600. Its 40-scene manifest, original Alexander audio selection and 990 exact caption words are locked. The 16 native draped or clothed route, access and recovery clips have verified frame counts and full decodes. The first complete cut exceeded the motion limit and is being corrected. Read the [current release checkpoint](RELEASE-CHECKPOINT.md) for exact per-film status.

All 20 episodes have a clinical source map, full script, storyboard, frame-locked timeline and Alexander narration. All 21 audio source files decoded. The [narration record](narration-verification.json) records the 862 caption cues and what was measured. Those checks cover source voice and captions; they do not certify a finished film.

Any unfinished file or failed review remains outside the release queue. There are no new YouTube watch links or schedule confirmations.

## Build a full episode

From the repository root, use the dependencies in `requirements.txt`, prepare the local FFmpeg path and set `PYTHONPATH=tools`. The renderer reads one scene timeline, actual narration ranges and explicit picture selections. An unselected or reference-only picture stops assembly.

```text
python -m elysian_video validate episode-01
python -m elysian_video render episode-01
python -m elysian_video.finish episode-01
python -m elysian_video.qa outputs/cardiology-series/v2/episode-01/delivery/episode-01-1440p.mp4 --ffmpeg PATH_TO_FFMPEG
```

Review the full decoded film, representative phone frames and the exact device transitions. The checker also decodes both derivative videos and independently measures the Short's speech level. Record the visual, anatomical, audio and caption checks against the master hash. The review status stays blocked until the technical and editorial gates both pass. The [legacy inventory](DELETED-VIDEOS.md) records what remains in Studio.
