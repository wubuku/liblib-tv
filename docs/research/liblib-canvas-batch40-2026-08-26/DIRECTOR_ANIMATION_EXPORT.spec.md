# Director Animation Export Specification

## 1. Purpose

Close the source-backed director workflow after preview: record the authored
timeline from the real 3D viewport, produce a browser-playable video and return
it to the source React Flow graph as one derived video node.

## 2. UI Contract

The director header owns a compact `导出视频到画布` command. Activating it opens
one anchored `导出设置` surface containing:

- `时长`: numeric seconds, clamped to `1..timeline.duration`;
- `比例`: `16:9`, `9:16` and `1:1`;
- primary `导出视频到画布` command;
- busy copy `正在导出动画视频...`;
- progress percentage;
- success copy `动画视频已导出到画布`;
- the most specific supported failure message.

While exporting:

- trigger and settings controls are disabled;
- closing the panel or workspace is blocked;
- transform/path/grid/camera-rig helpers are hidden via the existing capture
  state;
- the export state remains visible rather than becoming a detached toast.

## 3. Recording Contract

### Inputs

```ts
interface DirectorVideoExportRequest {
  id: number;
  durationSeconds: number;
  aspectRatio: DirectorAspectRatio;
}
```

The viewport resolves the request against:

- the actual R3F `gl.domElement`;
- the current composition-frame crop;
- `timeline.duration`;
- `setTimelineTime`;
- the current active camera metadata.

### Output sizes

| Ratio | Output |
|---|---:|
| `16:9` | `960 x 540` |
| `9:16` | `540 x 960` |
| `1:1` | `720 x 720` |

These are clone calibration, not source measurements.

### Timeline mapping

```text
record elapsed / requested output duration
  -> normalized progress 0..1
  -> timeline time 0..timeline.duration
```

This exports the complete authored animation even when the output duration is
shorter than the fixed clone timeline.

### Frame pipeline

1. Stop ordinary playback and seek to timeline `0`.
2. Wait for R3F to render.
3. Draw the visible aspect-frame crop from WebGL into an output canvas.
4. Validate that the first frame has non-zero/non-transparent pixel data.
5. Start `outputCanvas.captureStream(30)` and `MediaRecorder`.
6. On each animation frame, update timeline time, wait for render, draw and
   report progress.
7. Request final recorder data, stop and close all media tracks.
8. Reject an empty chunk list or zero-size blob.
9. Create a blob URL and return first-frame PNG poster plus scalar metadata.
10. Restore the user's prior timeline time/playback state in `finally`.

### MIME selection

Try in order:

```text
video/webm;codecs=vp9
video/webm;codecs=vp8
video/webm
```

This is an explicit frontend fallback. It does not claim source MP4 parity.

## 4. Error Contract

| Condition | User-facing result |
|---|---|
| `MediaRecorder` missing | `当前浏览器不支持导出动画视频` |
| canvas `captureStream` missing | `当前浏览器无法录制画布视频` |
| no supported recorder MIME | `当前浏览器不支持导出动画视频` |
| blank first frame | `导出视频画面为空` |
| recorder event/start/stop failure | `动画视频录制失败` |
| zero-byte blob | `导出视频为空` |
| graph transaction rejects result | `视频已生成，但画布节点创建失败` |

The source string says “视频已上传，但画布节点创建失败”; the clone must not use
“已上传” because no upload occurred.

## 5. Canvas Transaction

```ts
interface DirectorAnimationExportMetadata {
  sourceNodeId: string;
  exportId: string;
  sceneName: string;
  cameraId: string | null;
  cameraName: string;
  aspectRatio: DirectorAspectRatio;
  width: number;
  height: number;
  durationSeconds: number;
  mimeType: string;
  sizeBytes: number;
  createdAt: string;
  edgeId: string;
}
```

`canvasStore.createDirectorAnimationExport` receives metadata plus
`videoUrl` and `posterDataUrl`. One transaction:

1. verifies source node and non-empty URL;
2. finds the next collision-free right slot;
3. creates one ready `video` node with ratio-shaped dimensions;
4. creates one direct edge from source to result;
5. selects the result;
6. pushes exactly one history snapshot.

The node filename is `{sceneName} 动画导出`, matching the source naming template
without claiming exact source label normalization.

## 6. Video Rendering

When `VideoNodeData.directorAnimationExport` and `videoUrl` are present:

- render a real `<video controls preload="metadata">`;
- use the recorded first-frame PNG as poster;
- expose MIME, byte size, source, edge and duration as semantic data attributes;
- retain existing selected-node processing tools because source guidance says
  the returned video can continue through canvas editing.

Generic ready fixture videos keep the existing poster-based mock player.

## 7. Responsive Contract

- Desktop panel is anchored below the header export trigger and remains above
  the three-column workspace.
- On narrow viewports it stays within `12px` of both horizontal edges and does
  not depend on the hidden Inspector.
- Busy/status text wraps inside the panel; no button width changes with progress.
- The document root and body must not horizontally overflow at `390x844`.
