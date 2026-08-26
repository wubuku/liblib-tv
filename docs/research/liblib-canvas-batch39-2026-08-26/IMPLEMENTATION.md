# Batch 39 Implementation Log

> Status: main product implementation complete; focused verification and
> screenshot finalization pending.

## Protection Points

1. Source vocabulary, cross-chunk limit and calibration boundary.
2. Pure forward/inverse transform math and path schema.
3. Store transform/reset lifecycle.
4. R3F world/local anchor controls and Inspector UI.
5. Playwright, screenshot ledger, regressions and stable docs.

## Current Decisions

- Preserve local editable anchors and world-space derived `path.points`.
- Persist one creation-time centroid pivot and deep initial-anchor snapshot.
- Reuse the upstream replication's pure X→Y→Z group-transform pattern without
  claiming it as LibTV source behavior.
- Do not add a path-level TransformControls gizmo or animation export in this
  batch.

## Main Implementation

### Pure transform layer

- Added creation-time centroid pivot calculation, deep anchor cloning and
  identity path transforms.
- Added point/vector forward transforms with positive per-axis scale followed
  by X→Y→Z degree rotations and world translation.
- Added the exact inverse sequence for world-space anchor/handle commits.
- Added transformed world-anchor derivation while preserving the existing
  anchor-to-polyline Bezier builder.

### Serializable path state

- Every preset and free-draw path now stores `pivot`, `transform` and
  `initialAnchors`.
- `anchors` remains editable local geometry; `points` is rebuilt from
  transformed world anchors and remains the timeline playback boundary.
- Added path transform field updates with finite input handling and positive
  `0.05..20` scale clamping.
- Added distinct reset actions: offset-only identity reset versus creation
  snapshot restore.

### R3F and Inspector

- Persisted path lines, anchors, handles and guide lines now render from
  transformed world anchors.
- R3F submits world anchor/handle positions to store actions; the store uses the
  current path transform to commit local values atomically.
- Added exact source-labeled `位置`, `旋转`, `缩放`, `重置偏移` and `重置`
  controls before the anchor editor.
- Added semantic pivot and world-anchor selectors for deterministic tests.

## Browser Smoke Result

Run at `1440x900` against the local clone:

- rectangle creation produced four local anchors, four deep initial anchors, a
  finite centroid pivot and identity transform;
- position offset translated every world point and the sampled character;
- Y rotation and nonuniform X/Z scale rebuilt the world curve while preserving
  local anchors;
- a world anchor target round-tripped through the store inverse transform
  within `0.001`;
- a world output-handle target rebuilt the local handle and preserved exact
  symmetric opposition;
- `重置偏移` retained edited local geometry and restored identity transform;
- negative scale input clamped to `0.05`;
- after insertion, `重置` restored the original four-anchor snapshot, pivot and
  identity transform;
- capture completed with no console or page errors.

Quality gates after the main implementation:

```bash
npm run typecheck
npm run lint -- --quiet
git diff --check
```

All passed.

## Commit Protection

- Plan protection: `42f1a3c`.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

After the implementation commit, add `scripts/verify-liblib-batch39.py`,
generate only Batch 39 screenshots, inspect them once into
`SCREENSHOT_ANALYSIS.md`, then run Batch 35-39 regressions and repository
quality gates. Preserve Batch 38 selectors and do not stage verifier-regenerated
historical screenshots.
