# Editorial decisions for the combined cut

The master timeline is 12,588 frames at 30 fps, or 6:59.600. The spoken track consists of 990 words from the two approved Alexander recordings. Each retained line is a complete original sentence. The final sources card starts with the spoken outro and runs 7.5 seconds.

| Material in the two original films | Combined edit |
| --- | --- |
| Two opening questions and two introductions to the route | Use the original question once, with simulated contrast filling from the opening frame. Introduce the full video title after five seconds. The right-wrist and right-groin identifiers then appear at the start of their own examples. |
| Repeated setup, consent and reasons for testing | Use the wrist reasons-for-testing passage and the opening two preparation sentences once. Show staff monitoring visually with modest figures. |
| Identical descriptions of access details in both films | Keep the full radial needle-wire-sheath handoffs, with concise location and needle narration. Retain the fine groin wire and main iliac check, all six micropuncture exchange steps, and the optional groin access image. The groin route includes the final wire-and-catheter insertion visuals under its route narration. |
| Coronary imaging twice, with two different catheter choices | Follow the right-groin example through coronary imaging. The guidewire comes out before the left run. The left diagnostic catheter is replaced with the right catheter in this example, and the second guidewire comes out before the right run. The radial single-catheter example remains available in the original source materials. |
| Two readings of a sample angiogram | Use the first original groin result sentence and one next-steps passage. Use a separate treatment illustration if showing the balloon and stent. |
| Two full discharge sections and emergency passages | Keep distinct groin pressure or closure and wrist-band checks, one shared discharge and home-care section, and the original wrist emergency recording. The emergency card covers either the hand or foot on the accessed side. The groin version supplies the foot wording and supporting aftercare sources. |
| Long end holds and two summaries | Use the final original spoken discharge question over the animated sources and end-screen card. |

## Assembly

- [Timeline](timeline.json) paths are relative to the workspace root. Clip each `audio.path` from `in_sec` to `out_sec` with `end_frame` exclusive. Adjacent slices of the same recording share a source boundary where retained. Use frame-duration padding or trimming in silence to reconcile millisecond audio boundaries and the 30 fps picture grid. P40 has the spoken line followed by room-tone silence.
- Both Alexander M4As decoded through their full duration. Every discontinuous cut other than the original take endpoints falls in detected quiet audio. Captions use the exact retained words. Caption cues carry the original alignment; where a cue crosses a shortened selection, its retained words are re-timed within that source cue. Confirm synchronization against the finished sound mix.
- Every existing `reference_shots` and `footage` path is a clinical reference. Draw the final scenes with the current modest anatomy, phone text sizes and new layout. Cover the groin with a sterile drape outside one small access window. Use neutral body outlines and fully clothed patient or staff illustrations.
- For the planned Short, start on the simulated left coronary filling at P25 and keep the catheter tip and central branches inside the vertical frame. Its source span is approximately 23.8 seconds. The spoken text and captions follow the same matched recording.
