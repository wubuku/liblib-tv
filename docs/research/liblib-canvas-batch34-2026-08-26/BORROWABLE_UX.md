# Batch 34 Borrowable UX

## Decision Summary

The highest-value borrow is the upstream's **complete static 3D editor slice**:
R3F viewport, scene schema, object tree, selection-driven inspector, camera/shot
model, framing and capture return. Rebuilding those pieces as a 2D placeholder
would discard the main value of an existing LibTV director-desk replication.

This is a product sequencing decision, not a technical incompatibility claim:
React Flow and Three.js/R3F can coexist. If the director-desk experience requires
true 3D staging. R3F should be treated as the first-class central viewport and
connected to the LibTV graph through a typed session/return boundary.

## Priority A: Borrow

### A1. Full-bleed three-zone workbench

**Upstream fact:** `DirectorDeskShell.tsx:6-31` composes a central viewport with
absolute left/right sidebars; CSS fixes the sidebar widths at 220px and 300px and
offers a single collapse state.

**Why it is valuable:** The user always sees the working surface, object context
and property context at once. The sidebars do not become unrelated modal steps.
This is the clearest information architecture for a “导演台” mode inside a
canvas product.

**Borrow in LibTV:** Port the workbench shell with:

- a central stage/preview surface;
- a left scene/shot context rail;
- a right property/inspector rail;
- one explicit collapse/fullscreen action;
- safe-area-aware overlay positioning.

**Calibrate later:** the exact 220/300 values are upstream facts until the
authenticated LibTV desk is measured.

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

**Borrow in LibTV:** Reuse the dual camera-object/shot-record model with:

- stable shot id/name;
- source/reference association;
- framing/ratio and camera intent;
- preview/capture outputs;
- a link from shot record to the corresponding canvas node or node group.

The first implementation now includes the R3F runtime, so position, target and
FOV are legitimate first-slice fields rather than deferred 2D metadata.

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
make composition state visible. Port them into the R3F director viewport and
keep “what will be captured is visibly framed” as an explicit contract.

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
| Treating the nested Vite app as an opaque iframe dependency | Port the MIT code into current Next.js/React 19 boundaries so types, history and return transactions remain owned |
| `模型库/` asset glob and model files | The path is external to the submodule and asset licenses are separate |
| All upstream CSS tokens and dimensions | Visual evidence belongs to the upstream product, not LibTV source calibration |
| Host message names unchanged | Preserve the bridge shape, but rename and type it for current LibTV node transactions |
| README feature counts | README claims must be checked against fixed source/runtime |
| Model and screenshot assets | They have separate or unresolved rights; code reuse under MIT does not grant asset rights |

## Recommended Next Implementation Batch

The first product-facing director desk slice should be a **real R3F director
workspace** based on the existing replication:

1. open a director-desk mode from a verified LibTV shot/video context;
2. port the director store, scene schema and central R3F viewport;
3. show the semantic object tree and context-sensitive scene/object/camera inspector;
4. support transforms, camera view, aspect framing and composition guides;
5. create helper-free capture variants as a reversible local transaction;
6. allow sending a selected preview back to the main LibTV canvas;
7. add the source-backed timeline, motion paths and animation export in the next
   slice rather than inventing them from the upstream project.
