# Batch 42 Implementation Log

> Status: in progress. The articulated character, pose Inspector and typed
> pose-track composition are implemented. Focused desktop/mobile Playwright,
> durable screenshots and one-pass interpretation are complete; cross-batch
> regression and stable docs are next.

## Protection Points

1. Exact 50-key pose/SAM-related extraction from the current LibTV locale.
2. Exact 20 current source preset names.
3. Distinct source `姿态关键帧` / `姿态` timeline semantics.
4. Fixed upstream commit and reusable procedural-rig boundaries.
5. Explicit warning that upstream geometry, values and CSS are not LibTV
   source facts.
6. Required fix for the current one-track-per-object sampling bug.

## Progress

- [x] source vocabulary extraction
- [x] upstream pose code archaeology
- [x] implementation specification
- [x] articulated rig and pose data
- [x] Inspector preset/SAM controls
- [x] pose track sampling/composition
- [x] focused browser verification and screenshots
- [x] screenshot interpretation ledger
- [ ] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: `574d5b8`
- Articulated character and Inspector: `bdb6969`
- Pose timeline integration: pending
- Focused verification: pending
- Stable documentation/finalization: pending

## Articulated Character And Inspector Milestone

- Added a strict serializable rig model, 20 source-named calibrated presets,
  six source-named SAM groups and finite control normalization.
- Replaced the rigid six-part character with nested R3F body, torso, head,
  shoulder, elbow, wrist, hip, knee and foot chains.
- Added character-only `属性 / 姿势` tabs, a compact four-column preset grid,
  active/custom state and expandable grouped range controls.
- Kept preset numeric values, channel mapping, geometry and ranges explicitly
  clone-calibrated rather than source facts.

An initial `1440x900` Chromium smoke confirmed:

- exactly 20 preset commands and six SAM groups are rendered;
- applying `招手` stores `posePresetId: "wave"` and the expected finite rig
  controls;
- the actual WebGL canvas changes measurably after the preset;
- editing `rightShoulder.pitch` changes the state to `custom`;
- no console/page errors or document-width overflow occur.

## Pose Timeline Milestone

- Added a third strict timeline track kind, `pose`, with serializable sparse
  rig keyframes.
- Replaced the former one-track `Map<objectId, track>` sampler with per-object
  track composition.
- Added zero-default sparse-control interpolation through the existing
  track-level speed curve.
- Made preset and continuous-control edits upsert a pose keyframe at the
  current playhead and select the resulting pose track/keyframe.
- Kept transform/camera track creation independent from pose-track existence.
- Added pose track labeling/iconography and blocked preset/free-draw motion
  paths for pose tracks.
- Extended generic add/delete/select/seek and curve operations through the
  typed track union.

A second `1440x900` Chromium smoke confirmed:

- the lead character owns `transform + pose` tracks simultaneously;
- `招手` at `0s` and `踢球` at `4s` produce two pose keyframes;
- at `2s`, transform X is `-0.3`, right shoulder is `18°` and right elbow is
  `45°`, proving transform-plus-pose composition and sparse interpolation;
- the intermediate rig has no false preset identity;
- the real WebGL canvas changes between intermediate and endpoint poses;
- motion-path creation is disabled for the selected pose track;
- no console or page errors occur.

## Focused Verification

Added `scripts/verify-liblib-batch42.py`. It covers:

- all 20 preset labels, six SAM groups and 14 bone labels;
- nonblank articulated R3F rendering and measurable preset/interpolation pixel
  changes;
- character-only Inspector tabs, active/custom preset state and continuous
  controls;
- automatic pose-track creation and `0s / 4s` endpoint keyframes;
- transform-plus-pose composition at `2s`;
- generic pose keyframe add/delete and previous/next seeking;
- playback sampling and finite sparse-control values;
- UI and store-level motion-path rejection for pose tracks;
- desktop and `390x844` geometry, internal Inspector scrolling and document
  overflow;
- console, page and request failures.

The focused script passed and generated five Batch 42-only state screenshots
plus one contact sheet. Their first and only visual interpretation is recorded
in `SCREENSHOT_ANALYSIS.md`.

## Interruption Handoff

Continue with `PLAN.md` step 10: run Batch 35-42 regression and project gates,
then update stable docs and maturity assessment. Do not re-open Batch 42
screenshots; use `SCREENSHOT_ANALYSIS.md`. Preserve unrelated dirty PNGs and
concurrent docs, and use path-limited commits.
