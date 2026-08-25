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
  status?: "empty" | "failed" | "ready";
  durationSeconds?: number;
  resolution?: string;
  posterUrl?: string;
  prompt?: string;
  continuation?: VideoContinuationMetadata;
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
│   ├── ready: poster, play button, local timeline
│   └── empty: waiting-for-continuation body
└── selected lower editor
    ├── VideoGenerationPanel
    ├── SegmentReshootPanel for reshoot
    └── VideoContinuationSelector for continuation range selection
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
- `逐帧拉片` creates a connected top-level `shot-breakdown` node

### Empty Continuation Target

- dark empty media body with play glyph and `等待续写内容`
- filename is `续写 {sourceLabel}`
- no processing toolbar because the target is not ready media
- selected target shows `VideoGenerationPanel` with continuation context
- `退出续写模式` preserves the target but removes continuation metadata and its declared edge

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

See `VideoGenerationPanel.spec.md`, `SegmentReshootPanel.spec.md`, `VideoContinuationSelector.spec.md`, and the Batch 9 floating anchor spec for measurements.

## Files Referenced

- `src/components/nodes/VideoNode.tsx`
- `src/components/VideoGenerationPanel.tsx`
- `src/components/VideoProcessingToolbar.tsx`
- `src/components/SegmentReshootPanel.tsx`
- `src/components/VideoContinuationSelector.tsx`
- `src/store/canvasStore.ts`
- `scripts/verify-liblib-batch9.py`
- `scripts/verify-liblib-batch23.py`
- `scripts/verify-liblib-batch26.py`
