# LibTV Graph Mutation Entry-Point Trust Matrix

> Scope: 普通 LibTV 画布所有 graph 写入口、Open Canvas 固定版本的分层校验方法、入口信任等级、实施顺序、fixture 与 verifier 设计。
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL`。本文不授权修改 `src/`、测试脚本、Open Canvas submodule、FrameOS 或共享源站 graph。
>
> Clone baseline: `a54206860d02fd46b3615817ac8889d8ba303c57`（2026-08-27；相关 graph runtime 由 Batch 57 `cbb47fe` 引入）。
>
> Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`。

## 1. Why This Document Exists

Batch 57 已使普通 React Flow 连接和 `canvasStore.addEdge` 使用同一个结构 validator。这个进展只关闭了两个入口，不等于整个 graph 已被保护。

当前 store 还存在多类写路径：

- React Flow `NodeChange` / `EdgeChange`；
- 组织布局和 drag history 使用的 `setNodes`；
- 派生媒体、逐帧拉片、长视频和 Director 导出直接追加 node/edge；
- single/multi/canvas duplicate；
- group/ungroup；
- node data patch；
- delete/clear；
- undo/redo snapshot restore；
- future clipboard/import/batch/sync/persistence。

如果只保护 `onConnect -> addEdge`，其他入口仍可能写入 dangling edge、重复关系、循环、过期 `sourceNodeId/edgeId`、不完整 aggregate 或无法恢复的浅层 data。后续实现需要回答的不是“哪里再调用一次 connection validator”，而是：

1. 哪些入口接收不可信 proposal，必须先验证；
2. 哪些入口是可信 command planner 的输出，必须验证整个 draft；
3. 哪些入口只是 React Flow transport delta，必须限制 change type；
4. 哪些入口恢复历史或文档，必须走 codec/invariant gate；
5. 哪些入口来自 server/run patch，必须有 revision 与 field ownership；
6. 哪些状态只是 selection/viewport/UI owner，不应被错误塞进 graph validator。

本文把这些问题收敛为一张可执行的 trust matrix。它连接：

- connection 合同 [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)；
- document 合同 [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)；
- copy 合同 [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)；
- node data 合同 [`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)；
- delete 合同 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)。

## 2. Evidence And Claim Boundary

### 2.1 `OPEN_CANVAS_FACT`

固定 submodule 中可直接读取的代码行为。主要证据：

- [`shared/stores/canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts)；
- [`shared/lib/canvas/validation.ts`](../../research/upstream/open-canvas/shared/lib/canvas/validation.ts)；
- [`shared/lib/canvas/serialization.ts`](../../research/upstream/open-canvas/shared/lib/canvas/serialization.ts)；
- [`shared/lib/canvas/types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts)；
- [`shared/blocks/canvas/canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)；
- [`app/api/canvas/[canvasId]/graph/route.ts`](../../research/upstream/open-canvas/app/api/canvas/%5BcanvasId%5D/graph/route.ts)；
- [`shared/models/local-canvas-store.ts`](../../research/upstream/open-canvas/shared/models/local-canvas-store.ts)；
- [`lib/canvas-json.ts`](../../research/upstream/open-canvas/lib/canvas-json.ts)。

### 2.2 `CLONE_FACT`

当前 committed clone 的普通 LibTV route/store 行为。主要证据：

- [`src/app/page.tsx`](../../src/app/page.tsx)；
- [`src/store/canvasStore.ts`](../../src/store/canvasStore.ts)；
- [`src/lib/libtvGraphConnection.ts`](../../src/lib/libtvGraphConnection.ts)；
- 当前 node components 和 Batch 57 实施记录。

### 2.3 `DECISION`

本文提出的 trust class、command envelope、entry policy、fixture 和 verifier 是 clone-only correctness design。它们不声称来自 LibTV 源站，也不自动获得编码授权。

### 2.4 Explicit exclusions

- 不从 Open Canvas 推导 LibTV node type、Handle、provider、保存或协作语义；
- 不把 Open Canvas 现状美化为所有入口都严格验证；
- 不把当前 clone 的 deterministic derived edges 等同于源站真实任务拓扑；
- 不把普通 LibTV store 规则推广到独立 FrameOS store；
- 不在共享源站尝试 delete、copy、connect、run、save 或 import。

## 3. Big Picture: Validation Is Layered

Open Canvas 固定版本的真实边界不是一个“所有写入都经过的万能函数”，而是多层防线：

```text
UI gesture / command
  -> store-local guard and mutation
  -> serialize current flow graph
  -> full graph validation before save/share
  -> API payload parse + full graph validation
  -> optimistic revision compare
  -> durable graph replace
```

这套结构的价值在于：

- UI 命令可以返回局部、可解释的失败；
- save/API 边界不信任当前内存 graph；
- revision conflict 不与 graph validity 混成同一状态；
- server node patch 与用户 gesture 是不同 authority；
- durable write 前有第二道独立校验。

它的局限也必须保留：

- `pasteClipboard` 不逐边调用 `onConnect`，也不在提交前检查 DAG；
- clipboard parser 只验证 version 和 arrays，内部 item 形状依赖后续 typed code；
- `onNodesChange/onEdgesChange` 直接使用 React Flow `apply*Changes`；
- `hydrate` 信任已经进入 `CanvasDocumentRecord` 的 graph；
- conflict rebase 对 edges 采用 whole-array local-or-remote 策略，不是逐 edge merge；
- save-time validator 可能把局部错误延迟到 dirty graph 已进入内存之后。

因此正确借鉴是“分层信任 + 最终完整校验”，不是复制上游每个具体入口。

## 4. Open Canvas Entry-Point Inventory

### 4.1 Runtime store entry points

| Entry | Input authority | Local checks | Mutation | Full graph check before mutation | Conflict gate | Assessment |
|---|---|---|---|---|---|---|
| `hydrate` | loaded `CanvasDocumentRecord` | flow conversion/normalization | replace nodes/edges/viewport/revision | no | resets conflict | trusted document ingress; correctness depends on upstream load/API |
| `addNode` | UI node type/position | conflict、max nodes | add one selected node | not needed for edges | yes | bounded command |
| `duplicateNode` | existing node ID | conflict、source exists、max nodes、data normalize | add one detached node | no | yes | bounded copy command |
| `pasteClipboard` | clipboard packet | conflict、non-empty、node/edge limits、internal edge filter、ID map、direction normalize | append nodes/internal edges | no DAG/self/duplicate full check | yes | partial protection |
| `deleteNode` | node ID | exists | delete node + incident edges | no | yes | centralized structural delete |
| `deleteEdge` | edge ID | exists | delete edge | no | yes | centralized structural delete |
| `updateEdgeTargetHandle` | edge ID + target Handle | changed check、semantic dedupe | rewrite target Handle and dedupe | no DAG/type recheck | yes | specialized partial mutation |
| `deleteIncomingReference` | target/source IDs | matching edge exists | delete exact directed edge | no | yes | named edge relation action; currently no consumer found |
| `deleteSelection` | selected flags | no-op detection | delete selected nodes/edges + incident edges | no | yes | centralized selection delete |
| `onNodesChange` | React Flow changes | persistent-vs-selection classification | `applyNodeChanges` | no | yes | framework transport boundary |
| `onEdgesChange` | React Flow changes | persistent-vs-selection classification | `applyEdgeChanges` | no | yes | framework transport boundary |
| `onConnect` | React Flow connection | endpoints、opposite sides、direction、max edges、exact Handle duplicate、DAG | append one edge | local candidate check | yes | protected graph proposal |
| `updateViewport` | React Flow/UI viewport | normalize/no-op | replace viewport | not applicable | no explicit gate | presentation/document state |
| `updateNodeData` | UI patch | conflict、normalize per node type、changed check | patch one node | no cross-node aggregate check | yes | typed local patch, not relation-aware |
| `applyServerNodePatch` | server/run response | node existence and typed patch projection | patch node + revision/saved baseline | no local conflict gate | intentional trusted path | separate remote authority |

### 4.2 Save, import and durable ingress

| Boundary | What it does | Protection | Important limitation |
|---|---|---|---|
| `buildCanvasGraphFromFlow` | removes runtime-only selection/decorations and normalizes data/edge direction | explicit serialized graph projection | does not by itself prove graph validity |
| `validateCanvasGraph` before save/share | limits、unique node/edge IDs、endpoint existence、self-loop、DAG | full graph invariant gate | does not validate LibTV-specific node data relations |
| graph API `PUT` | parses unknown payload, normalizes edge direction, validates graph | independent server boundary | Open Canvas rules are only five-node product rules |
| `updateLocalCanvasDocumentGraph` | compares revision then replaces graph and increments revision | optimistic concurrency | assumes API already validated graph |
| JSON import | permissive normalize, create canvas, then graph API `PUT` | server validation prevents invalid durable graph | failed graph save may leave the newly created empty canvas |
| local DB read | `normalizeCanvasGraph` on stored records | tolerant recovery | normalization can drop invalid nodes/duplicate semantic edges rather than produce diagnostics |
| conflict auto-rebase | three-way node merge, viewport choice, whole-edge-array choice, then API `PUT` | final API validation and revision retry | edge conflicts are coarse; not a general collaboration merge model |

### 4.3 Mutation freeze during conflict

Most local graph/data commands return no-op or structured reject when `conflictDetected` is true. The shell also disables visible creation controls and stops debounced save. This is a valuable ownership pattern:

```text
revision conflict
  -> freeze ordinary local graph mutation
  -> load latest or attempt bounded rebase
  -> hydrate a resolved document
  -> resume local commands
```

Do not transplant this as a current LibTV feature. The clone has no ordinary-canvas persistence/revision contract. It is useful only when future persistence is explicitly authorized under [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md).

## 5. What Open Canvas Teaches And What It Does Not

### 5.1 High-value methods

1. **Name mutation commands.** `addNode`, `pasteClipboard`, `deleteSelection`, `updateEdgeTargetHandle` and `applyServerNodePatch` expose different intent rather than one generic `setGraph` UI API.
2. **Separate local candidate checks from full document checks.** A connection receives immediate feedback while durable save independently validates the whole graph.
3. **Treat conflict as an authority state.** Local commands stop instead of continuing to mutate an already stale revision.
4. **Keep server patches distinct.** Async execution result patches can advance revision/saved baseline without pretending to be a user edit.
5. **Normalize at serialization boundaries.** Runtime React Flow objects are projected into a versioned graph rather than persisted verbatim.
6. **Revalidate on the server.** Client type safety and current store state are not trusted across HTTP.

### 5.2 Upstream gaps that must not be copied

| Gap | Fixed-version behavior | LibTV guidance |
|---|---|---|
| Clipboard validation | parser checks only packet version and arrays | future LibTV packet needs strict node/data/reference validation before mutation |
| Paste DAG protection | internal edges are remapped and appended without full graph validation | validate complete proposed graph or every edge set before one commit |
| Framework deltas | `applyNodeChanges/applyEdgeChanges` accept incoming change variants | whitelist transport changes; route add/replace/remove through domain commands |
| Handle retarget | dedupes semantic edge after retarget but does not re-run cycle/type policy | treat retarget/reconnect as a connection replacement transaction |
| Tolerant storage normalize | malformed records can be dropped/normalized | portable LibTV load should reject with diagnostics, not silently become partial graph |
| Edge conflict merge | local or remote whole edge list wins | future collaboration requires operation/field ownership, not array preference |
| Runtime invalid window | some malformed local state is caught only at save | high-risk LibTV command validates draft before committing to runtime/history |

## 6. Current Clone Entry-Point Inventory

### 6.1 Trust status vocabulary

| Status | Meaning |
|---|---|
| `PROTECTED` | proposal is normalized/validated before one atomic mutation and has focused recorded verification |
| `PARTIAL` | command has useful preconditions or structural closure, but not all registered invariants |
| `TRUSTED_OUTPUT_UNPROVEN` | deterministic command builds graph directly; output is assumed valid and no final draft validator proves it |
| `BYPASS` | generic setter/restore path can replace graph state without domain/invariant validation |
| `DEFERRED` | runtime entry does not exist yet; future design must define ingress before implementation |
| `NON_GRAPH` | selection/viewport/UI state; should not be forced through graph proposal rules |

### 6.2 Canvas and node commands

| Clone entry | Current mutation | Status | Main uncovered invariant |
|---|---|---|---|
| `addCanvas` | add empty canvas and history stack | `PARTIAL` | canvas ID/schema registry and document envelope absent |
| `removeCanvas` | remove canvas, select first remaining, drop history | `PARTIAL` | UI/resource/run owner cleanup and fallback semantics |
| `duplicateCanvas` | remap structural node/parent/edge IDs, shallow-spread data | `TRUSTED_OUTPUT_UNPROVEN` | node-data refs、aggregate IDs、media/resource ownership、deep isolation |
| `addNode` / `addNodeAtPosition` | merge default data with arbitrary `Record<string, unknown>` | `PARTIAL` | closed type/dataVersion registry and payload validation |
| `addDerivedNode` | append one node and direct source edge | `TRUSTED_OUTPUT_UNPROVEN` | shared connection validation、owned data refs、domain policy |
| `createVideoContinuation` | append node/edge + nested continuation metadata | `TRUSTED_OUTPUT_UNPROVEN` | edge/data reciprocal integrity and duplicate operation policy |
| `createSubtitleErase` | append node/edge + normalized regions | `TRUSTED_OUTPUT_UNPROVEN` | final graph/registry validation |
| `createAudioSplit` | append two nodes/two edges + metadata | `TRUSTED_OUTPUT_UNPROVEN` | multi-output transaction invariant |
| `createVideoFrameCapture` | append image/edge + frame metadata | `TRUSTED_OUTPUT_UNPROVEN` | final graph/edge-owned ref validation |
| `createDepthMotionCapture` | append video/edge + task metadata | `TRUSTED_OUTPUT_UNPROVEN` | final graph/edge-owned ref validation |
| `createLongVideoProcess` | append V0 12-node/22-edge process graph | `TRUSTED_OUTPUT_UNPROVEN` | complete process cohort、unique IDs、DAG、source/product semantics |
| `createSmartMatting` | append video/edge + task metadata | `TRUSTED_OUTPUT_UNPROVEN` | final graph/edge-owned ref validation |
| `createPictureEdit` | append video/edge + scoped marks | `TRUSTED_OUTPUT_UNPROVEN` | mark ID scope、edge ref、media/resource budget |
| `createDirectorCapture` | append image/edge + data URL/provenance | `TRUSTED_OUTPUT_UNPROVEN` | data URL budget、Director workspace owner、edge ref |
| `createDirectorAnimationExport` | append video/edge + blob/data provenance | `TRUSTED_OUTPUT_UNPROVEN` | locator lifetime、Director storage cleanup、edge ref |
| `completeShotBreakdown` | patch source, append result nodes/edges | `TRUSTED_OUTPUT_UNPROVEN` | reciprocal aggregate completeness and atomic relation validation |

These direct creators are not automatically bugs. A deterministic command may legitimately create an edge that ordinary gesture policy would reject or classify differently. The gap is that the command output has no declared final-graph acceptance authority.

### 6.3 Copy, grouping, delete and data commands

| Clone entry | Current mutation | Status | Main uncovered invariant |
|---|---|---|---|
| `duplicateNode(includeEdges)` | shallow copy + optional incident-edge copy | `PARTIAL` / compatibility hold | external endpoint policy、cycle/duplicate、nested identities |
| `duplicateSelectedNodes` | descendant closure、parent remap、internal/compat edges | `PARTIAL` | node-data ref registry、aggregate/media、final graph validation |
| `groupSelectedNodes` | add group and rewrite child parent/relative position | `PARTIAL` | nested parent validation、aggregate ownership and final draft check |
| `ungroupSelectedNodes` | remove group and detach children | `PARTIAL` | relation/UI cleanup and full closure validation |
| `removeNode` / `removeSelectedNodes` | descendant closure、incident-edge filter、selection/history | `PARTIAL` | relation inverse index、aggregate/UI/resource repair |
| `removeEdge` | filter one edge | `PARTIAL` | edge-owned data and semantic reference repair |
| `clearVideoContinuation` | remove owned metadata + exact edge | `PARTIAL` | generalized registered relation handling |
| `updateNodeData` | shallow merge arbitrary patch + history | `BYPASS` for identity fields | type/version/field ownership and cross-node aggregate validation |

Delete and data details are authoritative in the dedicated delete/node-data documents; this matrix only classifies their ingress.

### 6.4 React Flow transport and low-level replacement

| Clone entry | Caller | Current behavior | Status | Risk |
|---|---|---|---|---|
| route `onNodesChange` | React Flow | splits selection, applies all other changes, calls `setNodes` | `BYPASS` | remove/add/replace semantics are not distinguished; node/edge updates are separate |
| route `onEdgesChange` | React Flow | applies all changes and calls `setEdges` | `BYPASS` | add/replace/reconnect can bypass `addEdge`; remove bypasses delete repair |
| store `setNodes` | route drag/layout/debug paths | replaces active nodes; optional history | `BYPASS` | arbitrary missing/duplicate IDs、parent/data changes |
| store `setEdges` | route React Flow changes | replaces active edges; optional history | `BYPASS` | dangling、duplicate、self/cycle、owned relation changes |
| organize apply/cancel | page command | calls `setNodes` with full node array | `PARTIAL` | intended position-only command has broader write capability |
| drag updates | React Flow/page | repeated position writes, one explicit history record on stop | `PARTIAL` | transport setter can change more than position if misused |

`setNodes/setEdges` are necessary implementation mechanisms, but they are currently public store actions with domain-level power. Future code should distinguish transport-only patching from graph command submission instead of merely renaming them.

### 6.5 Connection, history and deferred ingress

| Clone entry | Current behavior | Status | Boundary |
|---|---|---|---|
| route `isValidConnection/onConnect` | shared structural validator before edge ID/commit | `PROTECTED` | Batch 57 local structural slice only |
| store `addEdge` | revalidates programmatic edge and returns reason/result | `PROTECTED` | Reference/domain/import/sync still open |
| `undo` / `redo` | directly restore shallow `GraphSnapshot` arrays | `BYPASS` / trusted history | no snapshot decode/invariant check; nested data isolation incomplete |
| ordinary clipboard paste | absent | `DEFERRED` | must use subgraph packet/command contract |
| portable import/export | absent | `DEFERRED` | must use versioned strict document contract |
| batch mutation | absent as generic ingress | `DEFERRED` | derived commands already behave as bespoke batches |
| remote sync/collaboration | absent | `DEFERRED` | requires revision, field ownership and conflict policy |
| ordinary-canvas persistence | absent | `DEFERRED` | must not copy Open Canvas product semantics implicitly |

## 7. Risk Topology

### 7.1 The current protected island

```text
React Flow onConnect
  -> route structural validation
  -> canvasStore.addEdge
  -> store structural revalidation
  -> one edge + one history step
```

This is a strong local boundary, but it is an island. The following paths do not call `addEdge`:

- all derived creation commands;
- long-video and shot-breakdown multi-edge commands;
- duplicate/canvas duplicate;
- `setEdges` and React Flow `EdgeChange`;
- undo/redo restore;
- future clipboard/import/sync.

### 7.2 Why routing every edge through `addEdge` is wrong

An obvious response would be to make every direct creator loop over `addEdge`. That would violate transaction semantics:

- multi-node commands could partially add early edges before a later reject;
- each edge would create a separate history step;
- newly created endpoints do not exist in the current graph until the node draft is considered;
- ordinary gesture duplicate/domain rules may not match system-owned semantic edges;
- source node patch, target nodes, edges and aggregate IDs must be validated together;
- selection and UI result would be committed at the wrong time.

The correct abstraction is a full command plan whose complete proposed graph is validated once before one commit.

### 7.3 Why save-time validation alone is insufficient

The clone currently has no ordinary-canvas save gate. Even if one is added later, deferring errors until save would still allow:

- invalid graph to render and affect later commands;
- history to record invalid snapshots;
- UI overlays to bind to invalid owners;
- provider mock actions to consume malformed refs;
- a user action to appear successful and fail much later.

Save/API validation is defense in depth, not a substitute for command validation.

## 8. Proposed Trust Classes

### T0: Presentation-only transport

Examples: selection flags, viewport, transient connection line, hover, panel owner.

Rules:

- no graph semantic validation;
- no history unless explicitly part of product contract;
- cannot create/delete node/edge or rewrite node data identity;
- UI owner invalidation remains route/uiStore responsibility.

### T1: Whitelisted React Flow patch

Examples: node position/dimensions from drag/measure, selection changes, edge selection.

Rules:

- allowlist exact `NodeChange/EdgeChange` variants and fields;
- `add/remove/replace/reconnect` do not pass as generic transport;
- collapse continuous drag writes into one declared history transaction;
- reject unknown change type without partial apply.

### T2: Single-entity graph proposal

Examples: ordinary connection, add detached node, rename/update non-relational node field.

Rules:

- normalize and validate proposal before mutation;
- return stable allow/reject/unknown result;
- accepted command produces one graph/history transaction;
- relation-bearing data field upgrades the operation to T3.

### T3: Planned multi-entity command

Examples: derived node, long-video process, shot result expansion, copy, group, delete, edge retarget.

Rules:

- command planner receives immutable current graph and intent;
- computes nodes/edges/data/selection/UI/resource impact as one plan;
- validates final draft against structural, registry and command-specific invariants;
- any reject/unknown yields zero graph/history/UI mutation;
- commit consumes only a validated plan and adds one history step.

### T4: Snapshot/document restore

Examples: undo/redo, duplicate canvas snapshot, clipboard paste, portable import, fixture load.

Rules:

- decode according to the correct schema, not runtime `Node[]` trust;
- validate type/version/IDs/parents/edges/data refs/aggregates/media;
- distinguish strict portable load from trusted in-process history restore;
- restore into a draft and swap atomically;
- failure must keep active graph/history unchanged and report diagnostics.

### T5: Remote/server authority

Examples: provider result patch, collaboration sync, persisted document hydrate.

Rules:

- declare revision/base identity and allowed field ownership;
- never apply a generic object patch to graph-owned identities;
- stale/conflicting response is reject/quarantine/rebase, not silent last-write-wins;
- full document payload receives server-side validation;
- local UI feedback and remote persistence status remain separate owners.

Provider/run completion 的 operation/result envelope、expected current owner、stale/duplicate disposition、history/selection/resource 和 recoverable projection 继续由 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) 细化；T5 分类本身不是免检 patch 通道。

## 9. Command Envelope

The following is conceptual design, not an implementation signature:

```ts
type GraphMutationOrigin =
  | "react-flow-transport"
  | "user-command"
  | "system-derived-command"
  | "history-restore"
  | "clipboard"
  | "portable-import"
  | "server-patch"
  | "remote-sync";

type GraphMutationPlan = {
  commandId: string;
  commandKind: string;
  origin: GraphMutationOrigin;
  baseCanvasId: string;
  baseGraphRevision?: number;
  nextGraph: unknown;
  nextSelection?: string[];
  uiInvalidations?: unknown[];
  resourceImpacts?: unknown[];
  historyPolicy: "none" | "one-step" | "restore";
  diagnostics: unknown[];
};

type GraphMutationDecision =
  | { status: "ready"; plan: GraphMutationPlan }
  | { status: "reject"; reason: string }
  | { status: "unknown"; unresolvedPolicy: string };
```

Required properties:

1. only `ready` plans reach commit;
2. plan contains the whole final draft, not a sequence of imperative partial writes;
3. plan is tied to a base canvas/revision or equivalent graph identity;
4. stale plan cannot commit over a changed graph;
5. graph history records graph state, not transient UI/resource execution;
6. `uiInvalidations` and `resourceImpacts` are explicit side-result channels;
7. diagnostics use stable codes and preserve source/clone provenance.

## 10. Entry Policy Matrix

| Entry family | Trust class | Required authority | Must not use |
|---|---:|---|---|
| selection/viewport | T0 | route/UI owner | connection validator |
| node drag/measure | T1 | whitelisted patch reducer | arbitrary `setNodes` payload |
| edge selection | T1 | selection-only edge patch | relation delete planner |
| ordinary connect | T2 | `LibTVGraphConnection` structural/domain pipeline | direct edge append |
| detached node create | T2 | node registry/default-data validator | arbitrary type + `Record` merge |
| node data non-relational patch | T2 | type/version field registry | generic shallow spread |
| derived/process/shot command | T3 | command-specific planner + final graph invariant | repeated `addEdge` transactions |
| copy/group/delete/reconnect | T3 | dedicated planner + node-data relation registry | low-level array filter/map as product policy |
| undo/redo | T4 | history snapshot codec/invariant | unvalidated shallow array restore |
| clipboard/import | T4 | strict packet/document codec + final graph validator | tolerant normalization with silent drops |
| server run patch | T5 | typed field-owner patch + revision | generic UI update command |
| collaboration/sync | T5 | operation/revision/conflict contract | user gesture origin or last-write-wins |

## 11. Stable Ingress Decision Queue

### `LIBTV-ING-DQ-001`: low-level setter visibility

**Question:** should `setNodes/setEdges` remain public store actions?

**Recommended decision:** retain low-level reducers only as internal transport primitives; expose intent-specific commands to components/routes. If module privacy is impractical, require an explicit transport origin and allowlisted change shape.

### `LIBTV-ING-DQ-002`: React Flow change whitelist

**Question:** which `NodeChange/EdgeChange` variants may apply directly?

**Recommended decision:** selection and declared position/dimension updates may use T0/T1; add/remove/replace/reconnect route to T2/T3 commands. Unknown variants reject before `apply*Changes`.

### `LIBTV-ING-DQ-003`: derived command validation

**Question:** should deterministic derived edges use ordinary connection policy?

**Recommended decision:** use shared structural graph invariants on the complete proposed graph, but keep command/domain edge policy separate. Do not loop through user-gesture `addEdge`.

### `LIBTV-ING-DQ-004`: history restore trust

**Question:** can in-process history snapshots bypass full portable codec?

**Recommended decision:** yes, but only after history snapshot deep isolation and a lighter closed-schema invariant check. Invalid/stale snapshot returns a stable restore failure and does not consume past/future.

### `LIBTV-ING-DQ-005`: duplicate and canvas copy

**Question:** can existing copy helpers keep committing direct arrays?

**Recommended decision:** planners may keep specialized closure/placement logic, but output must become a T3/T4 plan and pass node-data/reference/final-graph validation before one commit.

### `LIBTV-ING-DQ-006`: node data patch ownership

**Question:** which fields may `updateNodeData` write without aggregate planning?

**Recommended decision:** only registry-declared local fields. `sourceNodeId`、`edgeId`、`resultNodeIds`、`sourceBreakdownId`、`processId`、Director provenance and resource locator changes require specialized commands.

### `LIBTV-ING-DQ-007`: future import behavior

**Question:** what happens when portable import is invalid?

**Recommended decision:** parse/validate before canvas creation or active replacement. First authorized slice imports as a new canvas, and any failure leaves canvas list/active graph/history unchanged.

### `LIBTV-ING-DQ-008`: future server/run patch

**Question:** how may asynchronous result patches interact with local graph edits?

**Recommended decision:** patch declares base graph/revision, node ID, source media version、operation/run/attempt/result ID and field ownership. Stale/duplicate/current/invalid 先分类，再由 operation-specific full plan 决定 apply/quarantine/reject；它不能 generically overwrite graph identity、user-authored fields、current selection 或 history。完整机械合同见 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。

## 12. Correctness Invariants

Add the following to the `LIBTV-PAR-008` invariant family:

| ID | Invariant | Current status | Required result |
|---|---|---|---|
| `LIBTV-GI-018` | every graph write entry has one declared trust class and authority | missing centralized map | no unclassified direct graph mutation |
| `LIBTV-GI-019` | T1 transport cannot add/delete/replace semantic graph entities | current generic setters bypass | unknown/non-whitelisted change is zero mutation |
| `LIBTV-GI-020` | T3 command validates complete draft before one commit | current derived commands append directly | no partial multi-node/edge mutation; one history step |
| `LIBTV-GI-021` | T4 restore validates schema/invariants before swap | undo/redo shallow direct restore | failure preserves graph and history cursor |
| `LIBTV-GI-022` | T5 patch declares revision and field ownership | ordinary remote ingress absent | stale/conflicting patch cannot silently overwrite local state |

Compatibility cases:

| ID | Scenario | Expected decision |
|---|---|---|
| `LIBTV-GC-018` | same invalid edge submitted through gesture and direct `addEdge` | same structural reason; zero mutation |
| `LIBTV-GC-019` | invalid edge embedded in derived multi-node draft | entire command reject/unknown; no partial nodes/edges/history |
| `LIBTV-GC-020` | React Flow `EdgeChange` attempts add/replace | reroute/reject; cannot bypass connection/reconnect authority |
| `LIBTV-GC-021` | malformed undo/redo snapshot | restore reject; history stacks unchanged |
| `LIBTV-GC-022` | clipboard/import contains valid structure plus invalid data ref | whole packet reject with path diagnostic |
| `LIBTV-GC-023` | stale server result patches a locally replaced node | stable stale/conflict result; no silent field overwrite |

## 13. Local Fixture Contract

### 13.1 Identity

`LIBTV-FIX-LOCAL-GRAPH-ENTRYPOINT-01` is a future deterministic fixture. Current status: `DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`.

It composes existing fixture contracts instead of creating another unrelated demo graph:

- A/B/C ordinary connection topology from `LOCAL-GRAPH-CONNECTION-01`;
- group/child/external/derived topology from `LOCAL-SUBGRAPH-COPY-01`;
- 11-type/reference/aggregate corpus from `LOCAL-NODE-DATA-01`;
- delete impact scenes from `LOCAL-GRAPH-DELETE-01`;
- valid/invalid history and document payloads from `LOCAL-GRAPH-DOCUMENT-01`.

### 13.2 Stable aliases

| Alias | Role |
|---|---|
| `A_SOURCE` / `B_TARGET` / `C_CYCLE` | ordinary structural cases |
| `G_PARENT` / `G_CHILD_A` / `G_CHILD_B` | group/parent transport and command cases |
| `D_DERIVED` | node with owned `sourceNodeId/edgeId` |
| `S_SHOT` / `S_RESULT` | reciprocal aggregate case |
| `P_PROCESS_*` | complete process cohort |
| `H_VALID` / `H_INVALID` | valid and malformed history snapshots |
| `R_LOCAL` / `R_STALE` | current and stale remote patch descriptors |

### 13.3 Scenario matrix

| Scenario | Entry | Proposal | Expected |
|---|---|---|---|
| ordinary gesture | route connect | duplicate/self/cycle | stable structural reject, zero mutation |
| programmatic connect | store `addEdge` | same proposals | same structural result |
| transport edge add | `onEdgesChange` | `add/replace` variant | rerouted or rejected before generic apply |
| position-only transport | `onNodesChange` | move selected child | position delta only, declared history behavior |
| derived draft invalid | derived planner | valid node + cycle/dangling edge | entire command reject, no partial node |
| copy invalid ref | copy planner | unknown owned identity | unknown/reject, no IDs consumed persistently |
| delete unresolved | delete planner | relation with unknown policy | unknown, graph/history/UI unchanged |
| undo invalid | history restore | malformed snapshot | restore reject, cursor unchanged |
| clipboard invalid | packet load | valid structure + bad aggregate ref | full reject with path diagnostic |
| stale server patch | T5 ingress | old run/revision | stale/conflict result, no overwrite |

### 13.4 Reset

Every scenario uses a fresh Page and a newly constructed local graph. Undo/redo is scenario behavior, never teardown. No generic mutable store injection is authorized by this document; fixture runtime needs separate authorization and must follow [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md).

## 14. `LIBTV-VR-014` Replacement Design

`LIBTV-VR-014` verifies routing enforcement, not the full semantics already owned by `VR-009..013`.

### 14.1 Static authority layer

- enumerate exported graph mutation actions from `CanvasState`;
- map every caller to T0-T5;
- fail on new unclassified actions that write `nodes/edges`;
- flag direct `edges: [...` or whole-array replacement outside approved planners/commit boundary;
- ensure FrameOS paths are excluded rather than accidentally governed by LibTV rules.

Static checks are advisory until an implementation establishes stable module boundaries; they must not use brittle line-number allowlists as architecture.

### 14.2 Pure layer

- same proposal through every applicable ingress produces equivalent structural result;
- T1 whitelist rejects add/remove/replace semantic changes;
- T3 invalid final draft yields zero mutation and one stable reason;
- T4 invalid snapshot/packet leaves graph/history unchanged;
- T5 stale patch leaves node/data/revision unchanged;
- accepted T2/T3 increments history exactly once;
- rejected/unknown entry consumes no history step and no surviving ID.

### 14.3 Focused browser layer

- real Handle drag remains Batch 57 behavior;
- node drag and organize only change allowed position/viewport fields;
- edge scissors/delete keyboard route through declared delete authority;
- node-local delete buttons do not produce node-only/dangling intermediate state;
- undo/redo selection and overlay owner cleanup follow existing contracts;
- no console/page errors, layout regression or edge flow visual change.

### 14.4 Retained verifiers

`VR-014` supplements rather than replaces:

- `VR-009` connection semantics;
- `VR-010` document/history schema;
- `VR-011` subgraph copy;
- `VR-012` node data identity;
- `VR-013` relation-aware delete;
- Batch 3-8 bounded graph/history/group regressions;
- Batch 57 structural connection recorded pass.

## 15. Authorized Implementation Slices

No slice is authorized by this document. If the user later authorizes code, keep the work vertical and separately reviewable.

### Slice A: classify and narrow React Flow transport

- define allowed node/edge change variants;
- preserve selection/drag/layout behavior;
- route semantic add/remove/replace through named commands;
- add static entrypoint inventory and narrow runtime tests.

### Slice B: validated multi-entity commit boundary

- introduce immutable draft/decision/commit shape;
- migrate one low-risk derived command first;
- prove full-draft reject and one-step accept;
- do not migrate every creator in one broad refactor.

### Slice C: copy/delete/data command integration

- consume existing planners/contracts rather than inventing parallel rules;
- keep source/product unknown states explicit;
- validate node data refs and aggregate integrity before commit.

### Slice D: history restore boundary

- first complete deep snapshot isolation from `VR-010`;
- add lighter history decode/invariant check;
- define invalid restore diagnostics without consuming past/future.

### Slice E: clipboard/import

- strict versioned packet/document parse;
- parse and validate before new-canvas creation;
- final graph invariant and zero-partial UI/history behavior;
- ordinary persistence remains deferred.

### Slice F: remote/server authority

- only after a real backend/run/sync interface is authorized;
- revision/base identity and field ownership are mandatory;
- compose `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` / `LIBTV-VR-015` before provider integration;
- do not copy Open Canvas file/KV/conflict UI as LibTV parity.

## 16. Implementation Review Checklist

Before approving any future graph mutation code, answer all of these:

1. What is the named user/system command?
2. Which trust class T0-T5 owns it?
3. Is the input a proposal, transport delta, command plan, document or remote patch?
4. What immutable graph identity/revision is the plan based on?
5. Which structural, node-data, aggregate and command-specific validators run?
6. Does validation occur before every graph/history mutation?
7. Can the command create more than one node/edge or patch source data?
8. If yes, is the whole draft committed once?
9. What happens to selection and node-bound overlays?
10. What resource/run effects are outside graph history?
11. What stable reject/unknown diagnostics are returned?
12. Can React Flow or a component call a lower-level bypass?
13. How do undo/redo reproduce or reject the result?
14. Which named fixture and verifier close the change?
15. Which LibTV source behavior remains unknown?

Any missing answer keeps the change in design review.

## 17. Non-Goals And Stop Conditions

- No current `setNodes/setEdges` action is removed or changed by this report.
- No derived creator, copy, delete, data patch or history path is migrated.
- No generic graph transaction framework is authorized.
- No Open Canvas source file or submodule pointer is changed.
- No ordinary-canvas persistence, revision, autosave, conflict UI or server is introduced.
- No source-site write interaction is needed to confirm clone correctness boundaries.
- No current Batch 57 structural connection result is downgraded; its scope remains explicit.
- If future implementation would require one broad rewrite of all store actions, stop and split by command/fixture/verifier.

## 18. Bottom Line

Open Canvas 的最大启发不是某个 validator 函数，而是把 mutation authority 分成 store command、serialization、full graph validation、API validation、revision 和 server patch 多层。同时，它的 clipboard、framework delta 和 tolerant normalization 也证明：参考项目本身仍有入口旁路，不能照抄。

当前 LibTV clone 已有一个可靠的 connection structural island，但 graph mutation 仍是“多个 intent-specific direct writes + 两个 generic array setters + shallow history restore”。下一步最有价值的实施前工作不是继续添加散落 guard，而是按 T0-T5 给入口定权、把 multi-entity 操作提升为 full-draft plan，并用 `LIBTV-VR-014` 证明任何入口都不能绕过已有 `VR-009..013` 语义权威。
