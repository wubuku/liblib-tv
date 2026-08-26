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
- [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)：从 LibTV/Open Canvas 主张反查证据、适用范围和不可推出的结论。
- [`VERIFICATION_LEDGER.md`](VERIFICATION_LEDGER.md)：Batch verifier、源站合同、clone fixture、fixture 阻塞和并行 WIP 的验证成熟度台账。
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：源站快捷键文案、clone 帮助面板、实际监听器、React Flow gesture 和上下文优先级对照。
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)：用户动作、store action、nodes/edges/selection/history 副作用和证据边界目录。
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：top-level、route-local、节点相对和 Director surfaces 的 state、mount owner、关闭路径、键盘边界及兼容残留目录。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：当前全路由 UI/UX 差距、价值/证据/风险/验证准备度排序、依赖、工作波次和停止条件。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：本地 baseline、空画布 UI 构造、transaction-derived、Director 和源站只读/disposable fixture 的统一身份与 reset 合同。
- [`open-canvas-2026-08-26/`](open-canvas-2026-08-26/README.md)：ZeroLu/open-canvas 固定版本 submodule、官网运行态和深度源码调研。
- [`open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)：四类可迁移模式卡，区分上游启发、LibTV 证据和 clone 验证闸门。
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

Each batch directory normally contains `README.md`, `PLAN.md` and `IMPLEMENTATION.md`; additional `*.spec.md`, JSON and screenshot analysis files are the detailed contract.

## Stable Cross-Cutting Research

- [`BEHAVIORS.md`](BEHAVIORS.md)：whole-app interaction map.
- [`PAGE_TOPOLOGY.md`](PAGE_TOPOLOGY.md)：page layout and z-index map.
- [`DESIGN_TOKENS.md`](DESIGN_TOKENS.md)：visual tokens.
- [`COMPONENT_INVENTORY.md`](COMPONENT_INVENTORY.md)：current component catalog.
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：help text 与实际运行语义的三方漂移审计。
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)：graph-changing action 与原子 history 边界目录。
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：UI overlay state、挂载 ownership、关闭路径和节点锚点策略目录。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：面向后续复刻的当前优先队列和 batch entry template。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：面向 verifier 和源站研究的 fixture catalog、隔离等级、副作用边界与 backlog 映射。
- [`INSPECTION_GUIDE.md`](INSPECTION_GUIDE.md)：live-site extraction workflow and screenshot ledger rule.

## Evidence Assets

- Raw structured audits live beside the relevant research directory.
- Original and clone screenshots live in [`../design-references/`](../design-references/).
- Screenshot interpretation is recorded in the nearest batch `SCREENSHOT_ANALYSIS.md`.
- A screenshot filename containing `final` is not proof that it still matches the current source.
