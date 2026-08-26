# Batch 37 Implementation Log

> Status: main implementation and browser smoke complete; focused verification
> and finalization pending.

## Protection Points

1. Fresh path/curve source extraction, plan, spec and selectors.
2. Pure Bezier/path sampling plus director store schema/actions.
3. R3F trajectory presentation and path-driven playback.
4. Path commands, functional curve editor and responsive states.
5. Playwright, screenshot ledger, regressions, stable docs and final handoff.

## Current Evidence Boundary

- Current LibTV source directly proves the path/curve command vocabulary and
  guide sequence from track creation to playback preview.
- Exact runtime geometry, path point generation and preset control values remain
  unresolved.
- The fixed upstream replication has no implementation to port for this layer.

## Main Implementation Result

- Added pure cubic-Bezier inversion/remapping, track-progress mapping, polyline
  arc-length sampling, tangent normalization and path-Y rotation helpers.
- Extended typed transform/camera tracks with serializable speed curves and
  optional motion-path bindings.
- Added serializable line/ring/rectangle paths, source-backed auto-path names,
  enable/delete/orient actions and one-path-per-track replacement semantics.
- Path sampling replaces position while preserving the remaining transform or
  camera target/FOV values. Non-camera orient-to-path takes control of Y rotation.
- Added real R3F world-space trajectory lines and selected-path anchors. Helpers
  are absent from camera view and helper-free capture.
- Added the exact source-labeled `创建运动轨迹` menu with `直线路径 / 圆环路径 /
  矩形路径`, plus enable, orient and delete controls.
- Added a functional timeline curve mode with `线性 / 平滑 / 缓入 / 缓出 /
  缓入缓出`, draggable Bezier handles, current parameter values and
  `返回时间线`.
- Inspector disables Y rotation and displays the exact source hint while
  orient-to-path controls a non-camera transform track.

## Browser Smoke Result

The local clone was exercised at `1440x900` without creating durable screenshots:

- ring creation produced one bound path with 16 persisted points and 16 semantic
  anchor selectors;
- linear `4s` path sampling moved the character to `[-4.05, 0, 0.2]`;
- orient-to-path changed Y rotation and exposed the source lock hint;
- changing the selected track to `缓入` changed the same `4s` sample to a
  different path position, proving the curve affects R3F state rather than only
  the SVG;
- curve mode returned to the ordinary timeline and browser errors remained empty.

`npm run typecheck`, `npm run lint -- --quiet` and `git diff --check` passed after
the main implementation.

## Commit Protection

- Plan protection: `baf0db9`.
- Implementation protection: recorded by the commit containing this log and
  the main runtime implementation.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the main implementation commit, add
`scripts/verify-liblib-batch37.py` and verify exact path lifecycle, curve sampling,
custom handle drag, capture-helper exclusion and mobile overflow. Then inspect the
new contact sheet once and finish stable docs. Do not stage verifier-regenerated
historical screenshots from Batch 9/15/21/26-36.
