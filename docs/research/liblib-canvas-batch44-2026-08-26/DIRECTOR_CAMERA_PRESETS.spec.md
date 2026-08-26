# Director Preset Camera Motion Specification

## Interaction Model

```text
selected camera track
  -> open 预设运镜
  -> choose 替换运镜 / 追加运镜
  -> choose one source-named preset
  -> generate ordinary camera keyframes
  -> existing timeline sampling drives R3F
```

The surface is click-driven. Scrub/playback uses the existing time-driven
camera track.

## Serializable Contract

```ts
type DirectorCameraMotionPresetId =
  | "orbit"
  | "half-arc"
  | "push-in"
  | "pull-out"
  | "pedestal-up"
  | "truck-right"
  | "spiral-up";

type DirectorCameraMotionPresetMode = "replace" | "append";

interface DirectorCameraMotionPresetApplication {
  trackId: string;
  preset: DirectorCameraMotionPresetId;
  mode: DirectorCameraMotionPresetMode;
  startTime: number;
  endTime: number;
  generatedKeyframeIds: string[];
  error: string | null;
}
```

No Three.js values or parallel animation engine enter Zustand.

## Replace

- Use the active sampled camera value as the generated start value.
- Generate sorted camera keyframes across `0..timeline.duration`.
- Replace the selected camera track's previous keyframes.
- Keep the selected track and current playhead.
- If a generic motion path is bound, preserve it but set `enabled: false`.

## Append

- Read the latest existing camera keyframe time/value.
- If it reaches timeline duration, reject without mutation and expose
  `当前时间轴没有可追加的时长`.
- Otherwise generate across `latest..timeline.duration`.
- Preserve all prior keyframes and append generated values after the duplicate
  start sample.
- Disable but preserve any bound generic path.

## Follow Conflict

If the camera has a follow target:

- disable the trigger;
- expose `跟随目标时不可使用预设运镜`;
- reject the store action without changing keyframes, paths or application
  metadata.

## Clone-Calibrated Geometry

- `环绕`: one full horizontal orbit around the current target.
- `半弧`: a 180-degree horizontal arc.
- `推近`: reduce camera-target radius while preserving view direction.
- `拉远`: increase camera-target radius.
- `升降`: raise the camera while preserving the target.
- `横移`: translate camera and target together along camera-local right.
- `螺旋上升`: full orbit plus vertical rise.

Every result is finite and rounded. Generated values preserve FOV, transform
rotation/scale and use ordinary typed camera keyframes.

## UI Contract

- Timeline entry: `预设运镜`.
- Two equal segmented modes: `替换运镜`, `追加运镜`.
- Seven compact source-named options.
- Status/error area has stable height so content does not shift.
- The panel is anchored to the timeline control band and remains above the
  timeline; compact screens may scroll the internal option grid.

The placement, icons, sizes and colors are clone calibration because no source
panel visual was recovered.

## Verification

Focused Playwright must verify:

- exact labels and selectors;
- all seven generated trajectories are finite and distinct;
- replace/append keyframe contracts;
- no-room and follow atomic rejection;
- generic path disable/preservation;
- target/FOV preservation;
- real WebGL pixel changes at matched playhead states;
- desktop/mobile bounds and zero browser errors.
