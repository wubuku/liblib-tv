# 文档生命周期与替代关系

> 建档日期：2026-08-26
> 目的：让维护者和 agents 判断一份文档是当前指引、带日期的研究事实、历史合同、兼容入口、证据资产还是并行 WIP。

## 1. 为什么需要本登记

`docs/` 当前约有 377 份 Markdown 文档，其中大部分位于 LibTV Batch 目录。它们同时承担当前指引、源站证据、实施历史和验证记录。仅凭文件日期或“已完成”字样无法判断权威性：

- 旧 Batch 的状态描述只对当时切片负责；
- 当前源站事实可能推翻旧截图中的尺寸或动作集合；
- clone 当前代码能够证明实现状态，但不能自动证明源站行为；
- Open Canvas 是固定版本研究对象，不是 LibTV 合同；
- `docs/README.md` 是兼容入口，不应继续承载新导航信息。

本登记只建立生命周期和 supersession 规则，不移动、删除或重命名现有研究资产。

## 2. 状态词表

| 状态 | 含义 | 维护方式 |
|---|---|---|
| `CANONICAL_ENTRY` | 当前人类或 agent 的正式入口 | 新增正式文档时同步更新；避免复制正文。 |
| `CURRENT_GUIDANCE` | 当前工程、架构、质量或协作规则 | 行为/边界变化时必须同步更新。 |
| `CURRENT_INDEX` | 当前目录、组件、主张或验证反向索引 | 新增资产时增量维护，不替代被索引文档。 |
| `CURRENT_RESEARCH` | 当前可执行研究结论或下一步闸门 | 新证据出现时注明日期和取代范围。 |
| `DATED_SOURCE_SNAPSHOT` | 某日期的 DOM、截图、bundle 或登录态观察 | 保留原貌；用新记录追加，不静默改写旧观察。 |
| `HISTORICAL_CONTRACT` | 某次 Batch 的计划、规格、实施和验证快照 | 保留 provenance；只在明确修正文档错误时改动。 |
| `EVIDENCE_ARTIFACT` | 截图、JSON、提取结果、contact sheet 等原始或派生证据 | 不以文件名中的 `final` 推断当前有效性。 |
| `COMPATIBILITY_ENTRY` | 为旧链接或工具保留的入口 | 只指向 canonical entry，不发展第二套导航。 |
| `PARALLEL_WIP` | 可能由其他开发者正在修改的研究或实施记录 | 只读和链接，不覆盖、搬移或统一格式。 |
| `ARCHIVED` | 已明确不再作为当前指导且有替代入口的文档 | 迁移到 `docs/archive/`，记录原因和替代文档。 |

## 3. 冲突判定顺序

不同文档出现冲突时，按问题类型判断，而不是简单使用“新文件优先”。

### 3.1 工程与协作规则

```text
AGENTS.md hard constraints
  -> DECISION_REGISTER.md active decisions
  -> ARCHITECTURE / LAYERS / QUALITY / DEVELOPMENT / HARNESS
  -> task-specific component/domain contract
  -> Batch implementation snapshot
```

代码当前行为可以暴露文档漂移，但不能绕过协作红线。Next.js API 变更仍需先读本地 `node_modules/next/dist/docs/`。

### 3.2 LibTV 源站事实

```text
newer dated live DOM/computed-style/bundle evidence
  -> current cross-cutting source contract
  -> older dated source audit
  -> historical clone screenshot/assertion
  -> clone-only decision
  -> Open Canvas/general inspiration
```

新证据只取代发生冲突的主张，不抹除旧记录对历史快照的解释力。

### 3.3 Clone 实现与验证状态

```text
current source code + focused current run
  -> VERIFICATION_LEDGER / HARNESS
  -> latest stable component/domain contract
  -> Batch IMPLEMENTATION / recorded pass
  -> screenshot filename or prose claim alone
```

“脚本存在”“文档记录曾通过”和“本轮实际运行通过”是不同状态，统一使用 [`research/VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md) 的词表。

## 4. 文档家族登记

### 4.1 根入口与正式指南

| 文档/家族 | 状态 | 权威范围 | 生命周期说明 |
|---|---|---|---|
| `AGENTS.md` | `CANONICAL_ENTRY` / `CURRENT_GUIDANCE` | agent 导航、硬约束、变更协议 | 先修改本文件，再运行 agent rules 同步脚本；不承载完整研究正文。 |
| 根 `README.md` | `CANONICAL_ENTRY` | 人类项目入口、路线、启动方式、prototype 边界 | 只保留稳定总览，深层事实链接到 docs。 |
| `docs/index.md` | `CANONICAL_ENTRY` | 正式文档 Hub | 新正式文档必须可从这里发现。 |
| `docs/README.md` | `COMPATIBILITY_ENTRY` | 旧工具和链接兼容 | 由 `docs/index.md` 取代导航权威；不新增独有内容。 |
| `ARCHITECTURE.md` / `LAYERS.md` | `CURRENT_GUIDANCE` | 路由、store、模块和依赖边界 | 结构变化时同步；不记录每次 UI 取证。 |
| `DEVELOPMENT.md` / `QUALITY.md` / `HARNESS.md` | `CURRENT_GUIDANCE` | 开发、质量和验证命令 | 命令与脚本集合变化时同步更新。 |
| `GLOSSARY.md` | `CURRENT_INDEX` | 跨文档术语 | 新概念进入稳定文档时补充。 |
| `BIG_PICTURE.md` | `CURRENT_GUIDANCE` | 当前项目整体认知和 prototype 边界 | 作为架构深读材料；不覆盖更窄的当前源站合同。 |
| `AGENT_TASK_MAP.md` | `CURRENT_INDEX` | 任务到最小阅读集合 | 新任务类型或关键合同出现时更新。 |
| `DECISION_REGISTER.md` | `CURRENT_INDEX` / `CURRENT_GUIDANCE` | 跨模块长期决策 | 旧决策改为 `SUPERSEDED`/`HISTORICAL`，不静默删除。 |
| `DOCUMENTATION_PLAN.md` | `HISTORICAL_CONTRACT` | 2026-08-25 文档体系迁移计划和验收 | 当前计数、缺口和维护状态由 `DOCUMENTATION_AUDIT.md` 取代。 |
| `DOCUMENTATION_AUDIT.md` | `CURRENT_GUIDANCE` | 文档漂移、维护 backlog 和验收 | 每次系统性文档维护追加结果。 |
| `DOCUMENT_LIFECYCLE.md` | `CURRENT_GUIDANCE` | 本表所述生命周期与替代关系 | 文档家族或权威边界变化时更新。 |

### 4.2 Research 根文档

| 文档/家族 | 状态 | 权威范围 | 生命周期说明 |
|---|---|---|---|
| `research/README.md` | `CANONICAL_ENTRY` / `CURRENT_INDEX` | 路线研究、Batch、组件和证据入口 | 新研究必须从这里可发现。 |
| `research/BEHAVIORS.md` | `CURRENT_INDEX` | 当前 clone 的跨组件行为目录 | 不能用其旧描述覆盖更新的专项源站合同。 |
| `research/PAGE_TOPOLOGY.md` | `CURRENT_GUIDANCE` | 页面区域、浮层和 z-index 结构 | 页面拓扑变化时同步。 |
| `research/DESIGN_TOKENS.md` | `CURRENT_GUIDANCE` | 已提取或 clone 采用的视觉 token | 数值必须保留来源层级。 |
| `research/COMPONENT_INVENTORY.md` | `CURRENT_INDEX` | clone 当前组件和 store 清单 | 结构清单权威；交互细节由组件合同负责。 |
| `research/components/COVERAGE_MATRIX.md` | `CURRENT_INDEX` | 源码组件到合同/证据/验证状态 | 不取代 `COMPONENT_INVENTORY` 或具体 spec。 |
| `research/TRACEABILITY_MATRIX.md` | `CURRENT_INDEX` | 产品主张到证据的反向索引 | 不把索引行当作新的原始证据。 |
| `research/VERIFICATION_LEDGER.md` | `CURRENT_INDEX` | 验证成熟度和 fixture 阻塞 | 脚本新增、记录通过或合同变化时更新。 |
| `research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md` | `CURRENT_GUIDANCE` | 源站帮助文案、clone help、运行时 handler/gesture/context 对照 | handler、帮助行或新的源站复核变化时更新。 |
| `research/LIBTV_GRAPH_TRANSACTION_CATALOG.md` | `CURRENT_GUIDANCE` | 普通 LibTV graph actions、selection 和 history 边界 | `canvasStore` action、route adapter 或专项 transaction 变化时更新。 |
| `research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` | `CURRENT_GUIDANCE` | top-level、route-local、节点相对和 Director surface 的 state/mount/close/runtime 边界 | `uiStore`、mount owner、Escape/outside/focus 或节点 anchor strategy 变化时更新。 |
| `research/LIBTV_UIUX_PARITY_BACKLOG.md` | `CURRENT_INDEX` / `CURRENT_RESEARCH` | 当前跨路由 parity 差距排序、依赖、授权/fixture 状态和 batch 入口 | 新 source evidence、稳定实现、verifier maturity 或 parallel-WIP 边界变化时更新；不替代专项合同。 |
| `research/LIBTV_FIXTURE_CATALOG.md` | `CURRENT_INDEX` / `CURRENT_GUIDANCE` | LibTV 本地、Director、共享源站和所需 disposable fixture 的身份、构造、隔离、reset 与副作用边界 | 新 fixture、owner、storage/reset、允许动作或 parity gate 变化时更新；不把 fixture 记录当源站事实。 |
| `research/LIBTV_SOURCE_FRESHNESS_REINSPECTION.md` | `CURRENT_RESEARCH` / `CURRENT_GUIDANCE` | 共享源站只读 freshness 复核顺序、采样、停止条件和 drift 处理 | 新日期 source run、登录态、viewport/zoom 样本或安全边界变化时追加，不改写旧 dated evidence。 |
| `research/LIBTV_VERIFIER_REPLACEMENT_MAP.md` | `CURRENT_RESEARCH` / `CURRENT_GUIDANCE` | 历史 verifier、current source contract、local fixture 和 replacement queue 的迁移关系 | source contract、fixture maturity、verifier 或授权状态变化时更新；不直接删除历史断言。 |
| `research/INSPECTION_GUIDE.md` | `CURRENT_GUIDANCE` | 源站检查和截图台账纪律 | 浏览器/取证流程变化时更新。 |

### 4.3 专项研究和 Batch

| 文档/家族 | 状态 | 权威范围 | 生命周期说明 |
|---|---|---|---|
| `liblib-live-YYYY-MM-DD/` | `DATED_SOURCE_SNAPSHOT` | 指定日期、URL、登录态和 fixture 的源站观察 | 新复核另建日期记录或专项 audit；旧 JSON/截图不改写。 |
| `liblib-seedance-2.5-2026-08-25/` | `CURRENT_RESEARCH` + `DATED_SOURCE_SNAPSHOT` | Seedance 主推能力、当前缺口、风险和授权闸门 | `FEATURE_GAP_MATRIX`/go-no-go 是当前导航；背景文章不是实现承诺。 |
| `open-canvas-2026-08-26/` | `CURRENT_RESEARCH` + `DATED_SOURCE_SNAPSHOT` | 固定 commit 的上游源码事实、采纳决策和 LibTV 实施交接 | `EVIDENCE_MATRIX`/源码报告负责固定事实，`ADOPTION_DECISION_MATRIX`/交接蓝图负责当前治理；不能替代 LibTV 源站合同。 |
| Open Canvas `IMPLEMENTATION_IMPLICATIONS.md` | `HISTORICAL_CONTRACT` | 第一阶段 Batch A-E 候选实施清单 | 保留研究 provenance；新工作使用采纳矩阵、交接蓝图和全局 parity ID，不扩展 A-E 编号。 |
| `liblib-canvas-batchN-*` | `HISTORICAL_CONTRACT` | 该批次的计划、规格、实现、验证和截图解释 | README 中“完成/进行中”只解释当时批次；当前完成度看 ledger 和现有代码。 |
| Batch 34 | `HISTORICAL_CONTRACT` / research-only | Director 既有代码考古和可借鉴性 | 没有专项 verifier，不伪造行为通过状态。 |
| Batch 45 | `HISTORICAL_CONTRACT` / recorded pass | Director group/crowd slice | 已有专项 verifier 和 serial regression 记录；仍是有界 clone 合同，不代表源站全量一致。 |
| Batch 46 | `HISTORICAL_CONTRACT` / recorded pass | Director camera screenshot gallery slice | 已有 focused verifier 和 Batch 35-46 serial regression；仍是有界 clone 合同。 |
| Batch 47 | `HISTORICAL_CONTRACT` / recorded pass | Director model-library slice | 已有 focused verifier 和 Batch 35-47 serial regression；clone-owned proxy model 已稳定，真实模型/环境资产仍不在合同内。 |
| Batch 48 | `HISTORICAL_CONTRACT` / recorded pass | Director local model-library persistence slice | evidence/archaeology/plan/contract、实现、focused verifier、截图台账和 maturity assessment 已闭环；真实 mesh loading/远程同步仍明确排除。 |
| Batch 49 | `HISTORICAL_CONTRACT` / recorded pass | Director viewport native coordinate gizmo | 计划、source evidence、spec、实现、截图台账、成熟度和 focused verifier 已闭环；只证明 clone-owned 有界合同，不证明 LibTV source-exact renderer/CSS。 |
| Batch 50 | `HISTORICAL_CONTRACT` / recorded pass | Director workspace collapse and keyboard boundary | 计划、source evidence、spec、实现、四态截图台账、成熟度和 focused verifier 已闭环；只证明 clone-owned shell/keyboard 合同，不证明 LibTV source-exact shell、完整 focus trap 或 source “全屏”语义。 |
| `research/components/*.spec.md` | `CURRENT_GUIDANCE` 或有界合同 | 对应组件的交互、几何、状态和图事务 | 先查 coverage matrix；旧组件 spec 可被更新的跨切面 source contract 部分取代。 |
| `research/frameos/` | `CURRENT_RESEARCH` | FrameOS 独立 route/store/UX | 不与 LibTV 组件和 store 合并。 |

### 4.4 证据与生命周期目录

| 文档/家族 | 状态 | 权威范围 | 生命周期说明 |
|---|---|---|---|
| `design-references/**` | `EVIDENCE_ARTIFACT` | 某次源站或 clone 截图 | 先读最近的 `SCREENSHOT_ANALYSIS.md`；文件被修改不代表解释已更新。 |
| `research/upstream/open-canvas` | 固定 upstream evidence | Open Canvas 固定 commit 源码 | submodule 不在研究批次中修改。 |
| `docs/drafts/` | active draft container | 尚未稳定的计划/设计 | 当前没有 standalone draft；Batch 自带 PLAN 留在 Batch。 |
| `docs/archive/` | `ARCHIVED` container | 有明确替代入口、无需继续维护的文档 | 当前没有归档候选。 |

## 5. 已确认的替代关系

| 旧入口/旧主张 | 当前入口/当前主张 | 取代范围 | 保留原因 |
|---|---|---|---|
| `docs/README.md` 导航 | [`docs/index.md`](index.md) | 正式导航 | 兼容旧链接。 |
| `DOCUMENTATION_PLAN.md` 的 2026-08-25 计数和缺口 | [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md) | 当前文档规模、Batch/verifier 范围和 backlog | 保留迁移计划与原始验收历史。 |
| 各页手写的 Batch 脚本范围 | [`HARNESS.md`](HARNESS.md) + [`VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md) | 当前可运行命令和验证成熟度 | Batch 自身仍保留当时 recorded pass。 |
| Batch 9/10 图片浮层历史尺寸 | [`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md) + current live matrices | 当前源站顶部/底部浮层几何 | 历史断言仍解释旧 clone fixture。 |
| Batch 10 固定候选 AutoLink 原型 | [`LibTVAutoLink.contract.md`](research/components/LibTVAutoLink.contract.md) + current AutoLink matrix | 当前源站 ghost、structured mention 和 ordinal 语义 | 保留旧 clone 为什么出现固定 popover。 |
| `COMPONENT_INVENTORY.md` 的“列出组件” | [`components/COVERAGE_MATRIX.md`](research/components/COVERAGE_MATRIX.md) 的“合同状态” | 判断应读哪个 spec/Batch | Inventory 继续负责源码结构。 |
| Open Canvas overlay/input/graph 模式 | LibTV 专项 source contract | LibTV 精确尺寸、动作、文案和副作用 | 上游模式只保留为机制启发。 |
| Open Canvas `IMPLEMENTATION_IMPLICATIONS.md` 的 Batch A-E | [`ADOPTION_DECISION_MATRIX.md`](research/open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md) + [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](research/open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md) + [`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md) | 当前采纳状态、纵向 slice 和稳定编号 | 旧文档继续解释首轮优先级与研究出口。 |
| `liblib-live-2026-08-25/README.md` 的当时差距排序 | [`research/LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md) | 当前跨路由研究/复刻优先级 | 旧文档继续保留 2026-08-25 source snapshot、当时 clone baseline 和实施 provenance。 |

## 6. 本轮归档审计结论

本轮没有文件满足归档条件：

- `docs/drafts/` 与 `docs/archive/` 都只有入口 README；
- 已完成的 Batch 3-48 仍承担实现 provenance、证据或接力上下文；它们不是应删除的临时稿；
- 旧 Batch 状态文字可能与当前项目完成度不同，但这属于 `HISTORICAL_CONTRACT`，不是应删除的错误；
- `docs/README.md` 仍有兼容价值，且已经明确指向 canonical hub；
- 截图和 JSON 属于证据资产，不以“过期”为由归档。

因此 P2 生命周期清理的正确结果是“建立状态和替代关系、暂不搬移文件”，而不是为了让目录看起来更整齐而制造大量 link churn。

## 7. 归档与替代门槛

只有同时满足以下条件才归档文档：

1. 已有明确替代文档，且替代范围写入本登记；
2. 已检查并更新所有 inbound links；
3. 文档不再解释当前代码、源站证据或历史决策 provenance；
4. 归档后不会让 Batch、截图或 commit 失去上下文；
5. `docs/archive/README.md` 记录日期、原因和替代入口；
6. `python3 scripts/verify-docs.py` 与 `git diff --check` 通过。

如果一份文档只是包含过时数字，应优先增加 dated note 或局部 supersession，而不是移动整份文件。

## 8. Agent 使用清单

1. 从 `AGENTS.md` 或 `docs/index.md` 进入，不从搜索命中的旧 Batch 直接开始实现。
2. 先判断文档状态，再判断内容是否适用于当前 route、fixture 和日期。
3. 遇到冲突时，只记录被取代的 claim，不宣布整份历史文档失效。
4. 修改组件先查 coverage matrix；修改验证先查 ledger/Harness；修改源站合同先查最新 dated evidence。
5. 未经编码授权，生命周期文档只解锁研究和计划，不解锁代码修改。
6. 共享工作区中只暂存自己的文档路径，不移动并行 WIP，不使用 stash。
