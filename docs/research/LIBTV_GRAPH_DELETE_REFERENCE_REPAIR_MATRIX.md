# LibTV Graph Delete Impact And Reference Repair Matrix

> Status: `STATIC_AUDIT_COMPLETE / DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / SOURCE_PRODUCT_DECISIONS_PARTIAL`
>
> Scope: 普通 LibTV route 的 node、edge、selection、group、derived metadata、shot/process aggregate、canvas lifecycle、overlay owner 和 media locator 删除影响。FrameOS 与 Director 内部对象删除不在本文范围；Director graph shell 和导出结果的跨边界影响进入本文。
>
> Constraint: 本文只记录研究、决策候选和 implementation handoff。它不授权修改 `src/`、测试、fixture adapter 或运行时行为。

## 1. Why This Matrix Exists

当前 clone 的通用删除闭包只有两层：

```text
requested node IDs
  -> parentId descendants
  -> incident edge endpoints
```

这足以保护 React Flow 的结构，但不足以保护 LibTV node data。普通画布还存在：

- nested `sourceNodeId` / `edgeId`；
- `shot-breakdown.resultNodeIds[] <-> shot-breakdown-result.sourceBreakdownId`；
- 12-node long-video process cohort 的 shared `processId`；
- Director shell、capture/export provenance 和独立 workspace；
- `uiStore` 中以 node ID 为 owner 的预览、标注、元素编辑和 Director surface；
- `data:`、`blob:`、repo path、remote URL 等不同资源生命周期。

所以“节点和 incident edge 已消失”不等于删除事务正确。正确的删除必须回答：

1. 哪些 graph entity 真正被删除；
2. 哪些 surviving node data 必须 patch、detach、reset 或阻止删除；
3. 哪些 aggregate 必须整体处理；
4. selection、overlay、history 和 resource owner 如何收口；
5. 哪些是 correctness floor，哪些仍需 LibTV 源站或产品决定。

本文把这些答案集中到一个可被后续 agent 发现和执行的设计 authority 中。

## 2. Baseline And Evidence Boundary

### 2.1 Fixed revisions

| Object | Revision / boundary |
|---|---|
| clone committed baseline | `7338152474a5b719529211ab3181ea328cc9f3ca` |
| Open Canvas submodule | `cf3a906bb8c35bb940d3267497e7f394b8f42582` |
| clone graph owner | [`src/store/canvasStore.ts`](../../src/store/canvasStore.ts) |
| clone route owner | [`src/app/page.tsx`](../../src/app/page.tsx) |
| clone UI owner | [`src/store/uiStore.ts`](../../src/store/uiStore.ts) |
| upstream graph owner | [`shared/stores/canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts) |
| upstream typed data | [`shared/lib/canvas/types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts) |

审计时共享工作区另有未提交的 Batch 57 graph connection WIP。该 WIP 只改变 connection validation、route connection handlers 和 debug evidence，没有改变 committed baseline 的删除入口、descendant closure、node data relation、aggregate 或 canvas removal 行为，因此不进入本文事实基线，也未被修改或暂存。

### 2.2 Classification vocabulary

| Classification | Meaning |
|---|---|
| `OPEN_CANVAS_FACT` | 固定 submodule 源码可直接复核 |
| `CLONE_FACT` | 固定 clone commit 可直接复核 |
| `SOURCE_FACT` | 已有 LibTV bundle/DOM/运行证据直接支持 |
| `REQUIRED_CORRECTNESS` | 不依赖产品选择也不能违反的数据完整性底线 |
| `PROPOSED_CLONE_DEFAULT` | 当前最稳妥的 clone 候选语义，尚未编码授权 |
| `SOURCE_PRODUCT_DECISION_REQUIRED` | cascade、detach、保留 provenance 等用户可见语义仍需源站或产品决定 |
| `DEFERRED_BACKEND_SCOPE` | run record、asset lease、remote cleanup、持久化等不属于当前前端原型 |

事实、启发和决策必须分开。Open Canvas 的删除实现不能被描述为 LibTV 源站行为；clone 的现有 cascade 也不能被反推为源站内部命令。

## 3. Executive Findings

### 3.1 What Open Canvas actually contributes

固定 Open Canvas 版本的 node data 是五类 closed union，普通 graph dependency 主要由 edges 表达。它的删除动作：

- `deleteNode(nodeId)` 删除一个 node 和 incident edges；
- `deleteEdge(edgeId)` 删除一个 edge；
- `deleteSelection()` 同时删除 selected nodes、selected edges 和被删 node 的 incident edges；
- `deleteIncomingReference(target, source)` 删除一条 source-to-target edge；
- conflict 状态下所有上述删除均 no-op；
- accepted mutation 设置 dirty/save state，menu owner 随命令关闭。

Open Canvas 没有 LibTV 的 parent descendants、shot reciprocal refs、process cohort 或 nested graph-owned edge IDs。因此值得借鉴的是：

1. 删除入口集中；
2. conflict/invalid 时零变更；
3. node/edge selection 一次提交；
4. typed data 和 normalize boundary 使 hidden relation 更少；
5. graph deletion 与 document deletion 分层。

不能借鉴为：

- LibTV 只需删 incident edges；
- 所有结果节点都应跟 source 一起删除；
- Open Canvas 的五类 node/data shape 可以替代 LibTV 11-type registry；
- dirty/save/conflict backend 已经存在于 clone。

### 3.2 Current clone risk

`CLONE_FACT`：`removeNode()` 和 `removeSelectedNodes()` 只 patch nodes、edges、selection 和 history；surviving node data 不变。`removeEdge()` 只过滤 edge。结果包括：

- 删除 shot source 后 result nodes 保留 stale `sourceBreakdownId`；
- 删除一个 shot result 后 source 保留 stale `resultNodeIds`；
- 删除任一 process node 后留下 partial cohort；
- 删除 source 或手动删除 derived edge 后 target 的 `sourceNodeId/edgeId` 仍声称 relation 有效；
- 手动删 continuation edge 后 `clearVideoContinuation()` 仍会按 stale edgeId 执行；
- 删除 active canvas/node 可能留下 `uiStore` owner ID，graph transaction 本身不关闭它；
- 删除含 `blob:` URL 的 node 没有明确资源 owner，既不能证明已释放，也不能安全自动 revoke。

### 3.3 Highest-value decision

删除不能继续作为 `filter(nodes) + filter(edges)` helper。后续授权实现应使用：

```text
named delete command
  -> structural closure
  -> relation inverse index
  -> aggregate impact
  -> per-type repair policy
  -> UI invalidation/resource diagnostics
  -> full-plan integrity validation
  -> one graph/history commit
```

任何无法决定 cascade/detach/reset 的关系返回 `unknown`，而不是先删结构再留下半个关系。

## 4. Destructive Command Inventory

### 4.1 Current commands

| Command / action | Current entry | Current delta | History domain | Current maturity |
|---|---|---|---|---|
| `removeNode(nodeId)` | store API；普通 route 未发现 direct UI caller | node + descendants + incident edges | 1 graph step | `CLONE_INFRA` |
| `removeSelectedNodes()` | Delete/Backspace | selected nodes + descendants + incident edges | 1 graph step | `CLONE_INFRA` |
| `removeEdge(edgeId)` | edge scissors `delete-edge` event | one edge only | 1 graph step | `CLONE_INFRA / METADATA_UNSAFE` |
| `clearVideoContinuation(targetId)` | continuation target action | keep target；remove metadata + declared edge | 1 graph step | `SOURCE_BACKED_SHAPE` |
| `ungroupSelectedNodes()` | Shift+G | remove group shell；detach direct children to world position | 1 graph step | `CLONE_ONLY STRUCTURAL COMMAND` |
| `removeCanvas(canvasId)` | canvas row menu | remove canvas + its history；switch active if needed | not graph-undoable | `CLONE_INFRA` |
| React Flow `onNodesChange/onEdgesChange` remove | low-level adapter path | replace graph arrays | default no graph step | must not become user delete command |

### 4.2 Future named commands needed by the model

这些是 design vocabulary，不是当前 UI 功能：

| Command | Intent | Why generic delete is insufficient |
|---|---|---|
| `DELETE_GRAPH_SELECTION` | delete selected structural entities | must include selected edges and relation repair |
| `DELETE_GRAPH_NODE` | explicit one-node request | relation may expand or block |
| `DELETE_GRAPH_EDGE` | explicit edge request | edge may own target metadata/feature |
| `CLEAR_DERIVED_RELATION` | keep target but detach declared source relation | requires a per-type detach recipe |
| `RESET_SHOT_RESULTS` | preserve shot source and clear all result artifacts | reciprocal refs/status/dimensions update together |
| `DELETE_LONG_VIDEO_PROCESS` | delete one complete process cohort | shared aggregate ID and 22-edge closure |
| `DELETE_CANVAS_DOCUMENT` | remove one canvas lifecycle unit | overlays/history/resources/project fallback differ from graph undo |

Named commands prevent one Delete key from silently choosing incompatible semantics for group children、independent output media、pending placeholders and process aggregates。

## 5. Relation Topology

### 5.1 Canonical relation classes

| Relation class | Carrier | Example | Delete impact |
|---|---|---|---|
| `STRUCTURAL_OWNERSHIP` | `node.parentId/extent` | storyboard group -> child | parent delete expands descendants；ungroup detaches |
| `GRAPH_DEPENDENCY` | edge endpoints/handles | ordinary A -> B | endpoint delete removes edge；edge-only delete keeps endpoints |
| `OWNED_EDGE_METADATA` | nested `sourceNodeId + edgeId` | continuation、subtitle、split、capture、edit | structure and metadata must change together |
| `EXTERNAL_PROVENANCE` | node/external ID + display snapshot | rotateMirror、Director capture/export IDs | may survive only as explicitly unresolved/snapshot provenance |
| `RECIPROCAL_AGGREGATE` | refs in both directions + edges | shot source/results | every accepted delete repairs both directions |
| `SHARED_AGGREGATE` | `processId` + stage topology | long-video process | V0 partial cohort has no valid lifecycle |
| `UI_OWNER` | `uiStore.*.nodeId` | preview、annotate、element edit、Director | owner delete closes or explicitly detaches surface |
| `MEDIA_LOCATOR` | path/URL/data/blob | result preview/export | graph delete is not automatically byte/resource delete |
| `CANVAS_LIFECYCLE` | canvas ID + history + active owner | canvas tab removal | separate project command, not graph history |

### 5.2 Registered nested relations

Only the node data registry may enumerate these paths. Suffix matching such as `*Id` is forbidden。

| Data path | Ref roles | Current target state | Delete concern |
|---|---|---|---|
| `image.rotateMirror.sourceNodeId` | external provenance node | renderable image snapshot | source may disappear；do not cascade by field name |
| `image.frameCapture` | source node + owned edge | renderable image-like result | edge/source delete needs detach or explicit invalidation |
| `image.directorCapture` | Director graph source + edge + external IDs | `data:` image snapshot | shell/workspace and graph result lifetimes differ |
| `video.continuation` | source node + owned edge | empty authoring target | existing source-backed clear recipe |
| `video.subtitleErase` | source node + owned edge | pending placeholder | no independent result/run identity |
| `audio/video.audioSplit` | source node + owned edge | two sibling outputs | deleting one output does not automatically define sibling policy |
| `video.depthMotionCapture` | source node + owned edge | pending placeholder | no detach lifecycle |
| `video.pictureEdit` | source node + owned edge | pending placeholder + scoped marks | marks remain node-local；source relation still required |
| `video.smartMatting` | source node + owned edge | pending placeholder | no stable completed output identity |
| `video.directorAnimationExport` | Director source + edge + external IDs | ready `blob:` result | graph delete and object URL disposal are separate |
| `shot-breakdown.resultNodeIds[]` | owned node refs | complete result aggregate | must match reverse refs exactly |
| `shot-breakdown-result.sourceBreakdownId` | owned node ref | one source | must patch source on result delete |
| `long-video-process.longVideoProcess` | aggregate + source provenance | fixed pending cohort | process/source/edge deletion cannot leave partial V0 |

## 6. Current Behavior Matrix

| Action x relation | Current runtime | Surviving risk | Classification |
|---|---|---|---|
| delete plain node | node + incident edges removed | none when data has no inbound registered refs | `CLONE_FACT / LOCALLY_SAFE` |
| delete group | recursive descendants + incident edges removed | empty ancestor groups may remain when deleting child only | existing clone invariant |
| delete derived target | target + its incident edge removed | source usually has no reciprocal target list | structurally safe；resource cleanup unspecified |
| delete derived source | source edge removed；target survives | stale nested source/edge refs；pending target can still look actionable | `P0 DATA_RISK` |
| delete owned derived edge | edge removed；both nodes survive | target metadata still dereferences deleted edge | `P0 DATA_RISK` |
| clear continuation | target survives；continuation + declared edge removed | if edge was already removed, history still records metadata clear | source-backed feature detach；precondition validation incomplete |
| delete shot source | source + incident result edges removed | all result nodes keep stale reverse ref | `P0 AGGREGATE_RISK` |
| delete shot result | result + incident edge removed | source keeps stale ID/status complete | `P0 AGGREGATE_RISK` |
| delete process member | member + incident edges removed | remaining nodes share incomplete processId topology | `P0 AGGREGATE_RISK` |
| delete process source | source + three direct shot edges removed | complete cohort remains with stale sourceNodeId | `P0 AGGREGATE_RISK` |
| remove selected nodes | same closure as node delete | selected edges without selected nodes are not explicitly removed by this command | differs from Open Canvas selection delete |
| delete active overlay owner | selection may clear | annotate/element edit close through selection effect；preview/Director owner is not part of graph action | `P1 UI_LIFECYCLE_RISK` |
| remove active canvas | graph/history removed；selection clear | node-bound `uiStore` surfaces and resource locators are not part of action | `P1 PROJECT_LIFECYCLE_RISK` |

## 7. Delete Planner Contract

### 7.1 Conceptual input

```ts
type LibTVDeleteCommand =
  | { kind: "DELETE_GRAPH_SELECTION"; nodeIds: string[]; edgeIds: string[] }
  | { kind: "DELETE_GRAPH_NODE"; nodeId: string }
  | { kind: "DELETE_GRAPH_EDGE"; edgeId: string }
  | { kind: "CLEAR_DERIVED_RELATION"; targetNodeId: string; relation: string }
  | { kind: "RESET_SHOT_RESULTS"; sourceNodeId: string }
  | { kind: "DELETE_LONG_VIDEO_PROCESS"; processId: string };
```

The future pure planner consumes：

- current nodes/edges；
- canonical node-data registry；
- command-specific edge and aggregate policy；
- policy version；
- active selection and a read-only UI owner snapshot。

It does not mutate Zustand、React Flow、DOM、URL objects or history。

### 7.2 Plan output

```ts
type LibTVDeletePlan = {
  deleteNodeIds: string[];
  deleteEdgeIds: string[];
  nodeDataPatches: Array<{ nodeId: string; patch: unknown }>;
  selectionAfter: string[];
  uiInvalidations: Array<{ owner: string; nodeId: string }>;
  resourceDiagnostics: string[];
  diagnostics: string[];
  historySteps: 0 | 1;
};
```

Arrays use stable graph order for deterministic fixtures. A plan never encodes "delete by ID prefix" or "rewrite every field ending in Id"。

### 7.3 Planning order

```text
1. validate command and requested IDs
2. select type/version registry entries
3. expand structural descendants
4. collect incident and explicitly selected edges
5. build inverse index of registered node/edge/aggregate refs
6. collect shot/process aggregate impact
7. apply per-relation cascade/detach/reset/block policy
8. compute surviving node patches
9. compute selection and UI invalidations
10. classify media/resource consequences
11. validate the complete post-delete graph in memory
12. return ready/reject/unknown without mutation
```

Store integration, after explicit authorization, may submit only a `ready` plan and must push one pre-command graph snapshot。

## 8. Required Correctness Rules

These rules do not require source-site product semantics：

1. no accepted plan leaves an edge endpoint missing；
2. no accepted plan leaves `parentId` pointing to a missing node；
3. no accepted plan leaves an `OWNED_NODE_REF` or `OWNED_EDGE_REF` unresolved；
4. shot forward and reverse membership sets match after the transaction；
5. V0 process cohort is complete or absent；partial lifecycle requires a newer explicit schema；
6. aggregate expansion uses registered metadata, never node ID string prefixes；
7. selected node/edge IDs are subsets of the post-delete graph；
8. one accepted user command produces its declared 0/1 history step；
9. reject/unknown leaves graph、selection、history and UI owners unchanged；
10. graph deletion does not revoke or remotely delete media without an explicit resource owner contract；
11. low-level React Flow change handlers do not bypass the user-command planner；
12. undo restores graph data exactly, while session overlays remain closed/reset unless a separate UI contract says otherwise。

## 9. Per-Relation Policy Matrix

### 9.1 Structural ownership and ordinary edges

| Situation | Policy | Status |
|---|---|---|
| delete group | cascade all descendants and incident edges | `ACTIVE_CLONE_INVARIANT` |
| delete child only | preserve parent, even if empty | `ACTIVE_CLONE_INVARIANT` |
| ungroup | delete only group shell；detach direct children to absolute positions | named structural command；not generic delete |
| delete node endpoint | remove every incident edge | `REQUIRED_CORRECTNESS` |
| delete ordinary edge | keep endpoints | `REQUIRED_CORRECTNESS` |
| delete selection containing edge only | remove selected edge | `PROPOSED_CLONE_DEFAULT`；aligns with Open Canvas method |

### 9.2 Owned edge metadata

Generic `DELETE_GRAPH_EDGE` cannot remove an edge referenced by surviving node metadata unless a recipe is chosen：

| Recipe | When valid | Result |
|---|---|---|
| `CLEAR_FEATURE` | feature has an exact source-backed clear command | delete metadata + edge；keep target |
| `DETACH_TO_PROVENANCE` | target owns an independently renderable result and schema can mark source unresolved | keep media/content；remove owned edge role；preserve source label/external IDs as provenance |
| `CASCADE_DEPENDENT_TARGET` | target is only a placeholder and has no independent result identity | delete target and incident edges |
| `BLOCK_UNKNOWN` | target state/schema cannot prove either detach or cascade | zero mutation with stable unknown reason |

`PROPOSED_CLONE_DEFAULT`：

- continuation uses `CLEAR_FEATURE` because source bundle evidence already defines it；
- pending subtitle/edit/matting/depth placeholders use `BLOCK_UNKNOWN` until source/product decides whether source delete cascades；
- frame/Director outputs may eventually use `DETACH_TO_PROVENANCE`, but V0 lacks an explicit resolved/unresolved provenance field；
- manual edge delete for every registered `edgeId` relation is blocked unless it routes through the relation-specific command。

This is intentionally stricter than current runtime. It prevents a clean-looking graph from carrying destructive stale edge IDs。

### 9.3 Shot breakdown aggregate

`REQUIRED_CORRECTNESS`：source `resultNodeIds[]` and reverse `sourceBreakdownId` sets always match。

Decision candidates：

| User intent | Candidate A | Candidate B | Preferred documentation default |
|---|---|---|---|
| delete source | cascade all result nodes | detach all results as independent assets | A for V0；results lack stable asset/version identity |
| delete one result | remove one result/ref/edge；source remains complete while any results remain | block and require reset-all | A for V0 data repair；source fidelity still requires fixture |
| delete final remaining result | source becomes `ready` when source snapshot exists, otherwise `empty`；`resultNodeIds=[]` | delete source too | first option；least destructive and re-authorable |
| reset results | keep source；delete all results/edges；reset status | delete entire aggregate | first option as future named command |

If result categories or expected partitions become versioned business data, the simple "any remaining -> complete" rule must be replaced by partial/result-state semantics from [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)。

### 9.4 Long-video process aggregate

Current V0 is a fixed local visualization：3 material + 3 shot + 4 candidate + 1 assembly + 1 final nodes and 22 declared edges。

| Situation | Preferred V0 policy | Status |
|---|---|---|
| delete any process member | expand to whole same-process cohort after confirmation-capable command | `PROPOSED_CLONE_DEFAULT` |
| delete process source | delete all dependent V0 process cohorts；then delete source | `PROPOSED_CLONE_DEFAULT` |
| delete one internal process edge | block；no V0 stage-detach recipe | `REQUIRED_CORRECTNESS / PRODUCT_DECISION_REQUIRED` |
| delete complete process | delete cohort + all cohort incident edges；preserve source | future named command |
| partial stage/result cleanup | unsupported until process/run/result schema exists | `SOURCE_PRODUCT_DECISION_REQUIRED` |

Whole-cohort cascade is preferred because every node is `pending`, no member has stable run/result identity, and a partial graph would falsely imply executable recovery. It is not claimed as LibTV source behavior。

### 9.5 External provenance and Director

- deleting a rotate/mirror source does not automatically delete a renderable copied result；the relation becomes unresolved provenance, not owned graph integrity；
- deleting a `script-execution` shell does not prove the independent global Director workspace was deleted；
- deleting a Director capture/export target does not delete Director scene、camera or capture history by default；
- deleting a Director shell while exported targets remain requires explicit provenance detachment or source/product policy；
- graph undo cannot restore a separately destroyed Director workspace, so workspace deletion must never be hidden inside graph node delete。

### 9.6 Canvas document deletion

`removeCanvas` remains a project-lifecycle command：

- it is not part of graph undo；
- at least one canvas remains in current clone；
- deleting active canvas chooses an active fallback and clears graph selection；
- every node-bound UI owner for that canvas must close or explicitly detach；
- its graph history is discarded；
- resource cleanup is emitted to a future owner, not inferred from URLs；
- source Open Canvas creates an empty canvas after deleting the final document, but clone's "refuse final deletion" behavior remains a separate product decision；canvas registry/fallback/history/UI/async/resource 的完整删除边界见 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。

## 10. Selection, Overlay And Focus Repair

### 10.1 Current UI owner paths

| Surface | Owner identity | Current behavior after graph delete | Required future result |
|---|---|---|---|
| node toolbar/bottom editor | React Flow selected node | unmounts when selection clears | no stale surface |
| image annotate | `uiStore.imageAnnotate.nodeId` | route effect closes on selection mismatch | explicit planner invalidation still preferred |
| image element edit | `uiStore.imageElementEdit.nodeId` | route effect closes on selection mismatch | explicit planner invalidation still preferred |
| image preview | `uiStore.imagePreview.nodeId` + snapshot fields | may remain after graph owner deletion | close, or mark as detached snapshot by contract |
| Director desk | `uiStore.activeDirectorNodeId` | keyboard delete is guarded while open；other lifecycle paths are separate | owner delete/canvas delete must close before graph disappearance |
| quick menus/dropdowns | component/store state | mostly close by click/Escape, not delete result | close when anchor/owner is removed |

UI invalidation is session state and does not enter graph history. The delete planner may report invalidations, but route/UI orchestration owns applying them. If graph commit succeeds and UI cleanup fails, the UI must reconcile from current graph on the next render; it must not roll back graph through a second unrelated history step。

### 10.2 Keyboard boundary

Delete/Backspace must continue to skip inputs、textareas and contenteditable owners. Active authoring surfaces may consume Delete for region/mark/editor-local objects；canvas delete must not steal the event. The exact priority is：

```text
focused editor-local delete
  -> modal/Director ownership guard
  -> graph selection delete
  -> no-op
```

## 11. Media And Resource Lifetime

| Locator | Graph node deletion | What must not be inferred |
|---|---|---|
| repo `/...` | remove graph reference only | deployment asset file is not deleted |
| `https:` | remove graph reference only | remote object/account asset is not deleted |
| `data:` | string becomes unreachable when graph/history no longer references it | no external revoke；history may still retain bytes until stack is gone |
| `blob:` | remove graph reference；report owner cleanup diagnostic | do not call `URL.revokeObjectURL` unless an explicit lease owner proves exclusive ownership |
| future stable asset ID | detach graph reference；resource policy delegated | graph deletion is not backend asset deletion by default |

Undo complicates disposal：a node removed from the current graph may still exist in `history.past`. Immediate resource destruction would make undo restore an invalid locator. Future resource ownership therefore needs graph/history reachability or reference counting；it is `DEFERRED_BACKEND_SCOPE` for this prototype。

## 12. Result And Reason Taxonomy

```ts
type LibTVDeletePlanResult =
  | { status: "ready"; plan: LibTVDeletePlan }
  | { status: "reject"; reason: LibTVDeleteRejectReason }
  | { status: "unknown"; reason: LibTVDeleteUnknownReason };
```

### 12.1 Reject reasons

| Reason | Meaning |
|---|---|
| `DELETE_TARGET_NOT_FOUND` | requested node/edge/aggregate does not exist |
| `INVALID_DELETE_COMMAND` | command fields or combinations are invalid |
| `UNREGISTERED_NODE_DATA_RELATION` | surviving identity-bearing data has no registry rule |
| `DANGLING_OWNED_NODE_REFERENCE` | accepted draft would leave required node ref missing |
| `DANGLING_OWNED_EDGE_REFERENCE` | accepted draft would leave required edge ref missing |
| `SHOT_BREAKDOWN_REFERENCE_MISMATCH` | current or planned reciprocal sets disagree |
| `PARTIAL_LONG_VIDEO_PROCESS_AGGREGATE` | planned V0 graph leaves partial cohort |
| `DELETE_PLAN_INTEGRITY_FAILURE` | post-plan graph violates a canonical invariant |

### 12.2 Unknown reasons

| Reason | Meaning |
|---|---|
| `DERIVED_SOURCE_DELETE_POLICY_REQUIRED` | pending/result target cascade vs detach is unresolved |
| `OWNED_EDGE_DELETE_POLICY_REQUIRED` | edge has dependent metadata without a detach recipe |
| `SHOT_RESULT_DELETE_POLICY_REQUIRED` | user-visible single-result semantics need source/product confirmation |
| `PROCESS_DELETE_POLICY_REQUIRED` | aggregate lifecycle is not accepted for this schema version |
| `DIRECTOR_WORKSPACE_DELETE_POLICY_REQUIRED` | graph shell and workspace lifetimes would be conflated |
| `ACTIVE_RUN_DELETE_POLICY_REQUIRED` | a real run/task exists and cancel/retain behavior is undefined |
| `MEDIA_RESOURCE_OWNER_REQUIRED` | operation asks to destroy bytes/resource without an owner contract |

Unknown and reject are both zero-mutation. UI copy may explain an unknown state, but must not convert it into a partial delete。

## 13. Decision Queue

| ID | Question | Current evidence | Recommended next state |
|---|---|---|---|
| `LIBTV-DEL-DQ-001` | source delete cascades pending derived target or keeps it unavailable? | clone has pending placeholders；no result/run identity | source fixture；until then block relation-unsafe delete |
| `LIBTV-DEL-DQ-002` | completed frame/Director result can detach as provenance? | data/media snapshot exists；V0 has no unresolved marker | design dataVersion migration before runtime |
| `LIBTV-DEL-DQ-003` | single shot result deletion is supported? | source result UI evidence asks this explicitly；runtime generic delete corrupts refs | disposable source result fixture |
| `LIBTV-DEL-DQ-004` | process member delete means stage cleanup or whole process delete? | current 12/22 is clone-only pending graph | prefer whole-cohort V0；confirm source process UX |
| `LIBTV-DEL-DQ-005` | manual deletion of semantic edge clears target feature? | continuation has one exact clear contract；others do not | only continuation accepted；block others |
| `LIBTV-DEL-DQ-006` | deleting Director shell deletes workspace? | workspace is global separate store | never imply workspace delete without document model |
| `LIBTV-DEL-DQ-007` | deleting final canvas refuses or creates empty fallback? | clone refuses；Open Canvas creates empty | keep separate product decision |
| `LIBTV-DEL-DQ-008` | graph delete should cancel a real run? | backend absent；process matrix separates run/result/source lifecycle | defer until run ownership contract |

Priority：`DQ-001/003/004/005` directly affect ordinary canvas correctness；`DQ-002/006` affect provenance/Director fidelity；`DQ-007/008` are project/backend scope。

## 14. Local Fixture Contract

### 14.1 Fixture identity

`LIBTV-FIX-LOCAL-GRAPH-DELETE-01`

Status：`REQUIRED_DISPOSABLE / DESIGN_SPEC_COMPLETE / RUNTIME_MISSING / CODING_AUTH_REQUIRED`

Substrate：fresh Page + deterministic graph constructor after explicit authorization. It may reuse node data corpus from [`LIBTV-FIX-LOCAL-NODE-DATA-01`](components/LibTVNodeDataIdentity.contract.md#12-fixture-contract), but deletion assertions have their own reset boundary。

### 14.2 Required scenes

| Scene | Graph shape | Command | Required result |
|---|---|---|---|
| `DELETE-PLAIN-01` | A -> B -> C | delete B | B + incident edges gone；A/C remain；1 step |
| `DELETE-GROUP-01` | group G + child C + external edge | delete G | G/C + touching edges gone；undo restores parent relation |
| `DELETE-EDGE-01` | selected ordinary edge only | delete selection | edge gone；nodes remain；selection valid |
| `DELETE-CONTINUATION-01` | source -> target + continuation edgeId | clear relation | target remains；metadata/edge gone；undo restores both |
| `DELETE-OWNED-EDGE-01` | derived target with registered edgeId | generic edge delete | unknown/zero mutation until recipe chosen |
| `DELETE-DERIVED-SOURCE-01` | source + pending target | delete source | policy result stable；never stale metadata |
| `DELETE-SHOT-SOURCE-01` | source + five results + reciprocal refs | delete source | policy cascade or accepted detach is atomic |
| `DELETE-SHOT-RESULT-01` | source + multiple results | delete one result | reciprocal source patch/status exact |
| `DELETE-PROCESS-01` | complete 12/22 cohort | delete one member/process command | whole cohort policy or stable unknown；never partial |
| `DELETE-PROCESS-BROKEN-01` | intentionally incomplete cohort | any process delete | reject before mutation with stable reason |
| `DELETE-OVERLAY-01` | selected image + annotate/preview owner | delete node | graph accepted；owner invalidation exact；no floating orphan |
| `DELETE-CANVAS-01` | two canvases + independent histories | delete active canvas | fallback/history/overlay boundary exact；other canvas unchanged |
| `DELETE-MEDIA-01` | repo/https/data/blob nodes | delete + undo | no accidental remote/repo deletion；undo locator behavior explicit |

### 14.3 Reset and isolation

- each browser scene uses a fresh Page；
- pure planner scenes use frozen input and compare zero mutation on reject/unknown；
- browser fixture does not call remote provider、upload、save、asset delete or URL cleanup APIs；
- source-site destructive verification requires a separately accepted disposable project；
- historical Batch fixtures remain unchanged until replacement protocol exit conditions are met。

## 15. `LIBTV-VR-013` Replacement Design

### 15.1 Pure suite

Required assertions：

1. descendant closure and stable ordering；
2. selected node + selected edge dedupe；
3. inverse index uses registered paths only；
4. owned node/edge refs repair or block；
5. shot reciprocal source/result sets；
6. complete/partial process cohort；
7. selection after plan；
8. reason precedence and zero mutation；
9. media/resource diagnostics；
10. deterministic plan and policy version。

### 15.2 Browser suite

Required assertions：

- Delete/Backspace focus ownership；
- edge scissors and relation-specific clear behavior；
- group descendant cascade；
- selected edge-only delete；
- selection/toolbars/bottom panels disappear coherently；
- annotate/element edit/preview/Director owner cleanup；
- one-step undo/redo graph restoration；
- aggregate reject/unknown leaves no visual or history residue；
- active canvas removal does not corrupt the surviving canvas。

### 15.3 Historical coverage retained

- Batch 3 command history and keyboard deletion；
- Batch 8 group descendant cascade；
- Batch 24 shot graph；
- Batch 26 continuation clear；
- Batch 27-32 derived processing outputs；
- Batch 33 long-video process topology；
- Batch 35/40 Director outputs；
- Batch 48 local Director asset deletion remains a separate Director-store contract。

`LIBTV-VR-013` does not replace source parity evidence. It replaces fragmented clone graph-integrity assertions only after runtime planner、fixture and focused browser verifier are implemented and recorded。

## 16. Source Evidence Acquisition Plan

Destructive source research must not use the shared logged-in research project. An accepted fixture needs：

- disposable project/canvas and explicit cleanup owner；
- known source node、derived pending/result node、shot result and process state；
- authorization for one exact delete action at a time；
- before/after DOM、node/edge count、selection、toolbar/panel、undo/redo and persistence observations；
- network-independent IDs when visible；
- post-cleanup confirmation outside graph history。

Read-only bundle/DOM research may continue without this fixture, but it cannot prove runtime cascade、confirmation、run cancellation or persisted result retention。

Highest-value source scenarios：

1. delete one shot result；
2. delete shot source with existing results；
3. delete one long-video intermediate node/process；
4. delete source of a pending/ready derived result；
5. delete a semantic edge while target panel is visible；
6. undo each accepted deletion and inspect selected overlay restoration。

## 17. Implementation Handoff After Authorization

The smallest safe slices are：

### Slice A: pure impact index

- relation inverse index from the node-data registry；
- structural/incident closure；
- no store integration。

### Slice B: pure planner and reasons

- named commands；
- ready/reject/unknown result；
- deterministic pure fixture corpus。

### Slice C: current-safe structural commands

- selection includes selected edges；
- group/plain node behavior through planner；
- no user-visible aggregate policy change yet。

### Slice D: relation-specific repair

- continuation clear first；
- shot reciprocal patch only after decision；
- pending derived and process policies only after source/product approval。

### Slice E: UI lifecycle

- apply planner-reported invalidations in route/UI owner；
- keep UI cleanup outside graph history；
- verify top/bottom node surfaces disappear without detached overlays。

### Slice F: resource ownership

- deferred until history-aware media lease/asset ownership exists；
- no speculative URL revoke or backend delete in earlier slices。

Every slice requires explicit coding authorization, focused verification, `npm run check`, documentation status update, commit and push. Shared WIP must not be stashed、reset、reverted or broadly staged。

## 18. Non-Goals And Maintenance Triggers

This document does not：

- claim source-site delete semantics where no disposable fixture exists；
- implement graph code、tests、confirmation dialog or toast；
- define FrameOS delete behavior；
- define Director internal object/keyframe/path deletion；
- delete provider runs、remote assets or local files；
- make graph history persistent；
- treat Open Canvas's simple incident-edge deletion as sufficient for LibTV。

Update this matrix when any of the following changes：

- runtime node/data registry adds a relation-bearing field；
- a source fixture resolves any `LIBTV-DEL-DQ-*` item；
- process/result schema gains stable run/result/version identity；
- UI store adds or removes a graph node owner；
- media/resource ownership becomes explicit；
- graph delete planner or `LIBTV-VR-013` receives coding authorization；
- Open Canvas submodule revision changes and its deletion model is re-audited。

Related authorities：[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)、[`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)、[`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md) and [`DECISION_REGISTER.md`](../DECISION_REGISTER.md)。
