# LibTV Graph Connection Validation Contract

> Scope: LibTV 普通 React Flow 画布的连接提议、方向归一化、校验结果、提交原子性、fixture 和 verifier 设计。
>
> Status: `STRUCTURAL_SLICE_RECORDED_PASS` / `DOMAIN_AND_ENTRY_POINT_OPEN` / `SOURCE_EXCEPTION_BLOCKED`。Batch 57 已完成本地结构校验和 React Flow/store 提交边界；本文不授权继续修改 `src/`、verifier 或共享源站 graph。

## 1. Product Boundary

连接不是“从一个圆点拖到另一个圆点后直接追加 edge”。后续 clone 应把它视为一个有明确阶段和失败结果的 graph transaction：

```text
raw gesture / programmatic request
  -> normalize direction and handles
  -> resolve endpoint identities
  -> structural validation
  -> LibTV domain compatibility
  -> allow / allow-with-adjustment / reject / unknown
  -> one accepted transaction or zero mutation
```

本文只覆盖普通 LibTV route。FrameOS 使用独立 route、store、Handle ID 和 selected-state 修正规则，不复用本文的产品兼容矩阵。

## 2. Evidence And Inspiration Boundary

### 2.1 `SOURCE_FACT`

2026-08-27 当前 LibTV production bundle 和 DOM 已静态确认：

- 左侧 `target` 和右侧 `source` Handle 都可能成为手势起点；
- 从 `target` 发起时，`onConnect` 会交换端点并规范化为 `source -> target`；
- ordinary connection path 按 unordered node pair 拒绝同向、反向和仅 Handle 不同的 parallel connection；
- programmatic pair 显式拒绝相同 node ID；普通非 `REFERENCE` source 还会进入 adjacency + DFS cycle guard；
- node action/type、目标容量、model capability 和可选 `switchToModel` 共同决定最终结果；
- validation failure 不调用 source bundle 的 edge submit 分支。

证据入口：[`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](../open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md) 和 [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#10-libtv-par-008-invariant-and-compatibility-design)。

### 2.2 `OPEN_CANVAS_INSPIRATION`

Open Canvas 固定版本可借鉴的是 pure validation、方向规范化、DAG/compatibility 分层和 invalid transaction 测试方法。不能移植它的五类 node、Handle 名称、clipboard payload、provider route、视觉反馈或保存语义。

### 2.3 `CLONE_FACT`

当前 clone：

- Batch 57 新增 pure `normalizeLibTVConnection` / `validateLibTVGraphConnection`，覆盖 endpoint、Handle direction、dangling、unordered duplicate pair、self-loop 和 directed-cycle guard；
- [`page.tsx`](../../../src/app/page.tsx) 的 React Flow 已挂载 `isValidConnection`、`onConnect`、`onConnectStart` 和 `onConnectEnd`；accepted proposal 在生成 edge 前完成校验，rejected proposal 不调用 store commit；
- [`canvasStore.ts`](../../../src/store/canvasStore.ts) 的 `addEdge` 会以 `programmatic` origin 二次调用同一 pure validator，accepted edge 规范化 Handle 并产生一个 history step，rejected edge 返回稳定 reason 且 graph/history 保持不变；
- `LibTVConnectionOrigin` 当前只实现 `react-flow | programmatic`；import、paste、batch、sync、collaboration 和 graph document load 尚未进入统一入口合同；
- 当前 runtime result 只表达 structural `allow | reject`，并以 `domainStatus: "not-evaluated"` 明示 Reference、node action/type、capacity 和 model adjustment 尚未实现；
- node renderers 普遍渲染固定左右 Handle，当前不会根据 node instance/domain capability 统一控制 `isConnectable`；
- `CustomHandle` 是未挂载的 legacy prototype，不能作为未来实现依据；真实 affordance 仍是节点内的 React Flow `<Handle>`。

结构切片的实现与 focused verification 见 [`liblib-canvas-batch57-2026-08-27/`](../liblib-canvas-batch57-2026-08-27/)。该结果只证明 clone-owned local fixture，不证明完整 LibTV parity，也不授权继续重写 store。

## 3. Vocabulary And Identity

下面是 clone 设计词汇，不声称与源站 TypeScript 命名相同。

```ts
type ConnectionOrigin =
  | "react-flow"
  | "programmatic"
  | "import"
  | "batch"
  | "sync";

type ProposedConnection = {
  origin: ConnectionOrigin;
  sourceNodeId: string | null;
  sourceHandleId: string | null;
  targetNodeId: string | null;
  targetHandleId: string | null;
  startedFromHandleType?: "source" | "target";
};

type NormalizedConnection = {
  sourceNodeId: string;
  sourceHandleId: string;
  targetNodeId: string;
  targetHandleId: string;
};
```

Stable identity rules:

1. node ID 是端点身份；label、媒体 URL、DOM 顺序和屏幕坐标不是身份；
2. ordinary edge pair identity 使用规范化后的 node pair；当前 source static guard 不允许用不同 Handle 绕过；
3. Handle ID 仍必须保留在 accepted edge 中，用于可访问性、React Flow routing 和未来多 Handle node；
4. raw gesture 与 normalized connection 必须可区分，避免从 target 发起时把视觉起点误存为 graph direction；
5. edge ID 只在 validation 通过、准备提交时生成；rejected/unknown request 不消耗持久 identity；
6. import/batch/sync 必须声明 origin，不能伪装成用户 gesture 以绕过不同的 diagnostics 或授权边界。

## 4. Direction Normalization

### 4.1 Ordinary gesture

| Raw start | Raw end | Normalized source | Normalized target |
|---|---|---|---|
| source Handle of A | target Handle of B | A/source | B/target |
| target Handle of B | source Handle of A | A/source | B/target |

如果 raw gesture 缺少可识别的另一端，返回 `MISSING_ENDPOINT`，不猜测最近 node，也不创建 pending edge。源站 `onConnectEnd` 的 node-under-pointer fallback 需要 disposable source fixture；当前不纳入 clone 第一 slice。

### 4.2 Programmatic/import/batch/sync

这些入口必须直接提交规范方向，或显式调用同一 normalizer。不能根据 node 的屏幕左右位置推断方向；用户移动节点后 graph 语义不得反转。

## 5. Validation Result Shape

目标结果是 discriminated decision，而不是只有 boolean：

```ts
type ConnectionAdjustment = {
  kind: "switch-target-model";
  modelKey: string;
};

type ConnectionValidationResult =
  | {
      status: "allow";
      connection: NormalizedConnection;
    }
  | {
      status: "allow-with-adjustment";
      connection: NormalizedConnection;
      adjustment: ConnectionAdjustment;
    }
  | {
      status: "reject";
      reason: ConnectionRejectionReason;
      invalidTargetNodeId?: string;
    }
  | {
      status: "unknown";
      reason: ConnectionUnknownReason;
      unresolvedPolicy: string;
    };
```

Design rules:

- `allow` 和 `allow-with-adjustment` 才能进入 edge transaction；
- `reject` 是已定义规则的确定 no-op；
- `unknown` 表示缺少 source/product decision，不等于 allow，也不应被测试改写成 reject；
- model adjustment 是 accepted transaction 的一部分，不能先改 model、后因 edge 失败留下半状态；
- user-facing 文案、toast 和红色 invalid-target style 是 presentation projection，不写进 graph/history；
- reason code 是 clone contract，用于测试和诊断，不冒充源站错误码。

## 6. Stable Reason Taxonomy

### 6.1 Rejection reasons

| Reason | Layer | Meaning | Expected mutation |
|---|---|---|---|
| `MISSING_ENDPOINT` | syntax | source 或 target 缺失 | none |
| `DANGLING_ENDPOINT` | graph | node ID 不在当前 canvas | none |
| `INVALID_HANDLE_DIRECTION` | normalization | raw handles 无法归一化为 source/target | none |
| `DUPLICATE_NODE_PAIR` | graph | 已有同向或反向 node pair，Handle 不构成旁路 | none |
| `SELF_LOOP` | graph | ordinary source 与 target 是同一 node | none |
| `DIRECTED_CYCLE` | graph | 候选 edge 关闭当前普通有向路径 | none |
| `NODE_TYPE_INCOMPATIBLE` | domain | 已有明确 LibTV node/action rule 拒绝 | none |
| `TARGET_CAPACITY_REACHED` | domain | target 的素材/片段/输入上限已满 | none |
| `MODEL_INCOMPATIBLE` | domain | 当前 model 无法接收候选素材且没有合法切换目标 | none |
| `SOURCE_ASSET_NOT_READY` | domain | source 仍是本地 blob/未就绪资源，已确认不能连接到目标 | none |
| `ENDPOINT_LOCKED` | collaboration | source bundle 的协作锁分支 | current clone out of scope; none |

### 6.2 Unknown reasons

| Reason | Why unknown | Stop condition |
|---|---|---|
| `REFERENCE_POLICY_UNCONFIRMED` | source bundle 对 `REFERENCE` source 排除普通 adjacency；交互未验证 | disposable source Reference fixture |
| `ENTRY_POINT_POLICY_UNCONFIRMED` | import/batch/sync 是否使用同一 source validator 未确认 | source/API evidence or explicit clone decision |
| `NODE_ACTION_UNMODELED` | 当前 clone node type/data union 未表达完整 source action matrix | domain schema review in an authorized slice |
| `SOURCE_UI_FEEDBACK_UNCONFIRMED` | invalid target、connection line、toast/tooltip lifecycle 未交互观察 | disposable source graph fixture |

`unknown` 不能被 silent fallback 隐藏。若一个早期授权 slice 只实现 structural rules，domain stage 应明确标记 `not-evaluated`，而不是给所有未建模 node action 返回 `allow` 的 source-parity 结论。

## 7. Validation Pipeline And Precedence

普通连接的稳定 pipeline：

| Order | Stage | Input | Output |
|---:|---|---|---|
| 1 | syntax | raw endpoint presence | `MISSING_ENDPOINT` |
| 2 | normalize | raw endpoints/handles | normalized connection or `INVALID_HANDLE_DIRECTION` |
| 3 | endpoint resolution | active canvas nodes | `DANGLING_ENDPOINT` |
| 4 | collaboration boundary | optional lock state | `ENDPOINT_LOCKED` or not-applicable |
| 5 | unordered pair guard | existing edges | `DUPLICATE_NODE_PAIR` |
| 6 | explicit self guard | normalized pair | `SELF_LOOP` |
| 7 | source-specific type guards | node data/action | `NODE_TYPE_INCOMPATIBLE` / unknown |
| 8 | cycle guard | existing ordinary adjacency + candidate | `DIRECTED_CYCLE` / Reference unknown |
| 9 | capacity/model validation | target state/model inputs | reject, allow or allow-with-adjustment |
| 10 | commit eligibility | final decision | accepted transaction descriptor |

Precedence is observable contract for diagnostics and tests. Example: reverse `B -> A` when `A -> B` already exists returns `DUPLICATE_NODE_PAIR`, even though it also creates a two-node cycle. Self-loop receives the explicit reason even if the same DFS could detect it.

Source bundle only proves allowed/rejected behavior and branch order, not these reason labels. If later source interaction exposes a different user-facing precedence, update evidence and presentation mapping without silently changing graph invariants.

## 8. Transaction Contract

### 8.1 Rejected or unknown

Required final state:

```text
nodes: unchanged
edges: unchanged
selection: unchanged
history past/future: unchanged
viewport: unchanged
node data/model: unchanged
pending connection: cleared
invalid target/feedback: transient and cleared by declared lifecycle
```

Calling `canvasStore.addEdge` and then removing the edge is not equivalent: it can create history, collaboration, analytics or selection residue. Validation must finish before graph mutation.

### 8.2 Allowed

One user connection gesture produces exactly one accepted graph transaction:

- add one normalized edge with stable source/target/Handle fields;
- selection remains unchanged unless later source evidence explicitly requires a shift;
- history gains exactly one pre-command graph snapshot;
- redo reproduces the same logical connection identity; edge ID policy must be declared before implementation;
- connection feedback and pending state are cleared after commit;
- no visual changes to the sourced `DeletableEdge` flow effect or Handle affordance.

### 8.3 Allow with adjustment

If validation returns a model switch:

- target model update and edge creation form one atomic transaction from the user's perspective;
- failure in either part leaves both graph and target data unchanged;
- undo reverts both edge and adjustment in one step;
- the adjustment must be visible before or immediately with commit according to a separate surface contract;
- no real provider request, billing or task is implied.

Atomic model adjustment is a `CLONE_DECISION` inspired by transaction safety. Current source static evidence confirms `switchToModel` exists, but does not fully prove source history semantics.

## 9. Entry-Point Ownership

| Entry | Required use of contract | Current state |
|---|---|---|
| React Flow `onConnect` | normalize, validate, commit accepted descriptor | Batch 57 implemented and recorded |
| React Flow `isValidConnection` | project pure result to connection affordance; must not mutate graph/history | Batch 57 implemented for structural result |
| programmatic connect | same validator and transaction result; explicit equal-ID behavior | `canvasStore.addEdge` revalidates through shared helper |
| derived action direct edge | structural validation at minimum; product-specific transaction remains separate | multiple store actions create edges directly |
| import/paste/batch | validate whole draft before partial write; report per-edge diagnostics | policy not centralized |
| remote sync/collaboration | reject corrupt payload or quarantine with diagnostics; do not apply UI gesture assumptions | current prototype out of scope |

The later implementation should have one pure validation authority. Do not copy duplicate/cycle rules into every node component. The exact file/module and whether `addEdge` accepts only a validated descriptor are implementation decisions for an authorized PLAN, not decisions made by this document.

## 10. Handle And Presentation Contract

- `<Handle>` remains the real draggable affordance; decorative layers stay `pointer-events:none`;
- current source allows both sides to start, so a future clone should not equate `type="target"` with “cannot begin drag” without rechecking React Flow behavior;
- instance-level `isConnectable` may hide impossible paths early, but final validator remains authoritative;
- invalid UI must not resize nodes, shift overlays or block later valid drags;
- `connectionLineStyle` and `DeletableEdge` flow effect remain unchanged in the graph-hardening slice;
- `CustomHandle` and `PlusIndicator` are legacy/no-op artifacts and are not implementation starting points;
- inaccessible disabled state is not acceptable: Handle availability and invalid feedback need an accessible name/state or equivalent keyboard-readable result when implemented.

Exact source invalid color, toast text, cursor, timeout and target highlight remain `SOURCE_UI_FEEDBACK_UNCONFIRMED`.

## 11. Fixture Contract

### 11.1 Fixture identity

`LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` is the deterministic local fixture. Current status: `AVAILABLE_LOCAL / DESIGN_SPEC_COMPLETE / RECORDED_PASS` for Batch 57 structural cases; domain, Reference and source-feedback extensions remain unavailable.

It derives from a fresh `LIBTV-FIX-LOCAL-EMPTY-01` Page and must provide stable aliases for:

| Alias | Minimum role |
|---|---|
| `A_SOURCE` | ordinary source-capable node |
| `B_TARGET` | ordinary target-capable node |
| `C_TARGET` | third node for cycle path |
| `D_INCOMPATIBLE` | node with an explicitly modeled incompatible domain role, only after domain schema exists |

Production node IDs remain normal runtime IDs; aliases belong to fixture/verifier reporting.

### 11.2 Scenario topology

| Scenario | Initial edges | Proposal | Expected decision |
|---|---|---|---|
| valid | none | A -> B | allow |
| target-start normalization | none | drag B target toward A source | normalized A -> B allow |
| duplicate | A -> B | A -> B | `DUPLICATE_NODE_PAIR` |
| reverse pair | A -> B | B -> A | `DUPLICATE_NODE_PAIR` |
| self | none | A -> A | `SELF_LOOP` |
| cycle | A -> B, B -> C | C -> A | `DIRECTED_CYCLE` |
| dangling | A only | A -> missing | `DANGLING_ENDPOINT` in pure/import case |
| different Handle same pair | A -> B | alternate A/B handles | `DUPLICATE_NODE_PAIR` under current source static rule |
| type/capacity/model | declared domain states | modeled proposal | domain result or explicit unknown |
| Reference exception | disposable source only until modeled | Reference proposal | `REFERENCE_POLICY_UNCONFIRMED` |

### 11.3 Setup and reset

Before every scenario:

1. create a fresh Page and select the initial empty canvas;
2. assert `0 nodes / 0 edges`, no selected node and declared viewport;
3. construct only the nodes/edges needed by that scenario through the authorized fixture path;
4. record current graph/history boundary and stable aliases;
5. assert no pending connection or invalid-target state.

After the assertion, discard the Page. Undo, reload or switching away from `canvas-1` is not sufficient teardown.

No fixture code, global store injector or source-site mutation is authorized by this contract.

## 12. Verifier Contract

`LIBTV-VR-009` is split into two layers. Batch 57 recorded the local structural subset in both layers; the bullets that depend on domain, Reference or source feedback remain planned:

### 12.1 Pure contract layer

- normalization from both Handle directions;
- missing/dangling endpoint;
- unordered pair duplicate precedence;
- self-loop and directed cycle;
- reason/result discriminated shape;
- accepted/rejected graph delta and history step count;
- Reference/domain unknown remains explicit.

### 12.2 Focused browser layer

- real `<Handle>` drag from both sides;
- accepted edge uses normalized source/target/Handle fields;
- rejected drag leaves node/edge/selection/history unchanged;
- connection line and invalid feedback clear on end, Escape, new valid drag and selection change as declared;
- pan/zoom and node movement do not change edge direction identity;
- no console/page errors and no edge-flow visual regression;
- old Batch 4-8 graph regressions remain retained, not rewritten to claim current source parity.

Disposable source interaction is a separate evidence run, not part of local `VR-009`.

## 13. Authorized Implementation Slices

These slices are ordered but independently authorized:

### Slice A: Pure Structural Validation

- normalize direction;
- missing/dangling/duplicate/self/cycle result;
- no mutation on reject;
- pure `VR-009` cases.

Status: completed and recorded by Batch 57.

### Slice B: React Flow Boundary

- use the pure result from `isValidConnection` and `onConnect`;
- preserve Handle and edge visuals;
- focused drag lifecycle and one-step history.

Status: completed and recorded by Batch 57 for local structural behavior. Exact source invalid-feedback lifecycle remains open.

### Slice C: Domain Compatibility

- reconcile runtime node data/action vocabulary;
- model target capacity and model adjustment;
- keep Reference policy blocked until evidence/decision exists.

### Slice D: Import/Batch/Sync Hardening

- validate a complete draft before mutation;
- define partial-error reporting, migration and quarantine;
- do not import Open Canvas serialized graph schema.

Slices C/D and any extension of A/B are not authorized by this document. The completed A/B slice must not be expanded opportunistically into snapshot deep-clone, subgraph copy, persistence or collaboration.

## 14. Non-Goals And Stop Conditions

- No domain, Reference, import/batch/sync, persistence or collaboration runtime is specified as completed; Batch 57 structural code, fixture evidence and screenshots are recorded separately.
- No exact source toast, cursor, invalid color, keyboard behavior or Reference outcome is claimed.
- No real provider/model runner, upload, billing, collaboration or remote save is introduced.
- No FrameOS route/store/Handle behavior is changed.
- No edge flow effect, node shell or selected overlay geometry is redesigned.
- Shared source project remains read-only; real duplicate/self/cycle drag requires an accepted disposable source fixture.
- If implementation cannot preserve zero mutation on reject or one-step history on accepted adjustment, stop and revise the transaction design before coding further.
