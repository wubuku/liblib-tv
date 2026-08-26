# Batch 37 计划：导演台运动轨迹与速度曲线

## 1. 缺口与价值排序

| Candidate | Current clone | Current source evidence | Value | Decision |
|---|---|---|---:|---|
| preset path creation | absent | direct workflow and labels | 5 | implement line/ring/rectangle |
| visible R3F trajectory | absent | path preview contract | 5 | implement |
| path-driven scrub/playback | absent | direct guide step | 5 | implement |
| orient-to-path | absent | direct command + Y lock hint | 5 | implement for non-camera transform tracks |
| speed curve presets | linear only | direct preset labels | 5 | implement |
| custom Bezier curve | absent | direct adjust/value labels | 5 | implement with draggable handles |
| pencil/pen path drawing | absent | direct labels | 5 | next batch after preset foundation |
| editable path anchors | absent | direct anchor vocabulary | 5 | next batch with real handles |
| path offset transform | absent | direct properties | 4 | defer with anchor editor |
| animation video return | screenshot only | direct guided step 5 | 5 | after path authoring matures |

## 2. Source Fact / Replication Fact / Clone Decision

### LibTV source fact

- A selected character or camera can receive a new track.
- Creating a path opens options for ring, line, rectangle, pencil and pen paths.
- Playback previews the resulting animation.
- A selected track can open a speed curve editor with named presets and Bezier
  adjustment.
- Non-camera objects may bind orientation to the path, taking control of Y rotation.

### Existing replication fact

- The fixed upstream R3F replication still has no timeline/path/curve domain.
- Batch 35 supplies the real R3F scene and Batch 36 supplies typed tracks/playback.

### Clone decision

- Add serializable motion paths to `directorStore` and bind at most one path to a
  typed track.
- Implement line/ring/rectangle presets because their source labels and workflow
  are explicit.
- Generate path geometry around the track object's authored start position.
  Exact point count, radius, extents and color are clone calibration.
- Path position overrides sampled position; transform/camera keyframes still drive
  rotation, scale, target and FOV.
- A track-level cubic Bezier speed curve remaps normalized path/timeline progress.
- Preset control points are clone calibration:
  `linear`, `smooth`, `ease-in`, `ease-out`, `ease-in-out`.
- Custom handle dragging is constrained to `[0,1]` and must immediately affect
  scrub/playback sampling.
- `orientToPath` applies only to non-camera transform tracks; camera look-at remains
  controlled by camera target/FOV state.

## 3. State Boundary

```text
DirectorTimelineTrack
  motionPathId?
  speedCurve { preset, control1, control2 }

DirectorMotionPath
  id / objectId / name / preset
  enabled / orientToPath / closed
  points[]

directorStore.timeline
  motionPaths[]
  selectedMotionPathId
  editorMode: timeline | curve

sampling
  seconds -> normalized track progress
  -> cubic Bezier speed remap
  -> path arc-length sampling
  -> position + tangent
  -> existing transform/camera values
```

Three.js runtime objects remain outside Zustand. Path geometry is serializable
tuples and is sampled by pure helpers.

## 4. Implementation Steps

1. Add Bezier solving and polyline arc-length sampling helpers.
2. Extend timeline tracks/state with speed curves and serializable motion paths.
3. Add path create/delete/enable/orient actions and deterministic fixture geometry.
4. Apply path position and optional tangent Y rotation in timeline sampling.
5. Render selected/all enabled trajectories and anchor points in the R3F viewport.
6. Add source-labeled preset path menu to the timeline controls.
7. Add a functional curve-editor mode with source preset labels, SVG curve,
   draggable handles and numeric values.
8. Add desktop/mobile Playwright covering creation, sampling, curve effect,
   orient-to-path, delete/disable and zero overflow.
9. Record screenshots once, update stable docs, run regressions and quality gates.

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-create-motion-path]` | path menu trigger |
| `[data-director-motion-path-menu]` | preset menu |
| `[data-director-motion-path-preset]` | line/ring/rectangle command |
| `[data-director-motion-path-id]` | R3F path presentation |
| `[data-director-motion-path-anchor]` | visible path anchor |
| `[data-director-motion-path-enabled]` | path enable toggle |
| `[data-director-motion-path-orient]` | orient-to-path toggle |
| `[data-director-delete-motion-path]` | delete selected/bound path |
| `[data-director-open-curve-editor]` | curve editor command |
| `[data-director-curve-editor]` | curve editor root |
| `[data-director-curve-preset]` | named preset command |
| `[data-director-curve-handle]` | draggable Bezier handle |
| `[data-director-curve-values]` | current control point values |
| `[data-director-back-to-timeline]` | restore track timeline |

## 6. Acceptance Criteria

- Selecting a track enables `创建运动轨迹`; no selected track keeps it disabled.
- The menu exposes exactly the implemented source-backed presets: `直线路径`,
  `圆环路径`, `矩形路径`.
- Creating a preset binds one path to the selected track and prevents orphan paths.
- An enabled path is visible in director view, hidden during helper-free capture
  and identifiable by stable path/anchor selectors.
- Scrub/playback moves the bound object or camera along the path deterministically.
- Disable falls back to ordinary keyframe sampling without deleting path data.
- Delete removes path and track binding, then falls back safely.
- Orient-to-path changes non-camera Y rotation from tangent and exposes the
  source-backed lock hint; camera tracks do not expose the toggle.
- Curve editor requires a selected track and uses the exact source preset labels.
- Changing presets or custom handles changes sampled midpoint progress and R3F
  object position, not only the SVG.
- Custom Bezier values remain finite and within `[0,1]`.
- Back returns to the ordinary timeline without changing current time.
- Desktop and `390x844` remain usable with internal overflow only.
- Existing Batch 35 capture return and Batch 36 timeline contracts remain green.
- No page, console, request or WebGL errors.

## 7. Out Of Scope

- pencil/pen/freehand drawing gestures;
- 3D anchor insertion, deletion or Bezier handle manipulation;
- symmetric/asymmetric path anchor semantics;
- path offset position/rotation/scale Inspector;
- multiple paths per track or path-to-track reassignment;
- path undo/redo/persistence;
- property curves per transform axis;
- pose/group tracks, animation export and phone virtual camera;
- claiming Batch 37 geometry or preset control points are measured LibTV values.

## 8. Status

- [x] Fresh source string context and guide workflow extracted
- [x] Scope, selectors and acceptance matrix documented
- [x] Bezier/path pure helpers and store schema
- [x] R3F trajectory and path-driven playback
- [x] Path commands and functional curve editor
- [ ] Playwright, screenshots, regressions and final documentation
