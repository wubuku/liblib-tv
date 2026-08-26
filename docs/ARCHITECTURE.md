# Architecture

## System Context

本项目是两个独立的前端画布原型：

- **LibTV route `/`**：从 `liblib.tv/canvas` 反向工程得到的节点式视频故事板编辑器。
- **FrameOS route `/frameos/*`**：从 `frameos.cn` 反向工程得到的 AI Prompt + 画布编辑器。

两条路线共享 React、Next.js、React Flow、TypeScript、Tailwind 和研究方法，但不共享业务 store、节点数据语义或页面编排。

## System Overview

```mermaid
graph TD
    Browser[Browser]
    Browser --> LibRoute[/]
    Browser --> FrameRoute[/frameos/canvas/id]

    LibRoute --> LibPage[LibTV page controller]
    LibPage --> LibFlow[React Flow graph]
    LibPage --> CanvasStore[canvasStore]
    LibPage --> UIStore[uiStore]
    LibFlow --> LibNodes[LibTV node renderers]
    LibFlow --> LibOverlays[toolbars panels dialogs]

    FrameRoute --> FramePage[FrameOS page controller]
    FramePage --> FrameFlow[React Flow graph]
    FramePage --> FrameStore[frameosStore]
    FrameFlow --> FrameNodes[FrameOS node renderers]
    FrameFlow --> FrameOverlays[floating toolbar prompt menus]

    Research[docs/research + screenshots] -. evidence .-> LibPage
    Research -. evidence .-> FramePage
```

## Route Structure

| Route | Controller | Store | Registered node renderers | Main boundary |
|---|---|---|---|---|
| `/` | `src/app/page.tsx` | `canvasStore` + `uiStore` | 10 LibTV types | in-memory LibTV prototype |
| `/frameos` | `src/app/frameos/page.tsx` | `frameosStore` | redirect entry | route entry only |
| `/frameos/canvas/[id]` | `src/app/frameos/canvas/[id]/page.tsx` | `frameosStore` | text/image/video | `[id]` is currently a demo placeholder |

## Module Responsibilities

| Module | Path | Responsibility |
|---|---|---|
| Route orchestration | `src/app/` | React Flow setup, route layout, keyboard and overlay composition |
| UI components | `src/components/` | panels, toolbars, dialogs and route-specific visual behavior |
| LibTV nodes | `src/components/nodes/` | script, image, text, video, execution, group, breakdown input/result, clip and audio |
| FrameOS nodes | `src/components/frameos/nodes/` | shared shell plus text/image/video renderers |
| State | `src/store/` | graph, selection, viewport, history and UI mock state; LibTV top-level overlay lifecycle is in `uiStore` |
| Pure helpers | `src/lib/` | organize topology and class-name utilities |
| Types | `src/types/` | route-specific data contracts |
| Evidence | `docs/research/` | source observations, specs, raw JSON and batch history |

## Data Flow

### LibTV

```text
React Flow event
  -> page.tsx handler
  -> canvasStore action
  -> active canvas nodes/edges/viewport
  -> controlled React Flow render
  -> selected-node overlays and UI store panels
```

`canvasStore` owns graph data and per-canvas in-memory history. `uiStore` owns global UI modes, page-level overlay visibility and LibTV's mutually exclusive `activePrimaryPanel`. Short-lived menu state may remain local to a component.

Derived media workflows use store-owned graph transactions. Continuation and subtitle
erase create one target + one source edge; audio split creates audio + silent-video
targets and two direct source edges; video frame capture creates one image + one direct
source edge; smart matting creates one pending video + one direct source edge. Frame
capture and smart matting preserve source selection for repeated commands. Each
workflow records one pre-change snapshot so one undo/redo operates on the whole result
set. Picture edit uses a shared node-local mark editor for three subject modes, then
creates one pending video + one direct source edge with request-shaped mark metadata.

### FrameOS

```text
React Flow event
  -> frameos page controller
  -> frameosStore action
  -> nodes/edges/history/selection
  -> React Flow render
  -> fixed/floating overlays
```

FrameOS re-applies `selectedNodeId` after `applyNodeChanges`, because xyflow v12 resets selected flags during change application.

## Node And Overlay Patterns

### LibTV

- Nodes are separate renderers and do not share a universal NodeShell.
- `<Handle>` is the actual connection affordance and is styled as the visible `+`.
- Image and video selected overlays are node-anchored; the image toolbar is a React Flow `NodeToolbar`, while the editor/generation panel is mounted inside the node and inverse-scaled.
- Video groups use real `parentId` hierarchy. The failed video child has relative position `(62,62)`.
- Selected single-node overlays may naturally clip at the canvas viewport edge; they are not recentered to the browser window.

### FrameOS

- `FrameosNodeShell` owns title, handles, selected state and resize affordance.
- `FrameosNodeFloatingToolbar` follows the selected node.
- `FrameosPromptEditor` is currently a fixed viewport overlay in the prototype.
- `FrameosNodeEditPanel` is a DEBUG-only developer convenience, not source-site behavior.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Store boundary | two independent stores | route data shapes and histories differ |
| Node boundary | route-specific renderers | prevents LibTV/FrameOS semantic unions |
| Connection affordance | native `<Handle>` | decorative plus overlays block drag-to-connect |
| LibTV edge hover | extracted 3-segment flow | visual behavior is evidence-driven |
| Image/video panel anchor | node-centered and inverse-scaled | source follows node, pan and zoom |
| Organize layout | evidence-based current-project topology | source project is known; generic auto-layout is not |
| Backend | local mock only | scope is frontend prototype validation |

## Prototype Boundaries

- No server persistence, real generation API, auth, upload service or collaboration model.
- LibTV organize is tuned to the current 10-node project and uses stable fallback placement for unknown nodes.
- FrameOS route ID does not yet select different persisted canvas data.
- Some menus and actions are closed-loop UI mocks; they do not imply source backend parity.

For the fuller implementation history and current state notes, read [`BIG_PICTURE.md`](BIG_PICTURE.md). For source evidence, read [`research/README.md`](research/README.md).
