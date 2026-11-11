# Picture production for coronary drug-coated balloons

The pictures follow the existing Alexander timeline. In the representative case, the original stent remains seated throughout. The plain preparation balloon widens the tissue channel and comes out. The coated balloon follows the same parked wire, contacts the treated wall, deflates and also comes out.

## Picture continuity

- P01–P02 establish the treated segment and tissue inside an existing stent. The focal underexpansion view is a separately labelled example. The mesh ends stay near the wall in that example.
- P03 uses simulated contrast X-rays and a separate illustrated internal cross-section before the guidewire crosses the narrowed channel.
- P04–P06 use one fixed longitudinal orientation for the device actions. The preparation balloon is pale blue. The coated balloon has a green exterior with small yellow coating marks. Tissue and local release remain at the contact area.
- P06 compares the same simulated left coronary projection before and after treatment. The same landmarks remain visible, with some residual narrowing after treatment.
- P07 presents a historical US approval example for in-stent restenosis and a separately labelled small-vessel research example. P08 uses a fully covered recovery illustration, a medicine-plan cue and an emergency card.
- P09 shows the old stent after both balloons have been removed. P10 shows the sources, production disclosure and next episode.

## Reproducibility

Run `python outputs/cardiology-series/v2/episode-08/render_dcb.py` from the workspace with PyAV, Skia and the shared series package available. Optional scene numbers limit rendering to those scenes. Use `--force` to replace selected outputs and `--thumbnail` to create the 1280×720 image. One local encoder renders each scene at 2560×1440 and 30 fps. The resulting `visuals/dcb-overrides.json` supplies the picture paths and frame-locked lengths to the shared master assembler.
