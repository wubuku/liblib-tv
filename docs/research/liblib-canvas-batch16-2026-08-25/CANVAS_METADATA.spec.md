# Canvas Navigation and Metadata Specification

## Scope

- **Target files:** `src/components/CanvasTabDropdown.tsx`, `src/components/TopNavBar.tsx`, `src/store/canvasStore.ts`
- **Trigger:** Top-left LibTV canvas button
- **State source:** `useCanvasStore` for project metadata and canvas data; `useUIStore` for dropdown visibility

## Source-shaped structure

```text
Canvas button: [active canvas name] [chevron]
  └─ dropdown
      ├─ 当前项目
      ├─ [editable project name]
      ├─ divider
      ├─ 画布                         [+ 新建画布]
      └─ canvas rows                 [active check]
```

The existing row-level action menu remains a clone interaction surface for rename/copy/delete. Its unexpanded visual is not asserted as source fact in this batch.

## State contract

```ts
interface CanvasState {
  projectName: string;
  setProjectName: (name: string) => void;
  canvases: CanvasData[];
  activeCanvasId: string;
}
```

- `projectName` is project-level, separate from `CanvasData.name`.
- `setProjectName` trims whitespace and ignores an empty name.
- This is browser-memory prototype state; refresh persistence is out of scope.

## Interaction contract

| Action | Expected result |
|---|---|
| Open canvas button | Opens the dropdown and shows project context |
| Click project name | Enters inline edit |
| Enter or blur project name | Stores trimmed value and exits edit |
| Click active/inactive canvas row | Activates the canvas and closes dropdown |
| Click new canvas | Creates and activates a new empty canvas, then closes dropdown |
| Rename / copy / delete | Performs existing store action and closes dropdown |
| Outside click / Escape | Closes dropdown |
| Open another top-level overlay | Canvas dropdown is closed by `uiStore` exclusivity |

## Stable selectors

- `[data-liblib-overlay="canvas-dropdown"]`
- `[data-canvas-trigger]`
- `[data-canvas-project]`
- `[data-canvas-project-input]`
- `[data-canvas-new]`
- `[data-canvas-row="<canvas-id>"]`
- `[data-canvas-active="true"]`
- `[data-canvas-active-check]`
- `[data-canvas-row-menu="<canvas-id>"]`

## Non-goals

- No backend project API.
- No persistence across refresh.
- No account permissions, collaboration or server-side deletion.
