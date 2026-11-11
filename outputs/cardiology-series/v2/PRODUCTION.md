# Production and release status

The 20 dates in [the release ledger](schedule.json) are targets. A YouTube date is confirmed only when the complete episode and its companion Short pass review, the correct channel and slot are checked, and Studio reads back the scheduled date, time zone, visibility and watch URL. No v2 release is confirmed yet. The original uploads remain unchanged.

The first combined film is 6:59.600 and uses the selected original Alexander recordings. Its 40-scene manifest, original source map and 990 exact caption words are locked. Native wrist, groin, root, contrast, and recovery artwork is in production. The second film uses the original full Alexander narration. The third and fourth films have complete Alexander takes and word alignment. The original angioplasty, drug-coated balloon and TAVI voices are retained for episodes 6, 8 and 18.

All 20 topics have sourced writing and picture direction. The ledger distinguishes scripts and timelines from complete media. Any unfinished file or failed review remains outside the release queue.

## Build a full episode

From the repository root, use the dependencies in `requirements.txt`, prepare the local FFmpeg path and set `PYTHONPATH=tools`. The renderer reads one scene timeline, actual narration ranges and explicit picture selections. An unselected or reference-only picture stops assembly.

```text
python -m elysian_video validate episode-01
python -m elysian_video render episode-01
python -m elysian_video.finish episode-01
python -m elysian_video.qa outputs/cardiology-series/v2/episode-01/delivery/episode-01-1440p.mp4 --ffmpeg PATH_TO_FFMPEG
```

Review the full decoded film, representative phone frames and the exact device transitions. Record the visual, anatomical, audio and caption checks against the master hash. The review status stays blocked until the technical and editorial gates both pass. The old queue is preserved as history.
