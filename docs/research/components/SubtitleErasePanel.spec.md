# SubtitleErasePanel

## Purpose

`src/components/SubtitleErasePanel.tsx` is the ready-video lower compact editor for `智能去字幕` and `框选去字幕`. In region mode it also owns the video-local rectangle session.

## Source Contract

- centered node-relative lower overlay
- source class semantics：`absolute -bottom-4`
- content-driven width, `48px` height
- `8px` panel padding and `12px` child gap
- `32x32` close
- `13px` mode label
- region help plus select/undo/redo/reset
- power cost display
- `28x28` submit
- region submit disabled without rectangles

## Region Contract

- normalized `relX / relY / width / height`
- multiple rectangles
- selected rectangle move
- corner resize
- undo/redo/reset session history
- active drawing toggle
- selected styling uses source-extracted cyan border/fill

The clone uses local history and does not claim source store/API parity.

## Graph Handoff

Submit calls `canvasStore.createSubtitleErase` once. The store creates a right-side pending video and one edge, records one history snapshot and selects the target.

## Prototype Boundary

- cost is `-`
- no real subtitle detection or media processing
- no schema validation, credits, task submission or polling
- pending target remains in memory until another local graph command changes it

## Evidence

- `docs/research/liblib-canvas-batch27-2026-08-25/SOURCE_EVIDENCE.md`
- `docs/research/liblib-canvas-batch27-2026-08-25/SUBTITLE_ERASE_WORKFLOW.spec.md`
- current source bundles sampled on 2026-08-25

## Stable Selectors

- `[data-subtitle-erase-panel]`
- `[data-subtitle-region-overlay]`
- `[data-subtitle-region]`
- `[data-subtitle-region-handle]`
- `[data-subtitle-region-undo]`
- `[data-subtitle-region-redo]`
- `[data-subtitle-region-reset]`
- `[data-subtitle-erase-submit]`
