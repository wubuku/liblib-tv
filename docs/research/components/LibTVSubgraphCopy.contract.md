# LibTV Subgraph Copy And Duplicate Contract

> Scope: 普通 LibTV route 的 selection duplicate、node-only copy、group descendant closure、ID/reference rewrite、edge policy、placement、history、fixture 和 verifier 设计。
>
> Status: `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL` / `SOURCE_GESTURE_BLOCKED`。本文不授权修改 `src/`、快捷键、系统剪贴板、Option-drag 或共享源站 graph。

## 1. Why This Contract Exists

当前 clone 已经能复制普通节点、多选集合、group descendants 和整张 canvas，但“复制”仍包含多套不一致语义：

- `duplicateNode(nodeId, includeEdges = true)` 默认复制所有 incident edges；
- `duplicateSelectedNodes()` 对单个非 group 也走 incident-edge compatibility 分支；
- 多选或 group 只复制 internal edges；
- child 单独复制会脱离旧 parent；
- `duplicateCanvas()` 重写整图 node/parent/edge ID，但不使用 portable document codec；
- node `data` 中的 `sourceNodeId`、`edgeId`、process/run/media identity 没有统一 remap/reset registry；
- 系统 clipboard 和 source-advertised Option-drag 尚未实现。

Open Canvas 提供了 versioned clipboard packet、internal-edge closure、ID map 和 flow-coordinate placement 的工程方法，但它没有 LibTV 的 parent/group/derived/process metadata。后续不能只复制它的 payload，也不能继续把所有复制入口压成一个 boolean。

## 2. Evidence And Inspiration Boundary

### 2.1 `OPEN_CANVAS_FACT`

固定 submodule `cf3a906bb8c35bb940d3267497e7f394b8f42582`：

- 复制 payload 使用 custom MIME `application/x-cyberbara-canvas-nodes` 和 `version: 1`；
- payload 提取 selected nodes 及 source/target 都在选择内的 internal edges；
- paste 先检查 node/edge limits，再为所有 node 建 old -> new ID map；
- edge endpoint 使用 ID map 重写，并保留 handle/type/data；
- paste placement 以 selection flow-space bounds 对齐当前 viewport screen center 转换后的 flow point；重复粘贴每次增加 `48` flow-unit shift；
- editable target 和 image preview 会拦截 canvas copy/paste；内存 clipboard 是系统 MIME 不可读时的本页 fallback。

证据：[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)、[`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts)。

可借的是 versioned packet、structured extraction、two-pass ID map、internal-edge closure、flow-space placement 和 failure-before-mutation。不能移植它的五类 node、MIME 名称、`48px` 产品数字、`200/400` limits、no-group assumption、provider data 或 UI feedback。

### 2.2 `SOURCE_FACT` And Unknowns

LibTV source 现有证据只足以说明：

- 快捷键帮助曾显示“复制节点和连线 `D`”；
- 另有“节点复制 `Option+拖动`”source-advertised 命令；
- 当前 source modifier、single/multi/group closure、external edge policy、drag ghost、cancel 和 placement 仍未由 disposable fixture 确认。

因此 exact keyboard、Option-drag 和 external-edge semantics 保持 `SOURCE_GESTURE_BLOCKED`。本文的 closure/reference/atomicity 是 clone correctness decision，不冒充 source implementation。

### 2.3 `CLONE_FACT`

当前 clone 的直接合同见 [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`DUPLICATE_SELECTION.spec.md`](../liblib-canvas-batch5-2026-08-25/DUPLICATE_SELECTION.spec.md) 和 [`VIDEO_GROUP_PARENTING.spec.md`](../liblib-canvas-batch8-2026-08-25/VIDEO_GROUP_PARENTING.spec.md)：

- Meta/Ctrl+D 调用 `duplicateSelectedNodes()`；source modifier 未确认；
- root selection 去重并自动包含其全部 descendants；
- copied parent 存在时 child 保持相对位置并重写 parentId；
- child 单独复制时转成 top-level absolute position并清除 parentId/extent；
- root copies 默认 `+40,+40`；copied child 在 copied parent 内保持原相对位置；
- duplicate transaction 一次入 history，完成后只选择用户请求 roots 的副本；
- undo/redo 恢复 graph 后清 selection；
- current single ordinary branch 复制所有 incident edges，multi/group 只复制 internal edges；
- `duplicateNode()` 没有普通 UI caller，但仍是 store public action；
- `duplicateCanvas()` 属于 canvas lifecycle，不属于 graph undo。

## 3. Named Commands, Not A Boolean

后续 copy planner 必须收到明确 command，而不是 `includeEdges?: boolean`。

```ts
type LibTVCopyCommand =
  | {
      kind: "duplicate-selection";
      requestedNodeIds: string[];
      placement: { kind: "fixed-flow-offset"; x: 40; y: 40 };
      edgePolicy: "internal-only" | "incident-compatibility";
    }
  | {
      kind: "create-node-copy";
      requestedNodeId: string;
      placement: { kind: "fixed-flow-offset"; x: 40; y: 40 };
      edgePolicy: "none";
    }
  | {
      kind: "paste-subgraph";
      packet: LibTVSubgraphPacketV1;
      placement: { kind: "flow-anchor"; anchor: { x: number; y: number } };
      edgePolicy: "internal-only";
    }
  | {
      kind: "option-drag-copy";
      requestedNodeIds: string[];
      placement: { kind: "flow-delta"; x: number; y: number };
      edgePolicy: "source-decision-required";
    };
```

Command boundaries:

| Command | Current maturity | Rule |
|---|---|---|
| duplicate selection | runtime exists | retain compatibility until an authorized consolidation slice |
| create node copy | historical context-menu concept | node-only semantics must not inherit incident edges |
| paste subgraph | missing | separately versioned packet and focus/clipboard ownership |
| option-drag copy | source-advertised, missing | blocked until source fixture confirms start/ghost/drop/cancel |
| duplicate canvas | runtime exists, separate domain | never route through graph history command |

`incident-compatibility` is a named legacy branch, not the default safe policy. New multi/group/clipboard commands use `internal-only` unless source/product evidence explicitly says otherwise。

## 4. Copy Closure

### 4.1 Root selection

```text
requested IDs
  -> remove duplicates
  -> retain IDs that exist in active canvas
  -> preserve graph array order for deterministic planning
  -> root IDs
```

If no valid root remains, return `NO_VALID_ROOTS` with zero mutation. A mixed valid/missing request must not silently ignore the missing identity; programmatic callers receive `DANGLING_REQUESTED_ID` unless the command explicitly came from sanitized current selection。

### 4.2 Descendant expansion

- selecting a parent/group includes every recursive descendant once；
- selecting both ancestor and descendant does not create a second descendant copy；
- descendant expansion follows parentId ownership, not edge reachability；
- malformed parent cycles or missing parents return structural error before ID generation；
- selecting only a child does not include its old parent or siblings；
- process/derived nodes are not recursively included merely because data contains `sourceNodeId`；that relation is metadata/provenance, not ownership。

The resulting `copyNodeIds` is the ownership closure. `selectedCopyIds` contains only mapped root IDs, preserving the user-visible selection contract。

## 5. Two-Pass Identity Rewrite

### Pass 1: allocate identities

Before constructing any copied entity:

1. allocate a new node ID for every `copyNodeId`；
2. choose candidate edges under the declared edge policy；
3. allocate a new edge ID for every copied edge；
4. assert all generated IDs are non-empty, unique and absent from the target graph；
5. keep nodeMap and edgeMap immutable for the remainder of the plan。

No graph mutation occurs during allocation. Random/time-based generation can be an implementation detail, but deterministic fixture ID providers are required for pure verifier output。

### Pass 2: rewrite structure and data

- node ID -> nodeMap；
- parentId -> mapped parent if parent is copied；otherwise detach under section 6；
- edge ID -> edgeMap；
- edge source/target -> nodeMap where endpoint is copied；
- Handle/type/visual edge data preserved through the graph codec；
- node data references follow the role registry in section 7；
- display-only labels are projected after stable identities are resolved。

If any required rewrite is unresolved, discard the whole plan. Do not create nodes first and repair edges/data later。

## 6. Parent And Placement Contract

### 6.1 Copied parent exists

When parentId is in nodeMap:

- child parentId becomes mapped parent ID；
- child relative position remains unchanged；
- child extent remains `parent` only if the copied parent contract supports it；
- parent root receives command placement；
- group dimensions/z-index follow the declared graph document codec。

### 6.2 Parent not copied

When a child is a requested root but its parent is outside closure:

```text
old absolute position
  = child relative position + ancestor positions
new top-level position
  = old absolute position + command placement delta
```

The copy clears `parentId` and `extent`. It must not retain a hidden reference to the old group or double-apply the parent offset。

### 6.3 Placement modes

| Mode | Coordinate domain | Contract |
|---|---|---|
| fixed-flow-offset | flow/world | current clone duplicate compatibility；root +40,+40；children stay relative |
| flow-anchor | flow/world | align copied closure bounds to an explicit anchor, then apply declared repeat offset |
| flow-delta | flow/world | Option-drag candidate uses pointer-derived flow delta after source evidence |

Screen pixels must be converted once through React Flow before planning. Zoom/pan cannot change copied graph geometry. Open Canvas viewport-center behavior is an inspiration for `flow-anchor`, not LibTV's decided paste placement。Actual host、coordinate-domain、live/stable viewport and owner validation are delegated to [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)；this copy contract retains closure/bounds/delta/history authority.

## 7. Node Data Reference Roles

Structural ID map alone is insufficient for current LibTV metadata. Every nodeType/dataVersion validator must classify reference-bearing fields。

| Role | Examples | Copy decision |
|---|---|---|
| `OWNED_NODE_REF` | metadata points to an entity owned inside copied subgraph | rewrite through nodeMap；missing target rejects |
| `EXTERNAL_PROVENANCE_NODE_REF` | copied derived result intentionally remembers original source | preserve old ID with explicit provenance marker；never pretend it was copied |
| `OWNED_EDGE_REF` | metadata `edgeId` names an edge copied in the same transaction | rewrite through edgeMap；missing copied edge rejects |
| `GLOBAL_ASSET_REF` | stable asset/media version identity | preserve；does not imply asset duplication |
| `RUN_OR_TASK_ID` | runId/provider task identity | reset/new/unresolved according to node contract；never silently reuse live task identity |
| `SESSION_OR_UI_ID` | editor session, temporary mark owner, pending state | remove/reset；not portable semantic data |
| `DISPLAY_PROJECTION` | sourceLabel、ordinal、title suffix | recompute from stable identity or apply declared copy label；not identity |

The detailed V0 classification for current `sourceNodeId`、`edgeId`、`processId`、capture/export IDs、source labels/posters、marks/regions、shot result identity and media locators is now defined by [`LibTVNodeDataIdentity.contract.md`](LibTVNodeDataIdentity.contract.md)。It extends this table with aggregate、scoped-local、catalog、media-locator and external-provenance roles。Auto Link mention identity remains owned by [`LibTVAutoLink.contract.md`](LibTVAutoLink.contract.md)。

If a node type contains a field that looks like an identity/reference but has no registry rule, return `UNMODELED_REFERENCE_FIELD` / `unknown`. Do not deep-clone it and call the transaction safe。

## 8. Edge Policies

### 8.1 `internal-only`

Copy an edge only when both source and target are in `copyNodeIds`. Both endpoints map to new node IDs. This is the safe default for multi/group/clipboard and matches Open Canvas's structured subgraph method。

### 8.2 `none`

Copy no edges. Used by explicit “create node copy” semantics. Node data must still clear/rewrite edge-owned fields；a copied node cannot retain an `edgeId` that claims a non-copied edge is owned by the new node。

### 8.3 `incident-compatibility`

Current single ordinary duplicate may copy every incident edge, mapping only the selected endpoint and preserving the external original endpoint. This can create：

- duplicate/reverse node pairs；
- cycle or self/Reference policy conflicts；
- ambiguous copied edge metadata；
- a new node unexpectedly connected to every existing neighbor。

Therefore this branch is `COMPATIBILITY_HOLD`, not a template for new commands. Every candidate incident edge must pass [`LibTVGraphConnection.contract.md`](LibTVGraphConnection.contract.md) with origin `programmatic`. Any reject/unknown aborts the full copy transaction；do not partially omit failed edges。

### 8.4 External edge record

When an external edge is intentionally not copied, the packet may record a non-executable boundary summary for diagnostics, but paste must not recreate it without an explicit product command. A summary is not an edge and never enters graph/history。

## 9. Copy Plan Result And Reasons

```ts
type LibTVSubgraphCopyPlanResult =
  | {
      status: "ready";
      copiedNodes: SerializedLibTVNodeV1[];
      copiedEdges: SerializedLibTVEdgeV1[];
      selectedCopyIds: string[];
      nodeIdMap: Record<string, string>;
      edgeIdMap: Record<string, string>;
    }
  | { status: "reject"; reason: SubgraphCopyRejectionReason }
  | { status: "unknown"; reason: SubgraphCopyUnknownReason };
```

Stable rejection reasons：

| Reason | Meaning |
|---|---|
| `NO_VALID_ROOTS` | sanitized root set is empty |
| `DANGLING_REQUESTED_ID` | caller requested a missing node |
| `MISSING_PARENT` | closure contains unresolved parent ownership |
| `PARENT_CYCLE` | parent chain is cyclic |
| `ID_COLLISION` | allocated node/edge ID collides |
| `INVALID_PLACEMENT` | non-finite anchor/delta or invalid bounds |
| `NON_PORTABLE_NODE_DATA` | graph document codec cannot isolate required data |
| `CONNECTION_REJECTED` | copied edge violates a defined connection rule |
| `COPY_LIMIT_EXCEEDED` | clone-defined count/byte/depth budget exceeded |

Unknown reasons：

| Reason | Why unknown |
|---|---|
| `UNMODELED_NODE_TYPE` | runtime node type/data registry incomplete |
| `UNMODELED_REFERENCE_FIELD` | node data identity role not declared |
| `EXTERNAL_EDGE_POLICY_REQUIRED` | caller asks for external edges without named policy |
| `SOURCE_OPTION_DRAG_UNCONFIRMED` | source start/ghost/drop/cancel semantics unknown |
| `CONNECTION_POLICY_UNRESOLVED` | Reference/domain edge validator returns unknown |

Reject/unknown both produce zero nodes、edges、selection、history、viewport and UI residue。

## 10. Atomic Transaction Contract

One accepted copy command：

1. snapshots the pre-command graph once；
2. computes and validates the complete copy plan without mutation；
3. appends all copied nodes/edges in one store transaction；
4. selects only mapped user roots, not automatically included descendants；
5. adds exactly one graph history step；
6. leaves viewport unchanged for duplicate-selection/node-copy；
7. clears redo future；
8. exposes no half-created IDs or transient graph entities。

Undo removes the complete copied subgraph in one step and clears selection under current history policy. Redo restores the same logical copied identities from snapshot；it does not run the planner again or allocate new IDs。

Failure after ID allocation but before commit is still zero mutation. Toast/feedback, if later designed, is UI state outside history。

## 11. Versioned Clipboard Packet

Future system clipboard uses a shape distinct from whole graph document：

```ts
type LibTVSubgraphPacketV1 = {
  kind: "libtv-canvas-subgraph";
  schemaVersion: 1;
  sourceBounds: { x: number; y: number; width: number; height: number };
  rootNodeIds: string[];
  nodes: SerializedLibTVNodeV1[];
  edges: SerializedLibTVEdgeV1[];
  externalBoundary?: Array<{
    direction: "incoming" | "outgoing";
    internalNodeId: string;
  }>;
};
```

Rules：

- packet uses the narrow codec from [`LibTVGraphDocument.contract.md`](LibTVGraphDocument.contract.md) but has independent kind/version/identity policy；
- source canvas/project/account identity is not required to paste；
- externalBoundary is diagnostics only, contains no executable external endpoint ID；
- parser is strict and version-aware；future version returns unsupported, not empty clipboard；
- editable targets, active text editors and modal/preview ownership must prevent canvas interception；
- MIME name、plain-text fallback、permission/toast and cross-tab behavior require a separate surface/security plan。

No clipboard implementation is authorized by this contract。

## 12. Fixture Contract

### 12.1 Fixture identity

`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` is the future deterministic copy fixture. Current status：`DESIGN_SPEC_COMPLETE / RUNTIME_MISSING`。

It derives from fresh Page + `LIBTV-FIX-LOCAL-EMPTY-01` and provides deterministic IDs for pure planning. The browser layer may use current demo/group topology only after recording exact aliases。

### 12.2 Topology

```text
G_GROUP
  |- A_CHILD -> B_CHILD
  `- C_CHILD

X_EXTERNAL -> A_CHILD
B_CHILD -> Y_EXTERNAL

D_DERIVED
  data.sourceNodeId = A_CHILD
  data.edgeId = edge(A_CHILD, D_DERIVED)
```

Add a nested metadata node with marks/regions/process arrays and a node with an intentionally unmodeled reference field。

### 12.3 Cases

| Case | Request/policy | Expected |
|---|---|---|
| single node-only | A / none | A copy only；detached top-level if parent excluded |
| single current compatibility | A / incident | all candidates validated；whole transaction accept or no-op |
| partial multi | A+B / internal | A/B + one internal edge；external edges absent |
| group | G / internal | G + all descendants；parents mapped；only internal edges |
| ancestor+child selected | G+A / internal | each copied once；selection roots mapped once |
| child detached | A / internal | absolute+offset；parent/extent cleared |
| derived with owned refs | A+D / internal | sourceNodeId/edgeId mapped by role registry |
| derived alone | D / none | external provenance preserved explicitly or unknown；never fake remap |
| unknown ref field | node with unmodeled ID field | unknown；zero mutation |
| parent cycle/missing | malformed pure graph | stable reject |
| repeated packet paste | same packet + declared count | deterministic flow-anchor offsets；IDs unique |
| undo/redo | accepted group copy | one-step remove/restore；selection/history/viewport exact |

### 12.4 Reset

Each scenario uses a fresh Page. Before action assert aliases、node/edge counts、selection、viewport、history and no open overlay. After assertions discard Page；undo is part of the case, not teardown。

## 13. Verifier Contract

Future `LIBTV-VR-011`：

### 13.1 Pure layer

- root sanitize、descendant closure、ancestor/child dedupe；
- parent copied vs detached absolute placement；
- deterministic nodeMap/edgeMap and collision rejection；
- internal/none/incident policy distinction；
- reference-role rewrite/preserve/reset/unknown；
- graph document deep isolation；
- packet strict parse/version/bounds；
- connection reject/unknown aborts whole plan；
- stable reason and zero-mutation descriptors。

### 13.2 Focused browser layer

- current duplicate-selection command on single/multi/group/child；
- copied nodes/edges/parentId/data references and selected roots；
- fixed flow offset remains invariant under pan/zoom；
- one-step history and redo logical identity；
- editable target/modal/preview shortcut ownership；
- no console/page errors and no overlay/edge visual regression。

System clipboard and Option-drag browser cases remain absent until their separate authorization/source evidence exists. Historical Batch 3/5/8 verifiers stay retained and version-labeled；`VR-011` does not rewrite them to claim current source parity。

## 14. Authorized Implementation Slices

### Slice A: Pure Copy Planner

- named commands/edge policies；
- closure、two-pass IDs、parent placement；
- pure result/reasons；
- deterministic fixture provider and `VR-011` pure cases。

### Slice B: Reference Role Registry Runtime

- use the completed 11-type static audit and [`LibTVNodeDataIdentity.contract.md`](LibTVNodeDataIdentity.contract.md) as design authority；
- implement rewrite/preserve/reset/projection per nodeType/dataVersion and named operation；
- block unmodeled reference fields；
- no provider/task backend。

### Slice C: Consolidate Existing Duplicate Selection

- route current Meta/Ctrl+D through planner without changing sourced visual；
- preserve current command compatibility deliberately；
- deprecate boolean semantics only after caller audit；
- focused browser/history cases。

### Slice D: Explicit Node-Only Copy

- only if a current LibTV surface/contract requires it；
- no edge copy；owned edge metadata cleanup；
- separate UI command and verifier scenario。

### Slice E: System Clipboard

- versioned packet/MIME/focus ownership/security；
- flow-anchor placement and repeated paste count；
- separate from duplicate-selection shortcut。

### Slice F: Option-Drag Copy

`BLOCKED_BY_DISPOSABLE_SOURCE_FIXTURE`。编码前需要先确认 source start threshold、ghost、multi/group scope、drop/cancel、edge policy、selection 和 history。

Every slice requires explicit coding authorization. Slice A/B must not opportunistically implement clipboard、Option-drag、persistence、FrameOS copy or source-site mutation。

## 15. Non-Goals And Stop Conditions

- 不声称 current LibTV source 使用 Open Canvas clipboard payload/placement；
- 不把 source shortcut label alone 当作 single/multi/group/external-edge contract；
- 不把 `incident-compatibility` 推广为新命令默认值；
- 不复制 DOM、screen pixels、React component/ref、selection/hover/editor session；
- 不复制 provider run/task identity、billing、upload session 或 remote save state；
- 不通过 silent field drop 处理 unmodeled node data/reference；
- 不让 partial edge failure 留下 copied nodes；
- 不把 duplicate canvas 塞进 graph undo，也不把 portable graph document 等同 clipboard packet；
- 不修改 FrameOS 独立 copy behavior、Open Canvas submodule 或 shared source project；
- 若无法在 mutation 前完成 closure、ID/reference rewrite 和 connection validation，停止并回到合同评审。
