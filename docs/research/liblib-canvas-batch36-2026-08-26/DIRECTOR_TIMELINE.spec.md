# Director Timeline Specification

## 1. Domain Types

```ts
type DirectorTimelineTrack =
  | {
      kind: "transform";
      objectId: string;
      keyframes: DirectorTransformKeyframe[];
    }
  | {
      kind: "camera";
      objectId: string;
      keyframes: DirectorCameraKeyframe[];
    };
```

Transform values contain complete position/rotation/scale snapshots. Camera values
also contain target and FOV, so a sampled camera frame cannot combine stale camera
properties with a new transform.

Every keyframe has a stable id and seconds-based time. Track keyframes remain sorted
by time after every mutation.

## 2. Sampling Contract

- clamp time to `[0, duration]`;
- before the first keyframe, use the first value;
- after the last keyframe, use the last value;
- between adjacent keyframes, linearly interpolate every scalar;
- timeline sampling updates live objects without recording keyframes;
- authored edits may record a keyframe only through an explicit/manual or
  auto-keyframe action;
- deleting the last keyframe leaves the current authored object state unchanged.

Linear interpolation is deliberate Batch 36 scope. It keeps playback visible and
testable while leaving curve semantics explicit for the next batch.

## 3. Timeline Layout

### Desktop

- full-width bottom band under the three-zone workspace;
- compact command header;
- fixed track-label column and horizontally scrollable time surface;
- one ruler plus one row per track;
- cyan playhead across ruler and all visible rows;
- diamond keyframes, with selected state visually distinct.

### Compact

- shorter band;
- controls may horizontally scroll inside their own row;
- narrower fixed label column;
- track time surface owns horizontal overflow;
- page/document must not overflow.

Exact heights and widths are clone calibration until authenticated source geometry
is measured.

## 4. Interaction Contract

### Selection

- selecting a track selects its object and routes the Inspector;
- selecting a keyframe selects track/object, seeks time and selects the marker;
- selecting an object in tree/viewport does not silently create a track.

### Scrub

- pointer down on ruler or track time surface starts scrubbing;
- pointer movement maps the local X coordinate to timeline seconds;
- pointer up ends the gesture;
- playback pauses at scrub start;
- ruler zoom changes pixels per second, not duration.

### Playback

- play starts from current time;
- if current time equals duration, play restarts at zero;
- requestAnimationFrame advances seconds using wall-clock elapsed time;
- loop wraps modulo duration;
- without loop, playback stops exactly at duration.

### Track And Keyframe Commands

- `+ 轨道` creates a transform or camera track for the selected object;
- duplicate object tracks are not created;
- `◆ 添加关键帧` captures the selected track object's complete current value;
- same-time add replaces the existing keyframe value;
- delete removes only the selected keyframe;
- previous/next searches all keyframes and skips the current timestamp using a
  small epsilon.

### Auto-Keyframe

- when enabled, Inspector transform/camera edits and completed gizmo drags call
  `recordObjectKeyframe`;
- if no track exists, auto-keyframe creates the correct typed track;
- timeline playback/scrubbing does not call authored edit actions and cannot
  recursively create keyframes.

## 5. Accessibility

- icon commands have `aria-label` and `title`;
- toggles expose `aria-pressed`;
- track rows expose selected/kind/object-id data;
- keyframes are buttons with object name and formatted time in their label;
- current time is visible as tabular text;
- scrub surfaces remain pointer-operable without hiding keyframe buttons.

## 6. Verification

The dedicated verifier must assert store values and WebGL pixels. Moving a DOM
playhead without changing the R3F scene is a failure.
