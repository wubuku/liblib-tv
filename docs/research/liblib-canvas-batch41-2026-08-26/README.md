# Batch 41: Director Phone Virtual Camera

> Status: planned. Source vocabulary, implementation boundary, state contract
> and verification matrix are protected before code changes.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): exact current LibTV locale
   contracts, public-chunk search and upstream boundary.
2. [`PLAN.md`](PLAN.md): value ranking, implementation order and acceptance
   criteria.
3. [`DIRECTOR_PHONE_VCAM.spec.md`](DIRECTOR_PHONE_VCAM.spec.md): UI, pose,
   recording and timeline-import contract.
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md): one-pass screenshot
   interpretation ledger.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): commits, verification and
   interruption handoff.

## Batch Goal

```text
source-shaped virtual-camera surface
  -> explicit local-preview pairing boundary
  -> real browser orientation / pointer pose input
  -> camera preview with stability, level, hold and elevation controls
  -> record from current playhead
  -> import a new phone-camera object and typed camera track
```

## Evidence Discipline

- **LibTV source fact:** current locale contracts prove same-Wi-Fi QR pairing,
  local signaling, certificate trust, gyro permission, stability/hold/elevation
  controls, recording from the current playhead and camera-track import.
- **Runtime limit:** no authenticated runtime screenshot or component DOM was
  captured for this feature. Exact placement, geometry, QR styling, protocol,
  smoothing math and sampling rate remain unknown.
- **Existing replication fact:** the fixed
  `storyai-3d-director-desk` submodule has no phone virtual camera.
- **Clone decision:** provide a visibly labeled local preview that uses real
  browser orientation when available and an on-screen pose pad otherwise.
  Never represent the local preview as working LAN signaling or a scannable
  pairing QR.

## Scope Boundary

This batch does not implement HTTPS certificate provisioning, LAN discovery,
WebRTC/ICE, video uplink, phone-hosted UI, remote QR pairing or performance
diagnostics. Those source capabilities remain documented, not simulated as
successful backend behavior.
