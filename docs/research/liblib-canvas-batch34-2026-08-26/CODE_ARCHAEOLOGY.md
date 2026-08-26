# Batch 34 Code Archaeology

## 1. Fixed Source

| Item | Value |
|---|---|
| Submodule path | `research/upstream/storyai-3d-director-desk` |
| Remote | `https://github.com/jiguang132/storyai-3d-director-desk.git` |
| Branch | `main` |
| Fixed commit | `8c8bd361790be4d37158a7430365e65546e358fe` |
| Short commit | `8c8bd36` |
| Commit date | 2026-07-06 11:21:59 +08:00 |
| Package | `storyai-3d-director-desk-demo@0.0.1` |
| License | MIT for the repository; model asset has a separate Sketchfab notice |

The commit is recorded by the parent repository gitlink and should be treated as
the only source version for this batch. Do not analyze a moving GitHub branch
without updating the fixed commit and implementation log.

## 2. Runtime Composition

```text
src/main.tsx
  -> App.tsx
     -> DirectorDeskShell
        -> ObjectTreePanel
        -> DirectorCanvas
           -> R3F Canvas
              -> ViewportBackground
              -> OrbitControls or PerspectiveCamera
              -> SceneRoot
        -> RightPanel
           -> ScenePanel
           -> CharacterPanel
           -> PropPanel
           -> CameraPanel
```

File-level evidence:

- `src/App.tsx:15-102` owns the top bar, director/camera mode switch, close
  message and Cmd/Ctrl copy, paste and undo shortcuts.
- `src/app/layout/DirectorDeskShell.tsx:6-31` makes a full-bleed workbench and
  overlays the left and right sidebars around the central viewport.
- `src/editor/canvas/DirectorCanvas.tsx:585-755` composes the R3F renderer,
  orbit/director camera, saved camera view, capture bridge, aspect overlay,
  native gizmo and viewport toolbar.
- `src/editor/canvas/SceneRoot.tsx:751-864` maps domain objects into ground,
  imported models, characters, props, crowds and camera rigs.

## 3. Domain Model

`src/editor/schema/directorProject.ts:1-108` defines a versioned project, not a
React Flow graph:

```text
DirectorProject
  scene: SceneSettings
  assets: DirectorAssetRef[]
  objects: DirectorObject[]
  cameras: DirectorCameraShot[]
  activeCameraId
  panoramaAssetId
```

Important relationships:

| Entity | Representation | UX consequence |
|---|---|---|
| Scene | one `SceneSettings` object | empty viewport selects the scene inspector |
| Asset | reusable file/url reference | model instances point to `assetRefId` |
| Object | visible/locked transformable scene item | object tree and 3D hit testing select it |
| Camera object | `DirectorObject(kind="camera")` | selectable and transformable in director view |
| Camera shot | separate `DirectorCameraShot` | stores FOV, target, active shot and captures |
| Camera link | object `linkedCameraId` -> shot `id` | moving the rig updates the shot transform |
| Crowd | many character objects sharing `crowdId` | tree presents one row; transforms fan out to members |
| Panorama | asset plus `panoramaAssetId` | scene background, not a selectable scene object |

The camera dual representation is the most important design detail to preserve
if this is adapted: the visible camera rig is an object, while the shot is a
semantic record that can own screenshots and target configuration.

## 4. Zustand Store And Lifecycle

`src/editor/store/directorStore.ts` is a single domain/UI store:

- `DirectorUiState` contains view mode, single/multi-selection, crowd selection,
  inspector mode, transform mode, aspect ratio, thirds guide and sidebar state
  (`:59-73`);
- `DirectorActions` covers creation, selection, transform, import, camera,
  capture, clipboard, undo and persistence (`:89-143`);
- the default project starts with one UE4 mannequin role and one camera
  (`:456-506`);
- mutations pass through `commitMutation` (`:1039-1081`), which compares a
  persisted snapshot, optionally writes local storage and tracks undo;
- continuous transform drags use `beginUndoBatch`/`endUndoBatch` to create one
  undo step (`:1090-1129`);
- the undo stack is capped at 80 entries (`:173-179`, `:1030-1031`);
- persisted scenes are scoped by the URL `instanceId`, and local models use a
  separate global library key (`:192-210`, `:268-312`, `:396-436`);
- `openScopedScene` switches the scene storage key and rehydrates a fresh runtime
  state (`:2014-2030`);
- imported project JSON is only parsed as `DirectorProject`; it is not schema
  validated beyond the store's lightweight shape guard (`:314-326` and
  `src/editor/io/importProjectJson.ts:1-5`).

This gives the upstream tool a coherent interaction contract: every visible edit,
whether made in a property field or a 3D handle, flows through the same mutation
and persistence path.

## 5. Viewport And Camera Architecture

The viewport is a real 3D runtime:

- `@react-three/fiber` owns the primary canvas;
- `OrbitControls` drives director view and keeps a `CameraShotSnapshot` in local
  React state;
- camera view replaces the default camera with a `PerspectiveCamera` built from
  the active shot;
- `TransformControls` attaches only to the selected, unlocked object or crowd;
- translation snap is enabled when `scene.snapToGrid` is true;
- a second small R3F canvas renders the native `GizmoViewport`, while transparent
  DOM hit buttons map axis clicks back to a camera snapshot
  (`DirectorCanvas.tsx:507-581`);
- the aspect frame and mask are DOM overlays, not 3D geometry; safe-area insets
  account for the 220px left and 300px right sidebars
  (`DirectorCanvas.tsx:603-613`);
- the camera rig is deliberately a wireframe body plus lens, reels, hit box and
  viewfinder frustum, and is hidden from screenshot capture
  (`SceneRoot.tsx:610-748`);
- scene labels are 3D billboards and can also be rasterized into exported
  screenshots.

The capture bridge temporarily renders from the requested camera, hides helper
objects, crops to the visible aspect frame and returns PNG data URLs plus
camera metadata. Four-view and twelve-view capture orbit around the current
target and restore the original camera in a `finally` block
(`DirectorCanvas.tsx:392-476`).

## 6. Panels And Interaction Routing

### Left object tree

`src/editor/panels/ObjectTreePanel.tsx:24-33` fixes the group order:

```text
角色 -> 群众 -> 几何体 -> 我的模型 -> 摄像机
```

It supports:

- keyword search with a centered empty state;
- group-specific icons;
- visibility and lock toggles without selecting the row;
- normal selection and Shift multi-select;
- crowd rows that expand to preview members but select the group as one unit;
- camera rows that activate the camera shot;
- Delete/Backspace deletion while protecting editable fields.

### Right inspector

`RightPanel` delegates by `selectRightPanelKind`:

| Context | Inspector | High-value controls |
|---|---|---|
| Empty director view or explicit scene selection | `ScenePanel` | scene transform, panorama, sky, ground, labels, snap |
| Character or crowd | `CharacterPanel` | transform, uniform scale, color, pose presets, joint sliders |
| Imported model or prop | `PropPanel` | name, transform, scale, color |
| Camera selection or camera view | `CameraPanel` | active shot, position, target mode, FOV, captures |

The inspector controls are intentionally shared: text fields, custom selects,
axis inputs, range-plus-number controls, color controls and collapsible sections
live in `InspectorControls.tsx`. Axis prefixes are draggable and keyboard
adjustable; focus/blur wraps field edits in an undo batch.

### Viewport toolbar

`ViewportToolbar.tsx` puts the highest-frequency actions into a compact icon
capsule: translate, rotate, scale, add character, panorama import, local model
import, model library, add camera, aspect ratio, current/four/twelve captures and
sidebar collapse. Menus are trigger-relative and close on outside pointer down.
Character creation uses hover submenus for crowd arrays and geometry primitives.

## 7. Assets, Models And Host Boundary

The upstream repository contains one GLB mannequin and a separate license notice.
The model library catalog is different: it uses Vite `import.meta.glob` against
`../../../../模型库/**/*.fbx` and thumbnail folders, which resolve outside the
submodule tree in the current checkout. Therefore the model catalog is not
self-contained in this research submodule.

Local FBX/OBJ files are read as data URLs by
`src/editor/loaders/localModelImport.ts`. Local model assets are persisted in
`localStorage`; normal project state can keep model instances separate from the
asset library.

`src/editor/io/hostBridge.ts` implements a same-origin `postMessage` protocol:

| Message | Direction | Meaning |
|---|---|---|
| `storyai:director-desk-ready` | desk -> host | runtime initialized |
| `storyai:director-desk-close` | desk -> host | user closed the desk |
| `storyai:director-desk-session` | host -> desk | scoped instance and theme |
| `storyai:director-desk-panorama` | host -> desk | connect a canvas panorama |
| `storyai:director-desk-panorama-removed` | desk -> host | connected panorama removed |
| `storyai:director-desk-captures-sent` | desk -> host | send one or all captures back |

The host bridge is a useful integration pattern but not a drop-in LibTV contract:
the current clone has no equivalent iframe session protocol.

## 8. Test And Quality Signals

The fixed source contains 34 `*.test.*` files and 299 `it`/`describe` declarations
by static scan. Tests cover:

- store creation, selection, crowds, object-focused cameras, persistence,
  migration, clipboard and undo batching;
- viewport geometry, camera rig orientation, aspect cropping, labels and helper
  hiding;
- toolbar menus, model library, local import, crowd creation and responsive
  overlay behavior;
- scene, character, prop and camera inspector interaction;
- host messages, screenshot bridge and panorama seam/pole processing.

The README at this fixed commit reports `304 / 312` tests passing with 8 failures.
Running `npm test` against this checkout produced the same aggregate result:
304 passed, 8 failed across 34 test files. The matching count is now a verified
fixed-checkout observation, while the individual failures remain relevant
maintenance signals.

## 9. What The Code Actually Provides

### Verified implementation

- full-bleed director workbench;
- director/camera mode switching;
- scene/object/camera domain separation;
- 3D transform handles and camera frustums;
- selection-driven inspector routing;
- crowd arrays with group transforms and pose updates;
- local model and panorama import;
- aspect frame, thirds guide, native gizmo and capture crop;
- screenshot records, viewer zoom/pan/delete/send;
- local persistence, scoped sessions, JSON export/import;
- copy/paste and batched undo;
- host message bridge.

### README-only, incomplete or externally constrained

- the exact count of eight built-in人物 and twenty poses is partly represented by
  presets, but the current source also exposes additional body-type/pose machinery;
- the external model library depends on a sibling `模型库/` directory absent from
  the submodule; three model-library tests fail because the expected catalog items
  are unavailable in the fixed checkout;
- JSON import has no robust runtime validation;
- no separate timeline or shot sequence editor was found in the inspected source;
- no production backend, collaboration or remote persistence was found.

## 10. Fixed-Checkout Verification Notes

`npm run build` passed at the fixed commit. The build emitted three unresolved
runtime thumbnail URL warnings for the external `模型库/` path and a large-chunk
warning. `npm test` passed 304 of 312 tests; the eight failures are documented in
[`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md). These results strengthen the
portability decision: extract interaction contracts and data relationships, then
rebuild the first LibTV slice around owned, source-backed entities.
