# LibTV Media Rendition, Aspect And Node Geometry Research Plan

> Status: `COMPLETE` / `HISTORICAL_CONTRACT` / `DOCUMENTATION_ONLY`.
>
> Scope: study how fixed Open Canvas and the current LibTV clone relate media intrinsic metadata, selected output identity, generation aspect/resolution, node frame geometry, React Flow measurement and per-surface fit/crop policy, then turn the useful methods and counterexamples into implementation-ready LibTV guidance.
>
> Baselines: clone `6aa92e8`; Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Stable authority: [`../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md) + [`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md). This file preserves execution history and does not compete with those documents.
>
> Authorization boundary: no changes to `src/`, tests, runtime fixtures, either submodule, FrameOS, Director behavior or either source website. Shared LibTV source remains read-only.

## 1. Problem

The repository already has strong contracts for node/overlay placement, media ingress, editor sessions and graph identity. It does not yet define which dimension or aspect value controls each media surface:

```text
local/source bytes
  -> intrinsic media width/height/duration
  -> stable media/output identity
  -> generation request aspect/resolution
  -> semantic node frame width/height
  -> React Flow measured rect
  -> canvas preview crop/fit/object-position
  -> detail/editor/thumbnail/export rendition
```

These values are related but are not interchangeable. A `1920x1080` image can be shown in a square node with `cover`, inspected in a modal with `contain`, referenced by a `1:1` generation setting and measured by React Flow as a larger card that includes metadata chrome. Treating all of them as one `width/height` pair can produce visible crop drift, wrong selection bounds, unstable overlay anchors, incorrect normalized media coordinates and misleading export labels.

Open Canvas is useful because its fixed implementation contains the complete conflict in one place:

- upload probes intrinsic image dimensions and maps them to the closest supported generation aspect ratio;
- image/video node cards use fixed type widths and derive preview height from the generation `aspectRatio`;
- node previews and output grids use `object-cover`, while the full-screen image viewer uses `object-contain`;
- media descriptors do not preserve intrinsic width/height;
- selected image/video output identity is normalized separately from the media URL;
- React Flow `measured` geometry is used for placement/overlay calculations, but passive measurement is not a user-resize contract;
- edited images can be appended and selected without visibly reconciling their new intrinsic ratio with the existing generation ratio.

The current clone likewise mixes graph node dimensions, image metadata labels, video resolution strings, Director export dimensions, fixed aspect wrappers and both `cover` and `contain`. The missing authority is therefore already relevant to the reported selected-node overlay positioning problem: overlay geometry may be mathematically correct while its node rect changed because media/chrome sizing follows an undeclared rule.

## 2. Authority Boundary

### 2.1 This study owns

- intrinsic media metadata and its provenance/confidence;
- selected media/output identity and per-output metadata;
- generation request aspect ratio and resolution as parameters, not DOM geometry;
- semantic node frame dimensions versus React Flow measured dimensions;
- passive content-driven measurement versus explicit product resize;
- per-surface rendition policy: `cover`, `contain`, crop position, letterbox and overflow;
- preview, detail, editor, thumbnail, filmstrip and export surface roles;
- media load/error/metadata-ready transitions that can change geometry;
- switching among outputs whose intrinsic ratios differ;
- geometry consequences for selection, handles, normalized media coordinates and overlays;
- source-evidence gates for exact LibTV crop, frame, object-position and resize behavior.

### 2.2 Adjacent authorities remain authoritative

| Authority | Owns | This study delegates |
|---|---|---|
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | coordinate domains, host/live viewport and placement | flow/client conversion and measured node anchor use |
| [`components/LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) | source-exact selected-node toolbar/panel geometry | overlay rect formulas and natural clipping |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) | bytes, validation, stable locators, leases and release | metadata probe operation/resource ownership |
| [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md) | editor baseline/draft/local history and commit | crop/annotate/editor session lifecycle |
| [`components/LibTVNodeDataIdentity.contract.md`](../components/LibTVNodeDataIdentity.contract.md) | semantic/reference/runtime field roles | media/output identity and portability classes |
| [`components/LibTVGraphDocument.contract.md`](../components/LibTVGraphDocument.contract.md) | portable graph schema and runtime exclusions | persisted node/media field boundary |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md) | semantic graph/history commands | accepted resize/output-selection command cardinality |
| [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) | source model/mode option projection | exact provider ratio/resolution option sets |
| [`ImagePreviewOverlay.spec.md`](../components/ImagePreviewOverlay.spec.md) | current image detail-overlay behavior | component-specific visual contract |

This study does not redefine the source overlay formulas and does not infer a resizable-node product feature from the presence of serialized `width/height` or React Flow measurement fields.

## 3. Working Model To Test

Every media-bearing node should be explainable using distinct authorities:

| Authority | Example | May change node DOM size |
|---|---|---:|
| `MEDIA_INTRINSIC` | decoded image `1808x1024`, video `1280x720` | no, unless an explicit frame policy consumes it |
| `MEDIA_OUTPUT` | selected image candidate 3 with its own identity/metadata | only through declared frame policy |
| `GENERATION_REQUEST` | `16:9`, `720P`, `2K` | only when the product declares request-driven frame geometry |
| `NODE_FRAME` | semantic graph frame `700x350` | yes |
| `NODE_MEASURED` | React Flow rect including current node shell/chrome | observation only; feeds anchors/selection |
| `SURFACE_RENDITION` | node=`cover`, detail=`contain`, thumbnail=`cover top` | changes visible crop, not media identity |
| `EDITOR_MEDIA_SPACE` | normalized or intrinsic coordinates used by marks/crops | no direct graph resize |
| `EXPORT_OUTPUT` | final encoded dimensions/aspect | no retroactive DOM authority without a command |

The central hypotheses are:

```text
intrinsic dimensions != generation settings
generation aspect != selected-output intrinsic aspect
node frame != React Flow measured rect
measured rect != user resize intent
cover crop != destructive media crop
detail contain != canvas-node rendition
```

## 4. Research Questions

1. Which Open Canvas paths probe intrinsic dimensions/duration, and where is that metadata discarded?
2. Does upload inference update only generation settings, or also media descriptors and node geometry?
3. Which value drives image/video preview aspect after upload, generation, edit-save and output switching?
4. Can image/video output histories contain candidates with different intrinsic ratios, and what happens when selection changes?
5. Which surfaces use `cover`, `contain`, explicit object position, clipping, letterbox or a fixed aspect wrapper?
6. Are node width/height values semantic graph state, serialization compatibility fields, CSS-derived measurement or explicit user-resize state?
7. Does Open Canvas expose a `NodeResizer`, resize handle or resize command, or only passive React Flow measurement?
8. Which dimensions are used to position Quick Add, selected toolbars/panels and context menus?
9. What happens before media metadata is ready, on decode failure and when a thumbnail has a different ratio from the full asset?
10. Which current clone node types keep graph frame and media aspect aligned, and which rely on `object-cover` to hide mismatch?
11. Which clone fields called `width`, `height` or `resolution` mean intrinsic media, generated output, normalized editor space, graph frame or display label?
12. Does current LibTV source crop ordinary image/video nodes, letterbox them, resize the node, or use another object-position policy?
13. Does source output/version switching preserve node frame, preserve crop focal point, or reflow the node and its overlays?
14. Is any source resize affordance present, and if so does resize preserve center, top-left, selected overlay gaps and semantic history?
15. What deterministic fixtures can prove visible crop and geometry without real uploads/providers?

## 5. Evidence Queue

### 5.1 Fixed Open Canvas

Read and record exact paths for:

- `CanvasNodeMedia`, image/video node data, selected output indexes and normalization;
- intrinsic image/video metadata probes and object URL cleanup;
- closest-generation-ratio inference after upload;
- model option normalization and execution payload projection;
- fixed node-card widths, `previewAspectRatio` and preview wrappers;
- `object-cover` node/output/media-control surfaces and `object-contain` detail/editor surfaces;
- selected output switching, edited-image append/selection and media-history merge;
- graph serialization of node width/height versus omission of `measured` dimensions;
- `measured -> width/height -> fallback` anchor calculations;
- absence/presence audit for `NodeResizer`, resize handles and explicit node-resize commands;
- thumbnail/full-media URL divergence and metadata absence.

Candidate evidence IDs: `OC-081..090`.

### 5.2 Current LibTV Clone

Read and record exact paths for:

- `ImageNode` media metadata, graph frame, `object-cover`, watermark and detail handoff;
- `VideoNode` poster/video rendition, ready/pending/error states and measured geometry use;
- `ImagePreviewOverlay` contain sizing and intrinsic-ratio assumptions;
- Shot Breakdown source/result cards and their fixed frame/crop policy;
- frame capture, Director capture/export and derived-node dimension propagation;
- `parseVideoResolution`, default node dimensions and derived placement;
- media-normalized mark/region/crop surfaces;
- all fields named width/height/resolution/aspectRatio and their current semantic classes;
- existing component specs, fixture expectations and overlay geometry assertions;
- missing metadata-ready/decode-error/output-switch/ratio-mismatch behavior.

Candidate issue prefix: `LIBTV-MRG-*` (`Media Rendition Geometry`).

### 5.3 LibTV Source-Site Read-Only Evidence

Use the existing authenticated project only for read-only inspection:

- ordinary image/video node shell, media element and computed `object-fit/object-position`;
- node graph rect versus visible media rect versus intrinsic media dimensions;
- selected toolbar/panel rect before and after media load or output/version switch;
- preview/detail rendition and thumbnail rendition;
- empty, failed, pending and ready media-frame geometry;
- presence/absence of node resize handles or cursor states;
- crop/letterbox behavior across landscape, portrait and square media already present in the shared project.

Do not upload, generate, edit, save, delete, switch a destructive setting or invoke paid/provider actions. If the shared fixture lacks ratio-diverse media or safe output history, record `SOURCE_UNKNOWN` and design `LIBTV-FIX-SOURCE-MEDIA-RENDITION-01` for a disposable fixture.

## 6. Surface Profiles To Compare

| Profile | Candidate surfaces | Main question |
|---|---|---|
| canvas primary media | ordinary image/video nodes | which authority fixes frame and crop? |
| candidate/history grid | image output grid, generated history | are mixed-ratio candidates cropped consistently? |
| detail preview | image modal/full-screen viewer | is full content visible with `contain`? |
| editor canvas | annotate/picture/crop surfaces | which intrinsic/normalized transform owns marks? |
| reference thumbnail | Prompt/media tokens | does thumbnail crop alter identity or meaning? |
| filmstrip/poster | continuation/reshoot/shot breakdown | fixed temporal frame versus source aspect |
| pending/error placeholder | empty/running/failed nodes | does status preserve stable geometry? |
| derived output | frame capture, edit result, Director export | how are output and graph dimensions propagated? |
| overlay anchor host | selected image/video node shell | is measured rect stable across rendition changes? |

## 7. Planned Deliverables

| Deliverable | Lifecycle | Purpose |
|---|---|---|
| `docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md` | dated reference | fixed Open Canvas/clone/source facts, counterexamples and ranked gaps |
| `docs/research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md` | stable guide/reference | dimension authorities, rendition profiles, state machine and handoffs |
| `media-rendition-geometry-static-evidence-2026-08-27.json` | evidence artifact | exact paths, claims, semantic classes and boundaries |
| `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` | fixture design | mixed-ratio image/video/output/status matrix without provider calls |
| `LIBTV-VR-023` | verifier design | pixel/rect/style/selection/overlay and pure authority checks |
| `OC-PATTERN-13` / `OC-ADOPT-026` / `OC-BP-013` | Open Canvas translation | reusable method, adoption boundary and implementation slices |
| `OC-TR-019` / `LIBTV-TR-045` / `DEC-039` / `LIBTV-UIX-23` | governance | traceability, decision and UI/UX mapping |
| `LIBTV-PAR-016` | parity backlog | one implementation-ready media-rendition slice |
| `OC-EQ-009` / `LIBTV-FIX-SOURCE-MEDIA-RENDITION-01` | source queue | ratio-diverse read-only/disposable source confirmation |

These IDs are now authoritative in their target documents. The final graph ranges are `LIBTV-GI-101..116` and `LIBTV-GC-127..145`; output/frame changes are modeled as explicit semantic commands, while passive measurement remains runtime-only and zero-history.

## 8. Work Sequence

1. Complete the authority-overlap audit and freeze the dimension vocabulary.
2. Extract fixed Open Canvas media/ratio/frame/rendition facts and counterexamples into a dated evidence artifact.
3. Extract current clone node/media/rendering behavior and classify every width/height/resolution field in scope.
4. Perform safe read-only LibTV source inspection using existing screenshots/DOM first, browser only for unresolved current facts.
5. Build cross-surface matrices for authority, crop/fit, object position, load state, output switch and overlay consequences.
6. Rank visible fidelity gaps separately from geometry correctness, identity, accessibility and performance risks.
7. Write the formal contract only after the dated audit proves the missing authority.
8. Define deterministic fixture/verifier designs without modifying runtime or tests.
9. Sync Hub -> Guide -> Reference navigation and Open Canvas adoption/handoff/governance chains.
10. Run documentation verification and diff checks; commit and push each key documentation milestone.
11. Promote this plan into dated Open Canvas research history when the batch closes.
12. Start the next highest-value documentation loop only after checking unresolved evidence and handoff gaps.

## 9. Decisions The Contract Must Resolve

- canonical names and provenance for intrinsic, request, output, frame, measured and export dimensions;
- whether each dimension is semantic, derived, runtime-only, display-only or unknown;
- per-output metadata requirements and selected-output reconciliation;
- fallback order when intrinsic metadata is absent, invalid, delayed or conflicts with labels;
- surface-specific `cover/contain/object-position` policy and whether crop is visual-only;
- thumbnail versus full-media identity and stale thumbnail handling;
- node frame policy: fixed by type, request-aspect-driven, intrinsic-aspect-driven or explicit semantic resize;
- passive measurement policy and the ban on interpreting it as user intent;
- output-switch behavior for mixed aspect ratios;
- pending/error/empty geometry stability;
- selection/handle/overlay remeasurement after a legitimate frame change;
- center/top-left preservation and one-history cardinality if explicit resize is later proven;
- media-normalized editor transform independence from graph viewport/DOM crop;
- export/derived-output dimension propagation;
- source-unknown behavior gates and prototype-safe fallback;
- explicit distinction among LibTV source fact, Open Canvas fact, inference and clone decision.

## 10. Risk Ranking Method

| Axis | High-risk example |
|---|---|
| visible fidelity | portrait source is silently center-cropped in a landscape LibTV node |
| geometry correctness | content reflow changes measured rect while toolbar/panel still uses stale dimensions |
| semantic correctness | changing generation ratio silently mutates source intrinsic metadata |
| interaction | marks are normalized against the cropped DOM rect but replayed against full intrinsic media |
| identity | selected output URL changes while width/height/thumbnail remain from the prior candidate |
| accessibility | full content is only reachable through a clipped node without an honest detail surface |
| performance | full-resolution media is decoded where a thumbnail surface should be authoritative |

Recommended implementation order will prioritize stable visible frame/rendition behavior and deterministic mixed-ratio fixtures before any generic resize abstraction.

## 11. Stop Conditions

Stop an evidence path when it would require:

- changing clone code, runtime tests or fixtures;
- changing/installing dependencies or modifying a submodule;
- uploading, generating, editing, saving or deleting on the shared source project;
- invoking paid/provider execution;
- inferring LibTV source crop/resize behavior from Open Canvas;
- treating a CSS aspect wrapper as intrinsic media metadata;
- treating React Flow `measured` fields as a semantic user-resize command;
- inventing provider-specific output dimensions or mixed-ratio behavior;
- collapsing Director/FrameOS media geometry into ordinary LibTV route authority.

Record the unknown, continue with the next safe evidence path and preserve the fact/inference/decision distinction.

## 12. Acceptance Criteria

This research batch is complete when:

- every media-bearing surface in scope names its dimension/rendition authority;
- intrinsic, selected output, generation request, node frame, measured rect, editor space and export dimensions are distinct;
- Open Canvas positive methods and counterexamples are fixed to exact code paths;
- current clone width/height/resolution/aspect fields have semantic classifications and known collision points;
- source-known and source-unknown crop/fit/resize behaviors are explicit;
- mixed-ratio output switching has a deterministic proposed policy;
- pending/error/load/decode transitions cannot silently change anchor geometry in the proposed contract;
- visual crop is distinct from destructive crop and editor media coordinates;
- fixture `LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` and verifier `LIBTV-VR-023` have deterministic cases;
- Open Canvas methods/counterexamples have explicit adoption decisions;
- agent navigation, traceability and implementation handoff remain discoverable;
- documentation checks pass and no runtime/submodule/WIP path is modified.

## 13. Completion Record

### 13.1 Milestones

| Milestone | Commit | Result |
|---|---|---|
| plan and authority boundary | `fd90b18` | active docs-only plan, questions, stop conditions and deliverables fixed |
| three-way static audit | `c2278f8` | `OC-081..090`, `LIBTV-MRG-001..014`, source measurements and raw JSON fixed |
| formal authority contract | `2c3b003` | ten authorities, frame/rendition profiles, fit transforms, invariants, fixture and `VR-023` design |
| component-spec propagation | `2d7d84c` | eight media/detail/editor specs aligned with the formal contract |
| Open Canvas governance | `c002272` | `OC-PATTERN-13`, `OC-ADOPT-026`, evidence/report/translation governance synchronized |
| LibTV handoff governance | `3523614` | traceability, UIX, blueprint, decision, parity and report synchronized |
| project verification governance | `1d46648` | graph/fixture/verifier/ledger/coverage/evidence queue synchronized |
| discovery and lifecycle closeout | closeout commit containing this historical record | Hub/task/glossary/Big Picture/lifecycle/audit/index and plan promotion synchronized |

### 13.2 Completed authority chain

```text
OC-081..090
  -> OC-PATTERN-13 / OC-ADOPT-026 / OC-BP-013
  -> LIBTV-TR-045 / LIBTV-UIX-23 / DEC-039 / LIBTV-PAR-016
  -> LIBTV-MRG-I-001..042
  -> GI-101..116 / GC-127..145
  -> LIBTV-FIX-LOCAL-MEDIA-RENDITION-01
  -> LIBTV-VR-023
  -> OC-EQ-009 / LIBTV-FIX-SOURCE-MEDIA-RENDITION-01
```

### 13.3 Remaining work is intentionally not claimed complete

- runtime remains `RUNTIME_FRAGMENTED`; no common media/frame/rendition/measurement authority was implemented;
- source parity remains partial; current read-only evidence is landscape-image bounded;
- portrait/square/odd-size/video/mixed-output/resize/editor-round-trip source behavior remains gated by a disposable fixture and per-action authorization;
- no runtime fixture, verifier, provider, upload, generation, save, test or submodule change was made;
- any implementation must re-enter through `LIBTV-PAR-016` + `OC-BP-013` and obtain explicit coding authorization.

### 13.4 Reopen conditions

Create a new dated plan rather than reactivating this file only when at least one of these occurs:

1. a ratio-diverse disposable LibTV source fixture is accepted;
2. clone runtime/fixture/verifier implementation is explicitly authorized;
3. Open Canvas baseline SHA changes in a way that affects `OC-081..090`;
4. new source evidence changes frame, fit, output-switch, resize or editor-coordinate decisions;
5. a runtime change invalidates an invariant or component-spec handoff.
