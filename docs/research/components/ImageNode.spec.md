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

## Media And Frame Authority

The current runtime has two dimension owners that must not be conflated:

- `ImageNodeData.width/height` describes the clone's intended media dimensions;
- the React Flow node `width/height` describes the graph frame and selected-overlay anchor.

The five initial landscape fixtures deliberately align those values with the
current LibTV source samples. Generic image creation, most derived-image actions
and portrait/square Director captures do not: they can retain one media ratio
while falling back to a `512x288` graph frame. The resulting centered
`object-cover` crop is a current runtime limitation, not a source-backed product
rule.

The normative authority, frame-policy and rendition rules are in
[`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md).
In particular:

- ordinary source-shaped landscape fixtures use `CANVAS_PRIMARY_IMAGE` with a
  media-shaped frame and centered cover;
- thumbnail dimensions, generation labels and React Flow measured dimensions do
  not replace full-media intrinsic dimensions;
- a future media/output switch must update identity and metadata atomically and
  may reflow the frame only through a declared policy;
- passive measurement may refresh toolbar/panel anchors but is not semantic
  resize or graph history;
- source portrait/square behavior remains gated and must not be invented from
  the Open Canvas fixed-card policy.

## Selected State

- cyan border and low-opacity cyan focus ring
- top horizontal `ImageToolbar`
- bottom `ImageEditPanel`

### Top toolbar

The toolbar uses React Flow `NodeToolbar` with `position=Top` and `align=center`. React Flow renders it outside the scaled viewport, so its height and controls stay at screen scale instead of shrinking with canvas zoom. Batch 51 maps the live viewport zoom to `offset = 10 + 24 * zoom`; this is equivalent to the current LibTV source host's `nodeTop - 24 * zoom - 10` plus `translateY(-100%)`, producing a `10 + 24 * zoom` gap. See [`../liblib-canvas-batch51-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch51-2026-08-26/IMPLEMENTATION.md) and [`../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md#35-源站-chunk-对顶部-host-定位的直接证据).

Toolbar width is a time-versioned content contract, not a permanent global constant:

- the 2026-08-25 source audit measured `900.5x49` with 7 text actions and 4 icon-only actions;
- the 2026-08-26 source audit measured `1092.5x49` on all five existing image nodes, with 9 text actions and 4 icon-only actions;
- the current source wrapper uses `w-fit`; `元素编辑` and `图层分离` added `192px` including gaps.

The current source order is `人像质感调节 / 全景 / 多角度 / 打光 / 九宫格 / 高清 / 元素编辑 / 图层分离 / 宫格切分`, followed by annotate, rotate, download and preview icons. Batch 52 renders this current action shell with a `1092.5x49` host. `标注` and `元素编辑` now have separate empty replacement states. Batch 56 adds a bounded rotate graph slice: when media exists, `旋转` creates and selects a `旋转与镜像` image node with a source edge and typed `rotateMirror` metadata; when media is absent, the action remains disabled. The local slice does not implement bitmap rotation, angle/mirror controls, dirty/save semantics or provider work. See [`../liblib-canvas-batch52-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch52-2026-08-26/IMPLEMENTATION.md), [`../liblib-canvas-batch53-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch53-2026-08-26/IMPLEMENTATION.md), [`../liblib-canvas-batch54-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch54-2026-08-26/IMPLEMENTATION.md), [`../liblib-canvas-batch56-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch56-2026-08-26/IMPLEMENTATION.md) and [`../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md).

These actions do not share one graph-mutation contract. In the clone, Preview opens a page overlay; active annotate and element edit each replace the standard toolbar, hide the bottom generation panel and render their own node-local empty authoring surface. Annotate exposes source-shaped tools plus an enabled no-op save; element edit exposes point/box/brush controls, a masked stage and an empty record panel. Neither empty state records edits or mutates the graph. Rotate, layer separation and download remain separate bounded actions. The complete source-state and side-effect matrix is [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md).

Its horizontal center equals the selected node center. It is not centered in the browser viewport and is not clamped at the viewport edge.

### Bottom editor

The editor is a child of `ImageNode`, centered on the node and counter-scaled by `1 / zoom`. See `ImageEditPanel.spec.md` for the exact formula and measurements.

### Overlay owner and hit-testing boundary

The standard pair is owned by the selected image node. Both surfaces expose the
same `data-owner-node-id`; after selection migration the old pair must unmount
and the new pair must mount without changing graph/history. Batch 60 also makes
the panel wrapper and non-interactive regions transparent to pointer hit
testing while restoring `pointer-events: auto` on textarea, buttons and
popover controls.

This pointer policy is a clone-owned interaction decision. The current source
evidence does not establish how LibTV routes a click on an adjacent node when
that node is covered by an editable panel, so the contract must not claim
source-exact routing for that case.

### Preview state

Clicking the enabled `预览` action dispatches an `ImagePreviewState` to the
page-level `uiStore` and mounts `ImagePreviewOverlay` outside the React Flow
transform layer. The overlay is fixed to the viewport, preserves the source
media ratio, and closes through its button or Escape without changing the
selected node, Prompt, graph, viewport or history. See
[`ImagePreviewOverlay.spec.md`](ImagePreviewOverlay.spec.md) and the Batch 52
runtime audit.

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

The capture metadata preserves the source video resolution, but the current
graph insertion path still uses the generic landscape image frame. This is
harmless only for matching landscape media and is explicitly tracked as
`LIBTV-MRG-005`; the spec does not claim portrait/square capture parity.

Stable root selector: `[data-video-frame-capture]`.

## Required Regressions

- selecting any image shows exactly one top toolbar and one bottom panel
- the current clone toolbar exposes 13 source-shaped actions in source order;
  `预览` opens the page-level read-only overlay and the five unimplemented
  high-risk actions do not create graph mutations
- entering an active image tool replaces the standard toolbar and hides the bottom generation panel; it does not add a third floating layer
- clicking enabled `旋转` creates one `旋转与镜像` image node, one source edge and a typed `rotateMirror` marker; the node is selected immediately
- clicking `旋转` on a no-media image is disabled/no-op
- element edit specifically renders a `272x44` toolbar, node-local stage and `400x50` empty record panel
- clicking empty canvas removes both overlays
- switching selected image moves both overlays to the new node
- standard toolbar and panel carry the same `data-owner-node-id`; selection migration leaves exactly one pair
- panel non-interactive regions do not blanket-capture pointer while textarea, buttons and popovers remain interactive
- node drag and viewport pan keep both overlays attached
- 28%, 53%, and 100% zoom preserve toolbar/panel screen size; toolbar width matches the action set for the selected source baseline
- mobile clipping follows the original; do not move the overlays to page center to keep them visible
- `scripts/verify-liblib-batch9.py` remains a historical compatibility check;
  `scripts/verify-liblib-batch52.py` is the current action-set/Preview check
- the five initial image nodes preserve their explicit editor height, Prompt, references, top controls and settings matrix
- `scripts/verify-liblib-batch10.py` remains green as a historical five-state
  image-panel/AutoLink compatibility check
- `scripts/verify-liblib-batch60.py` covers owner identity, selection migration,
  pointer boundary, active-tool replacement and graph/history isolation
- panorama creation preserves placeholder, edge, panel anchor and single-transaction history
- `scripts/verify-liblib-batch20.py` remains green
- video frame results preserve metadata, ordinary image overlays and
  single-transaction history
- `scripts/verify-liblib-batch29.py` remains green
- future `LIBTV-VR-023` replaces ratio-coincidence assumptions with deterministic
  square/portrait/odd-ratio, mixed-output and editor-transform checks; until that
  fixture exists, existing batch verifiers are compatibility evidence only

## Assets

- `public/images/scene-coffee-1.png`
- `public/images/scene-coffee-2.png`
- `public/images/scene-coffee-3.png`
- `public/images/scene-coffee-4.png`
- `public/images/storyboard-2.png`
