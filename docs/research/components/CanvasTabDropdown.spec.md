# CanvasTabDropdown Specification

## Overview

- **Target file:** `src/components/CanvasTabDropdown.tsx`
- **Trigger:** Top-left active canvas button.
- **State:** `canvasStore` owns `projectName`, canvases and active canvas; `uiStore` owns dropdown visibility.

## Structure

```text
当前项目
[editable project name]
----------------------
画布                  [+]
[active canvas]       [check]
[other canvases]
```

The active canvas is ordered first and shown with a right-side check, matching the saved source screenshot. Row-level more actions remain a clone interaction surface for rename/copy/delete; their expanded visual is not claimed as source fact.

## Interactions

| Action | Effect |
|---|---|
| Click project name | Enters inline editing |
| Enter / blur | Stores a trimmed, non-empty project name |
| Click canvas | Activates it and closes the dropdown |
| Click `+` | Creates and activates an empty canvas, then closes |
| Rename | Commits the canvas name and closes |
| Copy | Deep-copies the canvas graph, activates the copy and closes |
| Delete | Removes the canvas when more than one remains, then closes |
| Outside click / Escape | Closes the dropdown and clears local edit/menu state |

## Stable selectors

- `[data-canvas-trigger]`
- `[data-canvas-project]`
- `[data-canvas-project-input]`
- `[data-canvas-new]`
- `[data-canvas-row="<canvas-id>"]`
- `[data-canvas-active="true"]`
- `[data-canvas-active-check]`
- `[data-canvas-row-menu="<canvas-id>"]`

## Evidence and verification

- [`../liblib-canvas-batch16-2026-08-25/`](../liblib-canvas-batch16-2026-08-25/)
- `scripts/verify-liblib-batch16.py`
