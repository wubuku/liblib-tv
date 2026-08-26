# ImageNode Specification

## Overview

- **Target file:** `src/components/nodes/ImageNode.tsx`
- **Interaction model:** React Flow draggable/connectable node
- **Current source baseline:** four reference images plus `分镜 #2`

## Structure

```text
ImageNode
├── ImageToolbar via React Flow NodeToolbar (selected only)
├── target/source Handle
├── floating filename + dimensions
├── full-node image and optional watermark, or a typed empty placeholder
└── ImageEditPanel inside the node shell (selected only)
```

Node width and height come from the Zustand canvas data and React Flow's outer transform layer. Do not read `props.style`: xyflow v12 does not pass `node.style` to custom node components.

## Default State

- `4px` corner radius
- subtle border on `#202020`
- image fills the full node with `object-fit: cover`
- filename and source dimensions float above the node
- target/source handles sit at the horizontal midpoint
- optional LibTV watermark is rendered at the image's top-left

## Selected State

- cyan border and low-opacity cyan focus ring
- top horizontal `ImageToolbar`
- bottom `ImageEditPanel`

### Top toolbar

The toolbar uses React Flow `NodeToolbar` with `position=Top`, `align=center`, and `offset=16`. React Flow renders it outside the scaled viewport, so its height and controls stay at screen scale instead of shrinking with canvas zoom.

Toolbar width is a time-versioned content contract, not a permanent global constant:

- the 2026-08-25 source audit measured `900.5x49` with 7 text actions and 4 icon-only actions;
- the 2026-08-26 source audit measured `1092.5x49` on all five existing image nodes, with 9 text actions and 4 icon-only actions;
- the current source wrapper uses `w-fit`; `元素编辑` and `图层分离` added `192px` including gaps.

The current source order is `人像质感调节 / 全景 / 多角度 / 打光 / 九宫格 / 高清 / 元素编辑 / 图层分离 / 宫格切分`, followed by annotate, rotate, download and preview icons. The clone currently remains on the older fixed-width/action baseline; treat this as a documented gap until code changes are authorized. See [`../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md).

These actions do not share one graph-mutation contract. Preview opens a page overlay; annotate, rotate and element edit enter dedicated tool modes; layer separation owns an asynchronous composition state. Active annotate replaces the standard toolbar, hides the bottom generation panel and overlays a canvas on the selected node. The complete source-state and side-effect matrix is [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md).

Its horizontal center equals the selected node center. It is not centered in the browser viewport and is not clamped at the viewport edge.

### Bottom editor

The editor is a child of `ImageNode`, centered on the node and counter-scaled by `1 / zoom`. See `ImageEditPanel.spec.md` for the exact formula and measurements.

## Panorama Derived State

Batch 20 replaces the previous clone-only behavior that copied source media immediately after `全景`.

```text
source image
  └── edge
      └── selected 720°全景图
          ├── 700x350 dark panorama placeholder
          └── specialized 660x252 panel
```

- `imageUrl` is `null`; the source image appears only as the panel's single reference.
- world position uses the screenshot-derived offset `source right + 120`, `source y - 110`.
- node and edge insertion are one undo/redo transaction.
- stable placeholder selector: `[data-image-placeholder="panorama"]`.
- exact contract: [`../liblib-canvas-batch20-2026-08-25/PANORAMA_DERIVATION.spec.md`](../liblib-canvas-batch20-2026-08-25/PANORAMA_DERIVATION.spec.md).

Only `全景` has this source-backed derived-node contract. `多角度`, `打光`, `九宫格`, `高清` and `宫格切分` still use older clone prototype behavior and must not be described as faithful until each action is sampled on the source.

## Video Frame Capture State

Batch 29 uses the ordinary ImageNode renderer for video frame outputs:

- `filename` is `首帧`, `尾帧`, or `截图`;
- logical dimensions inherit the source video resolution;
- `imageUrl` is currently the source poster, explicitly as prototype fallback;
- image alt comes from source-backed `视频首帧 / 视频尾帧 / 视频截图`;
- metadata exposes source ID/label, kind, capture time, name, alt and edge ID;
- selecting the result opens the same ImageToolbar and ImageEditPanel as an
  ordinary image.

Stable root selector: `[data-video-frame-capture]`.

## Required Regressions

- selecting any image shows exactly one top toolbar and one bottom panel
- entering an active image tool replaces the standard toolbar and hides the bottom generation panel; it does not add a third floating layer
- clicking empty canvas removes both overlays
- switching selected image moves both overlays to the new node
- node drag and viewport pan keep both overlays attached
- 28%, 53%, and 100% zoom preserve toolbar/panel screen size; toolbar width matches the action set for the selected source baseline
- mobile clipping follows the original; do not move the overlays to page center to keep them visible
- `scripts/verify-liblib-batch9.py` remains green
- the five initial image nodes preserve their explicit editor height, Prompt, references, top controls and settings matrix
- `scripts/verify-liblib-batch10.py` remains green
- panorama creation preserves placeholder, edge, panel anchor and single-transaction history
- `scripts/verify-liblib-batch20.py` remains green
- video frame results preserve metadata, ordinary image overlays and
  single-transaction history
- `scripts/verify-liblib-batch29.py` remains green

## Assets

- `public/images/scene-coffee-1.png`
- `public/images/scene-coffee-2.png`
- `public/images/scene-coffee-3.png`
- `public/images/scene-coffee-4.png`
- `public/images/storyboard-2.png`
