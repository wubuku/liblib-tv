# 跨项目决策登记

> 本文只登记已经反复确认、会影响多个模块或多个研究批次的项目决策。它不是源站事实清单，也不是未经授权的未来功能列表。
>
> 状态含义：`ACTIVE` 表示当前必须遵守；`HISTORICAL` 表示只对历史快照负责；`RESEARCH_GATE` 表示进入编码前仍需授权或 fixture。

## 1. 决策总览

| ID | 主题 | 决策 | 状态 |
|---|---|---|---|
| DEC-001 | 路由与 store | LibTV 和 FrameOS 保持独立 route、node data、store 和 history | ACTIVE |
| DEC-002 | 证据优先级 | 当前源站证据优先于文章、Open Canvas、旧截图和记忆 | ACTIVE |
| DEC-003 | 事实分层 | `SOURCE_FACT`、`ARTICLE_EVIDENCE`、`OPEN_CANVAS_INSPIRATION`、`INFERENCE`、`CLONE_DECISION` 分开 | ACTIVE |
| DEC-004 | 图片双浮层 | toolbar 与 editor panel 是不同 anchor/层级合同，共享 node/viewport 语义但不共用视觉定位 | ACTIVE |
| DEC-005 | 浮层边缘策略 | 遵循源站自然裁切；没有证据不添加浏览器居中、自动避让或新 clamp | ACTIVE |
| DEC-006 | 连接入口 | `<Handle>` 是真实连接入口，不叠加会拦截拖拽的装饰 plus | ACTIVE |
| DEC-007 | React Flow 尺寸 | React Flow v12 自定义节点不从 `node.style` 读取尺寸；使用 store data、`props.measured` 或已定义的实际 rect | ACTIVE |
| DEC-008 | LibTV edge effect | 不改变已取证的 edge flow effect，除非重新取得源站证据并更新合同 | ACTIVE |
| DEC-009 | active image tool | 预览、标注、元素编辑、旋转、图层分离等不是统一派生节点动作；按 UI/task/graph 副作用分层 | ACTIVE / RESEARCH_GATE |
| DEC-010 | Auto Link | graph edge、reference role、Prompt mention 是独立关系；正式 mention 保留稳定 node identity | ACTIVE / RESEARCH_GATE |
| DEC-011 | Seedance 数值 | `4s`、`5` 段、`300s`、`14700` 等是采样时产品表现，不是永久后端契约 | ACTIVE |
| DEC-012 | 后端边界 | 当前项目是前端 prototype；生成、上传、账户、计费、协作和持久化不得被描述为真实接通 | ACTIVE |
| DEC-013 | Open Canvas submodule | 上游固定 commit 只作为可复核研究对象和通用机制启发，不替代 LibTV 行为 | ACTIVE |
| DEC-014 | FrameOS 调试面板 | `FrameosNodeEditPanel` 是 DEBUG-only，不是源站功能，不得升级为用户能力 | ACTIVE |
| DEC-015 | 研究到编码 | 用户未明确授权时只做研究、计划、合同、验证设计和文档，不修改 `src/` | RESEARCH_GATE |
| DEC-016 | 高风险源站操作 | 共享项目不执行输入、接受 Auto Link、上传、生成、保存、下载、发布或可能产生 graph mutation 的探索 | ACTIVE |
| DEC-017 | ready-video 研究 | 片段重拍、逐帧拉片、视频后处理和长视频过程需要 disposable fixture；没有则标记 `BLOCKED_BY_FIXTURE` | RESEARCH_GATE |
| DEC-018 | 协作工作区 | 不使用 stash/reset/checkout 覆盖他人 WIP；提交只暂存自己的路径，关键进展 commit/push | ACTIVE |
| DEC-019 | 历史截图 | 截图是带日期、viewport、zoom、状态的证据，不自动等于当前 UI | ACTIVE |
| DEC-020 | Director 边界 | Director 是独立的 lazy R3F island；React Flow graph、director serializable state 和 Three.js runtime refs 分层 | ACTIVE |
| DEC-021 | Fixture 身份与 reset | 后续 verifier 必须引用具名 fixture；普通画布以新 Page/真实 UI 构造隔离，undo 不替代 teardown；Director storage 使用显式清理和 fresh-context 断言 | ACTIVE |
| DEC-022 | 共享源站 fixture | 当前登录态共享项目只作为 `SHARED_READ_ONLY` 观察对象；没有独立 project、owner、允许动作、清理路径和停止条件时，不把它当可重复 source fixture | ACTIVE |
| DEC-023 | Verifier replacement | 历史断言先保留；只有 current source contract、稳定 fixture、明确编码授权和新 verifier 齐备后，才申请替换或退役 | RESEARCH_GATE |
| DEC-024 | Open Canvas 机制采纳 | 上游机制必须经过 LibTV source evidence、采纳分类、parity、fixture、verifier 和明确授权后，才可进入单一纵向 slice | ACTIVE / RESEARCH_GATE |
| DEC-025 | graph connection 校验边界 | 连接必须先归一化和纯校验，再以一个 accepted transaction 提交；reject/unknown 不得改变 graph、selection、history 或 model | ACTIVE / RESEARCH_GATE |
| DEC-026 | graph document 与 history 分层 | runtime graph、history snapshot、portable document、clipboard packet 和 persistence envelope 保持独立；portable load 必须 versioned、strict、zero-partial | ACTIVE / RESEARCH_GATE |
| DEC-027 | subgraph copy 身份闭包 | copy 使用具名 command、ownership closure、two-pass ID/reference rewrite 和 full-plan transaction；incident-edge 仅作兼容分支 | ACTIVE / RESEARCH_GATE |
| DEC-028 | node data 身份注册表 | node data 按 `(runtime type, dataVersion)` 验证，并按具名 operation 映射、重置、诊断或拒绝字段；aggregate/ref 不允许浅拷贝 | ACTIVE / RESEARCH_GATE |
| DEC-029 | graph delete 关系修复 | delete 必须先规划 structural/relation/aggregate/UI/resource impact，再以 repair/cascade/detach 或 stable unknown 原子收口；不得只过滤 node/edge | ACTIVE / RESEARCH_GATE |
| DEC-030 | graph mutation 入口定权 | 每个 graph 写入口必须归入 transport/proposal/planned command/restore/remote authority；multi-entity command 验证完整 draft 后一次提交，generic setter 不得成为业务旁路 | ACTIVE / RESEARCH_GATE |
| DEC-031 | 异步结果陈旧收敛 | completion 必须携带 operation/run/result/source-version identity，经 freshness、field ownership 和 graph plan 校验后幂等落图；stale/duplicate/reject 不得覆盖当前 draft、selection 或 history | ACTIVE / RESEARCH_GATE |
| DEC-032 | React Flow change routing | callback 整批分类，只允许 T0 selection 与 existing-node T1 position/passive measurement；semantic change 回到具名 command | ACTIVE / RESEARCH_GATE |
| DEC-033 | 多画布 lifecycle isolation | create/switch/rename/duplicate/delete 是跨 registry/document/history/session/external owner 的 lifecycle transaction | ACTIVE / RESEARCH_GATE |
| DEC-034 | command outcome feedback | typed disposition/reason 先于 UI projection；一个 primary owner，feedback 不进 graph history，stale completion 不宣告当前成功 | ACTIVE / RESEARCH_GATE |
| DEC-035 | selection/focus command context | node/edge/primary selection 是 active-session authority；focus zone 与 foreground surface 决定 command permission，one Escape 只处理一个 top context | ACTIVE / RESEARCH_GATE |
| DEC-036 | viewport/coordinate/placement authority | actual React Flow host、typed coordinate domain、live/stable viewport 和 canvas-generation-bound gesture/placement owner 共同决定空间结果 | ACTIVE / RESEARCH_GATE |
| DEC-037 | media ingress/resource lifecycle authority | media intent、local bytes/lease、asset identity、node reference 与 provisional/semantic projection 分权；release 只由显式 owner + reachability 决定 | ACTIVE / RESEARCH_GATE |
| DEC-038 | editor session/commit/history authority | foreground editor 以 profile/session/baseline/draft 定权；native/local/graph undo 分流，typed commit 决定 graph/async handoff 与 close | ACTIVE / RESEARCH_GATE |
| DEC-040 | Director project/session authority | Director portable project、session UI、runtime projection、resource lease 与 graph projection 分权；先实现 versioned strict codec，再做 owner registry、history/delete 与真实资产 | ACTIVE / RESEARCH_GATE |
| DEC-039 | media rendition/geometry authority | selected output、intrinsic metadata、request、semantic frame、passive measurement、surface rendition、editor space 与 export 分权 | ACTIVE / RESEARCH_GATE |
| DEC-041 | Director command/history/gesture authority | Director semantic mutation 使用 project-local typed command/history；完整 pointer lifecycle 逐类接入，delete/async/persistence 仍按独立合同推进 | ACTIVE / IMPLEMENTATION_GATE |

## 2. 决策详情

### DEC-001：两条路线保持独立

**背景：** LibTV 和 FrameOS 都使用画布，但节点语义、路由、状态形状和历史行为不同。

**决策：** LibTV 使用 `canvasStore` + `uiStore`，FrameOS 使用 `frameosStore`；不引入 route `mode` flag，也不合并节点联合类型或 history。

**影响：** 共享的纯工具可以复用，但 route orchestration、store、node renderer 和研究合同必须保持可识别边界。修改共享 CSS 后需要同时验证两条路线。

**依据：** [`ARCHITECTURE.md`](ARCHITECTURE.md)、[`LAYERS.md`](LAYERS.md)、[`BIG_PICTURE.md`](BIG_PICTURE.md)。

### DEC-004：图片双浮层是两条定位合同

**背景：** 源站选中图片节点后，上方工具条和下方编辑面板同时出现，且职责、层级、缩放和生命周期不同。

**决策：** toolbar 使用源站确认的 top host 公式和 NodeToolbar 语义；editor panel 使用节点中心、底部 gap 和 inverse scale；两者共享 live viewport/selection 生命周期，但不能用一个 CSS offset 或 page-level overlay 代替。

**影响：** 后续修复位置时先检查 measured rect、viewport snapshot、transform 和卸载时序。自然裁切是合同的一部分。

**依据：** [`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md)、[`LIBTV_UI_STATE_HIERARCHY.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)。

### DEC-009：图片动作按副作用分层

**背景：** 当前源站图片工具条不仅有派生动作，还包含 preview、annotate、element edit、rotate、layer separation 等不同状态。

**决策：** 进入 active tool 时允许替换标准双浮层；preview 是 page-level overlay；标注/元素编辑是 local authoring surface；旋转/图层分离可能产生 graph/task mutation。不能把所有入口都映射到统一 `addDerivedNode`。

**影响：** 每个动作进入实现前必须有状态、选择、退出、保存/任务和 graph 事务说明。高风险动作需要 disposable fixture。

**依据：** [`LIBTV_IMAGE_ACTION_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)。

### DEC-010：Auto Link 保留结构化身份

**背景：** 源站当前 Auto Link 是全局偏好、候选池、inline ghost 和 structured mention 的组合；clone 旧实现使用固定弹窗和字符串前缀。

**决策：** graph connection、reference role 和 prompt mention 分开建模；mention 至少保留 source node ID、媒体类型、职责和 ordinal，展示文本只是投影。

**影响：** 后续模型切换、候选重排、删除源节点和结果复用不会依赖不可逆字符串解析；进入编码前必须读 AutoLink 合同并准备编辑器 fixture。

**依据：** [`LibTVAutoLink.contract.md`](research/components/LibTVAutoLink.contract.md)、[`LIBTV_AUTOLINK_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)。

### DEC-015：研究和编码有明确闸门

**背景：** 当前工作区同时存在其他开发者业务/截图 WIP，且共享 LibTV 源站项目可能发生不可逆操作。

**决策：** 没有用户明确编码授权时，不修改 `src/`、测试脚本或业务实现；共享源站只做安全只读观察；需要写入或 ready-video 的问题先标记 fixture 阻塞。

**影响：** 研究阶段可以持续补文档、合同、索引、静态审计和只读证据；不能为了“验证一下”改变共享 graph。授权后仍按单 slice、local fixture、窄验证、实施记录和 path-scoped commit/push 进行。

**依据：** [`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)、[`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md)。

### DEC-021：Fixture 必须有身份和可证明的 reset

**背景：** 当前普通 LibTV、Director 和源站研究混用多种状态来源：源码内置 demo、空画布 UI 构造、transaction-derived graph、公开 Director store 和登录态共享项目。新 Page、reload、切换空画布、undo 和清理 browser-local storage 的隔离等级不同。

**决策：** 后续 verifier 和研究计划必须引用 [`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md) 的具名 fixture ID，并记录 owner、构造、初始状态、允许动作、禁止动作、reset method 和 reset assertions。普通 LibTV 优先使用新 Page 加真实 UI 构造；undo 只能验证 graph transaction，不能代替 teardown。Director 的 storage 必须显式清理并用 fresh Page/context 验证；未经授权不增加通用 fixture injector。

**影响：** “使用测试数据”“刷新即可”“按 Cmd/Ctrl+Z 撤销”都不足以描述可重复性。fixture 状态变化必须同步 fixture catalog、verification ledger 和受影响的 traceability claim。

**依据：** [`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`LIBTV_VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md)。

### DEC-022：共享源站只用于安全只读观察

**背景：** 当前 LibTV 登录态 URL 指向共享项目，无法证明每次研究前都能恢复相同 graph、viewport、selection、媒体版本或远端任务状态。

**决策：** 共享项目保持 `SHARED_READ_ONLY`。没有独立 project/space、owner、允许动作、消耗上限、预期观测量、远端清理路径和停止条件时，不输入 Prompt、不接受 AutoLink、不上传、不提交、不保存、不生成、不改变偏好，也不做可能产生 graph mutation 的探索。

**影响：** 共享源站可以回答“当前看见什么”，不能回答“写入后发生什么”或提供 source parity regression fixture。需要写入、ready-video、dirty image 或 process lifecycle 的问题必须登记 `REQUIRED_DISPOSABLE` / `BLOCKED_BY_FIXTURE`。

**依据：** [`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](research/LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)、[`LIBTV_RESEARCH_GO_NO_GO.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)。

### DEC-023：历史 verifier 采用双轨替换

**背景：** Batch 9/10 等历史 clone verifier 仍有兼容回归价值，但部分几何、AutoLink 和动作断言已被较新的 source contract 取代；Batch 48 则证明了另一个有界 clone-owned Director slice 已经可以 recorded pass。

**决策：** 历史 verifier 不因当前 source 漂移而直接删除、放宽或重写。先并行登记 current source contract、local/source fixture、focused verifier、截图台账和授权状态；新 verifier 稳定后再评估旧断言是保留、标历史、降级还是退役。clone-owned recorded pass 只提升 clone 的有界成熟度，不提升为源站 parity。

**影响：** replacement queue 的 `REPLACEMENT_READY` 不是“已经实现”，而是满足 source、fixture、授权和 verifier 前置条件后的可申请状态。任何替换都要保留 old verifier provenance，并以 path-scoped commit/push 落档。

**依据：** [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](research/LIBTV_VERIFIER_REPLACEMENT_MAP.md)、[`LIBTV_FIXTURE_CATALOG.md`](research/LIBTV_FIXTURE_CATALOG.md)、[`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md)。

### DEC-024：Open Canvas 机制按证据链采纳

**背景：** Open Canvas 固定源码能够为坐标、typed identity、状态分层和 graph transaction 提供高质量参考，但它的视觉、产品语义、provider、保存和 Quick Add 行为不等于 LibTV。

**决策：** 每项上游机制先在 [`ADOPTION_DECISION_MATRIX.md`](research/open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md) 标记为 `ADOPT_METHOD`、`ADAPT_TO_LIBTV`、`RESEARCH_ONLY`、`DEFER` 或 `REJECT_TRANSPLANT`。只有继续具备 LibTV current source contract、`LIBTV-PAR-*`、具名 `LIBTV-FIX-*`、`LIBTV-VR-*` 或等价窄验证合同，以及用户对该 slice 的明确编码授权，才可按 [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](research/open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md) 进入实现。

**影响：** 上游代码不直接成为 clone 文件清单；`ADOPT_METHOD` 也不等于已授权。没有 LibTV 同类事实的 Quick Add/pending connection 保持研究态，provider/key 和视觉皮肤保持拒绝移植，Batch A-E 旧清单只保留历史 provenance。

**依据：** [`EVIDENCE_MATRIX.md`](research/open-canvas-2026-08-26/EVIDENCE_MATRIX.md)、[`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md)、[`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md)。

### DEC-025：Graph connection 先校验后提交

**背景：** LibTV source static bundle 已证明普通连接存在 target-start 方向归一化、node-pair 去重、普通非 Reference cycle guard 和 domain validator；当前 clone 的 `onConnect -> addEdge` 则只检查端点非空后直接追加并记录 history。Open Canvas 可以提供 pure validation 和 transaction 方法，但不能决定 LibTV 的 node/Handle 产品语义。

**决策：** 后续连接入口统一遵循 normalize -> endpoint/structural/domain validate -> result -> commit。结果区分 `allow`、`allow-with-adjustment`、`reject` 和 `unknown`；reject/unknown 对 nodes、edges、selection、history、viewport 和 model 保持零 mutation，accepted gesture 只产生一个声明完整的 graph transaction。Reference、未建模 action 和未确认 entry point 保持显式 unknown，不默认放行或伪装 source parity。

**影响：** React Flow gesture、programmatic connect、import/batch/sync 最终使用同一纯校验权威；Handle 和 edge flow 视觉不在 graph-hardening slice 中改变。运行 fixture、validator 和 `LIBTV-VR-009` 仍需明确编码授权；真实 invalid feedback 与 Reference 语义仍需 disposable source fixture。

**依据：** [`LibTVGraphConnection.contract.md`](research/components/LibTVGraphConnection.contract.md)、[`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](research/open-canvas-2026-08-26/LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)。

### DEC-026：Graph document 与 history snapshot 分层

**背景：** 当前普通画布 `GraphSnapshot` 只做浅层 nested data 复制，runtime React Flow `Node/Edge`、undo snapshot、canvas duplicate 和未来 import/export 尚无独立 schema。Open Canvas 固定版本证明 versioned serialized graph、strict API validation、revision envelope 和 template runtime reset 可以分层，但其保存/协作产品语义不属于当前 clone。

**决策：** 后续保持 `RuntimeGraphState`、`GraphHistorySnapshot`、`PortableGraphDocument`、`ClipboardSubgraphPacket` 和 future `PersistenceEnvelope` 五层独立。History 深隔离 declared node/edge fields，但继续排除 viewport、selection、canvas CRUD、UI/save state；portable document 使用显式 kind/schemaVersion/node dataVersion、strict parse/migration/validation，任何 reject/unsupported 都不得产生 partial canvas mutation。

**影响：** 当前 `src/types/canvas.ts` 不能直接冒充完整 serialization registry；future import 第一 slice 只允许创建新 canvas，不替换 active canvas。Open Canvas 的 `200/400` limits、file/KV、revision、debounce、conflict rebase 和 provider fields 保持 inspiration/deferred，不进入 runtime 合同。Codec、history isolation、fixture 和 `LIBTV-VR-010` 仍需明确编码授权。

**依据：** [`LibTVGraphDocument.contract.md`](research/components/LibTVGraphDocument.contract.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`ADOPTION_DECISION_MATRIX.md`](research/open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md)。

### DEC-027：Subgraph copy 先构造完整身份闭包

**背景：** 当前 clone 已能复制 selection/group/child/canvas，但单个普通节点会复制所有 incident edges，多选/group 只复制 internal edges；node data 中的 sourceNodeId、edgeId、process/run/media identity 尚无统一 rewrite/reset 规则。Open Canvas 的 versioned packet、internal-edge closure 和 ID map 是方法参考，不覆盖 LibTV parent/derived/process 语义。

**决策：** 后续 copy 使用具名 `duplicate-selection / create-node-copy / paste-subgraph / option-drag-copy` command，不再以 `includeEdges` boolean 表达产品语义。Copy 在 mutation 前完成 root/descendant closure、two-pass node/edge ID map、parent placement、node-data reference role、edge policy 和 connection validation；reject/unknown 均 zero mutation，accepted command 只产生一个 history step。

**影响：** `internal-only` 是 multi/group/clipboard 的安全默认；current single-node incident-edge 分支只保持 `COMPATIBILITY_HOLD`。System clipboard 和 Option-drag 不因合同完成而实现，Option-drag 仍需 source fixture。任何 unmodeled identity field 都阻塞 transaction，不能只 remap structural edge 后深拷贝 data。

**依据：** [`LibTVSubgraphCopy.contract.md`](research/components/LibTVSubgraphCopy.contract.md)、[`DUPLICATE_SELECTION.spec.md`](research/liblib-canvas-batch5-2026-08-25/DUPLICATE_SELECTION.spec.md)、[`OPEN_CANVAS_PATTERN_CARDS.md`](research/open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)。

### DEC-028：Node data 必须由 type/version/operation 注册表解释

**背景：** 普通 LibTV runtime 有 11 类 node，但 renderer、Add Node、legacy types、default-data switch 和 component interfaces 不一致；node data 还包含 sourceNodeId、edgeId、shot reciprocal refs、processId、Director provenance、scoped mark IDs 和不同生命周期的 media locator。当前 history/duplicate/canvas duplicate 都只做浅层 data spread。

**决策：** 后续 graph codec 以 `(node.type, dataVersion)` 选择封闭 registry entry，并按 `HISTORY_SNAPSHOT / DUPLICATE_SELECTION / CREATE_NODE_COPY / DUPLICATE_CANVAS / CLIPBOARD_PASTE / PORTABLE_IMPORT / DELETE_REPAIR` profile 为每个字段声明 preserve、map、reset、recompute、diagnose 或 reject。Shot breakdown 必须校验双向 aggregate；long-video process 只允许完整 cohort 映射一个新 processId；unknown type/version/reference 和缺失 edge-owned ref 均 zero mutation。

**影响：** `src/types/canvas.ts`、`Record<string, unknown>`、字段名后缀和 object spread 都不能单独充当 schema。Director shell 复制不等于 workspace 复制；`data:` 受 byte budget，`blob:` 不 portable；node-specific status 不使用统一 reset。Registry、fixture 和 `LIBTV-VR-012` 仍需明确编码授权。

**依据：** [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`LibTVNodeDataIdentity.contract.md`](research/components/LibTVNodeDataIdentity.contract.md)、Open Canvas [`types.ts`](../research/upstream/open-canvas/shared/lib/canvas/types.ts) 与 [`serialization.ts`](../research/upstream/open-canvas/shared/lib/canvas/serialization.ts)。

### DEC-029：Graph delete 必须是 relation-aware full-plan transaction

**背景：** 当前 `removeNode/removeSelectedNodes` 只展开 group descendants、删除 incident edges 并更新 selection/history；`removeEdge` 只过滤 edge。普通 LibTV node data 还包含 owned node/edge refs、shot reciprocal refs、shared processId、Director provenance、node-bound overlay owner 和不同生命周期的 media locator。Open Canvas 的固定版本只有 typed node + ordinary edge 模型，其简单删除不能直接覆盖这些关系。

**决策：** 后续删除以具名 command 进入纯 planner，依次计算 structural closure、registered relation inverse index、aggregate impact、per-type cascade/detach/reset/block policy、selection/UI invalidation 和 resource diagnostics；只提交通过 post-plan integrity validation 的 `ready` plan，并形成一个 graph history step。Owned ref、shot/process aggregate 或 semantic edge 无安全 recipe 时返回 stable `unknown/reject` 且 zero mutation。Exact user-visible cascade/detach 仍按 source/product gate 决定，不用 Open Canvas 或字段名启发式填空。

**影响：** Generic edge scissors 不能绕过 nested `edgeId` repair；V0 process 不允许 partial cohort；shot refs 必须双向一致；graph delete 不自动销毁 Director workspace、provider run 或 media bytes；UI owner cleanup 不进入 graph history。`GRAPH-DELETE-01`、`LIBTV-VR-013` 与 runtime planner 仍需明确编码授权。

**依据：** [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)、[`LibTVNodeDataIdentity.contract.md`](research/components/LibTVNodeDataIdentity.contract.md)、Open Canvas [`canvas-store.ts`](../research/upstream/open-canvas/shared/stores/canvas-store.ts)。

### DEC-030：Graph mutation 入口必须先定权再验证

**背景：** Batch 57 已保护 React Flow connection 和 programmatic `addEdge`，但派生媒体、拉片/长视频、duplicate、group、delete、generic `setNodes/setEdges`、React Flow changes 和 undo/redo 仍通过不同入口直接写 graph。Open Canvas 固定版本采用 store command、serialization、save/API full-graph validation、revision 和 server patch 多层边界，但其 clipboard 与 framework delta 也不是完整验证入口。

**决策：** 每个 graph mutation ingress 必须归入 T0 presentation、T1 whitelisted transport、T2 single proposal、T3 planned multi-entity command、T4 snapshot/document restore 或 T5 remote authority。T3 在任何 mutation 前构造并验证完整 final draft，只以一个 history transaction 提交；T4 先 decode/invariant check 再原子 swap；T5 声明 revision/base identity 与 field ownership。低层 setter 只能承载已分类 transport/commit，不能被组件当作业务命令旁路。

**影响：** 不能把所有 derived edge 循环调用 `addEdge`，否则会产生 partial graph 和多 history step；也不能依赖 future save-time validation 才发现 runtime invalid state。后续先收窄 React Flow change 类型，再按单一 command 迁移 derived/copy/delete/history，不做一次性 store 重构。`GRAPH-ENTRYPOINT-01`、`LIBTV-VR-014` 和 runtime authority boundary 仍需明确编码授权。

**依据：** [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)、Open Canvas [`canvas-store.ts`](../research/upstream/open-canvas/shared/stores/canvas-store.ts) 与 [`validation.ts`](../research/upstream/open-canvas/shared/lib/canvas/validation.ts)。

### DEC-031：异步结果必须先判 freshness 再落图

**背景：** 当前 clone 的逐帧拉片、视频后处理和长视频主要由 component-local timer 延迟调用 graph creator，Director 动画导出则在真实 browser-side 录制完成后创建结果节点；普通画布没有共同的 operation/run/result ingress。Open Canvas 固定版本展示了 descriptor、run record、runId polling、server patch、revision 与 saved baseline 分层，但其 node patch 不比较 expected current run/source version/field owner，run terminal 与 graph patch 也不是一个原子写入。

**决策：** 每个 graph-producing completion 必须携带 canvas/source/source-version/operation/run/attempt/result identity。T5 或 local async ingress 先判 current、stale、duplicate 或 invalid，再检查 operation-specific field ownership、构造并验证完整 graph plan；只允许 current accepted plan 一次提交。Stale/duplicate/reject 默认 preserve 当前 draft、selection、surface 和 history；没有 provenance UI 时不偷偷附加孤立结果。Progress/status observation 不产生 graph history，undo 不自动重放外部 side effect，result resource 在 accepted commit 时才转移 ownership。

**影响：** 当前短 timer 统一解释为 `PROTOTYPE_LATENCY`，不能冒充 task backend。后续若获授权，先用 deterministic shot-breakdown fixture 验证 descriptor freeze、delete/undo stale rejection、selection preserve 和 duplicate no-op，再扩展长视频、视频处理与 Director；真实 provider、上传、计费、保存、cancel/retry backend 仍需独立授权。

**依据：** [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、[`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)、[`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、Open Canvas [`local-canvas-runner.ts`](../research/upstream/open-canvas/shared/services/canvas/local-canvas-runner.ts) 与 [`canvas-studio-shell.tsx`](../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)。

### DEC-032：React Flow change 必须先整批分类再归约

**背景：** clone 与 Open Canvas 固定版本都锁定 `@xyflow/react@12.11.1`。该版本的 `NodeChange` 包含 select/position/dimensions/add/remove/replace，`EdgeChange` 包含 select/add/remove/replace；reconnect 是独立 callback。当前 clone 把 node 非选择 change 与全部 edge change 直接交给 generic reducer，再以 whole-array setter 写回，其中 edge reducer base 还来自 render closure。Open Canvas 使用 current Zustand state 是正面方法，但同样接受所有 variant，并把所有 non-select change 统一视为 persistent。

**决策：** `onNodesChange/onEdgesChange` 必须在任何副作用前解析整个 batch。T0 只处理 selection；T1 只允许 existing-node finite position 和不带 `setAttributes` 的 passive measurement；node/edge add/remove/replace、attribute resize 与 reconnect 必须进入具名 T2/T3 command 或拒绝。Edge 在 12.11.1 没有 non-selection T1 variant。Accepted T0/T1 必须基于同一 current active-canvas snapshot；unsupported/malformed mixed batch 零 partial mutation；selection、measured/dragging/resizing 等 runtime 字段不得泄漏进 portable document/copy/semantic history。

**影响：** Batch 61 已实现 pure classifier/result、current-snapshot store routing、edge session selection owner 和 focused fixture，命名 connect/delete、drag-stop one-history、marquee 与图片双浮层相邻合同均保持。该 focused pass 不授权 node resize、reconnect、persistence、FrameOS 改造或视觉变更，也不表示其余 graph ingress 已经统一。`REACT-FLOW-CHANGES-01` 与 `LIBTV-VR-016` 的运行证据见 [`liblib-canvas-batch61-2026-08-27/`](research/liblib-canvas-batch61-2026-08-27/)。

**依据：** [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)、[`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)、Open Canvas [`canvas-store.ts`](../research/upstream/open-canvas/shared/stores/canvas-store.ts) 及固定 `@xyflow/react@12.11.1` / `@xyflow/system@0.0.78` 类型与 reducer 实现。

### DEC-033：多画布切换必须是 owner reconciliation transaction

**背景：** Batch 16 已实现内存 canvas CRUD，Batch 58 已为四类 node-bound surface 引入 `canvasId + nodeId` owner；当前 graph/viewport/history 也按 canvas 保存。但 `setActiveCanvas` 不验证 ID，organize/drag/connection/viewport transient 没有 canvas owner，demo viewport preset 会在切换时重写 store，delayed action 多数 late-read active canvas。Open Canvas 以 URL canvasId、summary/document、hydrate 和 delete-run cleanup 建立强文档边界，但 old-route in-flight save response 的 local `finishSave/failSave` 不校验 current canvas。

**决策：** create/switch/rename/duplicate/delete 使用具名 lifecycle plan/result。Switch 必须验证目标，在一次 current project snapshot 上切换 active/selection/history owner，保持 source/target graph-history-viewport，清 current clone selection，关闭 node-bound owner，并取消所有不具 canvasId/generation 的 page-local transaction。Delayed/remote completion 必须携带 canvas/operation owner，不能把 active canvas 当延迟目的地。Duplicate/delete 对 graph data、run、Director workspace 和 resource 返回显式影响；lifecycle 不进入 per-canvas graph undo。

**影响：** 当前 in-place CanvasTabDropdown 视觉和 Batch 16/58 合同保持；不移植 Open Canvas 列表页、URL、file/KV、revision/conflict。最终 canvas 删除、active fallback、projection panel 保留、responsive preset、background operation 和 resource copy 继续由 decision queue/source/product 约束。`CANVAS-LIFECYCLE-01`、`LIBTV-VR-017` 与 runtime planner 仍需明确编码授权。

**依据：** [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、[`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)、[`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)、Open Canvas list/page/store/hydrate/save fixed chain。

### DEC-034：命令结果先定权，再投影反馈

**背景：** 当前 clone 已有 connection reason union、多个 surface-local status、VideoNode timer chip 和 Director progress/error/retry，但没有共同 outcome-to-surface authority。Open Canvas 同时使用 global toast、node status/error、save/conflict surface 和 field errors，证明 feedback 应分层；其 coarse code + localized message lookup、无 canvas/operation owner 的 async toast 又会让 i18n、stale convergence 和 verifier 依赖字符串/当前页面。

**决策：** 每个用户命令先返回 `COMMITTED / STARTED / COMPLETED / REJECTED / NOOP / FAILED / CANCELED / STALE / CONFLICT / UNKNOWN` 中的稳定 disposition，以及 reason code/args 和 owner。Display copy 只在 presentation adapter 映射。Durable/recoverable state 使用 owner-local persistent surface；field rejection 靠近字段；visible graph result 是 primary；copy/download 等无持续对象的动作才默认适合 transient confirmation。一个 outcome 只有一个 primary visual authority，secondary announcement 不改变语义。Reject/noop/stale/unknown 默认 zero graph/history；stale/duplicate completion 不在当前 canvas 宣告成功。

**影响：** 不因本决策新增全局 LibTV toast，也不复用 FrameOS toast。当前 local-prototype disclosure 与 Director owner surface保持；精确 LibTV toast、invalid Handle style、颜色、文案、timeout 和 modal 仍 source-gated。`COMMAND-FEEDBACK-01`、reason projection、timer/dedupe/aria owner 和 `LIBTV-VR-018` runtime 均需明确编码授权。

**依据：** [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)、[`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)、[`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)、Open Canvas layout/store/i18n/studio/list/settings fixed chain。

### DEC-035：selection、focus 与 command context 分权

**背景：** 当前 clone node selection 已从 stored node data 分离，但 edge `selected` 仍经 generic reducer 留在 edge record；node selection 又有三个写入口。视觉前台 surface、DOM focus 与 page shortcut permission 没有共同 authority，导致 pointer-modal/keyboard-pass-through、local/global Escape 和 focus return 风险。Batch 50 已关闭 Director 背景 shortcut island。Open Canvas 的 local editor/editable clipboard 是正面方法，selected flag/conflict coupling、weak Escape、framework default destructive key 是反例。

**决策：** active canvas 使用 validated node/edge/primary selection snapshot，React Flow selected 只作 T0 transport/projection，不进 document/history。事件先解析 native/editable/local tool/Director/modal/menu/target-scoped/canvas context，再返回 `HANDLED/CONSUMED/PASS/BLOCKED/NOOP`；chord 只有被当前 owner 接受后才成为 command。视觉阻断 modal 按 clone correctness floor 暂停背景 canvas command；one Escape 默认只关闭一个 top context。Modal/exclusive owner 必须声明 initial focus、containment 和 opener/owner/canvas fallback，stale async/switch/delete 不得偷 selection/focus。Batch 62 已将其中的 validated snapshot、editable/IME boundary、blocking foreground suspension、one-Escape 和 canvas focus fallback 落成 clone-owned focused pass。

**影响：** 不因本决策引入 global modal manager 或 Radix，也不改变 FrameOS store。Character/History/Shortcuts/Canvas dropdown 的 exact source policy、mixed node-edge primary、undo selection、Director return 和 focus visual 继续 source/product-gated。Batch 62 的 focused slice 只覆盖 clone-owned correctness，不关闭 universal mixed primary、focus trap、target-scoped containment 或 source-exact modal policy。`LIBTV-FIX-LOCAL-SELECTION-FOCUS-CONTEXT-01`、`LIBTV-VR-019` 与后续 runtime convergence 仍需明确编码授权。

**依据：** [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)、Batch 50/58/60 records、Open Canvas studio/store/Radix fixed chain。

### DEC-036：空间结果由 actual host、坐标域和当前 owner 共同定权

**背景：** 当前 clone 已有 per-canvas viewport、controlled React Flow、V/H/Space 清理、drag one-history、derived/duplicate/organize placement 和 source-shaped overlay formula，但这些能力尚未共享一套空间 owner。默认新增节点仍以 browser window center 计算位置；asset panel 会改变实际 React Flow host。Viewport callback、organize、drag 和 connection transient 也可能在 canvas switch 后晚到。Open Canvas 的 screen-menu/flow-point 双锚点和 live/stable viewport 提供了可借方法，同时其 permissive normalize、窄 host clamp、缺 pointercancel cleanup 和逐文件 async drop 是反例。

**决策：** 普通 LibTV 空间边界显式区分 `CLIENT`、`HOST_LOCAL`、`FLOW_WORLD`、`NODE_LOCAL`、`SCREEN_OVERLAY` 和 `MEDIA_NORMALIZED`。Client/local conversion 只使用当前实际 React Flow host 和当前 live viewport；stable viewport 只在 current gesture/programmatic operation 结束时提交，bootstrap preset 只用于尚无用户稳定状态的首次投影。每个 gesture、delayed coordinate 和 placement plan 携带 route/canvas/generation，必要时携带 host epoch/operation ID。Default add 的 clone correctness floor 是 actual host center；screen clamp 不得改写 graph flow anchor；viewport/host/gesture transient 不进入 semantic graph history。

**影响：** Batch 63 已按本决策实现 actual-host default add；Batch 64 实现 Asset drawer open/close/X/Canvas-context 的 host-center anchor preservation；Batch 65 又把 desktop/compact preset 限制为 page-session bootstrap，并让用户 viewport、target canvas stored viewport、current/old canvas callback 和 finite validation 进入明确 owner guard。三批 viewport/layout 路径都不进入 graph history；窄桌面工具条碰撞仍只在 screen space clamp，不改 graph anchor。它们都不移植 Open Canvas Quick Add/drop/pending connection、菜单尺寸、缩放范围、overlay DOM 或 persistence。LibTV source 的 exact add/drawer/responsive anchor、animation、auto-pan、fit/zoom、browser resize、drag cancel、organize framing 和 mobile degradation继续留在 decision queue；full live/stable endpoint、generic generation/host epoch owner 与完整 `LIBTV-VR-020` 仍需独立授权。FrameOS React Flow viewport 与 Director 3D viewport 继续隔离。

**依据：** [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)、[`liblib-canvas-batch63-2026-08-27/`](research/liblib-canvas-batch63-2026-08-27/)、[`liblib-canvas-batch64-2026-08-27/`](research/liblib-canvas-batch64-2026-08-27/)、[`liblib-canvas-batch65-2026-08-27/`](research/liblib-canvas-batch65-2026-08-27/)、[`LibTVOverlayPositioning.contract.md`](research/components/LibTVOverlayPositioning.contract.md)、Open Canvas `OC-053..060` fixed chain。

### DEC-037：media intent、resource lease、asset 与 node reference 分权

**背景：** 当前 clone 的 Add Resource 上传/历史只是 mock；Shot Breakdown 用 component-local object URL 预览，却把 graph status 写成 ready；Director data/blob locator 又进入普通 graph/history。Open Canvas 提供 validation、metadata probe、stable URL/assetId 和 server dedupe 方法，但其 node-first drop、classifier drift、sequential partial mutation、autosaved running state和缺失 cancel/stale/cleanup 不能直接复制。当前 LibTV source 进一步证明上传、生成历史、风格/特效素材库、画布节点索引和 Personal/Agent asset 是不同 surface/owner。

**决策：** 每个媒体入口先形成 immutable ingress/attempt/canvas/node/source identity，经 canonical validation、metadata probe、materialization 和 freshness reconciliation 后，才生成完整 graph projection plan。`File`/`Blob` 和 probe/preview object URL 只存在于 instance-scoped operation/lease owner；provisional progress 不进 semantic graph/history/document。Stable asset、generated-history item、node media reference、material preset 和 session result 保持不同 identity。Multi-item ingress按 original order 收敛，accepted successes 默认 one cohort graph history；invalid/noop/stale/canceled 为 zero semantic history。Object URL 只能在 graph/history/clipboard/editor/operation 等 reachability 为零且 owner 证明 exclusive 时 exact-once release；graph delete 不推导 stable remote asset delete。

**影响：** 不因本决策接真实 provider/storage、上传、账户资产、计费或 persistence，也不把 Open Canvas MIME/size/provider/skin 当成 LibTV 产品事实。无后端 prototype 可以做 validation、local preview 和 deterministic fake materializer，但必须标明 `LOCAL_PREVIEW/UNAVAILABLE`，不能宣称 durable upload。`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01`、`LIBTV-VR-021` 与任何 runtime slice 均需明确编码授权；FrameOS 与 Director owner 继续隔离。

**依据：** [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、Open Canvas `OC-061..070` fixed chain、2026-08-27 LibTV read-only source DOM evidence。

### DEC-038：foreground editor session、local history 与 graph commit 分权

**背景：** 当前 clone 的普通编辑器形成了多个互不一致的 island：TextNode 有 local draft；ImageEditPanel 的 Prompt/reference/submitted 只存在组件内；图片标注的 Undo/Redo disabled 但 Save 看似可用且无 handler；图片编辑和字幕区域各有 30 步 local history，却分别采用延迟一次提交和即时 graph 写入；range/reshoot/camera dialog 还有不同的 cancel/reopen 行为；video toolbar 出现 enabled-looking inert Undo/Redo。Open Canvas 同样分开 inline/rich/bitmap draft 与 graph save，但其 active draft resync、40 个 full `ImageData` entry、Restore 折叠、close-first JPEG upload、node-ID-only patch 和 caller 忽略 no-op/conflict result 不能直接复制。

**决策：** 每个 foreground editor 必须声明十类 profile 之一，并在 open 时固定 route/canvas generation、session、target/source version、baseline digest 和 resource owner。Working draft 与 semantic graph 分离；dirty baseline drift 默认不被 effect 静默覆盖。Editable native history、editor-local history 和背景 graph history 按 foreground context 三选一消费 shortcut。Pointer gesture 只在 endpoint 形成一个 local history entry；accepted semantic commit 最多产生一步 graph history，或形成携带 freshness/resource owner 的 typed async handoff；invalid/noop/cancel/stale 为零 graph/history residue。Commit result 决定 close、保留或 recoverable failure，不以 panel close 代表成功。Bitmap history 同时受 entry/byte/pixel budget 约束；visible enabled control 必须有真实 handler，否则应 disabled/unavailable。

**影响：** 不因本决策引入全局 form framework、统一十类 editor schema、Open Canvas HTML/JPEG/timeout/upload/provider/persistence，也不改变未经 source 取证的 blur/Enter/Escape/outside/restore/save/close exact 行为。`LIBTV-FIX-LOCAL-EDITOR-SESSION-01`、`LIBTV-VR-022` 和任何 runtime slice 都需明确编码授权；FrameOS/Director history 与普通 LibTV editor owner 继续隔离。

**依据：** [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)、Open Canvas `OC-071..080` fixed chain、相关 LibTV component specs。

### DEC-039：media/output、node frame、rendition 与 measurement 分权

**背景：** 当前 clone 初始 landscape fixture 接近 LibTV source 的 media-shaped frame，但 generic image 把 `512x512` media 放入 `512x288` frame，多数 derived action 和 Director still capture 也会保留 media dimensions 后重置成 landscape graph frame。Node cover、detail contain、video poster/video branch 和 mark editor visible-plane 因此可能展示或编辑不同构图。Open Canvas 分开 selected output、按 surface role 使用 cover/contain 并以 measured rect 驱动 overlay，提供了可借方法；但 fixed card 由 request aspect 决定、per-output intrinsic dimensions 缺失、video probe 不对称、edited output ratio drift 和 optional serialized dimensions 不能直接复制。

**决策：** 普通 LibTV 分开 full/thumbnail media descriptor、selected output、generation request、semantic node frame、passive measured rect、surface rendition、visible media rect、editor coordinate space 和 export output。每个 media node 声明 frame policy，每个 surface 声明 fit/object-position/content-box policy。Cover/contain 是 display transform，不是 destructive crop。Mixed-ratio output switch 以一个 typed transaction 更新 identity/metadata，并按声明策略 reflow/preserve/reject；frame/rendition revision 后 stale measurement 不驱动 overlay/editor。Full-media mark 先经 visible-to-intrinsic transform；passive measurement、thumbnail/full swap 和 metadata cache refresh 不进入 semantic history。

**影响：** current source-backed landscape frame 与既有 toolbar/panel formula 保持；不以 Open Canvas fixed card/request aspect 或全局 contain 替代。Portrait/square/video/mixed-output/object-position/generic resize 继续 source/product-gated。`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01`、`LIBTV-VR-023` 和任何 runtime/schema/editor slice 都需明确编码授权；FrameOS/Director owner 继续隔离，Director 的 aspect-aware animation path仅作为 clone method evidence。

**依据：** [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)、[`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)、Open Canvas `OC-081..090` fixed chain、2026-08-27 LibTV landscape source measurements 和相关 component specs。

### DEC-040：Director project、session、runtime 与 graph projection 分权

**背景：** 当前 Director 是功能丰富的 R3F authoring island，但 `directorStore`
仍是单例；`openSession` 只替换 source node ID，scene、objects、groups、
timeline 和 captures 会跨 node 保留。Timeline seek/playback 又会把 sampled
值写回 objects，capture/export completion 在提交时 late-read active canvas。
StoryAI 和 Open Canvas 提供 versioned document、scoped owner、history 和
reference repair 的方法，也同时暴露 shallow decode、UI state persistence、
资源生命周期和 stale completion 反例。

**决策：** Director 必须分开 portable project document、session UI、runtime
projection、resource lease 和 ordinary graph projection。Portable document
具备独立 project ID、schema version、owner 与严格 decoder；session selection、
playhead、panel、recording、Three.js refs、Blob/object URL 和 graph `sentNodeId`
不得混入 document。实现顺序固定为 strict V1 codec、owner registry、
authored/runtime split、command/history/gesture authority、reference-aware delete，
再进入真实资产、panorama 和多机位。Director history 与 ordinary graph history
保持独立。

**影响：** Batch 66 已完成静态审计、两份正式合同、17-script current manifest、
`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` 与 `LIBTV-VR-024` 设计。Batch 67 已完成
V1 strict codec、snapshot adapter、runtime-field exclusion、reference validation
和 pure contract corpus。Batch 68 已完成 structured owner、in-memory project
registry、project/session/generation、A/B/cross-canvas restore、duplicate reset、
active-delete close 和 memory capture sidecar focused runtime。Batch 69 已完成
`authoredObjects` portable baseline、`objects` runtime projection、
seek/playback/path fingerprint stability、authoring restore 和 owner/graph isolation。
Batch 70 已完成 typed project-local command/history、undo/redo 和 gesture
coalescing；Batch 71 已完成 focused pointer lifecycle；Batch 72 已完成
reference-aware delete、关系闭包、相机回退、资源阻断/级联和 exact
delete/undo/redo。inactive-owner reconciliation、async destination、
copy/paste identity remap 与 persistence 仍缺。
Batch 59 继续是当前低成本 WebGL browser smoke；Batch 46/48/49/50 在
artifact/storage 隔离前只是 merge candidates。不得把 StoryAI/Open Canvas
schema、历史 verifier 或 clone screenshot 写成 LibTV source fact，也不得借下一
slice 包装全部 85 actions。

**依据：** [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](research/LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)、
[`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](research/LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)、
[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、
[`liblib-canvas-batch66-2026-08-27/`](research/liblib-canvas-batch66-2026-08-27/)、
[`liblib-canvas-batch67-2026-08-27/`](research/liblib-canvas-batch67-2026-08-27/)、
[`liblib-canvas-batch68-2026-08-27/`](research/liblib-canvas-batch68-2026-08-27/)、
StoryAI/Open Canvas 固定专题。

### DEC-041：Director semantic command、project-local history 与完整 gesture lifecycle

**背景：** Batch 67-69 已分别建立 Director V1 strict document、owner/session
隔离和 authored/runtime projection。此前 semantic mutation 没有统一的
project-local history；TransformControls、curve、Inspector、pose、path 和
free-draw 的连续输入也没有共同的 begin/update/commit/cancel 边界。

**决策：** Director semantic mutation 以 typed command result 和 portable
document fingerprint 定义 commit/no-op/reject；history 按 `projectId` 维护
bounded `past/future`，undo/redo 只恢复 Director document，不触碰普通
`canvasStore`。连续用户动作必须由显式 gesture transaction 收口：中间
preview 不生成 history，commit 最多生成一条，cancel、stale、invalid 和
same-value 产生零条。Batch 70 先落地 command kernel、undo/redo、object/group
TransformControls 与 speed-curve adapter；Batch 71 再补齐 Inspector numeric、
pose、motion-path anchor/Bezier、path transform 和 free-path draft 的真实
pointer lifecycle。

**影响：** Batch 70 将 `LIBTV-VR-024` 的同步 command/history slice 提升为
`HISTORY_FOCUSED_PASS`，Batch 71 提升 pointer lifecycle，Batch 72 提升
reference-aware delete。三批都保留 close/reopen 后同一 project 的 history
continuity、zero-partial 和普通 graph/history isolation。当前不宣称全部旧 action
已成为 typed command，也不宣称 LibTV source 已证实相同 undo/redo、删除菜单或
确认 UI。inactive-owner reconciliation、capture/export async freshness、durable
persistence、copy/paste identity remap、真实资源加载和 source-exact Director
DOM/CSS 仍是独立后续合同；Batch 72 的验收重点是 reference closure、last-camera
and resource policy、runtime cleanup 与每个 accepted destructive action 至多一条
history。

**依据：** [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](research/LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)、
[`liblib-canvas-batch70-2026-08-27/`](research/liblib-canvas-batch70-2026-08-27/)、
[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)、
`LIBTV-VR-024`。

## 3. 何时可以重审决策

只有出现以下事件之一，才需要更新对应决策，而不是在代码中悄悄绕过：

- LibTV 源站出现可重复的新交互、DOM/Bundle 结构或版本变化；
- 用户明确授权某个具体编码 slice；
- 获得可丢弃的源站/clone fixture，能够安全复现此前的未知状态；
- React Flow、Next.js 或项目路由边界发生已批准的基础设施升级；
- 其他开发者的业务接口稳定并明确需要最小测试夹具适配；
- fixture 的身份、reset/storage 边界或 verifier replacement 前置条件发生变化。

重审时必须追加新的证据、影响范围、替代方案和 commit，不得静默删除旧决策。历史 snapshot 若仍对旧 Batch 有效，保留为 `HISTORICAL`。
