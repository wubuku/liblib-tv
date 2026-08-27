# LibTV Media Ingress And Resource Lifecycle Static Audit

> Status: `COMPLETE` / `FIXED_STATIC_AND_READ_ONLY_SOURCE_AUDIT`.
>
> Scope: Open Canvas media ingress/resource methods and their implications for the ordinary LibTV clone route.
>
> Clone baseline: `6325a1f`; Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`.
>
> LibTV source observation: 2026-08-27, authenticated read-only DOM at the project URL already recorded in this repository.
>
> Authorization boundary: no runtime/test/submodule changes; no local file selected; no source upload, generation, save, download, delete or paid action.

## 1. Why This Audit Exists

The repository already knows how to classify media strings after they are present in node data. It does not yet describe the complete path by which bytes or an existing asset become node data, nor the path by which those bytes can eventually be released.

That missing path matters to UI/UX fidelity. A source-shaped `上传` button is not a faithful clone when it cannot answer:

- whether one or many files are accepted;
- when a node first appears;
- what is visible during validation and upload;
- whether failure leaves a retryable node;
- whether the selected file survives refresh, copy and undo;
- what happens if the node or canvas disappears before upload completion;
- whether `素材库`, `生成历史` and `资产管理` refer to the same repository of media.

This audit supplies fixed facts and counterexamples before a normative contract is written. It does not authorize implementing an upload backend.

## 2. Authority Boundary

This document owns dated evidence and gap classification only.

| Existing authority | Existing responsibility | This audit adds |
|---|---|---|
| [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) | locator classes and field roles | how a locator is first produced |
| [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md) | portable document boundary | when ingress becomes portable or remains session-only |
| [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | delayed result freshness and transfer/release | file/asset intent before generic result ingress |
| [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | delete impact and cleanup delegation | resource reachability created by ingress |
| [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | drop coordinate conversion and placement | what each dropped item means and when it commits |
| [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md) | named semantic graph/history commands | ingress command candidates and transaction cardinality |
| [`liblib-canvas-batch12-2026-08-25/`](liblib-canvas-batch12-2026-08-25/README.md) | historical asset-panel clone slice | current source asset/media ownership interpretation |
| [`liblib-canvas-batch15-2026-08-25/`](liblib-canvas-batch15-2026-08-25/README.md) | historical Add Node menu clone slice | current source upload/history/material drift |
| [`liblib-canvas-batch17-2026-08-25/`](liblib-canvas-batch17-2026-08-25/README.md) | historical asset-drawer clone slice | node inventory versus account/Agent asset distinction |

The future normative authority is reserved as `LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`.

## 3. Evidence Method

### 3.1 Evidence classes

| Label | Meaning |
|---|---|
| `OPEN_CANVAS_FACT` | directly present at the fixed submodule SHA |
| `CLONE_FACT` | directly present in committed clone code |
| `LIBTV_SOURCE_FACT` | visible in the authenticated source DOM without mutation |
| `INFERENCE` | consequence supported by facts but not directly exercised |
| `CLONE_DECISION` | recommended policy for the future contract |
| `SOURCE_UNKNOWN` | source behavior not safely established |

### 3.2 Fixed Open Canvas paths

- `shared/blocks/canvas/canvas-media-control.tsx`
- `shared/blocks/canvas/canvas-studio-shell.tsx`
- `shared/blocks/common/asset-picker-dialog.tsx`
- `shared/stores/canvas-store.ts`
- `shared/lib/canvas/types.ts`
- `shared/lib/canvas/serialization.ts`
- `lib/uploads.ts`
- `app/api/canvas/uploads/images/route.ts`
- `app/api/canvas/uploads/videos/route.ts`
- `app/api/storage/upload-audio/route.ts`

### 3.3 Fixed clone paths

- `src/components/AddNodePanel.tsx`
- `src/components/nodes/ShotBreakdownNode.tsx`
- `src/components/PictureEditPanel.tsx`
- `src/components/AssetManagerPanel.tsx`
- `src/store/canvasStore.ts`
- `src/components/director/directorLocalModelImport.ts`
- `src/components/director/directorVideoExport.ts`
- `src/components/director/DirectorDesk.tsx`
- `src/components/director/DirectorViewport.tsx`

### 3.4 Live read-only actions

The browser work was limited to:

1. reading the current canvas DOM;
2. opening Add Node, generated-history picker, material library and asset manager surfaces;
3. observing file-input attributes and whether the Add Node upload chooser allows multiple files;
4. switching generated-history media tabs;
5. reading asset filter labels.

No file chooser received a file. A file-chooser event was observed and abandoned without calling `setFiles`.

## 4. Executive Findings

### 4.1 Open Canvas has an end-to-end upload path, not an end-to-end lifecycle contract

`OPEN_CANVAS_FACT`: image and video can enter through an existing node control or whole-canvas drop. The code validates client-side, probes metadata, uploads to configured storage, receives a stable URL/storage key and projects a normalized `CanvasNodeMedia` into node data. The server repeats MIME/size/empty validation and can deduplicate by file digest.

`INFERENCE`: this is materially stronger than a component-local preview, but it does not close cancellation, stale completion, delete-during-upload, orphaned remote asset, history reachability or asset deletion. It is an implementation reference, not a lifecycle-safe template.

### 4.2 Ordinary LibTV clone ingress is still mostly presentational

`CLONE_FACT`:

- Add Node `上传` and `从生成历史选择` only set local explanatory text;
- Shot Breakdown creates a component-local object URL preview and writes filename/mock duration to graph data;
- picture-edit replacement buttons store only a local source label;
- the ordinary route has no whole-canvas file drop, file paste, upload service or asset registry;
- Director has real browser byte paths, but those belong to a separate 3D workspace and must not be generalized as the ordinary canvas contract.

### 4.3 LibTV source presents four different media domains

`LIBTV_SOURCE_FACT` identifies four visually adjacent but semantically different domains:

1. Add Resource upload: multi-file image/video/audio chooser;
2. Generated History: source-system/media-type picker with a ten-item selection cap;
3. Material Library: current side surface for style and effect node creation;
4. Asset Manager: canvas-node index plus a separate Personal/Agent asset tab.

`INFERENCE`: one generic local `MaterialLibraryPanel` cannot truthfully stand in for all four domains.

### 4.4 Highest-value design conclusion

The clone should not start with a real provider. The highest-value next implementation, if authorized later, is a deterministic local ingress fixture that proves:

```text
intent identity
  + validation result
  + temporary lease ownership
  + canvas/node freshness
  + one final graph projection
  + history cardinality
  + exact-once release
```

That slice would improve source-shaped progress/error/retry UI while remaining honest about the missing backend.

## 5. Open Canvas Ingress Surface Inventory

| Surface | Input | Timing | Projection | Current limitation |
|---|---|---|---|---|
| existing image node | one file | node already exists; status becomes running | `image`, output history, selected index, aspect ratio | no operation identity/cancel |
| existing video node | one file | node already exists; status becomes running | `video`, video history, selected index, duration | no operation identity/cancel |
| whole-canvas image drop | one item in sequential cohort | creates node before strict validation | uploaded image and output history | invalid item leaves error node |
| whole-canvas video drop | one item in sequential cohort | creates node before strict validation | uploaded video and history | invalid item leaves error node |
| whole-canvas audio drop | one item in sequential cohort | creates node before upload | audio media | local OSS endpoint always reports unavailable |
| whole-canvas text drop | one item in sequential cohort | creates node before `file.text()` | `plainText` and title | no byte budget; read error lacks node error projection |
| image-editor save | exported image file | existing node becomes running first | appends stable upload to image outputs | no cancellation/stale owner |
| asset picker | `AssetItem` reference | intended direct attach | media descriptor with `assetId` | fixed local OSS dialog is unavailable and does not select |
| clipboard node paste | normalized node snapshots | immediate | media descriptors are aliased into copied node data | no resource/ref-count policy |
| graph save | normalized graph JSON | 1.2s dirty debounce | URLs and asset IDs persist | intermediate running/error state may save |

## 6. Fixed Open Canvas Pipeline

### 6.1 Existing-node file input

```text
file chooser
  -> reset native input value
  -> set component isUploading
  -> patch node status=running
  -> validate MIME / non-empty / byte limit
  -> probe dimensions or duration
  -> POST multipart file
  -> validate response media.url
  -> normalize media descriptor
  -> patch node media/history/status=success
  -> toast success
```

On error, the node receives `status=error` and a translated message. The native input is reset before async work, allowing the same file to be selected again.

### 6.2 Whole-canvas drop

```text
dragenter/dragover
  -> drag-depth overlay state
drop
  -> screenToFlowPosition(drop point)
  -> classify each file by MIME OR extension
  -> sequential for-await loop
  -> create node at base + index offset
  -> patch title/inputMode/status=running
  -> strict validation and metadata probe
  -> upload
  -> patch success or error
```

Placement belongs to the viewport contract. This audit owns the fact that each item is processed sequentially and commits through multiple node-data updates.

### 6.3 Server materialization

The fixed server path:

1. parses multipart form data;
2. selects the first file;
3. normalizes `file.type`;
4. checks the media-specific MIME map;
5. checks empty/maximum bytes;
6. dispatches to Cyberbara storage or configured S3-compatible storage;
7. for S3-compatible storage, reads the full body and computes an MD5 digest;
8. builds `canvas/uploads/{images|videos}/{digest}.{ext}`;
9. returns an existing public URL when the key already exists;
10. otherwise uploads and returns URL, key, content type, size and dedupe status.

The route projects the storage key as `assetId`. The node does not store `deduped`, storage provider or a cleanup token.

## 7. Validation And Metadata Matrix

| Family | Client accept | Client budget | Metadata probe | Server validation | Audit result |
|---|---|---:|---|---|---|
| image | JPEG/JPG/PNG/WebP/GIF/SVG/AVIF/HEIC/HEIF MIME | 10 MiB | `createImageBitmap`, otherwise object URL + `Image` | same MIME family, empty, 10 MiB | strong duplicate gate, but not content sniffing |
| video | MP4/MOV MIME | 50 MiB | object URL + `<video preload=metadata>` | MP4/MOV/WebM MIME, empty, 50 MiB | server admits WebM that current client does not |
| audio | MP3/WAV MIME | none in canvas creator | none | local route reports unsupported | visible path exists but cannot succeed locally |
| text | plain/Markdown MIME or extension | none | `file.text()` | none | unbounded text can enter node data |

### 7.1 Positive methods

- Client validation provides immediate feedback before transmitting bytes.
- Server repeats trust-boundary validation instead of trusting UI controls.
- Metadata is obtained before projection, so node settings can reflect actual dimensions/duration.
- Short-lived object URLs used by fallback probes are revoked on success and error.
- Stable returned URL and storage key are separated from the original `File` object.

### 7.2 Counterexamples

1. Whole-canvas classification accepts extensions that downstream media creators reject when `file.type` is empty or unexpected.
2. `createImageBitmap` is used whenever available; failure for a browser-unsupported accepted image format does not fall back to the object-URL path.
3. The server checks the browser-provided MIME string, not file magic bytes.
4. Video server support includes WebM, while client accept/drop gates exclude it.
5. Text has no byte/character budget and no node-level error projection if `file.text()` rejects.
6. Audio creates a node even though the fixed local endpoint cannot upload it.
7. Full file bytes are materialized for digest calculation after multipart parsing; memory behavior is not bounded by a streaming contract.

These are `REJECT_TRANSPLANT` details, not reasons to reject the overall validation/materialization method.

## 8. Media Identity And Resource Classes

### 8.1 Open Canvas identities

| Identity | Example role | Lifetime |
|---|---|---|
| `File` object | selected local bytes | current JS operation |
| object URL | metadata probe | until probe success/error |
| digest | storage dedupe key input | server materialization |
| storage key / `assetId` | stable storage identity | backend-defined |
| public URL | render/provider locator | node/document lifetime |
| thumbnail URL | display optimization | media descriptor lifetime |
| node ID | graph projection owner | canvas document lifetime |
| run ID | generated-media operation | execution lifecycle, not file upload |

### 8.2 What Open Canvas gets right

The node receives a media descriptor rather than a raw `File`, `Blob` or object URL. Image/video uploads therefore become graph-serializable references. `assetId` is preferred over URL when media history deduplicates entries.

### 8.3 What remains unresolved

- Node duplication and clipboard paste preserve the same media descriptor; no alias/ref-count metadata is added.
- Node deletion removes graph references but does not call an asset owner.
- Upload completion after node deletion can produce an unreferenced remote object.
- Canvas switching/unmount has no upload cancellation or result-owner check.
- Storage deduplication means two nodes can intentionally share one asset; graph deletion cannot imply byte deletion.
- The fixed store has save/revision state but no undo/redo stack, so it does not solve clone history reachability.

## 9. Placeholder, Save And Concurrency Behavior

### 9.1 Placeholder-first is a product choice, not a universal rule

Whole-canvas drop creates and selects a node before validation. This provides immediate spatial feedback and a durable error surface, but it also means:

- unsupported/empty/oversize items consume node IDs and graph positions;
- a mixed cohort can leave success and error nodes;
- a rejected item is not a zero-mutation command;
- graph save may persist a running/error placeholder.

Existing-node upload naturally cannot defer node creation, so it needs a different policy. The future LibTV contract must specify each entry profile instead of applying one generic rule.

### 9.2 Autosave can observe intermediate state

Every node patch marks the Open Canvas graph dirty. A 1.2-second debounce saves the current graph. A slow upload can therefore save `status=running` without an upload operation descriptor capable of resuming after reload.

`INFERENCE`: persistence of visible progress is useful only when operation identity and recovery semantics are also persistent. Otherwise it is a stranded status snapshot.

### 9.3 Missing freshness checks

The upload closures retain a node ID but not:

- expected canvas ID/generation;
- expected node version;
- operation ID/attempt ID;
- cancellation signal;
- final field-owner token.

If the node is removed before completion, `updateNodeData` can fail to find it, but callers do not consistently consume that result. A success toast can still be emitted and a durable uploaded asset can remain unreferenced.

### 9.4 Multi-file cohort semantics

Multi-file drop is sequential:

- order is deterministic;
- one slow/failed item delays later items;
- each item can independently succeed or fail;
- each item mutates the graph several times;
- there is no cohort-level cancel, rollback, progress or one-step history.

LibTV can borrow deterministic placement/order while choosing a different commit/history policy.

## 10. Current LibTV Clone Audit

### 10.1 Surface classification

| Clone surface | Current state | Bytes/locator | Graph effect | Classification |
|---|---|---|---|---|
| Add Node `上传` | status text only | none | none | `MOCK` |
| Add Node `从生成历史选择` | status text only | none | none | `MOCK` |
| Add Node `素材库` | clone-only My/Preset submenu | repo presets | opens local material panel | `PARTIAL_AND_DRIFTED` |
| Shot Breakdown upload | native single video chooser | component object URL | ready + filename + mock duration | `LOCAL_PREVIEW_ONLY` |
| Shot Breakdown canvas choice | hard-coded coffee video | repo poster | ready metadata | `MOCK` |
| Picture replacement upload | button only | none | component source label | `MOCK` |
| Picture replacement history | button only | none | component source label | `MOCK` |
| ordinary image/video/audio node | repo paths/default strings | repo locators | normal graph data | `STATIC_FIXTURE` |
| Director local model import | FBX/OBJ to data URL | embedded data URL | Director library/store | `FUNCTIONAL_LOCAL_SUBSYSTEM` |
| Director capture | canvas image to data URL | embedded data URL | creates image node | `FUNCTIONAL_NON_PORTABLE` |
| Director animation export | recorded Blob to object URL | session blob URL | creates video node | `FUNCTIONAL_SESSION_ONLY` |

### 10.2 Shot Breakdown preview lifecycle

`CLONE_FACT`:

- `accept="video/*"` constrains the chooser but no MIME/size/empty validation is performed in the handler;
- the selected file becomes a component-local object URL;
- prior preview URL is revoked on replacement;
- the current URL is revoked by effect cleanup;
- graph data stores filename and a fixed duration, not the preview URL or real media identity;
- `updateNodeData` records a graph history step for this metadata patch.

Consequences:

- the visible preview does not survive remount, refresh or canvas switch;
- undo can restore graph metadata without restoring the same local bytes;
- `status=ready` overstates media recoverability;
- running Shot Breakdown later uses graph readiness that is disconnected from the component-only preview owner.

### 10.3 History and copy

The clone keeps up to 50 per-canvas graph snapshots. Snapshot cloning and node duplication shallow-copy node data. Media strings are therefore repeated/aliased without a resource identity or reachability ledger.

For repo/remote strings this is primarily a semantic identity problem. For `data:` it can amplify memory/serialized size. For `blob:` it can make several graph/history entries depend on one BrowserContext locator without declaring who may revoke it.

### 10.4 Delete and canvas lifecycle

Ordinary remove actions delete nodes/edges and push history. They do not invoke resource cleanup. That is currently correct for shared repo/remote media and unsafe to change without an owner contract. It also means Director blob URLs have no graph-delete disposal path.

This gap is already recognized by the delete/resource matrix; this audit adds the ingress-side requirement to register ownership before cleanup can ever be correct.

### 10.5 Route isolation

FrameOS contains separate browser-file behaviors. They are not evidence for ordinary LibTV and must remain isolated with `frameosStore`. The future LibTV contract must not gain a route `mode` flag or reuse FrameOS object URLs as cross-route assets.

## 11. LibTV Source Read-Only UI Evidence

### 11.1 `LIBTV-SRC-MIR-001`: Add Resource upload

Observed Add Node menu:

- `添加资源` section contains `上传` and `从生成历史选择`;
- activating `上传` produces a multiple file chooser;
- the associated current input accepts `image/*,video/*,audio/*`;
- no file was selected, so validation, progress, placement and final graph behavior remain unknown.

### 11.2 `LIBTV-SRC-MIR-002`: Generated History picker

Observed picker structure:

- defaults to `选择图片`;
- source-system filters: `LibTV`, `Lib生成器`, `WebUI`, `ComfyUI`, `AI应用`;
- media tabs: `图片`, `视频`, `音频`;
- selected counter: `0/10`;
- image view exposes pagination and `15条/页`;
- confirm is disabled at zero selection;
- current video/audio views displayed `暂无数据`;
- video/audio still displayed the image unit `张`, a current source copy inconsistency rather than a clone requirement.

### 11.3 `LIBTV-SRC-MIR-003`: Material Library is not account media history

The current bottom-toolbar `素材库` opens a side surface with:

- `风格库` and `新增风格节点`;
- `特效库` and `新增特效节点`.

This supersedes the old clone-only assumption that Add Node `素材库` should expand to `我的素材库 / 预设素材库`.

### 11.4 `LIBTV-SRC-MIR-004`: Asset Manager has two domains

The Asset Manager dialog exposes:

- `画布` tab: searchable/filterable node and group inventory with locate/more actions;
- `资产` tab: `个人` and `Agent` sources, search, type filter and current empty state;
- asset type tags: `其它`, `人物`, `场景`, `物品`, `风格`, `音效`.

The observed canvas contained image/video nodes while the asset tab reported `暂无资产`.

`INFERENCE`: visible node media is not automatically sufficient evidence of a registered project/account asset. A future clone must model node references and reusable assets as separate identities even if a local fixture maps one to the other.

### 11.5 `LIBTV-SRC-MIR-005`: Shot Breakdown source

The current node exposes a single `video/*` file input and `上传视频后开始`. Existing source research also records `从画布选择`, `画布上暂无可用视频`, `替换素材`, `拉片中`, retry and upstream-not-ready copy.

This supports a source-shaped node surface with upload and graph-reference modes. It does not prove backend validation or resource lifetime.

### 11.6 `LIBTV-SRC-MIR-006`: Dormant generic uploader

The loaded DOM also contained a hidden multiple uploader accepting image/video/audio, with its visible dashed trigger set to `display:none`. It is evidence of bundled/inactive UI structure only, not an active source command.

## 12. Open Canvas To LibTV Translation

| Open Canvas method | LibTV value | Decision candidate | Required adaptation |
|---|---|---|---|
| normalized media descriptor | high | `ADOPT_METHOD` | use explicit locator class and prototype provenance |
| client + server validation | high | `ADOPT_METHOD` | stable reason taxonomy and real content checks later |
| short metadata-probe object URL | high | `ADOPT_METHOD` | explicit lease owner and exact-once release |
| stable asset ID plus render URL | high | `ADAPT_TO_LIBTV` | distinguish project asset, history result and node ref |
| digest deduplication | medium | `RESEARCH_ONLY` | backend concern; no frontend fake |
| immediate drop placeholder | medium | `ADAPT_TO_LIBTV` | entry-specific policy and retry semantics |
| sequential multi-file drop | medium | `ADAPT_TO_LIBTV` | cohort progress/cancel and declared history |
| persist running/error node state | medium | `ADAPT_TO_LIBTV` | only with operation identity/recovery |
| extension fallback before strict MIME | low | `REJECT_TRANSPLANT` | one canonical classifier |
| no stale/delete cleanup | negative | `REJECT_TRANSPLANT` | compose async freshness/resource ledger |
| unavailable local asset picker | boundary | `RESEARCH_ONLY` | do not claim source parity |
| visual skin/provider settings | none | `REJECT_TRANSPLANT` | preserve LibTV product/UI evidence |

## 13. Ranked Findings

### P0: no ordinary-media ingress authority

The clone has visible upload/history surfaces but no shared intent, validation, lease, materialization, projection or release owner. Adding another local input directly to a node would deepen the divergence.

### P0: graph readiness can diverge from byte readiness

Shot Breakdown writes `ready` while its actual preview remains component-local. Undo/remount/switch can preserve graph metadata while losing bytes.

### P0: delayed materialization needs canvas/node freshness

Open Canvas demonstrates that a stable upload can finish after its graph owner disappears. LibTV already has multi-canvas generations and history, so ingress must compose with async authority from the first implementation slice.

### P1: generated history, material library and asset manager are conflated

Historical clone decisions route several source concepts to one local material panel. Current source observation proves separate surfaces and taxonomies.

### P1: locator strings hide ownership

Repo, remote, data and blob strings can render in the same UI but have incompatible copy/save/release rules. Ingress must produce an explicit class/provenance record even if node V0 remains string-backed temporarily.

### P1: history reachability has no resource ledger

The clone's 50-step history retains media aliases. Immediate revoke on graph deletion would break undo; never revoke leaks session resources. Reachability must be observable before any cleanup implementation.

### P1: validation and metadata are not shared

Shot Breakdown accepts wildcard video with no size/empty/duration check. Director local model import filters filename extension and embeds full data URLs without a byte budget. These are different profiles but need a common reason/result vocabulary.

### P2: source picker copy and dormant surfaces must not become parity requirements

The source picker uses `张` for video/audio and the DOM includes an inactive uploader. These are current implementation details, not desired clone behavior.

## 14. Clone Issue Register

| ID | Issue | Current evidence | Owner recommendation |
|---|---|---|---|
| `LIBTV-MIR-001` | ordinary Add Node upload is mock | `AddNodePanel.tsx` | ingress command owner |
| `LIBTV-MIR-002` | generated-history picker absent | source DOM + AddNode mock | asset/history picker surface |
| `LIBTV-MIR-003` | material submenu meaning drifted | source material side surface | parity backlog + Add Node spec |
| `LIBTV-MIR-004` | node media and reusable assets conflated | source Asset Manager split | asset-reference authority |
| `LIBTV-MIR-005` | Shot Breakdown preview is component-only | object URL local state | preview lease owner |
| `LIBTV-MIR-006` | Shot Breakdown ready state is non-restorable | graph metadata without locator | node ingress state machine |
| `LIBTV-MIR-007` | no ordinary route-wide media drop | no handler in ordinary route | command + viewport composition |
| `LIBTV-MIR-008` | no file-paste media ingress | clipboard only graph behavior elsewhere | command-context + ingress |
| `LIBTV-MIR-009` | validation profiles are ad hoc | wildcard/extension/file reader differences | validator registry |
| `LIBTV-MIR-010` | no upload operation identity | no ordinary upload service | async ingress composition |
| `LIBTV-MIR-011` | no stale canvas/node guard | multi-canvas + future delayed result | operation descriptor |
| `LIBTV-MIR-012` | no asset/lease ledger | plain strings/local state | resource registry |
| `LIBTV-MIR-013` | copy/history alias resources silently | shallow node data snapshots | node-data/document authority |
| `LIBTV-MIR-014` | delete cannot safely release bytes | delete only edits graph/history | delete/resource composition |
| `LIBTV-MIR-015` | Director blob locator is graph-visible session state | animation export node | Director async/resource slice |
| `LIBTV-MIR-016` | data URL budgets are not enforced at ingress | Director import/capture | document + validator registry |

## 15. Open Canvas Evidence Claims

| ID | Fixed evidence | Claim | Cannot prove |
|---|---|---|---|
| `OC-061` | media-control accept lists, budgets and probes | existing-node image/video validation and metadata method | LibTV limits or source feedback |
| `OC-062` | client multipart helpers and canvas upload routes | stable media descriptor returned to node | storage deletion/lease policy |
| `OC-063` | `lib/uploads.ts` | server MIME/empty/size gate and digest-key dedupe | content sniffing or collision policy |
| `OC-064` | shell drag handlers | file-only drag detection and screen-to-flow drop origin | LibTV source drop behavior |
| `OC-065` | shell media creator | placeholder-first running/success/error projection | atomic history or retry correctness |
| `OC-066` | shell `for ... files.entries()` with `await` | deterministic sequential multi-file processing | cohort transaction/cancel |
| `OC-067` | text/audio creators and audio route | asymmetric family support and local audio failure | hosted upstream capability |
| `OC-068` | media normalization, duplicate/paste/save | descriptor aliases survive graph operations | resource reference counting |
| `OC-069` | local asset-picker dialog | shared asset library is explicitly unavailable in fixed OSS shell | source LibTV asset behavior |
| `OC-070` | upload closures + store result handling + autosave | no explicit file-upload freshness/cancel/resource convergence | observed production leak rate |

## 16. Handoff Requirements For The Formal Contract

The formal contract must resolve these objects rather than adding more UI-specific booleans.

### 16.1 Ingress intent

Minimum identity:

```text
ingressId
entryProfile
canvasId + canvasGeneration
targetNodeId? + expectedNodeVersion?
cohortId? + itemIndex?
sourceKind
declared file descriptor or existing asset identity
placement policy
createdAt
```

### 16.2 Resource handle

Minimum resource classes:

- local `File`/bytes owner;
- metadata-probe object URL lease;
- preview object URL lease;
- embedded data URL with byte budget;
- stable repo locator;
- stable remote URL with provenance;
- future asset ID plus render URL;
- cleanup token owned outside graph data.

### 16.3 State machine

Required states:

```text
intent
  -> validating
  -> probing
  -> materializing
  -> ready-to-commit
  -> committed

any nonterminal
  -> failed | canceled | stale
```

`running` alone is insufficient because validation, local probe and remote materialization have different retry and release consequences.

### 16.4 Final commit

The accepted final projection must declare:

- node create versus existing-node patch;
- locator and provenance fields;
- metadata fields;
- selection result;
- one history policy;
- operation terminal result;
- resource ownership transfer;
- feedback owner.

### 16.5 Reachability

Release decisions must consider:

- current graph;
- history past/future;
- clipboard packet;
- open preview/editor;
- active ingress operation;
- reusable asset registry;
- exported/persisted document when relevant.

## 17. Future Source Evidence Queue

Use a disposable/read-only-safe fixture before claiming exact parity for:

1. accepted type/size limits and source reason copy;
2. placeholder timing before/after upload;
3. progress, cancel and retry controls;
4. failure node retention or rollback;
5. same-file and multi-file placement/order;
6. canvas switch or node delete during upload;
7. generated-history multi-selection projection;
8. asset registration after upload or generation;
9. refresh/save restoration of uploaded media;
10. Shot Breakdown replace and graph-selected video behavior.

Do not obtain this evidence by uploading private media or using paid/provider actions without explicit authorization.

## 18. Verification Implications

The future `LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` should use synthetic in-memory files and a fake materializer. It must expose:

- validation reason log;
- metadata probe count;
- object URL lease create/revoke count;
- upload resolver queue;
- graph/history before/after;
- canvas/node generation;
- asset/reference ledger;
- feedback events.

The future `LIBTV-VR-021` must reject a visually successful result when any of these fail:

- stale result mutates graph;
- canceled result commits;
- invalid file partially mutates under a commit-on-success profile;
- placeholder profile lacks an explicit error/retry result;
- history count differs from the declared profile;
- object URL releases zero or more than once after ownership ends;
- graph deletion destroys a resource still reachable from history;
- blob/data locator is represented as durable without conversion/budget.

## 19. Conclusion

Open Canvas contributes a concrete and valuable pipeline: validate, probe, materialize, normalize and project. Its fixed implementation also demonstrates why that pipeline is not enough: placeholder-first partial mutation, mismatched classifiers, sequential cohorts, autosaved running state and absent freshness/cleanup authority remain open.

Current LibTV source UI further shows that upload, generated history, material library and asset management are distinct product surfaces. The clone currently collapses them into mocks or one local panel and has no ordinary-media lifecycle owner.

The next document must therefore be a normative ingress/resource contract, not another upload-panel spec. It should preserve the source surface distinctions, reuse Open Canvas's typed pipeline method, and compose the repository's existing viewport, async, document, history and delete authorities.
