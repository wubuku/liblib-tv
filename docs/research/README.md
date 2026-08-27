# Research Index

> 原站事实、组件规格、截图台账、原始 JSON、批次计划和实施历史的统一入口。

## How To Read

1. Start with the route-specific overview.
2. Search for an existing `SCREENSHOT_ANALYSIS.md` before opening a screenshot.
3. Read a component spec before modifying its source.
4. Treat raw JSON as evidence, not as a current runtime contract by itself.
5. Keep source fact, inference and clone decision separate.

## Route Research

### LibTV

- [`liblib-live-2026-08-25/`](liblib-live-2026-08-25/README.md)：登录态原站总体审计、节点/边/面板 JSON 和差距排序。
- [`liblib-seedance-2.5-2026-08-25/`](liblib-seedance-2.5-2026-08-25/README.md)：Seedance 2.5 能力背景、原站复核、证据图和实现历史。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md`](liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md)：LibTV 五项主推能力的源站呈现、clone 缺口、价值排序和后续闸门。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md)：现有回归脚本与当前源站合同的覆盖矩阵及历史断言边界。
- [`liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md`](liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md)：获批的研究-only 执行计划、安全边界、产出顺序和授权门槛。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)：LibTV UI 状态层级、浮层替换、预览和 graph mutation 转换合同。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md`](liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md)：五项主推能力的共享底座、依赖关系、风险登记和研究优先级队列。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`](liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md)：编码授权前的继续研究、授权条件、fixture 规格和停止闸门。
- [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)：从 LibTV/Open Canvas 主张反查证据、适用范围、fixture/reset/source-write 边界和不可推出的结论。
- [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)：Batch verifier、源站合同、clone fixture、fixture 阻塞和并行 WIP 的验证成熟度台账。
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：源站快捷键文案、clone 帮助面板、实际监听器、React Flow gesture 和上下文优先级对照。
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)：用户动作、store action、nodes/edges/selection/history 副作用和证据边界目录。
- [`components/LibTVGraphConnection.contract.md`](components/LibTVGraphConnection.contract.md)：普通连接方向归一化、validation result/reason、零 mutation reject、one-step transaction、fixture 和 `LIBTV-VR-009` 设计合同。
- [`components/LibTVGraphDocument.contract.md`](components/LibTVGraphDocument.contract.md)：runtime/history/portable document/clipboard/persistence 五层、V1 schema、strict load、snapshot isolation 和 `LIBTV-VR-010` 设计合同。
- [`components/LibTVSubgraphCopy.contract.md`](components/LibTVSubgraphCopy.contract.md)：具名 copy command、group/child closure、node/edge/reference map、edge policy、flow placement 和 `LIBTV-VR-011` 设计合同。
- [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)：普通 LibTV 11 类 runtime node、identity/reference-bearing fields、shot/process aggregate、Director/media boundary 和 schema drift 的固定代码审计。
- [`components/LibTVNodeDataIdentity.contract.md`](components/LibTVNodeDataIdentity.contract.md)：11-type V0 registry、field roles、named operation profiles、shot/process aggregate、Director/media portability、fixture 和 `LIBTV-VR-012` 设计合同。
- [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)：普通 graph node/edge/selection/canvas 删除影响、relation-aware repair planner、shot/process/derived policy queue、`GRAPH-DELETE-01` 和 `LIBTV-VR-013` 设计合同。
- [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：Open Canvas store/save/API 分层与 clone 全 graph mutation ingress 的固定审计，定义 T0-T5、入口 policy、`GRAPH-ENTRYPOINT-01` 和 `LIBTV-VR-014`。
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：Open Canvas execute/run/poll/patch 的正反面证据、clone graph-producing timer/Director completion 审计，以及 operation/result envelope、stale/duplicate 收敛、`ASYNC-INGRESS-01` 和 `LIBTV-VR-015`。
- [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：两个项目共同锁定的 React Flow 12.11.1 change/reducer 语义、clone callback 旁路，以及 T0 selection、T1 node transport、T2/T3 semantic routing、`REACT-FLOW-CHANGES-01` 和 `LIBTV-VR-016`。
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)：Open Canvas summary/full record、URL/hydrate/delete/save owner 与 clone 多画布 registry/document/history/session/resource 边界，定义 switch manifest、`CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017`。
- [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)：Open Canvas command/toast/node/save/form feedback 与 clone local status/timer/Director 审计，定义 disposition/reason/copy、primary surface、owner、clear/retry/dedupe、`COMMAND-FEEDBACK-01` 和 `LIBTV-VR-018`。
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：top-level、route-local、节点相对和 Director surfaces 的 state、mount owner、关闭路径、键盘边界及兼容残留目录。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：当前全路由 UI/UX 差距、价值/证据/风险/验证准备度排序、依赖、工作波次和停止条件。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：本地 baseline、空画布 UI 构造、transaction-derived、Director 和源站只读/disposable fixture 的统一身份与 reset 合同。
- [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)：`PAR-005` 源站 page shell、baseline、overlay、lifecycle 和 responsive 的只读复核 runbook。
- [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)：历史 clone 断言的保留/降级/替换矩阵、fixture 前提和授权后的迁移顺序。
- [`open-canvas-2026-08-26/`](open-canvas-2026-08-26/README.md)：ZeroLu/open-canvas 固定版本 submodule、官网运行态和深度源码调研。
- [`open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)：八类可迁移模式卡，覆盖几何、typed input、状态分层、subgraph identity、stale-safe result ingress、framework change routing、多画布 lifecycle 和 command feedback，并区分上游启发、LibTV 证据和 clone 验证闸门。
- [`components/`](components/)：LibTV 组件规格，包括节点、面板、工具条和对话框。
- [`components/COVERAGE_MATRIX.md`](components/COVERAGE_MATRIX.md)：源码组件到组件合同、批次证据、验证状态和文档缺口的反向索引。
- [`COMPONENT_INVENTORY.md`](COMPONENT_INVENTORY.md)：当前 clone 的权威组件清单；先用覆盖矩阵判断应读哪个合同。

### FrameOS

- [`frameos/`](frameos/README.md)：FrameOS 原站抽取、视觉 token、行为、组件清单、运行手册和原始 JSON。
- [`frameos/IMPLEMENTATION.md`](frameos/IMPLEMENTATION.md)：设计决策与已知 prototype 边界。
- [`frameos/RUNBOOK.md`](frameos/RUNBOOK.md)：调试、扩展和浏览器诊断路径。

## Batch History

| Batch | Focus | Entry |
|---|---|---|
| 3 | command history, context menu, keyboard shortcuts | [`liblib-canvas-batch3-2026-08-25/`](liblib-canvas-batch3-2026-08-25/) |
| 4 | grouping and multi-selection | [`liblib-canvas-batch4-2026-08-25/`](liblib-canvas-batch4-2026-08-25/) |
| 5 | movement transactions and selection copy | [`liblib-canvas-batch5-2026-08-25/`](liblib-canvas-batch5-2026-08-25/) |
| 6 | marquee selection and navigation gestures | [`liblib-canvas-batch6-2026-08-25/`](liblib-canvas-batch6-2026-08-25/) |
| 7 | source-like organize topology and confirmation | [`liblib-canvas-batch7-2026-08-25/`](liblib-canvas-batch7-2026-08-25/) |
| 8 | video group parent-child hierarchy | [`liblib-canvas-batch8-2026-08-25/`](liblib-canvas-batch8-2026-08-25/) |
| 9 | selected-node floating UI anchor geometry | [`liblib-canvas-batch9-2026-08-25/`](liblib-canvas-batch9-2026-08-25/) |
| 10 | image editor five-state matrix | [`liblib-canvas-batch10-2026-08-25/`](liblib-canvas-batch10-2026-08-25/) |
| 11 | top-level overlay exclusivity and lifecycle | [`liblib-canvas-batch11-2026-08-25/`](liblib-canvas-batch11-2026-08-25/) |
| 12 | asset manager canvas/assets tabs and local media selection | [`liblib-canvas-batch12-2026-08-25/`](liblib-canvas-batch12-2026-08-25/) |
| 13 | storyboard mode data binding and key-elements/storyboard layout | [`liblib-canvas-batch13-2026-08-25/`](liblib-canvas-batch13-2026-08-25/) |
| 14 | Agent drawer and share panel source-shaped structure and local feedback | [`liblib-canvas-batch14-2026-08-25/`](liblib-canvas-batch14-2026-08-25/) |
| 15 | add-node source-shaped entries, audio renderer and material submenu | [`liblib-canvas-batch15-2026-08-25/`](liblib-canvas-batch15-2026-08-25/) |
| 16 | project metadata and multi-canvas navigation lifecycle | [`liblib-canvas-batch16-2026-08-25/`](liblib-canvas-batch16-2026-08-25/) |
| 17 | asset drawer project/canvas context, hierarchy and local browse controls | [`liblib-canvas-batch17-2026-08-25/`](liblib-canvas-batch17-2026-08-25/) |
| 18 | source-shaped zoom menu commands and unified overlay lifecycle | [`liblib-canvas-batch18-2026-08-25/`](liblib-canvas-batch18-2026-08-25/) |
| 19 | minimap trigger anchoring, source-shaped visuals and responsive avoidance | [`liblib-canvas-batch19-2026-08-25/`](liblib-canvas-batch19-2026-08-25/) |
| 20 | source-shaped 720° panorama derived node and specialized generation panel | [`liblib-canvas-batch20-2026-08-25/`](liblib-canvas-batch20-2026-08-25/) |
| 21 | Seedance normal/long-video parameter dialog geometry and control hierarchy | [`liblib-canvas-batch21-2026-08-25/`](liblib-canvas-batch21-2026-08-25/) |
| 22 | Seedance source-visible model menu geometry, item set and selected-row hierarchy | [`liblib-canvas-batch22-2026-08-25/`](liblib-canvas-batch22-2026-08-25/) |
| 23 | Seedance segment-reshoot filmstrip, prompt tokens and empty-intent rerun semantics | [`liblib-canvas-batch23-2026-08-25/`](liblib-canvas-batch23-2026-08-25/) |
| 24 | shot-breakdown persistent storyboard, motion and music result groups | [`liblib-canvas-batch24-2026-08-25/`](liblib-canvas-batch24-2026-08-25/) |
| 25 | video-clip empty node and node-anchored prompt editor | [`liblib-canvas-batch25-2026-08-25/`](liblib-canvas-batch25-2026-08-25/) |
| 26 | smart-continuation range selector, derived video target and graph lifecycle | [`liblib-canvas-batch26-2026-08-25/`](liblib-canvas-batch26-2026-08-25/) |
| 27 | smart/region subtitle-erase panel, rectangle editor and pending target graph | [`liblib-canvas-batch27-2026-08-25/`](liblib-canvas-batch27-2026-08-25/) |
| 28 | source-backed audio/video split menu, busy state and multi-output graph | [`liblib-canvas-batch28-2026-08-25/`](liblib-canvas-batch28-2026-08-25/) |
| 29 | first/last/current video-frame capture menus and source-linked image outputs | [`liblib-canvas-batch29-2026-08-25/`](liblib-canvas-batch29-2026-08-25/) |
| 30 | subject-edit menu correction and smart-matting pending video graph | [`liblib-canvas-batch30-2026-08-25/`](liblib-canvas-batch30-2026-08-25/) |
| 31 | subject remove/modify/replace marking editor and pending edit graph | [`liblib-canvas-batch31-2026-08-26/`](liblib-canvas-batch31-2026-08-26/) |
| 32 | depth motion capture reference workflow and pending graph | [`liblib-canvas-batch32-2026-08-26/`](liblib-canvas-batch32-2026-08-26/) |
| 33 | long-video canvas process graph, candidate batches and final pending handoff | [`liblib-canvas-batch33-2026-08-26/`](liblib-canvas-batch33-2026-08-26/) |
| 34 | existing LibTV director-desk replication archaeology, source delta and reuse plan | [`liblib-canvas-batch34-2026-08-26/`](liblib-canvas-batch34-2026-08-26/) |
| 35 | real R3F director workspace, camera framing, capture and canvas return | [`liblib-canvas-batch35-2026-08-26/`](liblib-canvas-batch35-2026-08-26/) |
| 36 | source-backed director timeline, typed keyframes and live R3F playback | [`liblib-canvas-batch36-2026-08-26/`](liblib-canvas-batch36-2026-08-26/) |
| 37 | director preset motion paths, path playback and speed curves | [`liblib-canvas-batch37-2026-08-26/`](liblib-canvas-batch37-2026-08-26/) |
| 38 | director pencil/pen paths and editable anchors/Bezier handles | [`liblib-canvas-batch38-2026-08-26/`](liblib-canvas-batch38-2026-08-26/) |
| 39 | director path-level position/rotation/scale and reset semantics | [`liblib-canvas-batch39-2026-08-26/`](liblib-canvas-batch39-2026-08-26/) |
| 40 | director browser-recorded animation export and playable canvas video return | [`liblib-canvas-batch40-2026-08-26/`](liblib-canvas-batch40-2026-08-26/) |
| 41 | director phone virtual-camera local preview, pose recording and camera-track import | [`liblib-canvas-batch41-2026-08-26/`](liblib-canvas-batch41-2026-08-26/) |
| 42 | director articulated character, SAM pose controls and independent pose tracks | [`liblib-canvas-batch42-2026-08-26/`](liblib-canvas-batch42-2026-08-26/) |
| 43 | director camera look-at modes, target following and path/phone conflict contract | [`liblib-canvas-batch43-2026-08-26/`](liblib-canvas-batch43-2026-08-26/) |
| 44 | director preset camera motion replace/append workflow and exact guards | [`liblib-canvas-batch44-2026-08-26/`](liblib-canvas-batch44-2026-08-26/) |
| 45 | director character groups, crowd arrays, group transforms and group timeline tracks | [`liblib-canvas-batch45-2026-08-26/`](liblib-canvas-batch45-2026-08-26/) |
| 46 | director camera screenshot gallery, preview viewer and bulk canvas return | [`liblib-canvas-batch46-2026-08-26/`](liblib-canvas-batch46-2026-08-26/) |
| 47 | director model-library entry, category browser and local proxy-object insertion | [`liblib-canvas-batch47-2026-08-26/`](liblib-canvas-batch47-2026-08-26/) |
| 48 | director `我的模型` local import, persistence, re-add and delete cleanup | [`liblib-canvas-batch48-2026-08-26/`](liblib-canvas-batch48-2026-08-26/) |
| 49 | director viewport native coordinate gizmo | [`liblib-canvas-batch49-2026-08-26/`](liblib-canvas-batch49-2026-08-26/) `SCRIPT_RECORDED_PASS`，clone-owned 有界合同 |
| 50 | director workspace collapse and keyboard boundary | [`liblib-canvas-batch50-2026-08-26/`](liblib-canvas-batch50-2026-08-26/) `SCRIPT_RECORDED_PASS`，clone-owned 有界合同 |
| 51 | ordinary canvas image toolbar zoom-aware top host geometry | [`liblib-canvas-batch51-2026-08-26/`](liblib-canvas-batch51-2026-08-26/) `SCRIPT_RECORDED_PASS`，几何 slice；action set 仍待独立 batch |
| 52 | current image-toolbar action set and page-level read-only preview | [`liblib-canvas-batch52-2026-08-26/`](liblib-canvas-batch52-2026-08-26/) `SCRIPT_RECORDED_PASS`，desktop/mobile 与相邻 Batch 10/11 回归已通过 |
| 53 | image annotate empty replacement state and source-shaped authoring controls | [`liblib-canvas-batch53-2026-08-26/`](liblib-canvas-batch53-2026-08-26/) `SCRIPT_RECORDED_PASS`，空态 toolbar/canvas replacement、DPR2、keyboard isolation 与 mobile clipping 已通过 |
| 54 | image element-edit empty replacement state and source-shaped authoring controls | [`liblib-canvas-batch54-2026-08-26/`](liblib-canvas-batch54-2026-08-26/) `SCRIPT_RECORDED_PASS`，空态 toolbar/stage/record replacement、keyboard isolation 与 mobile clipping 已通过 |
| 55 | source freshness reinspection attempt and blocked handoff | [`liblib-canvas-batch55-2026-08-26/`](liblib-canvas-batch55-2026-08-26/) `PARTIAL_RECORDED`，目标画布重定向首页且浏览器运行时版本路径异常；未产生新的 source behavior claim |
| 56 | bounded image rotate graph slice | [`liblib-canvas-batch56-2026-08-26/`](liblib-canvas-batch56-2026-08-26/) `SCRIPT_RECORDED_PASS`，media-gated 派生节点、source edge、selection、metadata、atomic undo/redo 和 mobile overflow 已通过；真实 bitmap/editor/save 仍不在合同内 |
| 57 | ordinary graph connection transaction | [`liblib-canvas-batch57-2026-08-27/`](liblib-canvas-batch57-2026-08-27/) `SCRIPT_RECORDED_PASS`，normalization、duplicate/reverse/parallel/self/cycle guards、accepted one-step history、rejected zero mutation 和 desktop/mobile focused verification 已通过；Reference/domain/source invalid feedback/import/sync 仍未覆盖 |
| 58 | node-bound image/Director owner invalidation on delete and canvas switch | [`liblib-canvas-batch58-2026-08-27/`](liblib-canvas-batch58-2026-08-27/) `SCRIPT_RECORDED_PASS`，preview/annotate/element-edit/Director owner 以 `canvasId + nodeId` 校验，删除/切换后 UI-only cleanup 已通过；relation-aware graph delete planner 仍未完成 |
| 59 | Director asset-library search, preview selection and explicit scene insertion | [`liblib-canvas-batch59-2026-08-27/`](liblib-canvas-batch59-2026-08-27/) `SCRIPT_RECORDED_PASS`，五分类资源搜索、preview-only selection、显式加入 proxy object、对象树/Inspector continuity、desktop/mobile 和普通 graph isolation 已通过；真实资产与认证后 LibTV exact surface 仍未知 |
| 60 | ordinary canvas image double-overlay owner continuity and pointer boundary | [`liblib-canvas-batch60-2026-08-26/`](liblib-canvas-batch60-2026-08-26/) `SCRIPT_RECORDED_PASS`，owner identity、selection migration、panel hit-testing boundary、active-tool replacement、graph/history isolation 和 desktop/mobile diagnostics 已通过；pointer routing 仍是 clone-owned decision |

Each batch directory normally contains `README.md`, `PLAN.md` and `IMPLEMENTATION.md`; additional `*.spec.md`, JSON and screenshot analysis files are the detailed contract.

## Stable Cross-Cutting Research

- [`BEHAVIORS.md`](BEHAVIORS.md)：whole-app interaction map.
- [`PAGE_TOPOLOGY.md`](PAGE_TOPOLOGY.md)：page layout and z-index map.
- [`DESIGN_TOKENS.md`](DESIGN_TOKENS.md)：visual tokens.
- [`COMPONENT_INVENTORY.md`](COMPONENT_INVENTORY.md)：current component catalog.
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：help text 与实际运行语义的三方漂移审计。
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)：graph-changing action 与原子 history 边界目录。
- [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)：graph 写入口的 authority、transport/command/restore/remote 分类与旁路风险。
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：异步 operation/run/result 身份、field ownership、陈旧结果 disposition、history/resource 和可恢复 projection 合同。
- [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：React Flow callbacks 的 exact variant allowlist、whole-batch planning、current-snapshot writeback、selection/history/document sanitation 合同。
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)：canvas registry、document、history、active session 和 external owner 的 create/switch/rename/duplicate/delete 隔离合同。
- [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)：command disposition、stable reason、primary feedback surface、announcement owner、clear/retry/dedupe 与 route/canvas isolation 合同。
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：UI overlay state、挂载 ownership、关闭路径和节点锚点策略目录。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：面向后续复刻的当前优先队列和 batch entry template。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：面向 verifier 和源站研究的 fixture catalog、隔离等级、副作用边界与 backlog 映射。
- [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)：面向源站复核的安全动作、版本化证据和 drift 判定模板。
- [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)：面向后续 batch 的 current-source verifier replacement queue 和 compatibility 规则。
- [`open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md`](open-canvas-2026-08-26/ADOPTION_DECISION_MATRIX.md)：Open Canvas 机制对 LibTV 的采纳、改造、研究、暂缓和拒绝矩阵，并对齐 parity、fixture 与 verifier。
- [`open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md`](open-canvas-2026-08-26/LIBTV_IMPLEMENTATION_HANDOFF_BLUEPRINT.md)：面向获批纵向 slice 的七层交接、依赖、fixture、验证和禁止扩边蓝图。
- [`open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md`](open-canvas-2026-08-26/LIBTV_PROCESS_RESULT_STATE_MATRIX.md)：LibTV 过程型能力的稳定身份、五轴状态、stale/retry、fixture 和 replacement verifier 设计。
- [`open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md`](open-canvas-2026-08-26/LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX.md)：模型 UI、参数、clone descriptor 和真实 runner 能力之间的可证实边界。
- [`open-canvas-2026-08-26/UPSTREAM_VERSION_IMPACT_PROTOCOL.md`](open-canvas-2026-08-26/UPSTREAM_VERSION_IMPACT_PROTOCOL.md)：固定 SHA 的 claim/pattern/adoption/runtime 影响审计和 submodule 更新闸门。
- [`open-canvas-2026-08-26/NEXT_EVIDENCE_ACQUISITION_PLAN.md`](open-canvas-2026-08-26/NEXT_EVIDENCE_ACQUISITION_PLAN.md)：Open Canvas 启发下剩余证据问题的执行波次、fixture gate 和安全停止条件。
- [`INSPECTION_GUIDE.md`](INSPECTION_GUIDE.md)：live-site extraction workflow and screenshot ledger rule.

## Evidence Assets

- Raw structured audits live beside the relevant research directory.
- Original and clone screenshots live in [`../design-references/`](../design-references/).
- Screenshot interpretation is recorded in the nearest batch `SCREENSHOT_ANALYSIS.md`.
- A screenshot filename containing `final` is not proof that it still matches the current source.
