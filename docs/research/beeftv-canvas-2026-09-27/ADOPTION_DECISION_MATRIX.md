# BeefTV 机制采纳决策矩阵（ADOPTION_DECISION_MATRIX）

> 对象：BeefTV v1.5.7（锁定 `85c9686`）的 44 项机制 → 本项目（LibTV / FrameOS / Jimeng 克隆，React Flow 12）的采纳决策。
> 决策分桶（与 tdcanvas 包同义）：**ADOPT_METHOD**（方法/形态借鉴，作为设计权威参照，不等于立即编码）/ **ADAPT**（候选改造，吸收前需源站证据 + Par 编号 + verifier）/ **RESEARCH_ONLY**（仅研究对照）/ **DEFER**（暂缓，条件出现再评）/ **REJECT**（拒绝移植，有明确理由）。
> 本矩阵不改变任何现有实现；编码需用户明确授权。

| # | 机制 | 模式卡 | 决策 | 理由 / 本项目对照 |
|---|---|---|---|---|
| 1 | live/committed 双轨视口（三频率） | BF-01 | RESEARCH_ONLY | RF 自管 viewport，无法照搬；「交互期绕过 React」思路留给 overlay 性能课题（对照 `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT` live/stable 双域） |
| 2 | 预算化虚拟化 + 空间索引（720/5000、enter/retain 双边距、1024-cell 网格） | BF-03/BF-04 | ADOPT_METHOD | clone 大画布化时的直接参照；RF `onlyRenderVisibleElements` 无预算/双边距概念，此为补全方案 |
| 3 | 三档性能模式（auto 80 节点/32 媒体阈值） | BF-05 | ADAPT | 形态可直接吸收；前提是 clone 有可降效果面，先立性能预算基线 |
| 4 | 语义引用稳定化（拖拽期 memo 保引用、几何/语义变更分级） | BF-06 | ADOPT_METHOD | Zustand selector 结构可直接应用：位置拖拽不应触发提示词面板重渲染 |
| 5 | Leafer 连线/套件位图层（CSS 预览 + 阈值 rebase） | BF-07 | REJECT | RF SVG 边体系已覆盖需求；仅在边渲染被证实为瓶颈时重开 |
| 6 | 纯 DOM 小地图（预览/commit 两段、按需挂载） | BF-08 | RESEARCH_ONLY | 若 clone 做小地图可参考；需先定义与 RF viewport 的同步面 |
| 7 | 视频静态首帧 + hover 单解码器租约（3s 上限、激进释放） | BF-09 | ADOPT_METHOD | 高价值通用手法；clone 视频节点预览可直接借鉴，语义与源站不冲突 |
| 8 | 资源 Blob LRU 缓存（quota 20%/2GB/500 条） | BF-10 | ADAPT | `VR-021` media lifecycle 的工程化参照；clone 落资源层时再议 |
| 9 | 指针意图路由表（resolveCanvasPointerIntent） | BF-11 | RESEARCH_ONLY | RF gesture 体系不同；作为 gesture owner 划分的文档化对照（`LIBTV_VIEWPORT_COORDINATE_GESTURE_*`） |
| 10 | 默认框选工具化（空白左键=框选、V/H 切换） | BF-12 | REJECT | 与 LibTV 源站权威（`CANVAS_NAVIGATION.md` Batch 77：blank-drag no-op、Shift+drag marquee）相反，不构成改动证据 |
| 11 | hover 侧栏「+」端口 + 锚点恒边缘垂直中心 | BF-13 | RESEARCH_ONLY | 源站 `+` Handle 是真 affordance（AGENTS.md 硬约束）；「视觉把手与几何锚点解耦」原则本身可记入设计常识 |
| 12 | 拖线圆形吸附命中（56px 屏幕像素 / k） | BF-14 | RESEARCH_ONLY | RF handle DOM 热区不同；做「拖线自动吸附」时借其算法；先采源站吸附语义 |
| 13 | 拖线到空白=「引用该节点生成」快速创建菜单（点 pin 即弹） | BF-15 | ADAPT | 与 TDCanvas TD-03 互证的开源画布惯例；需源站采样证据 + Par 编号 + verifier 后才落地 |
| 14 | 拖线换参考（elementFromPoint 命中参考 chip） | BF-16 | RESEARCH_ONLY | 形式依赖面板 DOM 结构、脆弱；LibTV 引用槽有自己的交互语义 |
| 15 | 连线接近 3D tilt 反馈 | BF-17 | DEFER | 纯装饰；源站无此视觉语言，性能降级清单里也排不上优先级 |
| 16 | Delete 优先删选中连线（删除目标歧义消解） | BF-18 | ADAPT | clone 同样有 selectedNode/selectedEdge 双态；吸收前进 `LIBTV_SHORTCUT_RUNTIME_CROSSWALK` 核对不与源站冲突 |
| 17 | 外置标题头反向缩放（1/scale、<0.35 隐藏） | BF-19 | RESEARCH_ONLY | 节点标题形态对照；RF 下需 NodeToolbar 类机制，先看源站标题形态 |
| 18 | 媒体自适应尺寸（manualSize 用户意图让位） | BF-20 | RESEARCH_ONLY | 源站约束是「图片节点保持原始比例」；若未来做自适应，manualSize 让位是必须配套 |
| 19 | 实体差异补丁 undo 栈（by-id 前后像 + 180ms 合并） | BF-21 | ADOPT_METHOD | clone history 层的设计参照（对照 `LIBTV_GRAPH_TRANSACTION_CATALOG`）；「事务语义目录+实体补丁」可能是混合最优 |
| 20 | Agent 整批 before 快照撤销（用户接手即失效） | BF-22 | ADOPT_METHOD | Director/Agent 化时首选撤销语义（比逐 op inverse 诚实）；立项时评审 |
| 21 | storageRevision + tombstone 三方 rebase（多写者乐观并发） | BF-23 | ADOPT_METHOD | 对照 `VR-017` 多画布 lifecycle 的本地冲突面；clone 单标签现状不阻塞记录此协议 |
| 22 | generationEffectKeys 两阶段事务持久化 + 四态递归回滚 | BF-24 | ADOPT_METHOD | 高价值：`VR-015` async ingress「stale/duplicate 收敛」在持久化层面的完整解法 |
| 23 | Web Locks 跨标签持久化串行 + 失败不毒化队列 | BF-25 | ADAPT | 通用工程纪律；clone 引入本地持久化写路径时吸收 |
| 24 | CanvasOperation 8 原语统一指令集 + verifyCanvasOperations 后置事实复核 | BF-26 | ADOPT_METHOD | 高价值：Director/Agent 化协议形态首选（与 tdcanvas 包结论互证）；复核话术/`resourceReady` 思路可进 verifier 体系 |
| 25 | 任务→节点 metadata 绑定 + 刷新按 taskId 对账恢复 | BF-27 | ADOPT_METHOD | 对照 `VR-007`/`VR-015`；「刷新对账」是 clone 异步结果语义缺失环节的补全参照 |
| 26 | 防重复计费四层防线（互斥锁/指纹确认/运行中拦截/幂等 id） | BF-28 | ADOPT_METHOD | 对照 `VR-007`；形态适用于任何昂贵本地操作 |
| 27 | 图片批量 root+children（每子独立任务）与退休重试 | BF-29 | RESEARCH_ONLY | LibTV 源站是「尝试列」语义（batch158），形态不同；仅记录 |
| 28 | 媒体版本族（兄弟节点 + versionPrimary 标志） | BF-30 | ADAPT | 生成历史的另一种节点表达（对照 batch101 生成历史模态；与 tdcanvas TD-06/TD-09 两极）；需源站语义对照 |
| 29 | 连线顺序=引用编号唯一源 + @mention composer 双模式 | BF-31 | RESEARCH_ONLY | 与 open-canvas 包 `LIBTV_AUTOLINK_STATE_MATRIX` 的引用语义对照第三方案 |
| 30 | 批量创作表（batch-table 表格×画布节点） | BF-32 | DEFER | 产品形态差异大，无对应源站物；产品立项才评 |
| 31 | 上传三层存储（本地 IndexedDB/后端 canonical/pendingRemoteUpload 降级） | BF-33 | RESEARCH_ONLY | `VR-021` validation/probe/materialization 状态机的真实实现参照；clone mock 形态暂不引入 |
| 32 | 视频本地处理（ffmpeg.wasm 同源内核、ISO-BMFF 输出校验、原生抽帧） | BF-34 | DEFER | clone 无后端且禁止真实生成（AGENTS.md 边界）；本地媒体工具立项时全套参照 |
| 33 | Agent patch 三路合并 + 生成终态保护（40ms 批处理） | BF-35 | ADOPT_METHOD | 高价值：`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE` 的合并纪律参照；「本地已知终态不被旧事件回退」是关键不变量 |
| 34 | Agent 上下文预算（按用户轮省略 + 省略声明 + 硬失败上限） | BF-36 | RESEARCH_ONLY | Agent 化时的上下文治理参照；诚实性约束（明示省略）值得记住 |
| 35 | LibTV 像素捕获夹具三件套（捕获→夹具→opt-in 注入→只读皮肤） | BF-37 | ADAPT | 与本项目 screenshot/verifier 体系互证；「原站固定几何回归」需要时按 `CANVAS_TEST_MEDIA` 授权边界复用此法 |
| 36 | 跨产品导入中间表示（ImportResult + 统计披露 + importSource 溯源 + 两段确认） | BF-38 | RESEARCH_ONLY | 若做「导入 BeefTV/其他画布导出物」时的直接模板 |
| 37 | 显式 LibTV 对齐证据（800% 缩放上限 / 导入物缩略图不急载 / libtv-res 快照推导） | BF-39 | RESEARCH_ONLY | 第三方对 LibTV 行为的独立采样，可与本项目源站合同交叉核对（旁证，不驱动改动） |
| 38 | 源码文本断言测试（readFileSync+toContain 回归钉、pretest 门禁） | BF-40 | ADOPT_METHOD | 与本项目静态审计+verifier 体系互证；「媒体预览不得含 video 元素」「控制面拦截画布手势」类不变量可在 clone verifier 对应 |
| 39 | 双插件体系（编译期内置 TS 插件 × 后端声明式协议包，前端零第三方执行） | BF-41 | RESEARCH_ONLY | 与 TDCanvas「无沙箱直执行」反面教材对照的安全姿态参照；clone 无插件需求，仅记录「上传物=纯数据、执行=宿主引擎」默认 |
| 40 | 本地伴随进程（framefield-local-runtime：loopback + CryptoKey 会话 + 模块 scope + 响应上限） | BF-42 | RESEARCH_ONLY | 本地推理/本地 Agent 通道的现成安全形态（与 tdcanvas canvas-agent 同构）；Agent 化立项时与云端形态对比评审 |
| 41 | TransformControls 冻结式手势事务（显式 attach + 同对象读回 + 冻结声明式 prop + blur=commit/Escape=cancel） | BF-43 | ADOPT_METHOD | 本项目 Director TransformControls 硬约束的成熟参照实现；Batch 77 契约复核时直接对照其「冻结 prop + 终态分型」 |
| 42 | 本地草稿 + 防抖排空循环 + revision 确认 + baseUpdatedAt 基线恢复 | BF-44 | ADOPT_METHOD | 画布持久化队列（BF-23/25）在编辑器域的细化版；clone 补「未保存恢复」时套用 |
| 43 | 白名单诊断（稳定码/常量 message/字段白名单）+ 确定性复现夹具与 15 条手工矩阵 | BF-45 | ADOPT_METHOD | 与本项目 verifier/稳定码文化同构；「复现矩阵」可用于 clone 手势/保存回归台账 |
| 44 | CSS 变量世界变换 + 交互期统一降负（`--canvas-live-*` / interacting 状态关阴影滤镜动画） | BF-02 | ADAPT | 通用低风险手法：clone 可对应「交互期关闭节点卡阴影/滤镜/过渡」；吸收前实测对 clone 节点卡的实际开销 |

## 分桶汇总

| 决策 | 数量 | 行号 |
|---|---|---|
| ADOPT_METHOD | 15 | 2,4,7,19,20,21,22,24,25,26,33,38,41,42,43 |
| ADAPT | 8 | 3,8,13,16,23,28,35,44 |
| RESEARCH_ONLY | 16 | 1,6,9,11,12,14,17,18,27,29,31,34,36,37,39,40 |
| DEFER | 3 | 15,30,32 |
| REJECT | 2 | 5,10 |
| 合计 | 44 | — |

## 阅读指引

- ADOPT_METHOD ≠ 立即编码：表示「若 clone 走到对应课题，此为首选参照形态」；每项的编码闸门见「理由/对照」列的 VR 合同或流程（Par 编号 + verifier）。
- REJECT 的两项（5/10）都是「与本项目既有权威（React Flow 边体系、`CANVAS_NAVIGATION.md`）直接冲突且有明确理由」的对照样本。
- 与 tdcanvas 包结论互证的三项：统一画布指令集（BF-24 ≈ TD-11 一族）、拖线建下游（BF-15 ≈ TD-03）、媒体版本/历史（BF-30 ≈ TD-06/TD-09）——两个独立开源画布在相同课题上收敛，可信度高于单一来源。
