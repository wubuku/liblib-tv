# Director Desk Maturity After Batch 44

## Executive Assessment

The Director Desk now has a complete, locally testable camera-authoring loop:

```text
select camera track
  -> choose replace or append
  -> apply one of seven source-named preset motions
  -> inspect generated keyframes in the typed timeline
  -> scrub/play the real R3F camera
  -> preserve or reject related path/follow states
```

This batch is mature as a frontend prototype slice. It is not source-exact in
the areas the public LibTV evidence did not expose.

## Capability Matrix

| Area | Clone maturity | Evidence confidence | Remaining risk |
|---|---|---|---|
| entry, full-screen shell, return | high | mixed source runtime + clone verification | exact source spacing and breakpoints |
| R3F scene and camera framing | high | source vocabulary + upstream + clone verification | source renderer/default details |
| typed timeline and keyframes | high | source vocabulary + clone verification | exact source track chrome/gestures |
| motion paths and curves | high | source labels + upstream + clone verification | exact source geometry/reset semantics |
| camera look-at/follow | high frontend loop | exact source names/conflicts + clone verification | source panel geometry and camera math |
| articulated character pose | medium-high | exact source names + upstream + clone verification | no authenticated source panel DOM/CSS |
| animation export | medium-high | source labels + real clone browser output | source codec/upload/progress |
| phone virtual camera | medium | source vocabulary + clone-local preview | no source transport evidence |
| preset camera motion | high frontend loop | exact source vocabulary + clone verification | source math, timing, easing and persistence |
| groups/crowds | low | broad upstream hints, source runtime not yet bounded | selection, hierarchy and timeline semantics |
| model/environment library | low | source/upstream hints | discovery/import/asset compatibility |
| capture management | medium | existing capture/send loop | source list, naming and lifecycle parity |

## What Batch 44 Added

- Seven source-named camera choices and two source-named application modes.
- Deterministic finite camera keyframe generation with replace and append
  contracts.
- Exact no-room and follow-conflict feedback in both UI and store actions.
- Existing generic paths remain in the serializable timeline and become
  disabled instead of being deleted.
- A compact panel that remains within desktop and `390x844` document bounds.
- Focused browser assertions for actual R3F pixel changes, state integrity and
  zero runtime errors.

## Evidence Debt

The current LibTV locale proves the preset entry, modes, seven labels, no-room
guard and follow conflict. It does not prove preset geometry, duration
allocation, keyframe count, easing, panel CSS, successful close behavior,
path-disable semantics or persistence. Those remain explicitly clone-only
decisions and must not be promoted to source facts.

## Next Highest-Value Queue

1. **Groups/crowds:** investigate the source vocabulary and the fixed
   `storyai-3d-director-desk` implementation for selectable group hierarchy,
   multi-object authoring and timeline semantics. Start with evidence and a
   bounded non-destructive prototype.
2. **Director capture management:** improve the existing capture history,
   naming, thumbnail and send-back workflow only where current source evidence
   can be observed safely.
3. **Model/environment library:** inspect source entry points, filtering,
   selection and import boundaries before adding any asset model.

The next batch should remain Director-first. Return to ordinary canvas feature
work only after these Director candidates are either mature or blocked by
missing source evidence.
