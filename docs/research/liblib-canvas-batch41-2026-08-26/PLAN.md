# Batch 41 Plan: Director Phone Virtual Camera

## 1. Gap And Value Ranking

| Candidate | Current clone | Source evidence | Value | Decision |
|---|---|---|---:|---|
| virtual-camera entry and state surface | absent | exact state vocabulary | 5 | implement |
| orientation-driven camera preview | absent | gyro/level/hold/elevation labels | 5 | implement |
| record from current playhead | absent | direct no-room/recording contracts | 5 | implement |
| named camera + typed camera-track import | absent | direct camera/track/import labels | 5 | implement |
| pairing presentation | absent | same-Wi-Fi/QR/certificate labels | 4 | local-preview boundary only |
| real LAN signaling and phone client | absent | source contract, no implementation detail | 2 | document/defer |
| phone performance diagnostics | absent | direct diagnostic labels | 2 | document/defer |
| camera-follow conflict | no follow authoring yet | direct conflict label | 2 | preserve as future guard |

## 2. Source / Replication / Clone Boundary

### LibTV source fact

- The feature is named `虚拟相机`.
- Startup progresses through local preparation/signaling, waiting for a phone
  QR connection, paired, recording and imported states.
- Motion input includes gyro, stability, level, hold and elevation controls.
- Recording starts at the current playhead and imports a named camera track.

### Existing replication fact

- The upstream director clone has no phone virtual-camera implementation.
- This clone already has an active camera, deterministic typed camera tracks,
  current-playhead control and real R3F camera rendering.

### Clone decision

- Keep LAN/network behavior explicitly unavailable rather than fake it.
- Add a local preview connection path for real browser orientation or pointer
  pose input.
- Drive the active R3F camera immediately from normalized pose input.
- Record serializable camera values from the current playhead.
- On stop, create `手机运镜 N` as a new camera and a new typed camera track,
  select it and leave the playhead at the take end.

## 3. Implementation Steps

1. Add pure phone-pose normalization, smoothing and orbit mapping helpers.
2. Extend `directorStore` with serializable virtual-camera state and actions.
3. Add `DirectorPhoneVcamPanel` with source-shaped status vocabulary,
   non-scannable local-preview pairing, orientation permission, pose pad,
   stability/level/hold/elevation controls and recording command.
4. Anchor a `Smartphone` trigger in the existing viewport toolbar.
5. Sample camera values while recording and import them as a new camera track.
6. Add semantic selectors for status, input values, sample count and imported
   camera/track identifiers.
7. Add desktop/mobile Playwright coverage and screenshot artifacts.
8. Interpret screenshots once, update stable docs and run Batch 35-41 plus
   project-wide gates.

## 4. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-phone-vcam-trigger]` | opens/closes virtual-camera surface |
| `[data-director-phone-vcam-panel]` | panel root and status |
| `[data-director-phone-vcam-local-preview]` | explicit non-LAN prototype boundary |
| `[data-director-phone-vcam-connect]` | local preview pairing command |
| `[data-director-phone-vcam-pose-pad]` | pointer/touch pose input |
| `[data-director-phone-vcam-enable-gyro]` | orientation permission/input command |
| `[data-director-phone-vcam-stability]` | smoothing control |
| `[data-director-phone-vcam-keep-level]` | roll/level toggle |
| `[data-director-phone-vcam-hold]` | temporary camera lock |
| `[data-director-phone-vcam-elevate]` | elevation controls |
| `[data-director-phone-vcam-record]` | record/stop command |
| `[data-director-phone-vcam-take]` | imported take metadata |

## 5. Acceptance Criteria

- The panel uses the exact source title and status/recording/control vocabulary
  where the clone supports the corresponding state.
- The local preview is visibly distinguished from real same-Wi-Fi signaling.
- Pointer pose changes the actual active R3F camera; browser orientation is
  used when available and permission is granted.
- Stability changes smoothing, keep-level suppresses roll metadata, hold blocks
  pose application, and elevation changes camera height.
- Record is rejected at the timeline end.
- Recording starts at `timeline.currentTime`, advances only through remaining
  duration and captures at least start/end camera values.
- Stop creates one new camera and one camera track named `手机运镜 N`, selects
  both and reports `手机运镜已导入机位时间轴`.
- Existing camera tracks, motion paths, still capture and video export remain
  functional.
- Desktop and `390x844` panel geometry stay inside the viewport with no
  document overflow.
- Batch 35-40, focused Batch 41, `docs:check`, `npm run check` and
  `git diff --check` pass.

## 6. Out Of Scope

- real QR payloads, phone-hosted page, HTTPS trust bootstrap or LAN signaling;
- WebRTC media/data channels, ICE diagnostics or video uplink;
- exact source geometry, timing, smoothing math or sample rate;
- camera-follow authoring and its conflict guard;
- persistence or graph return for raw phone takes.

## 7. Status

- [x] Current locale and public chunk corpus audited
- [x] Source/upstream/clone boundaries recorded
- [x] UI, pose, recording and import contracts planned
- [x] Store, math and panel implementation
- [x] Focused Playwright and screenshot ledger
- [x] Cross-batch regression, stable docs and final quality gate
