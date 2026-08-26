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
    LibPage --> DirectorStore[directorStore]
    LibFlow --> LibNodes[LibTV node renderers]
    LibFlow --> LibOverlays[toolbars panels dialogs]
    LibNodes --> DirectorDesk[lazy R3F DirectorDesk]
    DirectorDesk --> DirectorStore
    DirectorDesk --> CanvasStore

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
| `/` | `src/app/page.tsx` | `canvasStore` + `uiStore` + `directorStore` | 11 LibTV types | in-memory LibTV graph plus lazy R3F director island |
| `/frameos` | `src/app/frameos/page.tsx` | `frameosStore` | redirect entry | route entry only |
| `/frameos/canvas/[id]` | `src/app/frameos/canvas/[id]/page.tsx` | `frameosStore` | text/image/video | `[id]` is currently a demo placeholder |

## Module Responsibilities

| Module | Path | Responsibility |
|---|---|---|
| Route orchestration | `src/app/` | React Flow setup, route layout, keyboard and overlay composition |
| UI components | `src/components/` | panels, toolbars, dialogs and route-specific visual behavior |
| LibTV nodes | `src/components/nodes/` | script, image, text, video, execution, group, breakdown input/result, clip and audio |
| FrameOS nodes | `src/components/frameos/nodes/` | shared shell plus text/image/video renderers |
| Director desk | `src/components/director/` | full-screen shell, R3F scene, semantic tree, Inspector, framing, still capture, typed animation timeline, editable motion paths/speed curves, browser video recording and phone virtual-camera local preview |
| State | `src/store/` | graph/history in `canvasStore`, page overlays in `uiStore`, serializable 3D authoring and timeline state in `directorStore` |
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
source edge; smart matting creates one pending video + one direct source edge; depth
motion capture creates one pending reference video + one direct source edge. Frame
capture, smart matting and depth motion capture preserve source selection for repeated
commands. Each workflow records one pre-change snapshot so one undo/redo operates on
the whole result set. Picture edit uses a shared node-local mark editor for three
subject modes, then creates one pending video + one direct source edge with
request-shaped mark metadata.

The director path uses a separate state and renderer boundary:

```text
director node CTA
  -> uiStore.activeDirectorNodeId
  -> lazy client-only DirectorDesk
  -> directorStore scene/object/camera/timeline edits
  -> typed transform/camera tracks
  -> optional serializable motion path + track-level cubic-Bezier speed curve
  -> optional browser-orientation/pointer phone-camera pose recording
  -> deterministic scrub/playback sampling
  -> R3F Canvas render and helper-free still/video capture
  -> canvasStore.createDirectorCapture or createDirectorAnimationExport
  -> atomic image/video node + source edge + graph history
```

React Flow remains mounted while the fixed workspace is open. `directorStore`
contains only serializable authoring state; mutable Three.js camera, renderer and
Object3D references stay inside R3F components. Timeline sampling is a director
store concern: transform and camera tracks interpolate serializable values, then
optionally remap normalized progress through a track-level cubic-Bezier speed
curve and sample a bound polyline by arc length. The R3F scene observes the
resulting objects and renders enabled authoring paths; helper-free capture hides
those paths and anchors. Inspector edits and completed gizmo drags may
auto-keyframe at the current playhead, while scrub/playback never author new
keyframes. The phone virtual-camera prototype keeps orientation events, timers
and temporary sample buffers in its client component; `directorStore` receives
only finite pose/camera values and imports a completed take as a new serializable
camera object plus typed camera track.

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
- The director desk is a lazy-loaded full-screen R3F island, not a React Flow
  node panel. Its object tree, 3D selection, Inspector and bottom timeline share
  one director store.

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
| Director renderer | lazy R3F island over mounted React Flow | keeps graph and 3D renderer ownership independent while preserving return context |
| Director timeline | typed serializable tracks sampled in `directorStore` | keeps deterministic playback independent from mutable Three.js refs |
| Director motion path | local anchors/relative handles plus fixed pivot and serializable transform derive world sampled points | supports editable pencil/pen/Bezier authoring, path-level position/rotation/scale and deterministic playback without putting Three.js geometry in Zustand |
| Director speed curve | track-level cubic-Bezier control points | keeps preset/custom timing effects testable in pure sampling code |
| Director path interaction | viewport selection requests are store-guarded while a draft/anchor owns input | prevents R3F pointer-up/click ordering from changing the bound object during path authoring |
| Director path reset | identity-offset reset and creation-snapshot reset are distinct store actions | preserves a testable difference between placement cleanup and geometry restoration |
| Director return | one canvasStore graph transaction per still/video result | result node and source edge undo/redo atomically |
| Director video export | cropped 2D canvas + `captureStream`/`MediaRecorder` outside Zustand | records real R3F pixels while keeping browser runtime objects out of serializable authoring state |
| Director phone virtual camera | explicit local-preview boundary plus browser orientation/pointer input | preserves source-shaped pose recording and track import without pretending the frontend has LAN signaling, QR pairing or WebRTC |
| Backend | local mock only | scope is frontend prototype validation |

## Prototype Boundaries

- No server persistence, real generation API, auth, upload service or collaboration model.
- LibTV organize is tuned to the current 10-node project and uses stable fallback placement for unknown nodes.
- FrameOS route ID does not yet select different persisted canvas data.
- Some menus and actions are closed-loop UI mocks; they do not imply source backend parity.

For the fuller implementation history and current state notes, read [`BIG_PICTURE.md`](BIG_PICTURE.md). For source evidence, read [`research/README.md`](research/README.md).
