# LibTV Canvas Clone — Documentation

This is a reverse-engineered clone of [`liblib.tv/canvas`](https://www.liblib.tv/canvas) — a node-based video-storyboarding editor — plus a parallel [`frameos.cn`](https://www.frameos.cn) canvas route. Built with **Next.js 16**, **React Flow**, and **Zustand** on the `clone-website` template scaffold.

> **Current architecture and implementation status:** read [`BIG_PICTURE.md`](BIG_PICTURE.md). Research docs preserve original-site observations and earlier implementation stages, so they can be stale relative to `src/`.
>
> **Pick your starting point based on what you're doing:**
>
> | You want to … | Go to |
> |---|---|
> | Run the app | [§ Quick Start](#quick-start) |
> | Understand the high-level picture | [`BIG_PICTURE.md`](BIG_PICTURE.md) |
> | Find a specific component | [§ Source Tree](#source-tree-annotated) or [`docs/research/COMPONENT_INVENTORY.md`](research/COMPONENT_INVENTORY.md) |
> | Understand a specific interaction | [§ Behaviors](research/BEHAVIORS.md) or [§ Per-component specs](research/components/) |
> | Understand a design decision (e.g. "why does the handle look like a +?") | [§ Key Design Decisions](#key-design-decisions) |
> | Read the Seedance 2.5 background, research and implementation history | [`research/liblib-seedance-2.5-2026-08-25/`](research/liblib-seedance-2.5-2026-08-25/) |
> | Read the multi-selection and grouping batch handoff | [`research/liblib-canvas-batch4-2026-08-25/`](research/liblib-canvas-batch4-2026-08-25/) |
> | Look at the actual implementation of a node | [`src/components/nodes/`](../../src/components/nodes) |
> | Look at the FrameOS canvas (separate route) | [§ FrameOS Canvas](#frameos-canvas) |

---

## Quick Start

```bash
npm install
npm run dev      # localhost:3000 — main canvas editor (liblib-tv clone)
# FrameOS canvas lives at:  http://localhost:3000/frameos/canvas/demo
npm run build    # production build
npm run check    # lint + typecheck + build
```

On first load the LibTV canvas renders the current reverse-engineered project baseline: 10 nodes, 11 edges, and responsive 53%/28% viewports for project "未命名项目" → "画布 2".

---

## What This Is

- **`/` (liblib-tv clone)** — A pixel-perfect recreation of liblib.tv's canvas editor: nodes, edges, hover effects, dialogs, sidebars, bottom toolbar.
- **`/frameos/*`** — A separate canvas route cloned from `frameos.cn`. Different layout (floating toolbar, prompt bar at bottom, breadcrumb header, blue primary color, deeper `#0D0D0D` background).

Both routes share:
- React Flow (`@xyflow/react`) node/edge primitives
- Zustand store pattern (separate stores per route: `canvasStore`, `frameosStore`)
- The reverse-engineering workflow and local asset/document structure

Their current edge renderers are route-specific: LibTV uses `DeletableEdge`; FrameOS uses `FrameosEdge`.

---

## Documentation Map

### Hub
- [`AGENTS.md`](../AGENTS.md) — agent red-lines (read first if you're an AI agent)
- [`BIG_PICTURE.md`](BIG_PICTURE.md) — current architecture, route boundaries, state flow, research workflow, and prototype limits
- [`research/liblib-live-2026-08-25/README.md`](research/liblib-live-2026-08-25/README.md) — current live-site evidence, gap audit, value ranking, and implementation scope
- [`research/liblib-canvas-batch3-2026-08-25/README.md`](research/liblib-canvas-batch3-2026-08-25/README.md) — command-history batch plan, evidence corrections, implementation record, and handoff notes
- [`research/liblib-seedance-2.5-2026-08-25/BACKGROUND.md`](research/liblib-seedance-2.5-2026-08-25/BACKGROUND.md) — durable background knowledge extracted from the external LibTV Seedance 2.5 research document
- [`.claude/skills/clone-website/SKILL.md`](../.claude/skills/clone-website/SKILL.md) — source-of-truth workflow for browser extraction, specs, parallel building, and visual QA
- [`docs/research/INSPECTION_GUIDE.md`](research/INSPECTION_GUIDE.md) — how to extract info from a live target site

### Whole-app behavior & layout
| Doc | Purpose | When to read |
|-----|---------|--------------|
| [`research/PAGE_TOPOLOGY.md`](research/PAGE_TOPOLOGY.md) | ASCII diagram of every section on screen + z-index map | You need to know "where is X positioned?" |
| [`research/BEHAVIORS.md`](research/BEHAVIORS.md) | Every interaction (hover, click, drag, keyboard, dialog apply) | You need to know "what happens when…?" |
| [`research/COMPONENT_INVENTORY.md`](research/COMPONENT_INVENTORY.md) | Catalog of every component with file path + one-line purpose | You need to know "is there already a component for X?" |
| [`research/DESIGN_TOKENS.md`](research/DESIGN_TOKENS.md) | Colors, typography, spacing, shadows, animations, z-index | You need to pick a color/spacing/font value |

### Per-component specs
[`research/components/`](research/components/) — one spec per component, each with DOM structure, computed styles, interaction model, and file references. Open the one that matches the file you're touching.

### Design references
[`design-references/`](design-references/) — screenshots from the original sites (both liblib-tv and frameos), including a side-by-side comparison. Useful when you need to verify a visual decision.

### FrameOS-specific docs
- [`research/frameos/PAGE_TOPOLOGY.md`](research/frameos/PAGE_TOPOLOGY.md) — FrameOS canvas layout
- [`research/frameos/BEHAVIORS.md`](research/frameos/BEHAVIORS.md) — FrameOS interactions
- [`research/frameos/DESIGN_TOKENS.md`](research/frameos/DESIGN_TOKENS.md) — FrameOS palette (blue primary, deeper bg)
- [`research/frameos/*.json`](research/frameos/) — raw extracted data (assets, buttons, components, nodes, panel-styles, region-styles, svgs)

---

## Source Tree (annotated)

```
src/
├── app/
│   ├── page.tsx                  # Main canvas editor page (liblib-tv clone)
│   ├── layout.tsx                # Root layout + metadata
│   ├── globals.css               # Design tokens + React Flow styling (handles, edges)
│   └── frameos/                  # FrameOS canvas route — see "FrameOS Canvas" below
├── components/
│   ├── TopNavBar.tsx             # Floating nav: logo/canvas, workbench/storyboard, share, credits, Agent
│   ├── LeftSidebar.tsx           # Compatibility name: the centered 8-command primary bottom toolbar
│   ├── BottomToolbar.tsx         # Bottom-left canvas controls: assets, organize, minimap, edges, snap, zoom
│   ├── AssetManagerPanel.tsx     # 240px node/asset drawer
│   ├── AgentDrawer.tsx           # 340px Agent drawer and local prompt prototype
│   ├── StoryboardBoard.tsx       # Storyboard-mode column view
│   ├── AddNodePanel.tsx          # Current one-column 9-entry node/resource selector
│   ├── CanvasTabDropdown.tsx     # Multi-canvas switcher (rename/duplicate/delete)
│   ├── ImageToolbar.tsx          # NodeToolbar-anchored horizontal toolbar for a selected image
│   ├── ImageEditPanel.tsx        # Node-anchored, inverse-zoom 660px image prompt editor; 3 source-observed heights
│   ├── VideoGenerationPanel.tsx  # Seedance model/mode/parameter prompt editor
│   ├── VideoProcessingToolbar.tsx # Ready-video top processing toolbar
│   ├── SegmentReshootPanel.tsx   # Segment reshoot / smart continuation editor
│   ├── ShotBreakdownResultsPanel.tsx # Local frame-analysis media results
│   ├── CameraConfigDialog.tsx    # 9 cameras × 10 lenses × 7 focal lengths × 3 apertures
│   ├── CameraMovementDialog.tsx  # 10 movement types + speed + duration + amplitude
│   ├── ToolboxPanel.tsx          # 25-preset anchored toolbox cloned from live evidence
│   ├── MaterialLibraryPanel.tsx  # Two-command anchored material menu
│   ├── CharacterLibraryPanel.tsx # Character detail + asset carousel modal
│   ├── HistoryPanel.tsx          # Filterable local history asset modal
│   ├── KeyboardShortcutsDialog.tsx # Four-column anchored shortcuts panel
│   ├── PlusIndicator.tsx         # NO-OP stub — see "Key Design Decisions" §1
│   ├── CustomHandle.tsx          # Legacy handle prototype (unused)
│   ├── nodes/                    # All node types — see "Node System" below
│   └── frameos/                  # FrameOS-specific components — see "FrameOS Canvas"
├── store/
│   ├── canvasStore.ts            # Nodes, edges, canvii, selection, viewport (liblib-tv)
│   ├── uiStore.ts                # Panel visibility, grid/minimap toggles, zoom level
│   └── frameosStore.ts           # FrameOS-specific store
├── lib/utils.ts                  # cn() utility (shadcn)
└── types/                        # TypeScript interfaces
```

---

## Node System (liblib-tv route)

Eight React Flow node types are implemented. Each has its own spec.

| Type ID | File | Spec |
|---------|------|------|
| `script` (剧本) | [`src/components/nodes/ScriptNode.tsx`](../src/components/nodes/ScriptNode.tsx) | [`ScriptNode.spec.md`](research/components/ScriptNode.spec.md) |
| `image` (图片) | [`src/components/nodes/ImageNode.tsx`](../src/components/nodes/ImageNode.tsx) | [`ImageNode.spec.md`](research/components/ImageNode.spec.md) |
| `text` (文本) | [`src/components/nodes/TextNode.tsx`](../src/components/nodes/TextNode.tsx) | [`TextNode.spec.md`](research/components/TextNode.spec.md) |
| `video` (分镜视频) | [`src/components/nodes/VideoNode.tsx`](../src/components/nodes/VideoNode.tsx) | [`VideoNode.spec.md`](research/components/VideoNode.spec.md) |
| `script-execution` (剧本执行) | [`src/components/nodes/ScriptExecutionNode.tsx`](../src/components/nodes/ScriptExecutionNode.tsx) | [`ScriptExecutionNode.spec.md`](research/components/ScriptExecutionNode.spec.md) |
| `storyboard-group` (分镜图组合) | [`src/components/nodes/StoryboardGroupNode.tsx`](../src/components/nodes/StoryboardGroupNode.tsx) | [`StoryboardGroupNode.spec.md`](research/components/StoryboardGroupNode.spec.md) |
| `shot-breakdown` (逐帧拉片) | [`src/components/nodes/ShotBreakdownNode.tsx`](../src/components/nodes/ShotBreakdownNode.tsx) | [`ShotBreakdownNode.spec.md`](research/components/ShotBreakdownNode.spec.md) |
| `video-clip` (智能剪辑) | [`src/components/nodes/VideoClipNode.tsx`](../src/components/nodes/VideoClipNode.tsx) | [`VideoClipNode.spec.md`](research/components/VideoClipNode.spec.md) |

### Edge: `DeletableEdge`

Custom edge type registered as `default` in `page.tsx`. See [`DeletableEdge.tsx`](../src/components/nodes/DeletableEdge.tsx) and [`DeletableEdge.spec.md`](research/components/DeletableEdge.spec.md) — this is one of the most intricate components because of the per-edge CSS-in-JS keyframe injection.

---

## FrameOS Canvas

A separate canvas route cloned from `frameos.cn`. Lives under `src/app/frameos/` and `src/components/frameos/`.

| Element | File | Notes |
|---------|------|-------|
| Route | [`src/app/frameos/page.tsx`](../src/app/frameos/page.tsx), [`src/app/frameos/canvas/[id]/page.tsx`](../src/app/frameos/canvas/[id]/page.tsx) | `[id]` is the demo canvas ID; root `/frameos` redirects here |
| Layout | [`src/app/frameos/layout.tsx`](../src/app/frameos/layout.tsx) | Inherits globals but adds frameos-specific wrapper |
| AppHeader | [`src/components/frameos/FrameosAppHeader.tsx`](../src/components/frameos/FrameosAppHeader.tsx) | "帧界 FrameOS" logo + 撤销/重做 + 下载桌面端 + 金币/积分 counters |
| ToolRail | [`src/components/frameos/FrameosToolRail.tsx`](../src/components/frameos/FrameosToolRail.tsx) | Left floating tool rail: 添加节点 (含节点类型菜单) / 素材库 / 上传 / 帮助 |
| MapDock | [`src/components/frameos/FrameosMapDock.tsx`](../src/components/frameos/FrameosMapDock.tsx) | Bottom-left minimap + zoom + 整理方式菜单（横向/纵向/网格） |
| Breadcrumb | [`src/components/frameos/FrameosBreadcrumb.tsx`](../src/components/frameos/FrameosBreadcrumb.tsx) | Top-left "默认作品 / 咖啡馆对峙 / 画布 1"，每级支持下拉 |
| NodeFloatingToolbar | [`src/components/frameos/FrameosNodeFloatingToolbar.tsx`](../src/components/frameos/FrameosNodeFloatingToolbar.tsx) | 选中节点上方浮动工具条（下载/收藏/超清/720/改图/宫格切分），**跟随节点 + 画布缩放**（57px above） |
| PromptEditor | [`src/components/frameos/FrameosPromptEditor.tsx`](../src/components/frameos/FrameosPromptEditor.tsx) | 选中节点时显示的 AI prompt 面板；当前固定在视口右下，含节点缩略图 + 模型/1K/16:9 下拉 |
| NodeEditPanel | [`src/components/frameos/FrameosNodeEditPanel.tsx`](../src/components/frameos/FrameosNodeEditPanel.tsx) | **仅调试模式可见**（默认隐藏）— 当前无可见开关，可通过 `window.__frameos_store` 触发 |
| HelpPanel | [`src/components/frameos/FrameosHelpPanel.tsx`](../src/components/frameos/FrameosHelpPanel.tsx) | 快捷键 + 操作指南弹层（按 `?` 触发） |
| SidePanel | [`src/components/frameos/FrameosSidePanel.tsx`](../src/components/frameos/FrameosSidePanel.tsx) | 左侧展开菜单（汉堡按钮触发）— 项目列表 / 场景 / 画布 |
| MaterialLibrary | [`src/components/frameos/FrameosMaterialLibrary.tsx`](../src/components/frameos/FrameosMaterialLibrary.tsx) | 右侧抽屉：素材库（图片/视频筛选） |
| ContextMenu | [`src/components/frameos/FrameosContextMenu.tsx`](../src/components/frameos/FrameosContextMenu.tsx) | 全局右键菜单（节点 / 画布空白处） |
| Toast | [`src/components/frameos/FrameosToast.tsx`](../src/components/frameos/FrameosToast.tsx) | 全局通知（撤销/复制/删除 等） |
| ConfirmDialog | [`src/components/frameos/FrameosConfirmDialog.tsx`](../src/components/frameos/FrameosConfirmDialog.tsx) | 删除节点/边的确认弹窗 |
| GenerationOverlay | [`src/components/frameos/FrameosGenerationOverlay.tsx`](../src/components/frameos/FrameosGenerationOverlay.tsx) | 全屏生成中遮罩 |
| AlignmentGuides | [`src/components/frameos/FrameosAlignmentGuides.tsx`](../src/components/frameos/FrameosAlignmentGuides.tsx) | 节点拖动时的对齐辅助线 |
| Nodes | [`src/components/frameos/nodes/`](../src/components/frameos/nodes/) | `FrameosTextNode`、`FrameosImageNode`、`FrameosVideoNode`、`FrameosNodeShell` |
| CSS | [`src/app/frameos-canvas.css`](../src/app/frameos-canvas.css) | 动画 keyframes + 拖拽视觉 + handle 样式 |
| Store | [`src/store/frameosStore.ts`](../src/store/frameosStore.ts) | 含 history stack (undo/redo)、selectedNodeId、isPromptFullscreen、isDebugMode 等 |
| Types | [`src/types/frameos.ts`](../src/types/frameos.ts) | FrameosNode / FrameosNodeData |
| Icons | [`src/components/frameos/icons.tsx`](../src/components/frameos/icons.tsx) | 18+ 内联 SVG（替代 Remix Icon） |

### FrameOS 关键 UX 行为

- **节点选中 → 出现 floating-toolbar (顶部 57px above) + 右下 PromptEditor + 蓝边 handle**
- **节点拖动** → floating-toolbar 通过节点 DOM 的视口坐标持续跟随；PromptEditor 保持固定
- **添加节点菜单**（左侧蓝色 + 按钮）→ 弹出 文本/图片/视频/角色/场景/音频/风格/批量 类型选择
- **整理方式菜单**（左下整理按钮的下拉）→ 3 种整理模式 + 实际重排节点
- **Prompt 全屏按钮** → 当前为 mock alert，尚未实现全屏编辑
- **右键菜单**：节点上 `复制 / 创建副本 / 删除`；画布空白处 `添加文本/图片/视频节点 / 适应画布`
- **键盘快捷键**：`Esc`（多级退出）/ `Delete` / `Backspace` / `Cmd+Z` / `Cmd+Shift+Z` / `Cmd+D` / `Cmd+C` / `Cmd+X` / `Cmd+S` / `方向键（移动节点，Shift=10px）` / `Tab（切换节点）` / `M（minimap）` / `?` / `+` / `-` / `0`

For FrameOS-specific topology / behaviors / tokens, see [`research/frameos/`](research/frameos/).

---

## Key Design Decisions

These are non-obvious decisions with reasons. If you're about to "fix" something that looks wrong, check here first — there's often a reason.

### 1. Connection handling — `<Handle>` IS the "+" icon

Initially we built a separate decorative "+" indicator that floated near the node border. This broke the actual interaction: the user could see the "+" but couldn't drag from it to create connections. **Fix**: removed all decorative overlays. The handle is the only "+" entry point — when the node is hovered, the handle reveals itself at the node border with a "+" rendered via CSS `::before` pseudo-element. Drag from the handle to create connections. The handle accepts all of React Flow's native behaviors: hover snap, click-to-connect, magnet to valid targets, automatic visualization of the connection line while dragging.

The handle styling lives in `src/app/globals.css` `/* Node Handle */`. See also `PlusIndicator.tsx` (a no-op stub kept for backward-compat — do not re-introduce its decorations).

### 2. Edge hover effect — analysis-driven (not guessed)

We extracted the original site's edge hover implementation by walking the live DOM through Playwright. The original site renders **multiple light segments** with a flowing gradient + Gaussian-blur filter, not a simple stroke color change. We replicated this exactly:

- 3 segments per edge, traveling along the path with CSS-injected `@keyframes` (GPU-accelerated; earlier `requestAnimationFrame` prototype was dropped for perf).
- Each segment uses `linearGradient` (`rgba(180,220,255,0)` → solid → `rgba(180,220,255,0)`) + SVG `<filter>` with `feGaussianBlur` + `feFlood` + `feComposite` + `feMerge` for the glow.
- 3 segments staggered by `animation-delay` (0, -0.53s, -1.06s) create the continuous-flow appearance.
- `pathLength: 100` normalization + `strokeDasharray: "20 80"` → visible segment is 20% of path.

If you change this without re-extracting from the live site, it will regress.

### 3. CSS-in-JS keyframe injection for per-edge animations

Each active edge injects its own `@keyframes` block into `document.head`. Why? Because each edge has a unique ID and needs its own `animationName`, and `@keyframes` rules need to be in the global stylesheet (CSS `animation` property can't reference JS-defined animations otherwise). Cleanup on unmount removes the style tag.

### 4. Two-camera configuration pattern (UI scaffold)

The `ImageEditPanel` and `VideoNode` both expose a "摄像机" (camera) and "运镜" (camera movement) dialog. Both use plain React `useState` for local UI state and dispatch a custom event / callback with the chosen config. The pattern is **open the dialog → user picks → on `onApply` callback, write config to `node.data.cameraMovement`**. No backend persistence — this is a UI scaffold. See [`CameraConfigDialog.spec.md`](research/components/CameraConfigDialog.spec.md) and [`CameraMovementDialog.spec.md`](research/components/CameraMovementDialog.spec.md).

### 5. Pixel-perfect matching via DOM extraction, not visual guessing

The instruction in the original `clone-website` skill (`@AGENTS.md`) emphasizes "don't guess". We honor this by:
- Querying the live original site's DOM through Playwright to get exact bounding boxes, classes, computed styles.
- Capturing screenshots of every state (hover, selected, drag in progress) for visual reference.
- Saving raw computed CSS and HTML into spec files rather than reconstructed summaries.

### 6. Two routes, two stores

FrameOS and liblib-tv are intentionally separate routes with separate Zustand stores (`canvasStore`, `frameosStore`) rather than one shared store with a "mode" flag. Reason: their data shapes diverge (FrameOS has breadcrumb history, prompt bar, etc.) and trying to unify them forces awkward unions. If you're adding a feature that should exist on both routes, copy the relevant logic rather than abstracting prematurely.

---

## Common Tasks

### Add a new node type (liblib-tv)
1. Create `src/components/nodes/MyNode.tsx` with the React Flow `NodeProps` interface.
2. Register the type in the `nodeTypes` map in [`src/app/page.tsx`](../src/app/page.tsx).
3. Add the type to the `nodeTypes` array in [`src/components/AddNodePanel.tsx`](../src/components/AddNodePanel.tsx).
4. (Optional but encouraged) Add a spec under `docs/research/components/MyNode.spec.md`.

### Tweak the handle visual
Edit the `/* Node Handle */` block in [`src/app/globals.css`](../src/app/globals.css). The handle uses `::before` to render the "+" glyph.

### Tweak the edge hover effect
Edit [`src/components/nodes/DeletableEdge.tsx`](../src/components/nodes/DeletableEdge.tsx) and the `Edge Styling` block in `globals.css`. Re-extract from the live site first if you're trying to match something subtle.

### Add a new camera / camera-movement dimension
The 9-camera × 10-lens × 7-focal-length × 3-aperture matrix in `CameraConfigDialog.tsx` and the 10-movement × 5-speed × 2-slider matrix in `CameraMovementDialog.tsx` are simple typed arrays at the top of each file. Edit them in place; the dialogs render directly from the arrays.

### Document a new component
Create `docs/research/components/MyComponent.spec.md` matching the structure of an existing spec (Overview → DOM Structure → Computed Styles → States & Behaviors → Files Referenced). Update [`docs/research/COMPONENT_INVENTORY.md`](research/COMPONENT_INVENTORY.md).

---

## Known Limitations & Future Work

### Both routes
- **No backend**: all state is in-memory (Zustand). Refresh = data lost.
- **No real file upload / API integration**: prompts and replace-content buttons are wired to trigger `<input type="file">` but no upload backend.
- **No mention system**: `@` reference in PromptBar is placeholder text only.

### liblib-tv route (`/`)
- **Camera/Camera-movement dialogs**: UI only — selection is logged but doesn't generate anything.
- **ImageEditPanel**: prompt + camera + model selector is layout-only, no API integration.
- **ToolboxPanel / MaterialLibraryPanel / CharacterLibraryPanel / HistoryPanel**: evidence-backed local prototypes with source-derived geometry and assets; account data and backend commands remain mocked.
- **Zoom gesture on canvas dots**: the React Flow default works; we tuned `minZoom=0.1, maxZoom=2`.

### FrameOS route (`/frameos/*`)
- **NodeEditPanel is debug-only**. The original `frameos.cn` does NOT have it. Current UI has no visible DEBUG toggle; use `window.__frameos_store.getState().toggleDebugMode()` when developing.
- **Mock data only**: 7 demo nodes (2 text + 3 video + 2 image) with real downloaded images. No persistent storage.
- **Model / size / ratio dropdowns**: pickable；生成按钮触发 30 秒前端 generation mock。
- **"下载桌面端" / "金币 积分"**: mock alerts. "添加节点" and "帮助" are wired to frontend state.
- **Video playback**: tries to use the actual mp4 URL derived from the cover image URL; falls back to the cover image on error.
- **Prompt 全屏模式**: 当前未实现；提交只启动前端计时 mock，没有后端。

---

## License

UNLICENSED — internal development scaffold. Not for redistribution.
