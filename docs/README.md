# LibTV Canvas — Project Documentation Index

This is the reverse-engineered clone of [`liblib.tv/canvas`](https://www.liblib.tv/canvas) — a node-based video-storyboarding editor built with **Next.js 16** and **React Flow**.

> Use this index as the entry point when picking up the project — every important concept, component, and decision is documented below.

---

## Quick Start

```bash
npm run dev      # localhost:3000 — the canvas editor
npm run build    # production build
npm run check    # lint + typecheck + build
```

The editor opens to `/` and renders a storyboard canvas with sample nodes (script, images, video, etc.) for the project "未命名项目" → "画布 2".

---

## Documentation Map

| Doc | Purpose |
|-----|---------|
| [`docs/research/PAGE_TOPOLOGY.md`](./research/PAGE_TOPOLOGY.md) | High-level page layout (what's on screen, where it is) |
| [`docs/research/BEHAVIORS.md`](./research/BEHAVIORS.md) | All interaction behaviors extracted from the original site |
| [`docs/research/COMPONENT_INVENTORY.md`](./research/COMPONENT_INVENTORY.md) | Catalog of every UI component built |
| [`docs/research/DESIGN_TOKENS.md`](./research/DESIGN_TOKENS.md) | Colors, typography, spacing — the design system |
| [`docs/research/components/`](./research/components/) | Per-component specs (interaction model, computed styles, assets) |
| [`docs/design-references/`](./design-references/) | Screenshots and asset files from the original site |
| [`docs/research/INSPECTION_GUIDE.md`](./research/INSPECTION_GUIDE.md) | Original guide for how to extract info from the live site |

---

## Tech Stack

- **Framework:** Next.js 16 (App Router, React 19, TypeScript strict)
- **UI:** Tailwind CSS v4 with `@theme inline` design tokens
- **State:** [Zustand](https://github.com/pmndrs/zustand) (`canvasStore`, `uiStore`)
- **Canvas:** [React Flow (`@xyflow/react`)](https://reactflow.dev/) — node-based flow editor
- **Icons:** Inline SVG (no icon library)
- **Tooltips:** [`@base-ui/react`](https://base-ui.com/) tooltip primitive

---

## Source Tree (annotated)

```
src/
├── app/
│   ├── page.tsx                  # Page assembly — top nav, sidebars, canvas, bottom toolbar
│   ├── globals.css               # Design tokens + React Flow styling (handles, edges, controls)
│   └── layout.tsx                # Imports globals.css + metadata
├── components/
│   ├── TopNavBar.tsx             # Top navigation: logo, project name, canvas dropdown, VIP, FrameOS link
│   ├── BottomToolbar.tsx         # Centered floating bottom toolbar with zoom %, arrange, etc.
│   ├── LeftSidebar.tsx           # Left tool palette (add node, toolbox, materials, etc.)
│   ├── ScriptHeader.tsx          # "正在跟随" status banner + compact script title node
│   ├── PlusIndicator.tsx         # No-op stub (kept for backward compat — handles render directly)
│   ├── AddNodePanel.tsx          # Node-type selector that opens from LeftSidebar "+" button
│   ├── CanvasTabDropdown.tsx     # Multi-canvas switcher with rename/duplicate/delete
│   ├── ImageToolbar.tsx          # Vertical icon toolbar attached to selected image node
│   ├── ImageEditPanel.tsx        # Bottom panel for image style/mark editing
│   ├── CameraConfigDialog.tsx    # Camera/lens/focal-length/aperture dialog (9 cameras, 10 lenses)
│   ├── CameraMovementDialog.tsx  # Camera movement dialog (10 types, speed, duration, amplitude)
│   ├── ToolboxPanel.tsx          # Preset animation templates
│   ├── MaterialLibraryPanel.tsx  # Material library side panel
│   ├── CharacterLibraryPanel.tsx # Character library side panel
│   ├── HistoryPanel.tsx          # History side panel
│   ├── KeyboardShortcutsDialog.tsx # Keyboard shortcuts modal
│   ├── CustomHandle.tsx          # Legacy custom handle (currently unused)
│   └── nodes/                    # All node types — see "Node System" below
└── store/
    ├── canvasStore.ts            # Nodes, edges, canvii, selection, viewport
    └── uiStore.ts                # Panel visibility, grid/minimap toggles, zoom level
```

---

## Node System

Six React Flow node types are implemented. Each has a corresponding spec in [`docs/research/components/`](./research/components/).

| Node | Type ID | Spec |
|------|---------|------|
| Script node (`剧本`) | `script` | [`ScriptNode.spec.md`](./research/components/ScriptNode.spec.md) |
| Image node (图片) | `image` | [`ImageNode.spec.md`](./research/components/ImageNode.spec.md) |
| Text node (文本) | `text` | (see COMPONENT_INVENTORY) |
| Video node (分镜视频) | `video` | (see COMPONENT_INVENTORY) |
| Script execution node | `script-execution` | (see COMPONENT_INVENTORY) |
| Storyboard group (分镜图) | `storyboard-group` | (see COMPONENT_INVENTORY) |

### Edge: `DeletableEdge`

Custom edge type registered as `default` in `page.tsx`. See [`DeletableEdge.tsx`](../src/components/nodes/DeletableEdge.tsx).

---

## Key Design Decisions

### 1. Connection handling — React Flow's `<Handle>` IS the "+" icon

Initially we built a separate decorative "+" indicator (a `PlusIndicator.tsx` component) that floated near the node border. This broke the actual interaction: the user could see the "+" icon but couldn't drag from it to create connections. **Fix**: removed all decorative overlays. The handle is now the only "+" entry point — when the node is hovered, the handle reveals itself at the node border with a "+" rendered via CSS `::before` pseudo-element. Drag from the handle to create connections. The handle accepts all of React Flow's native behaviors: hover snap, click-to-connect, magnet to valid targets, automatic visualization of the connection line while dragging.

See [`globals.css` `/* Node Handle */` block](../src/app/globals.css) for the full handle styling.

### 2. Edge hover effect — analysis-driven (not guessed)

We extracted the original site's edge hover implementation by walking the live DOM through Playwright. The original site renders **multiple light segments** with a flowing gradient + Gaussian-blur filter, not a simple stroke color change. We replicated this exactly:

- 3 segments per edge, traveling along the path with `requestAnimationFrame` → moved to CSS-injected `@keyframes` (better performance, GPU-accelerated).
- Each segment uses `linearGradient` (`rgba(180,220,255,0)` → solid → `rgba(180,220,255,0)`) + SVG `<filter>` with `feGaussianBlur` + `feFlood` + `feComposite` + `feMerge` for the glow effect.
- 3 segments staggered by `animation-delay` (0, -0.53s, -1.06s) create the continuous-flow appearance.
- `pathLength: 100` normalization + `strokeDasharray: "20 80"` → visible segment is 20% of path.

### 3. CSS-in-JS keyframe injection for per-edge animations

Each active edge injects its own `@keyframes` block into `document.head`. Why? Because each edge has a unique ID and needs its own `animationName`, and `@keyframes` rules need to be in the global stylesheet (CSS `animation` property can't reference JS-defined animations otherwise). Cleanup on unmount removes the style tag.

### 4. Two-camera configuration pattern

The `ImageEditPanel` and `VideoNode` both expose a "摄像机" (camera) and "运镜" (camera movement) dialog. Both use plain React `useState` for local UI state and dispatch a custom event / callback with the chosen config. The pattern is **open the dialog → user picks → on `onApply` callback, write config to `node.data.cameraMovement`**. No backend persistence — this is a UI scaffold.

### 5. Pixel-perfect matching via DOM extraction, not visual guessing

The instruction in the original `clone-website` skill (`@AGENTS.md`) emphasizes "don't guess". We honor this by:
- Querying the live original site's DOM through Playwright to get exact bounding boxes, classes, computed styles.
- Capturing screenshots of every state (hover, selected, drag in progress) for visual reference.
- Saving raw computed CSS and HTML into spec files rather than reconstructed summaries.

---

## Common Tasks

### Add a new node type
1. Create `src/components/nodes/MyNode.tsx` with the React Flow `NodeProps` interface.
2. Register the type in the `nodeTypes` map in [`src/app/page.tsx`](../src/app/page.tsx).
3. Add the type to the `nodeTypes` array in [`src/components/AddNodePanel.tsx`](../src/components/AddNodePanel.tsx).
4. (Optional) Add a spec under `docs/research/components/MyNode.spec.md`.

### Tweak the handle visual
Edit the `/* Node Handle */` block in [`src/app/globals.css`](../src/app/globals.css). The handle uses `::before` to render the "+" glyph.

### Tweak the edge hover effect
Edit [`src/components/nodes/DeletableEdge.tsx`](../src/components/nodes/DeletableEdge.tsx) and the `Edge Edge Styling` block in `globals.css`.

---

## Known Limitations & Future Work

- **No backend**: all state is in-memory (Zustand). Refresh = data lost.
- **Camera/Camera-movement dialogs**: UI only — selection is logged but doesn't actually generate anything.
- **ImageEditPanel**: prompt + camera + model selector is layout-only, no API integration.
- **ToolboxPanel / MaterialLibraryPanel / CharacterLibraryPanel / HistoryPanel**: empty placeholders ready for content.
- **No zoom/pan gesture on canvas dots**: the React Flow default works; we tuned `minZoom=0.1, maxZoom=2`.

---

## License

UNLICENSED — internal development scaffold. Not for redistribution.
