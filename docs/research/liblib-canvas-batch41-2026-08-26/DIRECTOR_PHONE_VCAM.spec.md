# Director Phone Virtual Camera Specification

## 1. Purpose

Add the source-backed virtual-camera authoring loop without pretending the
frontend prototype has LibTV's local signaling infrastructure:

```text
open virtual camera
  -> enter explicit local preview
  -> apply orientation or pointer pose to the active camera
  -> record from the current playhead
  -> import a new named camera and camera track
```

## 2. UI Contract

The existing viewport toolbar gains one icon trigger with accessible label
`虚拟相机`. Its anchored panel has four visible regions:

1. header: title, connection/status dot, close;
2. pairing: source same-Wi-Fi guidance plus a non-scannable pairing motif,
   explicit `本机预演` badge and local-connect action;
3. controls: pose pad, gyro enablement, stability, keep-level, hold and
   elevation;
4. take controls: current playhead/remaining duration, record/stop, sample
   count and import result.

The panel never says a phone is connected when only local preview is active.
Its paired-equivalent status is `本机预演已连接`; source wording
`手机已连接，可开始录制` is reserved in the evidence document until a real phone
transport exists.

## 3. Serializable State

```ts
type DirectorPhoneVcamStatus =
  | "idle"
  | "preparing"
  | "waiting"
  | "local-ready"
  | "recording"
  | "imported"
  | "error";

interface DirectorPhoneVcamState {
  status: DirectorPhoneVcamStatus;
  gyroEnabled: boolean;
  stability: number;
  keepLevel: boolean;
  hold: boolean;
  elevation: number;
  pose: { yaw: number; pitch: number; roll: number };
  recordingStartTime: number | null;
  sampleCount: number;
  takeCount: number;
  importedCameraId: string | null;
  importedTrackId: string | null;
  error: string | null;
}
```

Browser event objects, timers and sample buffers stay inside the panel
component. Camera values passed into the final import action are plain data.

## 4. Pose Contract

### Inputs

- `deviceorientation`: normalized `alpha/beta/gamma` values after permission;
- pointer/touch pose pad: horizontal displacement maps to yaw, vertical
  displacement maps to pitch;
- elevation buttons: fixed positive/negative vertical offsets;
- hold: blocks new pose application while preserving the current preview.

### Mapping

The current active camera's target, radius, FOV and scale form the calibration
baseline. Smoothed yaw/pitch orbit the camera position around its target.
Elevation moves both camera position and target vertically. Keep-level forces
recorded roll to zero.

The clone sensitivity and smoothing formula are calibration, not source facts.
All outputs must remain finite and pitch must be clamped away from the poles.

## 5. Recording Contract

Start guards:

- local preview must be ready;
- active camera and viewport must exist;
- `timeline.currentTime < timeline.duration`.

On start:

1. stop ordinary playback;
2. capture the current playhead as `recordingStartTime`;
3. capture an immediate camera sample;
4. begin a local timer and advance the timeline in real elapsed time;
5. sample the live camera at approximately 10 Hz.

On stop or reaching the timeline end:

1. capture a final sample;
2. reject a take with no finite camera values;
3. normalize sample times to
   `recordingStartTime..timeline.duration`;
4. create a new camera object named `手机运镜 N`;
5. create a `camera` track with the same label and sampled keyframes;
6. select the new camera, track and last keyframe;
7. set status to `imported` and expose imported identifiers.

Recording does not overwrite the source camera track.

## 6. Responsive Contract

- Desktop: panel is positioned above the viewport toolbar and capped at
  approximately `340px`.
- Mobile: panel uses `left/right: 12px`, moves above the compact toolbar and
  stays within the viewport height with internal scrolling.
- Opening the panel does not resize the R3F canvas or timeline.
- Controls have fixed dimensions so status and sample-count changes do not
  shift the toolbar or composition frame.

## 7. Evidence Labels

Every screenshot/implementation document must distinguish:

- `source-backed`: title, state vocabulary, controls and import semantics;
- `clone-calibrated`: trigger placement, panel geometry, pose pad, timing and
  math;
- `not implemented`: LAN/QR/certificate/WebRTC/diagnostics.
