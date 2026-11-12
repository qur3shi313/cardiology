# Coronary angiogram through the wrist or groin

This Episode 01 revision expands the simulated coronary X-ray field in P01, P25, P28 and P29. The source catheter and artery geometry, projections, clinical sequence and scene timings carry over. P40 shows the series name, full title of the next episode, and clinical source names for 7.5 seconds. The right column leaves room for YouTube end screen elements.

The [clinical source map](../../../episode-01/SOURCES.md) and [original Episode 01 package](../../../episode-01/) remain with the approved narration and edit. The revised master uses the original narration and timed subtitle packets. The matching English SRT and chapters are included here.

Run `python rebuild.py --ffmpeg /path/to/ffmpeg` with the workspace render dependencies installed. It uses the original release candidate and its scene cache index. It recovers unavailable scene encodes from the release candidate at exact keyframes. Run `python check_exact_rebuild.py --master-only` to check the decoded master, and `python check_exact_rebuild.py` to compare packets and create the package samples before recording the visual review and running the shared validator.
