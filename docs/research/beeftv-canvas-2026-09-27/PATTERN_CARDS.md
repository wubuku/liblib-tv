# BeefTV 模式卡（PATTERN_CARDS）

> 45 张卡 = BF-01..45。每卡四段：**源码事实**（file:line，锁定 `85c9686`）/ **机制拆解** / **clone 启发**（对 LibTV/FrameOS/Jimeng，React Flow 12 语境）/ **验证门槛**（若未来要吸收，必须先证明什么）。
> 卡号被 ADOPTION_DECISION_MATRIX.md 引用；重命名/删卡须同步矩阵与 `scripts/check-beeftv-research.py`。

## BF-01 live/committed 双轨视口（三频率）

- 源码事实：交互期 `scheduleViewportChange` 只走 rAF + `applyCanvasLiveViewport` 直写 DOM，≥32ms 才广播 preview 事件；停止 120ms 才 commit 进 React state；虚拟化窗口另按 64ms 节流刷新（`components/canvas/infinite-canvas.tsx:122-149`、`lib/canvas/canvas-live-viewport.ts:44-64`、`pages/canvas/use-canvas-viewport-controller.ts:179-187`）。
- 机制拆解：React 树在交互期完全静止；DOM 每帧、React 64ms、Leafer 每帧三条频率各取所需；commit 时刻才发生集中 re-render（`scale` prop 传全部可见节点）。
- clone 启发：React Flow 自管 viewport，无法照搬；但「交互期绕过 React、按消费者分频」的思路适用于 clone 的 overlay/拖拽/连线预览性能。
- 验证门槛：若 clone 引入同类分频，需证实在 RF 受管 viewport 下不与其内部 state 打架（对照 LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT 的 live/stable 双域）。

## BF-02 CSS 变量世界变换 + 交互期降负

- 源码事实：worldLayer 用 `--canvas-live-*` 变量做 translate、raster 层用 committed scale 单独缩放（规避搜狗 Chromium zoom 偏移）；`[data-canvas-viewport-interacting]` 下关 transition/box-shadow/filter/backdrop-filter/连线动画（`infinite-canvas.tsx:428-437`、`styles/globals.css:11407-11467`）。
- 机制拆解：变换与降负都是纯 CSS 状态切换，JS 只翻一个 dataset 标记。
- clone 启发：clone 已有 CSS 变量 token 体系；「交互期统一降负」是低风险高收益的通用手法。
- 验证门槛：在 RF 下等价开关是 RF 自身的样式；需实测对 clone 的节点卡阴影/滤镜开销。

## BF-03 均匀网格空间索引

- 源码事实：cell 1024 世界单位、跨格超 256 cell 进 largeEntry 线性兜底、`query(bounds, limit)` 提前返回且按插入序保序（`lib/canvas/canvas-spatial-index.ts:20-107`）。
- 机制拆解：O(1) 网格定位 + AABB 精筛；保序让虚拟化与连线裁剪的叠放确定。
- clone 启发：clone 若做大画布虚拟化，直接可用（纯函数、无依赖）；比 R 树简单得多。
- 验证门槛：clone 的节点量级是否真到需要索引（LibTV mock 场景目前不需要）。

## BF-04 预算化视口虚拟化（720/5000 + 双边距）

- 源码事实：DOM 预算 720 节点/5000 连线；缩放分档 280/420/720；enter（192/128px）与 retain（384/640px）双边距；选中/拖拽节点强制保留（`lib/canvas/canvas-performance-mode.ts:8-44`、`pages/canvas/use-canvas-render-model.ts:147-204`）。
- 机制拆解：双边距防「边缘挂载-卸载闪烁」；预算随缩放变化（缩得越小同屏节点越多、预算反而越低）。
- clone 启发：RF `onlyRenderVisibleElements` 只有单一 padding，无预算与双边距；大画布化时此设计可直接借用。
- 验证门槛：需先有 clone 大画布实测数据（帧率/内存）证明必要性。

## BF-05 三档性能模式（auto 阈值 80 节点/32 媒体）

- 源码事实：quality/performance/auto 三档 localStorage 持久化；auto 按节点与媒体数判定 `reduceMediaEffects`；降效=收紧 padding+关 tilt/滤镜，**不是图片占位**（`canvas-performance-mode.ts:11-33`）。
- 机制拆解：把「画质 vs 流畅」做成用户可感知的三档而非黑盒。
- clone 启发：可直接对照吸收的设置项形态。
- 验证门槛：clone 需先有可降的效果面（滤镜/tilt 等尚不存在则无意义）。

## BF-06 语义引用稳定化（拖拽期 memo 保引用）

- 源码事实：拖拽仅位置变化时 `semanticNodesRef`+`sameNodeSemanticData` 保持语义数组引用不变，昂贵派生（prompt 引用/资源引用）不重算；空间索引 geometry-unchanged 短路（`use-canvas-render-model.ts:161-213`）。
- 机制拆解：区分「几何变化」与「语义变化」两个变更等级，派生链按等级短路。
- clone 启发：clone 的 Zustand selector 结构里同样适用——位置拖拽不该触发提示词面板重渲染。
- 验证门槛：对 clone 实测拖拽期的 selector 触发面（React DevTools profiler）。

## BF-07 Leafer 连线/套件位图层

- 源码事实：连线常驻层+框选/对齐线/批量预览套件全在 Leafer 场景，`hittable:false`；交互中缩放比 [0.85,1.25] 只做 CSS 合成层预览不重绘矢量，超阈值才 rebase 场景树；20 字段 signature diff 增量（`canvas-leafer-graphics-layer.tsx:182-288,388-445`、`canvas-leafer-viewport.ts:7-20`）。
- 机制拆解：位图层规避每帧 SVG path 重排；「CSS 预览 + 阈值 rebase」是位图与矢量折中。
- clone 启发：RF 边已是 SVG，若边数量成为瓶颈这是候选逃生通道；常态不采用。
- 验证门槛：clone 边渲染 profile 证明 SVG 成为瓶颈（目前无此证据）。

## BF-08 纯 DOM 小地图

- 源码事实：240×160 面板每可见节点一个色块；图片缩略图 ≤24 张才显示；live 视口矩形直写 style；按需挂载（`canvas-mini-map.tsx:12-208`、`project.tsx:3435`）。
- clone 启发：小地图不必用 canvas；按需挂载+预览/commit 两段同样适用。
- 验证门槛：clone 若做小地图，需定义与 RF viewport 的同步面（避免双向回路）。

## BF-09 视频静态首帧 + hover 单解码器租约

- 源码事实：静止节点永不挂 `<video>` 只渲染首帧图（「原始视频 URL 永不返回，宁可用图标占位」）；hover 预览全局单解码器租约、350ms 延迟、3s 上限、8s deadline、任一交互/离屏立即销毁并 `removeAttribute("src")+load()`（`lib/canvas/canvas-media-preview.ts:4-17`、`canvas-video-hover-preview.ts:1-81`）。
- 机制拆解：浏览器视频解码器是全局稀缺资源；单租约+激进释放是画布多视频场景的关键设计。
- clone 启发：**高价值**——clone 的视频节点预览可直接借鉴此策略。
- 验证门槛：需源站对照（LibTV 源站视频节点行为）确认语义不冲突。

## BF-10 资源 Blob LRU 缓存

- 源码事实：预算=quota×20%（上限 2GB 下限 64MB 最多 500 条）、并发下载 16、首帧内存 objectURL 同步命中、播放确认后 4s 才后台拉全量、使用中不淘汰、pagehide 统一撤销（`services/resource-blob-cache.ts:27-324`）。
- clone 启发：对照 `VR-021` media lifecycle 的「reachability/release」工程化参照实现。
- 验证门槛：clone 为 mock 形态（blob-data 路径），引入前需先落资源层。

## BF-11 指针意图路由表

- 源码事实：`resolveCanvasPointerIntent` 单函数把 (pointerType,button,space,modifiers,background,boxSelectEnabled) 归约为 pan/select/ignore（`lib/canvas/canvas-selection.ts:26-34`）。
- 机制拆解：意图判定与行为执行分离，触控板走 wheel 通道不过此路由。
- clone 启发：对照 LIBTV_VIEWPORT_COORDINATE_GESTURE 的 gesture owner 划分；RF 场景下作为文档化映射而非代码移植。
- 验证门槛：仅当 clone 脱离 RF 默认手势时才需要。

## BF-12 工具化框选（默认框选、V/H 切换）

- 源码事实：默认 `canvasTool="box-select"`，空白左键拖=框选；H/Space/中键/触控板才平移；快捷键文案与代码相反（上游 bug）（`project.tsx:362`、`canvas-toolbar.tsx:153-166`、`canvas-shortcuts.ts:117-123`）。
- clone 启发：与 LibTV 源站语义（blank-drag no-op、Shift+drag marquee）相反，纯对照样本；**不改 CANVAS_NAVIGATION.md 权威**。
- 验证门槛：不适用（REJECT 语义移植）。

## BF-13 hover 侧栏端口 + 恒定锚点

- 源码事实：端口=hover/选中才出现的 80px 圆热区侧栏「+」轨道；真实锚点恒为节点边缘垂直中心，注释明示「按鼠标落点比例取 Y 会形成伪端口，已废弃」；anchorRatio 持久化但渲染不消费（`canvas-node.tsx:859-949`、`canvas-connections.tsx:175-194`、`use-canvas-connection-controller.ts:326`）。
- 机制拆解：「视觉把手」与「几何锚点」解耦——把手可以漂、锚点必须稳。
- clone 启发：对照 LibTV 源站 `+` Handle（React Flow Handle 是真 affordance，AGENTS.md 硬约束）；「锚点恒定」原则与 RF handle 语义一致。
- 验证门槛：源站若改版才重开；当前维持 RF Handle 方案。

## BF-14 圆形吸附命中（56px 屏幕像素）

- 源码事实：`CONNECTION_SNAP_RADIUS=56` 屏幕像素、除以 k 得世界半径、圆形区域判定、命中但策略不过=isNearNode 不吸附、注释「对齐 LibTV 的 80px 快速添加区」「不把节点矩形当目标」（`use-canvas-connection-controller.ts:61,458-497`）。
- 机制拆解：屏幕像素半径保证任何缩放下手感一致；「靠近但拒绝」显式建模。
- clone 启发：RF 的 handle 命中是 DOM 热区；若做「拖线到附近自动吸附节点」可借其算法。
- 验证门槛：需源站 fixture 证实 LibTV 自身吸附语义后再对照。

## BF-15 拖线到空白=「引用该节点生成」快速创建菜单

- 源码事实：松手在空白弹快速创建菜单（不直接建节点），位置按源节点锚点 Y 排布而非松手点；点 pin（≤5px）也弹菜单；创建后自动建线+选中+开面板；菜单项可用性用虚拟节点预校验（`use-canvas-connection-controller.ts:678-683,818-827,274-456`）。
- 机制拆解：把「连线」和「新建下游」统一成一个手势；菜单位置跟随世界坐标随视口重算。
- clone 启发：**候选 ADAPT**——与 TDCanvas TD-03 互证（两个开源画布都做了「拖线建下游」）；LibTV 是否有同款需源站采样。
- 验证门槛：源站证据（采样）+ Par 编号 + verifier。

## BF-16 拖线换参考（elementFromPoint 命中 chip）

- 源码事实：source 拖出的线松手在提示词面板参考 chip 或参考架→替换该参考（就近命中），跨 DOM 区域的「重连」（`use-canvas-connection-controller.ts:618-667`）。
- 机制拆解：用 `document.elementFromPoint` 把连线手势延伸进面板 DOM。
- clone 启发：对照 LibTV 引用槽交互；形式新颖但依赖面板 DOM 结构，脆弱。
- 验证门槛：源站无此交互则不引入。

## BF-17 连线接近 3D tilt 反馈

- 源码事实：目标节点按进入方向 rotateX/Y ±10deg；`latchCanvasConnectionApproach` 只在首次进入时记录进入点防每帧抖动（`canvas-connection-tilt.ts:6-18`）。
- clone 启发：视觉语言样本；`reduceMediaEffects` 下会关闭（性能自觉）。
- 验证门槛：源站视觉对照；纯装饰优先级低（DEFER）。

## BF-18 Delete 优先连线

- 源码事实：选中连线时 Delete 只删连线；注释解释「连线点击会为 paint-order 留下节点选中，否则用户刚点的线没删、节点反而没了」（`use-canvas-keyboard.ts:193-207`）。
- 机制拆解：selection 双实体（节点/边）下的删除目标歧义消解规则。
- clone 启发：**候选 ADAPT**——clone 的 RF 场景同样存在 selectedNode/selectedEdge 双态；此规则可直接写进快捷键合同。
- 验证门槛：与 LIBTV_SHORTCUT_RUNTIME_CROSSWALK 对齐，不与源站冲突才吸收。

## BF-19 外置标题头反向缩放

- 源码事实：标题头挂节点上方、`1/scale` 反向缩放保持屏幕尺寸、scale<0.35 隐藏；标题行兼作拖拽热区、图标区承担拖拽、名称按钮保留重命名（`canvas-node.tsx:708-806,726-756`）。
- clone 启发：对照样本——RF 节点内嵌标题会随缩放过小；反向缩放是可选解（RF 下需 `NodeToolbar` 类似机制）。
- 验证门槛：源站节点标题形态对照。

## BF-20 媒体自适应尺寸（manualSize 让位）

- 源码事实：图片解码后回写 naturalWidth/Height，fitNodeSize 夹 [420×236, 720×520]；`freeResize||manualSize` 只补记不动宽高；占位期按比例串保持框（`canvas-node-size.ts:4-77`、`canvas-node-content.tsx:660-683`）。
- 机制拆解：「用户意图优先于系统自适应」用 `manualSize` 显式标记。
- clone 启发：对照样本（LibTV 源站图片节点保持原始比例，AGENTS.md 约束）；若 clone 做自适应，manualSize 让位是必须的配套。
- 验证门槛：源站证据。

## BF-21 实体差异补丁 undo 栈

- 源码事实：`EntityChange{id,before?,after?}` 按 id 对比、存整实体、记 beforeOrder/afterOrder；180ms debounce 合并、上限 50、拖拽暂停、应用期防回环（`pages/canvas/use-canvas-history.ts:7-42,110-248`）。
- 机制拆解：介于全量快照与命令模式之间——补丁体积小于快照、实现简单于 inverse 命令；代价是无 per-command 语义标签。
- clone 启发：对照 clone history 层（LIBTV_GRAPH_TRANSACTION_CATALOG 有事务目录）——「事务语义目录 + 实体补丁」可能是混合最优。
- 验证门槛：clone 若重做 history 层需先过 LIBTV_GRAPH_TRANSACTION_CATALOG 的动作清单。

## BF-22 Agent 整批快照撤销（引用失配清栈）

- 源码事实：Agent 批次 undo 用完整 before 快照（含 viewport/selection）；undo 前校验当前 refs==批次 after，用户编辑过即整栈清空；容量 10（`use-canvas-operation-history.ts:55,232-366`）。
- 机制拆解：Agent 操作成批、语义为「一次委托」，故整批回滚比逐 op inverse 诚实；「被用户接手即失效」避免把用户编辑卷进回滚。
- clone 启发：Director/Agent 化时首选语义（比 TDCanvas 的 applyOps 撤销更保守）。
- 验证门槛：clone Agent 化立项时评审。

## BF-23 storageRevision + tombstone 三方 rebase

- 源码事实：本地存储文档级单调 revision；base/local/durable 三方合并，实体级 tombstone 五级、字段级 durable 胜出、`generationEffectKeys` 取并集、stale 旁观者只保留 viewport（`lib/canvas/canvas-storage-revision.ts:6-16,120-248,310-394`）。
- 机制拆解：多标签页/多写者的乐观并发——读-合并-写循环 + tombstone 防复活；失败不毒化队列。
- clone 启发：对照 `VR-017` 多画布 lifecycle——clone 目前单标签使用，但文档化此协议对未来本地多开/协同是直接参照。
- 验证门槛：clone 落地本地持久化多写场景时评审。

## BF-24 generationEffectKeys 两阶段事务持久化

- 源码事实：普通队列只携带已确认 stamp；生成有专用 durable commit；失败时 `rollbackGenerationValue(previous,attempted,live,durable)` 四态递归回滚；无 stamp 溯源的 connections/activeChatId fail-closed 取 durable（`stores/canvas/use-canvas-store.ts:246-429`、`services/canvas-generation-consumer.ts:447-531`）。
- 机制拆解：把「生成结果落账」做成可对账事务——提交时登记 attempt、持久化时只认已确认 stamp、失败按四态推导回滚目标。
- clone 启发：**高价值**——对照 `VR-015` async result ingress 的「stale/duplicate 收敛」：BeefTV 给出了持久化层面的完整解法。
- 验证门槛：clone 引入真实生成流时按 VR-015 合同评审。

## BF-25 Web Locks 串行化 + 失败不毒化

- 源码事实：scope 级 promise tail 把前序失败转 void；`navigator.locks` 跨标签锁；不支持锁且跨 realm 要求时直接拒绝持久化而非静默降级（`use-canvas-store.ts:140-168`）。
- clone 启发：通用工程纪律（fail-closed 优先于静默丢数据）。
- 验证门槛：clone 引入本地持久化时适用。

## BF-26 CanvasOperation 8 原语统一指令集

- 源码事实：`add_node/update_node/delete_node/delete_connections/connect_nodes/set_viewport/select_nodes/run_generation`；只有 do+label+preview 无 inverse；`verifyCanvasOperations` 后置事实复核（FNV-1a 哈希+postcondition+中文话术+resourceReady）；Agent、workflow builder、短剧流水线共用（`lib/canvas/canvas-operation-contract.ts:8-16,78-204,316-395`、`canvas-workflow-builder.ts:59-161`）。
- 机制拆解：封闭小指令集 + 纯归约器 + 后置复核 = 自动化写画布的可验证底座；「资源物化才算完成」的复核话术直接产出用户可读结果。
- clone 启发：**高价值**——Director/Agent 化的协议形态首选（与 TDCanvas applyOps 结论互证）；verify 思路可进 clone verifier 体系。
- 验证门槛：clone Agent 化立项时按此形态评审。

## BF-27 任务→节点 metadata 绑定 + 轮询对账恢复

- 源码事实：taskId/taskStatus/taskProgress 等全写节点 metadata；「历史 taskId 不是锁，只有活跃任务态/提交才是」；刷新后 listGenerationTasks 对账、孤立 loading 标记中断；跨项目写串用 isCurrentProject 令牌+恢复协调器（`canvas-project-generation.ts:165-211`、`canvas-node-task-state.ts:3-11`、`use-canvas-generation.ts:50-87,384-546`）。
- clone 启发：对照 `VR-007`/`VR-015`；「刷新对账」是 clone 目前缺失的环节。
- 验证门槛：clone 引入真实任务流时评审。

## BF-28 防重复计费四层防线

- 源码事实：节点级提交互斥锁；请求指纹（含全部引用素材哈希）+同指纹二次确认；运行中拦截；clientOperationId 幂等+effectKey 回填幂等（§9.2 所引）。
- 机制拆解：四层分别防「双击/同参数重提交/运行中重入/网络重试重复」。
- clone 启发：**高价值**——对照 `VR-007`；即使 clone 不接真实计费，指纹+互斥的形态适用于任何「昂贵本地操作」。
- 验证门槛：clone 落地真实生成闸门时按 VR-007 评审。

## BF-29 图片批量 root+children 与退休重试

- 源码事实：count>1=root+N 子节点各挂独立任务；首张成功回填 root+primaryImageId；翻新时空占位子删除、有内容的「退休」到 root 左列并解除 batchRootId；取消时无内容子节点删除（`canvas-image-generation-executor.ts:81-272`、`canvas-image-batch-retry.ts:9-179`）。
- clone 启发：对照样本——LibTV 源站是「尝试列」语义（batch158 尝试列移入节点卡），形态不同。
- 验证门槛：源站采样决定是否需要。

## BF-30 媒体版本族（versionOfNodeId/versionLabel/versionPrimary）

- 源码事实：共享 versionOfNodeId 的节点组 + "A".."Z" label + primary 标志；重生成成功自动切 primary；对比 modal「设为主版本」只翻标志不删节点；`prepareInPlaceMediaVersion` 无调用点（未接线）（§8.5 所引）。
- 机制拆解：版本=兄弟节点而非节点内历史——与 TDCanvas 的「节点内 24 条历史+pinned」相对照的两极。
- clone 启发：**候选 ADAPT**——对照 LibTV 生成历史模态（batch101）；兄弟节点式对 RF 更友好（每版本可独立连线引用）。
- 验证门槛：源站语义对照 + Par 编号。

## BF-31 连线=引用顺序唯一源 + @mention composer 双模式

- 源码事实：连线数组顺序即引用编号；@mention 命中→composer 模式（mention 集合取代自动连线输入）；`composerContent` 与 `prompt` 双字段防互相覆盖（§9.6 所引）。
- clone 启发：对照 LibTV AutoLink/引用槽（open-canvas 包 LIBTV_AUTOLINK_STATE_MATRIX）——两套引用语义的第三方案本。
- 验证门槛：源站语义为准。

## BF-32 批量创作表（batch-table 节点）

- 源码事实：1280×560 表格节点；参考列 ≤6 组、行可连线笛卡尔自动生成、并发 10、每行输出节点带 batchSourceNodeId/batchRowId 溯源、确认弹窗带费用提示（`use-canvas-batch-table.ts:28-194`）。
- clone 启发：产品形态对照（LibTV 无此物）；「表格×画布」混合编排的参考。
- 验证门槛：产品立项才评。

## BF-33 上传三层存储与幂等键

- 源码事实：浏览器模式 IndexedDB 即持久层；托管模式后端 canonical（≤50MB multipart/>50MB 分片会话）；直传失败暂存 IndexedDB+pendingRemoteUpload，永久错误当场抛出；客户端预生成 storageKey 作 X-Idempotency-Key（§10.1 所引）。
- 机制拆解：「本地缓存≠已持久化」在类型与 UI 文案上显式区分（`AGENTS.md` §4）。
- clone 启发：对照 `VR-021` media ingress 的 validation/probe/materialization 状态机的真实实现参照。
- 验证门槛：clone 落地资源层时评审。

## BF-34 视频本地处理（ffmpeg.wasm 同源内核 + ISO-BMFF 校验）

- 源码事实：ffmpeg core 同源发布不依赖 CDN；精简构建编译期物理裁剪；trim/merge/裁切/音轨全本地；抽帧用 requestVideoFrameCallback；输出手工解析 ISO-BMFF 防空壳 MP4（§10.3 所引）。
- 机制拆解：重资源按需加载+预热；输出校验防「流程成功但产物不可用」。
- clone 启发：DEFER——clone 无后端且禁止真实生成；若做本地媒体工具此为全套参照。
- 验证门槛：媒体工具立项时评审。

## BF-35 Agent patch 三路合并 + 终态保护

- 源码事实：`{nodes:{before,after}}` 字段级三路合并、冲突抛「需校准、保留本地编辑」、防原型污染；本地已知任务终态绝不被 SSE 旧检查点回退；40ms 批处理+失败节流全量刷新（§11.2 所引）。
- 机制拆解：Agent 写与用户写并发时的合并纪律——字段级冲突宁可中断也不覆盖用户。
- clone 启发：**高价值**——对照 `LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE`（stale/duplicate 收敛）；「终态保护」是异步结果不回退的关键不变量。
- 验证门槛：clone Agent 化时按 VR-015 评审。

## BF-36 Agent 上下文预算（按用户轮省略 + 硬失败）

- 源码事实：历史预算 192KB/48k token、按「用户轮」从最旧省略并插入「上下文整理说明」、声明不得假装记得；live 交换超 384KB/96k 直接硬失败；`data:` 媒体只计数不发送（§11.3 所引）。
- 机制拆解：预算裁剪的诚实性约束（明示省略）优于静默截断。
- clone 启发：Director Agent 化时的上下文治理参照。
- 验证门槛：Agent 化立项时评审。

## BF-37 LibTV 像素捕获夹具三件套

- 源码事实：`libtv-original-*`（1440×900 视口几何/缩略图 URL/连线 path 的像素级捕获）+ `canvas-libtv-fixture.ts` 编译成节点夹具经 `?fixture=` 注入 + `?libtvChrome=1` 只读复刻皮肤；「opt-in and never enters a normal project」（§13.2 所引）。
- 机制拆解：捕获数据→夹具→opt-in 注入→只读皮肤，四件构成跨产品视觉回归闭环。
- clone 启发：与本项目 screenshot/verifier 体系互证；若需「原站某画布的固定几何回归」，此法可复用（捕获原站→夹具→verifier）。
- 验证门槛：仅在获得源站内容使用许可的范围内（本项目已有 CANVAS_TEST_MEDIA 授权边界）。

## BF-38 导入中间表示（ImportResult + importSource 溯源）

- 源码事实：`LibTVImportResult/TapNowImportResult` = 极简节点+连线+导入统计（multiResult/stale/reusedFailed/placeholder/convertedSpecial 计数）+ `metadata.importSource={provider,projectUuid,...}` 全量溯源；两段式「读取→确认导入」、保存失败整批回滚（§13.2/13.3 所引）。
- 机制拆解：跨产品导入=「服务端抓取→中间表示→前端映射→确认→原子应用」；统计计数披露信息丢失（多结果取首个等）。
- clone 启发：若 clone 做「导入 BeefTV/其他画布导出」，此中间表示+统计披露是直接模板。
- 验证门槛：产品需求出现时评审。

## BF-39 显式 LibTV 对齐证据（800% 缩放上限/缩略图/快照推导/LibTV-style 菜单/工具快捷键与视觉基线/默认尺寸基准）

- 源码事实：`web/test/canvas-grid-viewport.test.tsx:93` 测试名「supports the LibTV 800% precision zoom ceiling」（`viewportAtScale` clamp 8）；`web/test/canvas-media-performance.test.ts:66-70`「does not eagerly load or resize LibTV thumbnails」（`if (importedFromLibTV) return;`）；:332-339「derives LibTV snapshots」（`libtv-res.liblib.art` URL 推导 `video%2Fsnapshot` 首帧；`previewContent===content` 判无效）；`web/test/canvas-connection-create-menu.test.ts` 测试名「exposes the LibTV-style compact list layout」（添加菜单 `w-[232px]`/`grid-cols-4`/`--canvas-create-node-height` 按 LibTV 形态钉死）；`canvas-toolbar.tsx:151-152` 注释「Match LibTV's tool shortcuts」（V/H 工具快捷键对齐 LibTV）+ :65 `libtvChrome`「兼容 LibTV 视觉基线」prop + workspace-overlays:250「LibTV reserves only a small gap above the bottom controls」；`constant/canvas.ts:14,26-28` 文本节点 350×350「**作为首屏复刻基准**」+ 音频节点「LibTV renders an empty audio node as a square media card」（默认尺寸层也按 LibTV 复刻）。
- 机制拆解：BeefTV 不仅做 LibTV 导入，还把 LibTV 的缩放手感（800% 上限）与导入物的媒体管道（缩略图不急载、快照首帧）当作用例钉进回归；滚轮钳 0.05–2 与程序化钳 0.05–8 双轨并存。
- clone 启发：**互证**——第三方开源项目对 LibTV 行为的独立采样（800% 上限）可与本项目 `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT` 的源站采样交叉核对；「导入物按来源降级媒体管道」值得记住。
- 验证门槛：仅作对照证据，不驱动 clone 改动；若 clone 做 zoom 合同复核可引此为旁证。

## BF-40 源码文本断言测试（readFileSync + toContain 回归钉）

- 源码事实：`web/test/canvas-media-performance.test.ts:14-21` 等把组件/CSS 源码读进测试，`toContain` 钉死精确实现串（如 `InactiveVideoPreview` 不得含 `<video>`、CSS 变量消费式、aria 文案）；`package.json` `pretest`/`test:canvas` 分级门禁。
- 机制拆解：把「容易无声回退的实现细节」变成可回归的文本合同——比 e2e 便宜、比纯单测覆盖面广（能钉 CSS/aria/字符串文案）；代价是对重构脆弱。
- clone 启发：与本项目静态审计 + verifier 体系互证；「媒体预览不得含 `<video>`」「控制面拦截画布手势」这类不变量值得在 clone verifier 里对应。
- 验证门槛：clone 已有 verifier 体系，引入前先对照 `VERIFICATION_LEDGER` 避免重复。

## BF-41 双插件体系（编译期内置 TS 插件 × 后端声明式协议包）

- 源码事实：前端 6 个内置插件为编译期 TS 模块（副作用 import 注册，`lib/plugins/builtin/index.ts:1-6`），无运行时第三方 JS 加载路径；上传插件只进后端且「只能走声明式路径，宿主绑定保留给随应用发布的 manifest」（`backend/internal/protocol/manifest.go:75-77`）；84 个渠道包是纯声明 JSON（模板表达式驱动，Go 引擎执行）；画布创建插件节点被 `isPluginEffectivelyEnabled` 硬门禁（`canvas-operation-contract.ts:327`）；sandbox renderer 纯占位（`canvas-node-content.tsx:92-97`）。
- 机制拆解：扩展性被拆成「前端编译期 UI 插件 / 后端运行时数据协议」两层，前端永远不执行第三方代码——与 TDCanvas「无沙箱 ESM 直执行」是同一课题的两个极端解。
- clone 启发：若 clone 未来做扩展点，「上传物=纯数据、执行=宿主引擎」的安全姿态是更稳的默认；权限 fail-closed 断言（plugin-host/permission-check）形态可直接借。
- 验证门槛：clone 无插件需求，仅作安全设计参照（对照 tdcanvas 包 REPORT「反面教材」第 1 条：无沙箱直执行）。

## BF-42 本地伴随进程（framefield-local-runtime，loopback + scope 会话）

- 源码事实：独立本地进程 `http://127.0.0.1:17371`（`local-runtime-session.ts:8-24` 强制精确 loopback origin）；模块 canvas-agent/dreamina/portrait-clearance/depth·lineart·pose-estimation，每模块独立 scope（`local-runtime.ts:3,17-25`）；浏览器 CryptoKey 密钥注册 + scope 会话（idb 持久化）；响应体 64KB/32MB 上限、重定向判无效（:29-70）；估计请求三重响应校验（`depth-runtime.ts:31-37`）。
- 机制拆解：重能力（本地推理、敏感登录）外置给带 scope 会话的本地进程，浏览器只做瘦客户端；与「前端内置插件 / Go 后端协议」构成三层能力分布。
- clone 启发：若 clone 需要本地推理/本地 Agent 通道，此「loopback + 密钥注册 + scope + 响应上限」安全形态是现成模板（与 tdcanvas TD-11 的 canvas-agent 通道同构，端口同为 17371——巧合或惯例未考证）。
- 验证门槛：clone 无本地进程需求；Agent 化立项时与云端形态（§11）对比评审。

## BF-43 TransformControls 冻结式手势事务

- 源码事实：gizmo 显式 attach（`<TransformControls object={target}>` 仅 selected&&target 渲染）；拖拽期间 `setFrozen(snapshot)` 冻结声明式 transform prop（`transform = frozen || resolved`），gizmo 直接改 Object3D；终态从**被操控的同一 Object3D** 读回 position/rotation/scale 上抛（`director-viewport.tsx:553-604,638-640`）；手势事务 begin/end 恰好一个终态——pointerup/blur/hidden=commit、Escape/pointercancel=cancel，监听常驻安装（`director-gesture-transaction.ts:26-114`）；骨骼与对象 gizmo 共用同一事务 hook。
- 机制拆解：React 声明式状态与命令式 gizmo 的冲突用手势期「冻结 prop」化解；blur=commit 的语义是「失焦只是离开，用户已把对象拖到那里」。
- clone 启发：**本项目 Director TransformControls 硬约束（显式 attach + 同对象读回）的成熟参照实现**，且多出「冻结声明式 prop」与「终态分型」两块；Batch 77 契约复核时直接对照。
- 验证门槛：改动 clone Director 拖拽路径须跑 Batch 77（AGENTS.md 硬约束）；吸收冻结模式前先复核 clone 现有 commit 路径是否已有等价保护。

## BF-44 本地草稿 + 防抖排空 + revision 确认保存管线

- 源码事实：每次 edit revision+1 并**立即同步**写 localStorage 草稿（scope 键 `director-scene-draft:<id>`）→ 300ms 防抖进排空循环（目标 revision 取最新、未追平刷新 base 继续、追平才删草稿）；冲突靠 `baseUpdatedAt` 基线（草稿基线落后=陈旧残留不弹恢复）；prepareClose 三态 close/offer-draft-exit/stay；localStorage 不可用**显式抛错不降级**（`director-save.ts:129-443`、`director-save-wiring.ts:56-122`）。
- 机制拆解：「先落草稿再异步确认」让关闭/崩溃都有兜底；排空循环合并并发 flush；恢复提示的陈旧判定避免用过期草稿覆盖新内容。
- clone 启发：画布 store 400ms 队列（BF-23/25）在编辑器域的细化版；clone 的画布本地持久化若补「未保存恢复」可直接套此形态。
- 验证门槛：clone 落地本地持久化写路径时按 `VR-017` 评审。

## BF-45 白名单诊断 + 确定性复现夹具矩阵

- 源码事实：诊断仅 11 个白名单稳定码、message 只来自固定常量表（绝不接收 Error/stack/URL/业务文本）、字段白名单化、未知 code 丢弃、1.5s 签名去重（`director-diagnostics.ts:13-151`、recorder:13-37）；`director-repro-fixture.ts` 提供确定性离线场景 + **15 条手工复现矩阵**（每条 steps/expected）+ 注入变体（本地手写 glTF、确定性 404 资源）；repro-runtime 记录脱敏环境快照（WebGL capabilities 用一次性 canvas 探测后归还）。
- 机制拆解：把「缺陷可复现」做成资产——离线确定性场景 + 手工矩阵让手势/保存/加载的边界行为可被逐条人肉回归；诊断只发稳定码让远端日志可信。
- clone 启发：与本项目 verifier/稳定码文化同构；「复现矩阵（steps/expected 清单）」形态可用于 clone 的 Director/画布手势回归台账。
- 验证门槛：吸收前对照 `VERIFICATION_LEDGER` 现有台账形态，避免重复建设。
