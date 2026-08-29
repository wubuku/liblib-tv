# LibTV Media Ingress And Resource Lifecycle Contract

> Status: `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING_OR_PARTIAL` / `SOURCE_PARITY_PARTIAL`.
>
> Scope: ordinary LibTV media/file/asset ingress, temporary browser leases, locator materialization, graph projection and release composition.
>
> Evidence baseline: [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md), clone `6325a1f`, Open Canvas `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> Authorization boundary: this is a documentation contract. It does not authorize runtime, test, provider, upload, persistence, source-site or submodule changes.

## 1. Contract Objective

This contract defines how media enters the ordinary LibTV canvas without confusing five different things:

1. the user's ingress intent;
2. local bytes temporarily owned by the browser session;
3. a reusable asset identity;
4. a graph node's reference to media;
5. UI progress, preview and feedback.

The core rule is:

> A locator may render before it is portable, and a node may show progress before it owns media. Neither visual fact grants durable resource ownership.

The target lifecycle is:

```text
intent
  -> classify
  -> validate
  -> probe
  -> acquire preview/materialization leases
  -> materialize or resolve existing asset
  -> reconcile current canvas/node owner
  -> plan one semantic graph projection
  -> transfer/alias resource reference
  -> retain while reachable
  -> release only when the responsible owner proves it is safe
```

## 2. Evidence And Product Boundary

### 2.1 `OPEN_CANVAS_FACT`

The fixed Open Canvas implementation demonstrates:

- client and server media gates;
- local image/video metadata probes;
- multipart upload to configured storage;
- digest-derived storage keys and dedupe lookup;
- normalized media descriptors with URL, `assetId`, MIME, size, duration and thumbnail;
- whole-canvas file drop and deterministic item offsets;
- existing-node upload/replace;
- graph save of stable media references.

It also demonstrates counterexamples:

- placeholder node creation before strict validation;
- extension/MIME classifier disagreement;
- sequential multi-file partial mutation;
- autosaved running/error state without resumable upload identity;
- no upload cancel, stale-owner guard or orphan cleanup;
- no resource ref-count or asset deletion boundary.

### 2.2 `LIBTV_SOURCE_FACT`

Read-only source observation proves current visible separation among:

- Add Resource multi-file image/video/audio upload;
- generated-history picker with source/media filters and ten-item cap;
- style/effect Material Library;
- canvas-node inventory and Personal/Agent asset view;
- Shot Breakdown single-video upload and graph-video selection surfaces.

It does not prove exact validation limits, upload transport, placeholder timing, progress, retry, save portability or cleanup.

### 2.3 `CLONE_FACT`

The ordinary clone currently has:

- Add Resource mock feedback;
- component-local Shot Breakdown object URL preview;
- repo-path media fixtures;
- generic string locators in node data;
- per-canvas graph history;
- no ordinary route upload service, drop ingress, file paste or asset registry.

Director has browser-local data/blob paths. It composes with this contract but remains a separate subsystem and store.

### 2.4 `CLONE_DECISION`

LibTV adopts Open Canvas's typed pipeline method, not its provider, visual skin, exact MIME list, autosave semantics, placeholder mutations or cleanup omissions.

## 3. Authority Composition

| Authority | Owns | This contract delegates |
|---|---|---|
| [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) | node field roles and operation transforms | final locator/data field validation |
| [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md) | portable document/clipboard/persistence shapes | export/import portability |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | delayed result freshness/idempotency/transfer | materialization completion convergence |
| [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | destructive command impact | graph detach and cleanup diagnostics |
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | client/host/flow conversion and placement | drop/add/history placement |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | graph/history invariants and cases | semantic mutation correctness |
| [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | canvas ID/generation/switch/delete | canvas-owner freshness |
| [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) | disposition/reason/primary surface | feedback projection and lifecycle |
| [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | keyboard/focus/foreground precedence | picker/dialog/escape behavior |

This contract is the authority for the path between ingress intent and accepted media-reference projection, plus the resource reachability facts that later delete/document authorities consume.

## 4. Vocabulary

### 4.1 Core terms

| Term | Definition |
|---|---|
| ingress intent | one user or system request to attach/create media |
| entry profile | named surface-specific behavior policy |
| source descriptor | immutable description of local file, existing asset, graph media or generated result |
| materialization | conversion from session bytes/result into a stable locator or explicitly session-only resource |
| locator | value used to retrieve/render bytes |
| asset identity | reusable identity independent of one node reference |
| node media reference | one graph node's semantic reference to media/asset |
| lease | explicit temporary right and duty to retain/release a resource |
| alias | an additional reference to the same resource identity |
| transfer | exact-once change of lease/resource owner |
| reachability | set of current owners that still require a resource |
| provisional projection | progress UI excluded from semantic graph/history/document |
| semantic projection | accepted node/edge/data/selection/history transaction |

### 4.2 Media source kinds

```text
LOCAL_FILE
GENERATED_HISTORY_ITEM
REGISTERED_ASSET
CANVAS_NODE_MEDIA
LOCAL_EDITOR_EXPORT
DIRECTOR_BROWSER_EXPORT
DIRECTOR_LOCAL_MODEL
REPO_FIXTURE
REMOTE_RESULT
```

Source kind is provenance, not locator class. `LOCAL_EDITOR_EXPORT` can materialize to a stable remote asset or remain a session blob; the class must record the actual outcome.

## 5. Named Entry Profiles

| Profile | Source surface | Cardinality | Target | Default projection policy |
|---|---|---:|---|---|
| `ADD_RESOURCE_MULTI` | Add Node -> Upload | 1..N | new nodes | runtime placeholders, atomic accepted cohort commit |
| `CANVAS_DROP_MULTI` | files dropped on canvas | 1..N | new nodes at captured flow points | runtime placeholders, atomic accepted cohort commit |
| `NODE_MEDIA_REPLACE` | existing image/video node upload/replace | 1 | existing node | preserve last good media, commit success once |
| `SHOT_SOURCE_UPLOAD` | Shot Breakdown source upload | 1 | existing process source | local preview until durable/declared session owner |
| `GENERATED_HISTORY_ATTACH` | generated-history picker | 1..10 | new nodes or declared target | immediate atomic stable-reference commit |
| `REGISTERED_ASSET_ATTACH` | Personal/Agent asset picker | 1..N | new nodes or declared target | immediate atomic alias/reference commit |
| `CANVAS_MEDIA_REFERENCE` | select media from current canvas | 1 | process/input node | graph reference transaction, no byte transfer |
| `LOCAL_EDIT_EXPORT` | image editor save | 1 | existing/new result node | async materialize then one semantic commit |
| `DIRECTOR_BROWSER_EXPORT` | Director capture/video export | 1..N | ordinary canvas result nodes | generic async convergence + explicit data/blob policy |
| `DIRECTOR_LOCAL_MODEL_IMPORT` | Director model library file input | 1..N | Director library, not ordinary graph | separate subsystem profile with byte budget |

Entry profiles share results/reasons and resource semantics. They do not have to share one React component or one store action.

## 6. Conceptual Data Model

The following shapes are design vocabulary, not authorized implementation.

### 6.1 Ingress intent

```ts
type MediaIngressIntent = {
  ingressId: string;
  attemptId: string;
  entryProfile: MediaIngressEntryProfile;
  canvasId: string;
  canvasGeneration: number;
  targetNodeId: string | null;
  expectedNodeVersion: number | null;
  cohortId: string | null;
  itemIndex: number;
  source: MediaSourceDescriptor;
  placement: MediaPlacementDescriptor | null;
  requestedAt: string;
};
```

`attemptId` changes on retry. `ingressId` remains stable when the user retries the same logical item from its error surface.

### 6.2 Local file descriptor

```ts
type LocalFileDescriptor = {
  kind: "LOCAL_FILE";
  name: string;
  declaredMimeType: string;
  sizeBytes: number;
  lastModified: number;
};
```

The descriptor is serializable metadata. The actual `File` remains in an instance-scoped operation/lease owner and never enters graph/history/document state.

### 6.3 Media locator

```ts
type MediaLocatorDescriptor = {
  locatorClass:
    | "REPO_ASSET"
    | "REMOTE_URL"
    | "EMBEDDED_DATA_URL"
    | "SESSION_BLOB_URL"
    | "STABLE_ASSET";
  renderUrl: string;
  assetId: string | null;
  mimeType: string | null;
  sizeBytes: number | null;
  width: number | null;
  height: number | null;
  durationSeconds: number | null;
  thumbnailUrl: string | null;
  provenance: MediaProvenance;
  portable: boolean;
};
```

`portable` is derived from class, budget and owner evidence. It is not trusted merely because a URL string is non-empty.

### 6.4 Resource lease

```ts
type MediaResourceLease = {
  leaseId: string;
  resourceId: string;
  resourceClass:
    | "LOCAL_BYTES"
    | "METADATA_PROBE_URL"
    | "PREVIEW_URL"
    | "SESSION_RESULT_URL"
    | "STABLE_ASSET_REFERENCE";
  ownerKind:
    | "INGRESS_OPERATION"
    | "PREVIEW_SURFACE"
    | "GRAPH_REFERENCE_REGISTRY"
    | "DIRECTOR_WORKSPACE"
    | "ASSET_REGISTRY";
  ownerId: string;
  acquiredAt: string;
  transferredAt: string | null;
  releasedAt: string | null;
  releaseCount: number;
};
```

Stable remote assets usually transfer/alias a reference; they are not revoked by the browser. Object URL leases require a browser release action when their owner ends.

### 6.5 Projection plan

```ts
type MediaIngressProjectionPlan = {
  disposition: "accept" | "reject" | "noop" | "stale" | "unknown";
  reason: string | null;
  nodesToCreate: PlannedNode[];
  nodePatches: PlannedNodePatch[];
  edgesToCreate: PlannedEdge[];
  selectionAfter: string[];
  historyPolicy: "one-step" | "zero-step";
  leaseTransfers: PlannedLeaseTransfer[];
  leaseReleases: PlannedLeaseRelease[];
  feedback: PlannedFeedbackProjection[];
};
```

The whole plan validates before any semantic graph mutation.

## 7. State Machine

### 7.1 States

```text
INTENT
VALIDATING
PROBING
READY_TO_MATERIALIZE
MATERIALIZING
READY_TO_COMMIT
COMMITTING
COMMITTED
FAILED
CANCELED
STALE
```

### 7.2 Transition table

| From | Event | To | Required side effect |
|---|---|---|---|
| `INTENT` | descriptor captured | `VALIDATING` | freeze owner/source/placement |
| `VALIDATING` | invalid | `FAILED` | stable reason; release unneeded bytes/leases |
| `VALIDATING` | metadata required | `PROBING` | acquire probe lease if needed |
| `VALIDATING` | no probe required | `READY_TO_MATERIALIZE` | zero graph mutation |
| `PROBING` | success | `READY_TO_MATERIALIZE` | release probe lease exactly once |
| `PROBING` | fail | `FAILED` | reason + release probe lease |
| `READY_TO_MATERIALIZE` | start | `MATERIALIZING` | operation owns bytes/result lease |
| `MATERIALIZING` | stable/session locator produced | `READY_TO_COMMIT` | validate result envelope and owner freshness |
| `MATERIALIZING` | cancel/fail/stale | terminal | release untransferred lease exactly once |
| `READY_TO_COMMIT` | plan valid/current | `COMMITTING` | freeze final plan |
| `COMMITTING` | transaction accepted | `COMMITTED` | one graph/history projection + exact transfers |
| `COMMITTING` | graph conflict/failure | `FAILED` or recoverable result | no partial graph; result lease remains explicitly owned/released |

### 7.3 Terminal convergence

Terminal state is idempotent by `ingressId + attemptId + resultVersion`. Duplicate completion, repeated cancel or late error is an exact no-op after the first terminal result except for a detectable diagnostic.

## 8. Validation Registry

### 8.1 Validation order

1. validate entry profile/cardinality;
2. validate current canvas/target permission to start;
3. validate descriptor shape and finite size;
4. classify family using one canonical policy;
5. validate declared MIME/extension policy;
6. validate non-empty and profile byte budget;
7. probe and validate media metadata;
8. validate entry-specific duration/dimensions/model constraints;
9. materialize/resolve asset;
10. validate returned locator/asset identity and portability;
11. revalidate canvas generation/node version before graph planning.

Client validation is an experience optimization. A future server/materializer remains the trust boundary and returns the same stable reason family.

### 8.2 Profile registry requirements

| Profile family | Required fields | Budget owner | Metadata owner |
|---|---|---|---|
| ordinary image | type, size | product/config registry | image dimension probe |
| ordinary video | type, size | product/config registry | duration + dimensions when needed |
| ordinary audio | type, size | product/config registry | optional duration/waveform later |
| text/document | type, size/character budget | product/config registry | parser-specific |
| Director model | extension/type, size | Director profile | parser/importer |
| data URL result | MIME, decoded byte count | document/media registry | producer envelope |
| blob URL result | MIME, size, lease owner | producer/resource registry | producer envelope |

Exact LibTV source size/type limits remain `SOURCE_UNKNOWN`; a local fixture uses explicit clone-only limits and labels them as such.

### 8.3 Stable reason candidates

```text
MEDIA_ENTRY_PROFILE_INVALID
MEDIA_CARDINALITY_EXCEEDED
MEDIA_SOURCE_DESCRIPTOR_INVALID
MEDIA_TYPE_UNSUPPORTED
MEDIA_TYPE_AMBIGUOUS
MEDIA_EMPTY
MEDIA_SIZE_EXCEEDED
MEDIA_BUDGET_UNKNOWN
MEDIA_METADATA_READ_FAILED
MEDIA_DIMENSIONS_INVALID
MEDIA_DURATION_INVALID
MEDIA_MATERIALIZER_UNAVAILABLE
MEDIA_MATERIALIZATION_FAILED
MEDIA_RESULT_INVALID
MEDIA_ASSET_ID_REQUIRED
MEDIA_NON_PORTABLE_REFERENCE
MEDIA_CANVAS_STALE
MEDIA_TARGET_MISSING
MEDIA_TARGET_VERSION_STALE
MEDIA_ATTEMPT_SUPERSEDED
MEDIA_CANCELED
MEDIA_RESOURCE_OWNER_REQUIRED
MEDIA_RESOURCE_TRANSFER_FAILED
MEDIA_GRAPH_PLAN_REJECTED
```

Localized copy and source-exact wording remain outside the reason identity.

## 9. Probe And Preview Lease Contract

### 9.1 Metadata probe

A probe lease exists only to read dimensions/duration or decode validation metadata.

Required rules:

1. acquire after structural validation;
2. never write probe URL into graph/history/document;
3. release on probe success, error, cancel, timeout and unmount;
4. release exactly once;
5. probe completion checks current attempt before publishing metadata;
6. `createImageBitmap` resources are closed on all successful decode paths;
7. accepted-format decode failure returns a stable reason; fallback behavior is explicit, not accidental.

### 9.2 Local preview

A preview URL may outlive the probe but remains session UI state unless explicitly transferred to a graph-reference registry.

`SHOT_SOURCE_UPLOAD` uses these states:

```text
EMPTY
LOCAL_PREVIEW
MATERIALIZING
DURABLE_READY
SESSION_READY
FAILED
```

Current clone `status=ready` after creating only a component URL is replaced in the design by `LOCAL_PREVIEW`. A process cannot claim durable readiness unless its runner can consume the owned session bytes/lease or a stable locator exists.

### 9.3 Preview replacement

When preview B replaces preview A:

1. B validates/acquires first;
2. current owner atomically points to B;
3. A is released once if no other owner exists;
4. stale completion for A cannot restore it;
5. graph semantic history remains unchanged until durable/session-ready commit.

## 10. Asset Identity Versus Node Reference

### 10.1 Separate objects

| Object | Example | Delete semantics |
|---|---|---|
| generated-history item | one prior generation output | picker reference only |
| registered asset | Personal/Agent reusable media | asset registry owns lifecycle |
| node media reference | image node points to asset/url | graph delete detaches reference |
| material preset | style/effect catalog entry | creates/configures node; not uploaded media |
| repo fixture | `/images/...` clone asset | immutable shared reference |
| session result | Director blob URL | browser owner/reachability required |

### 10.2 Reference rules

- Attaching an existing asset creates a reference/alias, not a byte copy by default.
- Duplicating/copying a node preserves/remaps the node reference according to node-data policy; it does not duplicate backend bytes.
- Deleting the final graph reference does not delete a registered/stable remote asset without an explicit asset-owner command.
- Material Library entries do not become media assets merely because they render thumbnails.
- Canvas-node inventory and asset registry may cross-link but keep distinct IDs and filters.

## 11. Entry Projection Policies

### 11.1 `ADD_RESOURCE_MULTI`

Default clone design:

- capture all file descriptors and ordering at chooser acceptance;
- enforce the observed source maximum only after source evidence; local fixture declares its own cap;
- validate/probe each item without semantic graph mutation;
- show provisional runtime cards/progress owned by `cohortId`;
- reserve placement through the spatial authority;
- materialize accepted items with bounded concurrency;
- commit all successful items in original order as one semantic graph/history command;
- keep failed items in a cohort error surface with retry/remove;
- select all committed nodes, primary active node is the last item unless source evidence changes it.

This is `CLONE_DECISION`, not a claim about source placeholder timing.

### 11.2 `CANVAS_DROP_MULTI`

Same lifecycle as Add Resource, with differences:

- placement derives from captured drop `FLOW_WORLD` point plus declared item layout;
- screen overlay clamp never changes the captured flow point;
- unsupported non-media entries are rejected before provisional graph projection;
- mixed success remains one accepted-success graph transaction;
- one undo removes the committed successful cohort.

### 11.3 `NODE_MEDIA_REPLACE`

- keep last good media visible during validation/materialization;
- project busy/progress in runtime UI, not semantic history;
- on success, patch media + metadata in one graph history step;
- on failure/cancel/stale, preserve last good media and expose a recoverable outcome;
- if the node is deleted/version-replaced, release untransferred result and emit no current success.

### 11.4 `SHOT_SOURCE_UPLOAD`

- local preview is allowed before stable materialization;
- graph metadata cannot claim durable source readiness without locator/lease provenance;
- canvas-media selection creates a graph reference, not local bytes;
- replacing source invalidates dependent authoring/result state according to Shot Breakdown aggregate policy;
- starting breakdown freezes the accepted source version and operation owner.

### 11.5 `GENERATED_HISTORY_ATTACH`

- picker selection refers to existing stable result identities;
- selection cap and media/source filters are UI constraints backed by validator results;
- no upload progress is shown for pure reference attach;
- selected items project atomically as new nodes or one declared target patch;
- item ordering and duplicate policy are deterministic;
- source system remains provenance, not node type.

### 11.6 `REGISTERED_ASSET_ATTACH`

- creates aliases/reference records;
- does not claim ownership of backend byte deletion;
- Personal/Agent origin and semantic asset tag remain asset metadata;
- node copy/delete does not silently mutate asset registry.

### 11.7 Director profiles

Director paths use the same locator/lease/reachability vocabulary but keep Director store/workspace identity:

- local model data URL requires a byte budget and Director-only persistence policy;
- image capture data URL requires decoded byte accounting before ordinary graph projection;
- animation blob URL transfers from export operation to graph-reference registry exactly once;
- failed graph projection revokes producer-owned blob once;
- successful graph projection does not revoke while graph/history/preview remains reachable;
- ordinary LibTV entry components do not import Director store state.

Batch 82 adds a clone-owned Director-only local model materialization slice:

- `DirectorLocalResourceDescriptorV1` records bounded file metadata, provenance and a
  session-only locator class;
- `idle/loading/ready/failed/canceled/released` and request/attempt identity are
  observable through the Director store;
- OBJ/FBX bytes may be parsed locally with Three.js loaders for a finite prototype
  path; a parse failure retains the proxy and exposes retry;
- `File`, `Blob`, data URL, parsed `Object3D` and capture bytes remain outside the
  portable project document;
- this does not implement the ordinary LibTV ingress registry, remote materializer,
  stable cloud asset or production cache.

## 12. Cohort And Concurrency Contract

### 12.1 Cohort identity

A multi-item intent has one `cohortId` and stable item order. Each item has its own `ingressId`, attempt and terminal result.

### 12.2 Bounded concurrency

The contract permits sequential or bounded-parallel materialization. It requires:

- deterministic final item order independent of completion order;
- configurable concurrency outside UI component code;
- cohort cancel propagated to nonterminal attempts;
- no later item starvation after one failure;
- no toast storm; cohort feedback aggregates repeated failures;
- placement reserved from intent, not completion time.

### 12.3 Partial success

Default disposition:

```text
zero valid/success items -> reject/fail, zero semantic graph history
some success items       -> accept successes in one graph step + retain failure report
all success items        -> accept all in one graph step
cohort canceled          -> zero commit unless an explicit prior commit boundary exists
```

Retries create new attempts for failed items and one later graph step for newly accepted results. They do not replay already committed successes.

### 12.4 Duplicate items

Duplicate file descriptors do not prove duplicate bytes. The product policy can allow both node references while a materializer deduplicates assets. UI dedupe, storage dedupe and graph duplicate-node policy remain separate decisions.

## 13. Freshness And Async Composition

### 13.1 Start snapshot

Every delayed profile captures:

- canvas ID/generation;
- target node ID/version when applicable;
- ingress/attempt/cohort identity;
- source descriptor/version;
- placement descriptor and host epoch when derived from local screen geometry;
- expected field ownership;
- lease owner.

### 13.2 Completion reconciliation

Order:

1. validate result envelope identity/version;
2. reject duplicate/superseded terminal delivery;
3. check canvas ID/generation;
4. check target existence/version/field ownership;
5. check cancel state;
6. validate locator/asset/resource lease;
7. plan graph projection against current graph;
8. atomically apply graph/history/selection + transfers;
9. publish terminal feedback;
10. release producer/untransferred resources.

### 13.3 Delete, switch and unmount

- Surface unmount does not imply operation cancel unless the entry profile declares it.
- Canvas switch never retargets an operation to the newly active canvas.
- Node delete marks node-targeted attempt stale or canceled according to profile; completion cannot resurrect it.
- Canvas delete cancels/retains/releases through multi-canvas lifecycle policy.
- Closing a picker before intent acceptance creates no operation.

## 14. Graph, Selection And History

### 14.1 Provisional state

Validation/probe/materialization progress belongs to an operation/UI registry. It is excluded from:

- semantic graph document;
- graph undo/redo snapshots;
- clipboard/import/export;
- permanent node status after session loss.

A renderer may project provisional cards into the canvas plane, but those cards require separate runtime identity and are not normal graph nodes.

### 14.2 Semantic commit

| Profile | Graph commit | History | Selection |
|---|---:|---:|---|
| Add/drop cohort | successful items together | one step | all created; primary last |
| existing-node replace | one patch | one step | preserve current selection by default |
| history/asset attach | selected cohort together | one step | all created/declared target |
| Shot source reference | one source/aggregate patch | one step | preserve source node |
| rejected/invalid/stale/canceled | none | zero | unchanged |
| progress/probe update | none semantic | zero | unchanged |

Source-exact selection behavior remains gated; these are clone correctness defaults.

### 14.3 Undo/redo

Undo/redo changes graph references, not external bytes. Resource reachability is recomputed from current graph plus history/other owners. Feedback/progress does not replay.

## 15. Feedback And Interaction Surfaces

### 15.1 Primary surfaces

| Outcome | Primary owner |
|---|---|
| invalid file before placeholder | Add Resource/drop cohort list |
| node replace validation/materialization failure | node-local upload/replace surface |
| cohort partial success | cohort summary with failed item retry |
| stale/superseded background completion | operation diagnostic; no current success toast |
| backend/materializer unavailable in prototype | action-adjacent honest local boundary |
| asset/history picker empty | picker empty state |
| durable graph result | graph node/reference itself |

Toast is secondary announcement only. It cannot be the sole durable owner of a retryable failure.

### 15.2 Picker/focus behavior

- Add Node panel opens upload chooser or generated-history dialog as one foreground chain.
- Escape/file-chooser cancel returns focus to the invoking command and creates no operation.
- Generated-history media/source filter changes remain picker UI state.
- Confirm validates current selection; zero selection remains disabled/no-op.
- Asset Manager, Material Library and Generated History retain separate labels and data owners.

## 16. Resource Reachability Ledger

### 16.1 Reachability owners

```text
CURRENT_GRAPH
HISTORY_PAST
HISTORY_FUTURE
CLIPBOARD_PACKET
OPEN_PREVIEW_OR_EDITOR
ACTIVE_INGRESS_OPERATION
DIRECTOR_WORKSPACE
REGISTERED_ASSET_CATALOG
PORTABLE_DOCUMENT_EXPORT
```

An owner reports resource IDs/locator classes, not arbitrary URL string equality alone.

### 16.2 Release decision

For session resources:

```text
if producer still owns and result rejected/canceled/stale:
  release producer lease once
else if ownership transferred:
  producer cannot release
else if graph ref removed but any ledger owner reachable:
  retain
else if exclusive browser lease owner proves zero reachability:
  release once
else:
  emit MEDIA_RESOURCE_OWNER_REQUIRED; do not guess
```

For stable remote assets, zero graph reachability detaches references but does not delete backend bytes.

### 16.3 History pruning

When a history snapshot is evicted or future is cleared after a new command, the ledger recomputes resources reachable only from removed snapshots. Release is permitted only for session resources with an explicit exclusive owner and zero remaining reachability.

### 16.4 Clipboard/export

- In-memory clipboard may alias session resources only within the same BrowserContext and with an explicit lease owner.
- System clipboard/portable documents reject or materialize session blob locators.
- Embedded data URLs require decoded byte budgets and provenance.
- Copying stable asset references creates aliases, not leases to delete bytes.

## 17. Locator Materialization Policy

| Input | Allowed result | Portable result requirement |
|---|---|---|
| local file | stable asset, bounded embedded data, session preview | stable asset or budgeted data |
| generated-history item | stable asset/reference | stable identity + URL |
| registered asset | stable alias/reference | asset identity retained |
| canvas media reference | graph reference to existing media identity | source reference valid or materialized |
| editor Blob | stable asset or session result | stable materialization before portable export |
| Director data URL | bounded embedded media | decoded bytes under budget |
| Director blob URL | session result lease | reject portable until resolved/uploaded/embedded |
| repo fixture | repo asset locator | path validated in project bundle |

Materialization never silently rewrites one locator class as another based on string prefix alone. It returns a validated descriptor and transfer plan.

## 18. Honest Prototype Mode

### 18.1 No backend available

The frontend prototype may support:

- file selection and validation;
- local metadata probe;
- temporary preview with visible `本地预览` state;
- deterministic fixture materializer resolving to bundled repo assets;
- generated-history/asset mock dialogs clearly labeled local fixture;
- failure/retry/cancel and graph transaction verification.

It must not claim:

- remote upload progress/completion;
- durable asset registration;
- refresh persistence of local bytes;
- cloud deletion or storage dedupe;
- provider-generated results;
- account/Agent asset access.

### 18.2 Local fixture materializer

The fake materializer is deterministic by fixture item ID, not actual private file content. It can return:

- stable repo locator;
- delayed success/failure;
- session blob lease;
- invalid/stale/duplicate result envelopes.

This provides lifecycle coverage without transmitting files or inventing a production backend.

## 19. Required Invariants

| ID | Invariant |
|---|---|
| `LIBTV-MIR-I-001` | every ingress item has stable ingress/attempt identity |
| `LIBTV-MIR-I-002` | canvas ID/generation is frozen before delayed work |
| `LIBTV-MIR-I-003` | target node/version is frozen when a profile targets an existing node |
| `LIBTV-MIR-I-004` | actual `File`/`Blob` never enters semantic graph/history/document state |
| `LIBTV-MIR-I-005` | source kind and locator class remain separate |
| `LIBTV-MIR-I-006` | one canonical classifier owns file-family acceptance |
| `LIBTV-MIR-I-007` | validation failure follows the profile's declared zero/provisional mutation policy |
| `LIBTV-MIR-I-008` | client validation does not replace materializer/server trust validation |
| `LIBTV-MIR-I-009` | metadata probe leases release exactly once on all terminal paths |
| `LIBTV-MIR-I-010` | preview lease never implies portable ownership |
| `LIBTV-MIR-I-011` | local preview and durable/session ready are distinct states |
| `LIBTV-MIR-I-012` | materialization result carries locator/provenance/resource ownership |
| `LIBTV-MIR-I-013` | duplicate/superseded completion is an exact no-op |
| `LIBTV-MIR-I-014` | stale canvas/node completion cannot mutate graph, selection or current feedback |
| `LIBTV-MIR-I-015` | untransferred session result is released exactly once on reject/cancel/stale |
| `LIBTV-MIR-I-016` | successful lease transfer occurs exactly once |
| `LIBTV-MIR-I-017` | whole projection validates before semantic graph mutation |
| `LIBTV-MIR-I-018` | accepted cohort item order is independent of completion order |
| `LIBTV-MIR-I-019` | accepted cohort commit has one declared history step |
| `LIBTV-MIR-I-020` | invalid/noop/stale/canceled progress adds zero graph history |
| `LIBTV-MIR-I-021` | placement is captured through the spatial authority before async completion |
| `LIBTV-MIR-I-022` | screen feedback movement cannot change captured flow placement |
| `LIBTV-MIR-I-023` | existing-node replace preserves last good media until accepted success |
| `LIBTV-MIR-I-024` | generated-history/registered-asset attach does not fake upload |
| `LIBTV-MIR-I-025` | asset identity and node media reference remain distinct |
| `LIBTV-MIR-I-026` | graph delete never implies stable remote asset delete by default |
| `LIBTV-MIR-I-027` | session resource release considers graph/history/clipboard/editor/operation reachability |
| `LIBTV-MIR-I-028` | history eviction/future clear triggers deterministic reachability reconciliation |
| `LIBTV-MIR-I-029` | blob locator is not portable without resolution/materialization |
| `LIBTV-MIR-I-030` | data URL portability requires decoded byte budget and provenance |
| `LIBTV-MIR-I-031` | feedback has one primary owner and deterministic retry/clear lifecycle |
| `LIBTV-MIR-I-032` | stale completion cannot announce current success |
| `LIBTV-MIR-I-033` | Material Library, Generated History and Asset Manager retain separate product identities |
| `LIBTV-MIR-I-034` | ordinary LibTV, FrameOS and Director resource owners remain route/subsystem-isolated |
| `LIBTV-MIR-I-035` | prototype mode labels local preview/unavailable materializer honestly |
| `LIBTV-MIR-I-036` | no source parity claim is derived solely from Open Canvas behavior |

## 20. Decision Queue

### `LIBTV-MIR-DQ-001`: exact source type/size limits

Status: `SOURCE_EVIDENCE_REQUIRED`. Use clone-only fixture limits until safe source evidence exists.

### `LIBTV-MIR-DQ-002`: source placeholder timing

Status: `SOURCE_EVIDENCE_REQUIRED`. Default clone design uses runtime provisional cards and no pre-validation semantic node.

### `LIBTV-MIR-DQ-003`: source multi-file transaction/history

Status: `SOURCE_EVIDENCE_REQUIRED`. Correctness default is one accepted-success cohort graph step.

### `LIBTV-MIR-DQ-004`: source partial-success UI

Status: `SOURCE_EVIDENCE_REQUIRED`. Default is committed successes plus retryable failed-item cohort report.

### `LIBTV-MIR-DQ-005`: generated-history duplicate policy

Status: `PRODUCT_DECISION_REQUIRED`. Permit multiple node refs unless exact duplicate graph policy says otherwise; do not infer storage copies.

### `LIBTV-MIR-DQ-006`: uploaded media auto-registers as asset

Status: `SOURCE_EVIDENCE_REQUIRED`. Current read-only evidence suggests node media and asset registry can diverge.

### `LIBTV-MIR-DQ-007`: object URL registry location

Status: `DESIGN_DECISION`. Prefer an instance-scoped resource registry composed with graph/history reachability, not module globals or node data.

### `LIBTV-MIR-DQ-008`: local Shot Breakdown runner consumes bytes or stable locator

Status: `PRODUCT_DECISION_REQUIRED`. Until defined, local preview cannot become durable-ready input.

### `LIBTV-MIR-DQ-009`: session blob alias in in-memory copy

Status: `DESIGN_DECISION`. Allow only with explicit same-context lease alias; portable copy rejects.

### `LIBTV-MIR-DQ-010`: stable asset backend deletion

Status: `DEFERRED_BACKEND_SCOPE`. Never infer from graph delete.

### `LIBTV-MIR-DQ-011`: upload persistence/recovery after reload

Status: `DEFERRED_BACKEND_SCOPE`. Persist running state only after resumable operation identity exists.

### `LIBTV-MIR-DQ-012`: bounded concurrency value

Status: `IMPLEMENTATION_DECISION_AFTER_AUTHORIZATION`. Fixture must test at least sequential and out-of-order completion.

### `LIBTV-MIR-DQ-013`: source selection after multi-attach

Status: `SOURCE_EVIDENCE_REQUIRED`. Clone default selects all and makes the last item primary.

### `LIBTV-MIR-DQ-014`: first authorized slice

Recommendation: `ADD_RESOURCE_MULTI` with synthetic files, deterministic fake materializer, runtime provisional cards and one cohort commit. It exercises the broadest shared lifecycle without touching provider/storage.

## 21. `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`

### 21.1 Fixture substrate

The fixture is local, deterministic and instance-scoped. It uses synthetic files generated in browser memory and never uploads them.

Required fixture services:

- fake file descriptor factory;
- canonical classifier and profile budget registry;
- fake image/video metadata probe;
- object URL lease ledger with create/transfer/release counters;
- controllable materializer queue;
- canvas/node generation owner registry;
- graph/history/selection recorder;
- resource reachability ledger;
- command feedback event log.

### 21.2 Fixture media aliases

| Alias | Description |
|---|---|
| `F_IMG_OK` | valid small image descriptor |
| `F_VID_OK` | valid small video descriptor with metadata |
| `F_AUDIO_OK` | valid audio descriptor for unavailable/success profiles |
| `F_EMPTY` | zero-byte file |
| `F_LARGE` | over-budget file |
| `F_MIME_BAD` | unsupported declared MIME |
| `F_MIME_EXT_DRIFT` | extension suggests media but MIME disagrees |
| `F_META_FAIL` | validation passes, probe fails |
| `A_STABLE` | existing registered asset/reference |
| `H_STABLE` | generated-history stable result |
| `R_DATA` | bounded data URL result |
| `R_BLOB` | session blob result with observable lease |
| `R_INVALID` | malformed materializer result |

### 21.3 Owner aliases

| Alias | Description |
|---|---|
| `C_A@G1` | initial canvas generation |
| `C_A@G2` | same canvas after replacement lifecycle |
| `C_B@G1` | unrelated active canvas |
| `N_SRC@V1` | existing target node/source version |
| `N_SRC@V2` | edited/replaced target version |
| `Q1` | multi-item cohort |
| `I1/A1` | ingress item/attempt one |
| `I1/A2` | retry attempt |
| `L1` | observable preview/result lease |

### 21.4 Required pure cases

1. canonical family classification including MIME/extension disagreement;
2. empty/size/type budget reasons;
3. metadata probe success/failure and exact release;
4. stable asset versus repo/remote/data/blob portability;
5. duplicate result idempotency;
6. canvas/node/attempt stale disposition;
7. cohort result ordering under out-of-order completion;
8. whole projection zero-partial validation;
9. reachability across graph/history/clipboard/editor/operation;
10. history pruning/future clear release decision;
11. data URL decoded-byte budget;
12. blob portable rejection.

### 21.5 Required browser scenes

| Scene | Setup/action | Required observation |
|---|---|---|
| Add Resource cancel | open chooser then cancel | focus returns; no operation/graph/history/lease |
| invalid cohort | bad MIME + empty + oversize | item reasons; zero semantic nodes/history |
| mixed cohort | valid image + invalid + valid video | provisional order; one commit for successes; retry report |
| out-of-order completion | two valid items resolve reverse order | final nodes/placement remain original order |
| cohort cancel | two materializing items | zero commit; all untransferred leases released once |
| node replace success | existing media + delayed result | old media visible; one final patch/history |
| node replace failure | existing media + failure | old media exact; durable node-local failure |
| delete during upload | remove target before completion | stale; no resurrection/success; release once |
| switch during upload | start A, switch B, complete A | B exact; A explicit owner/stale policy |
| retry race | A1 fails/retries A2; A2 then late A1 | A2 wins; A1 exact no-op |
| history asset attach | select H_STABLE items | no upload; one graph step; provenance retained |
| registered asset attach/delete | alias A_STABLE then delete node | graph ref removed; asset bytes untouched |
| Shot local preview | select local video | `LOCAL_PREVIEW`, not durable ready; cleanup on replace/unmount |
| Director blob transfer | R_BLOB accepted/rejected/deleted/undo | exact transfer/release with reachability |
| route isolation | FrameOS/Director event during LibTV fixture | no shared graph/store/lease owner |

### 21.6 Reset

Discard the Page after each browser scene. Timers, fake files, object URLs, materializer promises, operations, asset aliases and lease ledger must be instance-scoped. Reset must assert zero unreleased fixture-owned session leases; it must not hide leaks by revoking unknown global URLs.

## 22. `LIBTV-VR-021`

### 22.1 Pure verification

Verify:

- intent/profile/result schema;
- validation order/reasons;
- probe/preview lease exactness;
- locator portability;
- stale/idempotent convergence;
- cohort ordering/partial-success plan;
- graph/history plan cardinality;
- reachability/release decisions;
- no backend delete inference.

### 22.2 Focused browser verification

For every scene record:

```text
visible provisional/progress/error state
operation snapshot
nodes/edges/selection/history before/after
canvas/node generation
materializer queue/result
lease ledger before/after
feedback event log
```

### 22.3 Replacement assertions

`LIBTV-VR-021` replaces no historical batch wholesale. It composes:

- Add Node/overlay regressions;
- Batch 12/15/17 local surface checks;
- Shot Breakdown Batch 24 behavior;
- Director Batch 40/46/48 resource paths;
- `VR-012` node data;
- `VR-013` delete/resource;
- `VR-015` async ingress;
- `VR-017` multi-canvas;
- `VR-018` feedback;
- `VR-019` focus/context;
- `VR-020` placement.

Historical assertions that upload/history remain local mock are retained as prototype-boundary coverage until the corresponding slice is explicitly authorized and replaced.

## 23. Implementation Slices After Authorization

### Slice A: pure descriptors, classifier and reasons

- no UI/store integration;
- schemas, profile registry, validation results;
- pure tests using fixture descriptors.

### Slice B: instance-scoped lease ledger and fake materializer

- observable probe/preview/session leases;
- deterministic delay/fail/stale/duplicate outcomes;
- no provider/storage/network.

### Slice C: Add Resource multi-file vertical slice

- current source-shaped chooser/dialog entry;
- runtime provisional cohort;
- one accepted-success graph transaction;
- local fixture materializer only;
- focused `VR-021` scenes.

### Slice D: Generated History and registered asset reference attach

- preserve separate surfaces/provenance;
- local fixture data only;
- no account/backend claim.

### Slice E: Shot Breakdown source lifecycle

- local-preview versus durable/session-ready states;
- graph-media reference mode;
- source-version freeze and aggregate reset;
- no provider run.

### Slice F: Director data/blob convergence

- byte budget and session lease transfer;
- graph/history reachability;
- delete/undo/canvas lifecycle composition.

### Slice G: future real materializer adapter

- only after backend/API/security/product contracts;
- server validation, authentication, progress/cancel/retry, stable asset identity;
- no changes to frontend contract semantics.

Each slice needs separate user authorization. No slice may quietly include a real upload or source mutation.

## 24. Source Evidence Acquisition

Priority order:

1. inspect safe visible validation copy without selecting/uploading private media when possible;
2. use a disposable source fixture only with explicit authorization;
3. record accepted type/size/cardinality and placeholder timing;
4. record progress/cancel/retry/delete/switch behavior;
5. record multi-file success/error ordering and selection/history-visible behavior;
6. record generated-history attach placement and duplicates;
7. record asset registration and refresh persistence.

Every record must separate input metadata, visible state, graph result and any remote side effect. Open Canvas behavior cannot fill a LibTV source-evidence gap.

## 25. Open Canvas Adoption Result

Adopt:

- typed media descriptor;
- client plus trust-boundary validation;
- local metadata probe before final projection;
- stable asset identity plus render locator;
- deterministic entry-specific pipeline;
- explicit unsupported local boundary.

Adapt:

- placeholder timing;
- multi-file concurrency/partial success;
- autosaved progress state;
- digest dedupe;
- asset/history/node-reference surface mapping.

Reject transplant:

- extension fallback followed by stricter MIME rejection;
- no text/audio budgets;
- no upload cancel/stale owner;
- success toast after failed graph ownership;
- graph delete as an implicit cleanup signal;
- Open Canvas provider/storage/UI skin as LibTV product truth.

## 26. Stop And Maintenance Conditions

Do not implement while any proposed slice lacks:

- explicit coding authorization;
- entry profile and stable reason set;
- fixture/reset contract;
- canvas/node freshness owner;
- graph/history cardinality;
- lease transfer/release policy;
- prototype/source boundary copy.

Update this contract when:

- source upload/history/asset behavior is safely observed;
- node-data schema gains explicit media descriptors;
- portable document/import/export is implemented;
- real provider/storage APIs are authorized;
- graph history becomes deep/structured;
- object URL/resource registry is implemented;
- Director media persistence policy changes;
- Open Canvas submodule SHA changes.

## 27. Completion Criteria

The design is complete because it now defines:

- entry profiles and product-surface separation;
- immutable intent/source/owner identities;
- validation/probe/materialization/commit state machine;
- probe/preview/result lease ownership;
- asset identity versus node reference;
- cohort concurrency/partial success/history;
- async stale/cancel/idempotent convergence;
- graph/selection/history/feedback composition;
- reachability and release rules;
- honest no-backend prototype mode;
- 36 invariants and 14 decision questions;
- deterministic fixture `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`;
- verifier replacement design `LIBTV-VR-021`;
- implementation slices gated by authorization.

Runtime remains missing/partial and source parity remains partial. This status must not be upgraded from document completeness alone.
