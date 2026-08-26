# Open Canvas 启发下的下一阶段证据获取计划

> 状态：`CURRENT_RESEARCH` / `CURRENT_GUIDANCE`
>
> 当前授权：文档和安全只读研究 `GO`；共享 LibTV 项目写入、clone 编码、verifier 修改和 submodule pointer 更新 `NO-GO`
>
> 用途：把当前剩余的证据缺口组织为可执行、可停止、可交接的研究队列。本文不维护第二套 parity 优先级，也不把 Open Canvas 机制当成 LibTV 源站事实。

## 1. 为什么还需要这份计划

现有文档已经分别回答了：

- Open Canvas 固定版本证明了什么；
- 哪些机制应采纳、改造、暂缓或拒绝；
- 获授权后的 LibTV slice 如何按七层交接；
- Auto Link、graph、process/result 和 model capability 的设计合同是什么。

剩余问题不再是“怎样设计一套更完整的抽象”，而是“还缺哪条 LibTV 或上游证据，怎样在不污染共享项目的前提下取得”。如果没有统一队列，后续 agent 容易重复写概述、把 design spec 误当 runtime fixture，或在共享源站试探会产生副作用的行为。

本计划只负责证据获取顺序和停止条件。当前排期仍以 [`../LIBTV_UIUX_PARITY_BACKLOG.md`](../LIBTV_UIUX_PARITY_BACKLOG.md) 为准；事实 authority 仍位于对应 source/component/research 文档。

## 2. 队列状态词表

| 状态 | 含义 | 当前允许动作 |
|---|---|---|
| `READY_READ_ONLY` | 已有共享登录态或静态资产，可在不写入的前提下继续 | DOM/computed style、已有节点选择、viewport/zoom、菜单 disclosure、bundle/source 读取 |
| `STATIC_FIRST` | 先用当前 bundle、DOM 或 clone 静态审计缩小问题 | 只读定位分支、类型、selector、文案和不可达路径 |
| `BLOCKED_BY_DISPOSABLE_SOURCE` | 必须输入、切换、连线、生成、重试或保存才能回答 | 只补接收规格；等待独立可丢弃源站项目和明确授权 |
| `TRIGGERED_BY_UPSTREAM_CHANGE` | 只有出现新的 immutable upstream SHA 才有工作 | 保持当前 baseline；候选出现后执行版本影响协议 |
| `CLOSED_AS_DESIGN` | 文档设计已经足够，不应继续以“缺设计”为由扩写 | 维护既有 authority，等待 fixture/授权或新证据 |
| `PARTIAL_RECORDED` | 一个有界场景已有新日期证据，但队列的其他 viewport/state 仍未覆盖 | 引用已记录结果，只补未覆盖场景，不重复测同一状态 |

`READY_READ_ONLY` 不等于可以操作任意控件。只要一个动作可能改变 Prompt、模型参数、偏好、graph、任务、媒体、账户或保存状态，就立即转为 `BLOCKED_BY_DISPOSABLE_SOURCE`。

## 3. 总队列

| ID | 证据问题 | 当前状态 | 价值 | 直接解锁/更新 |
|---|---|---|---|---|
| `OC-EQ-001` | 当前 LibTV 页面壳、入口、标准双浮层和可见 surface 是否发生新漂移 | `PARTIAL_RECORDED`：41% standard image；其余场景仍 `READY_READ_ONLY` | 高 | `LIBTV-PAR-005`、`OC-BP-001/002` 的 `L0` |
| `OC-EQ-002` | 非 Seedance 2.5 模型逐项有哪些可见 controls，哪些只存在于菜单/catalog | `PARTIAL_RECORDED`：35-row catalog；per-model controls 未选择 | 中高 | `OC-BP-006`、model capability matrix |
| `OC-EQ-003` | LibTV 是否允许 duplicate edge、parallel handle edge、self-loop、cycle，以及 Handle 类型兼容是什么 | `PARTIAL_RECORDED`：普通连接 path 的 bundle/DOM static guard 已记录；交互部分 `BLOCKED_BY_DISPOSABLE_SOURCE` | 高 | `OC-BP-004`、`LIBTV-GI-004..007` |
| `OC-EQ-004` | Auto Link 的输入、IME、单项/全量接受、失败回滚和 stale result 当前怎样运行 | `BLOCKED_BY_DISPOSABLE_SOURCE` | 高 | `OC-BP-003`、`LIBTV-VR-003..005` |
| `OC-EQ-005` | ready-video、逐帧拉片、片段重拍、长视频的 partial/retry/result replacement 生命周期 | `BLOCKED_BY_DISPOSABLE_SOURCE` | 高 | `OC-BP-005`、`LIBTV-VR-006/007` |
| `OC-EQ-006` | Open Canvas 新 commit 是否改变既有 claim、pattern、adoption 或 LibTV 启发 | `TRIGGERED_BY_UPSTREAM_CHANGE` | 条件性高 | `OC-TR-*`、`OC-ADOPT-*`、baseline decision |

这六项是当前固定研究基线下的完整证据队列。没有新的 source drift、fixture 或 upstream SHA 时，不另建同主题总览。

## 4. `OC-EQ-001`：LibTV source freshness

### 4.0 最新有界结果

2026-08-27 已在共享只读项目的既有选中态记录 41% standard image：`1092.5x49` toolbar、`660x191` panel、node-center anchor、`10 + 24 * zoom`、`16 * zoom` 和自然左侧裁切均未漂移，见 [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](LIBTV_SOURCE_FRESHNESS_2026-08-27.md)。该结果不覆盖 selection transition、多 zoom、mobile 或 active tool，因此本队列保持 `PARTIAL_RECORDED`。

### 4.1 研究问题

确认新日期下以下只读事实是否仍成立：

1. page shell、侧栏、底栏和主要入口的存在性与层级；
2. 已有图片节点选择后标准顶部工具条和底部面板是否同时挂载；
3. 当前动作 label/order、toolbar/panel rect、node center 和 zoom 关系；
4. 空白点击、切换已有节点、fit view 和安全 zoom 后的 selection/surface 生命周期；
5. desktop/mobile 下自然裁切、virtualization 和前台 overlay 是否有漂移。

### 4.2 安全方法

从 [`../LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](../LIBTV_SOURCE_FRESHNESS_REINSPECTION.md) 开始，复用已打开的登录态页面和现有节点。允许读取 DOM、computed style、可访问树、网络已加载 bundle 和截图；允许选择已有节点、点击空白、使用只改变本地 viewport 的 zoom/fit view。

禁止输入文本、切换 Auto Link、选择模型、拖动节点、创建/删除连接、打开可能先创建派生节点的动作、生成、上传、保存、下载或修改账户状态。

### 4.3 最小证据包

- 日期、URL、viewport、zoom、登录态和 fixture identity；
- 结构化 rect/action/visibility JSON；
- source screenshot 与逐图解释；
- 对旧 claim 的 `UNCHANGED` / `DRIFTED` / `UNKNOWN` 判定；
- 只更新受影响的 overlay/component/traceability authority。

### 4.4 退出与停止

得到同一 frame 的 node/toolbar/panel 几何和动作集合即可退出。若目标节点不存在、需要 graph mutation 才可构造、或任何动作出现写入风险，记录 `BLOCKED_BY_SOURCE_FIXTURE` 后停止。

## 5. `OC-EQ-002`：非 Seedance 模型能力

### 5.0 最新有界结果

2026-08-27 已从现有 failed video 的只读模型 dialog 记录 35 个 loaded DOM row、14/21 current-context style split、全部 description 和 selected alias，见 [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md)。本轮没有选择模型，因此逐模型 controls 仍为 `UNKNOWN_NOT_SELECTED`，队列保持 `PARTIAL_RECORDED`。

### 5.1 研究问题

Open Canvas 的 registry/current runner 漂移提醒本项目：模型出现在菜单中，不等于当前节点、request descriptor 或真实 runner 支持它。需要逐模型区分：

- source-visible label、description、estimate、premium 标记；
- 在当前节点上下文中可见的 mode、ratio、resolution、duration、audio、count 和 helper；
- control 是模型 capability、模式 capability 还是通用面板字段；
- clone 是否已有对应 UI state；
- 只能形成 descriptor，还是存在真实 adapter/runner 证据。

### 5.2 静态优先方法

第一步只读当前 DOM、已加载 bundle 和既有模型菜单证据，不选择新模型，不改变共享项目参数。只有 bundle 分支能明确绑定 model ID 与 control 条件时，才记为 `SOURCE_FACT`；从 label、estimate 或 Open Canvas registry 推测的能力只能记为 `INFERENCE`。

若必须切换模型才能观察字段变化，停止并登记 disposable source parameter fixture，不在共享项目试探。

### 5.3 最小证据包与退出

按 [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) 现有列追加逐模型行，并为每个值标注 `DOM`、`BUNDLE`、`ARTICLE`、`CLONE` 或 `UNKNOWN`。目标不是补齐营销模型大全，而是明确哪些 controls 可以进入后续 UI 合同、哪些仍不能推出 runner。

当当前静态资产不再能增加模型特有事实时退出；未知项保持 `UNKNOWN`，不以通用 Seedance 控件或 Open Canvas capability 填空。

## 6. `OC-EQ-003`：Graph compatibility source decisions

### 6.1 研究问题

只处理 [`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md) 中仍为 `SOURCE_DECISION_REQUIRED` 的四类问题：

| Invariant | 必须确认 | 不能借 Open Canvas 推出 |
|---|---|---|
| `LIBTV-GI-004` | duplicate/parallel edge identity 是否包含 handles | 上游去重规则 |
| `LIBTV-GI-005` | self-loop 接受、拒绝或 UI 不可构造 | 上游 DAG rejection |
| `LIBTV-GI-006` | directed cycle 接受、拒绝或仅某些 node type 禁止 | 上游 acyclic graph |
| `LIBTV-GI-007` | source/target Handle、node type 和方向兼容表 | 上游五类 node compatibility |

### 6.2 两阶段方法

**静态阶段**：从当前 LibTV bundle、DOM Handle 元数据、edge validation 分支和 clone runtime catalog 中寻找显式 guard。只记录可追溯条件，不把“未找到 guard”写成“源站允许”。

**交互阶段**：只有取得独立可丢弃源站 project 后，才通过最小 subgraph 测试 duplicate、parallel、self-loop 和 three-node cycle。每个动作前后记录 nodes/edges/selection/history/toast，并在单场景后销毁 fixture。

### 6.3 最新静态结果

2026-08-27 已完成当前 production bundle 和可见 DOM 的静态阶段，见 [`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md) 与 [结构化 JSON](libtv-graph-compatibility-static-audit-2026-08-27.json)。当前连接 validator 已直接暴露：

- 同向或反向的相同节点对会被 pair guard 拒绝，且 guard 不比较 Handle，因此普通连接路径不会因为改 Handle 而产生 parallel edge；
- programmatic pair 显式拒绝 `sourceId == targetId`，普通非 Reference source 也会进入 DFS self-loop/cycle guard；
- 候选 edge 加入 adjacency 后执行递归 DFS，普通有向环会被拒绝；
- 两侧 Handle 可以发起连接，但从 `target` 发起的手势会被归一化为标准 `source -> target`；最终允许与否还由 LibTV action/type/model/capacity matrix 决定。

这些是 `SOURCE_STATIC_EVIDENCE`，不是完整 source contract。Reference 例外、导入/批量/同步入口、invalid feedback 和 history/no-residue 仍需 disposable source fixture；因此不关闭 `GI-004..007`，也不授权修改 clone。

### 6.3 退出与停止

静态证据可缩小某项时，更新对应 `GI/GC` 行并标注 `STATIC_RECORDED`；无法关闭则保持 `SOURCE_DECISION_REQUIRED`。共享项目禁止拖 Handle 或创建测试边。四项决定没有全部取得，不阻塞 clone 侧结构校验合同和授权切片规划，但阻塞 source-parity 宣称、Reference/domain exception 与全入口一致性的实施。

### 6.4 Clone-side design handoff

在不增加 source interaction 的前提下，2026-08-27 已完成 [`LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)：

- 将 source static guard 转为 raw/normalized connection、result/reason 和 transaction no-op/atomicity 设计；
- 为 `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` 定义 A/B/C topology、逐场景 fresh Page reset 和禁止用 undo 充当 teardown；
- 为 `LIBTV-VR-009` 拆出 pure contract 与 focused browser 两层；
- 将 Reference、import/batch/sync 和 source invalid feedback 保持为显式 `unknown`/fixture blocker。

这关闭的是 clone 设计缺口，不关闭 `OC-EQ-003` 的交互证据问题，也不授权实现 fixture、validator 或 verifier。

## 7. `OC-EQ-004`：Auto Link disposable source evidence

### 7.1 前置接收条件

必须先有符合 [`../LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md) 的 `LIBTV-FIX-SOURCE-AUTOLINK-01`：独立可丢弃 project、至少两个 connected/reference candidates、允许输入 Prompt、可恢复或销毁、明确不会影响共享账户资产。

### 7.2 场景顺序

1. preference/visibility，不接受候选；
2. ghost lifecycle：input、delay、edit、blur、Escape；
3. click/Tab 单项接受与 Shift+Tab 全量接受；
4. IME composition 和 stale async result；
5. connected/reference candidate identity 与 ordinal reorder；
6. unconnected candidate 的 connect + mention success；
7. connection failure 的 badge/edge/reference rollback。

每个场景独立记录初始/最终 Prompt、mention token、reference roles、edges、selection 和错误反馈。不得把多个状态串在同一不可复位会话中。

### 7.3 退出与停止

场景只负责补 source contract，不验证 clone。遇到真实生成、上传、付费、账户偏好扩散或无法恢复的 graph mutation，立即停止。证据完成后更新 `LibTVAutoLink.contract.md`、`LIBTV_AUTOLINK_STATE_MATRIX.md`、traceability 和 verifier replacement；不自动获得编码授权。

## 8. `OC-EQ-005`：Ready-video 与 process/result 生命周期

### 8.1 前置接收条件

至少需要以下之一：

- `LIBTV-FIX-SOURCE-VIDEO-READY-01`：独立、已知 duration/version 的 ready video，可安全打开工具并丢弃；
- `LIBTV-FIX-SOURCE-PROCESS-01`：可观察 pending/failed/partial/success/retry 的独立任务或用户明确批准的 bounded source mock。

共享项目中的 failed video、文章截图和 clone 的 12 节点/22 边过程图都不能替代这两个 fixture。

### 8.2 证据轴

所有观察按 [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md) 的五轴记录：

1. authoring state；
2. node availability；
3. run state；
4. result state；
5. save state。

同时记录 source node、media version、operation、time range、run、result/version 六类 identity，重点观察 partial result、retry、stale input、局部重算、候选接受和结果替换。

### 8.3 退出与停止

不得为了得到 running/failed 状态而在共享源站触发真实任务。费用、进度百分比、轮询频率和结果时间只有直接证据时才能记录，且不作为 SLA。证据完成只允许升级 `L0` 和 fixture/verifier 规划；真实 runner、计费、保存后端仍是 `OUT_OF_SCOPE`。

## 9. `OC-EQ-006`：Open Canvas upstream impact diff

### 9.1 触发条件

只有出现以下事件之一才启动：

- 用户指定新的 Open Canvas immutable SHA；
- 上游发布与本项目关注路径直接相关的新版本；
- 既有 claim 的文件路径消失，需要确认是否重构；
- 用户明确要求评估是否更新 submodule baseline。

### 9.2 执行方法

严格使用 [`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](UPSTREAM_VERSION_IMPACT_PROTOCOL.md)：先比较 candidate SHA，不移动当前 pointer；逐项评估 claim、pattern、adoption、LibTV impact 和 runtime；最后给出 `KEEP_PINNED`、`ADD_SECOND_BASELINE`、`UPDATE_BASELINE` 或 `REJECT_CANDIDATE`。

候选源码变化不能自动改写 LibTV source contract。即使建议 `UPDATE_BASELINE`，submodule pointer、研究文档和 LibTV 代码也必须分 commit，并分别取得所需授权。

## 10. 执行波次

### Wave A：当前可主动推进

1. `OC-EQ-001`：按只读 freshness checklist 建立新日期基线；
2. `OC-EQ-002`：只用当前 DOM/bundle 扩展模型能力证据；
3. `OC-EQ-003`：先做 bundle/Handle 静态分支审计（已完成）；

Wave A 的任何一项一旦需要输入、选择会写入的参数或 graph mutation，就停止在静态证据，不自动进入 Wave B。

### Wave B：等待 disposable source fixture

1. `OC-EQ-004`：Auto Link input/IME/accept/rollback；
2. `OC-EQ-005`：ready-video toolbar 与 process/result lifecycle；
3. `OC-EQ-003` 的真实 graph compatibility 场景。

Wave B 必须逐 fixture 授权，不能用一个“可丢弃项目”笼统授权所有生成、上传、保存和账户动作。

### Wave C：事件触发

1. `OC-EQ-006`：仅在新 upstream SHA 出现时执行。

## 11. 单项研究交付模板

每次证据获取形成一个有日期、可独立提交的批次，至少包含：

```text
Question / queue ID:
Date / URL / commit / viewport:
Fixture identity and reset method:
Allowed actions actually used:
Actions intentionally not used:
Source facts:
Inferences:
Unknowns and stop reason:
Raw DOM/bundle/JSON/screenshot evidence:
Affected authority documents:
Blueprint/parity/fixture/verifier impact:
Code, verifier, screenshot or submodule changes: none
Commit / push:
```

新事实先追加到最近的 authority document，不另建“最终版”总览。原始 JSON 和截图必须有解释文档；截图文件名中的 `final` 不代表事实永久有效。

## 12. 完成定义

一个 `OC-EQ-*` 只有在以下条件满足时才能关闭：

1. 问题被直接证据回答，或明确记录为什么在当前权限/fixture 下仍不可回答；
2. source fact、Open Canvas fact、inference 和 clone decision 没有混写；
3. 证据带日期、URL/commit、fixture identity 和动作边界；
4. 对应 authority、traceability、parity、fixture 或 verifier 状态已按影响更新；
5. 没有修改共享源站状态、未授权代码、verifier 或 submodule pointer；
6. 文档检查、diff 检查、path-scoped commit 和 push 完成。

队列关闭只表示证据问题已处理，不表示相关 LibTV slice 已实现。编码仍必须从 [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md) 的七层状态机重新进入。
