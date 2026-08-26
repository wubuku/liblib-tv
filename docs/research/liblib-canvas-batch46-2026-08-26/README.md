# LibTV Canvas Replication Batch 46

> Director Desk camera screenshot gallery, preview viewer and bulk canvas
> return.

## Status

Evidence and implementation plan protected on 2026-08-26. The current clone
gap is bounded; implementation follows after this protection commit.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): current LibTV locale and fixed
   upstream facts.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): the existing
   StoryAI Director Desk capture panel and state model.
3. [`PLAN.md`](PLAN.md): value choice, scope, selectors and acceptance gates.
4. [`DIRECTOR_CAPTURE_GALLERY.spec.md`](DIRECTOR_CAPTURE_GALLERY.spec.md):
   clone contract and evidence boundaries.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): implementation and verification
   history.

## Why This Batch

Batch 45 made group authoring a mature Director slice. The next high-value
workflow is managing the screenshots that the Director already creates:

```text
capture several compositions
  -> inspect a camera-grouped gallery
  -> open a large preview
  -> send one or all to the canvas
  -> clear local screenshot records without deleting returned graph nodes
```

This improves a real authoring workflow without changing the R3F renderer,
timeline model or React Flow ownership.

## Evidence Discipline

- **LibTV current source fact:** locale keys prove the screenshot gallery
  vocabulary and empty/clear/bulk-send/close states.
- **Fixed upstream fact:** commit `8c8bd361790be4d37158a7430365e65546e358fe`
  contains a camera screenshot tab, grouped thumbnail grid, full-screen
  viewer and bulk actions.
- **Clone decision:** the current clone keeps a flat serializable capture list
  and derives camera groups from `cameraName`, because its fixture has one
  active camera and does not yet have a separate camera-document schema.
