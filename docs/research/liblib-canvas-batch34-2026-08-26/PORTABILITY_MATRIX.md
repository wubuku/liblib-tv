# Batch 34 Portability Matrix

## Current Architecture Constraints

The current clone has two independent routes and stores:

- LibTV `/` uses React Flow nodes, `canvasStore` and `uiStore`;
- FrameOS `/frameos/*` uses its own node system and `frameosStore`;
- the current clone does not currently depend on Three.js or React Three Fiber
  for product runtime; this is the starting state of the clone, not a
  compatibility restriction;
- selected-node panels are already calibrated as node-anchored overlays;
- graph workflows use atomic store transactions and local in-memory history.

The upstream desk is an existing LibTV-oriented replication: it stores a 3D
scene document and renders it through R3F. Portability means adapting its MIT
code to the current Next.js/React 19 project while keeping the director store
separate from both canvas stores.

## Capability Matrix

| Upstream capability | Source location | Current LibTV analogue | Cost | Decision |
|---|---|---|---:|---|
| Full-bleed three-zone shell | `src/app/layout/DirectorDeskShell.tsx` | canvas page + drawers/overlays | Low | Borrow layout principle |
| Selection-driven right inspector | `src/editor/store/directorSelectors.ts`, panels | selected-node panels | Low | Borrow routing principle |
| Semantic object tree | `ObjectTreePanel.tsx` | asset drawer/storyboard context | Medium | Borrow for director mode |
| Shot record linked to visible camera rig | `directorProject.ts`, `directorStore.ts` | video/image nodes and derived targets | Medium | Port dual rig/shot model |
| Camera view switching | `DirectorCanvas.tsx` | preview/player state | Medium | Port with R3F viewport |
| Aspect frame + thirds guide | `ViewportAspectOverlay.tsx` | image/video preview surfaces | Medium | Borrow after source calibration |
| Transform gizmo | R3F `TransformControls` + `SceneRoot.tsx` | none inside current clone | Medium | Port inside director viewport |
| 3D scene/object rendering | `DirectorCanvas.tsx`, `SceneRoot.tsx` | none in current clone | High | Port as first-slice baseline |
| Character body/pose runtime | `runtime/` and pose presets | source confirms pose/bone editing | High | Port basic presets; extend to keyframes later |
| Crowd array | `directorStore.ts`, `ObjectTreePanel.tsx` | source confirms group tracks | Medium | Port group transform model |
| Model library | `modelLibraryCatalog.ts`, external `模型库/` | asset manager/history | High | Rebuild around owned assets |
| Panorama import/adaptation | `panoramaImport.ts`, `ViewportBackground.tsx` | existing panorama prototype | Medium | Compare with existing source-backed behavior |
| Screenshot variants | capture bridge + `CameraPanel.tsx` | local result/image nodes | Medium | High-value candidate |
| Project JSON import/export | `io/exportProjectJson.ts`, `importProjectJson.ts` | in-memory canvas state | Medium | Borrow only after schema validation |
| Scoped local persistence | `directorStore.ts`, `hostBridge.ts` | active canvas store | Medium | Borrow scoped-key principle |
| StoryAI host bridge | `hostBridge.ts` | React Flow node/edge transactions | Medium | Adapt typed panorama/session/capture bridge |
| Animation timeline | absent upstream | source bundle confirms full timeline | High | New implementation after static desk |
| Motion paths and curves | absent upstream | source bundle confirms path editor | High | New implementation after timeline |
| Phone virtual camera | absent upstream | source bundle confirms gyro recording | Very high | Defer until camera tracks exist |

## Proposed Adaptation Boundary

```text
LibTV canvas node / selected video
  -> DirectorDeskSession (new director-specific state boundary)
     -> R3F scene staging, camera and capture
     -> timeline and motion-path extension
  -> selected capture / shot result
  -> LibTV image/video node transaction
```

The director session should not be a `mode` flag added to `canvasStore`, and it
should not reuse FrameOS state. A future implementation can use:

- a dedicated `directorStore` for shot session, selection, inspector and captures;
- typed adapters between LibTV node IDs and director shot IDs;
- an explicit return transaction to create or update LibTV nodes;
- a lazy-loaded R3F route or full-screen island opened by the director node.

## Asset And License Boundary

- Repository code is MIT at the fixed upstream commit.
- The included mannequin has a separate Sketchfab Standard notice and source URL.
- The model library references files outside the submodule and has no single
  license statement in the inspected source.
- Current clone should not copy the GLB, model library, thumbnails or README
  screenshots into product assets without separately reviewing rights.

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Two rendering systems in one route | bundle size, pointer-event conflicts, debugging cost | use a dedicated R3F viewport region and an explicit React Flow/R3F state bridge |
| Duplicate source of truth for shots | stale preview/node links | typed adapter and one transaction boundary |
| Persisting data URLs in localStorage | quota failures and slow hydration | keep preview metadata; use object URLs/IndexedDB when real |
| Upstream host protocol mismatch | silent integration failure | define LibTV-specific messages or same-store adapter |
| External `模型库/` dependency | non-reproducible build | replace with owned catalog or explicit optional asset package |
| README/test status drift | false confidence | record fixed commit and run commands in implementation log |
