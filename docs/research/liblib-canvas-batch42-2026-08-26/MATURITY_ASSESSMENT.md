# Director Desk Maturity After Batch 42

## Executive Assessment

The clone now has a coherent, testable Director Desk authoring loop:

```text
canvas entry
  -> real R3F scene and semantic selection
  -> object/camera/character Inspector authoring
  -> transform/camera/pose timeline animation
  -> preset or free motion paths and speed curves
  -> phone-camera local recording
  -> helper-free still or browser-recorded video
  -> atomic image/video return to the React Flow canvas
```

This is mature enough to stop treating the Director Desk as a shell. Its
highest-value foundational workflows are implemented and regression covered.
It is not yet source-faithful enough to declare the Director Desk finished.

## Capability Matrix

| Area | Clone maturity | Evidence confidence | Remaining risk |
|---|---|---|---|
| entry, full-screen shell, return | high | mixed source runtime + clone verification | exact source spacing and responsive breakpoints |
| R3F scene and camera framing | high | source vocabulary + upstream + clone verification | source camera defaults and renderer details |
| typed timeline and keyframes | high | source vocabulary + clone verification | exact source track chrome and editing gestures |
| motion paths and curves | high | source labels + upstream + clone verification | exact source path geometry and reset semantics |
| animation export | medium-high | source labels + real clone browser output | source codec/upload/progress behavior |
| phone virtual camera | medium | source vocabulary + clone-local preview | no source signaling, pairing or transport evidence |
| articulated character pose | medium-high | exact source names + upstream shape + clone verification | no authenticated source panel screenshot/DOM/CSS |
| character/model asset system | low | broad source/upstream hints only | asset discovery, import, rig compatibility |
| groups/crowds | low | source vocabulary not yet extracted for a batch | interaction model and timeline semantics unknown |
| camera follow/look-at authoring | low | candidate only | source behavior not yet proven |

## What Is Now Stable

- `directorStore` owns serializable scene, rig and typed timeline state.
- Three.js runtime objects remain inside R3F components.
- Tracks compose by object and kind, so transform and pose do not overwrite one
  another.
- Motion paths stay limited to transform/camera tracks.
- Still and video return use one graph transaction and one undo step.
- Focused scripts cover desktop/mobile geometry and real WebGL pixel changes.

## Evidence Debt

The pose implementation has exact current LibTV names but not authenticated
source visual geometry. The 20 preset angles, continuous channels, slider
ranges, procedural mannequin proportions and interpolation are clone
calibration informed by the fixed upstream replication. They must not be cited
as LibTV implementation facts.

The phone-camera boundary is similarly explicit: local browser orientation and
pointer input are real, while QR pairing, LAN discovery, signaling, WebRTC and
remote transport are not implemented or claimed.

## Next-Batch Ranking Rule

Before selecting another Director feature, extract current source evidence and
rank candidates by:

1. workflow impact on shot authoring;
2. evidence confidence;
3. reuse of current scene/timeline architecture;
4. ability to verify deterministically in Playwright;
5. risk of inventing source behavior.

The leading hypotheses are camera follow/look-at authoring and groups/crowds,
but neither is approved for implementation until current source labels,
interaction states or runtime behavior are recorded. If source evidence is too
weak, the next batch should return to a documented high-confidence canvas gap
instead.
