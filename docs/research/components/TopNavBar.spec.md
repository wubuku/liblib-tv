# TopNavBar Specification

## Overview

- **Target file:** `src/components/TopNavBar.tsx`
- **Position:** Floating controls at `top: 16px`, without a full-width header background.
- **Interaction model:** Left project/canvas navigation, workbench/storyboard segmented controls, and right share/credits/Agent commands.

## Current structure

```text
left:
  LibTV mark -> FrameOS route
  CanvasTabDropdown -> active canvas and project context
  workbench / storyboard controls

right:
  share
  local credits display
  Agent
```

- The project name is not a separate top-nav pill. It lives inside `CanvasTabDropdown`, matching the saved source screenshot.
- The right command cluster is hidden on compact viewports.
- Opening Agent causes the floating nav to avoid the right drawer.

## Interactions

| Element | Effect |
|---|---|
| LibTV mark | Navigates to `/frameos/canvas/demo` as the local route switch |
| Canvas button | Toggles the source-shaped project/canvas dropdown |
| Workbench | Sets `editorMode = "workbench"` |
| Storyboard | Sets `editorMode = "storyboard"` and opens Agent through `uiStore` |
| Share | Opens the local source-shaped share panel |
| Credits | Display-only local prototype |
| Agent | Opens the Agent drawer |

## Evidence

- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- [`../liblib-canvas-batch14-2026-08-25/`](../liblib-canvas-batch14-2026-08-25/)
- [`../liblib-canvas-batch16-2026-08-25/`](../liblib-canvas-batch16-2026-08-25/)

## Files referenced

- `src/components/TopNavBar.tsx`
- `src/components/CanvasTabDropdown.tsx`
- `src/store/uiStore.ts`
