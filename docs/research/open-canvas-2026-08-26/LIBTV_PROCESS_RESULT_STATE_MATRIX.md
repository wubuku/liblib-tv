# LibTV Process / Result 正交状态矩阵

> 状态：`CURRENT_RESEARCH` / `CURRENT_GUIDANCE`
>
> 对应：`OC-BP-005`、`OC-ADOPT-003/009/018`、`DEC-031`、`LIBTV-PAR-009`、`LIBTV-VR-007/015`
>
> 当前授权：只做研究和设计；不修改 `src/`、verifier 或共享源站状态

## 1. 目的

逐帧拉片、片段重拍和超长视频都同时涉及编辑输入、画布节点、异步任务、中间候选、最终结果和保存反馈。当前 clone 以三个不同的本地 prototype 表达它们：

- `shot-breakdown` 用 component-local `running` 后一次性创建持久结果节点；
- 片段重拍只显示本地提交确认，没有任务或结果 graph；
- 超长视频一次创建 12 个全为 `pending` 的过程节点和 22 条边。

这些实现各自有历史合同，但不能共同证明 LibTV 源站的任务协议。本文的目标不是先设计一个统一后端，而是建立正交词汇和验证场景，防止后续把“输入已准备”“任务已提交”“节点可显示”“部分结果已到达”“画布已保存”压成一个 `status`。

## 2. 证据与词汇边界

| 标记 | 含义 |
|---|---|
| `SOURCE_FACT` | 当前 LibTV DOM/bundle/文章截图支持的可见入口、形态或状态 |
| `CLONE_FACT` | 当前仓库组件、store 和历史 verifier 直接支持 |
| `DESIGN_VOCABULARY` | 为比较不同能力而定义的正交概念，不声称源站使用同名字段 |
| `UNKNOWN_SOURCE` | 需要 disposable source fixture 或真实业务接口才能确认 |
| `PROTOTYPE_DECISION` | 当前前端原型为可验证性作出的有界选择 |

Open Canvas 的贡献是证明 node status、run status 和 save/conflict 可以分层，以及媒体历史需要稳定 identity。它不提供 LibTV 的状态名、重试规则、时间范围、节点拓扑或结果替换合同。

## 3. 当前事实基线

| 能力 | 已知 LibTV 形态 | 当前 clone | 不能据此推出 |
|---|---|---|---|
| 逐帧拉片 | 独立节点；输入视频；分镜/动态/音乐结果卡 | `empty -> ready -> local running -> complete`；一次事务创建结构化结果 nodes/edges | 真实 run ID、部分成功、失败重试、结果版本和源视频替换策略 |
| 片段重拍 | ready-video 工具；时间范围 token；目标区间重做 | ready source + range authoring + local submit confirmation；无结果 graph | 提交后原地替换还是新版本、任务进度、失败恢复、音频处理 |
| 超长视频 | Beta 参数；画布可表达素材、镜头、候选和成片过程 | 一次事务创建 12 nodes / 22 edges；全部 `pending`；source 保持选中 | 源站精确拓扑、真实 stage 进度、局部重算、费用结算和最终结果 |
| 其他视频处理 | ready-video toolbar 派生 subtitle/matting/picture/depth 等路径 | 多数一次创建 `pending` target + source edge | 每个 source action 的真实 task、output version 和 retry 语义 |

主要证据：[`ShotBreakdownNode.spec.md`](../components/ShotBreakdownNode.spec.md)、[`SegmentReshootPanel.spec.md`](../components/SegmentReshootPanel.spec.md)、[`LongVideoProcessNode.spec.md`](../components/LongVideoProcessNode.spec.md)、[`LIBTV_SEEDANCE_CROSSWALK.md`](LIBTV_SEEDANCE_CROSSWALK.md) 和 [`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md)。

## 4. 六个正交身份

任何后续 process/result slice 在设计时至少回答以下身份。字段名只是文档词汇。

| 身份 | 稳定职责 | 不允许使用的替代品 |
|---|---|---|
| `sourceNodeId` | 发起操作的画布对象 | 显示标题、媒体 URL |
| `sourceMediaVersionId` | 本次操作实际读取的媒体版本 | “当前第一个输出”、可变 ordinal |
| `operation` | shot breakdown、segment reshoot、long video 或具体处理动作 | 通用 `generate` 文案 |
| `timeRange` | 可选的源媒体区间、单位和端点规则 | Prompt 中不可解析的普通字符串 |
| `runId` | 一次提交/重试/局部重算的执行身份 | process node ID 或 spinner boolean |
| `resultId/versionId` | 一个 candidate、部分结果或已接受输出 | 缩略图 URL、数组下标 |

当前 clone 尚没有稳定的 `sourceMediaVersionId`/`runId`/`resultId` 通用合同。这是 `DESIGN_FIRST` 缺口，不是要求立刻向 store 添加字段。

## 5. 五个正交状态轴

### 5.1 Authoring state

描述用户输入是否可编辑和可提交，不描述后台是否运行。

| 词汇 | 含义 | 例子 |
|---|---|---|
| `pristine` | 尚未开始编辑或使用默认值 | 空拉片节点、默认长视频面板 |
| `editing` | Prompt、范围、维度或参数正在修改 | 重拍选段、拉片维度切换 |
| `invalid` | 缺必要输入或违反本地 guard | 无视频、空维度、非法区间 |
| `submittable` | 当前输入可形成一次明确 descriptor snapshot | ready input + 合法参数 |
| `frozen-for-run` | 一次 run 已捕获输入快照，后续编辑属于新 draft | 真实异步实现的候选设计；当前源站未知 |

### 5.2 Node availability

描述画布节点当前能呈现/被引用的内容，不等于任务状态。

| 词汇 | 含义 |
|---|---|
| `input-missing` | 节点存在但没有可用 source media |
| `input-ready` | 输入可预览并可进入 authoring/submit |
| `placeholder` | 过程/结果节点已存在，但没有可用输出 |
| `output-ready` | 节点持有可预览或可引用的结果版本 |
| `unavailable` | 输出失败、过期或权限变化，节点仍可能保留解释信息 |

### 5.3 Run state

描述一次执行生命周期。以下是 `DESIGN_VOCABULARY`，不是已恢复的 LibTV API：

```text
not-created -> queued -> running -> succeeded
                         |        -> failed
                         |        -> canceled
                         -> failed/canceled
```

`retry` 不应把旧 run 原地改回 `queued`；设计评审需要决定它创建新 `runId` 还是 child attempt。局部重算还要记录 parent run、受影响 stage/range 和未变化结果。

### 5.4 Result state

| 词汇 | 含义 |
|---|---|
| `none` | 尚无结果 |
| `partial` | 部分 dimension/stage/range 已产生可识别结果 |
| `candidates` | 有多个可比较输出，尚未接受为当前版本 |
| `accepted` | 一个结果被选择为当前下游引用版本 |
| `superseded` | 旧结果仍可追溯，但不再是当前版本 |
| `rejected` | 用户明确丢弃候选；是否保留 provenance 待产品决定 |

### 5.5 Save state

`clean/dirty/saving/saved/error/conflict` 只用于 graph/draft 持久化语义。当前普通 LibTV prototype 没有真实保存后端，因此本轴保持 `PROTOTYPE_BOUNDARY`，不得因 run 成功显示“已保存”，也不得用 graph undo 模拟 conflict recovery。

## 6. 正交状态场景矩阵

| Scene | Authoring | Node | Run | Result | Save | UI / graph expectation |
|---|---|---|---|---|---|---|
| `LIBTV-PR-001` new input node | `pristine` | `input-missing` | `not-created` | `none` | `clean/unknown` | submit disabled；无 process/result graph |
| `LIBTV-PR-002` ready draft | `editing/submittable` | `input-ready` | `not-created` | `none` | `dirty/unknown` | 参数可改；没有“处理中” |
| `LIBTV-PR-003` submitted queue | `frozen-for-run` | source `input-ready`，targets 可为 `placeholder` | `queued` | `none` | independent | captured descriptor 可反查；重复提交策略明确 |
| `LIBTV-PR-004` running | new draft 可 `editing` | source 仍 `input-ready` | `running` | `none` 或旧 `accepted` | independent | 不覆盖用户后续草稿；取消/离开策略明确 |
| `LIBTV-PR-005` partial success | independent | 部分 result `output-ready` | `running` 或 terminal policy | `partial` | independent | 成功维度可见；失败/等待维度不伪装完成 |
| `LIBTV-PR-006` retryable failure | draft retained | placeholder `unavailable` 或 source 保持 ready | `failed` | `none/partial` | independent | 错误归属 run/stage；retry 不复制未知成功结果 |
| `LIBTV-PR-007` candidates ready | new draft independent | candidate nodes `output-ready` | `succeeded` | `candidates` | independent | candidates 有稳定 result ID/version；未选择不自动改下游引用 |
| `LIBTV-PR-008` result accepted | editable new draft | accepted result `output-ready` | terminal | `accepted` | `dirty/unknown` | selection/reference projection 更新；旧 candidate policy 明确 |
| `LIBTV-PR-009` source version changed | draft requires review | old result 可显示但标 stale/unavailable | old run terminal | `superseded/stale` | independent | 不静默把旧 result 解释为新 source 的输出 |
| `LIBTV-PR-010` canceled | draft retained or copied | source ready；placeholder cleanup policy explicit | `canceled` | `none/partial` | independent | 不显示成功；graph cleanup 是单事务或保留 provenance 的明确决定 |
| `LIBTV-PR-011` save conflict during run | authoring/run unchanged | availability unchanged | unchanged | unchanged | `conflict` | run 不因保存冲突变失败；当前 prototype 不实现此场景 |

矩阵的价值在于禁止非法推导。例如 `node=output-ready` 不等于 `save=saved`，`run=succeeded` 不等于已有 `accepted` 结果，`result=partial` 也不等于整个 process 已失败。

## 7. 能力投影

### 7.1 逐帧拉片

当前 clone 可稳定证明 `PR-001/002` 和一个本地化的 `PR-007/008` 合并态：完成动作一次性创建结果并把 source 标为 `complete`。它没有真实 queued/running/partial/failed run，component-local 计时不能作为 run record。

后续需决定：

- 三个 dimension 是一个 run 的并行 result partitions，还是独立 runs；
- 某一 dimension 失败是否形成 `partial`；
- 重试是只重算失败维度还是全部重算；
- 结果卡转正式素材前后使用哪个 version identity；
- source media version 改变时旧结果是 stale、superseded 还是仍可引用。

### 7.2 片段重拍

当前 clone 只覆盖 `PR-002` 和提交 feedback，不应标成 `PR-003` 之后的真实状态。真实合同至少需要 source media version、time range、captured Prompt、run、replacement candidate 和 accepted replacement。

待 source fixture 回答：

- whole rerun 和 selected-range reshoot 是否共用 operation；
- 多区间是一个 run 还是多个 child attempts；
- 输出是原节点新 version、派生节点还是 candidate group；
- 未选择区间和音频如何保持；
- retry/cancel 后 Prompt token 与范围是否保留。

### 7.3 超长视频

当前 12/22 graph 是 `PROTOTYPE_DECISION`：它在一次 graph transaction 中提前创建全部 `placeholder`，每个 stage status 都是 `pending`。这能验证 topology、selection、placement 和 undo/redo，不能覆盖 `PR-004..010`。

后续 source/process fixture 要回答：

- process、shot、candidate 和 assembly 是否各有 run identity；
- stage dependency、并行度和 partial failure；
- candidate 选择是否触发新的 assembly/final run；
- 局部重算保留哪些 result IDs、边和下游选择；
- 最终成片 accepted 后中间图是否保留、折叠或可继续编辑。

## 8. Stale Result 与 Retry 规则

以下是进入实现前必须明确的 correctness 规则：

1. run completion 必须携带 `runId` 和 captured source/version/descriptor identity；
2. 如果当前 draft 或 source version 已变，旧 completion 不得覆盖新 draft；
3. stale result 可以保留为 provenance，但必须与 current accepted result 区分；
4. retry 不复用旧错误状态作为新运行身份；
5. partial retry 只改变声明的 stage/dimension/range，未重算结果保持原 identity；
6. graph mutation、selection 和 history delta 由“接受结果/插入结果”命令定义，不由异步回调任意改写；
7. source deletion、result deletion 和 run record retention 是不同生命周期。

这些规则借鉴 Open Canvas 的 run/node/save 分离和稳定输入投影，但仍需要 LibTV 业务接口或明确 clone-only contract 才能编码。

本节只定义状态/身份语义。Completion envelope、current/stale/duplicate/invalid 判定、field ownership、graph plan、selection/history 和 resource transfer 的机械合同由 [`../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) 负责；未来实现必须同时满足 `LIBTV-VR-007` 与 `LIBTV-VR-015`，不能把“状态名齐全”当成 stale-safe result ingress。

## 9. `LIBTV-FIX-LOCAL-PROCESS-STATES-01` 接收规格

### 9.1 构造原则

- 每个 scenario 使用 fresh Page 和 `LIBTV-FIX-LOCAL-EMPTY-01` substrate；
- 通过真实 UI 构造 source node；复杂 run/result data 只有在领域合同提供窄 fixture adapter 后才可注入；
- fixed data 包含 source node/version、operation、optional range、run/attempt、result IDs 和 axis states；
- 不使用远端 URL、真实任务、积分、上传或 provider key；
- local fixture 显式显示“本地状态夹具”或通过 test-only path 隔离，不能在普通 prototype 中冒充真实任务。

### 9.2 最小场景集

| Fixture scene | Matrix coverage | Required graph shape |
|---|---|---|
| empty/input-ready | `PR-001/002` | one source/process input node，0 result |
| queued/running | `PR-003/004` | source + optional placeholder；captured identity inspectable |
| partial | `PR-005` | at least one ready result + one pending/failed partition |
| failed/retry | `PR-006` | original failed run + separate retry identity；no duplicate accepted result |
| candidates/accepted | `PR-007/008` | stable candidate IDs + one explicit accepted projection |
| stale source | `PR-009` | source version changes while old run/result remains traceable |
| canceled | `PR-010` | no success label；declared placeholder cleanup/provenance |

### 9.3 Reset assertions

Each scene records initial/final nodes, edges, selection, history and fixture-local run/result data. After the scene, discard the Page. One graph undo can verify a transaction but cannot reset asynchronous fixture state or BrowserContext storage.

## 10. `LIBTV-FIX-SOURCE-PROCESS-01` 接收条件

The source fixture requires an independently disposable project with:

- owner and allowed task/credit budget;
- ready source video and known media version;
- at least one observable pending/running/failed/partial/success or authorized equivalent state;
- permission to retry/cancel/select result only when the exact action is approved;
- remote cleanup path and post-cleanup assertions;
- capture plan for DOM, visible copy, network-independent identifiers and graph deltas.

The shared logged-in research project is not this fixture. Without an accepted disposable project, source process actions remain `BLOCKED_BY_FIXTURE`.

## 11. `LIBTV-VR-007` 验证合同

| Layer | Required assertions |
|---|---|
| identity | source node/version、operation/range、run/attempt、candidate/result independently inspectable |
| state | every visible label derives from the declared axis; no success/save inference from another axis |
| stale/race | old completion cannot overwrite newer draft/source/result selection |
| graph | exact node/edge delta per submit/result accept/retry; no orphan placeholders |
| selection | submit、partial result、accept、retry、undo/redo each declare output |
| history | one user transaction has exact step count; async state observation is not accidental graph history |
| failure | error belongs to run/stage; retained successes and retry scope explicit |
| prototype boundary | no claim of real progress、billing、provider、output quality or remote save |
| runtime | focused desktop/mobile states, console/page/request errors and deterministic reset |

Historical Batch 23/24/33 verifiers remain bounded compatibility tracks. `LIBTV-VR-007` does not replace them until current source contract, accepted fixture, authorized implementation and a stable new verifier all exist.

`LIBTV-VR-007` 检查状态语义，`LIBTV-VR-015` 检查 completion 的 authority/收敛机制；二者互相组合但不互相替代。

## 12. 未决问题与停止条件

| Question | Needed evidence | Current action |
|---|---|---|
| source media version identity | current result/version DOM or business interface | design only |
| partial success semantics | disposable shot/process run | `BLOCKED_BY_FIXTURE` |
| retry/new run identity | source behavior or stable local mock contract | design only |
| segment reshoot result placement | disposable ready-video task | `BLOCKED_BY_FIXTURE` |
| long-video local recompute | source process graph interaction | `BLOCKED_BY_FIXTURE` |
| save/conflict projection | product/backend scope | `DEFER` / `OUT_OF_SCOPE` |
| billing/progress accuracy | real provider/task contract | `OUT_OF_SCOPE` |

No code may be added from this matrix without separate authorization for one bounded capability/state slice. In particular, this document does not authorize introducing a global task store, persistence layer, polling service or unified status enum.

## 13. 更新规则

When new evidence arrives:

1. add the dated source/fixture observation;
2. update only the affected capability, identity or axis claim;
3. preserve old clone facts and historical verifier provenance;
4. update fixture catalog, `LIBTV-VR-007`, traceability and the implementation Batch together;
5. keep Open Canvas facts and LibTV facts separately labeled;
6. run docs verification and use a path-scoped commit/push.
