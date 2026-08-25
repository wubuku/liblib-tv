# BottomToolbar Specification

## Overview

- **Target file:** `src/components/BottomToolbar.tsx`
- **Role:** Secondary bottom canvas-controls toolbar.
- **Position:** Fixed near the lower-left; shifts right when the 240px AssetManagerPanel is open.
- **Related primary toolbar:** `LeftSidebar.tsx` is the compatibility name for the centered add/move/toolbox/material/character/history/shortcuts/tutorial toolbar.

## Controls

| Control | State / command |
|---|---|
| 资产管理 | `uiStore.toggleAssetPanel` |
| 整理画布 | page `onOrganize` |
| 缩略图 | `uiStore.toggleMinimap` |
| 节点连线 | `uiStore.toggleEdges` |
| 吸附到网格 | `uiStore.toggleSnapToGrid` |
| 缩放百分比 | `uiStore.toggleZoomMenu` |

The snap and zoom controls are hidden only in the middle compact range (`640-850px`) to protect layout; they remain available at the 390px mobile viewport.

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
