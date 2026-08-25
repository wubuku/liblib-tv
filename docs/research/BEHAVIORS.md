# Interaction Behaviors

> Catalog of every interactive behavior in the clone. For edge/node-specific specs, see `./components/`.

## Page-Level

### Canvas Interaction Model
- **Type:** Select/marquee + temporary/persistent pan + zoom + node drag (React Flow)
- **Select mode:** Empty-area left drag creates a partial-intersection marquee selection.
- **Persistent pan:** Press `H`, then left drag the pane. Press `V` to return to select mode.
- **Temporary pan:** Hold `Space` while left dragging the pane; release returns to the persistent tool.
- **Zoom:** Scroll wheel or pinch gesture (configured via `zoomOnScroll`)
- **Initial zoom:** About 53% on desktop and 28% on compact viewports for the source-derived project baseline.
- **Grid snap:** Toggle via `useUIStore.toggleSnapToGrid`; `snapGrid: [20, 20]`

### Keyboard Shortcuts
- `Cmd/Ctrl+Z` — Undo the active canvas graph
- `Cmd/Ctrl+Shift+Z` or `Cmd/Ctrl+Y` — Redo the active canvas graph
- `Cmd/Ctrl+D` — Duplicate the current selection; a single ordinary node keeps connected-edge compatibility, while multi-selection copies internal edges
- `Tab` — Open the add-node panel
- `Option/Alt+Shift+F` — Arrange canvas
- `Escape` — Deselect selection + close panels (`useUIStore.closeAllPanels` + `selectNode(null)`)
- `Delete` / `Backspace` — Delete selected node (calls `useCanvasStore.removeNode`)
- `Cmd/Ctrl+0` — Fit the canvas
- `Cmd/Ctrl++` / `Cmd/Ctrl+-` — Zoom in/out
- `V` / `H` — Select/move tool and hand tool
- Hold `Space` — Temporary hand tool; keyup/blur restores the persistent tool
- `G` — Group at least two selected ordinary nodes
- `Shift+G` — Ungroup the selected group or one of its children

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
- **History:** The graph from drag start is recorded once when the drag ends, so one drag is one undo step.

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

## LeftSidebar (primary bottom toolbar, 8 buttons)

Each button has identical styling: `h-8 w-8 rounded-lg`, hover `bg-[rgba(255,255,255,0.08)]`, active `bg-[rgba(255,255,255,0.15)]`.

| Button | Click Effect |
|--------|-------------|
| 添加节点 (`+` icon) | Toggles `useUIStore.isAddNodePanelOpen` |
| 工具箱 | Toggles local `activePanel === "toolbox"` |
| 素材库 | Toggles `activePanel === "material"` → opens `MaterialLibraryPanel` |
| 角色库 | Toggles `activePanel === "character"` → opens `CharacterLibraryPanel` |
| 历史记录 | Toggles `activePanel === "history"` → opens `HistoryPanel` |
| 快捷键 | Calls `useUIStore.toggleShortcutsPanel` → opens `KeyboardShortcutsDialog` modal |
| 教程 | Toggles the anchored four-command tutorial/help menu |

## AddNodePanel (8 node types)

Opens when clicking the `+` sidebar button. Click outside to close. Clicking a node type calls `useCanvasStore.addNode(type)` which spawns a new node at a default position with default data, then closes the panel.

Node types: text, image, video, composition (Beta), director (NEW), audio, script, library (NEW).

## BottomToolbar (bottom-left canvas controls)

Buttons (left to right):
- **资产管理:** Toggles the `240px` asset drawer.
- **整理画布 (`Option/Alt+Shift+F`):** Applies the source-like semantic topology and opens the keep/restore confirmation.
- **缩略图:** Toggles the React Flow minimap.
- **节点连线:** Shows or hides all edges.
- **吸附:** Toggles `20x20` grid snapping; hidden in the compact middle-width range.
- **缩放百分比:** Opens zoom in/out, fit view, fixed zoom and grid controls.

### Organize Preview

- The source project is arranged as four material nodes on the left, execution/storyboard in the middle, image/video groups on the right, and the script farther right at the top.
- At `929x874`, organized bounds produce about `28%` zoom and the left content starts around `x=48`, `y=49`.
- The confirmation card is fixed at the lower-left, about `168x88`, with the question on the first row and `还原` / `保留` on the second row.
- `还原` restores the pre-organize nodes and viewport.
- `保留` keeps the organized graph; undo/redo then switches between pre-organize and organized node positions.
- Unknown top-level nodes use a stable fallback below the source project. Child nodes retain their parent-relative position.
- See [`liblib-canvas-batch7-2026-08-25/`](./liblib-canvas-batch7-2026-08-25/) for evidence boundaries and measurements.

## Image-Specific Behaviors

### Select Image Node
- **Trigger:** Click an ImageNode
- **Effect:** Shows:
  - `ImageToolbar` above the node — horizontal `900×49` toolbar, node-centered with a `16px` screen-space offset and constant screen size
  - `ImageEditPanel` below the node — `660×274` populated prompt state, node-centered and counter-scaled by `1 / zoom`
  - Both overlays follow node drag, pan, and zoom; neither is clamped or recentered to the browser viewport

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

Opened via the primary toolbar "快捷键" button. The no-backdrop panel is anchored above the toolbar and lists four columns of shortcuts.

## Following Status Banner

- **Position:** Top center of canvas area.
- **Trigger:** Display only (always visible in current clone).
- **Click "取消ESC"** or press `Escape` → closes banner (no-op other than closing panels).

## Panels (open from primary toolbar)

| Panel | Presentation | Trigger |
|-------|------|---------|
| `ToolboxPanel` | 480x460 anchored floating panel | 工具箱 button |
| `MaterialLibraryPanel` | 240x163 anchored floating menu | 素材库 button |
| `CharacterLibraryPanel` | Centered responsive modal | 角色库 button |
| `HistoryPanel` | 90vw responsive modal | 历史记录 button |
| `KeyboardShortcutsDialog` | Wide anchored panel without backdrop | 快捷键 button |
| Tutorial menu | Compact anchored menu | 教程 button |

Primary entry states are mutually exclusive. Character and history use modal backdrops; the other panels preserve canvas context and stay anchored to their toolbar buttons.

## State management notes

- All pan/zoom, edges, node positions live in `useCanvasStore`.
- Graph editing commands use a per-canvas in-memory `past` / `future` history stack; selection, viewport, and panel visibility do not enter the stack.
- All panel visibility lives in `useUIStore`.
- Refresh / new tab = state lost (no backend).
