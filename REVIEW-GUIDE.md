# Review guide

Start with the [six delivered videos and matching captions](README.md#videos-in-this-snapshot). The seventh video is a script, storyboard and work-in-progress animation. Review the complete video and its SRT together when a master is available. Use the storyboard to inspect the intended sequence and the clinical source notes to assess the claims.

## Clinical and editorial references

| Video | Open first | Focus for review |
| --- | --- | --- |
| 1–2 · Diagnostic coronary angiography | [Scene scripts](outputs/cardiology-series/episode-01/production/scenes.json) · [Clinical review notes](outputs/cardiology-series/episode-01/REVIEW.md) · [Companion posts and alt text](outputs/cardiology-series/episode-01/companion-posts.md) | Right radial and right common femoral anatomy, separation of the access and diagnostic wires, femoral micropuncture exchange, two coronary contrast views, and distinct recovery pathways. |
| 3 · Angioplasty and stenting | [Script](outputs/cardiology-series/episode-02/narration-script.md) · [Storyboard and clinical sources](outputs/cardiology-series/episode-02/scene-timing-brief.md) | Diagnostic angiography and PCI as distinct steps. Check wire crossing, optional preparation balloon, stent already mounted on its delivery balloon, stent left in the artery, final contrast, and recovery. |
| 4 · Drug-coated balloons | [Script](outputs/cardiology-series/episode-03/narration-script.md) · [Storyboard and clinical sources](outputs/cardiology-series/episode-03/scene-timing-brief.md) | Selected in-stent restenosis, lesion preparation, local medicine transfer, the existing stent staying in place, and jurisdiction-specific labeling. |
| 5 · TAVI | [Storyboard](outputs/cardiology-series/episode-04/scene-timing-brief.md) · [Clinical sources](outputs/cardiology-series/episode-04/SOURCES.md) | One transfemoral, balloon-expandable example. Check the wire trajectory, implant alignment at the native annulus, new leaflet motion, valve function, leak checks, and rhythm monitoring. |
| 6 · Wrist vs groin access | [Storyboard](outputs/cardiology-series/episode-05/scene-timing-brief.md) · [Clinical sources](outputs/cardiology-series/episode-05/SOURCES.md) | Right-sided landmarks, choice of access across clinical settings, how a route change is explained, and closure and recovery by route. |
| 7 · Sheath, wire, catheter and contrast | [Storyboard](outputs/cardiology-series/episode-06/scene-timing-brief.md) · [Clinical sources](outputs/cardiology-series/episode-06/SOURCES.md) | Each component’s purpose, how the wire and catheter relate, contrast through the catheter, and brief warmth versus symptoms to report to staff. |

## How to review a completed episode

1. Watch the full master at normal speed with sound and English captions. Note unclear terms, incorrect pronunciation, rushed beats, reading time, and transitions. Check that caption timing and wording match the delivered audio. The transcripts and alignment manifests can help locate a concern.
2. Inspect device actions frame by frame. Check anatomical side, visible lumen, plausible instrument entry and withdrawal, and what stays in place during exchanges. Compare the illustrated example with its named source and flag where a different device or approach would behave differently.
3. Check that the educational claim matches the guideline population, jurisdiction or device indication when those distinctions matter. Identify any recovery advice that could sound universal even though it depends on the patient’s care team. Check that simulated imagery and synthetic narration are disclosed in the release copy.
4. Check the thumbnail and selected video frames on a small screen. Look for readable type, accessible contrast, coherent labeling, and diagrams that explain the subject without covering the instrument or the access site.

## What Claude can propose

For each finding, include the video and exact timestamp or scene ID, the current frame or wording, the specific concern, the supporting primary source and a concrete replacement. Label whether the fix changes clinical meaning, viewer comprehension or presentation. Start with errors that change anatomy, device order, indications or urgent symptoms.

- **Clinical and language changes.** Propose plain English rewrites and source-backed corrections to tool order, technique variations, medication wording, or recovery advice. Use current clinical society guidance, official patient information, or a relevant device instruction or regulatory label. Link the exact section when possible.
- **Illustration and motion changes.** Propose an isolated device shot, a fixed-angle cutaway or a clearer transition where a viewer could lose track of an instrument. Include the intended start and end positions and the structure that must remain visible.
- **Accessibility and pacing changes.** Propose revised caption text, a longer visual hold, shorter on-screen labels, or better contrast. Use the exact delivered master for timestamps.
- **Production changes.** Propose portable dependency paths, reproducible render commands or checks that preserve the existing media, status and source records. The repo contains source and review assets for analysis. Release and account actions are handled through the owner’s publishing workflow.

The research and QA records show source checks, visual inspection and technical verification where recorded. They are separate from an independent clinician’s review. Carry forward each episode’s scope and limits when suggesting changes.
