# Batch 36 Implementation Log

> Status: complete, verified and documented for handoff.

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

## Regression And Quality Result

- The focused high-risk regression set passed serially: Batch 9, 15, 21,
  26, 27, 28, 29, 30, 31, 32, 33, 35 and 36.
- `npm run check` passed: ESLint has the repository's existing 9 warnings and
  zero errors; TypeScript and the Next.js 16.2.1 production build passed.
- `npm run docs:check` passed with 276 Markdown files and 678 local targets.
- `git diff --check` passed.
- Stable docs now describe the timeline data flow, components, behavior,
  verification entry and current Big Picture.

## Commit Protection

- Plan protection: `55c48bd`.
- Implementation protection: `472df50`.
- Verification/finalization: recorded by the commit containing this completed
  log and stable-doc updates.

## Interruption Handoff

Batch 36 is complete. Continue with Batch 37 from the source-backed curve editor
and motion-path contract. Preserve the separation between source facts, clone
calibration and unresolved runtime geometry. Do not include regenerated historical
screenshots from earlier verifier runs in later commits.
