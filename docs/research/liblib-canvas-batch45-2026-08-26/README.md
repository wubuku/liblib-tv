# LibTV Canvas Replication Batch 45

> Director Desk character groups, crowd arrays, group transforms and typed
> group timeline tracks.

## Status

In progress. The source and upstream archaeology are protected before
implementation.

## Why This Batch

Batch 44 completed the camera-authoring loop. Current LibTV code now provides
direct evidence that the next missing Director capability is not a generic
multi-select approximation:

- the scene document owns explicit `characterGroups`;
- the animation document owns explicit `groupTracks`;
- group tracks may persist `memberOffsets`;
- the UI exposes group/ungroup, crowd arrays, group expansion and group
  keyframes.

That makes group authoring a high-value, source-backed continuation of the
Director Desk rather than an upstream-only idea.

## Documents

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): current LibTV facts and limits.
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): fixed StoryAI
  implementation facts.
- [`PLAN.md`](PLAN.md): ordered implementation and verification plan.
- [`DIRECTOR_GROUPS.spec.md`](DIRECTOR_GROUPS.spec.md): clone behavior contract.
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md): interruption-safe progress log.
- `SCREENSHOT_ANALYSIS.md`: created after the first focused clone visual pass.

## Evidence Rule

Keep these categories separate:

1. **LibTV current source fact**: current locale or downloaded business chunk.
2. **Fixed upstream fact**: code at submodule commit `8c8bd36`.
3. **Clone calibration**: bounded implementation chosen where source geometry
   or interaction details remain unavailable.
