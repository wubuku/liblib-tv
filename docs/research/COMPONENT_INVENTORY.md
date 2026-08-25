# Component Inventory

This is the authoritative catalog of components in this clone. For each, file path, purpose, and visual/behavioral notes are documented. Layout details that don't fit here live in individual specs under `./components/`.

> **Source of truth for component structure**: this file. For per-component interaction details, see `./components/<Name>.spec.md`.

---

## Layout & Shell

| Component | File | Purpose |
|-----------|------|---------|
| `TopNavBar` | `src/components/TopNavBar.tsx` | Top navigation: logo, project name, canvas dropdown, notification, VIP+credits, FrameOS link, user avatar. Height 48px, bg `#141414`. |
| `LeftSidebar` | `src/components/LeftSidebar.tsx` | Compatibility name for the centered primary bottom toolbar with 8 icon buttons and mutually exclusive entry panels. |
| `BottomToolbar` | `src/components/BottomToolbar.tsx` | Centered floating toolbar at bottom: 资产管理 text button, icon buttons, large cyan "+" (add node), zoom %. |
| `ScriptHeader` | `src/components/ScriptHeader.tsx` | Compact "正在跟随" + 取消ESC banner above canvas + script title node. |

## Node Components

All node types inherit the React Flow `NodeProps` shape. The connection handle is rendered by `<Handle>` from `@xyflow/react` and styled via globals.css (see "Node Handle" section of `globals.css`).

| Type ID | File | Notes |
|---------|------|-------|
| `script` | `src/components/nodes/ScriptNode.tsx` | Title + multi-line script text, default 320px wide, bg `#212121`. |
| `image` | `src/components/nodes/ImageNode.tsx` | Image with header (filename + dimensions), watermark overlay. Width capped at 360px. |
| `text` | `src/components/nodes/TextNode.tsx` | Inline-editable text block. |
| `video` | `src/components/nodes/VideoNode.tsx` | Video preview + "运镜" button → CameraMovementDialog. |
| `script-execution` | `src/components/nodes/ScriptExecutionNode.tsx` | 3-step progress UI (确认镜头/准备资产/合成提示词) + open-script-node button. |
| `storyboard-group` | `src/components/nodes/StoryboardGroupNode.tsx` | Image group with title + thumbnail grid. |

## Edge Components

| Type ID | File | Notes |
|---------|------|-------|
| `default` | `src/components/nodes/DeletableEdge.tsx` | Custom edge with hover-flow effect (3 light segments), base color `#86909c` → `#c0c8d0` on hover/select, strokeWidth 2 → 4. Scissors delete button at midpoint. |

## Panels & Dialogs

| Component | File | Purpose |
|-----------|------|---------|
| `AddNodePanel` | `src/components/AddNodePanel.tsx` | 8 node types grid + 上传/历史选择. Click outside to close. |
| `CanvasTabDropdown` | `src/components/CanvasTabDropdown.tsx` | Multi-canvas switcher dropdown with 新建/重命名/复制/删除. |
| `ToolboxPanel` | `src/components/ToolboxPanel.tsx` | Bottom-toolbar-anchored 480x460 panel with 25 source-derived presets. |
| `MaterialLibraryPanel` | `src/components/MaterialLibraryPanel.tsx` | Bottom-toolbar-anchored 240x163 material menu. |
| `CharacterLibraryPanel` | `src/components/CharacterLibraryPanel.tsx` | Responsive character detail and 23-item asset carousel modal. |
| `HistoryPanel` | `src/components/HistoryPanel.tsx` | Responsive asset history modal with filters, zoom, batch selection and local result images. |
| `ImageToolbar` | `src/components/ImageToolbar.tsx` | Horizontal `NodeToolbar` above the selected image: 人像质感, 全景, 多角度, 打光, 九宫格, 高清, 宫格切分. |
| `ImageEditPanel` | `src/components/ImageEditPanel.tsx` | `660px` node-anchored panel below the selected image; inverse-scales with viewport zoom. |
| `CameraConfigDialog` | `src/components/CameraConfigDialog.tsx` | 9 cameras × 10 lenses × 7 focal lengths × 3 apertures = custom camera config. |
| `CameraMovementDialog` | `src/components/CameraMovementDialog.tsx` | 10 movement types (静止/横摇/俯仰/推拉/横移/升降/旋转/变焦/环绕/摇臂) + speed + duration + amplitude. |
| `KeyboardShortcutsDialog` | `src/components/KeyboardShortcutsDialog.tsx` | Four-column, bottom-toolbar-anchored shortcuts panel without a backdrop. |

## Utilities

| Component | File | Notes |
|-----------|------|-------|
| `PlusIndicator` | `src/components/PlusIndicator.tsx` | **No-op stub.** Previously rendered decorative "+" but removed because it broke drag interaction. Replaced by the handle itself. |
| `CustomHandle` | `src/components/CustomHandle.tsx` | Legacy handle prototype; not currently used. |

---

## State Stores

| Store | File | Responsibility |
|------|------|--------|
| `useCanvasStore` | `src/store/canvasStore.ts` | All canvas data: canvii list, active canvas ID, multi-selection with a primary selected node, nodes, edges, viewport, and per-canvas in-memory history. Includes `addNode`, `duplicateNode`, `groupSelectedNodes`, `ungroupSelectedNodes`, `removeSelectedNodes`, `removeNode`, `addEdge`, `removeEdge`, `undo`, `redo`, `setViewport`, `setActiveCanvas`, `addCanvas`, `removeCanvas`, `duplicateCanvas`, etc. |
| `useUIStore` | `src/store/uiStore.ts` | Panel visibility (add node, shortcuts, asset panel, etc.), grid/minimap/snap toggles, zoom level. `toggleAddNodePanel`, `closeAllPanels`, etc. |

---

## Removed / Planned

These were considered during planning but not implemented in this snapshot:

- **Backend persistence**: every node/edge lives only in Zustand memory. Refresh wipes state.
- **Real image generation / model integration**: prompt + camera + model select are UI scaffold only.
- **Drag-handle "snap to target" animations on top of the connection line preview**.

For future work see [`README.md` → "Known Limitations"](../../README.md#known-limitations--future-work).
