# Batch 40 Source Evidence

## 1. Provenance

Observation date: 2026-08-26.

This batch reuses the current LibTV canvas locale extraction already protected
by Batch 36-39. The authenticated target is:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The decoded current locale chunk was:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| compressed response | `113458` bytes | `ca7be6208e2c16a57f718398f14b3fcb389daf5760644551558aa67d1976f492` |
| decoded JavaScript | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |

The minified source is not committed. This document preserves the relevant
product-contract facts so later agents do not need to repeat bundle extraction
or screenshot recognition.

## 2. Direct Export Settings

The current locale contains these exact keys and values:

```text
directorExportToCanvas: 导出视频到画布
directorExportingToCanvas: 导出中
directorExportSettings: 导出设置
directorExportDuration: 时长
directorExportAspectRatio: 比例
directorAnimationExporting: 正在导出动画视频...
directorAnimationExportSuccess: 动画视频已导出到画布
```

This directly establishes:

- an explicit export command;
- a settings surface rather than a one-click-only toast;
- duration and aspect-ratio controls;
- a visible busy state;
- a successful return to the canvas.

It does not establish exact panel placement, control widgets, defaults or
numeric ranges.

## 3. Direct Failure Taxonomy

The same locale contains:

```text
directorAnimationExportFailed: 动画视频导出失败
directorAnimationExportBrowserUnsupported: 当前浏览器不支持导出动画视频
directorAnimationExportMp4Unsupported: 当前浏览器不支持 MP4 画布录制
directorAnimationExportCanvasRecordUnsupported: 当前浏览器无法录制画布视频
directorAnimationExportRecordingFailed: 动画视频录制失败
directorAnimationExportEmptyFrame: 导出视频画面为空
directorAnimationExportEmptyVideo: 导出视频为空
directorAnimationExportReadonly: 只读模式无法导出视频到画布
directorAnimationExportLoginRequired: 请先登录
directorAnimationExportUploadFailed: 上传动画视频失败
directorAnimationExportNodeCreateFailed: 视频已上传，但画布节点创建失败
directorAnimationExportNodeName: {label} 动画导出
```

These strings are strong evidence for a staged pipeline:

```text
capability/auth guard
  -> canvas frame acquisition
  -> video recording
  -> non-empty result validation
  -> upload
  -> returned node creation
```

The source distinguishes upload failure from node-creation failure, so a clone
that only waits and shows a success toast would be materially inaccurate.

## 4. Direct Guided Workflow

The current guide says:

```text
预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑
```

Together with the Batch 36-39 timeline/path evidence, the source-backed workflow
is:

```text
author keyframes/path
  -> preview playback
  -> confirm export settings
  -> record animation video
  -> create canvas video node
  -> continue editing in the graph
```

## 5. Existing Replication Boundary

The fixed submodule at
`research/upstream/storyai-3d-director-desk` provides real R3F scene staging,
camera framing and still captures. Repository-wide searches find no
`MediaRecorder`, `captureStream`, animation timeline, motion-path or animation
video export implementation.

Therefore:

- its viewport and scene architecture remain useful implementation references;
- it does not provide evidence for LibTV export UI, encoding or return behavior;
- Batch 40 is a source-backed extension over the clone's Batch 35-39 timeline
  and path work.

## 6. Clone Calibration Boundary

Until authenticated runtime interaction proves more, these remain clone
decisions:

- export trigger placement in the director header;
- panel width, spacing and mobile geometry;
- duration input range and full-timeline retiming behavior;
- `30fps` recording target and output pixel dimensions;
- WebM fallback instead of source MP4/upload parity;
- session-local blob URL lifetime;
- whether success keeps the director open.

The clone must expose these boundaries in docs and never describe browser-local
WebM output as source-identical backend export.
