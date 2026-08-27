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
- entering region mode centers the source and raises zoom to at least `1`

## Region Contract

- normalized `relX / relY / width / height`
- multiple rectangles
- selected rectangle move
- corner resize
- undo/redo/reset session history
- active drawing toggle
- selected styling uses source-extracted cyan border/fill

The clone uses local history and does not claim source store/API parity.

Current `relX / relY / width / height` values are normalized against the visible
node overlay. They are not yet proven full-video coordinates. Under a
cover-cropped poster, a rectangle can therefore select a different region from
the eventual full media.

One pointer draw/move/resize interaction produces at most one local snapshot;
new interaction clears redo, and reset is a reversible local history command.
The history is capped at 30 entries and remains outside graph history before
confirm.

## Graph Handoff

Submit calls `canvasStore.createSubtitleErase` once. The store creates a right-side pending video and one edge, records one history snapshot and selects the target.

The formal `RECORD_EDITOR` session/commit boundary is
[`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md).
Current synchronous confirm has no panel-level submitting/idempotency token, so it
must not be reused unchanged for real asynchronous processing.

For a future full-media subtitle request, the editor must satisfy the open gate,
fit transform, drift and commit-baseline rules in
[`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md).
An explicitly visible-crop-only product mode may retain visible-render
coordinates, but must carry the exact crop/rendition descriptor and must not be
described as editing the untouched full video. This distinction is design-only;
the current Batch 27 verifier does not prove it.

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
