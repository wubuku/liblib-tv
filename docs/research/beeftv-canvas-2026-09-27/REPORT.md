# BeefTV 画布调研报告（面向项目决策）

> 上游：[`glanderness/BeefTV`](https://github.com/glanderness/BeefTV)，锁定提交 `85c9686`（2026-09-27，tag v1.5.7）。
> 事实与 file:line 证据在 [SOURCE_ANALYSIS.md](SOURCE_ANALYSIS.md)；可迁移模式在 [PATTERN_CARDS.md](PATTERN_CARDS.md)；采纳判断在 [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)。
> 本报告区分三类陈述：**源码事实**（已核对）、**证据支撑的推断**（标注）、**clone 决策建议**（不改变现有实现，等待授权）。

## 1. 一句话结论

BeefTV 是「**自研 DOM 画布内核 + 与 React 解耦的双轨渲染（live DOM 直写 / committed React state）+ 事务化的生成落账持久化 + Go 后端任务/资源/版本中心 + 云端 Agent（封闭指令集 + 审批 + 三路合并）**」的 AI 影视创作工作台；对本项目的核心价值不是视觉皮肤，而是**四条轴线**：(a) 大画布性能工程（预算化虚拟化、空间索引、媒体解码器治理）的完整落地样本；(b) 持久化对账三件套（storageRevision 三方 rebase / generationEffectKeys 两阶段事务 / Web Locks 失败隔离）——`VR-015`/`VR-017`/`VR-021` 的工程化参照；(c) Agent 操作画布的协议形态（8 原语指令集 + 后置事实复核 + patch 合并终态保护），与 TDCanvas 本地 applyOps 互证；(d) 又一个「React Flow 默认并非唯一解」的对照样本（默认框选、Delete 先连线、hover 侧栏端口）。

## 2. 架构定性（源码事实）

| 维度 | BeefTV | 对本项目（React Flow 12 clone）的意义 |
|---|---|---|
| 画布内核 | 零画布库；`InfiniteCanvas` 容器（wheel/pan/pinch/Space/意图路由）+ 两层世界 div + CSS 变量变换 + DOM 节点卡 | 证明「手写内核」路线的第二例（与 TDCanvas 互证）；其视口/命中/虚拟化逐条可与 RF v12 对照 |
| 视口渲染 | 三频率双轨：DOM 每帧（translate3d）、React 64ms（虚拟化窗口）、commit 120ms 防抖 | RF 自管 viewport 无法照搬；「消费者分频」思想适用于 clone overlay/拖拽性能 |
| 性能 | 720/5000 DOM 预算、缩放分档预算、enter/retain 双边距、1024-cell 空间索引、三档性能模式、交互期 CSS 降负 | clone 大画布化的直接参照（ADOPT_METHOD） |
| 状态 | 文档内嵌一切（nodes/connections/chatSessions/viewport/directorScenes/timeline）的 `CanvasProject[]`；Zustand persist + 自定义 storage | 与 clone「store 承载 graph」相似；其 updateProject 的 `sameCanvasContent` 去重与时间戳归并可对照 |
| 持久化 | 400ms 防抖队列 + Web Locks 跨标签串行 + 失败不毒化 + storageRevision/tombstone 三方 rebase + generationEffectKeys 两阶段事务 | **本项目最值得关注**：多写者冲突与生成落账的完整工程解（VR-015/VR-017/VR-021 对照） |
| 节点体系 | 18 内置类型 + 开放注册表（插件可注入、缺类型优雅降级）；显式 parentId 分组；「视觉把手与几何锚点解耦」的端口模型 | 开放注册表与降级链是 RF custom node 之外的对照；parentId 显式分组与 RF parentNode 概念同构 |
| 连线 | 语义=参考引用流；Leafer 常驻层+SVG 强调层双层渲染；左出右进贝塞尔、无箭头；56px 圆形吸附 | 语义与 LibTV AutoLink/引用槽同题第三方案；双层渲染是性能选项 |
| 生成管线 | 任务绑节点 metadata；四层防重复计费；刷新对账恢复；图片批量 root+children；媒体版本族 | 与 `VR-007`（命令反馈）/`VR-015`（异步 ingress）逐条可比 |
| 历史 | 用户级=实体差异补丁栈（by-id 前后像）；Agent 级=整批 before 快照（用户接手即失效）；项目级版本在 Go 后端 | 三层历史各自取舍清晰，对照 clone history 层设计 |
| Agent | 云端 run（REST+SSE）+ CanvasSnapshot read model + 8 原语 + 审批（参数重建预览）+ patch 三路合并（终态保护）+ 上下文预算（按用户轮省略） | 「Agent 操作画布」的云端形态（TDCanvas 是本地形态）；Director/Agent 化时首选参照 |
| 跨产品 | 内置 LibTV/TapNow 在线画布导入（服务端抓取+中间表示+统计披露）；对 LibTV 公开画布做像素捕获夹具+只读皮肤 | **BeefTV 也在研究 LibTV**；其捕获三件套与本项目采样/verifier 体系互证 |

## 3. 输入语义分歧（值得记录的设计分歧）

1. **默认空白左键拖=框选**（工具化 V/H，H/Space/中键/触控板才平移）——与 LibTV 源站（blank-drag no-op、Shift+drag marquee）和 RF 默认（pan）都相反。
2. **Delete/Backspace 优先删选中连线**——显式消解「点线后节点仍选中」的删除歧义；注释给出完整理由。
3. **端口是 hover 侧栏「+」轨道**、真实锚点恒为边缘垂直中心；注释明示废弃过「按鼠标落点取 Y」的伪端口方案。
4. **拖线命中是 56px 屏幕像素圆形吸附**（除以 k），显式建模「靠近但拒绝」态；注释自称对齐 LibTV 的 80px 快速添加区。
5. **拖线到空白/点 pin = 弹「引用该节点生成」快速创建菜单**（不直接建线也不直接建节点）。
6. **无既有连线端点拖拽重连**；换参考靠把线拖进提示词面板的 `elementFromPoint` 命中。
7. fit view 永不放大超 100%（maxScale=1）；适应选区才允许 1.25。

> 结论（推断）：这些与 TDCanvas 的分歧清单合并，构成「开源画布输入语义没有共识」的证据集；对本项目的价值是确认 `CANVAS_NAVIGATION.md` 权威需要源站证据而非行业惯例支撑——BeefTV 的任何分歧都不构成改动理由（REJECT/对照）。

## 4. 高价值机制清单（对本项目的可借鉴点）

按「证据强度 × 对 clone 主题相关性」排序，完整矩阵见 ADOPTION_DECISION_MATRIX.md：

1. **generationEffectKeys 两阶段事务持久化**（SOURCE_ANALYSIS §3.3）：普通队列只携带已确认 stamp、生成专用 durable commit、失败四态递归回滚、无 stamp 溯源字段 fail-closed——`VR-015` 异步结果收敛在持久化层面的完整解法。
2. **storageRevision + tombstone 三方 rebase**（§3.4）：多标签页字段级合并、durable 胜出、stale 旁观者只保留 viewport——`VR-017` 多画布 lifecycle 的本地冲突面参照。
3. **防重复计费四层 + 刷新对账恢复**（§9.2/§9.3）：互斥锁/请求指纹二次确认/运行中拦截/幂等 id + taskId 对账——`VR-007` 直接可比。
4. **CanvasOperation 8 原语 + verifyCanvasOperations 后置事实复核**（§8.3）：封闭指令集+纯归约器+「资源物化才算完成」的中文复核话术——Director/Agent 化协议首选（与 tdcanvas 包 TD-11 互证）。
5. **Agent patch 三路合并 + 终态保护**（§11.2）：本地已知终态绝不被旧事件回退；40ms 批处理——`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE` 参照。
6. **预算化虚拟化 + 空间索引 + 语义引用稳定化**（§7.1-7.3）：720/5000 预算、enter/retain 双边距、几何/语义变更分级短路——clone 大画布化工具箱。
7. **视频静态首帧 + hover 单解码器租约 + Blob LRU 缓存**（§7.6/§10.4）：解码器是稀缺资源的治理方案——clone 视频预览可直接借鉴。
8. **媒体版本族（兄弟节点+primary 标志）**（§8.5）：生成历史与 TDCanvas 节点内历史互为两极；对 RF 兄弟节点式更友好（候选 ADAPT）。
9. **Delete 优先连线、拖线空白快速创建菜单**（§6.2/§6.3）：两个交互细节候选 ADAPT（均需源站证据+Par+verifier）。

## 5. 反面教材 / 风险（源码事实）

1. **巨石页面**：`project.tsx` 约 214KB，28+ 控制器 hook 挂在单一编排点；controller 拆分缓解但不消灭（对照本项目「组件合同+verifier」治理路线）。
2. **双字段易腐**：`composerContent` 与 `prompt` 双字段持久化、靠注释警告「不能互相覆盖，否则刷新后富引用退化」——用注释而非类型系统守不变量。
3. **上游自身文案 bug**：快捷键面板 V/H 文案与代码相反（`canvas-shortcuts.ts:117-123`）——帮助面板与实现漂移是真实风险，本项目有 `LIBTV_SHORTCUT_RUNTIME_CROSSWALK` 防同类问题。
4. **未接线保留代码**：`prepareInPlaceMediaVersion` 全仓无调用点、sandbox 插件渲染器显示「等待隔离运行时」——能力先行的死代码风险。
5. **上传无内容哈希去重**：幂等依赖预生成 storageKey；同一文件上传两次会产生两份存储（有意的取舍，但与「dedupe」预期不同，对照 `VR-021` dedupe 设计）。
6. **轮询而非 SSE 驱动任务**：2s 轮询多播简单可靠，但代价是延迟与请求量（文本流才用 SSE+游标）；对照本项目若引入真实任务流需权衡。

## 6. 证据边界

- 全部为**静态源码阅读**（锁定 `85c9686`/v1.5.7）；未运行应用、未采样 DOM/网络；动画时长、命中手感等未经实机复核。
- 方法（v1）：7 路并行模块精读（交互/渲染/历史/节点/生成/媒体/Agent 与集成）+ 内核文件人工核读（infinite-canvas.tsx、use-canvas-store.ts 全文）+ 5 处承重断言抽查（全部吻合）。
- 方法（v2 增补）：Go 后端 `canvas_history.go` 全读 + `backend-database.mdx` 画布章节 + 上游画布回归测试四件全读（SOURCE_ANALYSIS §14/§15）；确认 `http-api.mdx` 为高层索引文档（36 行）无逐路由清单。
- **特别发现（v2）**：BeefTV 把 LibTV 行为显式钉进自己的回归测试——「LibTV 800% precision zoom ceiling」（程序化缩放 clamp 8）、「导入的 LibTV 缩略图不急载」、libtv-res 快照首帧推导（BF-39）。这是第三方项目对 LibTV 行为的独立采样，可与本项目源站合同交叉核对。
- 未覆盖（下一证据队列见 ITERATION_LOG v2）：插件运行时与 `plugin-packages/`、media-conversion 本地推理运行时、`features.mdx` 产品清单对照、backend task/generation/provider 域内部、其余 local-* 测试；运行时行为未执行。
- 本地副本 origin 即 upstream（非 fork）；公共历史始于 2026-09-24 快照发布，更早开发史不可见（对「机制归属」类结论不构成影响：本文不做 fork 归属审计）。

## 7. 建议的后续动作（不执行，等待授权）

1. 若 LibTV clone 要补「拖线到空白建下游」「Delete 先连线」「媒体版本族」任一能力：先按协议走 `LIBTV_UIUX_PARITY_BACKLOG` Par 编号 + verifier 流程；模式卡 BF-15 / BF-18 / BF-30，并与源站采样对照（两个开源画布的收敛不是源站证据）。
2. Director/Agent 化立项时：优先评审 BeefTV 的「8 原语 + 整批快照撤销 + patch 三路合并 + 后置事实复核」组合（BF-22/24/26/33/35），与 tdcanvas 包 TD-11 的本地通道形态对比后定协议；后端侧参照 §14 的「revision CAS + 快照采样 + 恢复即新版本」历史语义。
3. clone 若遭遇大画布性能问题：按 BF-03/04/06/09 顺序引入（空间索引→预算化虚拟化→语义引用稳定化→媒体解码器租约），先立帧率/内存基线再动；上游 `canvas-spatial-index.test.ts` 的 50k 夹具与 `canvas-media-performance.test.ts` 的节流/双边距断言可直接借为测试设计参考（BF-40）。
4. 可选核对（低成本）：BeefTV 的「LibTV 800% 缩放上限」（BF-39）与本项目 `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT` 的 zoom 域采样做一次交叉核对——若一致，即为源站行为的第三方旁证。
