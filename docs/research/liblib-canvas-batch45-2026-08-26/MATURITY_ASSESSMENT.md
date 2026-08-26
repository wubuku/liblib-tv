# Director Desk Maturity After Batch 45

## Executive Assessment

Batch 45 closes a high-value group-authoring loop:

```text
multi-select characters or create a crowd array
  -> create/select an explicit group
  -> inspect and transform the group
  -> create a typed group timeline track
  -> scrub/play deterministic member motion
  -> ungroup without deleting members
```

This is a mature frontend prototype slice. It is not source-exact where the
current LibTV evidence exposes vocabulary and data contracts but not the
authenticated panel DOM, numeric limits or transform math.

## Capability Matrix

| Area | Clone maturity | Evidence confidence | Remaining risk |
|---|---|---|---|
| entry, full-screen shell, return | high | clone verification + prior batches | exact source spacing and breakpoints |
| R3F scene and camera framing | high | source vocabulary + upstream + clone verification | source renderer/default details |
| typed timeline and keyframes | high | source vocabulary + clone verification | exact source track chrome/gestures |
| motion paths and curves | high frontend loop | source labels + upstream + clone verification | exact source geometry/reset semantics |
| camera look-at/follow and preset motion | high frontend loop | source names/conflicts + clone verification | source math, easing and persistence |
| articulated character pose | medium-high | source names + upstream + clone verification | source panel DOM/CSS |
| animation export | medium-high | clone browser output | source codec/upload/progress |
| phone virtual camera | medium | clone-local preview | source transport evidence |
| character groups/crowds | medium-high | source typed contracts + upstream + clone verification | source geometry, limits, locking and persistence |
| capture management | medium | existing capture/send loop | source list, naming and lifecycle parity |
| model/environment library | low | source/upstream hints | asset discovery/import compatibility |

## Batch 45 Boundaries

The implementation intentionally does not claim:

- source-exact crowd limits or array placement;
- source-exact group anchor/composition order;
- prop/camera membership in every source grouping path;
- group visibility/lock aggregation;
- group pose/color batch editing;
- group motion paths, persistence, clipboard or undo.

The group track is a typed clone model backed by current source evidence for
`groupTracks` and `memberOffsets`; its interpolation and UI geometry remain
clone decisions.

## Next Highest-Value Queue

1. **Director capture management:** source-backed capture history, thumbnail
   list, naming and send-back lifecycle, using the existing capture foundation.
2. **Director model/environment library:** source entry points, filters,
   selection and import boundaries before adding asset persistence.
3. **Director collaboration/persistence boundaries:** only if current source
   evidence can be safely observed without turning prototype state into a
   backend claim.

Ordinary canvas feature work can be reconsidered after the next one or two
Director batches, but Director remains the active priority until capture and
asset-library entry points have either matured or been blocked by evidence.
