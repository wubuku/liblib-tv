# Batch 46 Source Evidence

## 1. Current LibTV Locale

Observation date: 2026-08-26.

Target:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The current decoded canvas locale is preserved by the earlier Director batches:

```text
0_o2gxip5splz.js
size: 343745 bytes
sha256: 58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277
```

The current locale contains this exact screenshot vocabulary:

```text
directorCameraScreenshotTitle: {label}截图
directorNoCameraScreenshot: 暂无摄像机截图
directorClearAllScreenshots: 全部清空
directorSendAllToCanvas: 发送到画布
directorConfirmClearScreenshots: 确认清空所有截图？
directorCloseScreenshotPreviewAria: 关闭截图预览
```

This directly proves that the Director product has a screenshot-management
surface beyond a one-shot capture toast:

- screenshot records are associated with a camera label;
- an empty camera-screenshot state exists;
- all local screenshots can be cleared;
- all screenshots can be sent to the canvas;
- clearing has a confirmation state;
- a screenshot preview has an explicit close command.

The locale does not prove exact panel geometry, whether the gallery is a tab or
standalone route, card actions, viewer zoom/pan, single-item deletion,
cross-camera grouping or graph transaction semantics.

## 2. Existing Clone Gap

Current clone behavior before Batch 46:

- `directorStore.captures` prepends up to 12 records and tracks only one
  `activeCaptureId`;
- `DirectorInspector` renders one inline `当前截图` preview;
- one active capture can be sent to the canvas;
- there is no capture history grid, camera grouping, clear-all action, bulk
  send action, preview viewer or explicit preview-close action;
- sent captures are marked with `sentNodeId`, but there is no way to navigate
  among prior unsent/sent records.

## 3. Evidence Boundary

The source locale is current product evidence, not an authenticated screenshot
of the gallery DOM. The fixed upstream implementation supplies a concrete
replication reference, but its CSS and interaction details are not automatically
LibTV facts. Any panel dimensions, truncation, hover affordances and graph
placement behavior remain clone calibration unless separately observed on
LibTV.
