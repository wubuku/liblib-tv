# LibTV Canvas Page Topology

> Current state of the rebuilt clone. Diagrams show actual rendered layout.

## Page Type
**Canvas Editor** — Node-based flow graph editor for video storyboarding and production.

## Layout Structure

```text
┌──────────────────────────────────────────────────────────────────┐
│ floating TopNav: [mark][canvas][workbench/storyboard] ...       │
│                                              [share][20][Agent]  │
│                                                                  │
│ main: ReactFlow workbench OR StoryboardBoard                    │
│       optional AssetManager drawer at left                      │
│       optional AgentDrawer at right                             │
│                                                                  │
│ [asset][organize][map][edges][snap][zoom]                        │
│                    [add][move][toolbox][material][character]...  │
└──────────────────────────────────────────────────────────────────┘
 lower-left canvas controls       centered primary-entry toolbar
```

## Sections (top-to-bottom of visible viewport)

### 1. Top Navigation Bar (`<TopNavBar>`)
- **Type:** Floating fixed command groups, not a full-width header band.
- **Bounds:** `left/right/top: 16px`, `height: 32px`, `z-index: 70`.
- **Agent response:** on desktop the right bound moves to `356px` while Agent is open.
- **Children (left to right):**
  - LibTV mark linking to the FrameOS demo route in the clone;
  - canvas dropdown, hidden while the asset drawer owns project/canvas context;
  - workbench/storyboard segmented icon buttons on desktop;
  - share command, local credits display (`20`) and Agent command on desktop.

### 2. Script Header (`<ScriptHeader>`, legacy/unmounted)

- `src/components/ScriptHeader.tsx` still contains an old fixed title-chip prototype, but no current route imports or mounts it.
- Its two cyan dots are decorative spans, not React Flow handles.
- It is not part of the current runtime topology and has no current verifier.
- Earlier follow-banner descriptions are historical clone notes; the current page does not mount a global `正在跟随 / 取消ESC` banner.

See [`components/ScriptHeader.spec.md`](components/ScriptHeader.spec.md) before considering any future title/follow overlay.

### 3. Primary Entry Toolbar (`<LeftSidebar>` compatibility name)

- **Type:** Fixed centered bottom toolbar, not a left sidebar.
- **Bounds:** desktop `bottom: 12px`, `height: 49px`, `z-index: 60`; mobile moves to `bottom: 52px` to leave room for canvas controls.
- **Shell:** `#262626`, `12px` radius, `8px` padding, 8px item gap.
- **Commands:** 添加节点, 移动/抓手, 工具箱, 素材库, 角色库, 历史记录, 快捷键, 教程与帮助.
- **Lifecycle:** primary panels, add-node and shortcuts participate in shared top-level overlay exclusion.

### 4. Canvas Area (React Flow)
- **Type:** Main route surface. Workbench mounts React Flow; storyboard mode mounts `StoryboardBoard` instead.
- **Background:** `#171717` (`bg-canvas` token).
- **Contents:** Nodes (script, image, video, etc.) connected by custom `DeletableEdge` paths.
- **Interaction model:** Pan + Zoom + Drag (React Flow), with `panOnScroll`, `zoomOnScroll`, `panOnDrag` enabled.
- **Viewport bounds:** controlled viewport state, `minZoom=0.1`, `maxZoom=8`, `snapGrid=[20, 20]`; desktop/compact source-derived canvases use route-owned initial viewport baselines.
- **Backgrounds:** Optional dot grid via `<Background>` reads `useUIStore.showGrid`. The store still has `toggleGrid`, but the current shell has no grid command.

### 5. Following Status Banner (historical, not mounted)

The earlier purple `正在跟随 / 取消ESC` banner is not part of the current page. The 2026-08-25 live audit also records that the old clone's always-visible purple banner was too dominant relative to the source. Re-introduction requires current source evidence and an explicit visibility/lifecycle contract.

### 6. Bottom Toolbar (`<BottomToolbar>`)
- **Type:** Fixed lower-left canvas controls, `bottom: 12px`, `height: 40px`, `z-index: 60`.
- **Asset response:** `left: 16px` normally; shifts to `left: 256px` while the desktop asset drawer is open.
- **Children:** 资产管理, 整理画布, 缩略图, 节点连线, 吸附到网格, zoom trigger/menu.
- **Responsive:** snap and zoom controls hide in the compact desktop/mobile range; the toolbar does not become the primary entry toolbar.

### 7. Director Desk (`<DirectorDesk>`)

- **Type:** Lazy-loaded fixed overlay (`inset: 0`, `z-index: 100`) opened from the
  `3D导演台` node. It covers the route without unmounting React Flow.
- **Desktop:** 48px top bar, 220px object tree, flexible full-height R3F viewport
  and 288px Inspector.
- **Viewport overlays:** centered aspect frame, optional thirds and a compact
  bottom command toolbar; these are DOM authoring helpers and are excluded from
  PNG capture.
- **Compact `<900px`:** side rails become mutually exclusive drawers; the live
  R3F viewport remains full-screen.
- **Return:** close restores the source-node selection and unchanged React Flow
  viewport; sending a capture creates a source-linked image node.
- **Detailed topology:** [`liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md`](./liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md).

## Notes

- The current clone has two separate bottom command groups: the centered primary-entry toolbar (`LeftSidebar`) and lower-left canvas controls (`BottomToolbar`).
- The handle is positioned and styled in `globals.css` (see `/* Node Handle */` block). The handle is the connection source — drag from it to create edges.
- Per-node topology/structure details live in their component specs under [`components/`](./components/). This page only describes page-level layout.
- Top-level state ownership, close paths and the boundary with node-relative surfaces live in [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](./LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md).

## Related

- [`PAGE_TOPOLOGY.md` for FrameOS route](./frameos/PAGE_TOPOLOGY.md) — different layout entirely (floating toolbar + prompt bar + breadcrumb header).
- Per-component topology: see [`components/<Name>.spec.md`](./components/).
