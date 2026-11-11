# Picture production for What the Four Tools Do

The eleven spoken paragraphs and the clinical source map come from the earlier tools-of-angiography episode. The P01 visual opens with the simulated contrast result before revealing the title. The rest follows the previously reviewed device sequence.

## Retimable scenes

| File | Source duration | Motion |
| --- | ---: | --- |
| `visuals/P01.mp4` | 15 s | Coronary contrast fills. Title, then the four tools come into focus individually. |
| `visuals/P02.mp4` | 13 s | Separate right wrist and right groin arterial routes end in the aortic root. |
| `visuals/P03.mp4` | 14 s | Needle enters the near wall. Short wire passes into the lumen. Needle withdraws over the parked wire. |
| `visuals/P04.mp4` | 14 s | Sheath and tapered dilator advance together over the wire. Wire and dilator leave. The sheath stays. |
| `visuals/P05.mp4` | 12 s | Draped femoral micropuncture example. The transition explicitly skips the exchange between the temporary introducer and the working sheath. |
| `visuals/P06.mp4` | 15 s | Longer guidewire travels through the wrist sheath. Diagnostic catheter follows it. The arterial route map shows their approach to the aortic root. |
| `visuals/P07.mp4` | 13 s | The wire retracts into the stable catheter. The empty catheter tip then moves shallowly to the left coronary opening above the valve. |
| `visuals/P08.mp4` | 13 s | Contrast travels inside the catheter into the selected coronary opening. A simulated X-ray shows its passage through the artery and subsequent washout. |
| `visuals/P09.mp4` | 14 s | Separate left and right coronary recordings with a camera-angle change between them. |
| `visuals/P10.mp4` | 12 s | Fully clothed anonymous figures discuss kidney and prior contrast concerns, then symptoms to report during the test. |
| `visuals/P11.mp4` | 13 s | Catheter out, wrist band placed, sheath out, then the four tool roles recap. |
| `visuals/P12.mp4` | 8 s | Sources, credits and the next episode. |

Use the actual Alexander timings and captions to set final scene boundaries. The access and root actions remain in one plane each. Any change in scene duration should preserve the order of the device movements. These pictures are silent.

## Picture anchors for the editor

These are seconds within each silent source clip. Match the picture events to the corresponding words in the finished narration.

- P03 · Needle enters 0.28–3.64, short wire passes 3.96–7.28, needle withdraws 7.70–10.36.
- P04 · Sheath and dilator advance to the vessel at 2.38–5.04, dilator and short wire withdraw 5.46–8.54, then a closer view reveals the empty sheath.
- P05 · The card identifies the omitted exchange at 5.88. The working-sheath view follows at 7.68.
- P06 · Long wire enters 0.30–3.00. Simulated live X-ray starts at 3.30, the catheter follows 6.90–10.50, and the wider arterial route starts at 10.65. A final wrist view retains the seated sheath.
- P07 · Wire withdraws 0.23–3.51. The catheter tip moves to the left coronary opening 5.66–9.49.
- P08 · Contrast travels inside the catheter, then reaches the left opening at about 3.68. The X-ray simulation starts at 7.67.
- P09 · Left run begins at 0.00, equipment view at 5.67, separate right run at 8.61.
- P11 · Catheter withdraws by 1.89, wrist band starts appearing at 2.08, sheath withdraws 2.34–3.51, and the tool recap starts at 4.03. Moving X-rays close the scene.

## Reproducibility

Run `python outputs/cardiology-series/v2/episode-03/visuals/render_devices.py P01 P02` from the workspace with `numpy`, `skia-python` and FFmpeg available. Omit the scene IDs to build the full set. Use `--force` to replace an existing picture, `--thumbnail` to build the 1280×720 thumbnail, and `--stills` for design inspection.

The renderer uses the shared Skia access and angiogram library plus the reviewed common-femoral path and original coronary-route geometry. It renders 2560×1440 at 30 fps. It stages one temporary native frame spool at a time and uses one FFmpeg encoder with two threads. The spool is removed after the attempt. The final video master, captions, audio and delivery QA are separate assembly steps.
