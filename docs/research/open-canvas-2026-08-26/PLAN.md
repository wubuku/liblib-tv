# Open Canvas 上游研究计划

## 1. 目标

把 `ZeroLu/open-canvas` 作为可复核的开源研究对象引入当前仓库，回答以下问题：

1. 它实际解决的是哪一种画布问题，和当前 LibTV/FrameOS 克隆的边界有什么不同？
2. 图模型、节点状态、边约束、执行链路、持久化、provider 和 storage 如何协作？
3. 官网当前公开的交互是否与固定 commit 的源码能力一致？
4. 哪些设计适合借鉴，哪些会与当前项目的双路线架构、原站证据纪律或本地 prototype 边界冲突？
5. 在没有用户授权编码前，哪些工作可以形成清晰、可执行的后续任务队列？

## 2. 范围

### 必查

- submodule 版本、许可证、README、贡献与发布约束；
- Next.js 路由、画布列表、studio shell 和 React Flow 编排；
- `CanvasNodeData`、序列化/规范化、图校验、环检测和 store 事务；
- 上游输入解析、scene 推断、credit quote、task descriptor 和本地 runner；
- Cyberbara/OpenRouter/Replicate provider、上传接口和 S3-compatible storage；
- 多语言、provider 设置、JSON 导入导出、画布保存/冲突/模板 API；
- 官网落地页、托管应用入口、设置向导和可见的空状态。

### 不做

- 不在当前项目 `src/` 中编码或重构；
- 不改变上游 submodule 的 checkout、源码或依赖安装状态；
- 不在官网创建画布、输入 Key、上传文件、执行生成或修改远端数据；
- 不把官网营销文案当作源码事实；
- 不把 open-canvas 的设计直接替换当前 LibTV 的原站行为。

## 3. 方法

1. 先记录工作区状态，所有提交只暂存本任务新增的 submodule/研究文件；不使用 `stash`、不回滚其他人的 WIP。
2. 以 submodule 指向的 `cf3a906` 为唯一源码基线，使用 `rg`、行号和静态调用链阅读。
3. 将结论拆成三类：`源码事实`、`官网观察`、`面向当前项目的推断/建议`。
4. 对官网使用只读浏览：读取 DOM、标题、可见文本、入口结构和截图；登录/Key/生成/上传均不进行。
5. 把每个高价值能力写成“当前项目现状 → 上游证据 → 价值 → 风险 → 待授权动作”，避免只列功能名。
6. 完成报告后只运行不改代码的文档/仓库状态检查；不因研究需要启动或改动当前业务实现。

## 4. 交付物

| 文档 | 用途 |
|---|---|
| `README.md` | 研究入口和结论摘要 |
| `SOURCE_ANALYSIS.md` | 固定版本源码考古和模块证据 |
| `RUNTIME_AUDIT.md` | 官网只读观察、截图和事实边界 |
| `REPORT.md` | 深度报告、架构图、数据流、比较和决策 |
| `EVIDENCE_MATRIX.md` | 声明 ID、证据级别、可证明范围和待验证项 |
| `UIUX_TRANSLATION.md` | Open Canvas 启发到 LibTV 后续 UI/UX 复刻 batch 的转译 |
| `INTERACTION_CATALOG.md` | 选中、连线、视口、复制、媒体历史、状态和 onboarding 的交互模式目录 |
| `LIBTV_SEEDANCE_CROSSWALK.md` | Open Canvas 交互启发与当前 LibTV Seedance 2.5 能力链的逐项交叉研究 |
| `LIBTV_OVERLAY_GEOMETRY_MATRIX.md` | LibTV 五图片节点双浮层、工具条版本漂移和 clone 缺口矩阵 |
| `LIBTV_IMAGE_ACTION_MATRIX.md` | LibTV 图片工具条当前动作的状态、呈现、副作用与 clone 优先级 |
| `LIBTV_AUTOLINK_STATE_MATRIX.md` | LibTV AutoLink 开关、候选、ghost、正式 mention、graph 关系与 clone 差异 |
| `LIBTV_OVERLAY_MULTIZOOM_MATRIX.md` | LibTV 双浮层多 zoom 几何、自然裁切、virtualization 和选择生命周期 |
| `../components/LibTVOverlayPositioning.contract.md` | 后续编码 agent 可直接引用的 screen/flow 坐标、标准 toolbar/panel 公式和验证断言 |
| `../components/LibTVAutoLink.contract.md` | 后续编码 agent 可直接引用的 Auto Link 候选、ghost、structured mention 和 graph 事务合同 |
| `../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md` | Open Canvas run/poll/patch 正反面、clone delayed writer 审计，以及 stale-safe completion、history/resource 和 verifier 设计 |
| `../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md` | 共同 React Flow 12.11.1 change/reducer 深读、Open Canvas/clone adapter 对照，以及 transport whitelist、whole-batch/current-snapshot 和 verifier 设计 |
| `../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md` | Open Canvas list/URL/hydrate/delete/save owner 深读、clone 多画布/viewport/UI/transient/async 审计，以及 lifecycle manifest、fixture 和 verifier 设计 |
| `../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md` | Open Canvas toast/node/save/form feedback 正反面、clone reason/string/timer/Director 审计，以及 outcome/primary-surface/owner、fixture 和 verifier 设计 |
| `../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md` | Open Canvas selected flags/editable/Radix 与 clone node/edge selection、listener phase、foreground modal/Director focus、Batch 50 drift 的 fixed static audit |
| `../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md` | validated selection、focus zone、command-context precedence、single-layer Escape、fixture 和 `LIBTV-VR-019` 正式设计权威 |
| `../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md` | Open Canvas dual anchor/live viewport/placement 正反面与 clone host/window center、gesture/placement owner 的 fixed static audit |
| `../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md` | actual host、six coordinate domains、live/stable/bootstrap/target viewport、gesture/placement owner、fixture 和 `LIBTV-VR-020` 正式设计权威 |
| `../LIBTV_MEDIA_INGRESS_RESOURCE_STATIC_AUDIT_2026-08-27.md` | Open Canvas validation/probe/upload/dedupe/save 正反面、clone mock/local-preview/blob-data 与 LibTV source surface 分域的 fixed audit |
| `../LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md` | ten entry profiles、intent/lease/asset/reference、cohort、reachability/release、fixture 和 `LIBTV-VR-021` 正式设计权威 |
| `libtv-media-ingress-source-dom-audit-2026-08-27.json` | LibTV source Add Resource、Generated History、Material、Asset、Shot 和 dormant uploader 的只读原始 DOM 记录 |
| `IMPLEMENTATION_IMPLICATIONS.md` | 仅作为待授权的后续设计队列 |
| `OPEN_CANVAS_PATTERN_CARDS.md` | 十一类可迁移的坐标、引用、状态、子图、async ingress、framework change routing、canvas lifecycle、command feedback、selection/focus/context、spatial 与 media/resource authority 模式卡，以及对应的 LibTV 证据闸门 |
| `ITERATION_LOG.md` | 研究报告的版本演进和维护规则 |
| [`LIBTV_VIEWPORT_COORDINATE_GESTURE_RESEARCH_PLAN_2026-08-27.md`](LIBTV_VIEWPORT_COORDINATE_GESTURE_RESEARCH_PLAN_2026-08-27.md) | 已完成并保留的 viewport/coordinate/gesture/placement 研究计划与交付历史 |
| [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md`](LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_RESEARCH_PLAN_2026-08-27.md) | 已完成并保留的 media ingress/resource lifecycle 研究计划与交付历史 |

## 5. 状态

- [x] 确认当前实际分支为 `master`，保护其他 WIP
- [x] 读取项目文档与已有研究入口
- [x] 查询并锁定上游 `main` commit
- [x] 以 git submodule 引入上游
- [x] 官网落地页和应用入口只读核对
- [x] 完成源码模块与数据流分析
- [x] 完成深度报告和当前项目映射
- [x] 完成 LibTV 五图片节点双浮层矩阵与 clone 静态差异审计
- [x] 完成 LibTV 当前图片工具条六动作的 bundle/live 风险分级审计
- [x] 完成 LibTV AutoLink 当前 bundle/live 状态链和 clone 语义差异审计
- [x] 完成 LibTV 双浮层 28%/34%/41%/50%/100% zoom 与空白选择生命周期审计
- [x] 从当前生产 chunk 确认标准图片工具条 host 的 `nodeTop - 24 * zoom - 10` + `translateY(-100%)` 定位公式
- [x] 完成元素编辑空态的专用 toolbar/stage/record panel 只读取证，并确认旋转入口在共享 fixture 中的派生节点与撤销边界
- [x] 精确核对共同 React Flow 12.11.1 change union/reducer、Open Canvas functional current-state adapter 和 generic non-select acceptance 边界
- [x] 完成 LibTV T0/T1/semantic whole-batch change routing、history/runtime-field sanitation、fixture 和 `LIBTV-VR-016` 设计
- [x] 完成 Open Canvas canvas list/URL document/hydrate/delete/save owner 正反面审计
- [x] 完成 LibTV multi-canvas registry/document/history/session/external owner manifest、fixture 和 `LIBTV-VR-017` 设计
- [x] 完成 Open Canvas toast/node/save/form feedback 正反面与 clone reason/string/timer/Director inventory 审计
- [x] 完成 LibTV command disposition/reason/primary-surface/owner、fixture 和 `LIBTV-VR-018` 设计
- [x] 完成 Open Canvas/clone selection、focus、editable guard 与 listener precedence 双向静态审计
- [x] 完成 LibTV validated selection、focus lifecycle、command-context precedence、fixture 和 `LIBTV-VR-019` 正式设计
- [x] 修正 PAR-004 与 overlay catalog 中 Batch 50 之前的 Director shortcut 事实漂移
- [x] 完成 Open Canvas/clone viewport、coordinate domain、gesture owner 与 placement writer 双向静态审计
- [x] 完成 viewport/coordinate/placement 正式合同、fixture 与 `LIBTV-VR-020` 设计
- [x] 完成 `OC-PATTERN-10`、`OC-ADOPT-023`、`OC-BP-010`、`LIBTV-UIX-20` 与治理追溯同步
- [x] 完成 Open Canvas/clone media validation、probe、materialization、descriptor、placeholder/partial/freshness/cleanup 双向静态审计
- [x] 完成 LibTV source upload/history/material/asset/Shot surface 的只读 DOM 分域与原始 JSON 记录
- [x] 完成 media intent/local lease/stable asset/node reference/cohort/reachability 正式合同、fixture 与 `LIBTV-VR-021` 设计
- [x] 完成 `OC-PATTERN-11`、`OC-ADOPT-024`、`OC-BP-011`、`LIBTV-UIX-21`、`DEC-037` 与治理追溯同步
- [x] 文档检查、提交并推送研究成果

## 6. 验收标准

- 任何 agent 从本 README 能找到固定上游版本、完整报告和源码证据；
- 报告能解释“为什么这样设计”，而不只是复述 README；
- 每个跨项目建议都明确是推断/建议而非 LibTV 或 open-canvas 的事实；
- 没有触碰其他人已修改的截图、Batch 36 文件或业务代码；
- submodule 和研究文档均可通过 Git 历史复核。
