# LibTV Media Ingress And Resource Lifecycle Research Plan

> Status: `ACTIVE` / `DOCUMENTATION_ONLY`.
>
> Scope: study Open Canvas media ingress and resource-lifecycle methods, then translate the useful parts into implementation-ready guidance for the ordinary LibTV clone route.
>
> Baselines: clone `bc8add1`; Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: no changes to `src/`, tests, FrameOS, Director runtime, either submodule or either source website.

## 1. Problem

The repository already distinguishes repo paths, remote URLs, embedded data URLs and session blob URLs after they enter node data. It also defines async result transfer, delete-time resource diagnostics and portable-document rejection. It does not yet have one authority for the earlier and longer lifecycle:

```text
user/file/asset choice
  -> classify and validate
  -> inspect local metadata
  -> acquire temporary preview lease
  -> materialize or upload durable media
  -> project media into one graph transaction
  -> retain through copy/history/save
  -> release after all graph/history/session references disappear
```

Without that authority, a visual upload control can appear source-like while still producing a non-restorable graph, leaking object URLs, accepting inconsistent media, losing undo semantics or committing stale upload results into the wrong canvas generation.

Open Canvas is useful because its fixed implementation contains a concrete file-input path, whole-canvas drop path, asset-picker boundary, metadata probes, server upload validation, content-addressed keys and node projection. It is a method and counterexample source, not proof of LibTV product behavior.

## 2. Existing Authorities To Compose

| Authority | Owns | This study must not duplicate |
|---|---|---|
| [`LibTVNodeDataIdentity.contract.md`](../research/components/LibTVNodeDataIdentity.contract.md) | `MEDIA_LOCATOR` field role and locator classes | copy/import field transformation policy |
| [`LibTVGraphDocument.contract.md`](../research/components/LibTVGraphDocument.contract.md) | portable document and media-reference rejection | document codec and migration |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | delayed-result freshness, transfer/release and one graph commit | generic async completion authority |
| [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | delete impact, history reachability and cleanup delegation | destructive graph command planning |
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | drop-point conversion and multi-item placement | coordinate conversion and viewport ownership |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../research/LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph/history command boundaries | graph transaction taxonomy |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas identity/generation and switch/delete isolation | project/canvas lifecycle |

The new authority begins when an ingress intent acquires bytes or an existing asset reference. It ends by delegating accepted graph projection, document portability and destructive cleanup to the authorities above.

## 3. Research Questions

1. Which ingress surfaces exist in fixed Open Canvas: file input, canvas drop, existing asset, edited-image export, text file and audio upload?
2. Which ingress surfaces actually exist in the current LibTV clone, and which visible controls are placeholders only?
3. How are MIME, filename extension, size, emptiness, dimensions, duration and remote response validated on client and server?
4. When is a placeholder node created: before validation, after validation, after upload or only at final commit?
5. What identity survives the pipeline: local file identity, digest, storage key, asset ID, stable URL, thumbnail URL and node field?
6. Which object URLs are short metadata-probe leases, component preview leases or graph-owned locators?
7. How should cancel, failure, retry, duplicate delivery, canvas switch, node delete and stale completion converge?
8. How do multi-file drop ordering, partial success and history compose with the viewport placement contract?
9. Which media bytes remain reachable through current graph, history, clipboard, open editor, async operation or exported document?
10. What can the frontend prototype faithfully implement without pretending to own a backend asset store?
11. Which observed Open Canvas choices are reusable methods, and which are implementation gaps that LibTV should explicitly avoid?
12. Which LibTV source-site upload, drop, asset-library and retry behaviors remain unknown and need later read-only browser evidence?

## 4. Initial Static Findings To Verify

These are working observations, not final conclusions:

- Open Canvas validates file inputs before upload, but whole-canvas drop creates an empty node before strict media validation and leaves an error node on failure.
- Drop classification accepts known filename extensions as a fallback, while the downstream image/video/audio creators enforce MIME lists; the two gates can disagree.
- Image dimensions and video duration use short-lived object URLs when browser-native metadata APIs need them, and those URLs are revoked on success/error.
- Image/video upload APIs validate type, emptiness and byte limits again, then derive a digest-based storage key and report deduplication.
- Multi-file drop awaits each item in order; it is neither one atomic graph transaction nor parallel upload.
- The local Open Canvas asset-picker dialog is a declared unavailable boundary, so its type shape is not evidence of a working shared asset library.
- Current LibTV Shot Breakdown uses a component-local `blob:` preview and writes only filename/mock duration into graph data; the Add Node upload action and picture replacement upload are prototype placeholders.
- Current Director creates browser-owned blob/data locators, but its resource handoff belongs to existing Director/async contracts rather than ordinary media ingress.

The dated audit must confirm exact paths and separate `OPEN_CANVAS_FACT`, `CLONE_FACT`, `INFERENCE`, `CLONE_DECISION` and `SOURCE_UNKNOWN`.

## 5. Evidence Queue

### 5.1 Fixed Open Canvas

Read and record exact paths for:

- file-input accept lists and size budgets;
- image dimension and video duration probes;
- upload request/response shapes and error translation;
- storage-provider validation, digest key, existence check and deduplication;
- canvas drag-depth UI, file classification, drop placement and sequential processing;
- placeholder-node timing and success/error projection;
- text and audio import asymmetries;
- image-editor export upload;
- asset picker and media-history normalization;
- graph serialization/copy behavior for uploaded locators;
- cleanup, cancellation, retry and stale-result gaps.

Candidate evidence IDs: `OC-061..070`.

### 5.2 Current LibTV Clone

Read and record exact paths for:

- Add Node resource actions;
- Shot Breakdown upload/preview/unmount cleanup;
- picture replacement and history selection placeholders;
- image/video/audio node media fields and default repo assets;
- Director model import, capture and animation-export resource paths;
- graph history/copy/delete treatment of media strings;
- canvas switch/delete behavior for component-local previews;
- any route-wide drop, paste-file, asset registry, upload or progress owner;
- FrameOS-only media behavior that must not be generalized into LibTV.

Candidate issue prefix: `LIBTV-MIR-*` (`Media Ingress And Resource`).

### 5.3 LibTV Source-Site Unknowns

Prepare a later read-only evidence script for:

- invalid type and oversize file response;
- upload placeholder timing and progress surface;
- cancel/retry/delete-during-upload behavior;
- same file added twice and multi-file drop behavior;
- source asset-library selection and locator reuse;
- canvas switch during upload;
- refresh/save portability of uploaded media;
- whether failed ingress leaves, removes or rolls back a node.

No source mutation or paid/provider operation is authorized in this batch.

## 6. Planned Deliverables

| Deliverable | Lifecycle | Purpose |
|---|---|---|
| `docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md` | dated reference | fixed Open Canvas/clone facts, asymmetries and ranked gaps |
| `docs/research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md` | stable guide/reference | ingress envelope, state machine, leases, identity, projection and disposal |
| `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` | fixture design | deterministic synthetic files, fake upload resolver and observable lease ledger |
| `LIBTV-VR-021` | verifier design | pure validation/lifecycle checks plus focused browser traces |
| `OC-PATTERN-11` / `OC-ADOPT-024` / `OC-BP-011` | Open Canvas translation | reusable method, adoption boundary and implementation slices |
| `OC-TR-017` / `LIBTV-TR-043` / `DEC-037` / `LIBTV-UIX-21` | governance | traceability, decision and UI/UX mapping |

IDs are reserved by this active plan but become authoritative only when their target documents are written and indexed.

## 7. Work Sequence

1. Finish authority-overlap audit and record the precise ownership boundary.
2. Extract fixed Open Canvas ingress/resource call sites into a dated evidence table.
3. Extract current LibTV visible controls, actual byte ownership and graph projections.
4. Build one cross-surface state matrix: intent, validating, probing, materializing, committed, failed, canceled and stale.
5. Define resource classes and reachability owners without inventing a backend asset service.
6. Rank visible fidelity gaps separately from correctness and portability gaps.
7. Write the formal contract only after the static audit proves the missing authority.
8. Define deterministic fixture/verifier designs without modifying runtime or tests.
9. Sync Hub -> Guide -> Reference navigation and Open Canvas adoption/handoff/governance chains.
10. Run documentation verification and diff checks; commit and push each key documentation milestone.
11. Promote this plan to the dated Open Canvas research history when the batch closes.

## 8. Contract Topics To Resolve

The formal contract must make explicit decisions for:

- ingress intent and immutable operation identity;
- local file descriptor versus bytes versus durable asset reference;
- validation order and client/server trust boundary;
- metadata probe lease and preview lease ownership;
- placeholder-first versus commit-on-success UI policy;
- progress/error/retry projection;
- multi-file cohort and partial-success policy;
- locator materialization and portability class transition;
- final graph transaction and history cardinality;
- canvas generation/node existence stale checks;
- copy/import/export and clipboard behavior;
- current graph/history/editor/operation reachability;
- exact-once transfer/release and object URL revocation;
- prototype-safe behavior when no upload backend exists.

## 9. Stop Conditions

Stop an evidence path when it would require:

- modifying clone runtime, tests or fixtures;
- changing/installing dependencies or files in the Open Canvas submodule;
- uploading private media or mutating a source-site project;
- invoking a paid/provider generation or storage action;
- claiming LibTV parity from Open Canvas behavior;
- inventing backend asset deletion, billing, account or collaboration semantics;
- treating a `blob:` URL as durable merely because it renders in the current BrowserContext.

Record the unknown, continue with the next safe evidence path and preserve the distinction between current facts and recommended contracts.

## 10. Acceptance Criteria

This research batch is complete when:

- every current ingress surface is classified as functional, local-preview-only, mock or unavailable;
- validation/probe/materialization/projection order is explicit per media family;
- temporary preview leases and durable locators have separate owners;
- placeholder, failure, retry, cancel and stale completion policies are deterministic;
- multi-file drop composes with placement/history without hidden partial mutation;
- graph/history/editor/operation reachability governs release decisions;
- the new contract delegates instead of duplicating async, viewport, document and delete authorities;
- a no-backend prototype path remains honest and visually useful;
- fixture `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` and verifier `LIBTV-VR-021` have deterministic cases;
- Open Canvas methods and counterexamples have explicit adoption decisions;
- agent navigation, traceability and implementation handoff remain discoverable;
- documentation checks pass and no runtime/submodule/WIP path is modified.

## 11. Next Action

Complete the fixed-code and clone-code evidence extraction, then publish the dated static audit before drafting the normative lifecycle contract.
