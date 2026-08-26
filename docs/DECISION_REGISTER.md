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

## 3. 何时可以重审决策

只有出现以下事件之一，才需要更新对应决策，而不是在代码中悄悄绕过：

- LibTV 源站出现可重复的新交互、DOM/Bundle 结构或版本变化；
- 用户明确授权某个具体编码 slice；
- 获得可丢弃的源站/clone fixture，能够安全复现此前的未知状态；
- React Flow、Next.js 或项目路由边界发生已批准的基础设施升级；
- 其他开发者的业务接口稳定并明确需要最小测试夹具适配；
- fixture 的身份、reset/storage 边界或 verifier replacement 前置条件发生变化。

重审时必须追加新的证据、影响范围、替代方案和 commit，不得静默删除旧决策。历史 snapshot 若仍对旧 Batch 有效，保留为 `HISTORICAL`。
