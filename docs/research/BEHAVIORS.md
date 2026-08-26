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

### Top-Level Overlay Lifecycle

- **Primary panel state:** `move`, `toolbox`, `material`, `character`, `history` and `tutorial` are selected by `useUIStore.activePrimaryPanel`, not component-local state.
- **Mutual exclusion:** Opening a top-level surface closes the other primary panel, add-node panel, shortcuts, canvas dropdown, asset drawer, share menu, Agent and zoom menu.
- **Modal boundary:** Character and history modals still use their own backdrop; the backdrop blocks clicks to the canvas and bottom toolbar until the modal is closed.
- **Mode lifecycle:** Entering storyboard mode opens Agent after clearing other top-level surfaces; returning to workbench closes Agent.
- **Escape:** `Escape` invokes `closeAllPanels`, which clears the primary panel and zoom menu as well as the other top-level surfaces.
- **Verification:** `scripts/verify-liblib-batch11.py` and `scripts/verify-liblib-batch18.py`.

### Storyboard Mode

- **Structure:** The current canvas is projected into a left key-elements rail and two story-board columns, `图片` and `视频`; Agent remains a sibling right drawer.
- **Key elements:** Image and script nodes appear in the `图片` and `文本` groups.
- **Selection:** Clicking a storyboard or key-element card calls `useCanvasStore.selectNode`; the selected card exposes `aria-pressed="true"`.
- **Return:** `返回工作台` switches `editorMode` to `workbench` while retaining the selected node.
- **Empty states:** Empty canvases and empty media groups show explicit local prototype empty states.
- **Evidence and verification:** `docs/research/liblib-canvas-batch13-2026-08-25/` and `scripts/verify-liblib-batch13.py`.

### Agent Drawer

- **Source-shaped structure:** 340px right drawer with `新对话`, command icons, 2x2 Skill recommendations, browser notification banner and bottom composer.
- **Skill selection:** Clicking a local Skill card marks it pressed and writes its title into the composer.
- **Recommendation refresh:** `换一批` switches between two local recommendation sets; it does not call a remote recommendation service.
- **Notification banner:** `开启` or close dismisses the local banner.
- **Composer:** Sending non-empty text shows a local-only submission status; no Agent task is dispatched.
- **Share panel:** The top-right panel uses source copy for `在LibTV上发布` and `分享链接`; each command shows an explicit no-backend local status.
- **Evidence and verification:** `docs/research/liblib-canvas-batch14-2026-08-25/` and `scripts/verify-liblib-batch14.py`.

### Director Desk Lifecycle

- **Entry:** the `3D导演台` node CTA uses `nodrag nopan nowheel` plus pointer
  propagation guards, then sets `uiStore.activeDirectorNodeId`.
- **Mount:** `DirectorDesk` is lazy-loaded with `next/dynamic(..., { ssr: false })`
  and covers the viewport as a fixed full-screen authoring surface. React Flow
  remains mounted behind it.
- **Selection:** object-tree rows and R3F meshes share
  `directorStore.selectedObjectId`; empty viewport selection routes the Inspector
  back to scene settings. Selecting a camera also supplies camera-view controls.
- **Editing:** visibility, color, XYZ transform, camera target and FOV edits update
  the real R3F scene. TransformControls commit their values back to the store.
- **Framing:** director/camera views, `16:9 / 9:16 / 1:1` and thirds guides are
  visible authoring state.
- **Capture:** the WebGL canvas is cropped to the visible frame after temporarily
  hiding grid, transform controls and camera rigs. The PNG does not include DOM
  toolbar, rails, frame or guide overlays.
- **Canvas return:** one send command creates an image node plus one source edge
  in a single `canvasStore` history transaction. One undo/redo removes/restores
  both.
- **Close:** Escape first closes a compact drawer; otherwise Escape/back/close
  returns to the main canvas, reselects the source node and preserves viewport.
- **Responsive:** below `900px`, tree and Inspector become mutually exclusive
  left/right drawers over the full-screen R3F viewport.
- **Timeline shell:** a full-width bottom band remains outside the three-zone
  workspace. Its label column aligns with the object-tree rail; controls and the
  time canvas scroll internally on compact viewports.
- **Typed tracks:** current runtime values support transform and camera tracks.
  Track/keyframe selection routes object selection and the Inspector to the same
  context.
- **Scrub/playback:** ruler pointer input, previous/next navigation and playback
  sample transform/camera values deterministically. Pause freezes the scene;
  loop-off stops at duration and loop-on wraps.
- **Authoring:** manual keyframe add performs a same-time upsert. Inspector edits
  and completed TransformControls drags record at the playhead when auto-keyframe
  is enabled. Sampling itself never creates keyframes.
- **Timeline responsive behavior:** desktop uses a `196px` clone-calibrated band;
  `390x844` uses `176px`, a contracted label column and internal horizontal
  scrolling without document overflow.
- **Evidence and verification:** Batch 35 covers the R3F workspace and return;
  `docs/research/liblib-canvas-batch36-2026-08-26/` and
  `scripts/verify-liblib-batch36.py` cover the animation timeline.

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

### Group Hierarchy

- The source video group is a real React Flow parent; the failed video is its child at relative `(62,62)`.
- Dragging the video group moves the failed video by the same screen delta while the child relative position stays unchanged.
- Dragging the child changes only its relative position; the parent does not move.
- Copying a group includes descendants and remaps child `parentId`.
- Copying only a child creates a top-level copy at its absolute position plus `(40,40)`.
- Deleting a group cascades to descendants and edges touching any removed node.
- The source image group is empty and does not have `.parent`.
- See [`liblib-canvas-batch8-2026-08-25/`](./liblib-canvas-batch8-2026-08-25/) for the original DOM/xyflow evidence chain.

### Handle Drag to Connect
- **Trigger:** Mouse down on `<Handle>`, drag to another `<Handle>`
- **Effect:** Creates a connection edge. See "Edge → Connection Drag" above.
- **Snap behavior (React Flow native):** When dragging close to a valid target handle, that handle highlights (`valid` class, green) and the connection snaps to it.

## TopNavBar

### Canvas Tab Dropdown
- **Trigger:** Click "画布 2 ▾"
- **Structure:** `当前项目` and editable project name, followed by `画布`, a plus command and the canvas list. The active canvas is ordered first and has a right-side check.
- **Project metadata:** The project name is stored in `canvasStore.projectName`, separate from each canvas name; this remains in-memory prototype state.
- **Canvas actions:** Selecting, creating, renaming, copying or deleting a canvas performs the existing store action and closes the dropdown.
- **Cleanup:** Outside click and Escape close the dropdown and clear local edit/menu state.
- **Evidence and verification:** `docs/research/liblib-canvas-batch16-2026-08-25/` and `scripts/verify-liblib-batch16.py`.

### Asset Manager Context

- Opening the 240px drawer moves the workbench/storyboard controls to its right and hides the duplicate top canvas trigger.
- The drawer context row shows the current project and active canvas; clicking the canvas name closes the drawer and opens the top canvas dropdown.
- `画布` uses a one-level `parentId` tree. `资产` remains a current-canvas image/video projection.
- Sort, type filter and search operate only on local active-canvas data.
- Empty copy distinguishes no graph nodes from no media assets.
- Evidence and verification: `docs/research/liblib-canvas-batch17-2026-08-25/` and `scripts/verify-liblib-batch17.py`.

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

## AddNodePanel (9 source-shaped entries)

Opens when clicking the `+` sidebar button. Click outside to close. Clicking a node type calls `useCanvasStore.addNode(type)` which spawns a new node at a default position with default data, then closes the panel.

Node entries: text, image, video, video-clip (Beta), script-execution (NEW), shot-breakdown (SD 2.5), audio, script, material.

- `音频` creates a dedicated local `audio` node rather than a text node.
- `素材库` opens a two-item local submenu; selecting either item opens the existing MaterialLibraryPanel.
- `上传` and `从生成历史选择` show explicit local prototype status and do not create a node.

## BottomToolbar (bottom-left canvas controls)

Buttons (left to right):
- **资产管理:** Toggles the `240px` asset drawer.
- **整理画布 (`Option/Alt+Shift+F`):** Applies the source-like semantic topology and opens the keep/restore confirmation.
- **缩略图:** Toggles a `150x110px` React Flow minimap anchored above the trigger rather than at the default bottom-right. It follows the canvas when the asset drawer opens; compact viewports raise it above both bottom toolbars. Minimap-internal pan/zoom/click remain disabled pending source evidence.
- **节点连线:** Shows or hides all edges.
- **吸附:** Toggles `20x20` grid snapping; hidden in the compact middle-width range.
- **缩放百分比:** Opens the source-shaped current-percent, zoom in/out, fit-view and 50/100/800 menu. Zoom actions keep it open; Escape, outside pointerdown or another top-level overlay closes it. The menu no longer includes the unsupported grid item.

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
  - `ImageToolbar` above the node — horizontal `900.5×49` toolbar, node-centered with a `16px` screen-space offset and constant screen size
  - `ImageEditPanel` below the node — `660×274` populated prompt state, node-centered and counter-scaled by `1 / zoom`
  - Both overlays follow node drag, pan, and zoom; neither is clamped or recentered to the browser viewport
  - The lower panel gap is `16 * zoom`; the clone uses `bottom: -17px` only to compensate for its bordered node shell
- **Multi-select:** Hides every single-node toolbar/editor
- **Gesture isolation:** `nodrag nowheel nopan` keeps textarea and panel gestures from moving the node or canvas

Image prompt, reference, AutoLink and derived-node behaviors are documented in `ImageNode.spec.md` and `ImageEditPanel.spec.md`.

The five source image states use explicit panel heights rather than a generic Prompt-derived rule: `191/191/211/191/274`. In particular, `咖啡馆` has a 7-character Prompt but remains `191px`. Only nodes with current references show the “参考” top control. AutoLink is a footer icon in the clone; its local suggestion flow is retained as prototype behavior, not claimed as a fully extracted original interaction. See [`liblib-canvas-batch10-2026-08-25/`](./liblib-canvas-batch10-2026-08-25/).

## Video-Specific Behaviors

### Select VideoNode
- **Failed video:** Shows the `660×274` Seedance generation panel below the child node.
- **Ready video:** Also shows the top processing toolbar. Generator and segment reshoot use full lower editors; smart continuation first uses a separate `660x56` range selector, then creates a connected empty target whose generation panel owns the continuation Prompt.
- **Subtitle erase:** `智能去字幕` opens a `48px` compact lower bar. `框选去字幕` also overlays a normalized multi-rectangle editor with move, corner resize and local undo/redo/reset. Submit creates one connected pending target in a single graph transaction.
- **Audio split menu:** `音视频分离` opens a trigger-centered `160px` menu with `音视频分离 / 人声提取 / 背景音提取`; current feature flags hide `音效提取`. Starting a mode closes the menu and replaces icon/label/chevron with a disabled spinner + `分离中` state.
- **Audio split graph:** After the local busy timer, one graph transaction creates a mode-named audio node and a `{source}_无声` pending video. Both edges start at the source video; the silent video is positioned after the audio node and becomes the sole selection. One undo/redo removes/restores both outputs and both edges.
- **Frame capture menu:** The top `截取首帧` trigger follows `画面编辑` and opens `截取首帧 / 截取尾帧 / 截取当前帧` in a trigger-centered `160px` menu.
- **Player camera:** The `28x28` camera clicks directly to current-frame capture; hover opens the same three commands above the button. The local range playhead supplies current time in the prototype.
- **Frame capture graph:** First/last/current create an ordinary image plus a direct source edge with source-backed time/name/alt metadata. The first output is source right `+100` world units at the same Y; repeated outputs use clone vertical slots. Source remains selected, and one undo/redo removes/restores the last output and edge.
- **Frame result selection:** Clicking a captured image uses the ordinary ImageToolbar and ImageEditPanel rather than a dedicated frame editor.
- **Depth motion capture:** The separate `深度动作捕捉` command shows an independent duration-limit feedback state on the default 30-second fixture. The development-only `?duration=10` fixture opens a lower node-anchored panel while keeping the top processing toolbar visible.
- **Depth motion graph:** The panel shows the source summary, source-backed intro and local `720P / 1080P` state. Submit briefly disables with a spinner, then creates one pending reference video and one direct source edge. Repeated outputs use deterministic right-side slots, the source remains selected, and one undo/redo removes/restores the output and edge.
- **Long-video process handoff:** `超长视频` keeps the source-confirmed `30-300s` range and `300s / 14700`. `查看过程` explains that the process appears on the canvas; it no longer renders the guessed four-card process inside the editor.
- **Long-video process graph:** Submit briefly enters a disabled busy state, then one transaction creates 3 material, 3 shot, 4 candidate, 1 assembly and 1 final pending node. Source-to-shot, material-to-shot, shot-to-candidate, candidate-to-assembly and assembly-to-final edges form a dense process graph shaped by the article screenshot.
- **Long-video history:** All 12 nodes and 22 edges share one process/request metadata set and one undo step. Repeated submissions move the whole calibrated graph downward to avoid overlap; source remains selected. Node counts, coordinates and local images are clone calibration, not recovered backend rules.
- **Subject edit menu:** The source-backed `主体消除` trigger replaces the old unsupported `画面编辑` menu and opens `主体消除 / 主体修改 / 主体替换 / 智能抠像` in a trigger-centered `160px` menu. Toolbar dropdowns use `100ms` hover-open and `120ms` hover-close delays while retaining click toggle.
- **Duration guard:** On the default `30s` ready-video fixture, the first three subject actions show `视频大于15秒，暂不支持该功能` and do not mutate nodes, edges or history.
- **Smart matting panel:** `智能抠像` opens a node-centered `512x48` compact lower panel with close, label, unknown power `--` and submit/spinner states. It replaces the ordinary generation panel while active and keeps a `16px` screen-space node gap.
- **Smart matting graph:** Submit creates one `512x288` pending video plus a direct source edge in one transaction. The result records `volcano-portrait-matting`, `PICTURE_EDIT`, `WEBM`, source dimensions/duration and edge ID; source remains selected, repeated outputs use deterministic vertical slots, and one undo/redo removes/restores the output and edge. No real transparent video is claimed.
- **Picture edit modes:** On a source-compatible video, `主体消除`、`主体修改` and `主体替换` enter one shared mark editor. The editor exposes `点选 / 框选 / 画笔 / 橡皮`, a normalized mark overlay, per-mark frame time and local candidate label, plus local undo/redo/reset.
- **Picture edit validation:** Remove accepts marks up to `4`; modify accepts up to `4` and requires a non-empty description for every mark; replace accepts up to `2` and requires a replacement source for every mark. `本地上传 / 历史图库` are local prototype states and do not access files or account data.
- **Picture edit graph:** Submit shows `分析中`, then creates one pending video and one direct source edge in one graph transaction. Output metadata records mode, marks, descriptions/replacement source, source and edge ID; source remains selected and repeated outputs use deterministic right-side slots. The output body says `主体编辑 · 等待媒体资源` and does not claim real segmentation or video rendering.
- **Anchor:** The lower panel center equals the video child center, remains screen-sized through zoom, and uses a `16 * zoom` gap.
- **Parent move:** Dragging the video group selects the parent and unmounts the child panel. Re-selecting the child rebuilds the panel at the child's new absolute position.
- **Child move / pan / zoom:** Child and panel remain attached with no viewport clamping.
- **Multi-select:** Hides all single-node video overlays.
- **Verification:** `scripts/verify-liblib-batch9.py`, `scripts/verify-liblib-batch26.py` through `scripts/verify-liblib-batch33.py`, director return coverage in `scripts/verify-liblib-batch35.py`, and director timeline coverage in `scripts/verify-liblib-batch36.py`.

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
