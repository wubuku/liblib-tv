# Open Canvas 上游研究

> 研究对象：[`ZeroLu/open-canvas`](https://github.com/ZeroLu/open-canvas/)
> 及其官网 [`open-canvas.cyberbara.com/zh`](https://open-canvas.cyberbara.com/zh)。
> 本目录只记录研究，不代表已经授权将其能力编码进 LibTV 克隆。

## 研究锚点

| 项目 | 值 |
|---|---|
| 上游远端 | `https://github.com/ZeroLu/open-canvas.git` |
| 分支 | `main` |
| 锁定提交 | `cf3a906bb8c35bb940d3267497e7f394b8f42582` |
| 上游目录 | [`research/upstream/open-canvas`](../../../research/upstream/open-canvas) |
| 引入方式 | git submodule |
| 当前项目分支 | `master` |
| 观察日期 | 2026-08-26 |
| 实施边界 | 研究和报告；等待用户明确授权后才编码 |

## Read Order

1. [`PLAN.md`](PLAN.md)：研究问题、方法、范围和交付物。
2. [`REPORT.md`](REPORT.md)：面向项目决策的完整结论。
3. [`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md)：固定版本的目录、模块和源码证据。
4. [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md)：官网落地页和托管应用入口的只读核对。
5. [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)：OC claim ID、证据级别、可证明范围和待验证问题。
6. [`UIUX_TRANSLATION.md`](UIUX_TRANSLATION.md)：将 Open Canvas 的机制转译为 LibTV 后续 UI/UX 复刻 batch。
7. [`INTERACTION_CATALOG.md`](INTERACTION_CATALOG.md)：选中、连线、视口、复制、媒体历史、状态和 onboarding 的交互模式目录。
8. [`LIBTV_SEEDANCE_CROSSWALK.md`](LIBTV_SEEDANCE_CROSSWALK.md)：将 Open Canvas 交互启发与当前 LibTV Seedance 2.5 五条能力链逐项对照。
9. [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md)：LibTV 五个图片节点的双浮层矩阵、工具条时间版本差异和 clone 缺口。
10. [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)：当前图片工具条六个新增/末端动作的状态、呈现、副作用和 clone 差异。
11. [`LIBTV_AUTOLINK_STATE_MATRIX.md`](LIBTV_AUTOLINK_STATE_MATRIX.md)：当前 AutoLink 开关、候选、ghost suggestion、mention token 和 clone 语义缺口。
12. [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)：28%/34%/41%/50%/100% zoom 的双浮层几何、裁切和选择卸载生命周期。
13. [`../components/LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)：供后续 agent 使用的双浮层 screen/flow 定位合同与验证断言。
14. [`../components/LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)：Auto Link 候选、ghost、structured mention、竞态和 graph 事务合同。
15. [`../components/LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)：LibTV 普通连接的 normalize、result/reason、transaction、fixture 和 `VR-009` 设计权威。
16. [`../components/LibTVGraphDocument.contract.md`](../components/LibTVGraphDocument.contract.md)：runtime/history/portable document/clipboard/persistence 五层、V1 schema、strict load、snapshot isolation 和 `VR-010` 设计权威。
17. [`../components/LibTVSubgraphCopy.contract.md`](../components/LibTVSubgraphCopy.contract.md)：具名复制命令、descendant closure、two-pass identity/reference rewrite、edge policy、placement、atomic history 和 `VR-011` 设计权威。
18. [`../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)：11 类 runtime node、分散 data writer、cross-node/aggregate identity、Director/media boundary 和现有 shallow-copy 风险的 dated clone audit。
19. [`../components/LibTVNodeDataIdentity.contract.md`](../components/LibTVNodeDataIdentity.contract.md)：V0 registry、field roles、named operation profiles、aggregate/media integrity、fixture 和 `VR-012` 设计权威。
20. [`../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)：删除入口、relation inverse index、cascade/detach/reset/block、UI/resource lifecycle、fixture 和 `VR-013` 设计权威。
21. [`../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：Open Canvas 分层校验与 clone 全 graph ingress、T0-T5 authority、full-draft plan、fixture 和 `VR-014` 设计权威。
22. [`../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：Open Canvas run/poll/patch 正反面、clone delayed writer/Director completion 审计，以及 operation identity、stale/duplicate、field/history/resource ownership 和 `VR-015` 设计权威。
23. [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：共同 React Flow 12.11.1 change/reducer、Open Canvas/clone callback 对照，以及 T0/T1/semantic routing、whole-batch/current-snapshot、fixture 和 `VR-016` 设计权威。
24. [`../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)：Open Canvas list/URL/hydrate/delete/save owner 正反面、clone registry/viewport/history/UI/transient/async 审计，以及 lifecycle plan、fixture 和 `VR-017` 设计权威。
25. [`../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)：Open Canvas toast/node/save/form feedback 正反面、clone reason/string/timer/Director inventory，以及 outcome/primary-surface/owner、fixture 和 `VR-018` 设计权威。
26. [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)：Open Canvas selected flags/editable guard/Radix delegation 与 clone node/edge selection、listener phase、modal/Director focus、Batch 50 事实漂移的 fixed static audit。
27. [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：validated node/edge/primary selection、focus zone、command-context precedence、single-layer Escape、fixture 和 `VR-019` 正式设计权威。
28. [`../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)：Open Canvas dual screen/flow anchor、live/stable viewport、placement/counterexamples 与 clone coordinate domain、host center、gesture/lifecycle gap 的 fixed audit。
29. [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：actual host、six coordinate domains、live/stable/bootstrap/target viewport、gesture/placement/resize owner、fixture 和 `VR-020` 正式设计权威。
30. [`../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)：Open Canvas validation/probe/upload/dedupe/save 正反面、clone local-preview/blob-data 路径，以及 LibTV source upload/history/material/asset 分域的 dated audit。
31. [`../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)：十类 entry profile、validation/probe/materialization、temporary lease、asset/reference、cohort transaction、reachability/release、fixture 和 `VR-021` 正式设计权威。
32. [`libtv-media-ingress-source-dom-audit-2026-08-27.json`](libtv-media-ingress-source-dom-audit-2026-08-27.json)：当前 LibTV source 上传、生成历史、素材库、资产管理和 Shot Breakdown 的只读 DOM 原始记录及安全边界。
33. [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md)：本专题的问题拆解、执行顺序、停止条件、里程碑 commit 和完成记录。
34. [`../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)：Open Canvas bitmap/text editor、save/upload handoff 正反面与 clone draft/local-history/inert command/graph gateway 的 dated audit。
35. [`editor-session-static-evidence-2026-08-27.json`](editor-session-static-evidence-2026-08-27.json)：`OC-071..080` 与 `LIBTV-EDS-001..014` 的固定路径、事实和迁移边界原始清单。
36. [`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)：十类 editor profile、session/baseline/draft、native/local/graph undo、commit/cancel、async/resource handoff、fixture 和 `VR-022` 正式设计权威。
37. [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_RESEARCH_PLAN_2026-08-27.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_RESEARCH_PLAN_2026-08-27.md)：本专题的问题拆解、执行顺序、停止条件、里程碑 commit 和完成记录。
38. [`../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)：media intrinsic/output/request-aspect/node-frame/measured/rendition 分权、Open Canvas 正反面、clone collision 与 LibTV source read-only 尺寸审计。
39. [`media-rendition-geometry-static-evidence-2026-08-27.json`](media-rendition-geometry-static-evidence-2026-08-27.json)：`OC-081..090`、`LIBTV-MRG-001..014` 和 source `LIBTV-MRG-SRC-001..006` 的机器可读路径与测量记录。
40. [`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)：media/output/request/frame/measured/rendition 权威、fit transform、mixed-ratio output、measurement freshness、fixture 和 `VR-023` 正式设计权威。
41. [`ADOPTION_DECISION_MATRIX.md`](ADOPTION_DECISION_MATRIX.md)：将上游机制映射为 `ADOPT_METHOD`、`ADAPT_TO_LIBTV`、`RESEARCH_ONLY`、`DEFER` 或 `REJECT_TRANSPLANT`，并对齐当前 parity、fixture 和 verifier。
42. [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md)：将高价值机制拆成证据、身份、事务、surface、fixture、verifier 和 provenance 七层实施交接包。
43. [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md)：逐帧拉片、片段重拍和长视频的身份、authoring/node/run/result/save 正交状态、fixture 与 `VR-007` 合同。
44. [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)：模型目录、Seedance 2.5 authoring controls、clone state、descriptor 与真实 runner 的分层审计。
45. [`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md)：35-row current loaded DOM catalog、current-context style split 和 per-model control 停止点。
46. [`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](UPSTREAM_VERSION_IMPACT_PROTOCOL.md)：未来比较/更新上游 commit 时的 claim、pattern、adoption、runtime 和 submodule pointer 影响审计协议。
47. [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](NEXT_EVIDENCE_ACQUISITION_PLAN.md)：将 source freshness、模型能力、graph decision、Auto Link/process/media/editor fixture 和上游版本 diff 组织为带停止条件的证据队列。
48. [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](LIBTV_SOURCE_FRESHNESS_2026-08-27.md)：`OC-EQ-001` 的 41% 标准图片双浮层新日期只读样本、几何残差和自然裁切证据。
49. [`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md)：`OC-EQ-003` 的 LibTV DOM Handle、edge identity、方向归一化、duplicate/self-loop/cycle 和 action/type validator 静态证据。
50. [`libtv-graph-compatibility-static-audit-2026-08-27.json`](libtv-graph-compatibility-static-audit-2026-08-27.json)：graph compatibility 原始结构化采样、bundle 坐标和未决边界。
51. [`IMPLEMENTATION_IMPLICATIONS.md`](IMPLEMENTATION_IMPLICATIONS.md)：第一阶段候选实施清单、收益、风险和待授权队列；保留 Batch A-E provenance，不再作为当前编号入口。
52. [`OPEN_CANVAS_PATTERN_CARDS.md`](OPEN_CANVAS_PATTERN_CARDS.md)：十三类可迁移模式卡，新增 selected output、frame/rendition、measurement freshness 与 editor transform，继续区分上游启发、LibTV 证据、clone 决策和验证门槛。
53. [`ITERATION_LOG.md`](ITERATION_LOG.md)：研究报告版本和维护历史。
54. [`../liblib-canvas-batch55-2026-08-26/`](../liblib-canvas-batch55-2026-08-26/README.md)：`OC-EQ-001` freshness 接管尝试、登录态阻塞和可接力停止条件。

## 当前结论摘要

`open-canvas` 的高价值不在于复刻 LibTV 的具体视觉皮肤，而在于它把“可见节点画布”做成了一套可运行、可导入导出、可本地持久化、可替换 provider 的工作流内核。其核心边界如下：

- React Flow 负责空间交互，Zustand 负责画布文档与保存/冲突状态。
- 图模型只允许 `note`、`text`、`image`、`video`、`audio` 五类节点，边经过方向归一化和 DAG 校验。
- 节点执行先解析上游引用，再生成 task descriptor，服务端记录 run，前端对异步任务轮询。
- provider 是 BYOK 适配层：Cyberbara、OpenRouter、Replicate；媒体上传另有 Cyberbara/S3-compatible storage。
- local-first 不是纯浏览器 demo：默认使用文件 JSON，Cloudflare 运行时切换到 KV，并保留 API 路由、revision 和 conflict 语义。
- 官网当前应用入口首先要求配置 provider Key；没有 Key 时仍可读到产品骨架，但不能把“可生成”误判为无需后端配置的能力。
- LibTV 当前图片工具条已从 2026-08-25 的 7 个文字动作、`900.5px` 扩展为 9 个文字动作、`1092.5px`；clone 仍冻结在旧宽度和旧动作集合，详见双浮层矩阵。
- 当前工具条还包含 preview overlay、可替换标准双浮层的标注/旋转/元素编辑工具态，以及可能提交任务的图层分离；不能继续用统一 `addDerivedNode` 语义概括。
- 当前 AutoLink 是高级设置中的全局偏好，加上 Prompt 内联 ghost suggestion 和带稳定 node ID 的正式 mention；clone 的固定候选弹窗、全量接受和字符串前缀写回不是源站现行合同。
- 多 zoom 复测确认下方面板 gap 是 `16 * zoom`，上下浮层都保持 node-center anchor；当前生产 chunk 已确认顶部 host 使用 `nodeTop - 24 * zoom - 10` 加 `translateY(-100%)`，所以 28%/34%/41%/50% 的 gap 约为 `16.794/18.152/19.778/22px`，不能用 clone 当前固定 `offset=16` 直接代表源站合同。
- 当前 LibTV graph connection boundary 已在 production bundle 中静态确认 pair duplicate guard、普通非 Reference 的 DFS cycle guard、equal-ID programmatic guard、target-start 方向归一化和 action/type/model/capacity validator；clone 侧 result/reason/transaction、local fixture 和 `VR-009` 设计已完成；Reference、导入/批量/同步入口及 invalid lifecycle 仍需 disposable source fixture，不能仅凭静态结果关闭 `GI-004..007`。
- 当前 clone graph document/snapshot 已形成五层设计：runtime、history、portable document、clipboard packet、future persistence envelope；V1 schema、strict load、nested isolation、`GRAPH-DOCUMENT-01` 和 `VR-010` 已完成文档设计，runtime/import/export/persistence 均未实现。
- 当前 clone subgraph copy 已形成具名命令、descendant closure、two-pass identity/reference rewrite、parent detach/remap、edge policy、flow placement 和 atomic history 设计；`SUBGRAPH-COPY-01` 与 `VR-011` 已定义，现有 Batch 3/5/8 runtime 只属 partial，system clipboard/Option-drag 仍未实现或待 source fixture。
- 当前 clone node data 已完成 11-type static inventory 和 V0 registry design：shot reciprocal refs、long-video process cohort、Director shell/workspace、repo/https/data/blob media 与七类 named operation policy 已落档；`NODE-DATA-01` / `VR-012` 已定义，runtime 仍是 generic Node/Record + shallow spread。
- 当前 clone delete/repair 已形成 relation-aware design：Open Canvas 的 centralized selection/incident deletion 只作方法输入，LibTV 额外计算 parent、owned refs、shot/process aggregate、UI owner 和 resource impact；`GRAPH-DELETE-01` / `VR-013` 已定义，runtime planner 与 source cascade/detach decisions 未实现。
- 当前 clone graph ingress 已完成全入口 static audit：Batch 57 只保护 connection/addEdge island；derived/process/copy/delete、generic setters、React Flow changes 和 history restore 仍是 partial/bypass。Open Canvas 的 store/save/API/revision/server-patch 分层可借方法，但其 clipboard/framework delta 缺口也被保留；T0-T5、`GRAPH-ENTRYPOINT-01` / `VR-014` 已定义，runtime migration 未授权。
- 当前 React Flow change routing 已从 graph ingress 中独立细化：两项目都锁定 12.11.1；Open Canvas 使用 functional current store state 值得采纳，但 generic 接受全部 non-select variant 不值得复制。Clone 的 T0 selection、T1 existing-node position/passive measurement、semantic add/remove/replace/reconnect reroute、whole-batch zero-partial、runtime-field sanitation、`REACT-FLOW-CHANGES-01` / `VR-016` 已定义，runtime adapter 未收窄。
- 当前 multi-canvas lifecycle 已完成 cross-owner 静态审计：Open Canvas 的 list summary/URL document/hydrate/viewport/delete-run cleanup 可借方法，但 old-route save local convergence 缺少 expected current canvas guard；clone 已有 Batch 16 CRUD、per-canvas graph/viewport/history 和 Batch 58 node-bound cleanup，但 invalid target、page-local transient、responsive preset、delayed destination 和 resource impact 仍 partial。`CANVAS-LIFECYCLE-01` / `VR-017` 已定义，runtime planner 未授权。
- 当前 command outcome/feedback 已完成跨层静态审计：Open Canvas 的 toast、node status/error、save/conflict、field error/pending 分层可借，但 localized message lookup 和无 owner async toast 是反例；clone 有 connection reason、surface string、VideoNode timer 与 Director persistent islands，但无共同 disposition/primary-surface/owner authority。`COMMAND-FEEDBACK-01` / `VR-018` 已定义，runtime adapter 与 exact source feedback 未授权/未取证。
- 当前 async ingress 已完成 fixed Open Canvas 与 committed clone 双向审计：上游 descriptor/run/runId polling/server patch/revision/saved baseline 可借方法，但 patch 不校验 expected run/source version/field owner，terminal run 与 graph projection 非原子；clone 多数 graph-producing delay 仍是 component timer，Director 才有真实 browser async asset。`ASYNC-INGRESS-01` / `VR-015` 已定义，runtime/provider 均未授权。
- 当前采纳治理已进一步区分“借鉴方法”和“移植实现”：坐标域、稳定身份、状态分层和结构化 graph transaction 可进入设计评审；Open Canvas 的视觉皮肤、provider/key、保存语义和未被 LibTV 证实的 Quick Add 行为不能直接进入 clone。
- 当前 viewport/coordinate/gesture/placement 已形成正式权威：actual host、six domain、live/stable/bootstrap/target、generation-bound session、entry placement、resize、fixture/`VR-020` 均已落档；runtime/source parity 仍 partial。
- 当前 media ingress/resource lifecycle 已形成正式权威：Open Canvas validation/probe/materialization/descriptor 正面方法与 classifier drift、placeholder-first、partial commit、autosaved running、no cleanup 反例均已固定；LibTV source upload/history/material/asset/Shot 分域、clone mock/local-preview/data/blob islands、ten entry profiles、asset/reference/lease/reachability、fixture/`VR-021` 均已落档；runtime missing/partial、source parity partial，provider/storage/upload 保持边界外。
- 当前 editor session/commit/history 已形成正式权威：Open Canvas 的 session identity、gesture-level bitmap history、no-op guard、bounded decode 值得借鉴，但 entry-only bitmap budget、close-before-upload、node-only completion 和 active-draft resync 不可照搬；clone 十类 profile、native/local/graph undo、baseline drift、typed commit、async/resource handoff、40 invariants、fixture/`VR-022` 均已落档，runtime fragmented、source parity partial。
- 当前 media rendition/aspect/node geometry 已形成正式权威：Open Canvas selected output/surface-role fit/measured anchor 可借，request-shaped card、missing per-output dimensions、probe asymmetry 和 edited-output drift 是反例；LibTV source landscape media-shaped frame、clone generic/derived/Director still collision、fit transform、measurement freshness、42 invariants、fixture/`VR-023` 均已落档，runtime fragmented、ratio-diverse source parity gated。

本次研究不修改 `src/`、不修改上游 submodule 内容、不执行生成或上传、不创建官网画布。

## Authority Map

| 想确认什么 | 当前唯一入口 | 维护边界 |
|---|---|---|
| 固定 submodule 证明了什么 | [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md)、[`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md) | 新上游版本另做 diff，不静默移动本次基线 |
| 官网运行态实际观察到什么 | [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md) | 带日期追加，不用源码推断替换 live observation |
| 哪些一般机制值得研究 | [`OPEN_CANVAS_PATTERN_CARDS.md`](OPEN_CANVAS_PATTERN_CARDS.md)、[`INTERACTION_CATALOG.md`](INTERACTION_CATALOG.md) | 只提供机制，不提供 LibTV 产品真相 |
| 一个机制采纳、改造、暂缓还是拒绝 | [`ADOPTION_DECISION_MATRIX.md`](ADOPTION_DECISION_MATRIX.md) | 当前采纳状态权威；旧文档不得另起状态词表 |
| 获批后怎样形成最小 LibTV slice | [`LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md) | 七层交接和 `OC-BP-*` 权威；不代替具体组件合同 |
| Auto Link identity/session/fixture | [`../components/LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md) | typed editor 和 `VR-003..005` 权威 |
| Graph invariant/connection compatibility | [`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#10-libtv-par-008-invariant-and-compatibility-design)、[`../components/LibTVGraphConnection.contract.md`](../components/LibTVGraphConnection.contract.md)、[`LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md`](LIBTV_GRAPH_COMPATIBILITY_STATIC_AUDIT_2026-08-27.md) | catalog 管 `GI/GC`；connection contract 管 result/reason/transaction/fixture/`VR-009`；source-decision 项保持未决 |
| Graph document/snapshot | [`../components/LibTVGraphDocument.contract.md`](../components/LibTVGraphDocument.contract.md)、[`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#106-graph-document-and-snapshot-handoff) | 五层 shape、V1 schema、strict load、history isolation、fixture/`VR-010` 权威；persistence deferred |
| Graph subgraph copy/duplicate | [`../components/LibTVSubgraphCopy.contract.md`](../components/LibTVSubgraphCopy.contract.md)、[`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#107-subgraph-copy-and-duplicate-handoff) | 具名命令、closure、two-pass identity/reference rewrite、edge/placement/history policy、fixture/`VR-011` 权威；incident edge 是 compatibility hold，Option-drag 保持 source-blocked |
| Graph node data identity/aggregate | [`../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](../LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)、[`../components/LibTVNodeDataIdentity.contract.md`](../components/LibTVNodeDataIdentity.contract.md)、[`../LIBTV_GRAPH_TRANSACTION_CATALOG.md`](../LIBTV_GRAPH_TRANSACTION_CATALOG.md#108-node-data-identity-and-aggregate-handoff) | dated clone facts + 11-type V0 registry、field/operation/aggregate/media policy、fixture/`VR-012` 权威；runtime/schema/delete decisions remain missing |
| Graph delete/reference repair | [`../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](../LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md) | command/relation/aggregate/UI/resource impact、policy queue、`GRAPH-DELETE-01` / `VR-013` 权威；runtime missing，source/product cascade/detach 保持未决 |
| Graph mutation entrypoint authority | [`../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](../LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md) | Open Canvas layered boundary/limitations、clone writer inventory、T0-T5、decision queue、`GRAPH-ENTRYPOINT-01` / `VR-014` 权威；runtime partial，persistence/remote deferred |
| React Flow change routing | [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) | exact 12.11.1 variant/reducer、whole-batch T0/T1 classification、current snapshot、selection/history/runtime-field sanitation、`REACT-FLOW-CHANGES-01` / `VR-016` 权威；runtime partial，resize/reconnect blocked |
| Multi-canvas lifecycle/isolation | [`../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md) | project/document/history/session/external owner、CRUD/switch plan、reconciliation manifest、transient/async/resource race、`CANVAS-LIFECYCLE-01` / `VR-017` 权威；runtime partial，source final/fallback/panel decisions open |
| Command outcome/feedback | [`../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) | disposition/reason/copy、primary field/node/surface/canvas/transient owner、clear/retry/dedupe、history/accessibility/route isolation、`COMMAND-FEEDBACK-01` / `VR-018` 权威；runtime partial，exact source toast/invalid style/timeout open |
| Selection/focus command context | [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)、[`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md) | fixed facts + validated selection、focus zone、context precedence、dispatch result、single-layer Escape、fixture/`VR-019` 权威；design complete/runtime partial，exact source interactions partial |
| Viewport/coordinate/gesture/placement | [`../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)、[`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | dated facts + actual host、six domain、live/stable/bootstrap/target、gesture/placement/resize owner、fixture/`VR-020` authority；runtime/source parity partial，Quick Add/drop remain gated |
| Media ingress/resource lifecycle | [`../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)、[`../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)、[`libtv-media-ingress-source-dom-audit-2026-08-27.json`](libtv-media-ingress-source-dom-audit-2026-08-27.json) | Open Canvas/source/clone facts + intent/lease/asset/reference/cohort/reachability authority、fixture/`VR-021`；runtime missing/partial、source exact lifecycle partial，real upload/storage/provider out of scope |
| Editor session/draft/local history | [`../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)、[`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)、[`editor-session-static-evidence-2026-08-27.json`](editor-session-static-evidence-2026-08-27.json) | dated facts + ten profiles、session/baseline/draft、native/local/graph undo、commit/close/async/resource、fixture/`VR-022` 权威；runtime fragmented、exact source interaction partial |
| Media rendition/aspect/node geometry | [`../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)、[`../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](../LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)、[`media-rendition-geometry-static-evidence-2026-08-27.json`](media-rendition-geometry-static-evidence-2026-08-27.json) | dated facts + ten authorities、frame/rendition profile、fit transform、mixed-ratio switch、measurement freshness、fixture/`VR-023` 权威；runtime fragmented、source portrait/square/video/resize parity gated |
| Process/result identity/state | [`LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](LIBTV_PROCESS_RESULT_STATE_MATRIX.md) | `LIBTV-PR-*`、stale/retry、`VR-007` 权威 |
| Async completion ingress/convergence | [`../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md) | operation/run/result/source-version、freshness、field/history/resource ownership、`ASYNC-INGRESS-01` / `VR-015` 权威；runtime missing，provider out of scope |
| Model UI/descriptor/runner 边界 | [`LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)、[`LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md`](LIBTV_MODEL_CATALOG_FRESHNESS_2026-08-27.md) | capability projection authority + dated 35-row catalog；不等于 runner |
| 下一条证据如何安全取得 | [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](NEXT_EVIDENCE_ACQUISITION_PLAN.md) | `OC-EQ-*` 顺序、允许动作、停止条件和交付模板权威；不维护第二套 parity |
| 最新 LibTV 标准图片 freshness | [`LIBTV_SOURCE_FRESHNESS_2026-08-27.md`](LIBTV_SOURCE_FRESHNESS_2026-08-27.md)、[`../liblib-canvas-batch55-2026-08-26/`](../liblib-canvas-batch55-2026-08-26/README.md) | 41%/929x874/既有选中态证据仍有效；Batch 55 接管失败，不产生新的 source claim |
| 当前优先级与授权状态 | [`../LIBTV_UIUX_PARITY_BACKLOG.md`](../LIBTV_UIUX_PARITY_BACKLOG.md)、[`../liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md) | Open Canvas 目录不维护第二套当前排期 |
| 第一阶段为何按 A-E 排过 | [`IMPLEMENTATION_IMPLICATIONS.md`](IMPLEMENTATION_IMPLICATIONS.md) | 仅保留历史 provenance，不新增 A-E 条目 |
| 上游 commit 变化后哪些结论失效 | [`UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](UPSTREAM_VERSION_IMPACT_PROTOCOL.md) | 先比较 immutable SHA；未经批准不移动 submodule pointer |

## Research Completeness Boundary

在固定 commit 和当前只读证据范围内，以下文档工作已经完成：

- 产品/源码/运行态深度报告；
- Open Canvas claim 与不可推出结论；
- interaction/pattern 到 LibTV 的 crosswalk；
- 采纳/改造/拒绝治理；
- 单 slice 七层交接；
- Auto Link fixture、graph invariant、graph connection validation、graph document/snapshot、subgraph copy、node data identity/aggregate、relation-aware delete/repair、graph entrypoint authority、React Flow change routing、multi-canvas lifecycle、process/result state、async result ingress、viewport/coordinate/placement、media ingress/resource lifecycle、editor session/commit/history 和 model capability design-first 合同。
- `OC-EQ-003` 的 graph Handle/edge compatibility 静态审计；当前普通连接 path 的 guard 已有 bundle 证据，交互 fixture 仍未完成。

剩余高价值问题主要是证据或 fixture 工作，不是“缺一份文档”；统一执行入口见 [`NEXT_EVIDENCE_ACQUISITION_PLAN.md`](NEXT_EVIDENCE_ACQUISITION_PLAN.md)：

1. `LIBTV-PAR-005` 的新日期 source freshness：41% 标准图片场景已记录，page shell、selection transition、多 zoom/mobile 仍待补；
2. `LIBTV-FIX-SOURCE-AUTOLINK-01` 的输入/IME/accept 行为；
3. LibTV Reference、import/batch/sync、invalid feedback 与真实 self-loop/cycle/Handle cleanup 的 disposable source decision（static phase 和 clone design 已记录）；
4. `LIBTV-FIX-SOURCE-GRAPH-DELETE-01` 的 derived/shot/process/semantic-edge cascade、detach、confirmation 和 undo 决策；
5. `LIBTV-FIX-SOURCE-PROCESS-01` 的 partial/retry/result replacement；
6. 非 Seedance 2.5 模型逐项 mode/control capability：35-row catalog 已记录，逐模型 controls 仍未选择；
7. `LIBTV-FIX-SOURCE-MEDIA-INGRESS-01` 的 exact limits/reason、progress/cancel/retry、multi-file placement、replace retention、asset registration 和 refresh restoration；共享画布只读，不上传；
8. `OC-EQ-008` / `LIBTV-FIX-SOURCE-EDITOR-SESSION-01` 的 dirty close、local/global undo、redo invalidation、reset、text commit、save failure/retry 和 source drift；共享画布保持只读，需 disposable fixture/明确动作授权；
9. Open Canvas 上游 commit 变化后的 impact diff。

没有新证据时，应更新现有 claim 的状态、fixture blocker 或未决问题，不再新建同主题总览、最终版或第二套 backlog。获得新证据后，优先追加到对应 authority document，再更新 traceability、parity、fixture 和 verifier 入口。
