# Batch 48 Implementation Log

> Status: complete on 2026-08-26. Focused browser verification and source
> checks passed; repository-wide regression is recorded in the closeout
> section below.

## Protection Context

- `SOURCE_EVIDENCE.md` records the fixed upstream local-import behavior and
  explicit non-claims;
- `UPSTREAM_ARCHAEOLOGY.md` records the relevant loader, toolbar, store and
  test boundaries;
- `PLAN.md` records value choice, scope, acceptance gates and selectors;
- `DIRECTOR_LOCAL_MODEL_LIBRARY.spec.md` records the clone contract.

## Progress

- [x] source evidence and asset boundary recorded
- [x] upstream local-import/persistence implementation excavated
- [x] Batch 48 scope and selectors protected
- [x] local descriptor collection and defensive persistence
- [x] multiple-file import and populated `我的模型` cards
- [x] re-add and delete-linked-instances transaction
- [x] focused Playwright and screenshot ledger
- [x] cross-batch regression and repository gates
- [x] maturity assessment and commit/push

## Code Surface

- `src/components/director/directorLocalModelImport.ts`
  - accepts multiple `.fbx`/`.obj` files;
  - reads each file as a browser data URL;
  - maps the filename to an owned proxy visual and color.
- `src/store/directorStore.ts`
  - owns the local descriptor collection and clone-specific storage key;
  - defensively hydrates valid records from `localStorage`;
  - removes linked local proxy objects and their timeline/path state;
  - preserves a serializable local source/file-name boundary on scene props.
- `src/components/director/DirectorViewport.tsx`
  - enables the empty-state and populated-state `本地导入` actions;
  - renders local cards, re-add and delete controls;
  - retains the existing model-library dismissal and responsive geometry.
- `scripts/verify-liblib-batch48.py`
  - covers empty/import/populated/re-add/delete/refresh states;
  - checks invalid extension filtering, localStorage shape, R3F pixels,
    desktop/mobile bounds and browser errors.

## Focused Verification

Command:

```bash
/Users/yangjiefeng/.pyenv/versions/3.10.6/bin/python3 \
  scripts/verify-liblib-batch48.py
```

Result:

```text
Batch 48 director local-model-library verification passed.
```

The verifier specifically proves:

- the empty state exposes one multiple-file input;
- `.fbx` and `.obj` files become two cards while `.gltf` is ignored;
- card descriptors persist as the bounded clone-owned localStorage shape;
- a local card creates a selected `prop` and changes the R3F pixels;
- re-adding the same card creates a second linked instance;
- deleting the card removes both linked instances and leaves the other card;
- a fresh mobile browser context restores the remaining card from storage;
- deleting the final card returns to the empty state and clears storage;
- Escape/outside dismissal, viewport bounds and browser errors remain clean.

## Screenshot Ledger

The one-time visual reading is recorded in
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md). Do not reopen the contact
sheet unless a new question is not answered by that ledger.

## Repository Gates

Final command sequence and results:

```text
Batch 48 focused Playwright: passed
Batch 35-48 serial regression: passed
npm run typecheck: passed
npm run lint: passed (9 pre-existing warnings, 0 errors)
npm run docs:check: passed (401 Markdown files, 1450 local targets)
npm run check: passed
git diff --check: passed for Batch 48 source/docs/script files
```

The first attempted cross-batch run stopped at the old Batch 47 assertion that
expected a disabled `本地导入` placeholder. Batch 48 intentionally supersedes
that placeholder. The Batch 47 verifier was made deterministic by clearing the
clone-owned local-model storage and now asserts the superseding enabled entry
point; the complete Batch 35-48 rerun passed.

## Interruption Handoff

Start with `PLAN.md`, then implement only browser-local descriptors and the
existing R3F proxy mapping. Do not add a real FBX/OBJ loader or copy upstream
assets.
