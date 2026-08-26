# Batch 47 Source Evidence

## 1. Existing Project Evidence

Observation date: 2026-08-26.

The current project already records the relevant evidence in:

- `docs/research/liblib-canvas-batch34-2026-08-26/SOURCE_EVIDENCE.md`;
- `docs/research/liblib-canvas-batch34-2026-08-26/UPSTREAM_SCREENSHOT_ANALYSIS.md`;
- `docs/research/liblib-canvas-batch34-2026-08-26/BORROWABLE_UX.md`;
- `docs/research/liblib-canvas-batch45-2026-08-26/MATURITY_ASSESSMENT.md`;
- `docs/research/liblib-canvas-batch46-2026-08-26/MATURITY_ASSESSMENT.md`.

Those records establish:

- Director is an independent R3F workbench inside the LibTV clone;
- the upstream project is a LibTV-oriented replication reference, not current
  LibTV source truth;
- the upstream model catalog depends on an external sibling `模型库/`
  directory;
- the external catalog and asset licenses are not safe to copy;
- the current clone has serializable `DirectorObject` prop primitives but no
  model-library state or add-asset transaction.

## 2. Directly Reusable Interaction Signals

The evidence supports a bounded model-library interaction:

```text
viewport toolbar trigger
  -> floating model-library dialog
  -> category tabs
  -> scrollable thumbnail cards
  -> add selected item to the live scene
```

The evidence does not prove:

- that the current LibTV production runtime uses the exact upstream panel;
- the full current LibTV model catalog or item names;
- remote asset persistence, download behavior or provider APIs;
- exact source panel pixels, dimensions or breakpoint values;
- that environment assets share the same schema as model props.

## 3. Batch Boundary

This batch will implement only a clone-owned local proxy catalog. The proxy
catalog exists to make the UI and scene transaction testable without importing
unresolved external assets.

The following remain explicit future work:

- real FBX/OBJ loading;
- environment/panorama asset authoring;
- local file import persistence;
- remote library/provider integration;
- asset deletion and scene-instance cleanup;
- exact current LibTV runtime re-observation if authenticated source evidence
  becomes available.
