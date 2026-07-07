# Interaction Behaviors

> Catalog of every interactive behavior in the clone. For edge/node-specific specs, see `./components/`.

## Page-Level

### Canvas Interaction Model
- **Type:** Pan + Zoom + Drag (React Flow)
- **Pan:** Click + drag on empty canvas area
- **Zoom:** Scroll wheel or pinch gesture (configured via `zoomOnScroll`)
- **Initial zoom:** 54% (`x: 0, y: 0, zoom: 0.54` in `canvasStore.ts`)
- **Grid snap:** Toggle via `useUIStore.toggleGrid`; `snapGrid: [20, 20]`

### Keyboard Shortcuts
- `Option+Shift+F` — Arrange canvas (no-op in clone; reserved for future)
- `Escape` — Deselect selection + close panels (`useUIStore.closeAllPanels` + `selectNode(null)`)
- `Delete` / `Backspace` — Delete selected node (calls `useCanvasStore.removeNode`)
- `Cmd+A` — not implemented

## Edge (Connection Line)

### Hover Effect
- **Trigger:** mouse over `<Handle>` or edge `<path>` hit-area
- **Effect (matches original site):**
  - Base path stroke dimmed to `opacity: 0.45` and color changed to `#c0c8d0` (light gray-blue)
  - `stroke-width` increases from `2` to `4`
  - 3 light segments appear, traveling along the path with cyan glow (CSS-injected `@keyframes` + SVG `<filter>` Gaussian blur)
  - Scissors delete button fades in at the midpoint
  - All transitions in ~150ms

### Click Scissors Delete Button
- **Trigger:** Click button with `data-edge-delete` attribute
- **Effect:** Dispatches `CustomEvent("delete-edge", { detail: { id } })`. `page.tsx` listener calls `useCanvasStore.removeEdge(id)`. Edge disappears.

### Connection Drag
- **Trigger:** Mouse down on `<Handle>`, drag, release on another `<Handle>` or empty space
- **Effect:** React Flow manages the connection-line preview while dragging. On release, `onConnect` creates an edge in `useCanvasStore.addEdge`.
- **Visual feedback during drag:** A cyan bezier path from source to cursor (`react-flow__connection-path`).
- **Snap to valid handles:** `valid` class highlights compatible targets (green).

See [`DeletableEdge.spec.md`](./components/DeletableEdge.spec.md) for full details.

## Node (any type)

### Hover Display
- **Trigger:** Mouse over the node
- **Effect:** Subtle shadow (`hover:shadow-[0_4px_12px_rgba(0,0,0,0.3)]`)
- **Side effect:** Reveals the two `<Handle>` instances at left/right edges with opacity transitioning from `0` to `1`. Each handle renders a "+" glyph via CSS `::before`.

### Selection
- **Trigger:** Click (set by React Flow)
- **Effect:**
  - Border color becomes cyan (`border-[#09caf5]`)
  - Cyan ring shadow (`shadow-[0_0_0_2px_rgba(9,202,245,0.3)]`)
  - Handles stay visible (no hover required while selected)
  - Red delete button `(-top-2 -right-2)` appears on hover (group-hover:opacity-100)

### Drag to Move
- **Trigger:** Mouse down on node body (not handle)
- **Effect:** Standard React Flow drag. `onNodeDragStop` saves the final position to `useCanvasStore` via `setNodes`.

### Handle Drag to Connect
- **Trigger:** Mouse down on `<Handle>`, drag to another `<Handle>`
- **Effect:** Creates a connection edge. See "Edge → Connection Drag" above.
- **Snap behavior (React Flow native):** When dragging close to a valid target handle, that handle highlights (`valid` class, green) and the connection snaps to it.

## TopNavBar

### Project Name Inline Edit
- **Trigger:** Click the project name text (`未命名项目`)
- **Effect:** Input field appears with current value. Press `Enter` or click outside to commit.
- **Current implementation:** Local component state only; not persisted to `canvasStore`.

### Canvas Tab Dropdown
- **Trigger:** Click "画布 2 ▾"
- **Effect:** Dropdown opens showing all canvases. Selecting a canvas calls `useCanvasStore.setActiveCanvas(id)`.
- **Per-canvas actions:** "重命名" (rename — inline edit), "复制" (duplicate — `duplicateCanvas`), "删除" (delete — `removeCanvas`, only if > 1 canvas exists).
- **"新建画布" button:** Creates a new canvas via `addCanvas(name?)`.

### VIP + Credits Button
- Click → opens membership store (not implemented in clone).
- The button shows "⚡ 会员特惠37折 | ⚡ 64" with an orange "限时 37 折" badge above.

### FrameOS Link (NEW)
- Click → navigates to `/frameos/canvas/demo` (added to test navigation).

## LeftSidebar (7 buttons)

Each button has identical styling: `h-8 w-8 rounded-lg`, hover `bg-[rgba(255,255,255,0.08)]`, active `bg-[rgba(255,255,255,0.15)]`.

| Button | Click Effect |
|--------|-------------|
| 添加节点 (`+` icon) | Toggles `useUIStore.isAddNodePanelOpen` |
| 工具箱 | Toggles local `activePanel === "toolbox"` |
| 素材库 | Toggles `activePanel === "material"` → opens `MaterialLibraryPanel` |
| 角色库 | Toggles `activePanel === "character"` → opens `CharacterLibraryPanel` |
| 历史记录 | Toggles `activePanel === "history"` → opens `HistoryPanel` |
| 快捷键 | Calls `useUIStore.toggleShortcutsPanel` → opens `KeyboardShortcutsDialog` modal |
| 教程 | Toggles `activePanel === "tutorial"` (no-op — no panel implemented) |

## AddNodePanel (8 node types)

Opens when clicking the `+` sidebar button. Click outside to close. Clicking a node type calls `useCanvasStore.addNode(type)` which spawns a new node at a default position with default data, then closes the panel.

Node types: text, image, video, composition (Beta), director (NEW), audio, script, library (NEW).

## BottomToolbar (centered floating)

Buttons (left to right):
- **资产管理 (text):** Toggles `useUIStore.toggleAssetPanel` (panel not implemented yet)
- **整理画布 (icon, ⌘+Shift+F):** No-op (reserved for auto-arrange)
- **人物 icon:** No-op
- **`+` large cyan button:** Opens `AddNodePanel`
- **整理节点 (icon):** No-op
- **⭐ icon:** No-op (favorite)
- **⏰ icon:** No-op (history)
- **📷 icon:** No-op (image)
- **? icon:** Opens `KeyboardShortcutsDialog`
- **54% zoom:** Click → no-op in clone (could open a zoom menu)

## Image-Specific Behaviors

### Select Image Node
- **Trigger:** Click an ImageNode
- **Effect:** Shows:
  - `ImageEditPanel` (below the node) — bottom panel with style/mark tabs, prompt textarea, model selector, 摄像机 + 运镜 buttons, generate button
  - `ImageToolbar` (right of the node) — vertical icon toolbar with 7 features (人像质感, 全景, 多角度, 打光, 九宫格, 高清, 宫格切分)
  - The X (close) button on the image header becomes visible

### Click 摄像机 (Camera) Button in ImageEditPanel
- Opens `CameraConfigDialog`.
- Modal: pick from 9 cameras × 10 lenses × 7 focal lengths × 3 apertures.
- **Apply:** Calls `onApply(config)`. Currently `console.log` only. To persist, write to `useCanvasStore.updateNodeData(selectedImageNodeId, { cameraConfig: config })`.

### Click 运镜 (Camera Movement) Button
- Opens `CameraMovementDialog` (shared with `VideoNode`).
- Pick from 10 movement types, 5 speeds, two range sliders for duration (1-10s) and amplitude (0-100%).

## Video-Specific Behaviors

### Select VideoNode
- **Effect:** Shows the 运镜 button at the bottom of the node.
- **Click 运镜:** Opens `CameraMovementDialog`. On apply, the button label updates to show the selected movement type.

## KeyboardShortcutsDialog

Opened via LeftSidebar "快捷键" button or BottomToolbar `?` button. Modal lists keyboard shortcuts.

## Following Status Banner

- **Position:** Top center of canvas area.
- **Trigger:** Display only (always visible in current clone).
- **Click "取消ESC"** or press `Escape` → closes banner (no-op other than closing panels).

## Panels (open from sidebar)

| Panel | Side | Trigger |
|-------|------|---------|
| `ToolboxPanel` | Left | 工具箱 button |
| `MaterialLibraryPanel` | Right | 素材库 button |
| `CharacterLibraryPanel` | Right | 角色库 button |
| `HistoryPanel` | Right | 历史记录 button |

Each panel renders a fixed-position sidebar with grid of items. Click "X" (close button) to dismiss.

## State management notes

- All pan/zoom, edges, node positions live in `useCanvasStore`.
- All panel visibility lives in `useUIStore`.
- Refresh / new tab = state lost (no backend).
