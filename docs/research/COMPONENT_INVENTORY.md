# Component Inventory

This is the authoritative catalog of components in this clone. For each, file path, purpose, and visual/behavioral notes are documented. Layout details that don't fit here live in individual specs under `./components/`.

> **Source of truth for component structure**: this file. For per-component interaction details, see `./components/<Name>.spec.md`.

---

## Layout & Shell

| Component | File | Purpose |
|-----------|------|---------|
| `TopNavBar` | `src/components/TopNavBar.tsx` | Top navigation: logo, project name, canvas dropdown, notification, VIP+credits, FrameOS link, user avatar. Height 48px, bg `#141414`. |
| `LeftSidebar` | `src/components/LeftSidebar.tsx` | Left tool palette with 7 icon buttons (添加节点, 工具箱, 素材库, 角色库, 历史, 快捷键, 教程). Absolutely positioned at left center. |
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
| `ToolboxPanel` | `src/components/ToolboxPanel.tsx` | Preset animation templates (周星驰经典名场面 etc.). |
| `MaterialLibraryPanel` | `src/components/MaterialLibraryPanel.tsx` | Material library side panel (placeholder). |
| `CharacterLibraryPanel` | `src/components/CharacterLibraryPanel.tsx` | Character library side panel (placeholder). |
| `HistoryPanel` | `src/components/HistoryPanel.tsx` | History panel (placeholder). |
| `ImageToolbar` | `src/components/ImageToolbar.tsx` | Vertical icon toolbar for selected image node: 人像质感, 全景, 多角度, 打光, 九宫格, 高清, 宫格切分. |
| `ImageEditPanel` | `src/components/ImageEditPanel.tsx` | Bottom panel for selected image node: style/mark tabs, prompt, model selector, 摄像机 + 运镜 buttons, 生成 button. |
| `CameraConfigDialog` | `src/components/CameraConfigDialog.tsx` | 9 cameras × 10 lenses × 7 focal lengths × 3 apertures = custom camera config. |
| `CameraMovementDialog` | `src/components/CameraMovementDialog.tsx` | 10 movement types (静止/横摇/俯仰/推拉/横移/升降/旋转/变焦/环绕/摇臂) + speed + duration + amplitude. |
| `KeyboardShortcutsDialog` | `src/components/KeyboardShortcutsDialog.tsx` | Modal listing keyboard shortcuts. |

## Utilities

| Component | File | Notes |
|-----------|------|-------|
| `PlusIndicator` | `src/components/PlusIndicator.tsx` | **No-op stub.** Previously rendered decorative "+" but removed because it broke drag interaction. Replaced by the handle itself. |
| `CustomHandle` | `src/components/CustomHandle.tsx` | Legacy handle prototype; not currently used. |

---

## State Stores

| Store | File | Responsibility |
|------|------|--------|
| `useCanvasStore` | `src/store/canvasStore.ts` | All canvas data: canvii list, active canvas ID, nodes, edges, selection, viewport. `addNode`, `removeNode`, `addEdge`, `removeEdge`, `setViewport`, `setActiveCanvas`, `addCanvas`, `removeCanvas`, `duplicateCanvas`, etc. |
| `useUIStore` | `src/store/uiStore.ts` | Panel visibility (add node, shortcuts, asset panel, etc.), grid/minimap/snap toggles, zoom level. `toggleAddNodePanel`, `closeAllPanels`, etc. |

---

## Removed / Planned

These were considered during planning but not implemented in this snapshot:

- **Backend persistence**: every node/edge lives only in Zustand memory. Refresh wipes state.
- **Real image generation / model integration**: prompt + camera + model select are UI scaffold only.
- **Drag-handle "snap to target" animations on top of the connection line preview**.

For future work see [`README.md` → "Known Limitations"](../../README.md#known-limitations--future-work).
