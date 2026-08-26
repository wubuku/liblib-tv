# LibTV Canvas Replication Batch 48

> Director Desk `我的模型`: local FBX/OBJ import, persisted library cards,
> re-add to scene and instance cleanup.

## Status

Plan and source-boundary protection on 2026-08-26. The bounded implementation
closed on 2026-08-26; implementation and verification details are in
[`IMPLEMENTATION.md`](IMPLEMENTATION.md).

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): evidence and non-claims.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): fixed StoryAI
   implementation details.
3. [`PLAN.md`](PLAN.md): value choice, scope, acceptance gates and selectors.
4. [`DIRECTOR_LOCAL_MODEL_LIBRARY.spec.md`](DIRECTOR_LOCAL_MODEL_LIBRARY.spec.md):
   clone behavior contract.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): implementation and verification
   history.
6. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md): one-time visual reading
   of the generated clone states.
7. [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md): closed contracts,
   deliberate non-claims and next handoff boundary.

## Why This Batch

Batch 47 added the source-shaped model-library panel and a deliberate
`我的模型` empty state. The fixed upstream implementation shows the next
high-value step: local models can be imported into that tab, survive refresh,
be added to the scene later and be removed with their scene instances.

The clone will implement that workflow with browser-local data and owned proxy
geometry. It will not claim to parse or ship production model files.

## Evidence Discipline

- The local-import and persistence behavior is a fixed upstream code fact.
- The current LibTV production runtime is not inferred from that upstream code.
- Local model cards, visual mapping and proxy geometry are clone-owned
  calibration.
- Data URLs are used only as a browser-local prototype storage boundary.
