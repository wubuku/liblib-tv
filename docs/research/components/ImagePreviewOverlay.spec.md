# ImagePreviewOverlay

## Purpose

Render the selected image as LibTV's page-level, read-only media preview. This
is an L4 page overlay, not a React Flow node toolbar and not a graph result.

## Source Contract

At `929x874` with a single 2:1 image:

| Element | Source rect |
|---|---|
| overlay | `0,0,929,874` |
| content viewport | `69.67,87.40,789.65,699.20` |
| image | `69.67,239.59,789.65,394.82` |
| watermark | `79.67,249.59,48,23.31` |
| close button | `839.32,75.40,32,32` |

Derived layout:

```text
overlay = fixed inset 0, black / 80%
content = 85vw x 80vh, centered
media = contain within content, preserve source aspect ratio
close = content top/right - 12px, 32x32
watermark = media top/left + 10px, 48x23
```

Source evidence:

- [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#10-图片工具态与预览浮层)
- [`../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)

## State

The preview descriptor contains:

```text
nodeId
filename
imageUrl
watermarkUrl?
width
height
```

It lives in `uiStore`, because the owner is the page shell. The image node only
dispatches `openImagePreview`.

## Lifecycle

```text
selected image
  -> preview action
  -> overlay mounted, close button focused
  -> close button or Escape
  -> overlay unmounted
  -> same selected node and standard toolbar/panel remain
```

Opening, closing and keyboard interaction must not change:

- nodes or edges;
- selected node;
- Prompt, references or generation settings;
- viewport;
- graph history.

While open, ordinary canvas Delete/Backspace/Space/Tab/undo/redo/duplicate/tool
shortcuts do not execute.

## Accessibility

- `role="dialog"` and `aria-modal="true"`;
- a readable dialog label derived from the filename;
- the close button has `aria-label="关闭预览"` and receives initial focus;
- the preview image uses the filename as alt text;
- source lacks a close-button accessible name, but the clone does not copy that defect.

## Boundaries

- Single image only in Batch 52; no output-history previous/next controls;
- watermark is rendered only when the selected node provides `watermarkUrl`;
- no download, save, editing, metadata panel or remote request;
- no graph mutation and no new media node.

