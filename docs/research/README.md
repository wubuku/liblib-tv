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
- [`liblib-live-2026-09-05/`](liblib-live-2026-09-05/README.md)：登录态空画布项目 shell 审计：跟随状态条、添加资源分区、脚本 NEW/旧版双入口、Agent 选择模型/生成模式、生成历史模态、资产双 tab、工具箱预设与快捷键全量。
- [`liblib-canvas-batch97-2026-09-05/`](liblib-canvas-batch97-2026-09-05/README.md)：Agent 抽屉对齐 2026-09-05 源站的头部动作集合、源站 Skill 卡、composer 控件、选择模型目录菜单与生成模式菜单。
- [`liblib-canvas-batch98-2026-09-05/`](liblib-canvas-batch98-2026-09-05/README.md)：添加节点面板对齐 2026-09-05 源站：智能剪辑命名、脚本 NEW/旧版双入口、素材库风格/特效子菜单与搜索画布节点。
- [`liblib-canvas-batch99-2026-09-05/`](liblib-canvas-batch99-2026-09-05/README.md)：快捷键帮助面板对齐 2026-09-05 源站：四栏文案/键帽/suffix 全量对齐与 crosswalk 快照刷新，不改运行时 handler。
- [`liblib-canvas-batch100-2026-09-05/`](liblib-canvas-batch100-2026-09-05/README.md)：空画布状态与 4 个快捷生成芯片：源站命名/角标、诚实本地反馈与画布切换可达性。
- [`liblib-canvas-batch101-2026-09-05/`](liblib-canvas-batch101-2026-09-05/README.md)：生成历史模态对齐 2026-09-05 源站：标题、尺寸 slider、本画布 chip、计数 tab、评级本地菜单与空态文案。
- [`liblib-canvas-batch102-2026-09-05/`](liblib-canvas-batch102-2026-09-05/README.md)：资产管理抽屉对齐 2026-09-05 源站：评级/展示设置控件、空态文案、收起侧栏与搜索/筛选命名。
- [`liblib-canvas-batch103-2026-09-05/`](liblib-canvas-batch103-2026-09-05/README.md)：顶栏模式切换对齐 2026-09-05 源站：工作流/故事板 aria 命名、断言迁移与行为不变。
- [`liblib-canvas-batch104-2026-09-05/`](liblib-canvas-batch104-2026-09-05/README.md)：故事板三组对齐 2026-09-05 源站：文本/图片/视频列序、放大按钮、暂空文案与空画布侧栏隐藏。
- [`liblib-canvas-batch105-2026-09-05/`](liblib-canvas-batch105-2026-09-05/README.md)：协作跟随状态条：顶部 z-305 胶囊、淡出默认、uiStore 会话状态与单层 ESC 退出。
- [`liblib-canvas-batch106-2026-09-05/`](liblib-canvas-batch106-2026-09-05/README.md)：项目菜单（logo 下拉）对齐：四项源站命名与分组、本地 status 与教程 popover 锁定。
- [`liblib-canvas-batch107-2026-09-05/`](liblib-canvas-batch107-2026-09-05/README.md)：Skill 标题三文案轮换（换一批 驱动、与 editorMode 解耦）。
- [`liblib-canvas-batch108-2026-09-05/`](liblib-canvas-batch108-2026-09-05/README.md)：Batch 97-107 对齐系列跨批串行回归：81 项通过、12 项既有漂移经基线归因。
- [`liblib-canvas-batch110-2026-09-05/`](liblib-canvas-batch110-2026-09-05/README.md)：12 个既有漂移 verifier 的 AGED_GATE/HISTORICAL_CONTRACT 标注与 replacement map §4.z。
- [`liblib-canvas-batch111-2026-09-05/`](liblib-canvas-batch111-2026-09-05/README.md)：角色库模态几何与详情标签对齐 2026-09-05 补采样（1304x731、双角色标签、close aria）。
- [`liblib-canvas-batch112-2026-09-05/`](liblib-canvas-batch112-2026-09-05/README.md)：角色筛选面板对齐 2026-09-05 补采样：五组芯片、清空筛选与本地标签过滤。
- [`liblib-canvas-batch113-2026-09-05/`](liblib-canvas-batch113-2026-09-05/README.md)：角色卡片条均匀间距（移除位次特判）。
- [`liblib-canvas-sampling-2026-09-06/`](liblib-canvas-sampling-2026-09-06/README.md)：丢弃式测试项目采样：多画布 CRUD、双击生成流、脚本生成器节点、导演台入口。
- [`liblib-projects-page-2026-09-06/`](liblib-projects-page-2026-09-06/README.md)：「全部项目」列表页采样：路由 /project、页面分区与孤儿项目披露（研究记录，未实现）。
- [`liblib-canvas-batch114-2026-09-06/`](liblib-canvas-batch114-2026-09-06/README.md)：多画布下拉对齐 2026-09-06 采样：双按钮行、四项行级菜单、删除确认框、副本命名与 fallback。
- [`liblib-canvas-batch115-2026-09-06/`](liblib-canvas-batch115-2026-09-06/README.md)：双击画布打开添加节点面板。
- [`liblib-video-panel-2026-09-06/`](liblib-video-panel-2026-09-06/README.md)：视频生成面板改版采样（尝试行/工具行/2.0/设置芯片/135/新功能条）。
- [`liblib-canvas-batch125-2026-09-06/`](liblib-canvas-batch125-2026-09-06/README.md)：视频生成面板对齐：尝试行/新功能条/placeholder。
- [`liblib-canvas-batch148-2026-09-07/`](liblib-canvas-batch148-2026-09-07/README.md)：/project 项目卡封面占位图（渐变色+播放图标+节点计数）。
- [`liblib-canvas-batch169-2026-09-07/`](liblib-canvas-batch169-2026-09-07/README.md)：公共角色库模态页签 + Seedance 承诺书门本地模拟（未代用户同意，伦理边界留档）。
- [`liblib-canvas-batch168-2026-09-07/`](liblib-canvas-batch168-2026-09-07/README.md)：/project 左侧边栏落地（新建项目/导航行/促销+帮助）。
- [`liblib-canvas-batch167-2026-09-07/`](liblib-canvas-batch167-2026-09-07/README.md)：/project 次级表面对齐（实心次级按钮、创建卡封面结构、aspect-video 卡封面）。
- [`liblib-canvas-batch166-2026-09-07/`](liblib-canvas-batch166-2026-09-07/README.md)：提示词区去底色圆角 + 移除「3 个匹配」死弹窗芯片。
- [`liblib-canvas-batch165-2026-09-07/`](liblib-canvas-batch165-2026-09-07/README.md)：引用槽行布局对齐（flex-wrap/items-start/无固定高，去 Auto Link 汇总）。
- [`liblib-canvas-batch164-2026-09-07/`](liblib-canvas-batch164-2026-09-07/README.md)：页脚触发器采样类对齐（min-w-88/justify-between/13px、页脚 h-8 无分隔线）。
- [`liblib-canvas-batch163-2026-09-07/`](liblib-canvas-batch163-2026-09-07/README.md)：平板断点核查（768×1024 / 1024×768，无页面溢出，契约保持）。
- [`liblib-canvas-batch162-2026-09-07/`](liblib-canvas-batch162-2026-09-07/README.md)：移动端 390×844 断点核查（397px 增高后无溢出/裁切契约保持）。
- [`liblib-canvas-batch161-2026-09-07/`](liblib-canvas-batch161-2026-09-07/README.md)：视频面板增高 397px（修复 274px 溢出，提示词恢复 95px）。
- [`liblib-canvas-batch160-2026-09-07/`](liblib-canvas-batch160-2026-09-07/README.md)：芯片选长视频模式（14700）+ 引用槽空态条件渲染 + 去新功能条。
- [`liblib-canvas-batch159-2026-09-07/`](liblib-canvas-batch159-2026-09-07/README.md)：尝试列移入节点卡内（源站位置对齐，面板去重）。
- [`liblib-canvas-batch158-2026-09-07/`](liblib-canvas-batch158-2026-09-07/README.md)：默认模型回落 2.5 + 受控复测直证 batch128 联动 + 早期结论勘误（尝试列共存、新建节点有面板）。
- [`liblib-frameos-batch157-2026-09-07/`](liblib-frameos-batch157-2026-09-07/README.md)：FrameOS 右键菜单端到端验证 + BEHAVIORS.md 行为表勘误。
- [`liblib-canvas-batch156-2026-09-07/`](liblib-canvas-batch156-2026-09-07/README.md)：batch93 移动端抽屉关闭点击时序 flake 加固（左/右抽屉外点位）。
- [`liblib-canvas-batch155-2026-09-07/`](liblib-canvas-batch155-2026-09-07/README.md)：5分钟超长视频芯片时长范围修复（30..300 + 取消钳制）。
- [`liblib-canvas-batch154-2026-09-07/`](liblib-canvas-batch154-2026-09-07/README.md)：全量回归扫描（124 验证器：112 通过/12 老化/0 未解释；batch124 弹窗迁移；timeout/Rosetta 勘误）。
- [`liblib-canvas-batch153-2026-09-07/`](liblib-canvas-batch153-2026-09-07/README.md)：采样第三轮 —— Auto 因子证实（230=5×46）、新建节点无面板、积分块类名逐字吻合。
- [`liblib-canvas-batch152-2026-09-07/`](liblib-canvas-batch152-2026-09-07/README.md)：/project 卡副行仅日期 + 覆盖矩阵刷新（积分第四数据点、菜单 rAF 门控、分组内嵌面板）。
- [`liblib-canvas-batch151-2026-09-07/`](liblib-canvas-batch151-2026-09-07/README.md)：采样第二轮 + 工具行/积分块微对齐（面板绑定选中态确认、尝试一次性门控、菜单 rAF 门控）。
- [`liblib-canvas-batch150-2026-09-07/`](liblib-canvas-batch150-2026-09-07/README.md)：/project 画布卡新开标签 + 添加面板容器视觉（rounded-2xl/backdrop-blur）。
- [`liblib-canvas-batch149-2026-09-07/`](liblib-canvas-batch149-2026-09-07/README.md)：高级设置纵向列 + 默认模型 2.0（源站 2026-09-07 复采：分组内嵌生成面板、尝试列、积分 135、跟随横幅核对、会话降级根因勘误）。
- [`liblib-canvas-batch136-2026-09-06/`](liblib-canvas-batch136-2026-09-06/README.md)：回收站勾选与批量恢复：计数、逐项勾选与批量恢复按钮。
- [`liblib-surface-coverage-2026-09-07/`](liblib-surface-coverage-2026-09-07/README.md)：全表面覆盖矩阵：已对齐/待补采/阻塞 三态路线图（截至 2026-09-07）。
- [`liblib-canvas-batch135-2026-09-07/`](liblib-canvas-batch135-2026-09-07/README.md)：视频面板积分比例因子落地（16:9→27/s、Auto→46/s，采样校准）。
- [`liblib-canvas-batch139-2026-09-07/`](liblib-canvas-batch139-2026-09-07/README.md)：顶栏 积分超市/积分余额 拆分（源站顺序对齐）。
- [`liblib-canvas-batch141-2026-09-07/`](liblib-canvas-batch141-2026-09-07/README.md)：视频模型菜单全量目录落地（35 项采样校准）。
- [`liblib-frameos-batch133-2026-09-06/`](liblib-frameos-batch133-2026-09-06/README.md)：FrameOS 复制节点落地：Cmd+D 插入副本节点与 undo/redo。
- [`liblib-frameos-batch134-2026-09-06/`](liblib-frameos-batch134-2026-09-06/README.md)：FrameOS 复制/粘贴剪贴板闭环：Cmd+V 粘贴副本与 undo。
- [`liblib-canvas-batch116-2026-09-06/`](liblib-canvas-batch116-2026-09-06/README.md)：脚本生成器节点（脚本 NEW）：三尝试/参考图/GVLM 3.1 与本地提示词。
- [`liblib-canvas-batch117-2026-09-06/`](liblib-canvas-batch117-2026-09-06/README.md)：导演台节点卡文案对齐 2026-09-06 采样（导演台/描述/打开导演台）。
- [`liblib-canvas-batch124-2026-09-06/`](liblib-canvas-batch124-2026-09-06/README.md)：画布回收站（软删除+恢复）：/project 回收站面板与内容完整恢复。
- [`liblib-canvas-batch119-2026-09-06/`](liblib-canvas-batch119-2026-09-06/README.md)：/project 列表页落地：结构对齐、创建卡、画布卡导航与 logo 菜单 全部项目 路由。
- [`liblib-canvas-batch122-2026-09-06/`](liblib-canvas-batch122-2026-09-06/README.md)：工具箱预设完整性验证：源站 23 项全量采样与 clone 零缺失比对。
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
- [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：Open Canvas execute/run/poll/patch 的正反面证据、clone graph-producing timer/Director completion 审计，以及 operation/result envelope、stale/duplicate 收敛、Director Batch 73 async authority 和 ordinary `ASYNC-INGRESS-01` / `LIBTV-VR-015` 设计。
- [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)：两个项目共同锁定的 React Flow 12.11.1 change/reducer 语义、clone callback 旁路，以及 T0 selection、T1 node transport、T2/T3 semantic routing、`REACT-FLOW-CHANGES-01` 和 `LIBTV-VR-016`。
- [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)：Open Canvas summary/full record、URL/hydrate/delete/save owner 与 clone 多画布 registry/document/history/session/resource 边界，定义 switch manifest、`CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017`。
- [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)：Open Canvas command/toast/node/save/form feedback 与 clone local status/timer/Director 审计，定义 disposition/reason/copy、primary surface、owner、clear/retry/dedupe、`COMMAND-FEEDBACK-01` 和 `LIBTV-VR-018`。
- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)：Open Canvas selected flags/editable guard/Radix delegation 与 clone node/edge selection、capture/bubble listener、focus owner、Batch 50 事实漂移的 fixed static audit。
- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：node/edge/primary active-session selection、focus zones、foreground surface policy、dispatch result、one-Escape、focus return、`SELECTION-FOCUS-CONTEXT-01` 和 `LIBTV-VR-019`。
- [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)：Open Canvas dual screen/flow anchor、live/stable viewport、placement/counterexamples 与 clone coordinate domain、host center、gesture/lifecycle gap 的 fixed audit。
- [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：普通 LibTV actual host、六类坐标域、live/stable/bootstrap/target viewport、gesture/placement owner、resize reconciliation、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 和 `LIBTV-VR-020` 的正式设计权威。
- [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)：Open Canvas file-input/drop/probe/upload/dedupe/save 正反面、当前 clone mock/local-preview/blob-data 路径，以及 LibTV 源站上传/生成历史/素材库/资产管理分域的固定审计。
- [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)：普通 LibTV 十类 entry profile、validation/probe/materialization state machine、preview/result lease、asset/node reference、multi-item cohort、reachability/release、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` 和 `LIBTV-VR-021` 正式设计权威。
- [`open-canvas-2026-08-26/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md)：本专题从计划、里程碑 commit 到治理同步的历史执行记录；稳定指导仍以 audit + contract 为准。
- [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)：Open Canvas session/bitmap snapshot/text draft/save-upload 正反面与 clone 十四类 draft/history/commit surface、inert controls、graph gateway 和 spec drift 的固定审计。
- [`open-canvas-2026-08-26/editor-session-static-evidence-2026-08-27.json`](open-canvas-2026-08-26/editor-session-static-evidence-2026-08-27.json)：`OC-071..080` 与 `LIBTV-EDS-001..014` 的固定代码路径、事实、迁移含义和证据边界原始清单。
- [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)：十类 editor profile、session/baseline/draft model、native/local/graph undo、commit/async/resource handoff、40 invariants、`LIBTV-FIX-LOCAL-EDITOR-SESSION-01` 和 `LIBTV-VR-022` 正式设计权威。
- [`open-canvas-2026-08-26/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_RESEARCH_PLAN_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_RESEARCH_PLAN_2026-08-27.md)：本专题从计划、审计、正式合同到治理同步的历史执行记录；稳定指导仍以 dated audit + contract 为准。
- [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)：Open Canvas media/output/request-aspect/frame/rendition 正反面、当前 clone dimension collision 与当日 LibTV source media-shaped image node 的 fixed audit。
- [`open-canvas-2026-08-26/media-rendition-geometry-static-evidence-2026-08-27.json`](open-canvas-2026-08-26/media-rendition-geometry-static-evidence-2026-08-27.json)：`OC-081..090`、`LIBTV-MRG-001..014` 与六条 source read-only measurement 的固定路径、尺寸、事实和证据边界原始清单。
- [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)：media/output/request/frame/measured/rendition 十类权威、cover/contain transform、mixed-ratio output、measurement freshness、42 invariants、fixture 和 `LIBTV-VR-023` 正式设计权威。
- [`open-canvas-2026-08-26/LIBTV_MEDIA_RENDITION_GEOMETRY_RESEARCH_PLAN_2026-08-27.md`](open-canvas-2026-08-26/LIBTV_MEDIA_RENDITION_GEOMETRY_RESEARCH_PLAN_2026-08-27.md)：本专题从计划、静态审计、正式合同到项目治理同步的历史执行记录；稳定指导仍以 dated audit + contract 为准。
- [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)：top-level、route-local、节点相对和 Director surfaces 的 state、mount owner、关闭路径、键盘边界及兼容残留目录。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：当前全路由 UI/UX 差距、价值/证据/风险/验证准备度排序、依赖、工作波次和停止条件。
- [`LIBTV_FIXTURE_CATALOG.md`](LIBTV_FIXTURE_CATALOG.md)：本地 baseline、空画布 UI 构造、transaction-derived、Director 和源站只读/disposable fixture 的统一身份与 reset 合同。
- [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)：`PAR-005` 源站 page shell、baseline、overlay、lifecycle 和 responsive 的只读复核 runbook。
- [`LIBTV_VERIFIER_REPLACEMENT_MAP.md`](LIBTV_VERIFIER_REPLACEMENT_MAP.md)：历史 clone 断言的保留/降级/替换矩阵、fixture 前提和授权后的迁移顺序。
- [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：Director Batch 35-50/59 的 17 个 browser 脚本分级、Batch 67-96 current gates、artifact/storage 成本和 `LIBTV-VR-024` 可靠性入口。
- [`liblib-canvas-batch87-2026-08-29/`](liblib-canvas-batch87-2026-08-29/README.md)：Director undo/redo selection authority、失效选择 repair 和 portable-document 边界。
- [`storyai-3d-director-desk-2026-08-27/`](storyai-3d-director-desk-2026-08-27/README.md)：StoryAI 固定上游与当前 Director Desk 的跨批次进展审计、借鉴决策矩阵、证据账本和后续路线图。
- [`open-canvas-2026-08-26/`](open-canvas-2026-08-26/README.md)：ZeroLu/open-canvas 固定版本 submodule、官网运行态和深度源码调研。
- [`open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md`](open-canvas-2026-08-26/OPEN_CANVAS_PATTERN_CARDS.md)：十三类可迁移模式卡，覆盖浮层几何、typed input、状态分层、subgraph identity、stale-safe result ingress、framework change routing、多画布 lifecycle、command feedback、selection/focus/context、spatial、media/resource、editor session 和 media rendition authority，并区分上游启发、LibTV 证据和 clone 验证闸门。
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
| 61 | React Flow change routing and runtime selection authority | [`liblib-canvas-batch61-2026-08-27/`](liblib-canvas-batch61-2026-08-27/) `IMPLEMENTED_FOCUSED_PASS`，whole-batch T0/T1 classifier、current-snapshot commit、edge session selection、semantic zero-partial reject 和 `LIBTV-VR-016` focused verifier 已通过；混合 primary/focus 仍待后续 |
| 62 | command selection snapshot and one-Escape context | [`liblib-canvas-batch62-2026-08-27/`](liblib-canvas-batch62-2026-08-27/) `IMPLEMENTED_FOCUSED_PASS`，validated command snapshot、editable/IME guard、blocking foreground shortcut suspension、single-layer Escape 与 canvas focus fallback 已通过 focused verifier；universal mixed primary、focus trap、Asset/Agent containment 和 source-exact modal policy 保持后续 |
| 63 | actual React Flow host center placement for default node creation | [`liblib-canvas-batch63-2026-08-27/`](liblib-canvas-batch63-2026-08-27/) `IMPLEMENTED_FOCUSED_PASS`，Add Node 与 Character Library 已由 page 测量 actual host 并经 React Flow 转换，drawer closed/open、desktop/mobile、history/selection 和 zero-mutation guard 已通过；derived/duplicate/organize、live/stable viewport 和 source-exact add policy 保持后续 |
| 64 | Asset drawer host-resize anchor preservation | [`liblib-canvas-batch64-2026-08-27/`](liblib-canvas-batch64-2026-08-27/) `SCRIPT_RECORDED_PASS`，toolbar/X/Canvas-context 已统一进入 page-owned layout transaction；desktop/mobile host-center anchor、current owner guard、zero graph/history/selection mutation和 Batch 63 composition 已通过；source exact policy、通用 resize observer、browser bootstrap 与 live/stable split 保持后续 |
| 65 | responsive viewport bootstrap ownership | [`liblib-canvas-batch65-2026-08-27/`](liblib-canvas-batch65-2026-08-27/) `IMPLEMENTED_FOCUSED_PASS`，desktop/mobile bootstrap、未交互 breakpoint reprojection、用户 stable viewport preservation、A/B canvas restore、projection echo、stale/invalid callback 和 Batch 6/7/16/18/19/61-64 回归已通过；full live/stable endpoint、browser resize anchor、generic generation/host epoch 和 source exact responsive policy 保持后续 |
| 66 | Director project/session、command/history/delete 与 current verifier authority | [`liblib-canvas-batch66-2026-08-27/`](liblib-canvas-batch66-2026-08-27/) `RESEARCH_AND_GOVERNANCE_COMPLETE`，完成静态审计、两份正式合同、17-script manifest、Batch 59 current smoke 和治理索引；本批不修改业务 runtime |
| 67 | Director Project Document V1 strict codec | [`liblib-canvas-batch67-2026-08-27/`](liblib-canvas-batch67-2026-08-27/) `CODEC_IMPLEMENTED`，完成封闭 V1 DTO、snapshot adapter、strict unknown/future/identity/reference validation、runtime/media-byte exclusion 与 17-case pure verifier；owner registry、store authority、history/delete/persistence 保持后续 |
| 68 | Director owner registry 与 session lifecycle | [`liblib-canvas-batch68-2026-08-27/`](liblib-canvas-batch68-2026-08-27/) `OWNER_SESSION_FOCUSED_PASS`，完成 structured owner、per-owner project、fresh session/generation、A/B/cross-canvas/duplicate/delete-close、memory capture sidecar 和 graph isolation verifier；authored/runtime、async、history/delete/persistence 保持后续 |
| 69 | Director authored/runtime projection split | [`liblib-canvas-batch69-2026-08-27/`](liblib-canvas-batch69-2026-08-27/) `AUTHORED_RUNTIME_FOCUSED_PASS`，完成 `authoredObjects` portable baseline、`objects` runtime projection、seek/playback/path stability、object/camera/pose authoring restore、close/reopen、A/B owner 与 graph isolation；async、history/delete/persistence 和 source parity 保持后续 |
| 70 | Director command/history/gesture kernel | [`liblib-canvas-batch70-2026-08-27/`](liblib-canvas-batch70-2026-08-27/) `DIRECTOR_HISTORY_FOCUSED_PASS`，完成 typed command result、project-local history、no-op/rejection reason、gesture coalescing、undo/redo、future truncation、close/reopen continuity 与 ordinary graph/history isolation；reference-aware delete、async freshness、persistence 和 source parity 保持后续 |
| 71 | Director pointer lifecycle and gesture cleanup | [`liblib-canvas-batch71-2026-08-27/`](liblib-canvas-batch71-2026-08-27/) `POINTER_LIFECYCLE_FOCUSED_PASS`，完成 Inspector numeric、pose、camera、path anchor/Bezier、path transform、pencil/pen 的 commit/cancel/pointercancel 与 history/graph isolation；async、reference delete、persistence 和 source parity 保持后续 |
| 72 | Director reference-aware delete and resource closure | [`liblib-canvas-batch72-2026-08-27/`](liblib-canvas-batch72-2026-08-27/) `REFERENCE_DELETE_FOCUSED_PASS`，完成 object/group/camera/track/path/capture/resource closure、last-camera/resource policy、selection/runtime repair、exact delete/undo/redo 与 ordinary graph isolation；inactive-owner、async、persistence、copy/paste 和 source parity 保持后续 |
| 73 | Director async result authority | [`liblib-canvas-batch73-2026-08-27/`](liblib-canvas-batch73-2026-08-27/) `ASYNC_AUTHORITY_FOCUSED_PASS`，完成 capture/export/phone operation identity、owner/source freshness、retry/duplicate/terminal convergence、graph projection 与 resource transfer/release exactly once；ordinary canvas async、durable persistence、copy/paste 和 source parity 保持后续 |
| 74 | Director durable project persistence | [`liblib-canvas-batch74-2026-08-27/`](liblib-canvas-batch74-2026-08-27/) `PERSISTENCE_FOCUSED_PASS`，完成 browser-local versioned envelope、strict restore、owner/project/generation/fingerprint guard、stale save、corrupt payload preservation、runtime/UI/resource-byte exclusion 与 storage failure continuity；ordinary canvas persistence、remote storage、真实资源和 source parity 保持后续，copy/paste 已由 Batch 75 接续 |
| 75 | Director clipboard identity remap | [`liblib-canvas-batch75-2026-08-27/`](liblib-canvas-batch75-2026-08-27/) `CLIPBOARD_REMAP_FOCUSED_PASS`，完成 project-scoped typed packet、group/object/track/path closure、two-pass identity/reference remap、camera detach/freeze、stable resource alias、deterministic offset、one-history、keyboard guard、A-B-A/reload boundary 与 focused verifier；whole-project duplicate、cross-project/system clipboard、真实资源和 source parity 保持后续 |
| 76 | Director owner reachability reconciliation | [`liblib-canvas-batch76-2026-08-27/`](liblib-canvas-batch76-2026-08-27/) `OWNER_REACHABILITY_FOCUSED_PASS`，完成 all-canvas live owner、inactive source/canvas one-time tombstone、active shell/session/runtime 两阶段 cleanup、幂等、stale async、graph undo boundary 与 retained persistence；Batch 59、67-76 跨批回归已通过 |
| 77 | source-aligned canvas navigation and Director TransformControls binding regression | [`liblib-canvas-batch77-2026-08-28/`](liblib-canvas-batch77-2026-08-28/) `SCRIPT_RECORDED_PASS`，普通 wheel/middle/Space/H/V/blank no-op/modifier zoom 与 mobile overflow 已对齐源站运行态；Director object/group/path explicit attachment、真实 gizmo pointer drag、authored/runtime sync、undo/redo 和 zero-distance cleanup 已通过；不证明源站 Director exact DOM/CSS、真实触摸板硬件或内部实现技术 |
| 78 | Director pointer cancellation, cleanup and R3F teardown | [`liblib-canvas-batch78-2026-08-28/`](liblib-canvas-batch78-2026-08-28/) `POINTER_CANCELLATION_AND_R3F_TEARDOWN_RECORDED_PASS`，Curve/Phone Vcam/Timeline 的 pointercancel、blur、visibility、unmount、stale-pointer 防护以及跨 owner/canvas 的 R3F Canvas 异步 teardown 已通过；Batch 59、67-78 当前闸门串行回归、`npm run check` 和 `docs:check` 通过；不改变 phone runtime-only 语义，也不证明源站 Director exact DOM/CSS |
| 79 | Director whole-project duplicate | [`liblib-canvas-batch79-2026-08-28/`](liblib-canvas-batch79-2026-08-28/) `WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS`，graph/Director two-pass identity/reference remap、multi-owner project copy、fresh document policy、non-portable resource reject、clean target authority、persistence isolation 和 pure/browser verifier 已通过；不证明 LibTV source duplicate 语义或真实资源复制 |
| 80 | Director durable tombstone、storage/resource cleanup boundary | [`liblib-canvas-batch80-2026-08-28/`](liblib-canvas-batch80-2026-08-28/) `DURABLE_TOMBSTONE_FOCUSED_PASS`，strict tombstone envelope、save resurrection guard、active/inactive cleanup、capture sidecar 清理、共享/未引用 local resource policy、reload reopen reject 和 pure/browser verifier 已通过；不证明 LibTV source 删除/恢复语义或 remote persistence |
| 81 | Director strict project import/export and recoverable UI workflow | [`liblib-canvas-batch81-2026-08-29/`](liblib-canvas-batch81-2026-08-29/) `DIRECTOR_IMPORT_EXPORT_FOCUSED_PASS`，strict V1 document export/import、owner/project rebind、capture/runtime/UI exclusion、one-entry history、undo/redo、same-document no-op、invalid zero-partial、download/file-input round trip 和 ordinary graph isolation 已通过；不证明 LibTV source 文件格式或 remote sync |
| 82 | Director local resource lifecycle and finite OBJ/FBX materialization | [`liblib-canvas-batch82-2026-08-29/`](liblib-canvas-batch82-2026-08-29/) `LOCAL_RESOURCE_MATERIALIZATION_FOCUSED_PASS`，typed descriptor/provenance、attempt freshness、retry/cancel/release、valid OBJ materialization、parse-failure proxy retention、unsupported-extension zero mutation、model-library feedback 和 zero diagnostics 已通过；不证明生产 loader/cache、复杂 FBX/纹理、remote persistence 或 LibTV source resource semantics |
| 83 | Director command outcome feedback projection | [`liblib-canvas-batch83-2026-08-29/`](liblib-canvas-batch83-2026-08-29/) `COMMAND_FEEDBACK_FOCUSED_PASS`，typed disposition/reason 到固定 header status surface、ARIA、committed-success suppression、meaningful no-op、mobile geometry 和 zero-history feedback boundary 已通过；不证明 LibTV source feedback taxonomy 或 ordinary canvas unified feedback |
| 84 | Director object-tree lock/visibility and locked-target edit protection | [`liblib-canvas-batch84-2026-08-29/`](liblib-canvas-batch84-2026-08-29/) `LOCK_EDITABILITY_FOCUSED_PASS`，lock/unlock、Inspector disabled controls、direct rejection、zero mutation/history、visibility continuity、unlock recovery 和 mobile discovery 已通过；不证明 LibTV source Director lock UI 或 source parity |
| 85 | Director object-tree selection context and CRUD discoverability | [`liblib-canvas-batch85-2026-08-29/`](liblib-canvas-batch85-2026-08-29/) `SELECTION_CRUD_FOCUSED_PASS`，selection action bar、single/multi-selection count、project-scoped copy、clear zero-history、reference-aware batch delete、group context、mobile discovery 和 zero diagnostics 已通过；不证明 LibTV source Director selection bar 或 source parity |
| 86 | Director transform target context and pointer cancellation | [`liblib-canvas-batch86-2026-08-29/`](liblib-canvas-batch86-2026-08-29/) `TRANSFORM_CONTEXT_FOCUSED_PASS`，目标上下文、真实 gizmo drag、authoring/runtime/history、pointercancel/lost capture、locked zero mutation、Inspector position continuity、mobile geometry 和 zero diagnostics 已通过；不证明 LibTV source Director gizmo/target context 或 source parity |
| 87 | Director undo/redo restore selection authority | [`liblib-canvas-batch87-2026-08-29/`](liblib-canvas-batch87-2026-08-29/) `RESTORE_SELECTION_FOCUSED_PASS`，undo/redo/cancel preserve-and-repair、对象树/Inspector/Viewport/Timeline 一致性、失效选择清理、portable document selection exclusion 和 zero diagnostics 已通过；不证明 LibTV source Director undo selection policy 或 source parity |
| 88 | Director selection/timeline/TransformControls authority | [`liblib-canvas-batch88-2026-08-29/`](liblib-canvas-batch88-2026-08-29/) `SELECTION_TIMELINE_AUTHORITY_FOCUSED_PASS`，单/多/分组选择 normalization、Timeline 反向选择、keyframe/path ownership、delete repair、locked zero mutation、portable boundary、mobile geometry 和 zero diagnostics 已通过；不证明 LibTV source Director selection/Timeline 联动或 source parity |
| 89 | Director scene settings and add-camera discoverability | [`liblib-canvas-batch89-2026-08-29/`](liblib-canvas-batch89-2026-08-29/) `SCENE_ADD_CAMERA_FOCUSED_PASS`，场景名称、ground/grid 显隐、背景/地面颜色、对象树/Inspector 双入口、新 camera object/track/keyframe、active-camera/selection、undo/redo、portable export、mobile geometry 和 zero diagnostics 已通过；不证明 LibTV source Director add-camera defaults、shot lifecycle 或 source parity |
| 90 | Director project/session diagnostics and scene semantic command | [`liblib-canvas-batch90-2026-08-29/`](liblib-canvas-batch90-2026-08-29/) `FOCUSED_RUNTIME_RECORDED_PASS`，session outcome/lifecycle diagnostics、scene draft + Enter/blur commit、typed scene command、persistence、one-entry history、no-op/reject、undo/redo、mobile Inspector 和 zero diagnostics 已通过；不证明 LibTV source Director project/session/history semantics |
| 91 | Director object/camera/group command and history boundary | [`liblib-canvas-batch91-2026-08-29/`](liblib-canvas-batch91-2026-08-29/) `FOCUSED_RUNTIME_RECORDED_PASS`，对象属性、相机设置、角色组创建/重命名/变换、draft/commit、no-op/invalid/reference guard、persistence、one-entry history 和 zero diagnostics 已通过；不证明 LibTV source Director command/history semantics |
| 92 | Director local resource lifecycle and session lease | [`liblib-canvas-batch92-2026-08-29/`](liblib-canvas-batch92-2026-08-29/) `FOCUSED_RUNTIME_RECORDED_PASS`，strict descriptor/decoded-byte budget、owner-scoped request/lease、deferred/final release、有限 OBJ/FBX materialization、失败 proxy、retry/cancel 和 zero diagnostics 已通过；不证明 LibTV source resource protocol、生产 loader/cache 或 remote persistence |
| 94 | Director workspace/drawer focus containment, focus return, ARIA/inert and editable keyboard boundary | [`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/) `FOCUSED_RUNTIME_RECORDED_PASS`，desktop/mobile workspace 与 tree/Inspector drawer 的 Tab/Shift+Tab containment、focus return、editable boundary、ARIA/inert、overflow 和 zero diagnostics 已通过；不证明 LibTV source Director exact focus trap 或键盘实现 |
| 93 | Director final desktop/mobile regression and governance closeout | [`liblib-canvas-batch93-2026-08-29/`](liblib-canvas-batch93-2026-08-29/) `FINAL_REGRESSION_RECORDED_PASS`，桌面/移动端 Director shell、R3F、对象树、Inspector、Timeline、抽屉/折叠、close/reopen、普通画布跨批回归、Batch 59/67-92 current gates 和全量文档/项目检查已通过；不证明 LibTV source parity |
| 94 | Director focus containment and keyboard boundary | [`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/) `FOCUSED_RUNTIME_RECORDED_PASS`，workspace 正/反向 Tab 循环、打开/关闭回焦、移动 tree/Inspector 局部循环、非活动抽屉 `aria-hidden`/`inert`、Escape/editable boundary 和 desktop/mobile zero diagnostics 已通过；不证明 LibTV source-exact focus implementation |
| 95 | Director canvas image ingress and session-only environment preview | [`liblib-canvas-batch95-2026-08-29/`](liblib-canvas-batch95-2026-08-29/) `SCRIPT_RECORDED_PASS`，当前 Director 节点直接上游图片的 typed ingress、Inspector 选择/切换/清除、R3F 非交互环境预览、stale source 清理、导出排除和 desktop/mobile/failure `0/0/0` diagnostics 已通过；不证明 LibTV source-exact panorama UI、Three.js/R3F 实现或 ordinary media provider |
| 96 | Director multi-camera and Shot workflow | [`liblib-canvas-batch96-2026-08-29/`](liblib-canvas-batch96-2026-08-29/) `SCRIPT_RECORDED_PASS`，portable Shot record、旧 V1 兼容 decode、Shot create/switch/update、capture provenance/gallery、camera/Shot delete repair、clipboard/whole-project duplicate remap、reload/import/export、desktop/mobile 和 `0/0/0` diagnostics 已通过；不证明 LibTV source Shot schema 或 source parity，本批完成后停止 |
| 97 | Agent drawer current-source alignment | [`liblib-canvas-batch97-2026-09-05/`](liblib-canvas-batch97-2026-09-05/) `SCRIPT_RECORDED_PASS`，头部动作/disabled、源站 Skill 卡、composer 添加附件/选择模型/Skill/生成模式、模型目录 15 项与 premium 角标、生成模式默认/切换、Escape 分层与 `0/0/0` diagnostics 已通过；不证明 LibTV source-exact Drawer DOM/CSS 或真实服务接入 |
| 98 | Add-node panel current-source alignment | [`liblib-canvas-batch98-2026-09-05/`](liblib-canvas-batch98-2026-09-05/) `SCRIPT_RECORDED_PASS`，智能剪辑命名、脚本 NEW/（旧版）Beta flyout、素材库风格库/特效库、搜索画布节点过滤、上传/生成历史本地 status 与 `0/0/0` diagnostics 已通过；不证明新脚本节点能力或真实 media ingress |
| 99 | Shortcuts help panel copy alignment | [`liblib-canvas-batch99-2026-09-05/`](liblib-canvas-batch99-2026-09-05/) `SCRIPT_RECORDED_PASS`，四栏条目/键帽/suffix、删除行位置、画布节点搜索行与 Windows 重做移除已通过，crosswalk 快照列已刷新；不证明新快捷键运行时 handler |
| 100 | Empty-canvas state and quick-create chips | [`liblib-canvas-batch100-2026-09-05/`](liblib-canvas-batch100-2026-09-05/) `SCRIPT_RECORDED_PASS`，空态提示、4 芯片与角标、本地 status、画布切换隔离与 mobile 溢出已通过；不证明芯片真实生成流或双击生成 UI |
| 101 | Generation-history panel alignment | [`liblib-canvas-batch101-2026-09-05/`](liblib-canvas-batch101-2026-09-05/) `SCRIPT_RECORDED_PASS`，标题/滑杆/本画布 chip/计数 tab/评级本地菜单/空态文案与入口更名已通过；不证明真实历史数据或评级后端 |
| 102 | Asset manager drawer alignment | [`liblib-canvas-batch102-2026-09-05/`](liblib-canvas-batch102-2026-09-05/) `SCRIPT_RECORDED_PASS`，评级/展示设置控件、空态文案、收起侧栏与 aria 命名已通过；不证明评级/展示设置真实语义 |
| 103 | Top-bar mode toggle alignment | [`liblib-canvas-batch103-2026-09-05/`](liblib-canvas-batch103-2026-09-05/) `SCRIPT_RECORDED_PASS`，工作流/故事板命名、pressed 双态与断言迁移已通过；不证明源站图标形状或几何 |
| 104 | Storyboard three-section alignment | [`liblib-canvas-batch104-2026-09-05/`](liblib-canvas-batch104-2026-09-05/) `SCRIPT_RECORDED_PASS`，三列顺序、放大按钮、暂空文案与空画布侧栏隐藏已通过；不证明放大行为或非空画布源站布局 |
| 105 | Collaborative follow banner | [`liblib-canvas-batch105-2026-09-05/`](liblib-canvas-batch105-2026-09-05/) `SCRIPT_RECORDED_PASS`，横幅结构、淡出默认、取消与单层 ESC 优先已通过；不证明真实协作或跟随触发 |
| 106 | Project menu alignment | [`liblib-canvas-batch106-2026-09-05/`](liblib-canvas-batch106-2026-09-05/) `SCRIPT_RECORDED_PASS`，四项命名/分组、本地 status 与教程锁定已通过；不证明真实项目操作 |
| 107 | Skill headline rotation | [`liblib-canvas-batch107-2026-09-05/`](liblib-canvas-batch107-2026-09-05/) `SCRIPT_RECORDED_PASS`，三条源站标题轮换与回绕已通过；不证明源站轮换驱动 |
| 108 | 97-107 series cross-batch regression | [`liblib-canvas-batch108-2026-09-05/`](liblib-canvas-batch108-2026-09-05/) `REGRESSION_RECORDED_PASS`，81 项通过、12 项既有漂移经基线 86673b6 归因；无本系列回归 |
| 110 | Aged-gate deprecation | [`liblib-canvas-batch110-2026-09-05/`](liblib-canvas-batch110-2026-09-05/) `DOCS_RECORDED`，12 个既有漂移 verifier 标注 HISTORICAL_CONTRACT 并登记 replacement map §4.z；无运行时变更 |
| 111 | Character library modal alignment | [`liblib-canvas-batch111-2026-09-05/`](liblib-canvas-batch111-2026-09-05/) `SCRIPT_RECORDED_PASS`，模态几何、四图列比、双角色标签与 close aria 已通过；不证明其余角色标签或多视口几何 |
| 112 | Character filter panel alignment | [`liblib-canvas-batch112-2026-09-05/`](liblib-canvas-batch112-2026-09-05/) `SCRIPT_RECORDED_PASS`，五组芯片、清空筛选与本地过滤已通过；文化区域选项不证明 |
| 113 | Uniform character strip spacing | [`liblib-canvas-batch113-2026-09-05/`](liblib-canvas-batch113-2026-09-05/) `SCRIPT_RECORDED_PASS`，卡片条均匀节奏已通过；源站精确像素为截图粗读 |
| 114 | Multi-canvas dropdown alignment | [`liblib-canvas-batch114-2026-09-06/`](liblib-canvas-batch114-2026-09-06/) `SCRIPT_RECORDED_PASS`，行结构/行级菜单/确认框/副本命名与 fallback 已通过；在新窗口打开行为不证明 |
| 115 | Canvas double-click add panel | [`liblib-canvas-batch115-2026-09-06/`](liblib-canvas-batch115-2026-09-06/) `SCRIPT_RECORDED_PASS`，双击开面板/零创建/Escape/重触发已通过 |
| 141 | Video model menu full catalog | [`liblib-canvas-batch141-2026-09-07/`](liblib-canvas-batch141-2026-09-07/) `SCRIPT_RECORDED_PASS`，35 项采样目录落地与矩阵迁移已通过；premium 完整分布不证明 |
| 125 | Video panel attempts alignment | [`liblib-canvas-batch125-2026-09-06/`](liblib-canvas-batch125-2026-09-06/) `SCRIPT_RECORDED_PASS`，尝试行三芯片/新功能条/placeholder 对齐已通过；尝试子界面/模型菜单/积分 135 待补采样 |
| 136 | Recycle bin selection | [`liblib-canvas-batch136-2026-09-06/`](liblib-canvas-batch136-2026-09-06/) `SCRIPT_RECORDED_PASS`，勾选/计数/批量恢复已通过；源站勾选交互不证明 |
| 135 | Credits ratio factor | [`liblib-canvas-batch135-2026-09-07/`](liblib-canvas-batch135-2026-09-07/) `SCRIPT_RECORDED_PASS`，16:9→135/Auto→230 数据点校准的比例因子已落地；其余比例/模型定价不证明 |
| 139 | Topbar credits split | [`liblib-canvas-batch139-2026-09-07/`](liblib-canvas-batch139-2026-09-07/) `SCRIPT_RECORDED_PASS`，积分超市/余额 独立入口已通过；商城页行为不证明 |
| 133 | FrameOS duplicate node insertion | [`liblib-frameos-batch133-2026-09-06/`](liblib-frameos-batch133-2026-09-06/) `SCRIPT_RECORDED_PASS`，Cmd+D 插入副本/undo/redo/toast 已通过 |
| 148 | Project card cover placeholders | [`liblib-canvas-batch148-2026-09-07/`](liblib-canvas-batch148-2026-09-07/) `SCRIPT_RECORDED_PASS`，封面占位图/节点计数已通过；源站封面内容不证明 |
| 169 | Character library tabs + consent gate mock | [`liblib-canvas-batch169-2026-09-07/`](liblib-canvas-batch169-2026-09-07/) `SCRIPT_RECORDED_PASS`，12 checks |
| 168 | /project left sidebar | [`liblib-canvas-batch168-2026-09-07/`](liblib-canvas-batch168-2026-09-07/) `SCRIPT_RECORDED_PASS`，13 checks |
| 167 | /project secondary surface alignment | [`liblib-canvas-batch167-2026-09-07/`](liblib-canvas-batch167-2026-09-07/) `SCRIPT_RECORDED_PASS`，14 checks |
| 166 | Prompt region visual + chip removal | [`liblib-canvas-batch166-2026-09-07/`](liblib-canvas-batch166-2026-09-07/) `SCRIPT_RECORDED_PASS`，6 checks |
| 165 | Reference slot row layout | [`liblib-canvas-batch165-2026-09-07/`](liblib-canvas-batch165-2026-09-07/) `SCRIPT_RECORDED_PASS`，7 checks 槽行几何 |
| 164 | Footer trigger class alignment | [`liblib-canvas-batch164-2026-09-07/`](liblib-canvas-batch164-2026-09-07/) `SCRIPT_RECORDED_PASS`，8 checks 触发器几何 |
| 163 | Tablet breakpoints 768/1024 | [`liblib-canvas-batch163-2026-09-07/`](liblib-canvas-batch163-2026-09-07/) `SCRIPT_RECORDED_PASS`，平板 10 checks + 截图 |
| 162 | Mobile 390 breakpoint check | [`liblib-canvas-batch162-2026-09-07/`](liblib-canvas-batch162-2026-09-07/) `SCRIPT_RECORDED_PASS`，移动端 6 checks + 截图 |
| 161 | Panel height 397px overflow fix | [`liblib-canvas-batch161-2026-09-07/`](liblib-canvas-batch161-2026-09-07/) `SCRIPT_RECORDED_PASS`，测量断言防复发 |
| 160 | Chip long-video mode + slot empty-state | [`liblib-canvas-batch160-2026-09-07/`](liblib-canvas-batch160-2026-09-07/) `SCRIPT_RECORDED_PASS`，14700 直证 + 去条 |
| 159 | 尝试列移入节点卡内 | [`liblib-canvas-batch159-2026-09-07/`](liblib-canvas-batch159-2026-09-07/) `SCRIPT_RECORDED_PASS`，卡内纵向芯片 + 面板去重 |
| 158 | Default model revert + corrections | [`liblib-canvas-batch158-2026-09-07/`](liblib-canvas-batch158-2026-09-07/) `SCRIPT_RECORDED_PASS`，2.5 回落 + 联动直证 + 勘误记录 |
| FrameOS 157 | Context menu e2e verification | [`liblib-frameos-batch157-2026-09-07/`](liblib-frameos-batch157-2026-09-07/) `SCRIPT_RECORDED_PASS`，12 checks；行为表勘误 |
| 156 | batch93 drawer-close flake hardening | [`liblib-canvas-batch156-2026-09-07/`](liblib-canvas-batch156-2026-09-07/) `SCRIPT_RECORDED_PASS`，3/3 稳定通过 |
| 155 | 5min chip duration range fix | [`liblib-canvas-batch155-2026-09-07/`](liblib-canvas-batch155-2026-09-07/) `SCRIPT_RECORDED_PASS`，参数菜单长布局/取消钳制已通过 |
| 154 | Full verifier sweep (124) | [`liblib-canvas-batch154-2026-09-07/`](liblib-canvas-batch154-2026-09-07/) `SWEEP_RECORDED_PASS`，112 通过/12 老化/0 未解释 |
| 153 | Auto factor confirmation + panel behavior bounds | [`liblib-canvas-batch153-2026-09-07/`](liblib-canvas-batch153-2026-09-07/) `DOCS_RECORDED`，证据 batch；230=5×46 直证、新建节点无面板 |
| 152 | /project card sub-line + coverage matrix refresh | [`liblib-canvas-batch152-2026-09-07/`](liblib-canvas-batch152-2026-09-07/) `SCRIPT_RECORDED_PASS`，副行仅日期已通过；矩阵吸收 149-152 证据 |
| 151 | Toolbar/credits micro-alignment (round-2 sample) | [`liblib-canvas-batch151-2026-09-07/`](liblib-canvas-batch151-2026-09-07/) `SCRIPT_RECORDED_PASS`，pill/积分块已通过；尝试门控与菜单选中态待窗口前置复测 |
| 150 | /project new-tab cards + panel container visuals | [`liblib-canvas-batch150-2026-09-07/`](liblib-canvas-batch150-2026-09-07/) `SCRIPT_RECORDED_PASS`，新标签契约/容器视觉已通过；跨页 store 差异记录在案 |
| 149 | Advanced settings column + default model 2.0 | [`liblib-canvas-batch149-2026-09-07/`](liblib-canvas-batch149-2026-09-07/) `SCRIPT_RECORDED_PASS`，纵向开关列/触发器缩写/积分 135 已通过；尝试联动冲突待受控复测 |
| 134 | FrameOS copy/paste clipboard cycle | [`liblib-frameos-batch134-2026-09-06/`](liblib-frameos-batch134-2026-09-06/) `SCRIPT_RECORDED_PASS`，Cmd+C→Cmd+V 粘贴副本/undo/重复粘贴已通过 |
| 116 | Script-generator node type | [`liblib-canvas-batch116-2026-09-06/`](liblib-canvas-batch116-2026-09-06/) `SCRIPT_RECORDED_PASS`，脚本NEW 创建 脚本生成器、卡片内容与本地交互已通过；真实生成/子界面不证明 |
| 117 | Director node card alignment | [`liblib-canvas-batch117-2026-09-06/`](liblib-canvas-batch117-2026-09-06/) `SCRIPT_RECORDED_PASS`，卡片文案/工作区进入与关闭已通过；工作区内部结构经采样确认一致 |
| 124 | Canvas recycle bin | [`liblib-canvas-batch124-2026-09-06/`](liblib-canvas-batch124-2026-09-06/) `SCRIPT_RECORDED_PASS`，软删除/回收站面板/内容完整恢复已通过；30 天自动清除不证明 |
| 119 | /project list page | [`liblib-canvas-batch119-2026-09-06/`](liblib-canvas-batch119-2026-09-06/) `SCRIPT_RECORDED_PASS`，页面结构/创建卡/画布卡导航与 logo 菜单路由已通过；回收站行为不证明 |

Each batch directory normally contains `README.md`, `PLAN.md` and `IMPLEMENTATION.md`; additional `*.spec.md`, JSON and screenshot analysis files are the detailed contract.

## Planned Work

| Batch | Focus | Entry |
|---|---|---|
| 80 | Director durable tombstone、storage/resource cleanup boundary | 已完成；clone-owned durable tombstone、cleanup/release 与 reload gate 已通过，详见 [`liblib-canvas-batch80-2026-08-28/`](liblib-canvas-batch80-2026-08-28/) |
| 81 | Director strict project import/export and recoverable UI workflow | 已完成；strict V1 document codec 到本地文件 workflow 的 clone-owned 闭环，详见 [`liblib-canvas-batch81-2026-08-29/`](liblib-canvas-batch81-2026-08-29/) |
| 82 | Director local resource lifecycle and finite OBJ/FBX materialization | 已完成；clone-owned session-local materializer 与 resource lifecycle 已通过，详见 [`liblib-canvas-batch82-2026-08-29/`](liblib-canvas-batch82-2026-08-29/) |
| 83 | Director command outcome feedback projection | 已完成；current verifier manifest、typed outcome/reason 到 Director primary feedback surface 的 clone-owned 最小闭环已通过，详见 [`liblib-canvas-batch83-2026-08-29/`](liblib-canvas-batch83-2026-08-29/) |
| 84 | Director object-tree lock/editability | 已完成；current verifier manifest、locked-target UI/store guard、zero mutation/history reject 和 unlock recovery 已通过，详见 [`liblib-canvas-batch84-2026-08-29/`](liblib-canvas-batch84-2026-08-29/) |
| 85 | Director object-tree selection/CRUD discoverability | 已完成；selection action bar、单选/多选数量、project-scoped copy、clear zero-history、reference-aware batch delete 和 mobile discovery 已通过，详见 [`liblib-canvas-batch85-2026-08-29/`](liblib-canvas-batch85-2026-08-29/) |
| 86 | Director transform target context and pointer cancellation | 已完成；目标上下文、真实 gizmo drag、pointercancel/lost capture、locked rejection、authoring/runtime/history continuity 和 mobile geometry 已通过，详见 [`liblib-canvas-batch86-2026-08-29/`](liblib-canvas-batch86-2026-08-29/) |
| 87 | Director undo/redo restore selection authority | 已完成；恢复策略显式化、有效选择保留、失效选择 repair、对象树/Inspector/Viewport/Timeline authority 和 portable document exclusion 已通过，详见 [`liblib-canvas-batch87-2026-08-29/`](liblib-canvas-batch87-2026-08-29/) |
| 88 | Director selection/timeline/TransformControls authority | 已完成；单/多/分组选择 normalization、Timeline 反向选择、keyframe/path ownership、delete repair、locked zero mutation 和 mobile geometry 已通过，详见 [`liblib-canvas-batch88-2026-08-29/`](liblib-canvas-batch88-2026-08-29/) |
| 89 | Director scene settings and add-camera discoverability | 已完成；场景设置、ground/grid/颜色控件、对象树/Inspector 新增机位入口、camera track/keyframe 连续性和 current gate 已通过，详见 [`liblib-canvas-batch89-2026-08-29/`](liblib-canvas-batch89-2026-08-29/) |
| 90 | Director project/session diagnostics and scene semantic command | 已完成；session outcome/lifecycle 可观察性、scene draft/commit、typed command、persistence、one-entry history、no-op/reject、undo/redo 和 mobile Inspector focused gate 已通过，详见 [`liblib-canvas-batch90-2026-08-29/`](liblib-canvas-batch90-2026-08-29/) |
| 91 | Director object/camera/group command and history boundary | 已完成；对象属性、相机设置、角色组创建/重命名/变换的 typed command、persistence、draft/commit、no-op/invalid/reference guard、one-entry history 和 focused gate 已通过，详见 [`liblib-canvas-batch91-2026-08-29/`](liblib-canvas-batch91-2026-08-29/) |
| 92 | Director local resource lifecycle and session lease | 已完成；strict descriptor/decoded-byte budget、owner-scoped lease、deferred/final release、有限 OBJ/FBX materialization、失败 proxy、retry/cancel 和 focused gate 已通过，详见 [`liblib-canvas-batch92-2026-08-29/`](liblib-canvas-batch92-2026-08-29/) |
| 93 | Director final desktop/mobile regression and governance closeout | 已完成；桌面/移动端 Director 回归、普通画布跨批回归、Batch 59/67-92 current gates、治理文档和全量检查已通过，详见 [`liblib-canvas-batch93-2026-08-29/`](liblib-canvas-batch93-2026-08-29/)；本批完成后按计划停止 |
| 94 | Director focus containment and keyboard boundary | 已完成；workspace 与移动抽屉焦点边界、回焦、`aria-hidden`/`inert`、Escape/editable 优先级和 desktop/mobile focused verifier 已通过，详见 [`liblib-canvas-batch94-2026-08-29/`](liblib-canvas-batch94-2026-08-29/)；本批完成后按用户要求停止 |
| 95 | Director canvas image ingress and session-only environment preview | 已完成；普通画布直接上游图片进入 Director session 的 typed projection、R3F 环境预览、错误隔离和 desktop/mobile 专项 verifier 已通过，详见 [`liblib-canvas-batch95-2026-08-29/`](liblib-canvas-batch95-2026-08-29/)；本批完成后停止，不自动启动 Batch 96 |
| 96 | Director multi-camera and Shot workflow | 已完成；portable Shot、legacy V1 decode、Shot create/switch/update、capture provenance/gallery、camera/Shot delete repair、clipboard/whole-project duplicate remap、reload/import/export 和 desktop/mobile 专项 verifier 已通过，详见 [`liblib-canvas-batch96-2026-08-29/`](liblib-canvas-batch96-2026-08-29/)；本批完成后停止，不启动 Batch 97 |
| 97 | Agent drawer current-source alignment | 已完成；头部动作集合、源站 Skill 命名、composer 控件、选择模型目录菜单、生成模式菜单与本地反馈已通过，batch14 断言按 2026-09-05 源站更新，详见 [`liblib-canvas-batch97-2026-09-05/`](liblib-canvas-batch97-2026-09-05/)；后续批次按用户循环迭代指令继续 |
| 98 | Add-node panel current-source alignment | 已完成；智能剪辑命名、脚本双入口、素材库风格/特效子菜单、搜索过滤与本地资源反馈已通过，batch15 断言按 2026-09-05 源站更新，详见 [`liblib-canvas-batch98-2026-09-05/`](liblib-canvas-batch98-2026-09-05/)；循环迭代继续 |
| 110 | Aged-gate deprecation | 已完成；漂移 verifier 标注与登记已通过，详见 [`liblib-canvas-batch110-2026-09-05/`](liblib-canvas-batch110-2026-09-05/)；剩余候选均需 fixture 授权 |
| 111 | Character library modal alignment | 已完成；角色库模态对齐已通过，详见 [`liblib-canvas-batch111-2026-09-05/`](liblib-canvas-batch111-2026-09-05/)；其余候选需 fixture 授权 |
| 114 | Multi-canvas dropdown alignment | 已完成；多画布下拉对齐已通过（丢弃式采样解锁），详见 [`liblib-canvas-batch114-2026-09-06/`](liblib-canvas-batch114-2026-09-06/)；循环继续：115 双击生成、116 脚本生成器、117 导演台入口 |
| 115 | Canvas double-click add panel | 已完成；双击生成入口对齐已通过，详见 [`liblib-canvas-batch115-2026-09-06/`](liblib-canvas-batch115-2026-09-06/) |
| 141 | Video model menu full catalog | 已完成；模型菜单全量目录落地已通过，详见 [`liblib-canvas-batch141-2026-09-07/`](liblib-canvas-batch141-2026-09-07/)；循环继续 |
| 125 | Video panel attempts alignment | 已完成；视频面板对齐已通过，详见 [`liblib-canvas-batch125-2026-09-06/`](liblib-canvas-batch125-2026-09-06/)；循环继续 |
| 116 | Script-generator node type | 已完成；脚本生成器节点对齐已通过，详见 [`liblib-canvas-batch116-2026-09-06/`](liblib-canvas-batch116-2026-09-06/)；循环继续：117 导演台入口 |
| 117 | Director node card alignment | 已完成；导演台节点卡对齐已通过，详见 [`liblib-canvas-batch117-2026-09-06/`](liblib-canvas-batch117-2026-09-06/)；丢弃式采样四项发现全部落地 |
| 119 | /project list page | 已完成；全部项目页落地已通过，详见 [`liblib-canvas-batch119-2026-09-06/`](liblib-canvas-batch119-2026-09-06/)；循环继续 |
| 124 | Canvas recycle bin | 已完成；画布回收站落地已通过，详见 [`liblib-canvas-batch124-2026-09-06/`](liblib-canvas-batch124-2026-09-06/)；循环继续 |
| 133 | FrameOS duplicate node insertion | 已完成；FrameOS 复制节点缺口修复已通过，详见 [`liblib-frameos-batch133-2026-09-06/`](liblib-frameos-batch133-2026-09-06/)；循环继续 |
| 134 | FrameOS copy/paste clipboard cycle | 已完成；FrameOS 复制/粘贴闭环已通过，详见 [`liblib-frameos-batch134-2026-09-06/`](liblib-frameos-batch134-2026-09-06/)；循环继续 |
| 135 | Credits ratio factor | 已完成；积分比例因子已按当日采样落地，详见 [`liblib-canvas-batch135-2026-09-07/`](liblib-canvas-batch135-2026-09-07/)；循环继续 |
| 136 | Recycle bin selection | 已完成；回收站勾选与批量恢复已通过，详见 [`liblib-canvas-batch136-2026-09-06/`](liblib-canvas-batch136-2026-09-06/)；循环继续 |
| 139 | Topbar credits split | 已完成；顶栏积分入口拆分已通过，详见 [`liblib-canvas-batch139-2026-09-07/`](liblib-canvas-batch139-2026-09-07/)；循环继续 |
| 148 | Project card cover placeholders | 已完成；项目卡封面对齐已通过，详见 [`liblib-canvas-batch148-2026-09-07/`](liblib-canvas-batch148-2026-09-07/)；循环继续 |
| 169 | Character library tabs + consent gate | 已完成；页签与承诺书门已通过，详见 [`liblib-canvas-batch169-2026-09-07/`](liblib-canvas-batch169-2026-09-07/)；循环继续 |
| 168 | /project left sidebar | 已完成；侧边栏落地已通过，详见 [`liblib-canvas-batch168-2026-09-07/`](liblib-canvas-batch168-2026-09-07/)；循环继续 |
| 169 | Character library tabs + consent gate | 已完成；页签与承诺书门已通过，详见 [`liblib-canvas-batch169-2026-09-07/`](liblib-canvas-batch169-2026-09-07/)；循环继续 |
| 170 | Top bar workspace rename input | 已完成；工作区输入已通过，详见 [`liblib-canvas-batch170-2026-09-07/`](liblib-canvas-batch170-2026-09-07/)；循环继续 |
| 167 | /project secondary surface alignment | 已完成；次级表面对齐已通过，详见 [`liblib-canvas-batch167-2026-09-07/`](liblib-canvas-batch167-2026-09-07/)；循环继续 |
| 166 | Prompt region visual + chip removal | 已完成；提示词视觉与芯片移除已通过，详见 [`liblib-canvas-batch166-2026-09-07/`](liblib-canvas-batch166-2026-09-07/)；循环继续 |
| 165 | Reference slot row layout | 已完成；槽行对齐已通过，详见 [`liblib-canvas-batch165-2026-09-07/`](liblib-canvas-batch165-2026-09-07/)；循环继续 |
| 164 | Footer trigger class alignment | 已完成；触发器几何对齐已通过，详见 [`liblib-canvas-batch164-2026-09-07/`](liblib-canvas-batch164-2026-09-07/)；循环继续 |
| 163 | Tablet breakpoints 768/1024 | 已完成；平板核查已通过，详见 [`liblib-canvas-batch163-2026-09-07/`](liblib-canvas-batch163-2026-09-07/)；循环继续 |
| 162 | Mobile 390 breakpoint check | 已完成；移动端核查已通过，详见 [`liblib-canvas-batch162-2026-09-07/`](liblib-canvas-batch162-2026-09-07/)；循环继续 |
| 161 | Panel height 397px overflow fix | 已完成；溢出修复已通过，详见 [`liblib-canvas-batch161-2026-09-07/`](liblib-canvas-batch161-2026-09-07/)；循环继续 |
| 160 | Chip long-video mode + slot empty-state | 已完成；整面板实拍对齐已通过，详见 [`liblib-canvas-batch160-2026-09-07/`](liblib-canvas-batch160-2026-09-07/)；循环继续 |
| 159 | 尝试列移入节点卡内 | 已完成；位置对齐与联动保持已通过，详见 [`liblib-canvas-batch159-2026-09-07/`](liblib-canvas-batch159-2026-09-07/)；循环继续 |
| 158 | Default model revert + corrections | 已完成；默认模型回落与勘误已通过，详见 [`liblib-canvas-batch158-2026-09-07/`](liblib-canvas-batch158-2026-09-07/)；循环继续 |
| FrameOS 157 | Context menu e2e verification | 已完成；右键菜单已验证并修正行为表，详见 [`liblib-frameos-batch157-2026-09-07/`](liblib-frameos-batch157-2026-09-07/)；循环继续 |
| 156 | batch93 drawer-close flake hardening | 已完成；flake 加固 3/3 稳定，详见 [`liblib-canvas-batch156-2026-09-07/`](liblib-canvas-batch156-2026-09-07/)；循环继续 |
| 155 | 5min chip duration range fix | 已完成；芯片时长范围与取消钳制已通过，详见 [`liblib-canvas-batch155-2026-09-07/`](liblib-canvas-batch155-2026-09-07/)；循环继续 |
| 154 | Full verifier sweep | 已完成；全量扫描已记录，详见 [`liblib-canvas-batch154-2026-09-07/`](liblib-canvas-batch154-2026-09-07/)；循环继续 |
| 153 | Auto factor confirmation + panel bounds | 已完成；证据 batch 已记录，详见 [`liblib-canvas-batch153-2026-09-07/`](liblib-canvas-batch153-2026-09-07/)；循环继续 |
| 152 | /project card sub-line + matrix refresh | 已完成；副行对齐与矩阵刷新已通过，详见 [`liblib-canvas-batch152-2026-09-07/`](liblib-canvas-batch152-2026-09-07/)；循环继续 |
| 151 | Toolbar/credits micro-alignment | 已完成；工具行与积分块对齐已通过，详见 [`liblib-canvas-batch151-2026-09-07/`](liblib-canvas-batch151-2026-09-07/)；循环继续 |
| 150 | /project new-tab cards + panel container visuals | 已完成；新标签页导航与面板容器已通过，详见 [`liblib-canvas-batch150-2026-09-07/`](liblib-canvas-batch150-2026-09-07/)；循环继续 |
| 149 | Advanced settings column + default model 2.0 | 已完成；高级设置纵向列与默认模型 2.0 已通过，详见 [`liblib-canvas-batch149-2026-09-07/`](liblib-canvas-batch149-2026-09-07/)；循环继续 |
| 146b | Character filter 文化区域 | 已完成；文化区域选项补全已通过，详见 [`liblib-canvas-batch146b-2026-09-07/`](liblib-canvas-batch146b-2026-09-07/)；循环继续 |
| 113 | Uniform character strip spacing | 已完成；均匀间距对齐已通过，详见 [`liblib-canvas-batch113-2026-09-05/`](liblib-canvas-batch113-2026-09-05/)；其余候选需 fixture 授权 |
| 112 | Character filter panel alignment | 已完成；筛选面板对齐已通过，详见 [`liblib-canvas-batch112-2026-09-05/`](liblib-canvas-batch112-2026-09-05/)；其余候选需 fixture 授权 |
| 108 | 97-107 series cross-batch regression | 已完成；跨批回归与漂移归因已记录，详见 [`liblib-canvas-batch108-2026-09-05/`](liblib-canvas-batch108-2026-09-05/)；循环迭代继续 |
| 107 | Skill headline rotation | 已完成；标题轮换对齐已通过，详见 [`liblib-canvas-batch107-2026-09-05/`](liblib-canvas-batch107-2026-09-05/)；循环迭代继续 |
| 106 | Project menu alignment | 已完成；项目菜单对齐已通过，详见 [`liblib-canvas-batch106-2026-09-05/`](liblib-canvas-batch106-2026-09-05/)；循环迭代继续 |
| 105 | Collaborative follow banner | 已完成；跟随横幅展示与单层 ESC 合同已通过，详见 [`liblib-canvas-batch105-2026-09-05/`](liblib-canvas-batch105-2026-09-05/)；循环迭代继续 |
| 104 | Storyboard three-section alignment | 已完成；故事板三组对齐与 batch13 断言迁移已通过，详见 [`liblib-canvas-batch104-2026-09-05/`](liblib-canvas-batch104-2026-09-05/)；循环迭代继续 |
| 103 | Top-bar mode toggle alignment | 已完成；顶栏模式命名对齐与断言迁移已通过，详见 [`liblib-canvas-batch103-2026-09-05/`](liblib-canvas-batch103-2026-09-05/)；循环迭代继续 |
| 102 | Asset manager drawer alignment | 已完成；资产抽屉控件集合对齐与相邻回归已通过，详见 [`liblib-canvas-batch102-2026-09-05/`](liblib-canvas-batch102-2026-09-05/)；循环迭代继续 |
| 101 | Generation-history panel alignment | 已完成；生成历史模态对齐与入口更名已通过，详见 [`liblib-canvas-batch101-2026-09-05/`](liblib-canvas-batch101-2026-09-05/)；循环迭代继续 |
| 100 | Empty-canvas state and quick-create chips | 已完成；空画布空态与快捷芯片展示、本地反馈与切换隔离已通过，详见 [`liblib-canvas-batch100-2026-09-05/`](liblib-canvas-batch100-2026-09-05/)；循环迭代继续 |
| 99 | Shortcuts help panel copy alignment | 已完成；帮助面板四栏对齐 2026-09-05 快照、crosswalk 源站列刷新、运行时 handler 未改，详见 [`liblib-canvas-batch99-2026-09-05/`](liblib-canvas-batch99-2026-09-05/)；循环迭代继续 |

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
- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)：node/edge/primary selection、DOM focus zone、listener precedence、modal/Director ownership 与 stale documentation 的固定事实入口。
- [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)：selection snapshot、context precedence、surface keyboard policy、dispatch outcome、focus lifecycle 与 route/canvas/async composition 合同。
- [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：client/host/flow/node/media 坐标分域、actual host frame、live/stable viewport、手势 session、entry-specific placement 和 host resize 的跨入口合同。
- [`LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md)：文件/资产进入画布前后的 validation、metadata probe、temporary lease、materialization、graph projection、source surface 分域和 lifecycle gap 的 dated evidence。
- [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)：media intent、locator/asset/reference、provisional/semantic projection、cohort/history、async freshness 和 resource reachability 的跨入口权威。
- [`LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md`](LIBTV_EDITOR_SESSION_HISTORY_STATIC_AUDIT_2026-08-27.md)：foreground editor baseline、working draft、local/native/graph history、commit/cancel、async handoff 与 source-unknown 队列的 dated evidence。
- [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)：profile registry、field/source baseline drift、local history budget、no-op/sync/async acceptance、disposal 和 verifier 的跨编辑器权威。
- [`LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_STATIC_AUDIT_2026-08-27.md)：intrinsic/output/request/frame/measured/rendition 分权、Open Canvas 正反面、clone collision 和 LibTV source landscape sample 的 dated evidence。
- [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)：dimension authority、frame/rendition profile、fit transform、mixed-output、measurement freshness 和 editor media space 的跨媒体权威。
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
