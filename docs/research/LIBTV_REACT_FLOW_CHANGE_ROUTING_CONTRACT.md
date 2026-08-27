# LibTV React Flow Change Routing Contract

> Scope: 普通 LibTV 画布的 React Flow `NodeChange` / `EdgeChange` 入口、transport whitelist、选择权威、历史边界、运行时字段净化、混合批次拒绝策略，以及 Open Canvas 固定版本对这一边界的启发。
>
> Status: `STATIC_AUDIT_COMPLETE` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_PARTIAL`。本文只记录研究与实施约束，不授权修改 `src/`、测试、Open Canvas submodule、FrameOS 或共享源站 graph。
>
> Clone baseline: `bfdc918`（2026-08-27）。
>
> Open Canvas baseline: `cf3a906bb8c35bb940d3267497e7f394b8f42582`。
>
> Shared framework baseline: `@xyflow/react@12.11.1` / `@xyflow/system@0.0.78`。

## 1. Why This Contract Exists

React Flow 的 `onNodesChange` / `onEdgesChange` 看起来像普通受控组件回调，实际上位于三种不同权威的交界处：

1. **运行时展示状态**：选择、拖动中、测量中；
2. **低风险几何传输**：已存在节点的位置和测量尺寸；
3. **语义图变更**：增加、删除、替换节点或边，以及重连。

这三类状态不能共享一个“把 changes 全部交给 `apply*Changes`，再整数组写回”的策略。原因不是 React Flow 的 reducer 有缺陷，而是 reducer 只负责执行框架 delta，不知道 LibTV 的：

- node type、Handle 和连接策略；
- 删除引用修复和 aggregate 完整性；
- history command 边界；
- selection、document、copy、runtime 字段的不同 owner；
- async run、资源、父子节点和 node-data 引用；
- 当前 store snapshot 与 React render closure 的时序差异。

当前 clone 已经把普通 `onConnect` 路由到结构连接 validator，也把键盘删除路由到命名删除命令；但 `onNodesChange` 和 `onEdgesChange` 仍然接受框架 union 中的所有 variant。这会留下旁路：未来任何 React Flow 功能、内部行为或错误调用只要发出 `add/remove/replace`，就能绕过命名 graph command。

本文给出该入口的正式答案：

```text
React Flow callback
  -> parse and classify the entire batch
  -> reject or reroute semantic variants before any side effect
  -> route selection to selection owner
  -> apply only whitelisted transport variants to current store snapshot
  -> sanitize runtime fields at every graph/document/history/copy boundary
```

本文是 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md) 中 T0/T1 入口的细化合同。它不替代 connection、delete、document、copy 或 node-data 合同。

## 2. Evidence And Claim Boundary

### 2.1 `FRAMEWORK_FACT`

来自两个项目锁定的同一 React Flow 版本及其本地类型/实现：

- clone [`package-lock.json`](../../package-lock.json)；
- Open Canvas [`package-lock.json`](../../research/upstream/open-canvas/package-lock.json)；
- clone `node_modules/@xyflow/system/dist/esm/types/changes.d.ts`；
- clone `node_modules/@xyflow/react/dist/esm/index.js`。

这些事实可用于精确说明 union variant 和 `applyChanges` 行为，不代表应用层应该接受所有 variant。

### 2.2 `OPEN_CANVAS_FACT`

来自固定 submodule 的：

- [`shared/stores/canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts)；
- [`shared/lib/canvas/validation.ts`](../../research/upstream/open-canvas/shared/lib/canvas/validation.ts)；
- [`shared/blocks/canvas/canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)。

### 2.3 `CLONE_FACT`

来自 clone baseline 的：

- [`src/app/page.tsx`](../../src/app/page.tsx)；
- [`src/store/canvasStore.ts`](../../src/store/canvasStore.ts)；
- [`src/store/uiStore.ts`](../../src/store/uiStore.ts)；
- [`src/lib/libtvGraphConnection.ts`](../../src/lib/libtvGraphConnection.ts)。

### 2.4 `DECISION`

本文定义的 trust tier、batch plan、allowlist、结果码、fixture 和实施切片是 clone-only correctness design。它们不是 LibTV 源站事实，也不自动授权编码。

### 2.5 Explicit exclusions

- 不把 Open Canvas 的 node type、Handle、保存或 conflict 语义移植到 LibTV；
- 不把 React Flow 的 reducer 行为描述成 LibTV 业务规则；
- 不修改独立的 FrameOS route/store；
- 不推断源站是否使用 React Flow 或相同内部 union；
- 不在共享源站执行删除、重连、粘贴或保存实验；
- 不为尚未授权的自由缩放、协作或持久化功能提前编码。

## 3. Exact React Flow 12.11.1 Change Taxonomy

### 3.1 `NodeChange`

| Variant | Required identity | Payload | Framework intent | LibTV tier |
|---|---|---|---|---|
| `select` | `id` | `selected` | runtime selection | `T0_SELECTION` |
| `position` | `id` | `position?`, `positionAbsolute?`, `dragging?` | node move/drag frame | `T1_TRANSPORT` with strict fields |
| `dimensions` | `id` | `dimensions?`, `resizing?`, `setAttributes?` | measured/resized dimensions | `T1_TRANSPORT` only for measurement |
| `remove` | `id` | none | remove an element | `T2_SEMANTIC_COMMAND` |
| `add` | item/index | complete node item | insert an element | `T2_SEMANTIC_COMMAND` |
| `replace` | `id` + item | complete replacement | replace an element | `T3_DOCUMENT_OR_INTERNAL` |

Important details:

- `positionAbsolute` exists in the type but the installed `applyChange` position branch does not write it to the node object;
- `dimensions` without `setAttributes` updates measured runtime dimensions;
- `dimensions` with `setAttributes` may write width/height attributes and therefore becomes an explicit user layout mutation, not passive measurement;
- `add/remove/replace` can change graph identity and must never be treated as harmless framework transport.

### 3.2 `EdgeChange`

| Variant | Required identity | Payload | Framework intent | LibTV tier |
|---|---|---|---|---|
| `select` | `id` | `selected` | runtime selection | `T0_SELECTION` |
| `remove` | `id` | none | remove an edge | `T2_SEMANTIC_COMMAND` |
| `add` | item/index | complete edge item | insert an edge | `T2_SEMANTIC_COMMAND` |
| `replace` | `id` + item | complete replacement | replace an edge | `T3_DOCUMENT_OR_INTERNAL` |

There is no persistent `T1_TRANSPORT` `EdgeChange` variant in this version. Edge selection is T0; every non-selection edge change is semantic.

### 3.3 Reconnect is not an `EdgeChange`

React Flow exposes reconnection through separate callbacks/helpers such as `onReconnect` and `reconnectEdge`. It is not a fifth `EdgeChange` variant. LibTV must model reconnect/retarget as a named connection replacement transaction:

```text
validate old edge exists
  -> normalize proposed endpoints/handles
  -> validate graph with old edge removed and candidate inserted
  -> atomically replace edge
  -> repair edge-owned references if needed
  -> record exactly one history command
```

Routing reconnect through generic edge replacement would bypass connection policy and failure diagnostics.

## 4. What `applyChanges` Actually Guarantees

The reducer is deterministic, but its guarantees are narrower than a domain command.

### 4.1 Grouping and precedence

The installed implementation:

1. groups ordinary changes by element ID;
2. holds `add` changes separately and applies them after existing elements;
3. lets `remove` or `replace` override earlier queued ordinary changes for the same ID;
4. lets a later `replace` replace an earlier `replace` for the same ID;
5. may make `remove` plus later `add` of the same ID behave like replacement;
6. preserves an optional add index when inserting the new item.

This means filtering a mixed batch after the fact is not equivalent to classifying it before reducer execution. Variant order and same-ID grouping are observable.

### 4.2 Unknown variants are not an application-level reject

The internal `applyChange` switch has no application diagnostic contract. An unrecognized change can result in a shallow-cloned element with no intended mutation instead of an explicit failure. Therefore:

- TypeScript exhaustiveness is necessary but not sufficient at runtime;
- an app adapter must return or log a stable `UNSUPPORTED_CHANGE_VARIANT` result;
- “the reducer did nothing” is not proof that the batch was valid.

### 4.3 The reducer does not know LibTV invariants

`applyNodeChanges` and `applyEdgeChanges` do not validate:

- endpoint/Handle compatibility;
- duplicate semantic edges;
- DAG/cycle policy;
- parent/child closure;
- data-owned node/edge references;
- aggregate membership;
- resource and async-run ownership;
- history command boundaries;
- portable document fields.

They are appropriate only after an application-owned classifier has proved that the batch contains transport-only variants.

## 5. Open Canvas Fixed-Version Audit

### 5.1 Positive patterns

Open Canvas gives its store callbacks functional access to current Zustand state. Its `onNodesChange` / `onEdgesChange` do not derive the reducer base from a React render closure. This avoids one class of stale-array overwrite.

It also:

- blocks persistent graph mutations while a revision conflict is active;
- distinguishes selection-only changes from changes that mark the document dirty;
- serializes runtime React Flow state into a narrower graph document;
- validates the complete graph before save and again at the API boundary.

These are valuable methods: current snapshot, authority state, serialization projection and independent durable validation.

### 5.2 Gaps that must not be copied

Open Canvas sends all incoming `NodeChange` / `EdgeChange` variants to the generic reducers. Its persistent classifier is effectively “anything other than `select`”. Consequently:

- framework `add/remove/replace` are not routed through separate domain commands;
- position, measurement and semantic identity changes share one dirty classification;
- invalid runtime graph state may exist until save-time full validation rejects it;
- save validation protects durability, not every interactive ingress;
- `updateEdgeTargetHandle` dedupes the new semantic edge but does not rerun the complete compatibility/cycle policy.

The adoption rule is therefore:

> Borrow Open Canvas's current-snapshot store ownership and layered document validation. Do not copy its generic acceptance of every React Flow change variant.

### 5.3 Why the comparison is unusually strong

Both projects lock `@xyflow/react@12.11.1`. The observed difference is not a framework-version mismatch. It is an application routing decision made above the same reducer semantics.

## 6. Current LibTV Clone Audit

### 6.1 `onNodesChange`

The route currently:

1. splits `select` changes from all others;
2. applies selection against projected `flowNodes`, then calls `selectNodes`;
3. applies every non-selection variant through `applyNodeChanges`;
4. writes the resulting whole node array with `setStoreNodes`;
5. strips `selected` before storing semantic nodes.

Useful existing behavior:

- selection is projected from `selectedNodeIds`, not intended as portable node data;
- drag frames update position without producing one history entry per frame;
- drag stop records one history snapshot when the final position changed;
- node `selected` is stripped before graph storage.

Uncovered behavior:

- `remove/add/replace` are accepted even though they are semantic variants;
- `dimensions` with `setAttributes` is not separated from passive measurement;
- mixed selection + semantic batches can mutate selection before graph rejection/rerouting exists;
- the reducer base is not consistently defined as an atomic current-store snapshot;
- measured/dragging/resizing fields can enter the node array and need boundary sanitation;
- missing IDs and malformed numeric payloads have no stable adapter result.

### 6.2 `onEdgesChange`

The route currently sends every edge change through `applyEdgeChanges(changes, edges)` and writes the whole result with `setStoreEdges`.

This has four consequences:

1. `add` can bypass `onConnect -> addEdge -> validateLibtvGraphConnection`;
2. `remove` can bypass named delete/reference-repair behavior;
3. `replace` can bypass both connection and delete policy;
4. selection is stored on the semantic edge object instead of a declared runtime selection owner.

The callback also uses the rendered `edges` array as reducer base. If a prior graph command updates the store and an edge change arrives before the route rerenders, whole-array replacement can overwrite the newer state. This is an evidence-backed race hypothesis, not a recorded runtime reproduction; a focused fixture must prove or falsify it.

### 6.3 Current user-facing delete path is already named

The route disables React Flow's default deletion key with `deleteKeyCode={[]}`. Keyboard deletion uses clone-owned handlers, and the edge scissors action uses `removeEdge`. Therefore generic framework `remove` is not required for the currently recorded delete workflow.

This makes a conservative future implementation feasible: reject non-selection edge changes at this adapter and reject node `add/remove/replace`, while keeping named deletion behavior intact.

### 6.4 Runtime field leakage

Node selection is stripped, but React Flow can still add runtime fields such as:

- `measured`;
- `dragging`;
- `resizing`;
- edge `selected`.

These may be valid in the live render state. They are not automatically valid in:

- portable document payloads;
- copy packets;
- semantic equality/hash checks;
- graph history snapshots;
- async run baselines;
- research fixtures that claim durable graph shape.

The document and copy codecs remain responsible for an explicit projection. The transport adapter must not make “React Flow object equals LibTV document node” an implicit contract.

## 7. Authority Tiers

| Tier | Owner | Accepted input | May change identity/relations | History | Failure surface |
|---|---|---|---|---|---|
| `T0_SELECTION` | selection/UI store | node/edge `select` only | no | never | stale selection becomes deterministic no-op |
| `T1_TRANSPORT` | graph runtime adapter | existing-node position and passive measurement only | no | drag frames/measurement none; drag stop one | stable adapter result/diagnostic |
| `T2_SEMANTIC_COMMAND` | named graph command | create/delete/connect/reconnect/group/copy/resize | yes, under command rules | declared per command | typed command result |
| `T3_DOCUMENT_OR_INTERNAL` | codec/history/server-run authority | replace/restore/import/hydrate/server-owned patch | potentially full graph | boundary-specific | codec/revision/invariant result |

Rules:

1. A lower tier may not execute a higher-tier mutation merely because the framework union contains it.
2. A T2/T3 operation must not be decomposed into T0/T1 partial writes.
3. Selection success must not mask graph rejection in the same incoming batch.
4. A whole-array setter is an internal commit primitive, not a public UI command.

## 8. Normative Routing Matrix

### 8.1 Node changes

| Change | Preconditions | Route | Store effect | History |
|---|---|---|---|---|
| `select` | ID is known or stale | selection owner | update selected IDs only; stale ID no-op | none |
| `position` | existing ID; finite `x/y`; no identity/data/style item | T1 transport planner | update current node position and optional runtime dragging state | none per frame; one at drag stop |
| passive `dimensions` | existing ID; finite nonnegative measured width/height; `setAttributes` absent/false | T1 measurement planner | update runtime measured/resizing fields | none |
| explicit `dimensions` | `setAttributes` requests width/height mutation | named resize/layout command | validate final dimensions and commit semantic layout | exactly one when authorized |
| `remove` | any | named delete command | descendant/edge/reference repair transaction | command-owned |
| `add` | any | named create/copy/import command | validate node type/data/ID and draft graph | command-owned |
| `replace` | any | T3 restore/import/internal command | validate identity, ownership and full draft | boundary-owned |
| unknown | any | reject adapter batch | none | none |

### 8.2 Edge changes

| Change | Route | Store effect | History |
|---|---|---|---|
| `select` | edge selection owner | update selected edge ID(s) or runtime projection only | none |
| `remove` | named edge/delete-selection command | repair edge-owned references and remove edge atomically | command-owned |
| `add` | named connection command | normalize and validate connection before append | command-owned |
| `replace` | named reconnect or T3 document command | validate remove-old/add-new draft atomically | command/boundary-owned |
| unknown | reject adapter batch | none | none |

There is no allowlisted non-selection T1 edge change.

## 9. Whole-Batch Planning Contract

The adapter must classify the entire callback payload before mutating any owner.

### 9.1 Conceptual plan

```ts
type ChangeBatchPlan =
  | {
      kind: 'accept';
      selection: SelectionDelta[];
      transport: NodeTransportDelta[];
    }
  | {
      kind: 'reroute';
      command: SemanticCommandProposal;
    }
  | {
      kind: 'reject';
      code: ChangeRoutingCode;
      changeIndex: number;
      elementId?: string;
    };
```

This is a design shape, not prescribed source code. The implementation may use another representation if it preserves the invariants below.

### 9.2 Required algorithm

1. Read one current store snapshot for classification and commit.
2. Parse every change with an exhaustive variant switch.
3. Validate IDs, numeric payloads and allowed fields.
4. Detect whether any T2/T3 or unknown variant is present.
5. If semantic intent can be mapped to exactly one named command, reroute the whole semantic operation.
6. Otherwise reject before selection or transport mutation.
7. For a valid T0/T1 batch, compute selection and graph results from the same starting snapshot.
8. Commit each owner in a defined order without rereading a stale render closure.
9. Emit one stable result for diagnostics/fixtures.

### 9.3 Why partial filtering is forbidden

The adapter must not do this:

```text
apply select now
  -> discard remove/replace
  -> apply remaining position changes
```

That would turn one framework batch into partial success without a declared transaction model. It would also ignore same-ID reducer precedence. A batch containing an unsupported semantic variant is rejected or wholly rerouted before any effect.

### 9.4 Mixed valid T0/T1 batches

A batch containing only selection plus valid position/measurement changes may be accepted as one plan. Selection and graph transport still have separate owners, but both results are derived from the same snapshot and the commit order is deterministic.

## 10. Payload And Field Allowlist

### 10.1 Position

A T1 position change may carry only:

- existing node ID;
- finite `position.x` and `position.y` when position is present;
- optional boolean `dragging`;
- framework `positionAbsolute` only as ignored/untrusted transport metadata unless a future parent-layout contract explicitly owns it.

It may not:

- create an unknown ID;
- patch `data`, `type`, `parentId`, `extent`, `style`, width or height;
- change child ownership or edge endpoints;
- create a history entry for every drag frame.

### 10.2 Passive dimensions

A passive measurement change may carry:

- existing node ID;
- finite, nonnegative measured width and height when present;
- optional boolean `resizing`;
- no truthy `setAttributes` request.

If product semantics require user-visible node resize, that is a future T2 layout command with explicit minimum/maximum size, parent containment and one history boundary.

### 10.3 Selection

Selection changes may update only the stable selection owner. They must not become semantic graph data merely because React Flow represents `selected` on node/edge objects.

For edges, the implementation must choose and document one owner:

1. preferred: dedicated selected edge ID(s) in UI/selection state;
2. transitional: runtime edge projection with mandatory sanitation at every graph boundary.

An undeclared mixture is not acceptable.

## 11. Current Snapshot And Commit Semantics

### 11.1 Reducer base

Every accepted T1 batch must use the current active-canvas store snapshot, not `nodes` or `edges` captured by the route render that created the callback.

```text
bad:  applyEdgeChanges(changes, renderedEdges) -> setEdges(wholeArray)
good: plan against current active canvas -> atomically commit validated result
```

This rule is shared with the async ingress contract: the authority that decides whether an update is still applicable must observe the current version/current owner, not an earlier closure.

### 11.2 Missing IDs

Framework callbacks can race with named delete/canvas switch. Missing target IDs are therefore expected stale input, not necessarily corruption.

Required behavior:

- selection for missing ID: no-op with stable stale result if observed;
- position/measurement for missing ID: no-op/reject with `STALE_ELEMENT_ID`, but never create;
- mixed batch: deterministic whole-batch policy, recorded by fixture;
- no silent partial resurrection.

### 11.3 Active canvas

The plan and commit must refer to the same active canvas identity. If active canvas changes between observation and commit, the adapter must abort or replan; it must never apply deltas from one canvas to another.

## 12. History Contract

| Interaction | Runtime writes | History units |
|---|---:|---:|
| node selection | one or more selection changes | 0 |
| edge selection | one or more selection changes | 0 |
| drag movement frames | many T1 position updates | 0 during frames |
| drag completion | final position already in store | exactly 1 if semantic position changed |
| passive measurement | framework-dependent updates | 0 |
| future explicit resize | one named T2 command | exactly 1 if dimensions changed |
| create/delete/connect/reconnect | named T2 command | command policy, normally exactly 1 |
| restore/import/hydrate | T3 boundary | boundary policy; never accidental per-element entries |

Drag history must use the pre-drag graph snapshot captured at drag start, not reconstruct an approximation from the final node. No-op drag stop must not create history.

## 13. Stable Result Vocabulary

The adapter/fixture contract should expose stable machine-readable codes. Exact TypeScript names can change, but semantics must not.

| Code | Meaning | Mutation allowed |
|---|---|---|
| `APPLIED_SELECTION` | T0 selection plan committed | selection only |
| `APPLIED_TRANSPORT` | valid T1 position/measurement committed | transport only |
| `APPLIED_MIXED_RUNTIME` | valid T0 + T1 batch committed | selection + transport |
| `STALE_ELEMENT_ID` | target disappeared or belongs to old canvas | none for that deterministic policy |
| `INVALID_NUMERIC_PAYLOAD` | NaN/infinite/invalid dimensions or position | none |
| `SEMANTIC_CHANGE_REQUIRES_COMMAND` | add/remove/replace reached transport adapter | none |
| `ATTRIBUTE_RESIZE_REQUIRES_COMMAND` | dimension change requested semantic width/height | none |
| `UNSUPPORTED_CHANGE_VARIANT` | runtime input not recognized | none |
| `ACTIVE_CANVAS_CHANGED` | plan owner changed before commit | none |
| `REROUTED_TO_COMMAND` | adapter mapped exact semantic intent to a named command | only command-owned mutation |

User-facing notices are not required for ordinary stale runtime events. Diagnostics must be sufficient for verifier assertions and development investigation without flooding production UI.

## 14. Invariants

### `LIBTV-GC-034` — Exhaustive classification

Every `NodeChange` / `EdgeChange` is classified before any owner mutation. Unknown variants cannot fall through to a generic reducer.

### `LIBTV-GC-035` — No semantic transport

Node/edge `add/remove/replace` and reconnect never execute through T1 callbacks.

### `LIBTV-GC-036` — Current-snapshot base

Accepted transport deltas are planned from the current active-canvas store snapshot, never only from a render closure.

### `LIBTV-GC-037` — Whole-batch atomic classification

An unsupported semantic or malformed change prevents earlier selection/position changes in the same callback batch from becoming partial side effects.

### `LIBTV-GC-038` — Selection ownership

Node/edge selection is runtime state. It does not alter portable graph semantics, history equality, copy packets or async graph baselines. Its unified node/edge/primary active-session authority is defined by [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md); this framework contract owns only event classification and projection transport.

### `LIBTV-GC-039` — Measurement is not resize

Passive measured dimensions are T1 runtime transport; width/height attribute mutation is a named T2 layout command.

### `LIBTV-GC-040` — Stable stale behavior

Changes targeting a removed node/edge or old active canvas never recreate the element or overwrite another canvas.

### `LIBTV-GC-041` — One drag history unit

Drag frames create no history. A changed drag stop creates exactly one entry from the pre-drag snapshot.

### `LIBTV-GC-042` — Edge non-selection is semantic

No non-selection `EdgeChange` is allowlisted as T1 transport in React Flow 12.11.1.

### `LIBTV-GC-043` — Boundary sanitation

`selected`, `measured`, `dragging`, `resizing` and other framework-runtime fields cannot leak into portable document/copy/semantic-hash contracts unless explicitly versioned there.

## 15. Focused Fixture Catalog

Fixture ID: `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01`.

### 15.1 Accepted runtime cases

1. select an existing node; graph payload/history unchanged;
2. select an edge; semantic edge projection/history unchanged;
3. move one node with finite coordinates; only position changes;
4. issue multiple drag frames; history count remains unchanged;
5. stop a changed drag; exactly one history entry points to pre-drag snapshot;
6. stop a no-op drag; no history entry;
7. apply passive measured dimensions; no history/document semantic change;
8. accept one valid mixed select + position batch from one store snapshot.

### 15.2 Rejected/rerouted cases

9. node `add` reaches adapter; no graph/selection/history mutation;
10. node `remove` reaches adapter; named delete command is required;
11. node `replace` reaches adapter; T3 authority is required;
12. dimensions with `setAttributes`; named resize command is required;
13. edge `add/remove/replace`; no generic reducer mutation;
14. unknown variant; stable unsupported result;
15. NaN/infinite position or dimension; no partial mutation;
16. unsupported semantic change preceded by selection in the same batch; selection remains unchanged.

### 15.3 Concurrency and stale cases

17. store gains an edge after render but before edge selection callback; selection cannot drop the new edge;
18. node is deleted before a queued position frame arrives; node is not resurrected;
19. active canvas switches before commit; old-canvas delta cannot affect new canvas;
20. same-ID remove/add/position mixed batch; adapter rejects before framework precedence can create accidental replacement.

### 15.4 Boundary sanitation cases

21. history snapshot equality ignores runtime selection/measurement fields as specified;
22. duplicate/copy packet excludes framework-only fields;
23. document serialization excludes framework-only fields;
24. undo/redo does not restore a stale runtime edge selection as semantic graph content.

## 16. Verification Replacement

Verifier ID: `LIBTV-VR-016`.

| Layer | Required assertion |
|---|---|
| static route check | callbacks do not pass unclassified union directly to generic reducers |
| static ownership check | edge selection owner/sanitation boundary is explicit |
| unit/domain check | classifier exhaustively maps exact 12.11.1 variants and rejects unknown input |
| store integration | current snapshot, active canvas identity and no partial mixed-batch writes |
| history check | many drag frames + one stop yield exactly one entry |
| graph command check | add/remove/replace/reconnect still use named validators/repair |
| document/copy check | runtime fields are absent from portable outputs |
| Playwright | real drag, select, delete and connect workflows retain observed UX |

Recorded runtime evidence remains necessary because static checks cannot prove callback ordering or React Flow's emitted batch shapes under actual interaction.

## 17. Decision Queue

| ID | Decision | Recommended default | Evidence needed before change |
|---|---|---|---|
| `LIBTV-RFC-DQ-001` | edge selection owner | resolved：one validated active-session node/edge/primary authority；React Flow field is projection | [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)；runtime consumer migration still required |
| `LIBTV-RFC-DQ-002` | missing-ID position result | deterministic stale no-op with diagnostic | real queued drag/delete fixture |
| `LIBTV-RFC-DQ-003` | mixed valid T0/T1 commit primitive | one planned store action or equivalent atomic owner sequence | store subscriber/render behavior |
| `LIBTV-RFC-DQ-004` | runtime measured fields in semantic history | exclude from semantic equality; retain only where render needs them | undo/render regression fixture |
| `LIBTV-RFC-DQ-005` | explicit node resize | keep unsupported until source evidence/product authorization | LibTV source interaction evidence |
| `LIBTV-RFC-DQ-006` | semantic framework variant handling | reject at adapter first; reroute only when intent is unambiguous | emitted callbacks for enabled features |
| `LIBTV-RFC-DQ-007` | diagnostic channel | dev/test structured result, no routine user toast | expected stale-event frequency |
| `LIBTV-RFC-DQ-008` | active-canvas version token | canvas ID plus graph revision/epoch if needed | implementation race fixture |

These decisions are implementation-facing, not blockers for this research contract. The recommended defaults are conservative and compatible with current recorded behavior.

## 18. Implementation Slices After Authorization

### Slice A — Pure classifier and result vocabulary

- model exact installed variants with exhaustive checks;
- validate finite positions/dimensions and existing IDs;
- classify whole batches before side effects;
- add focused unit cases from fixture 01.

### Slice B — Current-snapshot store routing

- move T1 planning/commit behind a store-owned action or equivalent current-state primitive;
- stop using render-closure arrays as whole-array replacement authority;
- assert active canvas identity at commit.

### Slice C — Selection ownership

- project node/edge flags from the validated active-session selection authority;
- derive one primary selection under the formal selection/context contract;
- sanitize graph/history/copy/document boundaries.

### Slice D — Semantic rejection/rerouting

- reject node add/remove/replace and all non-selection edge variants at transport callbacks;
- preserve named create/delete/connect commands;
- add reconnect only as a dedicated replacement transaction if source/product evidence requires it.

### Slice E — Verification and evidence

- implement `LIBTV-VR-016`;
- record actual callback batches for drag/select/delete/connect;
- verify desktop/mobile overlays remain anchored after selection state routing;
- close decision queue items only with recorded evidence.

Each slice should be a separately reviewable commit. No slice should combine unrelated Director, FrameOS, visual styling or backend work.

## 19. Open Canvas Adoption Verdict

### Adopt

- functional current-store snapshot for framework callbacks;
- separation of selection-only and persistent changes;
- runtime-to-document projection;
- independent full graph validation at durable boundaries;
- conflict state as a mutation authority gate when persistence eventually exists.

### Adapt

- refine “non-select is persistent” into explicit T1/T2/T3 routing;
- retain passive measurement without making framework runtime fields portable;
- use save validation as defense in depth, not the first semantic guard;
- turn Handle retarget into complete connection replacement validation.

### Reject

- generic acceptance of every `NodeChange` / `EdgeChange` variant;
- whole-array writeback based on a render closure;
- edge selection embedded indefinitely in semantic document edges;
- silent partial filtering of malformed/mixed batches;
- treating reducer success as domain validity.

## 20. Completion Criteria

This contract is implemented only when all of the following are true:

- exact framework variants are exhaustively classified before mutation;
- selection and transport changes have declared owners;
- node add/remove/replace and edge add/remove/replace cannot bypass named commands;
- accepted transport uses current active-canvas state;
- mixed invalid batches have no partial side effects;
- drag and measurement history rules are recorded and verified;
- document/copy/history boundaries sanitize runtime fields;
- `LIBTV-FIX-LOCAL-REACT-FLOW-CHANGES-01` and `LIBTV-VR-016` pass;
- Playwright evidence confirms current LibTV clone interaction/overlay UX did not regress.

Until then, the accurate project status is:

> The clone has useful selection projection, named delete/connect paths and drag-stop history, but React Flow change adapters remain a partially trusted ingress. Open Canvas provides strong current-state and durable-validation patterns, while its generic change acceptance is a negative example to refine rather than reproduce.
