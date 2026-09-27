# BeefTV 画布上游研究

> 研究对象：[`glanderness/BeefTV`](https://github.com/glanderness/BeefTV)（本地工作副本 `/Users/yangjiefeng/Documents/glanderness/BeefTV`，origin 即 upstream，非 fork）。
> 本目录只记录研究，不代表已经授权将其能力编码进 LibTV / FrameOS / Jimeng 克隆。

## 研究锚点

| 项目 | 值 |
|---|---|
| 上游远端 | `https://github.com/glanderness/BeefTV.git` |
| 分支 | `master` |
| 锁定提交 | `85c9686c87a4c176449e29292beba8b96dc430bb`（2026-09-27，tag `v1.5.7`） |
| 上游最新已知 | `v1.5.9`（e2fd1d3，2026-09-28 fetch 发现；前移差异审计见 SOURCE_ANALYSIS §35，本包锚点不移动） |
| 版本 | `v1.5.7` |
| 上游目录 | `/Users/yangjiefeng/Documents/glanderness/BeefTV`（**未建 submodule**，与 open-canvas 包协议不同；工作树干净） |
| 项目起源 | 公共仓库历史始于 2026-09-24「publish audited BeefTV source snapshot」，为审计后快照发布；web 包名 `infinite-canvas` 仅为 package name，未发现与 `basketikun/infinite-canvas` 或 TDCanvas 的代码同源关系（全仓 grep 无引用） |
| 技术栈 | web：Vite + React 19 + TypeScript + Zustand + TanStack Query + AntD + Tailwind + Leafer + Excalidraw（仅绘图编辑器）+ ffmpeg.wasm + three.js（导演台）；backend：Go 1.25 + Gin + GORM + SQLite；桌面：Wails |
| 画布代码量 | `pages/canvas` + `components/canvas` + `stores/canvas` + `lib/canvas` 合计约 **73,000 行**（`wc -l` 实测 73,483） |
| 观察日期 | 2026-09-27 |
| 证据形态 | 静态源码阅读（未运行、未采样 DOM/网络）；7 路并行模块精读 + 内核人工核读 + 关键断言抽查（见 ITERATION_LOG v1） |
| 实施边界 | 研究和报告；等待用户明确授权后才编码 |

## 产品与技术定性（一句话）

BeefTV 是「AI 影视/短剧创作工作台」：**自研 DOM 画布内核（零 reactflow/konva/fabric 依赖）+ 与 React 相对解耦的双轨视口渲染（live DOM 直写 / committed React state）+ 预算化视口虚拟化（720 节点 / 5000 连线 DOM 上限）+ 带存储锁与 storageRevision 三方 rebase 的本地优先持久化 + generationEffectKeys 两阶段事务性生成落账 + Leafer 连线图形层 + Go 后端任务/资源/版本中心 + 云端 Agent（CanvasOperation 8 原语指令集 + 审批 + 三路合并）**；并且内置 LibTV / TapNow 在线画布导入与对 LibTV 公开画布的像素级捕获夹具。

## Read Order

1. [REPORT.md](REPORT.md)：面向项目决策的完整结论、高价值机制与反面教材。
2. [SOURCE_ANALYSIS.md](SOURCE_ANALYSIS.md)：模块级源码证据 35 章（§1-13 画布本体：内核视口/状态持久化/节点/连线/交互/渲染性能/历史版本/生成管线/上传媒体/Agent/导演分镜/工作区与跨产品导入；§14-32 增补：后端画布历史与数据模型/上游回归断言与 LibTV 对齐/插件运行时/本地伴随进程/产品功能清单对照/测试套件全景/协议引擎/时间线命令协议/内置插件能力面/导演台内部/时间线几何/后端任务域/官方应用与技能域/导演台 UI 边角/时间线编辑器八插槽面板/provider 域水合鉴权与出站边界/字幕高亮与 SRT 重分段/选区浮层与主工具栏/交叉校验台账；§33-34 导演台 workbench 编排层精读与 viewport 二次核读；§35 上游前移差异审计 v1.5.7→v1.5.9），全部 file:line 对齐锁定提交。
3. [INTERACTION_CATALOG.md](INTERACTION_CATALOG.md)：用户可达交互目录（视口手势/工具模式/选择/连线/节点生命周期/菜单/生成工作流 + 快捷键全表），每项带触发、行为、file:line 与 clone 相关性。
4. [PATTERN_CARDS.md](PATTERN_CARDS.md)：45 张模式卡 BF-01..45，区分源码事实、机制拆解、clone 启发与验证门槛。
5. [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)：44 项机制到 ADOPT_METHOD / ADAPT / RESEARCH_ONLY / DEFER / REJECT 的决策矩阵。
6. [ITERATION_LOG.md](ITERATION_LOG.md)：调研包版本史、覆盖面缺口与下一证据队列。

> 自检：`python3 scripts/check-beeftv-research.py`（只读）——校验 § 交叉引用、BF 卡号解析、ADOPTION 矩阵行号与汇总分桶、模式卡/矩阵计数声明的一致性。

## 当前结论摘要

- **架构**：无 reactflow/konva/fabric；自研 `InfiniteCanvas` 容器（wheel/pan/pinch/Space/意图路由）+ 两层世界 div（translate 层 + committed-scale 光栅层，CSS 变量 `--canvas-live-*` 驱动）+ DOM 节点卡；连线与选择套件下沉 Leafer 位图层，SVG 仅作 hover/选中强调层。视口是**三频率双轨**：交互期每帧直写 DOM（`translate3d`）、React 侧 64ms 节流刷新虚拟化、停 120ms 才 commit 进 React state。
- **性能体系**：均匀网格空间索引（1024 cell）只做裁剪不做命中；DOM 预算 720 节点/5000 连线，enter/retain 双边距防闪烁，缩放分档预算（280/420/720）；三档性能模式（auto：≥80 节点或 ≥32 媒体降效）；媒体侧「静态首帧 + 全局单解码器 hover 租约 + Blob LRU 缓存（quota 20%/2GB/500 条）」。
- **输入语义与 React Flow 惯例多处相反**：默认工具即框选（V/H 切换，H/Space/中键/触控板才平移）；Delete 优先删选中连线；端口是 hover 侧栏「+」轨道、真实锚点恒为边缘垂直中心；拖线命中是 56px 屏幕像素圆形吸附；**拖线到空白/点 pin 弹「引用该节点生成」快速创建菜单**；无既有连线端点拖拽重连（换参考靠把线拖到提示词面板参考 chip 的 `elementFromPoint` 命中）。这些是「React Flow 默认并非唯一解」的又一对照样本，**不构成**改动 `CANVAS_NAVIGATION.md` 权威的证据。
- **状态与持久化（本项目最值得关注的部分）**：Zustand store 只存 `CanvasProject[]`（文档内嵌 nodes/connections/chatSessions/viewport/directorScenes/timeline）；持久化是 400ms 防抖队列 + Web Locks 跨标签串行 + 失败不毒化队列 + `storageRevision`/tombstone 三方 rebase（多标签页字段级合并，durable 胜出）；生成结果用 `generationEffectKeys` 戳记做**两阶段事务持久化**——普通队列只携带已确认 stamp，失败时 `rollbackGenerationValue` 做 previous/attempted/live/durable 四态递归回滚。
- **生成管线**：任务绑定写进节点 metadata（taskId/taskStatus/taskProgress...）；轮询（2s）多播订阅 + 刷新后按 taskId 对账恢复；防重复计费四层防线（节点级提交互斥、请求指纹二次确认、运行中拦截、clientOperationId 幂等）；图片 count>1 = root+N 子节点各自独立任务；媒体版本族（`versionOfNodeId/versionLabel/versionPrimary`）；失败重试按指纹阻止审核类误重试。
- **历史**：用户级 undo/redo 是**实体差异补丁栈**（by-id EntityChange + 顺序 + 180ms 防抖合并 + 上限 50 + 拖拽暂停），不是全量快照也不是命令模式；Agent 批次另用整批 before 快照栈（引用失配即清栈）；项目级版本历史在 Go 后端（automatic/before_restore 快照）。
- **Agent**：云端 run（REST+SSE）+ `CanvasSnapshot` 上报 + `CanvasOperation` 8 原语（add/update/delete_node、delete_connections、connect、set_viewport、select、run_generation）+ 服务端 7 操作审批预览 + patch 三路合并（终态保护 + 40ms 批处理）+ 上下文预算（按用户轮省略、384KB 硬失败）+ 后置事实复核（资源物化才算完成）。与 TDCanvas 的本地 applyOps 通道互为「Agent 操作画布」的两极形态。
- **对本项目的价值排序**：(1) 持久化对账三件套（storageRevision rebase / generationEffectKeys 两阶段 / Web Locks 队列）——对照 `VR-015`/`VR-017`/`VR-021` 的工程化参照；(2) 防重复计费四层 + 任务对账恢复——对照 `VR-007`；(3) `CanvasOperation` 统一指令集 + 事实复核——Director/Agent 化的协议形态首选（与 TDCanvas 结论互证）；(4) 渲染性能方法论（预算化虚拟化、语义引用稳定化、静态首帧+解码器租约）——clone 大画布化时的直接参照；(5) 媒体版本族、拖线快速创建菜单、Delete-优先连线——候选 ADAPT，需走 Par/verifier 流程；(6) 自研内核与输入语义分歧——对照研究，REJECT 移植。
- **特别记录**：BeefTV 自身内置 LibTV 在线画布导入（服务端按 UUID 抓取，hosted-only）与「LibTV 公开画布像素捕获 + `?fixture` 注入 + `?libtvChrome` 只读皮肤」三件套——即 **BeefTV 也把 LibTV 当作对标研究对象**；其上游测试甚至以测试名显式钉住「LibTV 800% precision zoom ceiling」「导入的 LibTV 缩略图不急载」「libtv-res 快照首帧推导」（BF-39），与本项目源站采样构成第三方互证。
- **证据边界**：全部为静态阅读（锁定 `85c9686`/v1.5.7）；Go 后端 `canvas_history.go`、`test/` 套件、`docs/content/docs/` 站点未深读（见 ITERATION_LOG v1 缺口队列）；手感类断言（动画时长/命中半径）未经实机复核。
