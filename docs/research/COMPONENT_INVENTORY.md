# Component Inventory

This is the authoritative catalog of components in this clone. For each, file path, purpose, and visual/behavioral notes are documented. Layout details that don't fit here live in individual specs under `./components/`.

> **Source of truth for component structure**: this file. For per-component interaction details, see `./components/<Name>.spec.md`.

---

## Layout & Shell

| Component | File | Purpose |
|-----------|------|---------|
| `TopNavBar` | `src/components/TopNavBar.tsx` | Floating top controls: route mark, canvas/project navigation, workbench/storyboard mode, share, credits and Agent. |
| `LeftSidebar` | `src/components/LeftSidebar.tsx` | Compatibility name for the centered primary bottom toolbar with 8 icon buttons and mutually exclusive entry panels. |
| `BottomToolbar` | `src/components/BottomToolbar.tsx` | Lower-left canvas controls: asset drawer, organize, source-anchored minimap, edges, snap and store-driven zoom menu. |
| `ScriptHeader` | `src/components/ScriptHeader.tsx` | Compact "正在跟随" + 取消ESC banner above canvas + script title node. |
| `StoryboardBoard` | `src/components/StoryboardBoard.tsx` | Data-driven storyboard mode: current-canvas key elements rail plus image/video columns; card selection stays in `canvasStore`. |
| `AgentDrawer` | `src/components/AgentDrawer.tsx` | 340px right drawer with source-shaped new-chat header, 2x2 local Skill recommendations, notification banner and composer. |

## Node Components

All node types inherit the React Flow `NodeProps` shape. The connection handle is rendered by `<Handle>` from `@xyflow/react` and styled via globals.css (see "Node Handle" section of `globals.css`).

| Type ID | File | Notes |
|---------|------|-------|
| `script` | `src/components/nodes/ScriptNode.tsx` | Title + multi-line script text, default 320px wide, bg `#212121`. |
| `image` | `src/components/nodes/ImageNode.tsx` | Image with header (filename + dimensions), watermark overlay. Width capped at 360px. |
| `text` | `src/components/nodes/TextNode.tsx` | Inline-editable text block. |
| `video` | `src/components/nodes/VideoNode.tsx` | Failed/ready video renderer; single selection shows Seedance generation/processing/reshoot UI. Source failed video is a child of the video group. |
| `script-execution` | `src/components/nodes/ScriptExecutionNode.tsx` | 3-step progress UI (确认镜头/准备资产/合成提示词) + open-script-node button. |
| `storyboard-group` | `src/components/nodes/StoryboardGroupNode.tsx` | Image/video background shell; source video group parents the failed video at relative `(62,62)`. |
| `shot-breakdown` | `src/components/nodes/ShotBreakdownNode.tsx` | 逐帧拉片 input state, source metadata, dimensions and local completion command. |
| `shot-breakdown-result` | `src/components/nodes/ShotBreakdownResultNode.tsx` | Persistent storyboard, motion or music result group created by a completed breakdown. |
| `video-clip` | `src/components/nodes/VideoClipNode.tsx` | 智能剪辑 empty node with four single-column suggestion modes; editor is a selected-node overlay. |
| `audio` | `src/components/nodes/AudioNode.tsx` | Local audio preview card with handles, filename, waveform placeholder and duration. |

## Edge Components

| Type ID | File | Notes |
|---------|------|-------|
| `default` | `src/components/nodes/DeletableEdge.tsx` | Custom edge with hover-flow effect (3 light segments), base color `#86909c` → `#c0c8d0` on hover/select, strokeWidth 2 → 4. Scissors delete button at midpoint. |

## Panels & Dialogs

| Component | File | Purpose |
|-----------|------|---------|
| `AddNodePanel` | `src/components/AddNodePanel.tsx` | 9-entry source-shaped node list, material submenu, upload/history local feedback. |
| `CanvasTabDropdown` | `src/components/CanvasTabDropdown.tsx` | Source-shaped project context and multi-canvas lifecycle with active check, edit/new/switch/rename/copy/delete and explicit close cleanup. |
| `AssetManagerPanel` | `src/components/AssetManagerPanel.tsx` | 240px source-shaped project/canvas drawer with one-level node tree, canvas/assets tabs, local sort/filter/search and active-canvas empty states. |
| `ToolboxPanel` | `src/components/ToolboxPanel.tsx` | Bottom-toolbar-anchored 480x460 panel with 25 source-derived presets. |
| `MaterialLibraryPanel` | `src/components/MaterialLibraryPanel.tsx` | Bottom-toolbar-anchored 240x163 material menu. |
| `CharacterLibraryPanel` | `src/components/CharacterLibraryPanel.tsx` | Responsive character detail and 23-item asset carousel modal. |
| `HistoryPanel` | `src/components/HistoryPanel.tsx` | Responsive asset history modal with filters, zoom, batch selection and local result images. |
| `ImageToolbar` | `src/components/ImageToolbar.tsx` | `900.5x49` React Flow `NodeToolbar` above the selected image: 人像质感, 全景, 多角度, 打光, 九宫格, 高清, 宫格切分. |
| `ImageEditPanel` | `src/components/ImageEditPanel.tsx` | `660px` node-anchored image prompt panel; inverse-scales and keeps a `16 * zoom` lower gap. |
| `VideoGenerationPanel` | `src/components/VideoGenerationPanel.tsx` | `660x274` Seedance 2.5 model/mode/parameter prompt editor below a selected video. |
| `VideoProcessingToolbar` | `src/components/VideoProcessingToolbar.tsx` | Ready-video top toolbar for enhance, reshoot, frame analysis, continuation, subtitle/audio/edit and download actions. |
| `SegmentReshootPanel` | `src/components/SegmentReshootPanel.tsx` | Ready-video `片段重拍` filmstrip + Prompt editor; no continuation branch. |
| `VideoContinuationSelector` | `src/components/VideoContinuationSelector.tsx` | `660x56` smart-continuation range selector with handle/region drag and target-node handoff. |
| `VideoClipEditPanel` | `src/components/VideoClipEditPanel.tsx` | `660x191` node-anchored 智能剪辑 Prompt editor with local-only mode/reference/submit feedback. |
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
| `useCanvasStore` | `src/store/canvasStore.ts` | Project name plus all canvas data: canvas list, active ID, multi-selection, graph, viewport and per-canvas in-memory history. Includes project/canvas CRUD, graph commands and undo/redo. |
| `useUIStore` | `src/store/uiStore.ts` | Top-level overlay visibility including zoom menu, editor mode/tools, and grid/minimap/edge/snap/zoom display state. |

---

## Removed / Planned

These were considered during planning but not implemented in this snapshot:

- **Backend persistence**: every node/edge lives only in Zustand memory. Refresh wipes state.
- **Real image generation / model integration**: prompt + camera + model select are UI scaffold only.
- **Drag-handle "snap to target" animations on top of the connection line preview**.

For future work see [`README.md` → "Known Limitations"](../../README.md#known-limitations--future-work).
