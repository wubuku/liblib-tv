# Batch 36 Implementation Log

> Status: implementation and focused verification complete; final cross-batch
> regression and quality gate pending.

## Protection Points

1. Fresh source evidence, plan, timeline spec and selectors.
2. Timeline schema/store/sampling and workspace UI.
3. Track/keyframe lifecycle, auto-keyframe and scene/camera integration.
4. Playwright, screenshot ledger, regression and quality gates.
5. Final handoff and next-batch decision.

## Current Evidence Boundary

- Current LibTV source directly proves the timeline capability and interaction
  vocabulary.
- Exact runtime geometry remains unresolved.
- The fixed upstream replication has no timeline implementation to port.
- Batch 36 must therefore implement new source-backed behavior while clearly
  labeling its geometry and default fixture motion as clone calibration.

## Implementation Result

- Added `directorTimelineMath.ts` with time clamping and deterministic linear
  interpolation for transform and camera keyframes.
- Extended `directorStore` with an eight-second typed timeline, transform/camera
  tracks, seeded character/camera motion and play/pause/loop/zoom/seek state.
- Added track and keyframe selection, add/update/delete, previous/next navigation
  and duplicate-track prevention.
- Added auto-keyframe recording for Inspector transform/camera edits and completed
  R3F TransformControls commits. Timeline sampling never writes keyframes.
- Added `DirectorTimeline` as a stable full-width bottom band below the existing
  object-tree / R3F / Inspector authoring region.
- Added ruler scrubbing, playback clock, loop state, timecode, internal zoom and
  horizontally scrollable compact controls/track canvas.
- Selecting a timeline track or keyframe synchronizes object selection, Inspector
  routing and deterministic scene/camera sampling.
- Track labels follow object renames.
- A focused DOM measurement found that a `12px` square rotated by 45 degrees has
  an approximately `16.97px` visual bounding box. Endpoint marker centers are
  therefore clamped `9px` inward so the first/last diamonds remain fully visible.

## Focused Verification Result

- `python3 scripts/verify-liblib-batch36.py` passed.
- Desktop assertions cover exact workspace/timeline separation, two typed tracks,
  six fixture keyframes, ruler scrub, scene interpolation, keyframe selection,
  playback/pause, loop-on/off end behavior, previous/next navigation, zoom and
  zero document overflow.
- Lifecycle assertions cover one mug track, same-time keyframe upsert,
  auto-keyframed Inspector edits, keyframe deletion, track deletion, camera
  keyframe sampling, camera view pixels and manual camera keyframes with
  auto-keyframe disabled.
- Mobile assertions cover the `390x844` timeline band, internally overflowing
  controls/canvas, playback, tree drawer coexistence and zero document overflow.
- Browser console, page and request errors were empty in both viewports.
- The final contact sheet was visually inspected once. Detailed observations are
  preserved in [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md).

## Commit Protection

- Plan protection: `55c48bd`.
- Implementation protection: recorded by the commit containing this log,
  timeline code, verifier and screenshots.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the implementation commit, run the documented cross-batch
regression set, `npm run docs:check`, `npm run check` and `git diff --check`;
then record the exact commands and final commit ID here. Do not include the 37
historical Batch 9/15/21/26-33 screenshot modifications in any Batch 36 commit.
