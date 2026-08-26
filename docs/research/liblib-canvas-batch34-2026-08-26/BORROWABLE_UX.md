# Batch 34 Borrowable UX

## Decision Summary

The highest-value borrow is the **director-desk interaction model**, not the 3D
renderer. The current LibTV clone already has a dense 2D node canvas with selected
node toolbars/panels, React Flow topology and Zustand history. It can borrow the
director desk's context rules and camera-oriented workflows without pretending
that a 2D node graph is a 3D scene editor.

## Priority A: Borrow

### A1. Full-bleed three-zone workbench

**Upstream fact:** `DirectorDeskShell.tsx:6-31` composes a central viewport with
absolute left/right sidebars; CSS fixes the sidebar widths at 220px and 300px and
offers a single collapse state.

**Why it is valuable:** The user always sees the working surface, object context
and property context at once. The sidebars do not become unrelated modal steps.
This is the clearest information architecture for a “导演台” mode inside a
canvas product.

**Borrow in LibTV:** Create a director-desk route or mode shell with:

- a central stage/preview surface;
- a left scene/shot context rail;
- a right property/inspector rail;
- one explicit collapse/fullscreen action;
- safe-area-aware overlay positioning.

**Do not borrow:** the exact 220/300 values as a LibTV source fact. LibTV already
has source-calibrated overlay widths and should be measured independently.

### A2. Selection-driven inspector routing

**Upstream fact:** `directorSelectors.ts:1-17` maps view mode, crowd selection,
selected object kind and camera mode to `scene`, `character`, `prop` or `camera`.
An empty viewport click explicitly opens the scene inspector.

**Why it is valuable:** One stable property rail changes meaning with selection,
so the user does not search through a feature menu to find the relevant controls.
This matches the current clone's selected-node floating panels and makes a director
desk feel like an editor rather than a collection of dialogs.

**Borrow in LibTV:** Model a director-desk selection context with explicit variants:

```text
nothing selected -> scene/project inspector
shot selected    -> shot/camera inspector
character selected -> character inspector
media selected   -> media/shot properties
multi-select     -> shared properties or clear empty state
```

**Do not borrow:** a universal `mode` flag into `canvasStore`; the current project
already keeps LibTV and FrameOS stores independent. Add a director-specific state
boundary.

### A3. Object tree as a semantic companion to the canvas

**Upstream fact:** `ObjectTreePanel.tsx:24-33, 97-201` groups objects into roles,
crowds, geometry, models and cameras; it supports search and hides empty groups.
Rows expose visibility/lock controls and Shift selection.

**Why it is valuable:** The tree solves the selection problem that a spatial
canvas cannot solve well when objects overlap or are off-screen. It is also an
efficient place for repeated operations.

**Borrow in LibTV:** For a director-desk layer, add a compact shot/resource tree
with:

- semantic groups;
- search;
- visibility/lock;
- selection without requiring a spatial hit;
- group rows for repeated references or candidate batches.

**Do not borrow:** the exact entity groups as if LibTV already had roles and
cameras. The initial groups should follow verified LibTV entities: source media,
shots, prompt references, generated candidates and output.

### A4. Camera shot as a first-class record, not only a transform

**Upstream fact:** `DirectorProject` keeps camera rigs in `objects` and shot data
in `cameras`; `CameraPanel.tsx:480-584` edits name, active camera, position,
target mode, target coordinates and FOV. Moving a camera rig updates the linked
shot.

**Why it is valuable:** A camera is both a visible object in a staging space and
an authored shot that can be recalled, captured and sent elsewhere. This duality
is directly relevant to video storyboarding.

**Borrow in LibTV:** Represent a director-desk shot with:

- stable shot id/name;
- source/reference association;
- framing/ratio and camera intent;
- preview/capture outputs;
- a link from shot record to the corresponding canvas node or node group.

**Do not borrow:** 3D position/FOV semantics until a 3D runtime or an explicit
2D framing model exists. Start with shot metadata and preview state.

### A5. Capture as an authored artifact loop

**Upstream fact:** The camera panel stores captures per shot, groups them by camera,
offers thumbnail actions, a zoom/pan viewer, delete, download and “send to canvas”.
The viewport capture bridge crops to the visible aspect frame and removes helpers
before exporting.

**Why it is valuable:** It closes the loop from setup to review: a user can create
a shot, inspect the result, keep variants and send the chosen result back to the
main canvas.

**Borrow in LibTV:** Add a shot preview/capture history surface with:

- one current preview;
- saved variants;
- lightweight viewer;
- send/create-node action;
- metadata that records the request and source association.

This is especially high value for the existing Seedance and long-video workflows.

## Priority B: Borrow After A

### B1. Viewport toolbar with trigger-relative menus

The toolbar centralizes transform mode, resource add, camera add, aspect ratio,
capture and panel collapse. Menus close on outside pointer-down and are positioned
relative to their trigger. This pattern matches the current clone's overlay
lifecycle work and is safer than adding another global modal.

### B2. Framing tools as visible state

The aspect frame, safe-area mask, rule-of-thirds overlay and native axis gizmo
make composition state visible. In LibTV, the first adaptation can be a 2D
framing/shot overlay around a selected image/video node or director preview, with
the same “what will be captured is visibly framed” principle.

### B3. Axis fields with drag affordances and batched history

The inspector's `X/Y/Z` prefixes are draggable, keyboard-adjustable and wrapped in
one undo batch. This is a small but high-leverage interaction for numeric tuning.
It can be reused for shot duration, crop position, zoom, rotation or intensity
once the corresponding LibTV feature has evidence.

### B4. Group selection as a real entity

Crowd selection is not just a visual highlight: the store computes an anchor,
applies transform deltas to every member, and updates focused cameras. For LibTV,
the same pattern could apply to a shot bundle or candidate batch, but only after
the group semantics are source-backed.

### B5. Scoped persistence and host bridge

Per-instance local persistence and explicit ready/session/close/capture messages
are useful if the director desk is embedded as a route or iframe. The message
protocol must be redesigned around current LibTV identifiers and origin rules.

## Do Not Borrow Directly

| Upstream element | Reason |
|---|---|
| Three.js scene runtime as the first implementation | Current LibTV is a React Flow 2D canvas; adding a second rendering model has high integration cost |
| `模型库/` asset glob and model files | The path is external to the submodule and asset licenses are separate |
| All upstream CSS tokens and dimensions | Visual evidence belongs to the upstream product, not LibTV source calibration |
| Host message names | They are specific to StoryAI embedding and are not current LibTV contracts |
| README feature counts | README claims must be checked against fixed source/runtime |
| Direct source copy into `src/` | Creates license, ownership and architecture drift; use behavior/spec extraction |

## Recommended Next Implementation Batch

The first product-facing director desk slice should be **2D director workspace
shell + shot inspector + capture history**, not a full 3D scene:

1. open a director-desk mode from a verified LibTV shot/video context;
2. show a source-aware left rail for shots and references;
3. show a right inspector for shot name, ratio, duration, prompt and source links;
4. show a central framed preview with composition guides;
5. create capture/preview variants as a reversible local transaction;
6. allow sending a selected preview back to the main LibTV canvas;
7. keep the 3D viewport as a separately planned follow-up.

