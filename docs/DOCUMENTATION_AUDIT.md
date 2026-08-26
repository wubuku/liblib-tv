# 文档体系维护审计

> 审计日期：2026-08-27（在 2026-08-26 初次维护审计上增量复核）
> 审计范围：根入口、正式指南、研究索引、验证手册、Batch 目录/脚本和当前 LibTV/Open Canvas 研究入口。
> 目的：检查文档是否仍准确反映当前仓库，而不是重新识别已有截图或修改业务实现。

## 1. 审计基线

当前文档体系已经具备四层入口：

```text
AGENTS.md / README.md
  -> docs/index.md
     -> formal guides
     -> research/README.md
        -> source audits / component contracts / Batch history
```

本轮以以下内容为交叉基线：

- `AGENTS.md` 的 agent 规则和协作红线；
- `docs/index.md`、`docs/research/README.md` 的正式导航；
- `docs/HARNESS.md`、`docs/DEVELOPMENT.md`、`CONTRIBUTING.md` 中的验证命令；
- `scripts/verify-liblib-batch*.py` 的实际文件集合；
- `docs/research/liblib-canvas-batchN-*` 的实际研究目录；
- 当前 Seedance/Open Canvas 研究入口及其 go/no-go 文档。

### 1.1 当前计数与范围

| 对象 | 当前观察 | 文档含义 |
|---|---|---|
| Batch 研究目录 | 已有 Batch 3-48 的目录记录 | Batch 47 已在 `b1e6212` 完成有界 model-library slice；Batch 48 的 local-import foundation 已提交，完整 workflow 仍是 WIP |
| LibTV verifier | 有 Batch 4-33、35-47 的专项脚本 | Batch 34 是 research-only；Batch 48 当前没有专项 verifier |
| 默认工程门禁 | `npm run check`、`python3 scripts/verify-docs.py` | 不等于所有 Batch 行为回归都已执行 |
| 源站研究 | LibTV、FrameOS、Open Canvas 均有独立入口 | 源站事实、上游启发和 clone 决策必须继续分层 |
| 代码边界 | LibTV/FrameOS route 与 store 独立；后端为 mock | 研究文档不能暗示真实 Provider、上传或持久化已经存在 |

## 2. 发现的问题

| ID | 问题 | 风险 | 处理决策 |
|---|---|---|---|
| DOC-01 | 根 README 仍写 `Batch 4-40` | 低估当前验证资产范围 | 先修正为当时的 `4-33、35-44`，Batch 45 稳定后继续同步到 `35-45` |
| DOC-02 | Big Picture 自动化摘要仍写 `Batch 4-33` | 与 Harness 不一致 | 修正为当前脚本实际范围 |
| DOC-03 | Big Picture 仍称 root README/package.json 保留模板身份 | 与当前 README/package.json 已对齐事实冲突 | 删除该过期判断，保留真实 prototype 边界 |
| DOC-04 | Harness 总览写到 `batch43.py`，循环使用 `{4..44}` | 批量命令会把不存在的 Batch 34 当成脚本执行 | 改为显式 `4..33` 与当前 Director verifier 范围两段 |
| DOC-05 | Development/Contributing 只展示 Batch 4-10 | 新 agent 容易误以为后续 Batch 没有验证入口 | 改成单个窄脚本示例 + 链接到完整 Harness |
| DOC-06 | Documentation Plan 的原始审计仍写 Batch 3-10 | 维护者无法区分历史快照和当前状态 | 保留历史段落，增加本轮维护增量与 supersede 说明 |
| DOC-07 | 初次审计时 Batch 45 已进入研究索引但尚无 verifier | 容易把研究目录误读为已完成回归 | 当时记录为 WIP；脚本/实施稳定后升级，当前 WIP 前移到 Batch 46 |
| DOC-08 | Big Picture 的详细验证基线停在 Batch 43 | 最新已记录验证不在摘要中 | 先修正到 Batch 44，再随稳定 verifier 更新到 Batch 45 |
| DOC-09 | Batch 45 稳定提交后多个正式入口仍停在 `35-44`/Batch 45 WIP | agent 会忽略现有 verifier 或误判当前 WIP | 同步 README、Development、Contributing、Big Picture、计划和生命周期登记 |
| DOC-10 | Batch 46 已收口且 Batch 47 已进入研究索引，正式入口仍把 Batch 46 写成 WIP | agent 会漏跑 Batch 46 verifier，并可能把 Batch 47 计划误读成已实现 | 将稳定范围升级到 `35-46`，Batch 47 明确保持 `PARALLEL_WIP` |
| DOC-11 | 组件合同已丰富，但快捷键 help/handler 和 graph action/history 的运行语义仍分散 | 后续复刻容易把帮助文案当 handler，或把不同 graph transaction 压成统一副作用 | 新增 shortcut runtime crosswalk 与 graph transaction catalog，并接入 task map/index |
| DOC-12 | Batch 11 overlay 设计合同、当前 `uiStore` 状态和节点上下浮层 ownership 分散，且部分字段已无 mount owner | 后续 agent 容易把兼容 state 当产品入口、把 organize/Director/节点浮层并入同一互斥模型，或统一错误的 outside/Escape 策略 | 新增 UI overlay runtime catalog，修正 Behaviors/Page Topology 漂移并接入导航 |
| DOC-13 | Batch 47 在本轮 overlay 审计期间由并行开发者稳定提交，正式入口仍保留 implementation-pending/WIP 描述 | 新 agent 会漏跑现有 verifier，并误判 Director model-library 成熟度 | 同步正式范围到 `35-47`，保留 Batch 34 research-only 例外和 model asset/license 边界 |
| DOC-14 | Batch 48 随后建立 research/plan/contract 并提交 local-import foundation，最新并行 WIP 边界再次前移 | 如果只看 foundation commit，会把未完成的 local model workflow 误读为已验证能力 | 登记 Batch 48 为 `PARALLEL_WIP`，不纳入 Harness 稳定范围，不改写其后续源码/批次文件 |
| DOC-15 | 首轮 live gap、Seedance gap、verification coverage 和多个 runtime catalog 各自准确，但没有当前全路由优先队列 | agent 会继续按已完成的 2026-08-25 P0/P1 排期，或只从最近 Batch 猜下一项 | 新增 UI/UX parity backlog，以稳定 ID 统一价值、证据、验证准备度、风险、依赖和停止条件 |

## 3. 本轮已应用的修正

- 验证范围统一写成：专项脚本存在于 Batch `4-33` 和 `35-47`；
- `docs/HARNESS.md` 的批量示例不再跨过不存在的 Batch 34；
- 根 README、Big Picture、Development 和 Contributing 都链接到完整 Harness，而不是各自维护一份过时清单；
- Big Picture 的 README/package 身份判断以当前仓库实际内容为准；
- Big Picture 的详细验证基线更新到 Batch 47，并记录 model-library 的有界通过项；
- `docs/DOCUMENTATION_PLAN.md` 保留 2026-08-25 的迁移快照，并明确本审计是 2026-08-26 的维护增量；
- Batch 46/47 在各自专项脚本、实施记录和 serial regression 稳定后被纳入台账；Batch 47 的真实模型/环境资产加载仍不在合同内。
- Batch 48 已有 local-import foundation，但完整 workflow 仍保持 implementation-pending/无专项 verifier 的 `PARALLEL_WIP`，稳定门禁止于 Batch 47。
- 快捷键文案/handler/局部优先级和 graph action/history 副作用已有独立、可发现的运行语义地图。
- UI overlay 已有从命令反查 state、mount owner、关闭路径、键盘边界、节点 anchor strategy 和未挂载兼容字段的运行时目录。

## 4. 仍然有意保留的差异

### 4.1 Batch 34 没有专项 verifier

Batch 34 是既有导演台代码考古、源站差距和可借鉴性研究，不应被虚构成一条行为回归脚本。它的入口和证据仍由 [`docs/research/README.md`](research/README.md) 管理。

### 4.2 Batch 47 是有界 recorded pass

Batch 46 已在 `7b746aa` 完成实现、focused verifier 和 Batch 35-46 serial regression。Batch 47 随后在 `b1e6212` 完成 model-library trigger、五类 tab、clone-owned proxy cards、可序列化 prop 插入、R3F/tree/Inspector 联动、空态和响应式边界，并记录 focused verifier、Batch 35-47 serial regression、docs check 与 `npm run check` 通过。本轮只同步该稳定事实，不改写 Batch 47 的实现、截图或专项合同；真实 FBX/OBJ/环境资产和相关 license 决策仍明确排除。

### 4.3 旧 Batch 仍是历史合同

Batch 9/10 等历史截图和断言仍然有效，但只对各自日期的 clone 快照负责；它们不能覆盖当前 LibTV `1092.5px` 图片工具条、`10 + 24 * zoom` 顶部定位或 structured AutoLink 合同。

## 5. 后续文档 backlog

| 优先级 | 工作 | 价值 | 前置条件 |
|---|---|---|---|
| P0 | 任务到文档的 agent reading map | 新 agent 能按任务进入最小证据集合 | 已完成：[`AGENT_TASK_MAP.md`](AGENT_TASK_MAP.md) |
| P0 | 跨文档决策登记 | 关键红线和不可逆选择有单一索引 | 已完成：[`DECISION_REGISTER.md`](DECISION_REGISTER.md) |
| P1 | 证据 claim 反向索引 | 从产品能力反查 DOM/JSON/截图/脚本证据 | 已完成：[`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md) |
| P1 | verifier 能力台账 | 区分脚本存在、脚本通过、源站已复核和仅有文章证据 | 已完成：[`VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md) |
| P1 | clone-website 技能项目适配 | 说明通用技能与本项目授权/证据/协作规则的优先级 | 已完成：[`CLONE_WEBSITE_ADAPTATION.md`](CLONE_WEBSITE_ADAPTATION.md) |
| P1 | 组件合同覆盖矩阵 | 从源码组件反查独立 spec、父/领域合同、批次证据和 `NEEDS_SPEC` 缺口 | 已完成：[`research/components/COVERAGE_MATRIX.md`](research/components/COVERAGE_MATRIX.md) |
| P1 | 快捷键运行语义 crosswalk | 区分源站帮助文案、clone 帮助行、global handler、React Flow gesture 和 local context | 已完成：[`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md) |
| P1 | graph transaction catalog | 从用户动作反查 nodes/edges/selection/history 副作用、证据成熟度和风险 | 已完成：[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md) |
| P1 | UI overlay runtime catalog | 从命令反查 top-level/route-local/node/Director surface 的 state、mount owner、关闭路径、focus/shortcut 与定位 ownership | 已完成：[`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md) |
| P1 | 当前 UI/UX parity backlog | 汇总全路由 source/clone delta，按价值、证据、验证准备度、风险、依赖和授权/fixture 状态排序 | 已完成：[`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md) |
| P2 | 文档生命周期清理 | 区分当前指引、历史合同、兼容入口、证据资产和 supersession；审计归档候选 | 已完成：[`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md)；当前无应搬移文件 |

本审计不建议现在做全量目录重排、截图重命名或双语文档翻译；这些动作的收益低于继续维护证据可追溯性。

## 5.1 本轮追加维护

组件覆盖矩阵已建立，并由组件索引、研究总入口、正式文档入口和 agent task map 共同导出。建立时没有改写当时的 Batch 45 WIP；Batch 45-47 后续均由各批次开发者闭环后，矩阵再同步稳定状态。后续新增组件合同时，应先更新矩阵再更新索引。

P2 生命周期审计随后确认 `drafts/`、`archive/` 当前都没有应搬移资产。新增 [`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md) 统一登记 authority、dated snapshot、historical contract、compatibility entry、evidence artifact、parallel WIP 和 supersession；历史 Batch 不再因为状态文字过时而被误判为待删除文档。

2026-08-27 增量维护进一步补齐两张跨切面运行语义地图：[`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md) 固化 help/handler/gesture/context 差异，[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md) 固化 route/store/graph/history 边界。两者只做静态审计与文档导航，没有修改业务代码。

同日继续补齐 [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：它把 Batch 11 历史设计、当前 `uiStore`、真实 mount owner、逐 surface close path、storyboard/Director 边界和 selected-node 混合锚点策略对齐，并明确冗余 boolean、未挂载 Notification/UserMenu、不可达 grid action 只属于 clone runtime 残留。本轮同时修正 `BEHAVIORS.md` 的 local-state/credits 旧描述与 `PAGE_TOPOLOGY.md` 的 `maxZoom` 漂移。

该目录落档期间，并行工作先后把 Batch 47 稳定提交为 recorded pass，并为 Batch 48 新建 evidence/plan/contract、提交 local-import foundation。正式验证范围因此同步到 `4-33、35-47`，最新 `PARALLEL_WIP` 边界前移到 Batch 48；本轮没有修改两个批次的源码、verifier、截图或专项合同。

随后新增 [`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md)，将首轮 live gap 的历史排期、Seedance 专项缺口、shortcut/overlay/graph runtime 风险和 verification readiness 收束为 13 个稳定 ID。该表明确区分 `READY_FOR_AUTHORIZATION`、`DESIGN_FIRST`、`RESEARCH_FIRST`、`BLOCKED_BY_FIXTURE`、`PROTOTYPE_BOUNDARY`、`OUT_OF_SCOPE` 和 `PARALLEL_WIP`，并把当前最高价值收敛到图片标准双浮层、低风险 active surfaces、Auto Link、keyboard ownership 和 source freshness refresh。

## 6. 验收

本批维护完成的最低标准：

1. `docs/index.md` 能发现本审计；
2. 所有验证范围描述与实际脚本集合一致；
3. Batch 34 的 research-only 和 Batch 48 的 implementation-pending 状态没有被隐藏，Batch 46/47 的 recorded pass 没有被误写成源站全量一致；
4. 文档链接检查通过；
5. 不修改代码、不修改上游 submodule、不覆盖其他开发者 WIP。
