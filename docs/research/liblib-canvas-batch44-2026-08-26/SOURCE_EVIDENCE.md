# Batch 44 Source Evidence

## 1. Fresh Current Extraction

Observation date: 2026-08-26.

Target:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| current canvas HTML | `648317` bytes | `2d25b62abed0ce241795902940f3910c4578f8b81337e5456c11e8bd4ce2d0e0` |
| compressed locale response | `113458` bytes | `ca7be6208e2c16a57f718398f14b3fcb389daf5760644551558aa67d1976f492` |
| decoded locale chunk | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The HTML references 108 unique current JavaScript chunks. The decoded locale
hash matches the Batch 43 extraction. The HTML hash differs despite identical
size, so it is treated as a fresh shell fetch rather than a stable application
artifact.

## 2. Exact Current Contracts

```text
directorCameraMotionPresetButton: 预设运镜
directorCameraMotionPresetShort: 预设
directorCameraMotionPresetReplace: 替换运镜
directorCameraMotionPresetAppend: 追加运镜
directorCameraMotionPresetOrbit: 环绕
directorCameraMotionPresetHalfArc: 半弧
directorCameraMotionPresetPushIn: 推近
directorCameraMotionPresetPullOut: 拉远
directorCameraMotionPresetPedestalUp: 升降
directorCameraMotionPresetTruckRight: 横移
directorCameraMotionPresetSpiralUp: 螺旋上升
directorCameraMotionPresetNoRoom: 当前时间轴没有可追加的时长
directorCameraMotionPresetFollowBlocked: 跟随目标时不可使用预设运镜
```

This directly proves:

- a dedicated preset-camera-motion entry;
- replace and append modes;
- seven named motion choices;
- an append failure when the timeline has no remaining duration;
- incompatibility with active camera follow.

## 3. What The Source Does Not Prove

The public locale does not establish:

- where the entry is placed or whether the surface is a popover/modal/panel;
- preset iconography, grid shape, spacing or responsive layout;
- generated keyframe count, duration, geometry, target behavior or FOV;
- whether replace clears paths, keyframes or an internal clip/segment;
- whether append begins at the playhead, last keyframe or last motion clip;
- easing defaults or whether source presets use paths instead of keyframes;
- whether successful application closes the surface.

No authenticated preset panel screenshot, DOM, computed CSS or runtime state
was captured. Those areas must remain clone calibration.

## 4. Adjacent Proven Contract

Batch 43 already implements the exact conflict boundary:

```text
跟随目标时不可使用预设运镜
```

The preset trigger and store action must both enforce it. UI disablement alone
is insufficient because `window.__director_store` actions are part of the
browser verification surface.
