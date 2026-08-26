# 研究主张可追溯矩阵

> 目的：从当前项目的重要产品/架构主张反查证据、适用范围和不能据此推出的结论。
>
> 本文是索引，不替代专项研究。主张 ID 只作为导航和评审引用；如果事实发生变化，应追加新证据和日期，不能静默覆盖历史快照。

## 1. 证据分类

| 类别 | 含义 | 可支持的用途 |
|---|---|---|
| `SOURCE_FACT` | LibTV/FrameOS 当前登录态 DOM、computed rect、bundle 或可重复源站交互事实 | 当前源站行为合同，带日期和状态边界 |
| `ARTICLE_EVIDENCE` | 第三方文章中的截图或陈述 | 产品线索、功能形态和待复核问题 |
| `CLONE_FACT` | 当前仓库代码、fixture 或已运行脚本直接支持 | clone 现状和历史实现合同 |
| `OPEN_CANVAS_FACT` | 固定 submodule 源码/官网研究支持 | 通用机制启发，不是 LibTV 视觉真相 |
| `INFERENCE` | 从多个事实推导的解释 | 研究假设，必须保留推理链 |
| `DECISION` | 当前项目为安全、范围或工程一致性作出的选择 | clone-only 规则，不可冒充源站事实 |

## 2. LibTV 与项目主张

| ID | 主张 | 类别 | 主要证据 | 适用范围 | 不能据此推出 |
|---|---|---|---|---|---|
| LIBTV-TR-001 | 当前项目是 LibTV + FrameOS 两条独立前端画布原型，后端服务未实现 | `CLONE_FACT` / `DECISION` | [`AGENTS.md`](../../AGENTS.md)、[`ARCHITECTURE.md`](../ARCHITECTURE.md)、[`BIG_PICTURE.md`](../BIG_PICTURE.md) | route、store、产品边界 | 不代表源站没有后端能力 |
| LIBTV-TR-002 | LibTV 图片节点标准态同时有上方工具条和下方编辑面板 | `SOURCE_FACT` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、[`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md) | 当前已观测的图片节点选择态 | 不代表 active tool 仍叠加标准双浮层 |
| LIBTV-TR-003 | 当前图片工具条使用 9 个文字动作 + 4 个图标动作，外层宽度为 `1092.5x49` | `SOURCE_FACT` | [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md) | 2026-08-26 当前采样版本 | 不覆盖 2026-08-25 的历史 `900.5x49` 快照 |
| LIBTV-TR-004 | 当前顶部工具条 host 公式为 `nodeTop - 24 * zoom - 10`，结合自身 transform 形成 `10 + 24 * zoom` 的 screen gap | `SOURCE_FACT` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md) | 标准图片工具条 | 不代表标注/旋转/元素编辑使用同一 host |
| LIBTV-TR-005 | 当前下方面板 gap 为 `16 * zoom`，以节点中心为横向 anchor 并保持屏幕尺寸 | `SOURCE_FACT` / `INFERENCE` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)、[`ImageEditPanel.spec.md`](components/ImageEditPanel.spec.md) | 图片/视频节点下方面板已测场景 | 不代表任意新面板都能复用该尺寸 |
| LIBTV-TR-006 | 源站靠近画布边缘时允许浮层自然裁切，不应凭感觉移到浏览器中心 | `SOURCE_FACT` / `DECISION` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、[`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) | 当前图片节点边缘样本 | 不代表所有 page-level modal 都允许裁切 |
| LIBTV-TR-007 | 标注、元素编辑、预览、旋转、图层分离具有不同 UI/任务/graph 副作用 | `SOURCE_FACT` / `INFERENCE` | [`LIBTV_IMAGE_ACTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | 当前安全观察和 bundle 分支 | 不代表所有高风险动作的最终提交合同已确认 |
| LIBTV-TR-008 | Auto Link 是全局偏好、候选池、inline ghost 和 structured mention 的组合 | `SOURCE_FACT` | [`LIBTV_AUTOLINK_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)、[`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md) | 当前生产前端的状态链 | 不代表 clone 当前固定 popover 已经等价 |
| LIBTV-TR-009 | graph edge、reference role 和 Prompt mention 是不同关系，正式 mention 需要稳定 node identity | `SOURCE_FACT` / `DECISION` | [`LibTVAutoLink.contract.md`](components/LibTVAutoLink.contract.md)、[`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md) | Auto Link 和后续素材复用 | 不代表必须复制 Open Canvas 的 Handle/provider 语义 |
| LIBTV-TR-010 | Seedance 普通/超长生成面板将模型、模式、参数、音频、数量和费用放在同一提交上下文 | `SOURCE_FACT` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 21/22 研究记录 | 当前采样的生成面板 | 不代表真实 provider 或计费已接入 clone |
| LIBTV-TR-011 | `4s`、最多 `5` 段、`30-300s`、`300s / 14700` 是采样时产品表现，不是永久 API 合同 | `SOURCE_FACT` / `DECISION` | [`LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)、[`LIBTV_DEPENDENCY_RISK_QUEUE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 文章、bundle 和现场交叉解释 | 不应把采样数字直接写入后端假设 |
| LIBTV-TR-012 | 逐帧拉片是独立节点，结果形态包含分镜/动态/音乐等结构化媒体卡 | `SOURCE_FACT` / `ARTICLE_EVIDENCE` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 24 记录、`evidence/` | 入口和文章结果形态 | 不代表当前共享项目已执行真实分析任务 |
| LIBTV-TR-013 | 片段重拍依赖 ready video、时间范围、Prompt token 和结果版本关系 | `SOURCE_FACT` / `ARTICLE_EVIDENCE` | [`LIVE_AUDIT.md`](liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)、Batch 23、[`LIBTV_DEPENDENCY_RISK_QUEUE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md) | 入口文案、bundle 和文章截图 | 不代表共享项目具备安全 ready-video fixture |
| LIBTV-TR-014 | 超长视频过程图和局部重算的源站状态仍不完整，当前 clone 的 12 节点/22 边只是本地 prototype fixture | `CLONE_FACT` / `ARTICLE_EVIDENCE` / `INFERENCE` | Batch 33、[`LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md) | 区分 clone 形态和源站未知 | 不代表源站真实任务拆分已经复刻 |
| LIBTV-TR-015 | 研究阶段没有明确编码授权时，不修改 `src/`、回归脚本或共享源站状态 | `DECISION` | [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)、[`DECISION_REGISTER.md`](../DECISION_REGISTER.md) | 当前研究-only 工作 | 用户明确授权后可按单 slice 进入编码 |
| LIBTV-TR-016 | 当前 top-level overlays 由 `uiStore` write-side exclusion 协调，organize confirmation 独立，selected-node surfaces 不进入该 store | `CLONE_FACT` | [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) | 当前稳定 clone runtime | 不代表全部 surface 在源站使用同一种 outside/Escape 策略 |
| LIBTV-TR-017 | 当前 clone 的节点上下 surface 混用 React Flow `NodeToolbar` 和 node-internal inverse scale，而最新 source toolbar formula/action set 尚未进入 clone | `SOURCE_FACT` / `CLONE_FACT` | [`LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)、[`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md) | standard image/video 与部分 active tool | 不代表应把所有 bottom panel 改成同一种 anchor |
| LIBTV-TR-018 | 当前 clone 的 page global shortcuts 只对 editable target 和 Director Escape 做局部 guard，modal/Director 前台的其他 keyboard ownership 仍有风险 | `CLONE_FACT` / `INFERENCE` | [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)、[`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md) | 当前 page shell 与 Director 边界 | 不证明源站 keyboard/focus 行为；需要只读复核和产品决定 |
| LIBTV-TR-019 | 普通 LibTV verifier 的确定性隔离依赖新 Page、切换到初始空画布和真实 UI 构造，不依赖通用 `canvasStore` 注入 API | `CLONE_FACT` / `DECISION` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`canvasStore.ts`](../../src/store/canvasStore.ts)、[`verify-liblib-batch33.py`](../../scripts/verify-liblib-batch33.py) | 普通本地画布回归和可丢弃场景 | 不代表 `page.evaluate` 可以安全写入任意 store，也不代表新 Page 会清理同一 BrowserContext 的持久化 |
| LIBTV-TR-020 | 当前 `canvas-2` 是 10 节点/11 边的 source-shaped demo，包含 5 个图片节点和一个 `failed` 视频子节点 | `CLONE_FACT` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`canvasStore.ts`](../../src/store/canvasStore.ts) | 本地 baseline、历史图片 variant、group 和 failed 分支 | 不代表源站当前 graph、节点数量或视频 ready 状态 |
| LIBTV-TR-021 | 本地 Add Node 视频 fixture 默认是 `ready`、30 秒、`1280x720`、Seedance 2.5；它是 clone-only 的可复现输入 | `CLONE_FACT` / `DECISION` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`canvasStore.ts`](../../src/store/canvasStore.ts) | 本地片段重拍、视频动作和长视频入口回归 | 不代表源站提供相同 ready toolbar、结果版本或任务生命周期 |
| LIBTV-TR-022 | graph history 不能充当 fixture teardown：默认 `setNodes`/`setEdges` 不入 history，undo 不恢复 viewport、canvas CRUD、UI 或远端副作用，snapshot 的 nested data 也不是深拷贝 | `CLONE_FACT` / `DECISION` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`canvasStore.ts`](../../src/store/canvasStore.ts) | reset 设计、transaction 回归和 undo/redo 解释 | 不代表源站用户可见 undo 语义，也不允许用多次 Cmd/Ctrl+Z 代替独立 Page |
| LIBTV-TR-023 | 共享登录态源站项目是 `SHARED_READ_ONLY`，不能作为可重复 reset 的 source fixture；输入、提交、上传、保存、生成和 graph mutation 都不在当前研究边界 | `DECISION` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | 源站 freshness、已有状态和安全只读观察 | 不代表源站后端没有持久化、任务或独立 disposable project 能力 |
| LIBTV-TR-024 | 历史 verifier 只有在 current source contract、稳定 fixture、明确授权和新 verifier 都具备后，才进入 replacement；旧断言先保留并标为历史合同 | `DECISION` | [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)、[`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | verifier 演进、回归台账和授权 batch 规划 | 不代表已有 replacement queue 已实施，也不允许通过放宽旧断言制造“通过” |
| LIBTV-TR-025 | Director 的 `window.__director_store` 和 Batch 48 的 browser-local persistence 属于独立 fixture 域，不是普通 `canvasStore` 的持久化或注入合同 | `CLONE_FACT` / `DECISION` | [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)、[`Batch 48 PLAN.md`](liblib-canvas-batch48-2026-08-26/PLAN.md)、[`directorStore.ts`](../../src/store/directorStore.ts) | Director 专项回归、local model proxy 研究和 Batch 48 有界 recorded pass | 不代表普通 LibTV route 具有同样 storage、fresh-context reset 或公开 store API |
| LIBTV-TR-026 | 当前逐帧拉片、片段重拍和长视频使用三套有界本地状态近似，尚没有共同的真实 run/result/save backend contract | `CLONE_FACT` / `DECISION` | [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)、对应 component specs、Batch 23/24/33 | `LIBTV-PAR-009` 状态设计、fixture 和 replacement planning | 不代表三项能力应共用一个实现枚举，也不代表本地 `running/pending/complete` 是源站 API |
| LIBTV-TR-027 | 2026-08-27 的 41% 标准图片只读样本继续符合 `1092.5x49` toolbar、`660x191` panel、node-center、`10 + 24 * zoom`、`16 * zoom` 和自然左侧裁切 | `SOURCE_FACT` | [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_SOURCE_FRESHNESS_2026-08-27.md)、[结构化 JSON](open-canvas-2026-08-26/libtv-source-freshness-standard-image-41-2026-08-27.json) | `OC-EQ-001` 的 41%/929x874/既有选中态，强化 `OC-BP-001 L0` | 不覆盖 selection transition、多 zoom/mobile、active tool，也不证明 Batch 51 clone 已通过 |
| LIBTV-TR-028 | 2026-08-27 当前 failed-video dialog 加载 35 个模型 row，14/21 行分别使用 selectable/unavailable style，当前 `2.0 Fast` 映射选中 `Seedance 2.0 Fast VIP` | `SOURCE_FACT` | [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md)、[结构化 JSON](open-canvas-2026-08-26/libtv-model-catalog-audit-2026-08-27.json) | `OC-EQ-002` 的当前登录态/failed video/catalog disclosure | 不证明 35 个 runner 可执行，不解释 unavailable 原因，也不提供逐模型 mode/control contract |
| LIBTV-TR-029 | 2026-08-27 LibTV production bundle 的普通连接 path 具备 target-start 方向归一化、同/反向 node-pair 去重、普通非 Reference 的 DFS cycle guard、equal-ID programmatic guard，以及 action/type/model/capacity validator | `SOURCE_FACT` | [`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)、[结构化 JSON](open-canvas-2026-08-26/libtv-graph-compatibility-static-audit-2026-08-27.json) | `OC-EQ-003` static phase、`LIBTV-GI-004..007` 和 `OC-BP-004` 设计收敛 | 不证明 Reference/导入/批量/同步入口、invalid feedback、history residue 或 disposable source 交互结果 |
| LIBTV-TR-030 | clone 的 graph connection 应先归一化并返回稳定 validation result，再以零 mutation reject/unknown 或 one-step accepted transaction 收口 | `DECISION` / `CLONE_FACT` / `OPEN_CANVAS_FACT` | [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)、Batch 57 [`runtime-audit.json`](liblib-canvas-batch57-2026-08-27/runtime-audit.json) | `LIBTV-PAR-008` connection structural slice / `LIBTV-FIX-LOCAL-GRAPH-CONNECTION-01` / `LIBTV-VR-009` | Batch 57 已证明 local structural runtime；不证明 Reference、domain compatibility、source invalid feedback 或 import/batch/sync |
| LIBTV-TR-031 | clone 应分开 runtime graph、deep-isolated history snapshot、versioned portable document、clipboard packet 和 future persistence envelope；load failure 必须 zero-partial | `DECISION` / `CLONE_FACT` / `OPEN_CANVAS_FACT` | [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)、Open Canvas [`types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts) 与 [`validation.ts`](../../research/upstream/open-canvas/shared/lib/canvas/validation.ts) | `LIBTV-PAR-008` document/snapshot 子切片、future `LIBTV-FIX-LOCAL-GRAPH-DOCUMENT-01` / `LIBTV-VR-010` | 不表示 import/export/persistence 已实现，也不授权 Open Canvas revision/file/KV/rebase |
| LIBTV-TR-032 | subgraph copy 应以具名 command、ownership closure、two-pass node/edge map、node-data reference role 和 full-plan transaction 收口 | `DECISION` / `CLONE_FACT` / `OPEN_CANVAS_FACT` | [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)、[`DUPLICATE_SELECTION.spec.md`](liblib-canvas-batch5-2026-08-25/DUPLICATE_SELECTION.spec.md)、Open Canvas [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts) | `LIBTV-PAR-008` copy 子切片、future `LIBTV-FIX-LOCAL-SUBGRAPH-COPY-01` / `LIBTV-VR-011` | 不证明 source shortcut/Option-drag/clipboard 语义，也不表示 current incident-edge branch 已安全统一 |
| LIBTV-TR-033 | 普通 LibTV 11 类 runtime node 的 data 必须按 type/version/operation registry 解释；shot reciprocal refs、process cohort、Director provenance 和 media locator 不能由浅拷贝或字段名启发式处理 | `CLONE_FACT` / `DECISION` / `OPEN_CANVAS_FACT` | [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)、Open Canvas [`types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts) | `LIBTV-PAR-008` data/aggregate 子切片、future `LIBTV-FIX-LOCAL-NODE-DATA-01` / `LIBTV-VR-012` | 不表示 runtime registry/codec 已实现，不证明 source copy/delete/Director semantics，也不把 Open Canvas 五类 data union 移植到 LibTV |
| LIBTV-TR-034 | graph delete 必须在 mutation 前计算 structural closure、registered inverse refs、aggregate、UI owner 和 resource impact；owned relation 无 repair policy 时 zero mutation | `CLONE_FACT` / `DECISION` / `OPEN_CANVAS_FACT` | [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)、[`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、Open Canvas [`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts) | `LIBTV-PAR-008` delete 子切片、future `LIBTV-FIX-LOCAL-GRAPH-DELETE-01` / `LIBTV-VR-013` | 不表示 runtime planner 已实现，不证明 source cascade/detach/run cancellation，也不授权 media/Director workspace destruction |

## 3. Open Canvas 启发主张

| ID | 主张 | 类别 | 主要证据 | 可迁移范围 | 不能据此推出 |
|---|---|---|---|---|---|
| OC-TR-001 | Open Canvas 固定版本使用 measured node + live viewport 组织 selected editor/action overlay | `OPEN_CANVAS_FACT` | [`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)、上游 [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964) | 统一 screen anchor 的方法 | 不替代 LibTV 的 gap、Panel 层级或裁切合同 |
| OC-TR-002 | Open Canvas 将 typed inputs 分桶，最后才投影到 provider route/task descriptor | `OPEN_CANVAS_FACT` | [`OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)、上游 [`execution.ts`](../../research/upstream/open-canvas/shared/lib/canvas/execution.ts#L69) | 稳定引用身份和请求投影分离 | 不代表 LibTV 使用同样 provider 或 scene 名 |
| OC-TR-003 | Open Canvas 把 node status、run status、save/conflict status 分开 | `OPEN_CANVAS_FACT` | 上游 [`types.ts`](../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L60)、[`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38) | 过程型 UI 的状态分层 | 不代表当前 clone 已有真实任务或保存后端 |
| OC-TR-004 | Open Canvas 复制粘贴以结构化子图和 ID map 保持内部边关系 | `OPEN_CANVAS_FACT` | 上游 [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896)、[`canvas-store.ts`](../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339) | 派生/复制时的身份与坐标边界 | 不代表 LibTV 的历史候选必须改成复制子图 |
| OC-TR-005 | Open Canvas Quick Add 同时维护 screen menu anchor、flow drop point 和 pending connection transaction | `OPEN_CANVAS_FACT` | [`EVIDENCE_MATRIX.md`](open-canvas-2026-08-26/EVIDENCE_MATRIX.md) 的 `OC-021..023`、上游 [`canvas-studio-shell.tsx`](../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4899) | 坐标域分离和多步 graph transaction 的研究案例 | 不证明 LibTV 存在同类悬空连线菜单，也不允许改变当前 Handle affordance |
| OC-TR-006 | Open Canvas 的模型 registry、设置 UI、legacy route 和 current runner 覆盖范围不同 | `OPEN_CANVAS_FACT` / `INFERENCE` | [`EVIDENCE_MATRIX.md`](open-canvas-2026-08-26/EVIDENCE_MATRIX.md) 的 `OC-006..009/016`、[`SOURCE_ANALYSIS.md`](open-canvas-2026-08-26/SOURCE_ANALYSIS.md)、[`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md) | 审计“UI 可选、descriptor 可构造、真实可执行”三层差异 | 不证明 LibTV clone 或 Open Canvas current studio 已执行全部可见 provider/model |
| OC-TR-007 | Open Canvas 机制只有经过 LibTV source、采纳分类、parity、fixture、verifier 和授权链，才可进入 clone slice | `DECISION` | [`ADOPTION_DECISION_MATRIX.md`](open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md)、[`DECISION_REGISTER.md`](../DECISION_REGISTER.md) 的 `DEC-024` | 上游研究到 LibTV 实施的治理边界 | 不代表标为 `ADOPT_METHOD` 的机制已经授权或实现 |
| OC-TR-008 | 获批的上游启发按 evidence、identity、transaction、surface、fixture、verifier、provenance 七层纵向交接 | `DECISION` | [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md) | 单 slice 计划、评审、验证和接力 | 不允许把多项机制打成横向重构，也不替代具体组件合同 |
| OC-TR-009 | Open Canvas 新版本必须先以 immutable SHA 做逐 claim impact audit，不能先移动 submodule pointer 或覆盖旧研究基线 | `DECISION` | [`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](open-canvas-2026-08-26/UPSTREAM_VERSION_IMPACT_PROTOCOL.md)、[`DECISION_REGISTER.md`](../DECISION_REGISTER.md) 的 `DEC-013/024` | 上游版本比较、claim/pattern/adoption 重审和 git provenance | 不代表当前存在待更新版本，也不授权修改 submodule 或 LibTV code |

## 4. 证据更新规则

### 4.1 什么会使主张过期

- 同一源站路径在新日期出现不同 DOM/行为；
- 生产 chunk 或当前 route 版本改变，使旧公式/按钮集合不再适用；
- clone 实现或 verifier 更新，使原来的 `CLONE_FACT` 只剩历史意义；
- Open Canvas submodule 更新，导致固定行号或调用链改变；
- 用户授权后某个 clone-only 决策被实现并形成新的实施合同。
- fixture 构造、reset、BrowserContext persistence 或 verifier replacement 前提发生变化；这类变化应先更新 fixture catalog，再更新受影响主张。

### 4.2 更新动作

1. 在专项证据文档追加新的观察或实施记录；
2. 在本表增加或更新主张 ID 的状态和日期；
3. 将旧主张标为 `HISTORICAL`，不要无说明删除；
4. 更新 [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md) 的覆盖解释；
5. 若变化涉及普通画布 reset、Director storage 或 source write boundary，回读 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)；若涉及历史断言，回读 [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)。
6. 运行 `python3 scripts/verify-docs.py`，并对文档变更做 path-scoped commit/push。

## 5. 当前最重要的反向查找

| 想确认什么 | 从哪里开始 |
|---|---|
| 图片双浮层为什么会乱 | LIBTV-TR-002 到 LIBTV-TR-007 |
| Auto Link 是否只是字符串前缀 | LIBTV-TR-008、LIBTV-TR-009 |
| Seedance 文章数字能否直接写死 | LIBTV-TR-010、LIBTV-TR-011 |
| 长视频/重拍是否已经完成 | LIBTV-TR-012 到 LIBTV-TR-014，再查验证台账 |
| 当前最值得先研究/复刻什么 | LIBTV-TR-016 到 LIBTV-TR-018，再查 [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md) |
| Open Canvas 能借鉴什么、哪些不能移植 | OC-TR-001 到 OC-TR-009，再查采纳决策矩阵、实施交接蓝图和上游版本影响协议 |
| 现在能不能编码 | LIBTV-TR-015 和 [`LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) |
| 为什么新 Page、切换 `canvas-1` 和 undo 不能混称为 reset | LIBTV-TR-019、LIBTV-TR-022、LIBTV-TR-025，再查 [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md) |
| 为什么不能把失败视频当 ready-video | LIBTV-TR-020、LIBTV-TR-021，再查 fixture catalog 的本地视频和 demo baseline 条目 |
| 为什么不能在共享源站试探输入或提交 | LIBTV-TR-023，再查 source freshness runbook 和 go/no-go |
| 历史 verifier 什么时候可以替换 | LIBTV-TR-024，再查 [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md) |
| 为什么不能直接把 Open Canvas DAG guard 移植进 LibTV | LIBTV-TR-029，再查 [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md#10-libtv-par-008-invariant-and-compatibility-design) 与 [`ADOPTION_DECISION_MATRIX.md`](open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md) |
| graph connection 后续应怎样实现和验证 | LIBTV-TR-030，再查 [`LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)、fixture catalog 和 verifier replacement map |
| graph snapshot 为什么不能直接等同保存文档 | LIBTV-TR-031，再查 [`LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)、fixture catalog 和 `DEC-026` |
| 复制节点为什么不能只重写 edge endpoint | LIBTV-TR-032，再查 [`LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)、Batch 5/8 和 `DEC-027` |
| 为什么 node data 不能继续任意浅拷贝 | LIBTV-TR-033，再查 [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md) 和 `DEC-028` |
| 为什么删除 node/edge 不能只做数组过滤 | LIBTV-TR-034，再查 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)、`DEC-029` 和 `LIBTV-VR-013` |
