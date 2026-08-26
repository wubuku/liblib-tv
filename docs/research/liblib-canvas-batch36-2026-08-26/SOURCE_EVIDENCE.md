# Batch 36 Source Evidence

## 1. Fresh Source Extraction

Observation date: 2026-08-26.

The target canvas HTML was fetched again from:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The response was `648317` bytes and contained `734` LibTV static chunk
references, `108` unique. It still directly referenced:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
```

The chunk was gzip-compressed:

| Artifact | Size | SHA-256 |
|---|---:|---|
| downloaded response | `113458` bytes | `ca7be6208e2c16a57f718398f14b3fcb389daf5760644551558aa67d1976f492` |
| decoded JavaScript | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The minified source is not committed. This document preserves the extracted
product-contract facts so later agents do not need to repeat the same recognition.

## 2. Direct Timeline Strings

The decoded current chunk contains all of these exact strings:

```text
动画时间轴
动画时间轴播放头
播放/暂停
循环播放
时间轴缩放
◆ 添加关键帧
上一关键帧
下一关键帧
当前帧有关键帧
当前帧无关键帧
新建轨道
新建轨道后可录制关键帧动画
移除轨道
解除当前选中元素的动画轨道
```

This confirms a time-driven editing surface with track lifecycle, a playhead,
playback, loop, zoom and explicit keyframe navigation. It is stronger than a
generic marketing reference, but does not reveal exact runtime geometry.

## 3. Direct Typed-Keyframe Strings

The same current chunk contains:

```text
变换关键帧
姿态关键帧
道具关键帧
分组关键帧
机位关键帧
机位轨
运镜轨道
机位自动帧轨迹
```

It also contains source contracts for:

```text
曲线
曲线编辑器
启用曲线
编辑属性曲线
选择一个轨道后编辑速度曲线
```

Therefore LibTV's timeline is typed rather than a flat list of timestamp markers.
The current Batch 35 clone can immediately support real transform and camera
tracks. Pose, group and curve UI must wait for corresponding runtime state.

## 4. Output And Path Boundary

The source also confirms later layers:

```text
路径绘制后点击播放，可预览动画
已开启沿路径朝向，Y 轴旋转由运动轨迹控制
正在导出动画视频...
动画视频已导出到画布
```

These are not Batch 36 acceptance criteria. They define the next sequence:

```text
typed timeline
  -> path/curve authoring
  -> animation recording/export
  -> video node return
```

## 5. Runtime Questions Still Open

- Exact timeline height, track-label width and ruler density.
- Whether the source timeline spans below all three columns or only the viewport.
- Default duration, frame rate and snapping increments.
- Whether auto-keyframe is enabled by default.
- Exact curve editor presentation and whether it replaces or expands the timeline.
- Account/feature gating for pose, group, phone-camera and animation export.

Until authenticated runtime geometry is measured, Batch 36 layout values remain
explicit clone calibration and must not be promoted to source facts.
