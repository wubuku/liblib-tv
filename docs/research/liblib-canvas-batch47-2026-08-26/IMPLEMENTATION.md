# Batch 47 Implementation Log

> Status: complete on 2026-08-26. Focused browser verification and source
> checks passed; repository-wide regression is recorded in the closeout
> section below.

## Protection Context

- current project evidence is recorded in `SOURCE_EVIDENCE.md`;
- fixed upstream model-library behavior is recorded in
  `UPSTREAM_ARCHAEOLOGY.md`;
- value choice, scope, selectors and acceptance gates are recorded in
  `PLAN.md`;
- the bounded clone contract is recorded in
  `DIRECTOR_MODEL_LIBRARY.spec.md`.

## Progress

- [x] current evidence and asset-license boundary recorded
- [x] fixed upstream model-library implementation excavated
- [x] Batch 47 value choice and scope protected
- [x] proxy catalog and serializable asset mapping
- [x] viewport toolbar model-library panel
- [x] add-to-scene prop transaction and R3F proxy
- [x] focused Playwright and screenshot ledger
- [x] cross-batch regression and repository gates
- [x] final maturity/stable docs and commit/push

## Code Surface

- `src/components/director/directorModelLibrary.ts`
  - owns five source-shaped category labels and 12 clone-owned proxy items;
  - keeps proxy descriptors serializable and independent of upstream model files.
- `src/store/directorStore.ts`
  - adds `library` to the Director primitive union;
  - creates and selects ordinary `prop` objects with stable library metadata;
  - clears group/path selection and places new props beside the existing scene.
- `src/components/director/DirectorViewport.tsx`
  - adds the toolbar trigger, floating category panel, card actions and empty
    `我的模型` state;
  - renders bounded R3F bottle/chair/lamp/plant/box proxy geometry;
  - closes the panel on Escape/outside pointer and keeps it inside desktop and
    mobile viewport bounds.
- `src/components/director/directorCameraFollow.ts`
  - accepts library props as camera target candidates with a bounded focus height.
- `scripts/verify-liblib-batch47.py`
  - covers category switching, insertion metadata, tree/Inspector continuity,
    WebGL pixel change, empty state, dismissal, responsive bounds and errors.

## Interruption Handoff

Read [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md) before selecting the
next batch. The bounded model-library slice is complete; do not expand it into
real FBX/OBJ loading without a new source/asset/license decision.

Batch 48 later enabled the previously deferred local-import entry point. Its
current verifier keeps this catalog slice deterministic by clearing the
clone-owned local-model storage before testing and asserts the superseding
enabled empty-state action.

## Focused Verification

Command:

```bash
/Users/yangjiefeng/.pyenv/versions/3.10.6/bin/python3 \
  scripts/verify-liblib-batch47.py
```

Result:

```text
Batch 47 director model-library verification passed.
```

The verifier covers:

- five reachable category tabs and category-specific card sets;
- panel placement above the toolbar and inside the viewport;
- one-card insertion with `libraryAssetId`, category and visual metadata;
- selected tree row, `prop` Inspector and transform fields;
- non-blank WebGL output and pixel change after insertion;
- `我的模型` empty state;
- Escape/outside-pointer close without closing the Director workspace;
- desktop/mobile no-overflow and zero console/page/request errors.

## Screenshot Ledger

The one-time visual reading is recorded in
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md). Do not reopen the contact
sheet unless a new question is not answered by that ledger.

## Repository Gates

Final command sequence and results:

```text
Batch 35-47 serial regression: passed
npm run docs:check: passed (392 Markdown files, 1406 local targets)
npm run check: passed (9 pre-existing lint warnings, 0 errors)
git diff --check: passed
```

The production build also reports the existing multiple-lockfile workspace-root
warning from Next.js; it does not fail the build.
