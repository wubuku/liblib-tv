# Batch 36 计划：导演台动画时间轴第一条纵切

## 1. 缺口与价值排序

| Candidate | Current clone | Current source evidence | Value | Decision |
|---|---|---|---:|---|
| typed timeline + playhead | absent | direct current chunk strings | 5 | implement |
| scrub/playback/loop | absent | direct current chunk strings | 5 | implement |
| transform/camera keyframes | absent | direct typed-keyframe strings | 5 | implement |
| add/remove/select track and keyframe | absent | direct track/keyframe lifecycle strings | 5 | implement |
| auto-keyframe editing | absent | source capability contract | 4 | implement for current runtime fields |
| curve editor | absent | direct strings, no runtime geometry | 5 | next batch |
| motion paths | absent | direct strings, needs track foundation | 5 | after curve foundation |
| pose/group keyframes | no pose/group runtime | direct strings | 4 | defer until model exists |
| animation-video return | screenshot return only | direct export strings | 5 | after playback/path maturity |

## 2. Source Fact / Replication Fact / Clone Decision

### LibTV source fact

- The current loaded locale chunk names the animation timeline, playhead,
  play/pause, loop, zoom, track creation/removal and keyframe navigation.
- Keyframes are typed: transform, pose, prop, group and camera.
- Curves, paths and animation-video return are separate product layers.

### Existing replication fact

- The fixed upstream R3F replication provides the static scene/camera workspace.
- It has no timeline, playback, keyframes, paths or animation export.

### Clone decision

- Add a full-width bottom timeline band beneath the existing three-zone desk.
- Keep timeline state in `directorStore`; it remains independent from React Flow
  graph history.
- Implement discriminated transform and camera tracks because those values exist
  and can drive the current R3F scene.
- Seed one character track and one camera track so playback is demonstrable
  immediately; exact values are clone fixture data.
- Use linear interpolation in this batch. Curve/easing state is reserved for the
  next layer rather than hidden inside an uneditable default.
- Use an `8s` scene duration and second-based ruler as calibration, not source fact.
- Auto-keyframe records Inspector edits and completed TransformControls drags at
  the current playhead; timeline sampling itself never writes new keyframes.

## 3. State Boundary

```text
directorStore
  timeline:
    duration / currentTime / playing / loop / zoom / autoKeyframe
    tracks[] / selectedTrackId / selectedKeyframeId

  actions:
    setTimelineTime -> clamp + deterministic sample
    setTimelinePlaying / toggle loop / set zoom
    addTrackForObject / removeTrack
    addKeyframe / deleteKeyframe / selectKeyframe
    seekPreviousKeyframe / seekNextKeyframe
    recordObjectKeyframe

DirectorTimeline
  requestAnimationFrame playback clock
  controls / ruler / tracks / keyframe markers / playhead

DirectorInspector + DirectorViewport
  authored edit -> update object/camera -> optional recordObjectKeyframe
```

## 4. Implementation Steps

1. Add timeline discriminated unions and pure sampling helpers.
2. Extend `directorStore` with seeded tracks and deterministic seek/playback state.
3. Add `DirectorTimeline` bottom band with controls, ruler, rows and playhead.
4. Add track/keyframe lifecycle and selected-object routing.
5. Wire Inspector and TransformControls commits to auto-keyframe.
6. Verify R3F transform and camera sampling at exact times.
7. Verify playback, loop, zoom, mobile internal scrolling and zero page overflow.
8. Add Batch 36 screenshot ledger, Playwright verifier and stable-doc updates.
9. Run focused regressions, `npm run docs:check`, `npm run check` and
   `git diff --check`.

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-timeline]` | timeline root |
| `[data-director-timeline-controls]` | playback/track/keyframe command row |
| `[data-director-playback]` | play/pause command |
| `[data-director-loop]` | loop toggle |
| `[data-director-auto-keyframe]` | auto-keyframe toggle |
| `[data-director-timeline-time]` | current time readout |
| `[data-director-timeline-zoom]` | zoom range |
| `[data-director-timeline-ruler]` | scrub surface |
| `[data-director-playhead]` | visible current-time line |
| `[data-director-track-id]` | typed track row |
| `[data-director-keyframe-id]` | keyframe marker |
| `[data-director-add-track]` | add track for selected object |
| `[data-director-add-keyframe]` | add/update keyframe at playhead |
| `[data-director-delete-keyframe]` | delete selected keyframe |

## 6. Acceptance Criteria

- Timeline is a stable bottom band and does not overlap the viewport toolbar,
  side rails or mobile drawers.
- Default scene exposes one transform track and one camera track with at least two
  keyframes each.
- Clicking/scrubbing the ruler updates `currentTime` and interpolates the R3F
  character or camera deterministically.
- Playback advances the playhead and scene; pause freezes them.
- Loop wraps at duration; loop-off stops at duration.
- Previous/next keyframe navigation seeks to the correct global keyframe.
- Selecting a keyframe seeks time and synchronizes object/tree/Inspector context.
- `+ 轨道` creates one typed track for the selected object and prevents duplicates.
- Manual add updates an existing keyframe at the same time rather than duplicating it.
- Deleting a selected keyframe updates both UI and sampled scene safely.
- With auto-keyframe enabled, Inspector edits and gizmo commits record at the
  current time; scrub/playback never create keyframes.
- Timeline zoom changes internal content width without document horizontal overflow.
- Desktop and `390x844` remain usable; timeline content scrolls internally.
- No page/console/WebGL errors.

## 7. Out Of Scope

- spline/Bezier curve editor and easing handles;
- freehand, pen or preset motion paths;
- orient-to-path and speed curves;
- pose/SAM bone and group runtime;
- frame-rate selection and frame-number timecode;
- director undo/redo stack or persistence;
- animation recording, upload and video-node return;
- claiming Batch 36 dimensions are measured LibTV geometry.

## 8. Status

- [x] Fresh current HTML/chunk evidence extracted
- [x] Scope, selectors and acceptance matrix documented
- [x] Timeline schema and sampling helpers
- [x] Timeline UI and scene/camera playback
- [x] Track/keyframe lifecycle and auto-keyframe
- [x] Focused Playwright and screenshot verification
- [x] Cross-batch regressions, stable docs and final quality gate
