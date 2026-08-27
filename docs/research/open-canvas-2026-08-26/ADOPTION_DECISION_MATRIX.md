# Open Canvas -> LibTV 机制采纳决策矩阵

> 状态：`CURRENT_RESEARCH` / `CURRENT_GUIDANCE`
>
> 研究基线：`ZeroLu/open-canvas@cf3a906bb8c35bb940d3267497e7f394b8f42582`
>
> 用途：把 Open Canvas 的源码启发转成可评审的 LibTV 原型决策。本文不是编码授权，不替代 LibTV 源站证据，也不允许直接复制上游视觉、数据结构或 provider 实现。

## 1. 本文解决什么问题

现有报告已经回答了 Open Canvas 的产品边界、源码结构和交互机制，但“值得借鉴”仍可能被误读成“可以移植”。后续 agent 在进入 LibTV 实施前，需要对每项机制同时回答：

1. Open Canvas 固定版本实际证明了什么；
2. LibTV 源站是否存在同类问题和独立证据；
3. 当前 clone 的差距位于视觉、交互、身份、graph transaction 还是 backend；
4. 应采纳方法、按 LibTV 语义改造、只保留研究、暂缓，还是明确拒绝移植；
5. 哪个 parity item、fixture 和 verifier 才能关闭该项；
6. 在缺少授权或证据时，agent 必须停在哪里。

本文是上述问题的唯一汇总入口。原始事实继续以 [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)、[`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md) 和固定 submodule 为准。

## 2. 决策词表

| 决策 | 含义 | 可以做 | 不能做 |
|---|---|---|---|
| `ADOPT_METHOD` | 上游解决问题的方法可作为 clone 内部设计原则 | 写合同、纯逻辑边界、fixture 和验收；获授权后按当前架构实现 | 复制上游组件、像素、字段名或 store 形状，并宣称 source parity |
| `ADAPT_TO_LIBTV` | 上游机制有价值，但身份、状态或生命周期必须由 LibTV 证据重定义 | 先建 LibTV source contract，再做最小 slice | 用上游缺省语义填补 LibTV 未知行为 |
| `RESEARCH_ONLY` | 当前只有启发或线索，没有足够 LibTV 证据进入设计 | 继续只读取证和问题建模 | 进入实现 backlog，或把营销/源码能力写成 clone 已支持 |
| `DEFER` | 机制合理，但不属于当前高价值前端 fidelity 路径 | 记录触发条件和依赖 | 借局部 UI 工作顺手扩大状态面 |
| `REJECT_TRANSPLANT` | 上游做法与当前产品边界、安全要求或 LibTV 事实冲突 | 保留反例和拒绝原因 | 直接接入或包装后改名接入 |

决策对象是“迁移方式”，不是对 Open Canvas 质量的评价。`ADOPT_METHOD` 也仍需要编码授权。

## 3. 决策规则

### 3.1 证据优先级

```text
LibTV current source evidence
  -> LibTV cross-cutting/component contract
  -> current clone runtime and fixture
  -> Open Canvas fixed-source mechanism
  -> clone-only decision
```

Open Canvas 只能帮助回答“怎样把问题建模得更稳”，不能回答“LibTV 源站具体怎样表现”。精确动作、文案、尺寸、坐标、关闭路径和 graph 副作用始终由 LibTV 证据决定。

### 3.2 进入实施候选的最小条件

一项机制只有同时满足以下条件，才可从研究进入待授权 slice：

- 有 `OC-*` 或 `OC-TR-*` 证据锚点；
- 有独立的 LibTV `SOURCE_FACT` 或明确的 clone-only correctness 问题；
- 已映射到一个 `LIBTV-PAR-*`，或说明为什么只是基础设计输入；
- 有可重复且无远端副作用的 `LIBTV-FIX-*`；
- 已定义 replacement verifier 或窄验证合同；
- 用户明确授权修改代码；
- 目标文件没有被其他开发者并行修改，或能在不覆盖 WIP 的前提下协作。

任一条件缺失时，保持文档态。共享源站 `LIBTV-FIX-SOURCE-SHARED-01` 只能提供只读事实，不是实现后回归 fixture。

## 4. 采纳总矩阵

| ID | Open Canvas 机制 | 决策 | LibTV 的实际用途 | 当前治理映射 | 关闭闸门 |
|---|---|---|---|---|---|
| `OC-ADOPT-001` | measured node + live viewport 的 screen anchor | `ADOPT_METHOD` | 用统一几何模型诊断节点上下浮层，但保留 LibTV 顶部 screen-space、底部 flow-space 两条合同 | `OC-018`、`OC-TR-001`；`LIBTV-PAR-001`、`LIBTV-PAR-002`；`LIBTV-FIX-LOCAL-IMAGE-01`；`LIBTV-VR-001`、`LIBTV-VR-002` | 当前 source 公式、动作集合、多 zoom、边缘裁切和 selection lifecycle 全部由同 frame verifier 证明 |
| `OC-ADOPT-002` | typed input buckets 与 provider projection 分离 | `ADAPT_TO_LIBTV` | 分开 graph edge、reference role、Prompt mention、media version 和最终请求投影 | `OC-004/005`、`OC-TR-002`；`LIBTV-PAR-003`、`LIBTV-PAR-009`；`LIBTV-VR-003..005`、`LIBTV-VR-007` | 先有 LibTV typed identity/session 合同；没有 disposable fixture 时不得验证提交链 |
| `OC-ADOPT-003` | node、run、save/conflict 状态分层 | `ADAPT_TO_LIBTV` | 避免把长视频 process、节点媒体状态、局部任务和画布保存反馈压成一个 `status` | `OC-010/025`、`OC-TR-003`；`LIBTV-PAR-009`；`LIBTV-VR-007` | 取得 process/result 生命周期证据；prototype 不伪造真实进度、费用、保存后端或 conflict |
| `OC-ADOPT-004` | versioned serialized graph + validation | `ADOPT_METHOD` | 为 graph snapshot、迁移、非法边、node data registry 和 fixture schema 提供边界设计输入 | `OC-003`；`LIBTV-PAR-008`；`LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` + `NODE-DATA-01`；`LIBTV-VR-010/012` | 五层/V1/strict load 与 11-type V0 registry/aggregate/media 设计已完成；runtime 未实现，persistence 保持 deferred |
| `OC-ADOPT-005` | 结构化子图复制、ID map、仅恢复内部边 | `ADAPT_TO_LIBTV` | 改善 duplicate/copy 的身份重写与 subgraph closure 设计 | `OC-024`、`OC-TR-004`；`LIBTV-PAR-008`；`LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` + `NODE-DATA-01`；`LIBTV-VR-011/012` | named command、parent/edge/reference/aggregate/media/placement/transaction 设计已完成；runtime 未集中，clipboard/Option-drag 仍 blocked；不能套用 Open Canvas payload |
| `OC-ADOPT-006` | connection type compatibility、方向归一化和 DAG guard | `ADOPT_METHOD` | 为 duplicate/dangling/self-loop/cycle guard 提供纯逻辑参考；LibTV 普通连接 path 的 pair/DFS/type guard 已有静态 bundle 证据 | `OC-003`、`OC-EQ-003`；`LIBTV-PAR-008`；`LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01`；`LIBTV-VR-009` | Batch 57 已完成 local structural runtime、fixture 和 recorded verifier；Reference/domain/其他 entry point/source invalid lifecycle 仍待授权或 disposable fixture；不改变 edge flow 视觉 |
| `OC-ADOPT-007` | Quick Add 同时保存 screen menu anchor 与 flow drop point | `RESEARCH_ONLY` | 作为坐标域分离的案例，帮助评审 Add Node/connection 菜单 | `OC-021`；当前无独立 parity item | 只有 LibTV 源站证明同类入口后才能建 slice；不得把上游落点或 clamp 规则移植过来 |
| `OC-ADOPT-008` | pending connection -> create node -> create edge transaction | `RESEARCH_ONLY` | 作为“一个用户动作、多个 graph mutation”的原子性案例 | `OC-022/023`；可为未来 `LIBTV-PAR-008` 提供测试思想 | 先取得 LibTV 悬空连线/新增节点事实；当前 `<Handle>` 仍是真实连接 affordance |
| `OC-ADOPT-009` | media output history 与当前候选分离 | `ADAPT_TO_LIBTV` | 帮助区分 Seedance candidate、派生媒体、重拍结果、被选版本和 source node | `OC-TR-002/003`；`LIBTV-PAR-009`；`LIBTV-VR-007` | 建立 `source/mediaVersion/operation/range/candidate/result` 身份合同与 disposable process fixture |
| `OC-ADOPT-010` | capability-driven model registry 与表单投影 | `ADAPT_TO_LIBTV` | 将模型能力、可见字段和请求投影分层，减少散落条件判断 | `OC-005/006/009`；Seedance gap/crosswalk | 必须以 LibTV 当前模型菜单和参数证据为真相；registry 可见不等于 runner 可执行 |
| `OC-ADOPT-011` | revision、dirty、debounced save、conflict | `DEFER` | 作为未来本地快照或协作保存的状态参考 | `OC-010/011/025`；`LIBTV-PAR-010`、`LIBTV-PAR-012` 边界 | 只有当前原型明确需要刷新恢复、并发保存或协作时重新立项；不得伪装真实云保存 |
| `OC-ADOPT-012` | local file/KV persistence | `DEFER` | 仅供研究 fixture、版本迁移和损坏恢复的设计比较 | `OC-011/012`；当前 prototype boundary | 需要独立 persistence 合同、reset 方案和数据迁移计划；不能把 Director storage 推广到普通画布 |
| `OC-ADOPT-013` | BYOK/provider adapter/current runner | `REJECT_TRANSPLANT` | 当前只用于识别“UI registry 不等于可执行能力”的风险 | `OC-006..009/013/016`；`LIBTV-PAR-012 OUT_OF_SCOPE` | 需要新的后端、密钥、上传、计费和安全授权；不能接入上游 cookie/key 方案 |
| `OC-ADOPT-014` | provider 设置向导、导入 JSON、空画布 onboarding | `RESEARCH_ONLY` | 作为空态任务分流和渐进披露的产品参考 | `OC-014/015`；当前无 LibTV parity 证据 | 先确认 LibTV 空画布和首访 source contract；不把 Open Canvas 产品叙事复刻到 LibTV |
| `OC-ADOPT-015` | Open Canvas 的视觉皮肤、Panel 层级和具体尺寸 | `REJECT_TRANSPLANT` | 只作为源码定位线索，不作为 LibTV 视觉输入 | `OC-017/018/020` | LibTV 视觉只能由当前 DOM、computed style、截图和组件合同决定 |
| `OC-ADOPT-016` | 集中 node/edge/selection delete、incident-edge cleanup 和 conflict no-op | `ADAPT_TO_LIBTV` | 借鉴 named deletion、zero-mutation gate 和一次提交；扩展为 LibTV relation inverse index、aggregate repair、UI/resource result | `OC-003`；`LIBTV-PAR-008`；`LIBTV-FIX-LOCAL-GRAPH-DELETE-01`；`LIBTV-VR-013` | delete matrix/design 已完成；runtime、derived/shot/process/Director/media semantics 和 disposable source fixture 未完成；不得只移植 incident-edge filter |
| `OC-ADOPT-017` | store local guard + serialization/save/API validation + revision/server-patch 分层 authority | `ADOPT_METHOD` | 为 LibTV graph ingress 定 T0-T5；将 transport、proposal、planned command、restore 和 remote patch 分开；同时保留上游 clipboard/framework delta 反例 | `OC-TR-010`；`DEC-030`；`LIBTV-PAR-008`；`GRAPH-ENTRYPOINT-01`；`LIBTV-VR-014` | static/design complete；runtime 仅 connection island protected；不得移植 autosave/conflict/persistence，也不得把上游 partial ingress 当正确模板 |
| `OC-ADOPT-018` | descriptor/run/runId polling/server patch 控制面与 stale-result 反例 | `ADAPT_TO_LIBTV` | 为 process/result completion 定 operation/run/result/source-version identity、freshness、field ownership、idempotent projection 和 resource transfer | `OC-026..030`、`OC-TR-011`；`DEC-031`；`LIBTV-PAR-009`；`ASYNC-INGRESS-01`；`LIBTV-VR-015` | design complete/runtime missing；只借分层与 run-keyed observation，不移植 generic patch、URL identity、provider、persistence 或非原子 write flow |
| `OC-ADOPT-019` | functional current-state React Flow callback + generic non-select change 反例 | `ADAPT_TO_LIBTV` | 借 current active-canvas snapshot；细化为 whole-batch T0 selection、T1 node position/passive measurement 与 T2/T3 semantic command routing | `OC-031..034`、`OC-TR-012`；`DEC-032`；`LIBTV-PAR-008`；`REACT-FLOW-CHANGES-01`；`LIBTV-VR-016` | design complete/runtime partial；不移植 generic add/remove/replace、Open Canvas conflict 产品语义、node types、resize/reconnect UX |
| `OC-ADOPT-020` | list summary + URL document + hydrate owner + delete-run cleanup + stale save 反例 | `ADAPT_TO_LIBTV` | 为 in-place LibTV 多画布定义 registry/document/history/session/external owner、switch manifest、canvas generation 和 explicit async destination | `OC-035..039`、`OC-TR-013`；`DEC-033`；`LIBTV-PAR-008/011`；`CANVAS-LIFECYCLE-01`；`LIBTV-VR-017` | design complete/runtime partial；不移植 list/URL visual、persistence/revision/conflict/final-delete policy；source fallback/panel/resource decisions open |
| `OC-ADOPT-021` | global toast + node status/error + save/conflict surface + field error/pending，以及 localized message/owner 反例 | `ADAPT_TO_LIBTV` | 为 LibTV command outcome 定 disposition/reason/primary surface/owner/clear-retry-dedupe；保留 local prototype honesty 与 Director persistent surface | `OC-040..045`、`OC-TR-014`；`DEC-034`；`LIBTV-PAR-004/008..011`；`COMMAND-FEEDBACK-01`；`LIBTV-VR-018` | design complete/runtime partial；不新增 global toast、不复用 FrameOS toast、不复制 skin/message/save/provider；exact invalid style/timeout source-blocked |
| `OC-ADOPT-022` | selected flags + editable guards + local editor ownership + Radix focus delegation，以及 conflict gate/weak Escape/default key handler 反例 | `ADAPT_TO_LIBTV` | 为 LibTV 定义 validated node/edge/primary selection、focus zone、command-context precedence、single-layer Escape 和 focus return；保留 route/store 隔离 | `OC-046..052`、`OC-TR-015`；`DEC-035`；`LIBTV-PAR-004/007/008/011`；`SELECTION-FOCUS-CONTEXT-01`；`LIBTV-VR-019` | design complete/runtime partial；不移植 Radix/global modal manager、不复制 selected flags/conflict gate/weak Escape；exact source multi-select/edge/focus behavior partial |
| `OC-ADOPT-023` | screen/flow dual anchor + actual host conversion + live/stable viewport + entry-specific placement，以及 permissive normalize/clamp/gesture/drop 反例 | `ADAPT_TO_LIBTV` | 为 LibTV 定义 six-domain、actual host/epoch、viewport phase、generation-bound gesture/placement、resize reconciliation 和 exact history/selection composition | `OC-053..060`、`OC-TR-016`；`DEC-036`；`LIBTV-PAR-001/002/007/008/011`；`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01`；`LIBTV-VR-020` | design complete/runtime/source parity partial；不移植 Quick Add/drop/pending connection、menu/zoom/pan/overlay/persistence；exact source add/fit/resize behavior remains gated |
| `OC-ADOPT-024` | validation/probe/upload/normalized descriptor/digest reuse，以及 placeholder-first、classifier drift、sequential partial commit、autosaved running 和无 cleanup/freshness 反例 | `ADAPT_TO_LIBTV` | 为 LibTV 定义 media intent、local byte/lease、stable asset、node reference、provisional/semantic projection、cohort transaction 和 reachability release | `OC-061..070`、`OC-TR-017`；`DEC-037`；`LIBTV-PAR-008/009/010/011/014`；`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`；`LIBTV-VR-021` | design complete/runtime missing or partial/source parity partial；不移植 provider/storage/MIME/size/visual、placeholder-first 或 partial history；无 backend 只允许 honest local preview/unavailable |

## 5. 高价值采纳路径

### 5.1 立即可用于文档和评审

以下内容不需要编码授权即可继续深化：

1. `OC-ADOPT-001`：用坐标域和 anchor owner 评审 `PAR-001/002`，但所有数字回到 LibTV 合同；
2. `OC-ADOPT-002`：维护已经完成的 Auto Link typed identity/session/fixture 合同，等待运行 fixture 授权；
3. `OC-ADOPT-004..006/016/017/019..024`：使用已经完成的 graph invariant/case 表、四份 component contracts、delete matrix、[`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、[`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、[`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md) 和相应 dated static audit；按 verifier 分开维护 runtime maturity，保持 persistence/provider deferred，继续取得 Reference、导入/批量/同步、invalid lifecycle/feedback、Option-drag、resize/reconnect、canvas fallback/panel/resource、feedback timeout/placement、multi-select/edge/focus、source add/fit/resize、source upload/progress/cancel/replace 和 cascade/detach source/product 决定；
4. `OC-ADOPT-003/009/018`：为 `PAR-009` 拆开 source、candidate、result、run 和 save 状态，并以 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) 约束 completion freshness、field/history/resource ownership；
5. `OC-ADOPT-010`：建立“模型 UI 能力 / 请求投影 / 实际 runner”三层审计表。

这些工作只能产出设计和验证合同，不能修改 `src/` 或测试脚本。

### 5.2 获授权后最先落地的借鉴

Open Canvas 对当前第一优先级 `PAR-001` 的价值很窄：借鉴“同一套测量输入和坐标推导”的方法，不借它的 overlay DOM。最小 slice 仍由 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) 决定，并由 `LIBTV-VR-001` 替换历史图片标准态断言。

Auto Link 和 graph transaction 不应跟随该视觉 slice 一起实现。前者要先完成 typed identity/session 设计，后者要先定义 compatibility 与 history 规则。

### 5.3 必须等待 fixture 的借鉴

- 长视频、逐帧拉片、片段重拍的 process/result 状态；
- ready-video source toolbar 和 active action；
- 有效元素编辑 record、dirty image save、图层分离；
- 真实 provider 请求、上传、轮询、费用和结果回写。

没有 disposable fixture 时，继续标记 `BLOCKED_BY_FIXTURE` 或 `OUT_OF_SCOPE`，不能用 Open Canvas 可运行代码替代 LibTV 未知事实。

## 6. 明确拒绝的移植方式

| 反模式 | 为什么错误 | 正确处理 |
|---|---|---|
| 复制 `canvas-studio-shell.tsx` 的 overlay DOM/CSS | 上游只证明一种组织方法，LibTV 的上下浮层位于不同坐标域且允许自然裁切 | 读取 LibTV current contract，只借统一测量与推导思想 |
| 用 Open Canvas input bucket 直接定义 Auto Link token | bucket 是执行输入分类，LibTV mention 还包含 stable node ID、media type 和 ordinal | 先定义 LibTV identity，再在边界层投影 |
| 将所有 `status` 收敛成上游枚举 | LibTV 过程节点、媒体 ready/failed、候选和保存反馈不是同一生命周期 | 分别定义 node/run/result/save 状态和 owner |
| 复制 Open Canvas generic server node patch | fixed path 不比较 expected current run/source version/field owner，run terminal 与 graph projection 也非原子 | 只借独立 authority；先判 stale/duplicate，再以 operation-specific full plan 幂等落图 |
| 把上游子图 clipboard payload 当成 LibTV schema | LibTV 有 group、parent-child、derived media 和历史 candidate 语义 | 只借 ID map 与内部边闭包，重新定义 payload |
| 因上游有 provider registry 就在 clone 宣称支持模型 | registry、设置 UI、legacy route 和 current runner 范围并不相等 | 同时证明 UI、adapter、request、polling 和 result write-back |
| 复制非 HttpOnly provider key cookie | 与当前原型安全和 backend 边界冲突 | 保持 `PAR-012 OUT_OF_SCOPE`，另立安全设计 |
| 用 Open Canvas local-first 保存填补 LibTV 保存未知 | 产品语义、账号、协作和 reset 均未对齐 | 仅在有明确产品需求时重新立项 |
| 看到 Quick Add/pending connection 就改 LibTV Handle | 当前没有 LibTV 同类源站证据，且 Handle 是真实拖拽 affordance | 保留现有连接入口，先研究 source |
| 把 React Flow `selected` flags 当成完整 selection authority | node/edge flags 不能单独表达 primary、active canvas、stale ID 与 surface context | 先归一化 validated active selection，再向 React Flow 投影 |
| 复制 Open Canvas conflict gate 或弱 Escape handler | 单个 guard/handler 不构成 command-context precedence，也不能保证一次只退一层 | 使用具名 context resolver、declared dispatch result 和 single-layer unwind |
| 因 Open Canvas 使用 Radix 就引入全局 modal manager | 上游库只证明局部 focus containment/return 方法，不证明 LibTV 产品层级 | 保留现有 surface owner；按 LibTV 合同声明 acquire/contain/return/fallback |
| 复制 Open Canvas Quick Add/drop/pending connection 或其 menu/zoom 数字 | 双锚点和 live/stable 是空间方法，不证明 LibTV 有相同入口、视觉或产品手势 | 使用 actual host/typed domain/generation owner；source 未证入口保持 absent/honest |
| 用 viewport normalize fallback 或 surface clamp 修复无效 graph anchor | 这会把坏输入静默变成有效坐标，或把 UI 可见性混入 graph placement | strict finite/owner validation；screen anchor 与 flow anchor 独立 |
| 把 Open Canvas upload route、digest key、accept/size 直接当 LibTV 上传规格 | 上游只证明技术路径；当前 LibTV source 尚未暴露 limits、storage、progress、cancel 或 durability | 只采纳 validate/probe/materialize/descriptor 分层；产品数字和后端保持 source-blocked/out of scope |
| 把 source upload、generated history、material library 和 asset manager 合并为一个素材 picker | 四个 surface 的 identity、owner 和副作用不同；clone 当前文案还存在历史漂移 | 使用具名 entry profile，分别声明 attach/create/register/materialize 和 history policy |
| 把 object URL 当 stable URL 保存或因 node delete 立即 revoke/delete asset | object URL 是 instance lease；资源可能仍由 history、clipboard、editor、operation 或 asset registry 引用 | 建 resource ledger，显式 transfer/release，zero reachability 后 exact-once cleanup |

## 7. 决策更新协议

每次新研究或实施只更新受影响的行：

1. 新增或修订 `OC-*` / `LIBTV-TR-*` 证据；
2. 更新本表决策、理由、parity/fixture/verifier 映射；
3. 若进入 implementation-ready，另建单 slice 计划和验收，不在本表写代码步骤；
4. 若实现完成，链接对应 Batch `IMPLEMENTATION.md` 和 verifier 记录，但保留原决策 provenance；
5. 若 Open Canvas submodule 更新，建立新的版本差异审计，不静默移动本研究基线；
6. 运行 `python3 scripts/verify-docs.py` 和 `git diff --check`，只提交自己的文档路径。

## 8. 当前结论

Open Canvas 对本项目最有价值的是六类工程方法：坐标域/空间 owner 显式化、稳定身份与请求投影分离、状态生命周期分层、结构化 graph transaction、current owner 收敛、media bytes/asset/reference/resource lease 分权。它最不适合作为 LibTV 视觉、产品文案、provider 能力、上传规格和保存语义的替代来源。

因此，后续复刻应把它当作“设计评审器”：用上游实现暴露当前 clone 可能遗漏的状态、身份和原子性问题，再回到 LibTV 源站决定最终行为。任何没有 LibTV 证据、fixture、verifier 和授权的机制，都停留在研究文档中。
