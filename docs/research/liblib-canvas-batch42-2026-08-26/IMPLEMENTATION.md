# Batch 42 Implementation Log

> Status: in progress. The articulated character and pose Inspector milestone
> is implemented and browser-smoked; typed pose tracks are next.

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
- [ ] pose track sampling/composition
- [ ] focused browser verification and screenshots
- [ ] screenshot interpretation ledger
- [ ] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: pending
- Articulated character and Inspector: pending
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

## Interruption Handoff

Continue with `PLAN.md` step 5: add `kind: "pose"` keyframes and multi-track
composition. Do not re-open historical screenshots: this batch has no durable
screenshot yet. Preserve all unrelated dirty PNGs and stage only exact Batch 42
paths. The most important invariant is that transform and pose tracks must
compose for one character rather than compete in a `Map<objectId, track>`.
