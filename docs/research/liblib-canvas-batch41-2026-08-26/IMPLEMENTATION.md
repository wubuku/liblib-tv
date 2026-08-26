# Batch 41 Implementation Log

> Status: implementation complete; focused verification and final regression
> remain.

## Protection Points

1. Exact 55-key current LibTV phone virtual-camera locale extraction.
2. Public 108-chunk search result and lack of component/CSS evidence.
3. Explicit local-preview boundary instead of fake LAN/QR success.
4. Real pose preview and current-playhead camera-track import contract.
5. Planned Playwright, screenshot ledger and Batch 35-41 regression.

## Implementation

- [x] phone pose math and serializable director state
- [x] source-shaped panel and local input adapters
- [x] live camera preview and recording timer
- [x] named camera plus typed camera-track import
- [ ] focused desktop/mobile Playwright
- [ ] one-pass screenshot interpretation
- [ ] stable docs and cross-batch quality gates

## Main Implementation

### Pose math

- Added finite orientation normalization with shortest-angle yaw deltas.
- Added source-calibrated yaw/pitch orbit mapping around the current camera
  target.
- Added stability-dependent smoothing, keep-level roll suppression and bounded
  elevation.
- Kept all calculations in plain tuples and camera keyframe values.

### Director state

- Added a serializable phone virtual-camera state machine and calibration
  baseline.
- Added local connection, gyro, stability, hold, calibration, pose, elevation,
  recording-time and sample-count actions.
- Recording-time advancement samples the ordinary timeline while preserving
  the live phone-controlled camera.
- Import restores the original source camera, creates one independent
  `手机运镜 N` camera and one typed camera track, then selects the imported
  camera/track/keyframe.

### Panel and runtime

- Added a viewport-toolbar `Smartphone` trigger and anchored desktop/mobile
  panel.
- Added source vocabulary for startup, waiting, certificate guidance,
  controls, recording guards and import success.
- The pairing motif is intentionally non-scannable and labeled `本机预演`.
- Real `deviceorientation` input is used when permission is available; the
  pointer/touch pose pad is the deterministic local fallback.
- Browser events, animation frames and temporary sample buffers remain in the
  panel component rather than Zustand.
- Workspace close, animation export and still capture are blocked during a
  phone take.

## Browser Smoke

An initial Chromium smoke at `1440x900` confirmed:

- pointer pose moved the active camera from `[4.8, 2.65, 6.9]` to
  approximately `[6.43, 3.61, 4.69]`;
- a take imported nine valid camera keyframes;
- `手机运镜 1` became the active/selected camera and selected timeline track;
- no console or page errors occurred.

At `390x844`, the connected panel measured `x=12`, `width=366`,
`y=131`, `height=465`; document scroll width remained `390`.

TypeScript, quiet lint and targeted `git diff --check` passed after the main
implementation.

## Commits

- Plan/evidence protection: `6419f40`
- Main implementation: recorded by the next code commit
- Focused verification: pending
- Stable documentation/finalization: pending

## Interruption Handoff

If interrupted before implementation, read `SOURCE_EVIDENCE.md`, `PLAN.md` and
`DIRECTOR_PHONE_VCAM.spec.md`. Do not infer source UI geometry from the locale
or implement a fake scannable QR/phone-connected state.
