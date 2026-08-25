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
├── full-node image and optional watermark
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

The toolbar uses React Flow `NodeToolbar` with `position=Top`, `align=center`, and `offset=16`. React Flow renders it outside the scaled viewport, so it stays `900.5x49` screen pixels at every zoom.

Its horizontal center equals the selected node center. It is not centered in the browser viewport and is not clamped at the viewport edge.

### Bottom editor

The editor is a child of `ImageNode`, centered on the node and counter-scaled by `1 / zoom`. See `ImageEditPanel.spec.md` for the exact formula and measurements.

## Required Regressions

- selecting any image shows exactly one top toolbar and one bottom panel
- clicking empty canvas removes both overlays
- switching selected image moves both overlays to the new node
- node drag and viewport pan keep both overlays attached
- 28%, 53%, and 100% zoom preserve toolbar/panel screen size
- mobile clipping follows the original; do not move the overlays to page center to keep them visible
- `scripts/verify-liblib-batch9.py` remains green
- the five initial image nodes preserve their explicit editor height, Prompt, references, top controls and settings matrix
- `scripts/verify-liblib-batch10.py` remains green

## Assets

- `public/images/scene-coffee-1.png`
- `public/images/scene-coffee-2.png`
- `public/images/scene-coffee-3.png`
- `public/images/scene-coffee-4.png`
- `public/images/storyboard-2.png`
