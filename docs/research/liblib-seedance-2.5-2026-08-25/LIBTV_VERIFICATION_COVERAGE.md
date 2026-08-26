# LibTV Clone Verification Coverage

> Purpose: map current source-backed contracts to the clone's existing browser checks. This document identifies test gaps; it does not authorize code or test-script changes.
>
> Current cross-route implementation/research priority is maintained in
> [`../LIBTV_UIUX_PARITY_BACKLOG.md`](../LIBTV_UIUX_PARITY_BACKLOG.md); this file
> remains the detailed image/AutoLink/video verification-coverage view.

## 1. Executive Summary

The existing LibTV checks are valuable historical implementation checks, but they are not yet a complete regression suite for the current source contract:

- Batch 9 covers node-centered lower panels, pan/zoom follow, natural clipping and the old `900.5x49` toolbar baseline. Its top-gap assertion is a historical clone contract, not the current source formula.
- Batch 10 covers the five original image panel content states and the clone's old AutoLink popover. Its AutoLink assertions must be replaced, not silently preserved, when structured inline mentions are authorized.
- Batches 21-33 cover the clone's Seedance video workflow in increasing detail, but source-ready video toolbar behavior, real segment replacement and live frame-analysis results remain unverified because the shared source project has no safe ready-video fixture.
- Batch 52 now covers the current toolbar action-set width/order and image Preview; Batch 53/54 cover the empty annotate and element-edit replacement states. No current clone script covers rotate boundary, layer separation or non-empty active-tool semantics.
- No current clone script covers the source AutoLink contract: global preference, connected/reference candidate scope, ghost spans, single/batch keyboard acceptance, IME/race guards and graph/mention transaction consistency.

The next authorized coding batch should create new focused checks alongside the historical scripts. It should not rewrite old evidence until the expected contract is explicitly versioned.

## 2. Coverage Matrix

| Contract | Existing evidence/check | Coverage | Correct interpretation | Required future check |
|---|---|---|---|---|
| Standard selected image has one top toolbar and one bottom panel | `scripts/verify-liblib-batch9.py`, `batch10.py` | Partial | Current clone lifecycle and five panel states are covered | Keep lifecycle check; add current action-set/version fixture |
| Toolbar and panel share node-center anchor | Batch 9 | Good for center | Center alignment and edge clipping are covered on clone | Assert both surfaces from one viewport snapshot at each selected zoom |
| Bottom panel gap is `16 * zoom` | Batch 9 | Good | Clone lower-panel compensation is covered | Keep; add explicit source-vs-clone comment and panel height variants |
| Current source top gap is `10 + 24 * zoom` | No clone script | Missing | Existing Batch 9 `16px` top assertion is obsolete for current source fidelity | Add a versioned current-toolbar test after implementation authorization |
| Current source toolbar is content-sized `1092.5x49` | Batch 52 focused verifier | Good for bounded clone slice | Source CSS remains versioned evidence; five high-risk clone actions are disabled placeholders | Reinspect only after source action-set change |
| Active image tool replaces standard double overlay | Source live/bundle action matrix + Batch 53/54 | Good for empty replacement states | Annotate and element-edit empty states are covered; rotate/layer separation and non-empty save/record semantics remain unverified | Add disposable fixture only for non-empty/high-risk states |
| Preview is page-level read-only overlay | Batch 52 focused verifier and runtime audit | Good for bounded clone slice | Single image, local fixture, no remote media history | Add only if multi-media navigation or source behavior changes |
| Annotate empty state | Batch 53 focused verifier and source contract | Good for bounded clone slice | Empty toolbar/canvas replacement is covered; stroke/save/result semantics remain unverified | Add disposable fixture only for non-empty dirty/save state |
| Element edit empty state | Batch 54 focused verifier and source contract | Good for bounded clone slice | Empty toolbar/stage/record replacement is covered; object record/generate/result semantics remain unverified | Add disposable fixture only for non-empty record state |
| Rotate entry may mutate graph | Source live fixture + immediate undo | Missing | Must not assume pure local CSS action | Test only on disposable clone fixture with graph-count assertion |
| Layer separation async composition | Source bundle only | Missing | High-risk path has no safe live evidence | Require disposable fixture and explicit task-boundary contract |
| Five image panel heights/prompts/references | `scripts/verify-liblib-batch10.py` | Good for historical states | Explicit `191/211/274` clone data contract is covered | Keep as compatibility regression |
| AutoLink global preference | Source bundle/DOM only; clone has local state | Missing | Batch 10 does not cover source semantics | Add cross-image/video persistence and reload check |
| AutoLink candidate pool | Source bundle/DOM only | Missing | Fixed clone candidates are intentionally not source-faithful | Add graph/reference-driven candidate fixture |
| AutoLink ghost before acceptance | No script | Missing | No committed Prompt/reference/graph mutation should occur | Add DOM marker and state immutability assertions |
| AutoLink click/Tab/Shift+Tab | No script | Missing | Current clone has one button and no inline editor | Add single and batch acceptance tests |
| AutoLink Escape/edit/blur cleanup | No script | Missing | Stale ghost cleanup is untested | Add preservation checks for user text and committed badges |
| AutoLink IME/stale-result guards | No script | Missing | Reliability contract is entirely untested | Add deterministic delayed-result fixture |
| AutoLink graph/reference/mention transaction | No script | Missing | Current image panel only changes local references | Add success/failure atomicity and ordinal projection checks |
| Seedance model/mode/normal parameters | Batches 21-22 | Good | Clone UI and local formulas are covered | Keep; do not promote product numbers to permanent model facts |
| Segment reshoot filmstrip and five-range cap | Batch 23 | Good for clone prototype | Local UI closure is covered; source result replacement is not | Add source-ready fixture only when available |
| Shot breakdown node/results | Batch 24 | Good for clone prototype | Structure and persistence are covered; source result state remains article/bundle evidence | Add source status mapping if live fixture becomes safe |
| Long-video process graph | Batch 33 | Good for clone prototype | Local 12-node/22-edge process and history are covered | Keep read-only process boundary; do not fake provider progress |
| Ready-video processing toolbar | Batches 27-32 use clone fixtures | Partial | Individual clone tools are covered; source ready toolbar order is not | Add source-shaped ready-video toolbar contract |
| Director preset camera motion | `docs/research/liblib-canvas-batch44-2026-08-26/`, `scripts/verify-liblib-batch44.py` | Good for bounded clone slice | Source locale proves entry/modes/names/guards; generated math, timing and panel CSS remain clone calibration | Reinspect only with authenticated source preset state or a new source artifact |

## 3. Historical Tests That Need Explicit Version Labels

### Batch 9

`verify-liblib-batch9.py` currently asserts:

```text
toolbar gap = 16px
toolbar width = 900.5px
toolbar height = 49px
```

The height remains compatible, but the width and top-gap values describe the 2026-08-25 clone/source snapshot. The current source evidence is:

```text
toolbar width = 1092.5px
toolbar gap = 10 + 24 * zoom
panel gap = 16 * zoom
```

The panel assertion can remain a current contract. The toolbar assertions require a versioned replacement after the clone is authorized to adopt the current action set.

### Batch 10

`verify-liblib-batch10.py` asserts the fixed clone behavior:

- AutoLink exists only when Prompt is non-empty and references are empty;
- a separate popover says `匹配到陈默、咖啡 2 个画布素材`;
- one `引用` button accepts both entries;
- ordinary string tokens are prepended to the textarea.

These assertions are useful for reproducing the historical clone snapshot, but contradict the current source AutoLink contract. They should be retained as historical evidence until a replacement is implemented and verified; they must not be extended with more fixed candidates.

## 4. Required Test Layers After Authorization

### Layer A: Pure contract checks

Use deterministic data and pure helpers to check:

- screen/flow positioning formulas;
- toolbar and panel center/gap calculations;
- reference ordinal projection from stable node IDs;
- AutoLink stale-result acceptance rules;
- graph/reference/mention transaction outcomes.

These checks should not require a live source login or a real provider.

### Layer B: Local browser fixture checks

Use disposable local clone fixtures for:

- standard image/video overlay lifecycle;
- current action-set and active-tool replacement;
- preview, annotate empty and element-edit empty states;
- AutoLink ghost, keyboard, IME and competing-popover behavior;
- ready-video segment reshoot and analysis result states;
- graph count, selection, undo/redo and mobile clipping.

Every fixture must be reset between tests. Tests that create derived nodes must assert the expected graph delta and restore through a transaction or a fresh page.

### Layer C: Source observation checks

Source-site observations should remain separate from clone regression scripts. They may record DOM, computed rects, bundle strings and screenshots, but must not type Prompt text, accept suggestions, toggle settings, upload, download, generate or save on the shared research project.

## 5. Safe Research Queue

| Queue item | Can proceed without coding authorization? | Safe prerequisite |
|---|---|---|
| Reconcile existing script names and docs with historical/current labels | yes | Documentation-only commit |
| Add pure formula examples to contracts | yes | No source interaction |
| Inspect source ready-video toolbar through current DOM | only if a safe ready fixture is already visible | No click that can submit or mutate |
| Verify source AutoLink ghost by typing | no | Disposable source project or explicit user authorization |
| Verify source rotate/layer separation dirty paths | no | Disposable source project and mutation permission |
| Replace Batch 9/10 assertions | no | Current clone implementation authorization plus new fixtures |

## 6. Current Decision

Until coding is explicitly authorized:

1. Keep Batch 9 and Batch 10 as historical clone regressions.
2. Do not claim they cover the current source toolbar or AutoLink contracts.
3. Do not weaken their assertions merely to make a future implementation pass.
4. Add new tests only after the relevant source-backed component contract and implementation slice are approved.
5. Keep `npm run check` and `python3 scripts/verify-docs.py` as repository-level gates; this research batch does not run a code build because it makes no code change and other developer WIP is active.

## 7. Related Contracts

- [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)
- [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)
- [`LIBTV_FEATURE_GAP_MATRIX.md`](LIBTV_FEATURE_GAP_MATRIX.md)
- [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)
- [`LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)
- [`HARNESS.md`](../../HARNESS.md)
