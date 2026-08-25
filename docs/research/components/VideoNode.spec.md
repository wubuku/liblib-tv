# VideoNode Specification

## Overview

- **Target file:** `src/components/nodes/VideoNode.tsx`
- **Type ID:** `video`
- **Current source baseline:** one failed Seedance video inside the source video group
- **Interaction model:** draggable/connectable React Flow node with failed and ready media states plus single-selection editing overlays

## Data Shape

```typescript
interface VideoNodeData {
  filename?: string;
  model?: string;
  status?: "empty" | "failed" | "ready" | "pending";
  durationSeconds?: number;
  resolution?: string;
  posterUrl?: string;
  prompt?: string;
  continuation?: VideoContinuationMetadata;
  subtitleErase?: SubtitleEraseMetadata;
  audioSplit?: AudioSplitMetadata;
}
```

The initial failed video has `parentId: "g-EFbbHpwq5w"` and relative position `(62,62)`. Its displayed absolute position is derived from the video group.

## Structure

```text
VideoNode
├── VideoProcessingToolbar (ready + single selected)
├── target/source Handle
├── floating filename + resolution
├── media body
│   ├── failed: warning icon, 生成失败, model
│   ├── ready: poster, play button, local timeline + frame camera
│   └── empty: waiting-for-continuation body
└── selected lower editor
    ├── VideoGenerationPanel
    ├── SegmentReshootPanel for reshoot
    └── VideoContinuationSelector for continuation range selection
    └── SubtitleErasePanel for smart/region subtitle erase
```

## States

### Failed

- dark `#202020` media body
- red warning icon and `生成失败`
- model label
- single selection shows `VideoGenerationPanel`
- no top processing toolbar

### Ready

- local poster and play control
- duration/timeline overlay
- optional local enhanced visual filter
- single selection shows `VideoProcessingToolbar`
- lower editor defaults to `VideoGenerationPanel`
- toolbar can switch the lower editor to `片段重拍` or `智能续写`
- `片段重拍` uses a separate filmstrip + Prompt editor stack; the active toolbar command switches back to the generator
- `智能续写` first shows only the `660x56` range selector; confirm creates and selects a connected target video
- `智能去字幕` and `框选去字幕` open a compact lower panel; region mode also overlays a multi-rectangle editor on the video
- while subtitle mode is open, the normal generator and top processing toolbar are hidden
- `逐帧拉片` creates a connected top-level `shot-breakdown` node
- the top frame group creates first/last/current linked image resources
- the player camera clicks directly to current-frame capture; hover exposes the
  same three frame commands
- the local range playhead supplies current-frame time for the prototype
- frame capture preserves source selection so repeated capture remains available

### Empty Continuation Target

- dark empty media body with play glyph and `等待续写内容`
- filename is `续写 {sourceLabel}`
- no processing toolbar because the target is not ready media
- selected target shows `VideoGenerationPanel` with continuation context
- `退出续写模式` preserves the target but removes continuation metadata and its declared edge

### Pending Subtitle-Erase Target

- filename is `视频一键去字幕-{sourceLabel}`
- no processing toolbar or normal video generator
- smart copy：`点击生成自动去除字幕`
- region copy：`框选区域生成去字幕视频`
- target metadata records source, mode, region snapshot, model/request mode and edge

### Pending Silent-Video Target

- filename is `{sourceLabel}_无声`
- no source poster is reused as if the media processing had completed
- body shows a muted `无声视频结果` resource placeholder
- duration and resolution inherit the source
- metadata records source, split mode, `outputKind: "silent-video"` and the
  direct source edge
- selection moves to this rightmost output after the transaction

### Selection

- cyan border and low-opacity focus ring
- overlays only appear when this is the sole selected node
- multi-selection hides both top and bottom single-node overlays

## Floating UI Contract

The lower editor is mounted inside the video node, centered on the child and inverse-scaled by `1 / zoom`. It remains `660px` wide on screen and is not clamped to the browser viewport.

Generation/reshoot use the source semantic `16 * zoom` gap and clone compensation `bottom: -17px`. The continuation selector uses `8 * zoom` and `bottom: -9px`.

For the parented failed video:

- child drag keeps the panel continuously attached;
- pan and zoom preserve the center and screen size;
- dragging the parent switches selection to the parent and unmounts the panel;
- selecting the child again anchors the panel to its new absolute position.

See `VideoGenerationPanel.spec.md`, `SegmentReshootPanel.spec.md`, `VideoContinuationSelector.spec.md`, `SubtitleErasePanel.spec.md`, and the Batch 9 floating anchor spec for measurements.

## Frame Capture

Batch 29 adds a source-backed video-to-image path:

- first：`0s`, `首帧`, `视频首帧`;
- last：`duration - 0.05s`, `尾帧`, `视频尾帧`;
- current：local playhead, `截图`, `视频截图`;
- source-to-image direct edge;
- first result at source right `+100` world units and the same Y;
- repeated results use clone slot search;
- source remains selected;
- one image + edge is one undo/redo transaction.

The current prototype reuses the source poster; it does not decode a real frame.
See
[`../liblib-canvas-batch29-2026-08-25/FRAME_CAPTURE_WORKFLOW.spec.md`](../liblib-canvas-batch29-2026-08-25/FRAME_CAPTURE_WORKFLOW.spec.md).

## Files Referenced

- `src/components/nodes/VideoNode.tsx`
- `src/components/VideoGenerationPanel.tsx`
- `src/components/VideoProcessingToolbar.tsx`
- `src/components/SegmentReshootPanel.tsx`
- `src/components/VideoContinuationSelector.tsx`
- `src/components/SubtitleErasePanel.tsx`
- `src/store/canvasStore.ts`
- `scripts/verify-liblib-batch9.py`
- `scripts/verify-liblib-batch23.py`
- `scripts/verify-liblib-batch26.py`
- `scripts/verify-liblib-batch27.py`
- `scripts/verify-liblib-batch28.py`
- `scripts/verify-liblib-batch29.py`
