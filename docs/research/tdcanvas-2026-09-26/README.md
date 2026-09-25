# TDCanvas 上游研究

> 研究对象：[`AICoderTudou/TDCanvas`](https://github.com/AICoderTudou/TDCanvas)（本地工作副本 `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`，origin 为 fork `wubuku/TDCanvas`）。
> 本目录只记录研究，不代表已经授权将其能力编码进 LibTV / FrameOS / Jimeng 克隆。

## 研究锚点

| 项目 | 值 |
|---|---|
| 上游远端 | `https://github.com/AICoderTudou/TDCanvas.git` |
| 分支 | `master` |
| 锁定提交 | `16b31273633f983cdbd8de05694ec36d471b2650`（2026-09-15） |
| 版本 | `v0.14.0` |
| 上游目录 | `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`（本地工作副本；**未建 submodule**，与 open-canvas 包协议不同，见 ITERATION_LOG v1） |
| 上游的上游 | `basketikun/infinite-canvas`（约 7k star，官网 canvas.best；本项目**未调研过**，归属 diff 待做） |
| 观察日期 | 2026-09-26 |
| 证据形态 | 静态源码阅读（未运行、未采样 DOM/网络） |
| 实施边界 | 研究和报告；等待用户明确授权后才编码 |

## 产品与技术定性（一句话）

TDCanvas 是 TDTV 的桌面端 AI 无限画布（Tauri 2 + Vite + React 19 + AntD 6 + Zustand 5）：**零画布库依赖的手写 DOM 画布内核**、本地优先持久化（localforage + Tauri media-cache）、生成走 AI 土豆（Aitudou）API、带本地 Agent 通道（Codex/Claude Code）与无沙箱插件系统（含 ComfyUI 本地集成）。

## Read Order

1. [REPORT.md](REPORT.md)：面向项目决策的完整结论与反面教材。
2. [SOURCE_ANALYSIS.md](SOURCE_ANALYSIS.md)：固定版本的模块级源码证据（渲染内核/状态/节点/交互生成/Agent/插件 + v2 周边表面补遗，全部 file:line）。
3. [INTERACTION_CATALOG.md](INTERACTION_CATALOG.md)：用户可达交互目录（触发→行为→证据→clone 相关性）与快捷键全表。
4. [PATTERN_CARDS.md](PATTERN_CARDS.md)：21 张模式卡 = TDCanvas 机制卡 TD-01..15 + 上游参考卡 UP-01..06，区分上游事实、机制拆解、clone 启发与验证门槛。
5. [UPSTREAM_DIFF_AUDIT.md](UPSTREAM_DIFF_AUDIT.md)：与上游 `basketikun/infinite-canvas` 的机制归属审计（继承/原创/上游独有，机械 diff 证据 + 上游机制逐个精读 §5/§6）。
6. [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)：26 项机制到 ADOPT_METHOD / ADAPT / RESEARCH_ONLY / DEFER / REJECT 的决策矩阵。
7. [ITERATION_LOG.md](ITERATION_LOG.md)：调研包版本史、覆盖面缺口与下一证据队列。

## 当前结论摘要

- **架构**：无 reactflow/konva/fabric 等画布库；`ViewportTransform {x,y,k}` 单一 transform 层 + DOM div 节点 + 锚定世界原点的固定 10000×10000 SVG 连线层（贝塞尔、流动光效）；280px 外扩视口裁剪虚拟化；小地图纯 div 实现。状态是「薄 store（仅项目文档 CRUD+persist）+ 4242 行页面编排」；undo/redo 是页面级全量快照双栈（180ms 防抖合并、拖拽暂停、上限 50）。
- **输入语义与 React Flow 惯例相反**：wheel 永远缩放（0.05–5、鼠标锚）、Space+拖拽被故意禁用（空白左键即平移）、ctrl/cmd+拖空白=框选；对 clone 是「React Flow 默认并非唯一解」的对照样本，但**不构成**改动 `CANVAS_NAVIGATION.md` 权威的证据。
- **数据与媒体**：全自动三级持久化漏斗（页面 effect → 400ms 防抖 → localforage）；媒体双轨制（IndexedDB Blob + Tauri media-cache：URL SHA-256 去重、SSRF 防护、manifest 原子写）；加载时五级 hydrate 恢复链；图片历史 24 条、FNV-1a 签名去重、支持 pinned 版本引用；项目封面=最新生成物数据推导；viewport 存进项目文档；**无 schema 版本无迁移**。
- **节点体系**：7 类内置（Aitudou 类型是未注册的遗留）；开放 `CanvasNodeDefinition` 注册表（ports 可函数、Content/Panel/toolbar 可注入、动态端口、缺插件占位）；port 锚点=等分比例模型；几何式分组（groupId+中心点包含）；删除引用清理链完整（含 13 项悬空 UI 状态清扫）。
- **生成管线**：连线=上游引用语义（@mention 标签、pinned、连线/objects 双模式互斥）；Aitudou 任务 8 相位状态机（partial 部分成功、attention 等参数、本地停止≠远端取消且明示计费、提交即写 journal 刷新恢复、节点级守卫防重复计费）；批量输出两代表（旧管线 batch 堆叠 / 新管线兄弟节点阵列）；图片后处理 crop/split/upscale 本地 Canvas 2D，angle 走 AI，mask-edit 是未接线死代码。
- **扩展通道**：canvas-agent 独立进程（loopback HTTP 17371 + 随机 token + Origin 白名单；Codex 走 app-server stdio JSON-RPC、Claude 走 CLI stream-json，双入口收敛到 30 个高级工具→8 种 `CanvasAgentOp` 原语）；网页持续上报快照、写操作经 SSE 回传并在网页侧二次确认（协议版本握手=5）。插件=无沙箱 ESM 主页面直执行（SECURITY 自认取舍）+ 宿主能力注入 + **与 Agent 共用 applyOps**；comfyui-local 演示完整闭环（API Format JSON→object_info 推导动态端口→沙化启动 ComfyUI→结果节点回填）。
- **对本项目的价值排序**：生成任务生命周期与媒体资源生命周期（对照 `VR-007`/`VR-015`/`VR-021`）> 统一画布指令集（Agent/插件共用 applyOps，Director 之外的 Agent 化参考）> 拖线到空白建节点/批量堆叠/图片历史 pinned（候选 ADAPT，需源站 fixture）> 手写内核与输入语义（对照研究，REJECT 移植）。
- **证据边界**：全部为静态阅读（锁定 `16b3127`）；上游归属已完成 diff 审计（`UPSTREAM_DIFF_AUDIT.md`：注册表/插件加载器/小地图/Agent 通道/Group/主题继承自 infinite-canvas，任务状态机/批量堆叠/图片历史/无线引用/对齐辅助线/氛围层/Aitudou/Tauri 为 TDCanvas 原创；上游 v0.19.0 比 TDCanvas v0.14.0 更新，两仓双向演化）；`chatSessions` 已定性为**无 UI 的遗留子系统**（数据链全就绪、零聊天 UI，真实助手走 agent 面板）；上游自身（selection-toolbar/canvas-proxy/Group 资源集合）是否独立立项待定（见 ITERATION_LOG v2 队列）。
