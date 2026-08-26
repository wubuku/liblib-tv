# Director Motion Path And Speed Curve Specification

## 1. Data Contract

```ts
type DirectorSpeedCurvePreset =
  | "linear"
  | "smooth"
  | "ease-in"
  | "ease-out"
  | "ease-in-out"
  | "custom";

interface DirectorSpeedCurve {
  preset: DirectorSpeedCurvePreset;
  control1: [number, number];
  control2: [number, number];
}

interface DirectorMotionPath {
  id: string;
  objectId: string;
  name: string;
  preset: "line" | "ring" | "rectangle";
  enabled: boolean;
  orientToPath: boolean;
  closed: boolean;
  points: DirectorTuple3[];
}
```

Tracks own `motionPathId` and `speedCurve`. Paths remain timeline-owned serializable
data. One path may be bound to one track in Batch 37.

## 2. Speed Sampling

- Convert seconds to normalized progress across `[0, duration]`.
- Solve cubic Bezier X for that normalized time, then read Bezier Y as remapped
  progress.
- Clamp inputs, control points and result to `[0,1]`.
- A linear curve exactly preserves progress.
- Nonlinear presets and custom handles must affect both keyframe interpolation and
  path position.
- Pure helpers must not import React, R3F or mutable Three.js scene objects.

## 3. Path Sampling

- Preset paths are ordered 3D point arrays on the ground plane around the object's
  authored starting position.
- Line is open; ring and rectangle are closed.
- Sample by cumulative segment length so equal progress covers equal path distance.
- Closed paths include the final-to-first segment without duplicating the first
  point in persisted state.
- Return both position and normalized tangent.
- Disabled/missing/invalid paths return ordinary keyframe sampling.
- A path with fewer than two distinct points is invalid and must not move the object.

## 4. Composition With Keyframes

For a bound enabled path:

1. sample the track using the remapped speed progress;
2. replace transform/camera position with path position;
3. preserve sampled scale and non-Y rotation;
4. when `orientToPath` is enabled on a non-camera transform track, set Y rotation
   from the ground-plane tangent;
5. preserve camera target and FOV for camera tracks.

Path sampling must never author keyframes or mutate path control points.

## 5. R3F Presentation

- Enabled paths render only in director view and only while not capturing.
- Use an unframed world-space line, not an HTML card or SVG overlay.
- The path bound to the selected track/object is brighter than other paths.
- Persisted points render as small world-space anchors.
- Path helpers do not intercept object selection.
- Capture output must remain helper-free.

## 6. Timeline Commands

- `创建运动轨迹` opens a trigger-relative menu.
- Implemented commands are `直线路径`, `圆环路径`, `矩形路径`.
- Creating a new preset replaces the selected track's previous path and removes
  the replaced orphan from `motionPaths`.
- The bound path row exposes enable, orient where supported and delete.
- Path creation selects the bound track/path and leaves the current playhead stable.

## 7. Curve Editor

- `曲线编辑器` switches the timeline body from track rows to one selected-track
  curve surface.
- No selected track shows the exact source empty copy.
- Preset commands use the source labels `线性`, `平滑`, `缓入`, `缓出`,
  `缓入缓出`.
- The SVG plots the cubic curve and its two handle lines.
- Dragging either handle updates normalized control points and switches the preset
  to `custom`.
- `贝塞尔曲线参数` exposes current values as tabular text.
- `返回时间线` restores track rows without changing selection or time.

## 8. Responsive Contract

- The editor remains inside the existing timeline band.
- Preset controls may scroll horizontally on compact viewports.
- The graph has stable dimensions and does not resize when values change.
- Document/body must not gain horizontal overflow.

## 9. Evidence Boundary

The command vocabulary and guided workflow are direct current LibTV source facts.
Preset geometry, colors, control-point values, one-path-per-track ownership and
timeline-integrated editor layout are Batch 37 clone calibration.
