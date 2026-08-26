# LibTV 异步结果入口与陈旧执行收敛合同

> 状态：`CURRENT_RESEARCH` / `DESIGN_SPEC_COMPLETE` / `RUNTIME_MISSING`
>
> 对应：`DEC-031`、`LIBTV-TR-037`、`OC-TR-011`、`OC-ADOPT-018`、`LIBTV-PAR-009`
>
> Fixture / verifier：`LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` / `LIBTV-VR-015`
>
> 当前授权：只做研究和设计；不修改 `src/`、测试脚本、submodule pointer、provider 或共享源站状态

## 1. 目的

当前文档体系已经回答了两个相邻问题：

- [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md) 定义 source、run、result、node 和 save 的正交身份与状态语义；
- [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md) 定义 T0-T5 graph mutation authority，并要求 remote/server patch 不能伪装成用户 gesture。

仍缺少的机械合同是：**一次已接受的操作异步完成后，结果如何证明仍属于当前 canvas/source/version/run，如何与期间发生的编辑、删除、切换、undo、retry 和另一个 completion 收敛，以及如何把结果以一次受验证的 graph transaction 落地。**

本文不再创造一套 run status，也不设计真实后端。它只把状态语义和 graph authority 之间的空白补齐，避免未来 Seedance 逐帧拉片、片段重拍、超长视频、视频处理和 Director 导出继续由 component timer 或 generic node patch 决定 durable graph state。

## 2. 研究基线与证据边界

| 对象 | 固定基线 | 研究方法 | 边界 |
|---|---|---|---|
| Open Canvas | submodule `cf3a906bb8c35bb940d3267497e7f394b8f42582` | 静态读取 execute route、runner、run store、node patch、polling、save/revision | 未调用 provider、未压测 KV/file persistence、未证明公网部署版本 |
| LibTV clone | fixed audit commit `8007e13`；共享分支随后推进到 Batch 58/59，后续并行改动不纳入本轮事实 | 审计时使用 `git show 8007e13:*` 等价的 committed view，不把工作区 WIP 当稳定事实 | 无网络任务、无真实 run backend、无代码修改 |
| LibTV source | 既有文章、live/bundle 和 fixture 研究 | 只引用已有事实 | 共享项目不执行上传、提交、生成、重试、取消或删除 |

本文标记：

| 标记 | 含义 |
|---|---|
| `OPEN_CANVAS_FACT` | 固定上游源码直接支持 |
| `OPEN_CANVAS_LIMITATION` | 固定调用链存在的明确缺口或由代码可直接推出的竞态窗口 |
| `CLONE_FACT` | 当前已提交 clone 源码直接支持 |
| `DESIGN_DECISION` | 为后续有界实现推荐的合同，不声称 LibTV 源站使用同名字段 |
| `SOURCE_UNKNOWN` | 必须由 disposable source fixture 或业务接口确认 |
| `PROTOTYPE_BOUNDARY` | 当前前端近似，不得包装成真实远端执行 |

## 3. 位置：三份权威各管一层

```text
Process / Result State Matrix
  -> identity and state meaning

Graph Mutation Entry-point Trust Matrix
  -> T0-T5 authority and full-draft transaction

This contract
  -> async envelope, freshness checks, field ownership,
     stale disposition, history/resource convergence
```

任何后续实现计划必须同时引用三份文档。只引用状态矩阵会缺少 graph commit 规则；只引用 T5 会缺少 run/result 语义；只引用本文则会丢失现有 graph invariant、copy/delete 和 document authority。

## 4. Open Canvas 当前执行链

### 4.1 固定调用链

```text
CanvasStudioShell.handleExecuteSelectedNode
  -> saveGraphNow()
  -> POST /api/canvas/:canvasId/nodes/:nodeId/execute
      { revision, triggerType }
  -> executeLocalCanvasNode()
      revision equality check
      build descriptor from persisted graph
      create run(status=running)
      invoke provider
      update run
      apply node patch
      increment canvas revision
  -> client applyServerNodePatch()
      patch live node
      advance revision and savedGraphString baseline
  -> non-terminal run starts runId-keyed polling
  -> GET /api/canvas/:canvasId/runs/:runId
      query provider
      update run
      optional node patch + revision
  -> terminal toast / polling cleanup
```

直接证据：

- [`execute route`](../../research/upstream/open-canvas/app/api/canvas/[canvasId]/nodes/[nodeId]/execute/route.ts#L1) 只接收 revision 与 manual/retry trigger；
- [`local-canvas-runner.ts`](../../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts#L90) 在持久化 graph 上构造 descriptor、创建 run、调用 provider 并产生 node patch；
- [`run route`](../../research/upstream/open-canvas/app/api/canvas/[canvasId]/runs/[runId]/route.ts#L1) 以 run ID 查询异步任务；
- [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5187) 按 run ID 管理 polling timer，并可从 `node.status + lastRunId` 恢复 polling；
- [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L836) 将 server patch 同时投影到 live nodes 与 saved baseline；
- [`local-canvas-store.ts`](../../research/upstream/open-canvas/shared/models/local-canvas-store.ts#L337) 将 node patch 写回 durable graph 并增加 revision。

### 4.2 值得借鉴的结构

| 机制 | 价值 | LibTV 可借范围 |
|---|---|---|
| 执行前保存并提交 revision | descriptor 基于明确 persisted graph，而不是随时变化的 UI object | future remote execution 的 base identity；当前 prototype 不引入 persistence |
| run record 独立于 node data | run 可记录 trigger、scene、provider、model、prompt、input/request/response/output/error | 对齐 source/run/result 正交身份，不移植 provider 字段 |
| polling 以 `runId` 为 key | 一个 timer 对应一个执行身份，页面重载后可由 node 指针恢复 | local deterministic fixture 和 future task transport |
| server patch 是独立 store authority | 远端结果不冒充普通表单编辑 | 对齐 T5；必须补 LibTV field ownership/freshness |
| server patch 推进 revision 与 saved baseline | 远端写入不应被错误标成未保存的本地 gesture | 只作为 future persistence 设计输入 |
| image/video history 合并 | 新 output 可进入历史而非只覆盖一个 URL | 需先换成稳定 result/version identity，不能用 URL 充当 ID |

### 4.3 不能照抄的缺口

Open Canvas 给出了正确的分层形状，但固定实现没有形成完整的 stale-result authority。

| ID | 固定实现 | 缺口 | 对 LibTV 的警示 |
|---|---|---|---|
| `OC-AR-001` | execute 先读取 canvas 并比较 revision，随后才另行创建 run | revision check、run reservation 与 node owner claim 不是一个原子提交 | 两个并发请求可能都通过早期检查；不能把 preflight compare 当 durable lease |
| `OC-AR-002` | run 先以 `running` 创建，之后才进入 audio/provider 路径 | audio unsupported 和 provider throw 没有 runner-level cleanup；run 可滞留 `running` | 先写 run 后调用外部系统必须有 terminal failure/finally 补偿 |
| `OC-AR-003` | terminal run update 与 node patch 是两次独立 `updateDb` | 中间失败会产生 terminal run / stale node，或相反 | run/result/graph projection 需要可恢复的 commit protocol |
| `OC-AR-004` | `applyLocalCanvasNodePatch` 只要求 canvas/node 存在 | 不比较 expected revision、expected current run、source version 或 patch owner | old completion 可落到仍同 ID、但语义已变化的 node |
| `OC-AR-005` | `applyServerNodePatch` 对 live node 和 saved baseline 直接应用 typed-looking patch | 不验证 patch 是否仍属于 `lastRunId`，也没有字段 owner registry | stale text run 可覆盖用户后续 `plainText`；状态/媒体选择也可能被旧 run 改写 |
| `OC-AR-006` | image/video patch 以 URL 合并历史，并让 patched media 成为 current selection | URL 同时承担去重与当前结果选择 | 结果身份、内容地址和 accepted selection 应分开 |
| `OC-AR-007` | failed/canceled polling 在应用 server patch 后又调用本地 `updateNodeData` | translated error 可能成为 dirty local edit，server/user authority 混合 | terminal transport feedback 不应通过 generic user edit path 修正 |
| `OC-AR-008` | `updateDb` 是 storage 上的 read-modify-write | file/KV 层没有锁或 storage CAS；revision 只存在于读出的对象副本 | 多请求/多实例原子性未被源码证明 |
| `OC-AR-009` | 类型声明支持 retry/canceled | current shell 未找到 retry/cancel command 或 cancel route | 数据枚举存在不等于完整用户生命周期已接通 |

`OC-AR-001/004/005` 是本项目最重要的反例：**revision 数字存在，并不自动证明某个 run 仍有权写某个字段。**

## 5. 当前 LibTV clone 异步入口审计

### 5.1 总体事实

对 fixed commit `8007e13` 的 `src/` 静态搜索得到：

- 没有 `fetch`、XHR、WebSocket、EventSource 或 AbortController；
- 没有普通 LibTV canvas run store、run ID、source media version 或 remote patch ingress；
- 多数“处理中”只是 component-local timer 后调用现有 graph creator；
- 多数创建出的处理节点保持 `pending`，没有后续 completion path；
- Director 动画导出是唯一执行真实长耗时 browser work 后再向普通 canvas 写入 ready result 的路径。

因此当前 clone 不是“已经有一个简化 task backend”，而是三类不同近似：

```text
feedback-only local state
deferred graph creation after a short timer
real browser-side asset production followed by graph insertion
```

### 5.2 Graph-producing delayed entries

| Entry | Delay / async owner | Captured input | Completion graph action | Current guard | Current output |
|---|---|---|---|---|---|
| shot breakdown | node component timer，700ms | source node ID + dimension array | `completeShotBreakdown` | component unmount clears timer；store checks source exists and no prior results | patches source complete + result nodes/edges；selects first result |
| audio split | `VideoNode` timer，600ms | source ID + split mode | `createAudioSplit` | unmount clears timer；store pre-checks source | audio + pending silent-video + two edges；selects silent video |
| depth motion | `VideoNode` timer，520ms | source ID + resolution + duration | `createDepthMotionCapture` | unmount clears timer；store pre-checks source | one pending video + edge；selection returns source |
| smart matting | `VideoNode` timer，480ms | source ID | `createSmartMatting` | unmount clears timer；store pre-checks source | one pending video + edge；selection returns source |
| picture edit | `VideoNode` timer，520ms | source ID + mode + marks | `createPictureEdit` | unmount clears timer；store pre-checks source/marks | one pending video + edge；selection returns source |
| long video | selected generation panel timer，520ms | source ID + prompt/model/ratio/resolution/duration/audio/credits/reference count | `createLongVideoProcess` | panel unmount clears timer；store pre-checks source | 12 pending nodes + 22 edges；selection returns source |
| Director animation export | `VideoExportController` async recorder | source ID + request ID + scene/camera/export parameters | `createDirectorAnimationExport` | controller `active` flag suppresses unmounted completion；store pre-checks source and blob metadata | ready video node + edge；selection moves to result |

Source anchors：[`ShotBreakdownNode.tsx`](../../src/components/nodes/ShotBreakdownNode.tsx#L69)、[`VideoNode.tsx`](../../src/components/nodes/VideoNode.tsx#L214)、[`VideoGenerationPanel.tsx`](../../src/components/VideoGenerationPanel.tsx#L175)、[`DirectorViewport.tsx`](../../src/components/director/DirectorViewport.tsx#L1260)、[`DirectorDesk.tsx`](../../src/components/director/DirectorDesk.tsx#L224) 和 [`canvasStore.ts`](../../src/store/canvasStore.ts#L1240)。

### 5.3 当前近似中已经出现的收敛问题

| ID | 场景 | 当前可推出结果 | 风险分类 |
|---|---|---|---|
| `LIBTV-AR-001` | shot breakdown 运行时继续切换 dimensions | timer 捕获旧 dimensions，但 source data 可继续变化；completion 以旧数组建 result、保留新 data | descriptor/result aggregate mismatch |
| `LIBTV-AR-002` | delayed VideoNode/shot completion 前用户选中别的节点 | node component 仍 mounted，completion action 按各自规则重写全局 selection | stale UI owner / selection steal |
| `LIBTV-AR-003` | long-video 提交后 panel 因 selection/surface replacement 卸载 | cleanup 清 timer，尚未创建任何 durable operation；提交表现可被 UI 生命周期取消 | acceptance point ambiguity |
| `LIBTV-AR-004` | long-video 等待期间继续编辑 prompt/params | callback 捕获提交时 render 的值，但当前表单显示新 draft；完成 feedback 没有 descriptor identity | old descriptor / current draft conflation |
| `LIBTV-AR-005` | video processing 短延迟结束 | 创建的是永久 `pending` target；没有 run/result ingress 将其推进到 ready/error | pending placeholder presented as lifecycle |
| `LIBTV-AR-006` | store creator 在 pre-read 后提交 | 多数 creator 用旧 canvas/source 计算 nodes/position，再在 `set` 中只确认 canvas 仍存在 | stale proposal can commit against changed graph |
| `LIBTV-AR-007` | Director 录制完成后创建结果 | 有 request ID、unmount suppression 和 blob commit-failure cleanup，但没有 source media version、graph base 或 accepted run owner | strongest current path, still identity-incomplete |
| `LIBTV-AR-008` | undo 已接受的 external operation | 当前没有统一 operation record 或 cancel/ignore marker | future completion semantics undefined |

这些是 committed clone 的设计缺口，不是 LibTV source 行为声明。短 timer 目前可以继续作为 `PROTOTYPE_LATENCY` 解释，但不能成为未来真实 provider integration 的执行骨架。

## 6. Authority 模型

### 6.1 三个不可替代的对象

以下是概念 schema，不是已授权 TypeScript API：

```ts
interface AsyncOperationDescriptor {
  operationId: string;
  canvasId: string;
  sourceNodeId: string;
  sourceNodeType: string;
  sourceMediaVersionId: string | null;
  operation: string;
  draftFingerprint: string;
  baseGraphIdentity: string;
  submittedAt: string;
}

interface AsyncResultEnvelope {
  operationId: string;
  runId: string;
  attemptId: string;
  sourceNodeId: string;
  sourceMediaVersionId: string | null;
  resultId: string;
  resultVersionId: string;
  terminalState: "succeeded" | "failed" | "canceled";
  ownedPatch: unknown;
}

type AsyncIngressDisposition =
  | "apply-current"
  | "attach-superseded"
  | "duplicate-noop"
  | "quarantine"
  | "reject-stale"
  | "reject-invalid";
```

职责必须分开：

- descriptor 是用户接受操作时冻结的输入；
- envelope 是 transport/provider 返回的事实；
- disposition 是当前 graph authority 对 envelope 的判定；
- graph command plan 是 disposition 允许后生成的完整 nodes/edges/data/selection/history/resource delta。

### 6.2 T5 不是免检通道

T5 remote/server authority 必须经过：

```text
parse envelope
  -> authenticate/identify operation and attempt
  -> load current canvas/source/owner
  -> compare source version + run owner + graph identity
  -> validate field ownership
  -> classify stale/duplicate/current
  -> build full final graph draft
  -> run existing graph invariants
  -> commit once or return zero-mutation result
```

server “已经成功”只证明 transport/run fact，不等于它仍能覆盖当前 draft、成为 accepted result、抢走 selection 或写入 graph history。

## 7. Field Ownership

### 7.1 字段类别

| Owner | 例子 | 可由 async patch 改写？ |
|---|---|---|
| graph identity | node ID/type、parentId、edge endpoints、aggregate membership | 否；只能由 validated graph command plan 改 |
| user draft | prompt、marks、time range、model/params、candidate selection | 默认否；结果只能引用 captured fingerprint |
| run projection | current run ID、queued/running/terminal summary、stage progress、error | 仅匹配 current operation/attempt 时 |
| result projection | result/version ID、output locator、duration/resolution、provenance | 仅匹配 operation/source version 且 payload valid 时 |
| derived display | title、subtitle、status badge、thumbnail choice | 从 authoritative state 派生，不作为 transport 真相 |
| resource ownership | blob/object URL、upload handle、cleanup token | 通过显式 transfer/release，不由普通 object spread |

### 7.2 冲突规则

1. async patch 不接受 `Partial<NodeData>` 或任意 object spread；
2. 每个 operation 注册 allowed result fields、required identities 和 graph projection；
3. 同一字段如果既是 user-authored 又是 generated output，必须拆 current draft 与 accepted result，或显式进入 conflict/quarantine；
4. node status 不能作为唯一 owner token；
5. `lastRunId` 只有经过 compare-and-set 才能承担 current run 指针；
6. media URL 不能同时充当 result ID、version ID、去重 key 和 current selection；
7. translated UI error 不回写为 server-authoritative payload。

## 8. Freshness 与收敛矩阵

| Current state when result arrives | Required classification | Graph effect | UI effect |
|---|---|---|---|
| canvas identity missing/replaced | `reject-stale` | zero mutation | optional diagnostic；release unowned resource |
| source node deleted | `reject-stale` or declared provenance quarantine | no implicit source recreation | no selection steal |
| same node ID, incompatible type | `reject-invalid` | zero mutation | stable diagnostic |
| source media version changed | `attach-superseded` or `quarantine` | never overwrite current accepted result | stale provenance may be inspectable if product allows |
| current operation/run differs | `reject-stale` or `attach-superseded` | old run cannot change current run/status/selection | current run feedback unchanged |
| draft fingerprint changed, source version same | result may remain valid for old descriptor | attach to captured operation only | current draft stays editing; no false “this draft completed” |
| placeholder still owned by same operation | `apply-current` | validated in-place result projection | selection follows declared transaction only |
| placeholder was manually removed/undo submit | `reject-stale` or quarantine | no placeholder resurrection | no toast that implies visible result exists |
| same result/version already committed | `duplicate-noop` | no history, no duplicate media/edge/node | optional idempotent acknowledgement |
| older attempt finishes after retry | old attempt stale | no current status/result overwrite | retry remains owner |
| terminal failure after partial outputs | operation-specific partial plan | retain declared successes; mark failed partition | failure is scoped to run/stage |
| result payload valid but graph plan violates invariant | `reject-invalid` / quarantine | zero partial graph mutation | stable error and cleanup path |

`attach-superseded` 是产品能力，不是默认兜底。没有明确 provenance/history UI 时，当前 prototype 应使用 `reject-stale` + deterministic diagnostic，而不是偷偷创建孤立节点。

## 9. 提交与 History 合同

### 9.1 Acceptance point

每个操作必须声明用户动作何时被接受：

| Option | 含义 | 适用范围 |
|---|---|---|
| `presentation-delay-only` | timer 结束前没有 durable operation；关闭 surface 可取消 | 纯 feedback demo；不得显示真实任务已提交 |
| `accepted-local-operation` | 点击时立即记录 descriptor/owner，结果可稍后到达 | deterministic local fixture / bounded prototype |
| `accepted-remote-run` | server 原子创建 run/lease 并返回 identity 后才算 accepted | future provider backend |

当前短 timer 混合了第一、第二种语义。后续若实现 async fixture，推荐点击时明确接受 descriptor；spinner 只是 projection，不能成为 operation owner。

### 9.2 History rules

1. progress/polling/status observation 不产生 graph history step；
2. submit 若创建 placeholder/cohort，是一个用户 transaction；
3. result patch 若只填充该 placeholder 的 run-owned/result-owned字段，不为每次 poll 追加 history；
4. 新增 candidate/result topology 时使用一个完整 graph command，而不是每个 output 一步；
5. duplicate/stale/rejected completion 是 zero-history；
6. undo submit 表示当前 graph 不再接受该 operation 的 completion；是否请求远端 cancel 由 transport 决定；
7. redo 不得自动重放计费/provider side effect；它只能恢复本地 descriptor/placeholder，随后要求显式 resume/retry policy；
8. result accepted/superseded 是独立用户意图时，按一个 history transaction 记录；
9. async completion 不得无条件把 selection 改回 source/result；selection output 必须比较 current UI intent 或定义为 preserve。

### 9.3 Run 与 graph commit 不可原子时

未来后端若无法把 terminal run 与 graph projection 放在同一事务中，必须至少支持：

```text
terminal run stores immutable result envelope
  -> graph projection attempts idempotently by resultVersionId
  -> projection state records pending/applied/rejected
  -> retry projection never re-invokes provider
```

这比“run success 后立即 generic patch，失败就丢失”更可恢复，也避免 graph commit retry 触发重复计费。

## 10. UI 与 Resource Ownership

### 10.1 UI owner

- durable operation 不以 React component 是否 mounted 作为唯一生命线；
- timer cleanup 只能停止 polling/animation callback，不能把已接受 operation 从事实中删除；
- completion 默认 preserve 当前 selection、active panel 和 canvas focus；
- 只有 source-confirmed 或 clone-only 明确合同允许 result-ready 自动选择时，才可请求 selection change；
- node/canvas deletion、canvas switch 和 owner reconciliation 先使 UI surface 失效，再由 async ingress 独立判 stale。

### 10.2 Resource transfer

以 Director blob URL 为例：

```text
producer owns URL
  -> graph commit accepted
  -> resource ownership transfers to result node/registry

producer owns URL
  -> stale/reject/commit failure/unmount without accepted handoff
  -> producer revokes URL
```

删除 result、canvas、undo/redo 与 document portability 的后续释放规则继续服从 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) 和 [`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)。本文不另造 media registry。

## 11. 决策队列

### `LIBTV-ASYNC-DQ-001`：当前短 timer 是什么

**推荐决策：** 全部标为 `PROTOTYPE_LATENCY`，不是 run backend。只有新 fixture/实现显式创建 operation identity 后，才可使用 queued/running/result 语义。

### `LIBTV-ASYNC-DQ-002`：accepted operation 是否随 surface unmount 取消

**推荐决策：** 否。未 accepted 的 presentation delay 可取消；已 accepted operation 由 operation owner 管理，surface 只订阅 projection。

### `LIBTV-ASYNC-DQ-003`：descriptor 与继续编辑的 draft

**推荐决策：** submit 冻结 descriptor fingerprint；后续编辑形成新 draft。旧结果可归属旧 descriptor，但不能把新 draft 标成 complete。

### `LIBTV-ASYNC-DQ-004`：默认 stale policy

**推荐决策：** 当前无 provenance UI 时 `reject-stale`；只有 operation 明确支持历史结果浏览时才 `attach-superseded`。

### `LIBTV-ASYNC-DQ-005`：selection output

**推荐决策：** async completion 默认 `preserve-current`。自动选 result 必须是 source-confirmed 或 clone-only 明确、并经过“用户仍停留在该 operation context”检查的行为。

### `LIBTV-ASYNC-DQ-006`：undo/redo 与外部 side effect

**推荐决策：** undo 使本地 owner 无效并忽略晚到结果；可 best-effort cancel transport。redo 不自动重新调用 provider。

### `LIBTV-ASYNC-DQ-007`：result patch 是否记 history

**推荐决策：** progress/status patch 不记；同一 placeholder 的 terminal projection 不逐 patch 记；新 topology 或用户 accept/supersede 是具名 transaction。

### `LIBTV-ASYNC-DQ-008`：run terminal 与 graph patch 分离失败

**推荐决策：** result envelope 持久且 projection 可幂等重试；projection retry 不重新执行 provider。

### `LIBTV-ASYNC-DQ-009`：第一实施候选

**推荐决策：** 若未来授权，先用 shot breakdown deterministic fixture 证明 descriptor freeze、selection preserve、delete/undo stale rejection，再覆盖多节点长视频和 Director resource transfer。不要先接真实 provider。

### `LIBTV-ASYNC-DQ-010`：Open Canvas server patch 是否可复用

**推荐决策：** 只借独立 authority 和 saved-baseline projection 思路；不复用其 generic patch、URL identity、无 owner compare 或非原子 run/patch 流程。

## 12. Invariants

| ID | Invariant | Current clone | Pass condition |
|---|---|---|---|
| `LIBTV-GI-023` | every graph-producing async completion carries operation/run/result identity | timers call creator directly | no anonymous delayed graph write |
| `LIBTV-GI-024` | completion is checked against canvas/source/type/media version/current owner before planning | source existence only or component active flag | stale/invalid returns stable zero-mutation disposition |
| `LIBTV-GI-025` | async patch touches only operation-registered fields | generic node data mechanisms remain available | no overwrite of graph identity or current user draft |
| `LIBTV-GI-026` | duplicate/out-of-order completions are idempotent | no result/version ingress | no duplicate node/edge/media/history/selection effect |
| `LIBTV-GI-027` | accepted result graph delta is one validated full-draft command | current creators append direct precomputed nodes/edges | existing GI/GC authorities run before one commit |
| `LIBTV-GI-028` | component unmount and durable operation lifecycle are explicitly separate | mixed timer cleanup semantics | accepted operation remains observable or explicitly canceled |
| `LIBTV-GI-029` | async completion does not steal unrelated current selection/surface | several creators rewrite selection | default preserve or declared contextual selection result |
| `LIBTV-GI-030` | resource ownership transfers exactly once or is released | Director has partial local cleanup | stale/reject/delete/commit failure have deterministic release |

These extend `LIBTV-GI-018..022`; they do not replace graph connection, document, data, delete or ingress invariants.

## 13. Required Cases

| ID | Scenario | Required result |
|---|---|---|
| `LIBTV-GC-024` | submit descriptor A, edit current draft to B, A completes | A attaches only to A operation；B remains editing |
| `LIBTV-GC-025` | source media version changes during run | old result stale/superseded；current output unchanged |
| `LIBTV-GC-026` | source/placeholder deleted or submit undone before completion | no resurrection、selection steal or partial graph |
| `LIBTV-GC-027` | retry B becomes current, old attempt A finishes last | A cannot overwrite B status/result/error |
| `LIBTV-GC-028` | same terminal response delivered twice | second delivery duplicate-noop；history/counts unchanged |
| `LIBTV-GC-029` | user selects another node/surface before completion | current UI owner preserved unless explicit contextual rule passes |
| `LIBTV-GC-030` | graph changed so precomputed placement/edges are stale | plan rebuilt from current graph or rejected；no dangling/collision-dependent stale append |
| `LIBTV-GC-031` | run terminal persisted but graph projection fails | envelope remains retryable；provider not re-invoked |
| `LIBTV-GC-032` | result resource produced but ingress rejects | producer releases blob/temp resource exactly once |
| `LIBTV-GC-033` | progress/failure/success polling sequence | no accidental graph history per poll；terminal UI derives from authoritative run/result state |

## 14. `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01`

### 14.1 Substrate

- fresh Page + `LIBTV-FIX-LOCAL-EMPTY-01`；
- deterministic canvas/source/version/operation/run/attempt/result IDs；
- fake clock or controllable completion queue；
- no remote request、provider key、upload、billing or shared source project；
- graph fixture reuses connection/document/data/delete/entrypoint authorities instead of bypassing them；
- every scenario records nodes、edges、selection、history、operation owner、result envelope and resource ledger before/after.

### 14.2 Required aliases

| Alias | Meaning |
|---|---|
| `C1/C2` | original and switched canvas |
| `S1@V1/S1@V2` | same source node with two media versions |
| `D_A/D_B` | submitted descriptor and later draft |
| `R_A1/R_A2/R_B1` | old attempt、retry、new operation runs |
| `O_A/O_B` | operation owner identities |
| `X1/X2` | stable result/version identities |
| `P1` | operation-owned placeholder |
| `U1` | produced blob/temp resource with observable owner/release count |

### 14.3 Scenario corpus

| Scene | Setup | Controlled event | Assertions |
|---|---|---|---|
| current apply | C1/S1@V1/O_A/P1 current | X1 success | one terminal projection、declared selection/history、resource transfer |
| draft drift | D_A submitted, current D_B | X1 success | D_B unchanged；result records D_A fingerprint |
| source drift | S1 changes V1 -> V2 | V1 result | stale/superseded；no current overwrite |
| delete/undo | remove P1 or undo submit | X1 success | zero graph mutation、no resurrection、release U1 |
| retry race | A1 old, A2 current | A2 then A1 | A2 remains current；A1 stale |
| duplicate delivery | X1 twice | second delivery | exact no-op incl. history/selection/resource |
| UI drift | select unrelated node/open surface | X1 success | owner remains unless declared contextual transition |
| graph drift | move/add/delete around source/target | X1 success | current-state replan or stable reject |
| projection recovery | persist terminal X1, inject graph commit failure | retry projection | provider call count unchanged；eventual one commit |
| invalid payload | missing identity/bad field/type/resource | ingress | stable reject-invalid；zero partial mutation |

### 14.4 Reset

Discard the Page after each browser scene. Fake clock、completion queue、object URLs、operation registry and resource ledger must be instance-scoped. Undo is a scenario action, not fixture teardown.

## 15. `LIBTV-VR-015`

| Layer | Required assertions |
|---|---|
| static inventory | every graph-producing timer/promise/poll/subscription maps to T5 or declared local async authority |
| identity | descriptor/envelope expose canvas/source/version/operation/run/attempt/result identities independently |
| freshness | current/stale/duplicate/invalid dispositions are deterministic and reasoned |
| field ownership | operation patch cannot alter graph identity or unrelated user draft fields |
| graph | accepted plan passes existing GI/GC checks；reject has zero nodes/edges/data mutation |
| selection/UI | unrelated current selection/surface is preserved；no stale toast claims visible success |
| history | no per-poll history；accepted topology/accept action has exact declared step count |
| race | retry out-of-order、duplicate delivery、delete/undo and graph drift cases pass |
| recovery | terminal envelope can retry projection without provider re-execution |
| resource | transfer/release exactly once；no leaked blob/temp owner in fixture ledger |
| prototype boundary | no real progress、provider、billing、upload、save or source parity claim |
| runtime | focused desktop/mobile only where visible feedback contract requires；console/page/request errors captured |

`LIBTV-VR-015` composes `VR-007` state semantics、`VR-012` node data、`VR-013` delete/resource and `VR-014` ingress authority. It does not replace them.

## 16. Future Implementation Slices

No slice below is currently authorized.

### Slice A: pure async envelope and reconciliation

- conceptual identities become a narrow closed schema；
- pure current/stale/duplicate/invalid cases；
- no component or provider integration；
- fixture clock/queue only after authorization.

### Slice B: shot breakdown deterministic operation

- freeze dimensions at acceptance；
- prevent changed draft/result aggregate mismatch；
- preserve unrelated selection；
- delete/undo completion becomes stale zero-mutation；
- retain current result visual topology and source facts.

### Slice C: video derived operation family

- audio split、depth、matting、picture edit each register operation fields/topology；
- remove component timer as durable owner；
- keep each existing bounded source/clone contract separate；
- no claim of real processing completion.

### Slice D: long-video placeholder cohort

- descriptor/process ID becomes explicit owner；
- 12/22 topology remains clone-only unless new source evidence changes it；
- current all-pending graph gains deterministic local state fixture only if separately authorized；
- no provider/progress/billing integration.

### Slice E: Director browser asset handoff

- preserve current recorder and active-unmount protection；
- add source/version/operation freshness boundary；
- prove blob ownership transfer/release；
- do not merge `directorStore` and ordinary `canvasStore`.

### Slice F: future remote provider authority

- atomic run reservation or equivalent current-owner CAS；
- immutable terminal result envelope；
- idempotent graph projection；
- cancel/retry/security/billing/storage require independent backend authorization.

## 17. Open Canvas 采纳结论

| Element | Decision | Reason |
|---|---|---|
| run/node/save 分层 | `ADOPT_METHOD` | 已由现有状态矩阵吸收 |
| runId-keyed polling and reload recovery | `ADAPT_TO_LIBTV` | 方法有效，但只在真实 operation identity 存在时 |
| descriptor built from persisted graph | `ADOPT_METHOD` | 强化 captured input；当前 prototype 不引入 persistence |
| separate server patch authority | `ADOPT_METHOD` | 对齐 T5；必须补 freshness/field owner |
| current generic `CanvasNodePatch` apply | `REJECT_TRANSPLANT` | 无 expected run/version/field ownership |
| URL-based media history identity | `REJECT_TRANSPLANT` | locator 不能代替 result/version ID |
| current run-update + node-patch two-write flow | `RESEARCH_ONLY` | 可作 failure/recovery 反例，不作模板 |
| current file/KV updateDb | `REJECT_TRANSPLANT` | persistence product scope 不匹配，原子性也未证明 |

## 18. Stop Conditions

以下任一情况都保持文档态：

- 没有该 capability 的 LibTV source fact 或明确 clone-only boundary；
- source media version、operation/run/result identity 尚未决定；
- 只有 UI spinner，没有 accepted operation owner；
- 需要真实 provider、上传、计费、远端保存或 shared source mutation；
- graph plan 仍通过 generic `setNodes/setEdges/updateNodeData` 绕过现有 authority；
- stale policy、undo/redo、selection 或 resource cleanup 未写入 verifier；
- 相关文件存在并行 WIP，无法形成窄且不干扰的 implementation boundary；
- 用户未明确授权编码。

## 19. 结论

Open Canvas 最值得借鉴的是一条可见的控制面：descriptor、run record、runId polling、server patch、revision 和 saved baseline 是分开的。它同时证明，仅有这些名词仍不够：固定实现没有把 patch 绑定到 expected current run/source version/field owner，run terminal 与 graph patch 也不是原子提交。

当前 LibTV clone 更早：短 timer 多数只是延迟创建 graph，pending output 没有 completion ingress，Director 才有真实异步资产回写。下一步若获得编码授权，不应先接 provider，而应先用 `LIBTV-FIX-LOCAL-ASYNC-INGRESS-01` 和 `LIBTV-VR-015` 证明 descriptor freeze、stale rejection、selection preservation、idempotent projection 和 resource transfer。这样未来逐帧拉片、长视频、重拍和 Director 才能共享 correctness 方法，而不必共享一个虚假的通用 `status` 或 generic node patch。
