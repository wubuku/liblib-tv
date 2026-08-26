# Existing Replication Reference Matrix

## Classification

The fixed upstream repository is classified as an **existing LibTV
director-desk replication/implementation reference**.

The public README does not explicitly use the word LibTV. The fixed source does:

- the initial public commit contains the test name `defines the approved
  LibTV-style procedural body types`;
- its scene sessions are scoped with `node_director_*` identifiers;
- its host panorama tests model `edge-image-director` and `sourceNodeId`;
- its bridge accepts a source canvas panorama and sends captures back to the
  host canvas;
- its shell, object groups, camera/capture flow and screenshot composition match
  the known LibTV director-desk domain.

This establishes targeting and borrowing value. It still does not make every
upstream choice a verified current LibTV source fact.

## Three-Way Comparison

| Area | Current LibTV source evidence | Upstream replication | Borrowing decision |
|---|---|---|---|
| Canvas entry | 3D director node inside the React Flow canvas | host session IDs and panorama/capture bridge | reuse the bridge concept with current clone node IDs |
| Workspace | scene editing plus animation timeline | top mode switch, left tree, R3F viewport, right inspector | reuse shell and viewport as the first implementation base |
| Renderer | real hardware-accelerated 3D; exact library unresolved | Three.js + R3F + Drei | reuse R3F unless authenticated source evidence contradicts behavior |
| Scene objects | character, prop, group and camera timeline targets | characters, crowds, primitives, models and camera rigs | reuse schema/store concepts and extend them |
| Selection | runtime details pending | tree, viewport and inspector share one selection state | reuse directly as a director-specific store contract |
| Camera | camera tracks, keyframes, follow/look-at and FOV | camera object plus semantic shot record, director/camera views | reuse dual object/shot representation |
| Framing | screenshot used as a composition reference | aspect frame, thirds guide and cropped helper-free capture | reuse directly, then source-calibrate geometry |
| Panorama | panorama preview is a hardware-accelerated 3D feature | host panorama import and spherical background | reuse loader/bridge pattern; retain existing clone panorama node |
| Character poses | pose and SAM bone keyframes | body presets, pose presets and joint sliders | reuse basic pose runtime; plan keyframe extension |
| Crowds/groups | group keyframes exist | crowd entity with batched transforms | reuse group transform model |
| Timeline | animation timeline, keyframes, curves and playback | absent | implement as a new source-backed layer |
| Motion paths | draw/edit paths, orient-to-path and speed curves | absent | implement after the static R3F desk is integrated |
| Phone virtual camera | pairing, gyro, recording and track import | absent | defer until timeline and camera tracks exist |
| Output to canvas | screenshots and animation video create canvas outputs | captures sent to host canvas | reuse capture return flow; extend to animation later |
| Persistence | runtime details pending | scoped local storage and JSON import/export | reuse schema/versioning idea, add validation |
| Assets | source has product-managed assets | one separately licensed GLB and missing external catalog | do not copy assets; use owned procedural primitives first |

## What Can Be Reused

Repository code is MIT. Code may be adapted into this MIT project if the
upstream copyright and license notice are preserved for substantial copied
portions. The following modules are high-value starting points:

1. project schema, camera object/shot linkage and selectors;
2. director-specific Zustand store structure and undo batching;
3. R3F viewport composition, transform controls and helper hiding;
4. object tree and context-sensitive inspector routing;
5. aspect-frame math and screenshot crop pipeline;
6. host panorama/capture message flow;
7. viewport toolbar menu lifecycle and camera capture variants.

These should be ported deliberately to React 19/Next.js 16 and current project
conventions. They should not remain an opaque nested app runtime.

## What Must Not Be Treated As Complete

- The upstream project stops before the current LibTV animation timeline.
- GitHub issue `#3` explicitly reports missing action and camera movement.
- GitHub issue `#1` reports that body manipulation still relies heavily on the
  right-side form instead of direct limb dragging.
- The external `模型库/` catalog is absent from the fixed repository checkout.
- Eight upstream tests currently fail.
- The included mannequin and external model assets are not covered solely by the
  repository's MIT code license.

## Recommended Implementation Sequence

### Slice 1: Static 3D Director Desk

- add a dedicated director route or lazy-loaded full-screen region;
- port the R3F viewport, scene schema, director store, tree and inspector;
- open it from the existing LibTV director node;
- accept a connected panorama/source image;
- create camera shots and send helper-free captures back as image nodes.

### Slice 2: Source-Calibrated UX

- measure authenticated LibTV shell, toolbar, panel and transition geometry;
- replace upstream-only visual guesses;
- verify camera mode, aspect framing, screenshot history and close/return flow.

### Slice 3: Current LibTV Differentiators

- add animation timeline and typed tracks;
- add transform, pose, prop, group and camera keyframes;
- add motion paths and speed curves;
- export animation video to the React Flow canvas;
- add phone virtual camera only after the camera-track model is stable.

This sequence uses the completed upstream replication to avoid rebuilding the
static 3D editor from zero while keeping the current LibTV source as the product
truth.
