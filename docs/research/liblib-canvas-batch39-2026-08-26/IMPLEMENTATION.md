# Batch 39 Implementation Log

> Status: evidence and implementation plan complete; product work pending.

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

## Commit Protection

- Plan protection: pending.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

After the plan commit, start in `directorMotionMath.ts`: add tested pure
forward/inverse transforms before extending the store or R3F. Preserve Batch
38 selectors and do not stage verifier-regenerated historical screenshots.
