# Batch 41 Implementation Log

> Status: complete. Main implementation, focused browser verification,
> screenshot ledger, Batch 35-41 regression and final quality gates passed.

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
- [x] focused desktop/mobile Playwright
- [x] one-pass screenshot interpretation
- [x] stable docs and cross-batch quality gates

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

## Focused Verification

Added `scripts/verify-liblib-batch41.py`. It covers:

- waiting-state source vocabulary and explicit local-preview boundary;
- real active-camera position changes from pointer pose;
- stability, keep-level, hold and elevation behavior;
- current-playhead end guard with no camera/track mutation;
- recording-time close/export/capture exclusion;
- advancing playhead and dynamic camera sample differences;
- original camera restoration;
- one new `手机运镜 1` camera plus typed camera track;
- active object/track/keyframe selection and imported metadata;
- nonblank R3F canvas, desktop/mobile overflow and mobile panel geometry;
- console, page and request failures.

The focused script passed and generated six Batch 41-only image artifacts.
Their first visual interpretation is recorded in `SCREENSHOT_ANALYSIS.md`.

## Regression And Quality Result

The final gate passed on August 26, 2026:

```bash
python3 scripts/verify-liblib-batch35.py
python3 scripts/verify-liblib-batch36.py
python3 scripts/verify-liblib-batch37.py
python3 scripts/verify-liblib-batch38.py
python3 scripts/verify-liblib-batch39.py
python3 scripts/verify-liblib-batch40.py
python3 scripts/verify-liblib-batch41.py
npm run docs:check
npm run check
git diff --check
```

All passed. The initial full lint reported one new ARIA warning on the pose-pad
slider; the missing `aria-valuemin`, `aria-valuemax` and `aria-valuenow`
contract was added and the gate rerun. Final lint output contains only the
same nine existing FrameOS/`CustomHandle` warnings.

Verifier runs rewrite several historical PNGs non-deterministically. They
remain unstaged; this batch staged only its deliberate artifacts before the
cross-batch rerun.

## Commits

- Plan/evidence protection: `6419f40`
- Main implementation: `4e20e5a`
- Focused verification: `77075df`
- Stable documentation/finalization: recorded by the next documentation-only
  closeout commit

## Interruption Handoff

Batch 41 is closed. Read `MATURITY_ASSESSMENT.md` before selecting the next
director batch. Do not infer source UI geometry from the locale or upgrade the
local-preview state to real phone/LAN parity without implementing and verifying
the transport.
