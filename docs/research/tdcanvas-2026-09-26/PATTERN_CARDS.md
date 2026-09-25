# TDCanvas 可迁移模式卡

> 每张卡四层：**TD 事实**（源码已核对，file:line 见 SOURCE_ANALYSIS 对应节）、**机制拆解**、**对本项目（LibTV/FrameOS/Jimeng clone）的启发**、**验证门槛**（若未来被授权采纳，clone 侧必须先具备的证据/fixture）。
> TD-01..15 为 TDCanvas 机制卡；**UP-01..06 为上游参考卡**（机制属于上游 `basketikun/infinite-canvas`，精读证据见 [UPSTREAM_DIFF_AUDIT.md](UPSTREAM_DIFF_AUDIT.md) §5/§6，行号对齐上游基准 `dab19ad`）。
> 本文件只描述模式与启发，**不构成实现授权**。

---

## TD-01 手写画布内核：单一 transform 层 + DOM 节点 + 固定 SVG 连线层

- **TD 事实**：无任何画布库依赖；`ViewportTransform {x,y,k}` 施加于单一 div（`td-canvas-surface.tsx:241-248`），节点 transform 定位 + `contain:layout style`；连线为锚在世界原点的 10000×10000 SVG + `overflow-visible` 支持负坐标（`project.tsx:3702`）；视口外扩 280px 裁剪虚拟化（`project.tsx:617-628`）。
- **启发**：React Flow v12 的 viewport/edge 渲染是黑盒时，这套实现给出「等价物」的参考答案——尤其固定尺寸 SVG + overflow 的负坐标连线画法、`contain` 的合成优化、280px 外扩裁剪阈值。
- **验证门槛**：clone 已锁定 React Flow 12.11.1（`VR-016` 权威）；此卡仅作对照研究，不允许混用两套 viewport 体系。

## TD-02 输入语义分歧：wheel=zoom、Space 禁用、ctrl 框选

- **TD 事实**：wheel 恒缩放（pow(1.1,-dy/100)，0.05–5，鼠标锚）；Space+拖拽只 preventDefault（`td-canvas-surface.tsx:69-122`）；ctrl/cmd+拖空白=框选（`project.tsx:1270-1302`）；滑杆缩放以视口中心为锚（`project.tsx:1207-1218`）。
- **启发**：与 LibTV 既有语义（wheel 缩放、Shift+drag marquee、blank-drag no-op、Space 平移）互为反例；证明同一产品类别存在两种合理输入合同。弹层豁免（`[data-canvas-no-zoom]` + antd 弹层清单）与 clone 的 overlay 滚轮劫持问题同构。
- **验证门槛**：clone 输入语义权威是 `docs/CANVAS_NAVIGATION.md` + Batch 77 证据；任何改动需先重取源站证据，TDCanvas 不构成证据。

## TD-03 连线落点几何命中 + 落空白弹创建菜单

- **TD 事实**：`getConnectionDropTarget` 世界坐标距离命中（端口 40/scale、节点 padding 32/scale），优先级 (命中口 0<节点内 1<扩展区 2)*1e5+距离、节点逆序顶层优先（`project.tsx:573-615`）；落空白弹 文本/图片/视频/音频 四项菜单，建节点+反向端口连线+选中+开面板（`project.tsx:547-566`；`canvas-create-menus.tsx:16-43`）。
- **启发**：「拖线到空白→弹菜单建节点并自动连线」是 LibTV 采样中源站具备的交互方向；几何命中算法（屏幕半径/scale、三级优先级）可直接移植到 React Flow 的 `onConnectEnd`。
- **验证门槛**：需源站 fixture（菜单项集合、落点距离、新节点位置规则）+ `GI-004..007` 相关 verifier；不能仅凭 TDCanvas 行为实现。

## TD-04 开放节点注册表（definition 驱动）

- **TD 事实**：`CanvasNodeDefinition` 20 个字段含 ports(可函数)/Content/Panel/toolbar/onDoubleClick/keepAspectRatio/resource/minimapColor/showInCreateMenu（`types/canvas-plugin.ts:107-136`）；注册表带 zustand version 触发重渲（`node-registry.ts:8-15`）；插件节点 type `"<pluginId>:<name>"` 进同一 registry；未注册类型回退 FALLBACK_SPEC + 缺插件占位渲染。
- **启发**：clone 的节点种类（LibTV 11 类 runtime node）目前是硬编码分发；若未来做「搜索画布节点/插件节点」，definition 注册表 + 缺插件占位是完整参考。
- **验证门槛**：与 `LIBTV_NODE_DATA_STATIC_AUDIT` 的 11 类 registry 决策对齐；引入前需 V0→V1 registry 评审。

## TD-05 等分比例 port 锚点 + legacy 回退

- **TD 事实**：第 i 口 `y=(i+1)/(n+1)*height`（`canvas-node-ports.ts:44-54`）与 UI `top` 百分比一致；无 ports 定义回退单输入/单输出 `__legacy-*`（`:6-27`）；兼容 any 通配、`multiple:false` 限一条入边（`:56-85`）。
- **启发**：React Flow Handle 位置自由，但「按序等分」模型保证锚点几何可纯函数推导（无需 measure）——对 clone 的 port 几何合同（`VR-009` 相关）是个简化参照。
- **验证门槛**：clone Handle 是真实连接 affordance（AGENTS.md 硬约束）；锚点策略改动需 `LibTVGraphConnection.contract` fixture 更新。

## TD-06 连线 = 上游引用（数据流语义）+ 双模式互斥

- **TD 事实**：生成输入 = 自身入边 + objectReferences 去重（`canvas-resource-references.ts:85-107`）；上游文本拼接 prompt、媒体进 reference 数组（`canvas-node-generation.ts:38-55`）；`@mention` 序列化为「图片 N」标签、Config composer 用 `@[node:<id>]` token；objects 模式不渲染连线、`addObjectReference` 清空已有连线（`project.tsx:905-923, 3703`）；pinned 版本锁 imageHistory 某一版（`canvas-resource-references.ts:174-190`）。
- **启发**：「连线与对象引用两种模式互斥」「引用可 pinned 到历史版本」与 LibTV AutoLink/引用槽语义直接可比；mention 标签的 `kind+序号` 命名是可复用的序列化格式。
- **验证门槛**：AutoLink 权威是 `LibTVAutoLink.contract.md`（候选/ghost/mention token）；pinned 语义需 source fixture。

## TD-07 生成任务状态机（8 相位 + partial/attention/停止≠取消 + journal 恢复 + 防重复计费）

- **TD 事实**：`providerTask.phase` idle|queued|running|succeeded|partial|failed|attention|stopped（`canvas.ts:42`）；批量 allSettled→partial（`aitudou.ts:178-234`）；Midjourney MODAL→attention；停止轮询仅本地、明示「远端仍计费」（`project.tsx:2196-2214`）；提交即写 journal、刷新合回（`aitudou-task-journal.ts:21-123`）；节点级锁 + `hasUnresolvedAitudouTask` 守卫（`project.tsx:2112-2255, 4192-4196`）；不确定中断三正则判定（`:4185-4190`）。
- **启发**：这是「异步生成结果 ingress」问题最完整的静态样本之一，与 clone `VR-007`（process result state）/`VR-015`（async result ingress convergence）逐相位可比；「提交即持久化任务凭据」解决了刷新丢任务问题；「节点级 unresolved 守卫」是防重复计费的通用形态。
- **验证门槛**：clone 已有 delayed-writer/Director completion 设计；采纳任一子机制需先在 `LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md` 登记 diff 并补 fixture。

## TD-08 批量生成堆叠模型（batch root/child）

- **TD 事实**：count>1 时建 batch root（isBatchRoot/batchChildIds/primaryImageId/imageBatchExpanded）+ N child，root↔source、root→child 连线；空节点原地替换；堆叠帧动效、展开/收起、设主图（`project.tsx:2819-3239, 664-676, 1870-1921`）；批量子图随拖动/删除联动（`:845-870, 1343-1352`）；Aitudou 新管线改为「多输出各建独立节点 + 6 个一列」并防重复建节点（`:4081-4123, 2096-2103`）。
- **启发**：同一产品里并存两种多结果表达（堆叠 vs 兄弟节点阵列），切换点（旧管线 vs 新管线）本身是产品演进样本；对照 LibTV 生成历史/多尝试的节点表达决策。
- **验证门槛**：需 source 端多结果 fixture；与 `SUBGRAPH-COPY`（descendant closure）联动测试。

## TD-09 媒体资源生命周期（双轨制 + 稳定本地地址 + hydrate 恢复链）

- **TD 事实**：IndexedDB Blob（`image:`/`file:` 键）+ 桌面 media-cache（URL SHA-256 去重、SHA-256 内容校验、1GB 限、manifest 原子写、SSRF 防护、mime 白名单）（`media_cache.rs`）；节点只存 `localPath/storageKey/sourceUrl`；加载时恢复链五级（直读→迁移旧缓存→asset://→Web 前缀→重下载）（`canvas-generation-helpers.ts:121-179`）；孤儿回收以「引用反查」删除（`use-asset-store.ts:94-100`）。
- **启发**：与 clone `VR-021`（media ingress resource lifecycle）的 temporary lease/asset/reference/cohort 概念一一对应；「URL 哈希稳定文件名 + manifest 原子写」是桌面/本地优先形态的完整解法。
- **验证门槛**：clone 是纯 Web 原型（blob-data 路径），采纳需先定持久化边界；SSRF 白名单逻辑仅在引入服务端时相关。

## TD-10 项目封面数据推导 + viewport 即文档

- **TD 事实**：封面筛 `sourceOrigin==="generated"`，优先级 imageHistory>outputs>content，取最新 completedAt，注释「用户可能正看旧版本，封面保持最新」（`canvas-home.ts:23-56`）；`CanvasProject.viewport` 字段 + 500ms 防抖保存 + 进入恢复（`project.tsx:448-460, 384`）。
- **启发**：「封面=最新生成物而非截图」与「viewport 存进项目文档」都是多画布 lifecycle（`VR-017`）的细节决策点。
- **验证门槛**：对照 clone Batch 16/58/65 的 per-canvas viewport 存取现状。

## TD-11 Agent 通道：快照上报 + SSE 回传桥接 + 写操作二次确认

- **TD 事实**：loopback HTTP 17371 + 随机 token + Origin 白名单持久化（`http.ts:422-529`）；网页持续 POST 快照，读工具回缓存、写工具 SSE `tool_call`(requestId) 下发、网页执行后 POST result（`session.ts:436-500`）；协议版本握手 hello/protocolVersion=5；写类 `canvas_apply_ops`/`create_attachment_nodes` 强制网页侧批准；Codex 走 app-server stdio JSON-RPC、Claude 走 CLI stream-json，双入口收敛到同一工具集（30 个高级工具编译为 8 种 `CanvasAgentOp` 原语）。
- **启发**：为 FrameOS/LibTV 未来「Agent 操作画布」给出完整协议形态：**回传式桥接**（页面仍是执行主体、agent 只发意图）优于直改 store；8 原语指令集 + 纯函数 `applyOps` + 单次 undo 快照是可移植的最小集。
- **验证门槛**：clone Director 体系已有 authoredObjects 基线；Agent 指令集设计需新合同（不与 Director 命令混淆）。

## TD-12 插件 = 无沙箱 ESM + 宿主能力注入 + 与 Agent 共用 applyOps

- **TD 事实**：Blob URL 动态 import 主线程执行，无沙箱（`plugin-loader.ts:11-23`；SECURITY.md 自认取舍）；PluginRuntime 单例注入 React/injectCSS/事件/storage；`CanvasNodeContext.applyOps` 与 Agent 同指令集（`canvas-plugin.ts:59-60`）；comfyui-local 用 `ctx.applyOps` 完成执行闭环、动态具名端口（`execution.ts:21-136`）。
- **启发**：「插件与 Agent 共享同一画布指令集」是统一扩展面的优雅设计；comfyui-local 的「工作流 JSON → object_info 推导动态端口 → 宏节点」是把外部运行时封装为节点的完整范式（FrameOS 生成节点可参照）。
- **验证门槛**：clone 引入任何插件机制必须否决无沙箱路线（iframe/Worker + 能力白名单）；安全边界写入合同。

## TD-13 全量快照 undo/redo（页面级）

- **TD 事实**：past/future 各 50、180ms 防抖合并、引用相等跳过、拖拽 historyPaused 合并为一条、应用时清空选择、加载清栈（`project.tsx:205, 405-438, 1220-1257`）。
- **启发**：与 clone 的 history 层（portable document/transaction）相比是「最简单可行」端；防抖合并 + 拖拽暂停两个细节任何快照式 history 都需要。
- **验证门槛**：clone history 权威是五层文档模型（`VR-010`）；此卡仅提供细节校准。

## TD-14 屏幕空间氛围网格（视差 + 指针 focus 层 + 密度分档）

- **TD 事实**：网格是屏幕空间 CSS background（不在 transform 层），双层视差 0.78x/0.025x、指针跟随 radial-mask、11s 漂移、按 k 分档密度（`td-canvas-surface.tsx:262-315`；`globals.css:328-413`）。
- **启发**：与 React Flow `<Grid>`（被 transform 的图案）是两种空间感哲学；视差层「不动/慢动」制造深度而不暴露坐标系。
- **验证门槛**：clone 视觉对齐以源站截图为准；此卡为可选项素材。

## TD-15 其他小而美的细节

- **几何式分组**：groupId + 中心点包含判定（pad=24、拖入自动收进、成员联动），无显式成员列表（`canvas-node-geometry.ts:16-47`）。
- **删除的引用清理链**：展开批量子图→停生成→清 objectReferences/groupId/主图重选→删连接→清 13 项悬空 UI 状态→清文件（`project.tsx:841-893`）——与 clone `VR-013` 删除修复矩阵逐项可比。
- **对齐辅助线**：start/center/end 三锚点、7 屏幕像素阈值（除以 scale）、世界坐标覆盖层 1/scale 线宽补偿（`canvas-alignment-guides.ts`）。
- **图片历史签名去重**：FNV-1a `image-version-<base36>`、24 条上限（`canvas-image-history.ts`）。
- **系统剪贴板兜底**：内部剪贴板空时图→图片节点、文→文本节点（`project.tsx:1716-1733`）。
- **防重复计费守卫**与**不确定中断三正则**（TD-07 内）。

---

# 上游参考卡（UP-01..06，`basketikun/infinite-canvas`）

> 这些机制在 TDCanvas 中被继承、弱化或移除（归属判定见 UPSTREAM_DIFF_AUDIT §2/§5/§6）；列出是因为它们对 clone 仍有独立参考价值。

## UP-01 多选浮动工具条与成组操作族（TDCanvas 已移除）

- **上游事实**：`CanvasSelectionToolbar` = 选中包围盒虚线轮廓（SELECTION_PAD=14）+ 两按钮浮动条（Group/Ungroup），`showToolbar` 随拖拽/缩放隐藏（`canvas-selection-toolbar.tsx:11-68`；`project.tsx:3282-3290`）；三入口（工具条/右键/Cmd+G±Shift，`project.tsx:1593-1606, 3325-3326`）；操作族：包裹矩形（顶部留标题 padding）、嵌套组扁平化、空组 GC、解组选中还原（`canvas-node-geometry.ts:58-125`）。
- **启发**：「多选即出浮动操作条」是多选交互的轻量形态；成组操作族的守卫与 GC 细节（≥2 成员、不全属同组、空壳回收）是任何分组功能的必备清单。
- **验证门槛**：需源站多选/成组 fixture；与 clone TD-15 分组（DEFER）同批评估。

## UP-02 canvas-proxy 本地 CORS 转发方法

- **上游事实**：零依赖 Node http 服务（默认 `127.0.0.1:23210`），目标 URL 内嵌路径（decodeURI 还原 + `//` 修复 + `^https?://` 校验），双向头剥离 + 宽松 CORS 注入，SSE 逐块透传与断连 destroy，状态即打日志、失败 502/根路径版本 JSON（`canvas-proxy/index.js:35-132`）；客户端 `buildApiUrl` 全量过代理（`use-config-store.ts:474-496`）。
- **启发**：本地开发态转发代理的**最小完备实现**（对照 clone 未来任何「浏览器直连第三方 API 被 CORS 拦截」的场景）；「身份 JSON 兼作连通性探测」是干净的握手设计（`local-proxy.ts:4-11`）。
- **验证门槛**：仅方法借鉴（ADOPT_METHOD）；引入任何代理需先有 SSRF/白名单合同（对照 TD-09 的 Rust 中继校验）。

## UP-03 Group 资源集合语义（TDCanvas 移除，改 objectReferences）

- **上游事实**：`getGroupResourceNodes` 只取组内有资源的成员（`canvas-resource-references.ts:96-98`）；持有资源的组获得「可引用节点」资格（`:83-89`）；输入解析时组**展平为成员资源**并按 id 去重（`:91-94`）；三级管线 Config 优先（`:53-81`）。
- **启发**：「分组同时是引用打包单位」让用户可以用一个组把若干素材一次性挂到下游——与 clone 引用槽/AutoLink 的批处理语义互补；「资源资格判定集中在一个 `resourceKind` 函数」也值得对照（`TD canvas-node-registry resource()` 是同构设计）。
- **验证门槛**：需源站「组引用」fixture；若 clone 引入，须与 `LibTVGraphConnection`/`LibTVAutoLink` 合同对齐组→引用的展开顺序。

## UP-04 model-plugin BYOK 脚本层（TDCanvas 移除，换固定后端）

- **上游事实**：每能力（image/video/audio/text）用户可编辑 JS 脚本；`new Function` 17 参数注入（prompt/images/.../http/request/poll/sleep/signal/onDelta）+ `"use strict"` 异步包裹（`model-plugin.ts:113-164`）；17 变量能力 scoping 文档（`:166-190`）；模板库 4 能力 × {OpenAI, Gemini}（`:224-975`）；`normalizePluginImages` 归一化（`:977`）。
- **启发**：「以脚本接入任意兼容模型」+「poll/onDelta 把轮询与流式抽象为运行时能力」是 BYOK 形态的完整参照；模板即教学（OpenAI/Gemini 两协议族覆盖常见拓扑）。
- **验证门槛**：**安全反面**——主线程 `new Function`、apiKey 进脚本作用域，无沙箱（同 TD-12 否决理由）；clone 若做 BYOK 必须 iframe/Worker + 能力白名单，且密钥不得裸注入。

## UP-05 prompt-source 开放 JSON 约定（两仓同源继承）

- **上游事实**：`RawPrompt` 18 字段含生成提示 imageMode/imageModel/imageSize/imageCount（`prompt-source-runtime.ts:4-18`）；根必须为数组、`title+prompt` 必填否则丢弃、id 缺省 `${source.id}-序号` 并按 id 去重（`:31-119`）；每源缓存 TTL 1h + 到期刷新（`prompts.ts:139-195`）。
- **启发**：「用户可自建提示词源」的开放数据契约很小（一个 JSON 数组）却能挂接生成参数提示——对照 clone 提示词库的扩展性设计；「签名变化才后台刷新、失败回落旧缓存」的缓存策略（TD 已继承）可直接复用。
- **验证门槛**：clone 引入需先定源信任边界（远程 JSON 渲染/注入面）。

## UP-06 selection/pan 双模式与临时工具反转（TDCanvas 重写为固定手势）

- **上游事实**：surface 声明 `tool: "select"|"pan"`（`infinite-canvas.tsx:11`）；`temporaryTool = ctrl||space` 把当前工具**反转**（`:114-115, 206-207`）——select 态 Space+拖=平移、pan 态 Ctrl+拖=选择；按键状态机带输入守卫与 blur 复位（`:52-74`）。
- **启发**：与 TD-02/TD-12 合并阅读——同一产品类别存在「固定手势」「显式双模式+临时反转」两种输入合同；clone 的 `CANVAS_NAVIGATION.md` 权威属于后者之外的第三种（React Flow 惯例）。
- **验证门槛**：REJECT 移植（同 ADOPTION #12）；仅作输入语义对照研究。
