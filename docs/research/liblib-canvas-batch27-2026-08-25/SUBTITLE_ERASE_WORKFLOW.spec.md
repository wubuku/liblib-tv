# Subtitle Erase Workflow

## Purpose

复刻当前 LibTV ready video 的两种去字幕画布工作流：

```text
ready source video
  -> toolbar dropdown
  -> smart compact panel
     OR region overlay + compact panel
  -> submit
  -> connected pending subtitle-erase video
```

## Mode Contract

```typescript
type SubtitleEraseMode = "smart" | "region";

interface SubtitleEraseRegion {
  id: string;
  relX: number;
  relY: number;
  width: number;
  height: number;
}
```

所有坐标均归一化到 source media box 的 `0..1`。

## Compact Panel Contract

- node-relative centered overlay
- source semantic bottom offset：`16` flow units
- height：`48px`
- width：content-driven
- surface gap：`12px`
- horizontal/vertical padding：`8px`
- close：`32x32`
- mode label：`13px`
- region tools：four `32x32` icon buttons
- submit：`28x28`
- smart submit enabled
- region submit disabled until at least one region exists
- close and capture-phase Escape clear the workflow

Stable selectors:

- `[data-subtitle-erase-panel]`
- `[data-subtitle-erase-mode]`
- `[data-subtitle-erase-close]`
- `[data-subtitle-erase-help]`
- `[data-subtitle-region-toggle]`
- `[data-subtitle-region-undo]`
- `[data-subtitle-region-redo]`
- `[data-subtitle-region-reset]`
- `[data-subtitle-erase-cost]`
- `[data-subtitle-erase-submit]`

## Region Editor Contract

- only mounted in `region` mode
- absolute overlay clipped to source media
- active drawing cursor：crosshair
- supports multiple rectangles
- click rectangle selects it
- selected rectangle can move
- four corner handles can resize
- minimum width/height：`0.02`
- undo/redo history includes create, move, resize and reset
- reset clears all regions and is itself undoable
- closing mode discards session history

Stable selectors:

- `[data-subtitle-region-overlay]`
- `[data-subtitle-region]`
- `[data-subtitle-region-selected="true"]`
- `[data-subtitle-region-handle]`

## Graph Contract

Submit creates one transaction:

- target type：`video`
- target status：`pending`
- target filename：`视频一键去字幕-{sourceLabel}`
- target position：source right + `120` world units
- one source-to-target edge
- target metadata:
  - source node ID and label
  - source poster URL
  - mode
  - cloned region array
  - edge ID
  - model `volcano-subtitle-eraser`
  - request mode `Subtitle` or `Text`
- selection moves to target

Pending body copy:

- smart：`点击生成自动去除字幕`
- region：`框选区域生成去字幕视频`

Undo removes target and edge together. Redo restores both.

## Prototype Boundary

No subtitle detection, media processing, schema validation, credits, task submission, polling, failure cleanup or persistence. The target remains pending to make the local boundary explicit.
