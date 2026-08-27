# BottomToolbar Specification

## Overview

- **Target file:** `src/components/BottomToolbar.tsx`
- **Role:** Secondary bottom canvas-controls toolbar.
- **Position:** Fixed near the lower-left; shifts right when the 240px AssetManagerPanel is open.
- **Related primary toolbar:** `LeftSidebar.tsx` is the compatibility name for the centered add/move/toolbox/material/character/history/shortcuts/tutorial toolbar.

## Controls

| Control | State / command |
|---|---|
| 资产管理 | page-owned Asset layout callback |
| 整理画布 | page `onOrganize` |
| 缩略图 | `uiStore.toggleMinimap` |
| 节点连线 | `uiStore.toggleEdges` |
| 吸附到网格 | `uiStore.toggleSnapToGrid` |
| 缩放百分比 | `uiStore.toggleZoomMenu` |

The snap and zoom controls are hidden only in the middle compact range
(`640-850px`) to protect layout; they remain available at the `390px` mobile
viewport.

At `929x874`, the pre-Batch-63 asset-open toolbar overlapped the primary toolbar
by about `231.5px` and intercepted Add Node. Batch 64 regression corrected the
first compact implementation: this toolbar keeps its full control widths and
240px drawer follow, while the primary toolbar applies a screen-space collision
floor. This preserves minimap/zoom trigger geometry and separates screen UI clamp
from graph anchor policy. It remains clone-owned responsive correctness, not a
source-exact policy claim.

## Minimap

- The trigger toggles `uiStore.showMinimap` and exposes `aria-pressed`.
- The `150x110px` minimap is not placed at React Flow's default bottom-right.
- At `929x874`, it is anchored at `left: 152px; bottom: 54px`, approximately aligning its left edge with the minimap trigger.
- Because the offset is relative to the React Flow canvas, opening the 240px asset drawer moves the minimap and trigger right by the same amount.
- At `390x844`, `bottom: 107px` keeps it above the two bottom toolbars.
- The clone does not enable minimap click, pan or zoom without source interaction evidence.

Evidence and verification: [`../liblib-canvas-batch19-2026-08-25/`](../liblib-canvas-batch19-2026-08-25/).

Asset layout transaction and adjacent regression:
[`../liblib-canvas-batch64-2026-08-27/`](../liblib-canvas-batch64-2026-08-27/).

## Zoom menu

The source-shaped menu contains:

1. current percent state row;
2. 放大 `⌘ +`;
3. 缩小 `⌘ -`;
4. 适合屏幕 `⌘ 0`;
5. divider;
6. 50%, 100%, 800%.

The menu is store-driven and participates in top-level overlay mutual exclusion. Zoom actions keep it open; Escape, outside pointerdown and opening another overlay close it.

## Stable selectors

- `[data-viewport-menu-trigger="zoom"]`
- `[data-liblib-overlay="zoom-menu"]`
- `[data-zoom-current]`
- `[data-zoom-action]`

## Evidence

- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- [`../liblib-canvas-batch18-2026-08-25/`](../liblib-canvas-batch18-2026-08-25/)
