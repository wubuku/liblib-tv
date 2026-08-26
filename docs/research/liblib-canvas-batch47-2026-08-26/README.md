# LibTV Canvas Replication Batch 47

> Director Desk model-library entry, category browsing, preview cards and
> local proxy-object insertion.

## Status

Plan/evidence protection on 2026-08-26. Implementation starts after this
context-protection commit.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): current project evidence and
   explicit non-claims.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): fixed StoryAI model
   library implementation.
3. [`PLAN.md`](PLAN.md): value choice, scope, acceptance gates and selectors.
4. [`DIRECTOR_MODEL_LIBRARY.spec.md`](DIRECTOR_MODEL_LIBRARY.spec.md): clone
   behavior contract.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): created after implementation and
   verification.

## Why This Batch

Batch 46 closed screenshot management. The next highest-value Director gap is
the source-shaped model-library entry point that lets a scene author browse a
small catalog and place an object into the live 3D scene.

The batch deliberately uses owned proxy assets:

```text
source-shaped categories and card interactions
  -> clone-owned fixture catalog
  -> add a serializable prop object
  -> select it in tree/Inspector and preserve transform continuity
```

## Evidence Discipline

- **Current LibTV evidence:** Batch 34 records the Director source/feature
  boundaries and warns that the upstream external model catalog is not
  self-contained.
- **Fixed upstream fact:** the StoryAI checkout contains a `模型库` toolbar
  panel with five tabs, catalog cards, `我的模型` empty state and an
  add-to-scene transaction.
- **Clone calibration:** proxy item names, category counts, card colors,
  generic R3F geometry and exact panel dimensions are owned by this prototype.

No external FBX, OBJ, thumbnail or unresolved third-party asset is copied.
