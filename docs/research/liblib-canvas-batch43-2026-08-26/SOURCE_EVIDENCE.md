# Batch 43 Source Evidence

## 1. Fresh Current Extraction

Observation date: 2026-08-26.

Target:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The current public canvas shell was fetched again:

| Artifact | Size | SHA-256 |
|---|---:|---|
| canvas HTML | `648317` bytes | `03e4cd7690143c1f05343c1e10b67517207438813c94e8c4843d85300e5acb26` |
| current locale chunk | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The HTML referenced 108 unique current JavaScript chunks. Their decoded total
was `14439615` bytes. A complete corpus search found every camera-follow key
below only in:

```text
0_o2gxip5splz.js
```

Therefore the evidence proves current product vocabulary and explicit
conflicts, but does not recover component DOM, CSS, state schema or runtime
math.

## 2. Exact Camera Contracts

### Look-at

```text
directorCameraLookAt: 注视目标
directorCameraManualCoord: 手动坐标
directorCameraManualRotation: 手动旋转
directorCameraLookAtCoord: 注视坐标
```

This proves at least two look-at authoring modes: a coordinate target and a
camera-rotation mode. The locale does not prove the dropdown geometry, whether
scene objects appear in the same chooser or the rotation order.

### Follow

```text
directorCameraFollowTarget: 跟随目标
directorCameraFollowNone: 不跟随
directorCameraFollowOffset: 跟随偏移
directorCameraFollowViewMode: 跟随视角
directorCameraFollowThirdPerson: 第三人称
directorCameraFollowFirstPerson: 第一人称
```

This proves a selectable target, a no-follow state, an editable offset and two
view modes. It does not prove:

- whether offsets use world or target-local coordinates;
- character eye/head focus height;
- first-person forward distance;
- smoothing, dead zones or collision behavior;
- whether follow configuration itself can be keyframed.

### Explicit conflicts

```text
directorCameraMotionPresetFollowBlocked: 跟随目标时不可使用预设运镜
directorCameraFollowDisableBeforePathBind: 请先关闭机位跟随，再绘制轨迹
directorPhoneVcamDisableFollowHint: 请先关闭机位跟随，再使用手机运镜
```

These are direct source product constraints. A clone that allows a followed
camera to bind a new motion path or start phone-camera authoring would violate
the current source contract.

## 3. Adjacent Preset-Motion Vocabulary

The same locale section also contains:

```text
预设运镜
预设
替换运镜
追加运镜
环绕
半弧
推近
拉远
升降
横移
螺旋上升
当前时间轴没有可追加的时长
```

This is a high-value future batch. It is not added here because the current
clone already has a different path-preset workflow and the source runtime
geometry/timing for replace versus append has not been recovered.

## 4. Runtime Evidence Limit

No authenticated camera-follow panel screenshot, DOM state or computed CSS was
captured for this batch. The source page remained the target of the extraction,
but the current chunk corpus exposes only locale strings for this feature.

Consequences:

- source labels and the three conflict rules may be used verbatim;
- panel spacing, widgets and responsive geometry must follow the established
  clone Inspector design and remain labeled clone calibration;
- target-relative math must be implemented as deterministic prototype behavior,
  not described as recovered LibTV internals.
