# Director Desk Maturity After Batch 46

## Executive Assessment

Batch 46 closes a bounded camera-screenshot management loop:

```text
capture several compositions
  -> inspect the camera screenshot gallery
  -> select and preview a record
  -> send one or all records to the canvas
  -> clear local records without deleting returned nodes
```

This slice is mature as a frontend prototype contract. It is not source-exact
where the current LibTV evidence exposes locale vocabulary but not the
authenticated gallery DOM. Source facts, fixed-upstream borrowing and clone
calibration remain separated in the batch documents.

## Capability Matrix

| Area | Clone maturity | Evidence confidence | Remaining risk |
|---|---|---|---|
| Director shell, R3F scene and timeline | high | prior focused regression | exact source spacing and defaults |
| camera properties and motion authoring | high frontend loop | source vocabulary + clone regression | source math and persistence |
| groups and crowd authoring | medium-high | source typed contracts + upstream + regression | source geometry, limits and persistence |
| capture generation and canvas return | high frontend loop | clone WebGL/graph regression | source host bridge and remote lifecycle |
| camera screenshot gallery | medium-high | current locale + fixed upstream + focused regression | source DOM, grouping schema and exact chrome |
| viewer and local cleanup semantics | medium-high | locale close/clear evidence + upstream + regression | source download/persistence behavior |
| model/environment library | low | source/upstream hints only | asset discovery, filters, import and persistence |
| collaboration and remote persistence | out of scope | no safe current contract | backend and auth boundary |

## What Is Now Stable

- camera Inspector exposes `属性 / 摄像机截图`;
- empty, grouped, selected and sent capture states are serializable and
  discoverable through stable selectors;
- single and bulk canvas return reuse the existing atomic graph transaction;
- clear-all is confirmed and does not remove returned graph nodes;
- viewer close, Escape, backdrop, zoom and download controls are bounded;
- the viewer does not leak the Inspector stacking context;
- desktop/mobile browser verification and cross-batch regression are recorded.

## Explicit Boundaries

The clone does not claim:

- exact LibTV gallery DOM, dimensions, thumbnail object-fit or hover timing;
- remote screenshot persistence or host bridge behavior;
- source camera-document serialization beyond the current clone payload;
- multi-camera authoring, capture presets or undo/redo for local gallery state;
- deletion of already returned React Flow nodes when local records are cleared.

## Next Highest-Value Queue

The Director Desk remains the active priority because its model/environment
library is still low maturity. The next batch should research and implement a
bounded asset-library loop:

```text
open model/environment library
  -> inspect tabs/search/filter states
  -> choose a fixture asset
  -> preview and add it to the Director scene
  -> verify selection, tree ownership and transform continuity
```

Do not add remote asset persistence or provider claims until current LibTV
evidence establishes them.
