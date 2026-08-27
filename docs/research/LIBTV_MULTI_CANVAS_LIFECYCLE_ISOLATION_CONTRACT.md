# LibTV Multi-Canvas Lifecycle And Isolation Contract

> Scope: 普通 LibTV route 的 project/canvas registry、create/switch/rename/duplicate/delete、per-canvas graph/viewport/history、selection、node-bound UI、page-local transaction、async/resource owner，以及 Open Canvas 固定版本对这些边界的正反面启发。
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL`。本文只记录研究和实施约束，不授权修改 `src/`、测试、Open Canvas submodule、FrameOS、持久化后端或共享源站状态。
>
> Clone baseline: `024e351`（2026-08-27）。
>
> Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`。

## 1. Why This Contract Exists

“多画布”不是在下拉菜单里放一个 `canvases[]` 就完成了。切换 active canvas 会同时改变或保留多种状态：

- project-level canvas registry 和 metadata；
- 每张 canvas 的 graph、viewport 和 history；
- 当前 selection；
- 节点绑定的 toolbar、panel、preview、annotate、element edit 和 Director；
- asset/history/agent/add-node 等投影型 panel；
- organize preview、drag baseline、pending connection 等 page-local transaction；
- component timer、browser export 或 future provider run；
- media/resource ownership；
- future dirty/save/revision/conflict owner。

这些状态如果只依赖“当前 activeCanvasId 是什么”而没有 captured owner，旧画布上的 delayed callback、drag stop、viewport event 或 restore command 就可能写到新画布。反过来，如果切换时把所有状态一律清空，又会丢失每张画布应保留的 viewport/history，或错误关闭 project-level preference。

当前 Batch 16 已完成下拉菜单、新建、切换、重命名、复制、删除和内存项目名的 UI/fixture；Batch 58 已让四类 node-bound owner 带 `canvasId + nodeId` 并在切换后关闭。它们是有价值的局部实现，但还不是完整 lifecycle contract：

- `setActiveCanvas` 不验证 ID；
- selection 是 global active projection，history 是 per-canvas map；
- viewport 看似 per-canvas，但 demo canvas 有 route effect 强制 preset；
- organize snapshot、drag history baseline 和 connection gesture 没有 canvas owner；
- generic/async store action 多数在执行时读取 active canvas，而不是提交时声明目标 canvas；
- duplicate/delete 对 node-data aggregate、resource 和 external operation owner 仍不完整。

本文给出统一设计：

```text
canvas lifecycle proposal
  -> resolve project registry and target canvas identity
  -> classify every state owner
  -> plan graph/document/history/viewport/session/UI/async/resource effects
  -> validate active/fallback/duplicate/delete invariants
  -> commit lifecycle state once
  -> reconcile UI and external side effects from an explicit result
```

本文组合而不替代：

- [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)；
- [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)；
- [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)；
- [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)；
- [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)；
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)；
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)。

## 2. Evidence And Claim Boundary

### 2.1 `OPEN_CANVAS_FACT`

固定 submodule 的主要证据：

- [`components/canvas-list-page.tsx`](../../research/upstream/open-canvas/components/canvas-list-page.tsx)；
- [`components/open-canvas-shell.tsx`](../../research/upstream/open-canvas/components/open-canvas-shell.tsx)；
- [`app/[locale]/canvas/page.tsx`](../../research/upstream/open-canvas/app/%5Blocale%5D/canvas/page.tsx)；
- [`app/[locale]/canvas/[canvasId]/page.tsx`](../../research/upstream/open-canvas/app/%5Blocale%5D/canvas/%5BcanvasId%5D/page.tsx)；
- [`app/api/canvas/route.ts`](../../research/upstream/open-canvas/app/api/canvas/route.ts)；
- [`app/api/canvas/[canvasId]/route.ts`](../../research/upstream/open-canvas/app/api/canvas/%5BcanvasId%5D/route.ts)；
- [`shared/models/local-canvas-store.ts`](../../research/upstream/open-canvas/shared/models/local-canvas-store.ts)；
- [`shared/stores/canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts)；
- [`shared/blocks/canvas/canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)；
- [`shared/lib/canvas/types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts)。

### 2.2 `CLONE_FACT`

Clone baseline 的主要证据：

- [`src/store/canvasStore.ts`](../../src/store/canvasStore.ts)；
- [`src/store/uiStore.ts`](../../src/store/uiStore.ts)；
- [`src/app/page.tsx`](../../src/app/page.tsx)；
- [`src/components/CanvasTabDropdown.tsx`](../../src/components/CanvasTabDropdown.tsx)；
- Batch 16 canvas metadata 和 Batch 58 owner reconciliation 记录。

### 2.3 `DECISION`

本文的 owner classes、lifecycle plan/result、invariants、fixture、verifier 和实施切片是 clone-only correctness design。它不声称来自 LibTV 源站，也不自动授权编码。

### 2.4 Explicit exclusions

- 不把 Open Canvas 的列表页、URL 路由、视觉卡片或最近更新时间排序复制成 LibTV UI；
- 不把 Open Canvas file/KV、revision、autosave、conflict、template、provider 或 login 变成当前 clone 产品范围；
- 不决定 LibTV 源站删除最后一张画布、fallback 相邻项、复制资源或切换时 panel 保留的真实语义；
- 不把普通 LibTV lifecycle 规则推广到独立 FrameOS store；
- 不操作共享源站的画布新建、复制、重命名、删除、保存或生成；
- 不修改 Batch 60 或其他开发者的并行 WIP。

## 3. Owner Model

### 3.1 Five state domains

| Domain | Identity | Examples | Expected lifetime |
|---|---|---|---|
| `PROJECT_REGISTRY` | project/session | projectName、ordered canvas descriptors、activeCanvasId | outlives one canvas switch |
| `CANVAS_DOCUMENT` | canvasId | name、nodes、edges、viewport、future revision | preserved while canvas exists |
| `CANVAS_HISTORY` | canvasId | graph past/future | preserved across switch；removed with canvas |
| `ACTIVE_SESSION` | active canvas generation | selection、zoom projection、node-bound UI、transaction refs | reset/rebind/cancel on switch |
| `EXTERNAL_OWNER` | canvasId + operation/resource ID | async run、Director workspace、blob/media | explicit transfer/cancel/detach；not implied by graph alone |

### 3.2 Why `activeCanvasId` alone is insufficient

`activeCanvasId` answers “what is active now”. It does not answer：

- which canvas began this drag/organize/export/run；
- whether a callback planned against an earlier active generation；
- whether a preview is a live node owner or detached media snapshot；
- whether a blob belongs to a canvas result、Director workspace or pending operation；
- whether a duplicate should share、copy、reset or reject a resource/reference。

Every delayed or multi-step action therefore needs captured owner identity, not a late read of whichever canvas happens to be active.

### 3.3 Canvas generation

For local runtime protection, a lifecycle adapter may use a monotonic active generation/epoch in addition to `canvasId`：

```text
ActiveCanvasOwner = { canvasId, generation }
```

The exact implementation is open. The invariant is not: a plan begun under generation N cannot commit to generation N+1 merely because both observations resolve to a valid store.

## 4. Open Canvas Lifecycle Audit

### 4.1 Registry and document identity

Open Canvas separates canvas summary from full record：

```text
CanvasDocumentSummary
  id / title / status / revision
  preview counts + hero/text summary
  lastOpenedAt / createdAt / updatedAt

CanvasDocumentRecord
  summary fields
  + SerializedCanvasGraph(version/nodes/edges/viewport)
```

The list route loads summaries; a URL-scoped `/canvas/[canvasId]` page loads one record by stable ID and calls `notFound()` when absent. The studio store holds one `canvasId`, not an in-memory array plus active index.

High-value method：registry/list projection and active document are separate boundaries. A summary does not masquerade as the full editable graph.

### 4.2 Create, rename and open

Fixed behavior：

- create makes an empty graph document with UUID, title, revision 1, active status, preview and timestamps；
- list UI inserts the returned summary and navigates to its URL；
- rename requires a non-empty trimmed title at the API boundary and updates `updatedAt`；
- opening a missing ID returns not-found rather than a blank editor with invalid owner；
- list items are sorted by updated/created time；“latest” uses that list order；
- the studio links back to the list instead of switching another graph in-place。

These are product facts for Open Canvas only. LibTV's current in-place dropdown and active-first ordering remain separate source/clone behavior.

### 4.3 Delete and final fallback

Open Canvas delete：

1. confirms in list UI；
2. deletes the document by ID；
3. removes all stored runs whose `canvasId` matches；
4. if the registry becomes empty, creates a new empty document；
5. refreshes the list from server state。

The valuable method is explicit document/run ownership cleanup plus a valid-registry postcondition. The exact fallback differs from clone：current clone refuses to delete the final canvas rather than replacing it。

### 4.4 Hydrate as an active-document boundary

`hydrate(canvas)` atomically replaces：

- canvasId；
- flow nodes/edges；
- viewport；
- revision and saved graph baseline；
- hydrated/dirty/save/error/conflict status。

Serialized graph conversion does not preserve runtime selection, so old selection does not intentionally cross documents. The studio hydration effect also resets title/saved title/edit-title state and applies the persisted viewport to React Flow。

This is a useful full-owner replacement pattern. A canvas switch should not be implemented as a sequence of unrelated node/edge/viewport setters that exposes an intermediate mixed document。

### 4.5 Viewport ownership

Open Canvas stores viewport inside `SerializedCanvasGraph`：

- hydrate restores it；
- React Flow viewport changes normalize it and mark the document dirty；
- save serializes graph + viewport together；
- conflict rebase explicitly chooses local or remote viewport。

LibTV does not have to copy “viewport is a durable save edit”. The transferable method is that viewport owner is one canvas identity and restore is explicit.

### 4.6 Async and route-lifecycle limitation

The fixed implementation's graph PUT uses the explicit `initialCanvas.id`, which prevents the server request from accidentally writing another durable document. But the later global-store `finishSave/failSave/enterConflict` calls do not carry or compare expected current canvas ID. A request from the old route can continue after unmount/navigation; if a new canvas hydrates before the old promise settles, the old result can update the new in-memory revision/save baseline/status。

This is an evidence-backed race inference, not a recorded production incident. It yields a direct adoption rule：

> Explicit request URL identity is not enough. Every async local convergence step must also compare the current in-memory owner before applying.

The studio clears run polling timers on unmount, but local UI state reset largely depends on route/component lifecycle. If `initialCanvas` changes without a full remount, the hydrate effect explicitly resets only a subset of page-local states. This reinforces the need for a declared reset registry rather than relying on incidental remount behavior。

## 5. Current Clone Lifecycle Audit

### 5.1 Registry shape

The clone keeps in one Zustand store：

```text
projectName
canvases[] = { id, name, nodes, edges, viewport }
activeCanvasId
selectedNodeIds / selectedNodeId
historyByCanvas[canvasId]
```

Positive current behavior：

- at least one initial canvas exists；
- create/duplicate activate the new canvas and clear selection；
- switch clears selection and preserves per-canvas histories；
- delete removes the target history；
- deleting active canvas chooses a fallback and clears selection；
- duplicate copies viewport, remaps structural node/parent/edge IDs and creates empty history；
- React Flow is keyed by `activeCanvasId`, so the flow subtree remounts on switch；
- Batch 58 reconciles image preview/annotate/element edit/Director by `canvasId + nodeId`。

### 5.2 Invalid active identity

`setActiveCanvas(id)` currently writes any string without checking registry membership. UI rows pass known IDs, but the public store and browser fixture API can create：

```text
canvases is non-empty
activeCanvasId does not resolve
getActiveCanvas() returns undefined
React Flow renders an empty projection
```

This violates a project registry invariant. Missing route/store target must return a stable reject/no-op, not create an invalid active owner。

### 5.3 Viewport behavior

Each `CanvasData` has a viewport, and ordinary canvas switch reads it. But `canvas-2` has special desktop/mobile preset ownership in the route：

- initial flow viewport uses a calibration preset；
- every activeCanvasId/media-query effect for `canvas-2` reapplies the preset；
- the effect writes that preset back to the store；
- switching away and back therefore may replace a user-adjusted `canvas-2` viewport instead of restoring it。

This is clone-specific calibration, not source proof. The correctness default is：seed/bootstrap viewport applies only at declared initialization; after user interaction, target canvas viewport is the owner. If responsive source evidence requires recomputation, that needs a separate product rule and must not masquerade as ordinary restore。

### 5.4 Selection and history

Selection is active-session state：

- create/switch/duplicate/active delete clear it；
- `selectNodes` filters IDs against current active nodes；
- history is keyed by canvas ID and survives switch；
- undo/redo operate only on active history and clear selection；
- graph history excludes viewport and canvas lifecycle。

These are coherent foundations. Remaining gaps：

- `selectedNodeId` and `selectedNodeIds` remain dual fields and depend on every action preserving equivalence；
- inactive canvas delete preserves active selection, which is correct only because selection is not canvas-keyed；
- graph history snapshots themselves still have the deep-isolation/runtime-field gaps documented elsewhere；
- canvas lifecycle has no project-level undo, which must remain explicit rather than hidden inside graph history。

Selection 的 node/edge/primary normalization、context precedence 和 focus-return target 有效性由 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) 负责；本文只负责 canvas generation、switch/delete reconciliation 和跨 owner 隔离。

### 5.5 Page-local transactions

The route owns three high-risk transient holders without canvas identity：

| Holder | Captured payload | Current cross-switch risk |
|---|---|---|
| `organizeSnapshot` | nodes + viewport | restore after switch can apply old nodes/viewport to newly active canvas |
| `dragHistorySnapshot` | graph snapshot + node IDs | late drag stop can record old-canvas history baseline against current canvas |
| `connectionGesture` | node/handle/type | gesture state can survive owner change until end/reset ordering completes |

`flowViewport` is also route-local and is synchronized into the active canvas by effects/events. A late viewport event from an unmounted flow must not update the new canvas。

React Flow `key={activeCanvasId}` reduces several runtime risks by remounting the subtree, but it is not a transaction guarantee. Refs/state outside the keyed subtree remain mounted in the route component。

### 5.6 UI owner classes

Current UI state needs explicit classification rather than “close all” or “keep all”：

| UI class | Examples | Recommended switch behavior |
|---|---|---|
| node-bound | toolbar/panel、preview、annotate、element edit、Director shell | close unless owner canvas/node matches target |
| active-canvas projection | asset panel、history panel、storyboard board、Agent graph projection | either remain open and atomically rebind, or close by source contract；never show old data |
| command menu | add node、canvas row menu、zoom menu | close/rebind according to anchor owner；never commit old target |
| project/session preference | grid、edge visibility、snap、select/pan tool | may persist if declared global preference |
| viewport projection | zoom percentage、minimap viewport rect | recompute from target canvas immediately |

Batch 58 covers four node-bound owner types. It does not yet constitute a full switch manifest for every top-level/page-local surface。

### 5.7 Delayed and external owners

Many store actions select the active canvas at invocation time. That is fine for immediate user commands but unsafe for delayed completion that began on another canvas。

Required distinction：

```text
immediate active-canvas command
  -> resolve and commit current active owner synchronously

captured/delayed operation
  -> carry explicit canvasId + operation identity
  -> compare current/source owner
  -> commit to declared canvas or stable stale disposition
```

Switching away is not automatically canceling a provider operation or Director export. It only changes observation/UI owner. Cancellation, continued background execution and result notification are separate product decisions。

## 6. Normative Lifecycle Command Matrix

### 6.1 `CREATE_CANVAS`

| Field | Contract |
|---|---|
| precondition | project registry available；new ID unique；name policy valid |
| document | create empty graph + declared initial viewport |
| active | new canvas becomes active when command says so |
| selection | empty |
| history | empty stack keyed to new ID or canonical implicit empty |
| UI/transients | old node-bound/page-transaction owners invalidated；project preferences classified |
| failure | zero registry/active/selection/history mutation |

### 6.2 `SWITCH_CANVAS`

| Field | Contract |
|---|---|
| precondition | target ID resolves；same-ID switch is stable no-op |
| source document | graph/viewport/history preserved exactly |
| target document | target graph/viewport/history become active projection atomically |
| selection | clear by current clone contract；future preserve requires source evidence and per-canvas owner |
| node-bound UI | invalidate old owner |
| projection panels | close or atomically rebind by declared manifest |
| page transactions | cancel/clear unless explicitly portable |
| async/resource | remain bound to original IDs；switch alone does not destroy |
| graph history | zero new step on source and target |

### 6.3 `RENAME_CANVAS`

| Field | Contract |
|---|---|
| precondition | ID resolves；trimmed non-empty name；length/duplicate policy explicit |
| document | metadata only；graph/viewport unchanged |
| selection/history/UI | unchanged except visible title projection |
| same value | no-op |
| failure | stable result；no partial metadata mutation |

### 6.4 `DUPLICATE_CANVAS`

| Field | Contract |
|---|---|
| precondition | source ID resolves；ID provider available；full copy plan valid |
| graph | map all structural IDs and registered node-data/aggregate identities in one plan |
| viewport | copy or reset by declared command profile；current clone copies |
| history | new empty history；never copy source past/future |
| selection | empty；new canvas active by current clone contract |
| UI | source node-bound UI does not retarget to copied node |
| async/run | do not copy live run/attempt owner；reset/reject by registry |
| resource | share immutable locator、copy owned resource or reject per field/resource policy |
| failure | no orphan canvas, ID allocation residue or active switch |

`DUPLICATE_CANVAS` composes the document/node-data/copy contracts; structural `nodeIdMap` alone is insufficient。

### 6.5 `DELETE_CANVAS`

| Field | Contract |
|---|---|
| precondition | target resolves；final-canvas policy passes；resource/run policy resolved |
| registry | remove exactly target |
| graph history | remove target history permanently；not graph-undoable |
| active fallback | deterministic and valid when deleting active target |
| selection | clear only when active owner changes；inactive delete preserves valid active selection |
| UI/page transactions | invalidate every target owner |
| async/run | cancel/detach/background-preserve according to operation policy |
| resource | emit cleanup/retention impacts；do not infer from URL |
| failure/unknown | zero registry/active/history/UI/resource mutation |

Deleting the final canvas remains a source/product decision：reject, replace-empty and navigate-empty are distinct policies。

## 7. Switch Reconciliation Manifest

Every canvas-scoped owner must appear once in this manifest or a linked registry。

| Owner | Source state on switch | Target state | History impact |
|---|---|---|---|
| nodes/edges | preserve source | target arrays | none |
| viewport | preserve source | restore target | none |
| graph history | preserve source stack | activate target stack | none |
| selection | clear | empty | none |
| image node toolbar/panel | unmount through selection/owner | none until target selection | none |
| preview/annotate/element edit | close old canvas owner | none | none |
| Director desk | close shell owner；workspace policy separate | none | none |
| organize snapshot | cancel old transaction | null | none |
| drag baseline | cancel old gesture | null | none |
| connection gesture | cancel old gesture/line | null | none |
| zoom label/minimap | discard source projection | derive from target viewport | none |
| asset/history/storyboard projection | preserve-open-and-rebind or close by decision | target-only data | none |
| grid/edge/snap/tool preference | preserve if global | same preference | none |
| async operation | keep original canvas owner | observe according to UI policy | none until accepted result |
| resource ledger | unchanged | unchanged | none |

The manifest makes omission reviewable. A newly introduced panel/ref/run cannot silently inherit switch behavior。

## 8. Atomic Planning And Result

### 8.1 Conceptual plan

```ts
type CanvasLifecyclePlan = {
  command: 'create' | 'switch' | 'rename' | 'duplicate' | 'delete';
  baseProjectVersion: number;
  sourceCanvasId: string | null;
  targetCanvasId: string | null;
  nextCanvases: CanvasData[];
  nextActiveCanvasId: string;
  historyEffects: CanvasHistoryEffect[];
  selectionEffect: 'preserve' | 'clear';
  uiInvalidations: CanvasUiOwnerInvalidation[];
  transactionInvalidations: CanvasTransientInvalidation[];
  operationImpacts: CanvasOperationImpact[];
  resourceImpacts: CanvasResourceImpact[];
};
```

This is a design shape, not prescribed source code。

### 8.2 Stable result

```ts
type CanvasLifecycleResult =
  | { status: 'ready'; plan: CanvasLifecyclePlan }
  | { status: 'noop'; reason: string }
  | { status: 'reject'; reason: string }
  | { status: 'unknown'; unresolvedPolicy: string };
```

Only `ready` reaches commit. UI/resource/operation side effects consume the committed result; they do not pre-mutate and hope graph lifecycle succeeds。

### 8.3 Whole-owner commit

At minimum, registry、active ID、selection and history-map changes commit from one current project snapshot. Viewport/graph already live inside target canvas record. Page-local refs and UI owners are reconciled immediately after commit from the same result and also have render-time self-healing guards。

## 9. Invariants

### `LIBTV-GI-038` — Active ID resolves

When registry is non-empty, `activeCanvasId` resolves to exactly one canvas. Unknown switch target cannot create a blank invalid active projection。

### `LIBTV-GI-039` — Registry IDs are unique

Canvas IDs are non-empty and unique. Create/duplicate cannot partially allocate an ID or collide with an existing/deleted/imported identity。

### `LIBTV-GI-040` — Per-canvas owner closure

Graph、viewport and history are keyed to one canvas and preserved across switch until that canvas is deleted。

### `LIBTV-GI-041` — Selection is active-session state

Current clone selection clears on create/switch/duplicate/active delete and is always a subset of active nodes. It never selects an inactive canvas node。

### `LIBTV-GI-042` — Page transactions carry canvas owner

Organize、drag、connection and viewport callbacks cannot commit after active canvas generation changes。

### `LIBTV-GI-043` — Node-bound UI cannot cross canvases

Every node-bound surface includes canvasId + nodeId or derives safely from target selection; owner mismatch closes without graph/history mutation。

### `LIBTV-GI-044` — Lifecycle is not graph undo

Create、rename、switch、duplicate and delete do not enter current per-canvas graph history. Future project undo requires a separate product/domain contract。

### `LIBTV-GI-045` — Delayed writes use declared canvas

Timer、promise、poll、subscription and browser export results carry explicit canvas/operation identity. They never late-read active canvas as destination authority。

### `LIBTV-GI-046` — Delete/duplicate external impacts are explicit

Run、Director workspace and media/resource ownership are not inferred from graph removal or URL shape. Copy/delete returns explicit reset/detach/retain/release/unknown effects。

### `LIBTV-GI-047` — Viewport restore has one owner

Switch restores the target canvas viewport. Seed/responsive calibration cannot silently overwrite a user-owned viewport without a separately declared rule。

### `LIBTV-GI-048` — Async convergence checks current owner

Even when a network request URL targets the correct durable canvas, its local completion cannot update the current in-memory store unless expected canvas/generation still matches or an explicit background-canvas store adapter owns the result。

## 10. Compatibility Cases

| ID | Setup | Action | Required observation |
|---|---|---|---|
| `LIBTV-GC-044` valid switch | A/B with distinct graph/viewport/history | A -> B -> A | each graph/viewport/history exact；selection cleared；zero new history |
| `LIBTV-GC-045` unknown target | valid A active | switch missing ID | stable reject/no-op；A remains active and unchanged |
| `LIBTV-GC-046` same target | A active | switch A | exact no-op；no UI flicker/history/reset |
| `LIBTV-GC-047` organize switch | organize preview on A | switch B then restore | old snapshot cannot change B；transaction canceled |
| `LIBTV-GC-048` drag switch | drag baseline on A | switch B before late stop | no B position/history change；old baseline discarded |
| `LIBTV-GC-049` viewport race | viewport callback queued from A | switch B then callback | B viewport remains its own；stale callback no-op |
| `LIBTV-GC-050` node-bound surface | preview/annotate/Director on A | switch B | surface closes；A/B graph/history unchanged |
| `LIBTV-GC-051` projection panel | asset/history panel open on A | switch B | panel closes or shows only B according to manifest；never mixed |
| `LIBTV-GC-052` duplicate full graph | group/derived/shot/process/Director refs | duplicate A | one valid B；IDs/refs/aggregate/resource policy exact；history/selection empty |
| `LIBTV-GC-053` delete inactive | A active/selected；B exists | delete B | A graph/selection/history/viewport unchanged；B owners removed |
| `LIBTV-GC-054` delete active | A active；B/C exist | delete A | deterministic valid fallback；selection/UI/transients clear；A history removed |
| `LIBTV-GC-055` final delete | one canvas | delete | exact reject or replace-empty policy；registry never invalid |
| `LIBTV-GC-056` old local timer | operation starts on A | switch B；A completion | result targets A/stale policy；never creates in B or steals B selection |
| `LIBTV-GC-057` old save response | save A in flight | hydrate B；A response | durable A may complete；B in-memory revision/baseline/status unchanged |
| `LIBTV-GC-058` resource delete | A owns pending blob/run/workspace | delete A | declared cancel/detach/release/retain；exactly once；no URL heuristic |

## 11. Local Fixture Contract

Fixture ID: `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01`。

### 11.1 Required controls

- fresh Page with deterministic project/canvas/node/edge IDs；
- A/B/C canvases with distinct graph、viewport and history；
- controlled active selection and node-bound UI owners；
- controlled organize/drag/connection/viewport transient holders；
- fake completion/save queue with canvas/generation identity；
- resource/operation ledger；
- deterministic duplicate ID provider；
- reset that reconstructs the page/store instead of using graph undo as teardown。

### 11.2 Core scenes

1. `A_ACTIVE`：A selected node、custom viewport、one past/one future history；
2. `B_TARGET`：different nodes/viewport/history；
3. `A_ORGANIZE_PENDING`：old snapshot armed；
4. `A_DRAG_PENDING`：pre-drag snapshot armed；
5. `A_SURFACE_OPEN`：preview/annotate/Director owner；
6. `A_ASYNC_PENDING`：old completion and optional resource；
7. `A_DUPLICATE_COMPLEX`：group/derived/shot/process/Director/media identity corpus；
8. `FINAL_CANVAS`：one-item registry；
9. `INVALID_TARGET`：unknown canvas ID；
10. `A_SAVE_PENDING_B_HYDRATED`：Open Canvas-inspired stale completion simulation。

### 11.3 Reset assertions

- active ID resolves；
- canvas IDs unique；
- selection subset active graph；
- histories exist only for declared canvas IDs；
- no page transaction or node-bound owner from prior scene；
- viewport finite and exact per fixture；
- resource/operation ledger empty or declared；
- no local storage/provider/network dependency。

## 12. Verification Replacement

Verifier ID: `LIBTV-VR-017`。

| Layer | Required assertion |
|---|---|
| static registry | every lifecycle command and canvas-scoped owner is cataloged；unknown target guarded |
| pure planner | create/switch/rename/duplicate/delete ready/noop/reject/unknown and zero-partial behavior |
| store integration | active/registry/selection/history atomicity；target viewport restore；fallback exact |
| transient race | organize/drag/connection/viewport old-owner callbacks cannot mutate target |
| UI integration | node-bound close；projection panel rebind/close；global preference behavior exact |
| async/resource | old completion/save response owner check；resource impact exactly once |
| browser | Batch 16 CRUD/dropdown plus Batch 58 owner regression；desktop/mobile；no page/console error |

`LIBTV-VR-017` composes but does not replace graph document/copy/delete/entrypoint/change/async verifier families。

## 13. Decision Queue

| ID | Decision | Recommended default | Evidence needed |
|---|---|---|---|
| `LIBTV-CAN-DQ-001` | invalid `setActiveCanvas` target | reject/no-op with stable code | local fixture；no source dependency |
| `LIBTV-CAN-DQ-002` | switch selection | clear by current clone contract | LibTV source only if changing to per-canvas preserve |
| `LIBTV-CAN-DQ-003` | fallback after active delete | deterministic next neighbor preferred over first-item surprise | source row-order/delete evidence or explicit clone decision |
| `LIBTV-CAN-DQ-004` | delete final canvas | retain current reject until source/product decision | disposable source fixture |
| `LIBTV-CAN-DQ-005` | duplicate viewport | copy source by current clone contract | source duplicate behavior if parity claim desired |
| `LIBTV-CAN-DQ-006` | demo canvas responsive preset | bootstrap-only；stored user viewport wins after interaction | multi-viewport clone fixture + source evidence if parity |
| `LIBTV-CAN-DQ-007` | asset/history/agent panels on switch | remain open only if atomically rebound to target；otherwise close | current component projection audit + source behavior |
| `LIBTV-CAN-DQ-008` | background operation after switch | continue under original canvas owner；do not steal target selection | operation-specific source/product contract |
| `LIBTV-CAN-DQ-009` | canvas duplicate resource policy | immutable locator may share；owned mutable/run/workspace resets or blocks | node-data/resource registry |
| `LIBTV-CAN-DQ-010` | project-level lifecycle undo | keep absent/deferred | explicit source/product request and separate history design |

## 14. Implementation Slices After Authorization

### Slice A — Registry and switch correctness

- guard target ID and same-ID no-op；
- define lifecycle result；
- assert active ID resolves and selection clears；
- keep graph/history/viewport target exact。

### Slice B — Page transaction invalidation

- bind organize/drag/connection/viewport callbacks to canvas owner/generation；
- clear old transaction state on switch；
- add race cases without changing normal UI geometry。

### Slice C — UI reconciliation manifest

- retain Batch 58 node-bound owner behavior；
- classify active-canvas projections and global preferences；
- close/rebind every registered surface；
- maintain render-time self-healing。

### Slice D — Duplicate/delete plan composition

- use graph document/node-data/copy/delete registries；
- define fallback/final-canvas policy；
- report operation/resource impacts；
- preserve zero-partial lifecycle commit。

### Slice E — Async/background ownership

- make delayed actions carry canvasId/generation/operation identity；
- prevent old save/result callbacks from updating current owner；
- define background notification/observation separately from commit。

Each slice is separately reviewable. No slice combines FrameOS、Open Canvas persistence、provider、visual redesign or shared source mutation。

## 15. Open Canvas Adoption Verdict

### Adopt

- stable canvas identity separated from list summary and active document；
- explicit missing-ID failure instead of blank invalid editor；
- one hydrate boundary for graph/viewport/revision/save owner replacement；
- per-canvas viewport restore；
- delete cleans run records and preserves a valid registry postcondition；
- explicit canvas ID in durable request paths。

### Adapt

- keep LibTV in-place dropdown UI while applying an equivalent atomic owner transition；
- retain in-memory/no-backend prototype boundary；
- keep current graph history separate from lifecycle；
- choose LibTV-specific final delete、fallback、panel and duplicate resource policies；
- add current in-memory owner/generation checks to every async completion。

### Reject

- copying Open Canvas list-card visual、route structure or recent sorting as LibTV parity；
- assuming route remount alone resets every page-local owner；
- applying old save/run completion to whichever canvas store is current；
- transplanting file/KV/revision/conflict/template/provider behavior；
- treating delete-final replacement or run cleanup as proven LibTV source semantics。

## 16. Completion Criteria

This contract is implemented only when：

- active ID always resolves and IDs are unique；
- switch is zero-history and preserves exact source/target graph-history-viewport ownership；
- selection/UI/page transactions follow the reconciliation manifest；
- stale drag/organize/connection/viewport callbacks cannot mutate another canvas；
- duplicate validates the complete graph/data/resource plan before one lifecycle commit；
- delete has exact fallback/final/history/UI/operation/resource effects；
- delayed and network completions compare canvas/generation owner；
- `LIBTV-FIX-LOCAL-CANVAS-LIFECYCLE-01` and `LIBTV-VR-017` pass；
- Batch 16/58 and current canvas dropdown/overlay visual contracts do not regress。

Until then, the accurate status is：

Spatial phase、actual host、gesture/placement session and resize mechanics are delegated to [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md). This lifecycle contract remains authoritative for canvas registry/generation and switch/delete invalidation; neither document may late-read the new active canvas as an old operation destination.

> The clone has a functional in-memory multi-canvas menu, per-canvas graph/history/viewport storage and partial node-bound owner cleanup. It does not yet have a complete lifecycle transaction that prevents page-local, async, resource and viewport ownership from crossing canvas boundaries. Open Canvas offers strong identity/hydrate/delete methods and an important stale local-convergence counterexample, but not LibTV product semantics.
