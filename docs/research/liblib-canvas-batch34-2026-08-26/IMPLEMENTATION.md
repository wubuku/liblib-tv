# Batch 34 Implementation Log

## 1. Protection And Source Setup

- Batch 33 implementation commit: `2bf1617`
- Batch 34 plan protection commit: `b9895c7`
- Batch 34 research commit: `e1d20ef` (pushed to `origin/master`)
- Batch 34 handoff metadata commit: `84a7c59` (pushed to `origin/master`)
- Submodule path: `research/upstream/storyai-3d-director-desk`
- Submodule commit: `8c8bd361790be4d37158a7430365e65546e358fe`
- Submodule branch at inspection time: `main`
- Parent repository branch: `master`

## 2. Research Actions Completed

- [x] Read the upstream README, package metadata and MIT license.
- [x] Inspected the source tree and identified app/layout, canvas, panels, store,
  schema, runtime, loaders, IO and style boundaries.
- [x] Inspected the project schema and camera/object relationship.
- [x] Inspected persistence, undo batching, clipboard and scoped session logic.
- [x] Inspected object tree, inspector routing, camera capture and host bridge.
- [x] Inspected model catalog and recorded the external `模型库/` dependency.
- [x] Inspected the included mannequin license notice.
- [x] Recorded high-value borrowable UX and current-project portability risks.
- [x] Confirmed fixed-source `LibTV-style` targeting and canvas/director host semantics.
- [x] Extracted current LibTV timeline, motion-path, animation-export and phone-camera scope.
- [x] Recorded all seven upstream README screenshots in a durable recognition ledger.
- [x] Finish upstream `npm ci`, `npm test` and `npm run build` result.
- [x] Run parent `npm run docs:check` and `git diff --check`.
- [x] Run parent `npm run check`.

## 3. Static Findings

The fixed source contains:

- 34 test files;
- 299 statically detected `it`/`describe` declarations;
- one R3F viewport plus a separate R3F gizmo canvas;
- one Zustand domain/UI store with versioned project data;
- four context-sensitive right inspectors;
- five semantic object-tree groups;
- local JSON/data-URL persistence and a same-origin host bridge.

The upstream README's `304 / 312` test result with 8 failures matches the fixed
checkout after running `npm test`.

## 4. Result

The corrected highest-value borrowing decision is:

> Treat the upstream repository as an existing LibTV director-desk replication.
> Port its MIT-licensed static R3F editor slice into a dedicated current-project
> director boundary, then add the current LibTV source's missing timeline,
> motion-path, animation-export and phone-camera layers.

No upstream source, model, texture or screenshot has been copied into `src/` in
Batch 34. A later implementation batch may adapt MIT-licensed code while
preserving its notice; model and catalog assets remain excluded.

## 5. Verification Result

Commands run from the fixed submodule checkout on 2026-08-26:

```text
npm ci          passed; 278 packages installed
npm run build   passed; Vite production build completed
npm test        304 passed, 8 failed, 312 total, 34 test files
```

The eight failures are recorded in
[`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md). They expose upstream maintenance
boundaries around the external model catalog, viewport geometry/style assertions
and one pose preset; they do not change the product-facing borrowing priority.

## 6. Parent Repository Integration Verification

Adding a nested Vite/R3F project exposed a repository-boundary issue: the parent
ESLint and TypeScript glob patterns initially scanned the submodule's source,
tests and generated `dist/` files. The parent project now explicitly excludes
`research/upstream/**` in both [`eslint.config.mjs`](../../../eslint.config.mjs)
and [`tsconfig.json`](../../../tsconfig.json). The submodule remains independently
validated by its own toolchain.

Parent commands run on 2026-08-26:

```text
npm run docs:check   passed; 253 Markdown files, 597 local targets
git diff --check     passed
npm run check        passed
```

`npm run check` retains 9 existing lint warnings but no lint errors. Next build
also reports the repository's pre-existing multiple-lockfile workspace-root
warning; the application build and typecheck complete successfully.

## 5. Handoff

Next implementation batch should begin from:

- [`LIBTV_DIRECTOR_EVIDENCE.md`](LIBTV_DIRECTOR_EVIDENCE.md) source scope;
- [`REPLICATION_REFERENCE_MATRIX.md`](REPLICATION_REFERENCE_MATRIX.md) reuse boundary;
- [`BORROWABLE_UX.md`](BORROWABLE_UX.md) recommended slice;
- [`PORTABILITY_MATRIX.md`](PORTABILITY_MATRIX.md) architecture boundary;
- existing LibTV source evidence for shot/video/capture behaviors;
- a new implementation plan that ports the static R3F desk first and defines the
  selector, store, route, return transaction and browser verification contracts.
