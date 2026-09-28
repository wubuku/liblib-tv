# BeefTV 源码分析（SOURCE_ANALYSIS）

> 上游：`glanderness/BeefTV`，锁定提交 `85c9686c87a4c176449e29292beba8b96dc430bb`（2026-09-27，tag `v1.5.7`）。
> 本文全部为静态源码阅读证据；行号对齐锁定提交。路径约定：无前缀者相对 `web/src/`；后端/根目录文件给全路径。事实 / 推断分开标注。

## 1. 架构总览与目录边界

- 单元边界（BeefTV `AGENTS.md` §1 表格）：`web/`（工作区 UI、画布交互、浏览器缓存、API 与模型协议）、`backend/`（本地工作区 API、持久化任务、资源、外部模型协议，`cmd/desktop` 与 `cmd/server` 双入口）、`docs/`（Fumadocs 站点）。
- 画布代码四分法（BeefTV `AGENTS.md` §6 明文约定）：组件 `components/canvas/`、状态 `stores/canvas/`、算法 `lib/canvas/`，页面编排 `pages/canvas/`。
- **无画布库依赖**：`web/package.json` 无 reactflow/@xyflow/konva/fabric；`@excalidraw/excalidraw 0.18.1` 仅用于独立绘图编辑器（`components/canvas/canvas-drawing-excalidraw-editor.tsx`），`@react-three/fiber` 仅用于导演台，`@ffmpeg/ffmpeg` 仅用于视频本地处理，`@mediapipe/tasks-vision` 仅用于人脸检测。
- 体量：`pages/canvas + components/canvas + stores/canvas + lib/canvas` 合计 73,483 行（`wc -l`）；最大的页面编排文件 `pages/canvas/project.tsx` 约 214KB；页面下挂 28+ 个 `use-canvas-*` 控制器 hook（connection 53KB、media-tools 70KB、upload 44KB、storyboard 40KB 等）——「页面编排 + 控制器 hook」是其对抗巨型组件的手段（但 project.tsx 本身仍是巨石）。
- 状态分域：`stores/canvas/use-canvas-store.ts`（画布项目文档）、`use-canvas-history-store.ts`（回收站，非 undo）、`use-canvas-theme-store.ts`、`use-canvas-ui-store.ts`、`use-director-workbench-store.ts`；另有 `stores/editor/editor-store.ts`。跨页副作用在 `services/`（task-center、workspace-resource-storage、resource-blob-cache、agent-canvas-sync 等）。

## 2. 画布内核与视口体系

### 2.1 InfiniteCanvas 容器

- `components/canvas/infinite-canvas.tsx`（495 行）是唯一容器内核：props 收 `viewport: ViewportTransform`、`onViewportChange/previewChange`、`boxSelectEnabled`、`graphicsLayer`（Leafer 层插槽）与 children（节点层）。
- DOM 层级：容器 `data-canvas-viewport` → `CanvasGrid`（装饰网格，固定屏幕坐标，注释「避免缩放时改变密度或亚像素位移闪烁」，:466-485）→ `graphicsLayer` → `data-canvas-world-layer`（`.canvas-world-layer`）→ `data-canvas-world-raster-layer`（`.canvas-world-raster-layer`）→ 节点 children（:452-461）。
- 交互期标记：容器 `dataset.canvasViewportInteracting="true"`（:128），CSS 据此降负（§2.2）。
- 浮层排除：`CANVAS_WHEEL_IGNORE_SELECTOR` / `CANVAS_POINTER_IGNORE_SELECTOR` 覆盖 `[data-canvas-no-zoom]`、`[data-canvas-wheel-scroll]`、AntD modal/popover/dropdown/select-picker（:31-32）；注释明确「AntD 浮层通过 Portal 渲染到节点 DOM 之外，不统一排除会被误判为画布空白」（:236-237）。与本项目 overlay 命中问题是同一课题（§12 对照）。
- `interactive=false` 时（版本预览等只读形态）在 layoutEffect 中释放指针捕获、清计时器、复位光标（:73-92）。

### 2.2 三频率双轨视口（live / committed）

- committed 轨：React state；InfiniteCanvas 把 committed viewport 写成容器 inline CSS 变量 `--canvas-live-x/y/scale/inverse-scale/--canvas-committed-scale/--canvas-live-scale-ratio(=1)`（:428-437）。CSS 消费：`.canvas-world-layer { transform: translate(var(--canvas-live-x), var(--canvas-live-y)) scale(var(--canvas-live-scale-ratio)) }`、`.canvas-world-raster-layer { transform: scale(var(--canvas-committed-scale)) }`（`styles/globals.css:11448-11458`；注释说明分层 scale 规避搜狗 Chromium zoom 偏移）。
- live 轨：`scheduleViewportChange`（:122-149）更新 `viewportRef` → rAF 帧里 `applyCanvasLiveViewport`（`lib/canvas/canvas-live-viewport.ts:44-57`）直接改 worldLayer `style.transform = translate3d(x,y,0) scale(k/committedScale)` 并写四个 CSS 变量；preview 事件每 ≥32ms 才广播（:135-137）。滚轮/平移停止后 **120ms debounce** 才 `syncViewport()` 提交 React state（:140-146）。
- 中间频率：交互期间 `handleViewportPreviewChange` 按 **64ms 节流**把 live viewport 写进 React，仅用于刷新虚拟化窗口（`pages/canvas/use-canvas-viewport-controller.ts:179-187` + `lib/canvas/canvas-viewport-render-sync.ts:3-8`）。
- 三条消费者频率：DOM 每帧（live 轨）、React 64ms（虚拟化）、Leafer 每帧（专用无节流 `CANVAS_GRAPHICS_VIEWPORT_PREVIEW_EVENT`）+ AntD 浮层感知的合成 `scroll` 事件（`canvas-live-viewport.ts:58-64`）。
- 非交互期由 `useLayoutEffect` 把 committed viewport 复位回 DOM，带 `interactingRef` 守卫防止交互中被旧 props 覆盖（:94-99）。

### 2.3 输入语义

- wheel（:182-231）：触控板双指/Shift 横滚判为 pan（`looksLikeTrackpadPan` 用 delta 整除性区分鼠标滚轮，:201-202）；鼠标滚轮与 Ctrl/Meta 捏合=以鼠标为锚缩放，`factor = 1.1^(-deltaY/72)`（:218-219），`clampScale` 范围 **0.05–2**（:493-495）。Ctrl/Meta 滚轮在浮层区域也被画布接管（注释：避免浮层触发浏览器页面缩放，:196-197）。
- 指针意图路由：`resolveCanvasPointerIntent`（`lib/canvas/canvas-selection.ts:26-34`）——touch+背景=pan；中键=pan；Space 按住=pan；背景+(框选工具开启 或 Alt/Ctrl/Meta/Shift)=select；其余背景拖=pan。**默认工具是 box-select**（`pages/canvas/project.tsx:362`，`boxSelectEnabled={canvasTool==="box-select"}` :3066），即默认空白左键拖=框选，抓手靠 V/H、Space、中键或触控板——与 React Flow 默认 pan 相反。
- Space：window keydown/keyup 置位 + 抓手光标，输入元素不生效（infinite-canvas.tsx:151-180）。
- touch：单指背景=pan；双指 pinch 以两指中点为锚缩放（pinchState 记录 initialDistance/worldAnchor，:259-281、326-345）；touch 轻点背景（未移动）触发 `onCanvasDeselect`（:381-383）。
- 双击空白=`onCanvasDoubleClick`（打开右键菜单并展开添加节点，§6.4）；drop/dragover 直接挂容器（:444-450）。

### 2.4 外观与主题

- `lib/canvas/canvas-appearance.ts`：`resolveCanvasAppearance/resolveCanvasGridColor`，背景模式 lines/dots/blank（`CanvasBackgroundMode`，`lib/canvas-theme.ts`）；网格 48px、dots 0.34 / lines 0.46 透明度（infinite-canvas.tsx:466-485）。
- 主题 store：`stores/canvas/use-canvas-theme-store.ts`（37 行，`useActiveTheme`）。

## 3. 状态与持久化

### 3.1 CanvasProject 文档模型与 store

- `CanvasProject`（`stores/canvas/use-canvas-store.ts:17-41`）：`id/revision/remoteContentHash/workspaceProjectId/projectId/folderId/title/canvasTitle/createdAt/updatedAt/nodes[]/connections[]/chatSessions[]/activeChatId/starterMode/appearance/backgroundMode/showImageInfo/viewport/directorScenes[]/timeline?`。**文档内嵌一切**（含视口与时间线），工作区项目 1:N 画布靠 `workspaceProjectId`。
- store actions（:51-68）：项目 CRUD + `importProject`（structuredClone 隔离源数据，:552-579）+ `updateProject`（`sameCanvasContent` 去重，内容未变不刷 `updatedAt`，:599-607）。
- 文件夹（`CanvasFolder`）不进 forage 文档，存 scoped localStorage `infinite-canvas:canvas_folders`（:70-84）。
- persist：zustand `persist` 中间件 + 自定义 `PersistStorage`，`partialize` 只存 `projects`（:609-618）；`onRehydrateStorage` 读文件夹并置 `hydrated`。

### 3.2 持久化管线（队列、锁、失败隔离）

- per-user-scope localforage（`localForageStorageForScope(scope)`，:431-445）；`setItem` 时若内存引用未变直接短路（:449）。
- 400ms 防抖队列：`queuedCanvasPersists` 每 scope 一条，token 防乱序（:446-476）；失败仅 console.error，**队列保留给下一次写入或显式 flush**（:470-473 注释）。
- 双重串行化：`withCanvasStorePersistenceLock`（:156-168）= scope 级 promise tail（前一个失败被转成 void，**一次失败不毒化后续保存队列**，:150-155 注释）+ `navigator.locks` 跨标签存储锁（不支持锁的浏览器在跨 realm 要求时直接拒绝持久化而非静默降级，:140-148）。
- 提交流水线 `commitPendingCanvasStorePersistenceLocked`（:188-216）：循环「读 durable → `rebaseCanvasProjects` 三方合并 → 写回 → 更新 observed 快照」；多条排队时把 base 前滚到最新 storageRevision（:207-215）。
- `flushCanvasStorePersistence`（:483-490）供显式冲刷（版本恢复前等）。

### 3.3 generationEffectKeys 两阶段事务持久化

- 生成效果（媒体落节点、会话消息）带 `generationEffectKeys` 戳记（节点 `metadata.generationEffectKeys` / 会话 `generationEffectKeys`）；**普通持久化队列只能携带已确认 stamp**（:463-464 注释），未确认效果在快照层被剔除。
- `ordinaryCanvasProjectSnapshot`（:320-401）：逐节点对比 local 与 durable 的 stamp——本地有新 stamp（未确认）→ 用 `pendingCanvasGenerationAttempts` 里登记的 attempt 做**四态递归回滚** `rollbackGenerationValue(previous, attempted, live, durable)`（:272-308，按字段比较 previous/attempted/live/durable 决定保留 durable、保留 live 或递归合并）；有任何未确认生成实体时 connections/activeChatId 也 fail-closed 取 durable（:390-399 注释：这些记录无 stamp 溯源）。
- `registerCanvasGenerationPersistenceAttempt`（:246-262）：生成提交方登记 `{previousNodes, nodes, previousChatSessions, chatSessions}`，返回注销函数。
- 生成专用 durable commit 在 `services/canvas-generation-consumer.ts`（§9.2）；专用 commit 完成后 `rebasePendingCanvasStorePersistenceAfterGenerationCommitLocked` 用同 scope 最新内存重投影普通队列（:227-235 注释：避免同节点普通编辑被旧 durable 快照替换）。
- 失败对账入口 `reconcileCanvasGenerationFailure`（:423-429）：用 durable 投影内存并 suppress 持久化回写。

### 3.4 storageRevision 与 tombstone 三方 rebase

- `CanvasStorageDocument = { state:{projects}, version, storageRevision, tombstones }`（`lib/canvas/canvas-storage-revision.ts:14-19`）；tombstones 五级 projects/nodes/connections/sessions/messages（:6-12）。`parseCanvasStorageDocument` 宽容解析（旧桌面记录缺 nodes 也可加载，:87-105）。
- `rebaseCanvasProjects`（:372-394）：base（写队列建立时基线）/local（内存）/durable（磁盘现值）三方合并——
  - 实体级 `mergeEntities`（:187-248）：base 有 local 无 → 删除并记 tombstone@nextRevision；local 新增但该 id tombstone 时间戳 > baseRevision → 并发冲突、放弃 local；双方均改 → 字段级合并。
  - 字段级 `mergeValue`（:120-132）：local==base 取 durable；durable==base 取 local；`updatedAt` 恒取 durable；`generationEffectKeys` 取并集；叶子冲突 **durable 胜出**并记录 `concurrent-update` 冲突。
  - project 级（:310-316）：`local.revision !== durable.revision` 且 local 与 base 内容相同（本标签页是 stale 旁观者）→ 只保留 local viewport；否则整分支保留 local，注释「let the server reject its stale revision」。
- revision 是**本地存储文档级**单调计数器（每次 rebase +1，:379,392）；服务器另有 `project.revision`（PUT 响应回写，`services/local-workspace-sync.ts:66-71`），两者不混用。
- `sameCanvasContent`（`lib/canvas/canvas-content.ts:5-16`）排除 viewport/updatedAt/revision/remoteContentHash 四个本地查看/同步状态字段，其余全键 RFC 8785 规范化比较。

### 3.5 本地/后端边界

- `services/local-workspace-sync.ts` 自述为 backward-compatible facade（`hasRemoteUserDataSyncSession()` 恒 false，:34-41 直接 GET 后端）；`remoteContentHash`/`canvasContentHash` 在 v1.5.7 前端已是残留字段（类型存在、被 sameCanvasContent 排除、导入/副本时清空、迁移时删除；`canvasContentHash` 无调用方）。
- 用户切换隔离 React Query、localforage 与资源缓存（BeefTV `AGENTS.md` §4）。

## 4. 节点体系

### 4.1 CanvasNodeData 与 metadata

- 核心类型（`types/canvas.ts:503-514`）：`id/type/title/createdAt/updatedAt/position/width/height/parentId?/metadata?`。
- `CanvasNodeMetadata`（:185-501，约 300 个可选字段）分组：角色语义（`nodeRole:"generator"|"result"`、`resultOrigin`、`generatedFromNodeId`、`importSource`（libtv/tapnow））、内容媒体（`content/previewContent/videoPreview/storageKey/mimeType/bytes/durationMs/hasAudio/naturalWidth/naturalHeight/primaryImageId`）、生成任务（`status:"idle"|"loading"|"success"|"error"`、`taskId/taskStatus/taskProgress/taskStage/taskProvider/taskErrorCode/generationEffectKeys`）、生成参数（`prompt/composerContent/model/size/count/seconds/references/generationMode`）、视频再加工溯源（`videoSegment*/videoTrim*/videoCrop/videoRetake*/audioExtract*/videoMergeSourceNodeIds`）、版本（`versionOfNodeId/versionLabel/versionPrimary/copiedFromNodeId`）、分组（`frame:{collapsed,expandedWidth,expandedHeight}`、`folder:{style,theme,...}`）、扩展节点自有字段（`storyboard/batchTable/mediaConversion/colorGrade/artCritique/panoramaConfig/emotionEdit/drawing*`）。
- 时间戳归并：`stampCanvasNodeChanges`（`lib/canvas/canvas-node-timestamps.ts`）只对「有意义变更」刷 updatedAt，媒体 hydrate 键（content/storageKey/naturalWidth 等）不计入（:8-19,103-123）；createdAt 缺失时按 metadata 兜底链推导（:23-37）。
- 节点↔素材库资产：`lib/canvas/canvas-node-asset.ts:15-92` `canvasNodeToAsset`、:104-150 按 resourceId 复用绑定 assetId。

### 4.2 节点类型与开放注册表

- 内置 18 种 enum（`types/canvas.ts:21-40`）：image/text/drawing/script(分镜脚本)/skill/config/video/audio/frame(背板)/markdown/svg/html/panorama/compare/chart/colorgrade/media-conversion/batch-table(批量创作表)；另有插件类型 `"ai-art-critique"`（`lib/art-critique/contracts.ts:6`）。默认尺寸表在 `constant/canvas.ts:11-34`（如 image 720×405、script 920×360、batch-table 1280×560）。
- 注册表（`lib/canvas/node-registry/`）：模块级 `Map<type, definition>` + owner 表（node-registry.ts:7-9）；`registerNodeDefinitions` 重复/跨 owner 冲突抛错（:15-26）；插件经 `registerPluginCanvasNodes` 注册（:29-31，调用点 `lib/plugins/plugin-registry.ts:68`）。定义单元 `CanvasNodeDefinition`（node-definition.ts:16-60）：label/icon/defaultTitle/defaultSize/minSize/keepAspectRatio/showInCreateMenu/resourceKind/generationMode/showOutputConnection/acceptsInputKind/maxInputCount/inputKind/plugin。
- 缺类型降级：label→「未知节点」（node-registry.ts:64）、minSize→220×160（:12,:80）、内容→`UnknownNodeContent` 占位（canvas-node-content.tsx:89,:292-294）、图标→FileText（canvas-node.tsx:817）。
- 内容分发链（`components/canvas/canvas-node-content.tsx:70-97`）：fileUpload 态 → 自定义内容节点（config/script/batch-table/角色卡等 `renderNodeContent` 注入）→ art-critique → media-conversion → 批次根 → loading → error → 插件 renderer（sandbox 渲染器显示「等待隔离运行时」）→ 内置渲染表 → Unknown。

### 4.3 节点 DOM 结构

- `components/canvas/canvas-node.tsx`（`React.memo` + 自定义逐 prop 比较 `areCanvasNodePropsEqual`，:588-655）。根 div：absolute + translate(position+dragOffset) + 宽高 + `contain:"layout style"`（:340-346），携带约 30 个 `data-*` 观测属性（:306-339，verifier 友好）。
- 垂直结构：**外置标题头** `NodeExternalHeader`（:710-806，挂在节点上方、按 `1/scale` 反向缩放保持屏幕尺寸、scale<0.35 隐藏；标题 button hover 出铅笔→点击进入受控 input，Enter/blur 提交、Esc 取消、空值回滚 :288-296；标题行非按钮区域 mousedown 交给画布拖动 :745-756）→ 节点壳（双击分发：批次根开合/图片看大图/director/绘图/文本编辑，:390-419）→ 内容层（状态徽章 + content + 四个编辑器覆盖层 :421-499）→ 悬浮件（版本徽标/批次徽标/锁定徽标 :501-568）→ 四角 ResizeHandle（偏移 14px、热区 28px，:575-580）→ 左右 `ConnectionSideRail`（:583-584）。
- z 序：CSS elevation 14 档（`styles/globals.css:229-245`，ADR-001）；会话级 paint order `bringCanvasNodeToFront`（`lib/canvas/canvas-node-stack-order.ts:8-12`，**不持久化**，注释 :3-6）；渲染时 frame 先渲染（z0）、其余按 stack order 稳定排序（`pages/canvas/canvas-project-world-layers.tsx:109-112`）。

### 4.4 尺寸体系

- 宽高存节点字段；三条来源：注册表 defaultSize、用户拉伸（minSize + `shouldKeepAspectRatio`，媒体默认锁比例，canvas-node.tsx:213-254）、**媒体自适应**——图片解码后回写 naturalWidth/Height，`fitNodeSize` 夹 [420×236, 720×520]（`lib/canvas/canvas-node-size.ts:4-15`）；判据「用户没手动定过尺寸」，`freeResize||manualSize` 只补记不覆盖（canvas-node-content.tsx:660-683 注释）。
- 占位期按 `metadata.size` 比例串（"16:9" 等）保持占位框（canvas-node-size.ts:17-77）。

### 4.5 frame / folder 分组

- 同一 `frame` 类型节点两种形态，靠 metadata 区分（`lib/canvas/canvas-frame.ts:15-17`）；**成员模型是显式 `parentId`**（`getFrameChildren = nodes.filter(node.parentId===frameId)`，:31-33），几何包含只用于**拖放判定**（找「所有被拖节点中心点都落在其 bounds 内」的 frame，:79-92，空间索引加速 :62-77）。
- frame（背板）：仅收 image/text/drawing/script/video（`canFrameContain` :19-21）；放置后自动扩张包住 children+padding（:113-135）。folder：除 frame 全收（:23-25）；折叠时子节点 ≤3 列网格重排（:138-173）；可关联素材库目录（`folder.assetFolderId`，归档规则更严 :27-29）。
- 折叠：`metadata.frame.collapsed` 隐藏子节点，连线改道到 frame 本身（`resolveFrameConnection` :175-184）。
- UI：`canvas-frame-node.tsx`——展开态 36px 头部 + 折叠 chevron + workflow 徽标（分镜/引用/角色/画风）+ 子节点计数 + 折叠缩略图墙；folder 折叠态替换为封面卡（6 种 style，`canvas-folder-preview.tsx`）。

## 5. 连线体系

### 5.1 数据模型与策略

- `CanvasConnection = { id, fromNodeId, toNodeId, fromHandleId?, toHandleId?, fromAnchorRatio?, toAnchorRatio?, relation?, pathD? }`（`types/canvas.ts:516-534`）；`relation` 枚举 `"storyboard-output"|"storyboard-asset-reference"|"batch-output"`；`pathD` 仅只读 fixture 用。
- 语义是「上游产物成为下游生成的参考输入」：`canvasConnectionError`（`lib/canvas/canvas-connection-policy.ts:12-55`）按节点注册表输入 kind（image/video/audio/text/table_data）匹配、最大输入数、生成模式约束（图片节点禁参考视频/音频、配音只收文本或单角色卡）与模型容量上限（:82-87）。
- 方向归一化 `normalizeConnection`（`lib/canvas/canvas-project-domain.ts:242-253`）：Config-Config 互斥、Config 永远当 target、其余按拖拽方向；同端点重复连线只更新 anchorRatio（`pages/canvas/use-canvas-connection-controller.ts:264-266`）。连到分镜行会同步行绑定与提示词（`attachNodeToStoryboardRow`，canvas-project-domain.ts:255-289）。

### 5.2 锚点几何（反「伪端口」）

- `connectionHandleY`（`components/canvas/canvas-connections.tsx:175-194`）：单端口侧**恒为节点边缘垂直正中**；注释明示曾按鼠标落点比例取 Y 会形成「伪端口」漂移，已废弃。`fromAnchorRatio/toAnchorRatio` 持久化但渲染不消费，仅用于快速创建节点的落点 Y（connection-controller.ts:326）。
- 多端口仅三类句柄：分镜行 `row:<rowId>`（按行索引几何）、`storyboard:context`（底部 composer 中点）、batch-table 参考列（`lib/canvas/canvas-batch-table.ts:47-54`）。
- 端口 UI 是 hover/选中才出现的侧栏轨道 `ConnectionSideRail`（canvas-node.tsx:583-584,:859-949）：80px 圆形热区、视觉「+」圆钮、真实锚点=rail 中心（:910 `onPointerDown(event, 0.5)`）；script/batch-table 无左 rail，script/config 或 `showOutputConnection===false` 无右 rail。

### 5.3 渲染双层

- 层 1 Leafer（常驻）：`canvas-leafer-graphics-layer.tsx` 每线一条 Path，20 字段 signature diff 增量同步（:216-276），描边 `strokeScaleFixed:true`、常态 2px/强调 2.8px/密集只读 1px（:278-288）；拖拽预览路径与批量连线预览也在该层。
- 层 2 SVG（强调）：`canvas-project-world-layers.tsx:129-150` 一个绝对定位 svg，`visualMode="hover-only"` **常态不画、悬停/选中才画**，节点拖动时整体隐藏防残影（:143-145 注释）。强调态分层：blur 光晕（strokeWidth 8 + blur 3px）、底衬+主描边两叠、**两端点圆点而非箭头**（全仓无 arrow/marker，:117-118）、流动虚线与「彗星」流光两动画（2.1s/1.25s 错拍，:120-145）；命中区是 transparent stroke 宽 16 的 path（:73-93）。
- 路径算法：水平方向三次贝塞尔 `canvasConnectionPath`（:150-159），控制点水平外推 `curvature=max(dx*0.5,50)`，方向固定左出右进。
- 连线接近目标的 3D 倾斜反馈：`lib/canvas/canvas-connection-tilt.ts:12-18`（rotateX/Y ±10deg），`latchCanvasConnectionApproach` 只在首次进入目标时记录进入点防每帧抖动（:6-9），应用在 canvas-node.tsx:299。

## 6. 交互控制器

### 6.1 选择与拖拽（`pages/canvas/use-canvas-selection-controller.ts`）

- 点选（:159-224）：仅左键；Alt=减选、Shift/Ctrl/Meta=toggle、普通点击清空后单选；锁定节点只响应 click；拖拽集合自动带 batch 子节点与 frame 子节点；拖拽期间暂停历史记录（:214，`historyPausedRef`）。
- 框选：背景按下建手势（:138-157），策略 `resolveCanvasSelectionStrategy`（canvas-selection.ts:63-68）Alt=subtract/Ctrl=toggle/Shift=add/默认 replace；移动阈值 4/k 世界单位，低于阈值松手=点空白清空选择（:307,:352-361）；命中模式恒 intersect（`resolveCanvasSelectionHitMode` canvas-selection.ts:70-72，contain 分支不可达）；命中查询用空间索引并以不可变数组身份缓存（:41-61）。
- **框选预览完全绕过 React**：`applyCanvasSelectionPreview/applyCanvasNodeSelectionPreview` 直写 DOM 属性/样式（selection-controller.ts:313-326，注释「React only learns that a gesture exists」），pointer-up 才 `setSelectedNodeIds`（:328-333）。
- 节点拖动：rAF 节流（:275-300）；>3px 记 hasMoved；智能对齐容差 7/k、网格吸附 16px、frame 吸附检测 100ms 节流；松手未移动且单选→触发开面板（:269-272）；拖拽位置预览同样 DOM 直写（`applyCanvasNodeDragPreview`，canvas-live-viewport.ts:84-127，querySelectorAll 每会话一次缓存进 WeakMap）。

### 6.2 连线控制器（`pages/canvas/use-canvas-connection-controller.ts`，53KB）

- 拖出：rail `onPointerDown` → `handleConnectStart`（:686-716）记录 pointerId/起点、`setConnecting({nodeId,handleType,handleId,anchorRatio})`；全局 `window.pointermove` + rAF 每帧只处理最新事件（:783-789 注释：防 React/Leafer 抖动）。
- 命中判定 `getConnectionDropTarget`（:458-497）：吸附半径 `CONNECTION_SNAP_RADIUS=56` 是**屏幕像素**、除以 k 得世界半径（:61,:460-461 注释：对齐 LibTV 的 80px 快速添加区）；**圆形区域判定**（`dx*dx+dy*dy<=r*r` :484，注释「不把节点矩形当目标」）；过滤隐藏 batch 子节点/折叠 frame；命中圆区但策略不过 → `isNearNode=true, nodeId=null`（靠近了但不吸附）。
- 松手优先级 `finishConnection`（:607-684）：① source 拖出时 `document.elementFromPoint` 命中提示词面板参考 chip 或参考架就近 chip → `onReplaceReference` **换参考**（:618-667，跨 DOM 区域的重连路径）；② 合法目标 → `connectNodes`；③ isNearNode 非法 → 静默取消；④ 拖到空白 → `setPendingConnectionCreate` 弹「引用该节点生成」快速创建菜单（:678-683）。点 pin（位移 ≤5px）也直接弹菜单不画线（:818-827 `quick:true`）。
- `createConnectedNode`（:274-437）：菜单位置按源节点锚点 Y 排布而非松手点（:319-326 注释）；source 侧创建用 `placeConnectedNodeWithoutOverlap`（水平 96px 间距、冲突逐个下移，:69-104）；创建后自动建线、选中、按类型打开面板；Drawing 仅允许从有图图片的输出线创建（:391-422）；菜单项可用性用虚拟 `__pending-connection-node__` 预校验（:439-456）。
- 批量连线：多选 ≥2 后 Alt+L（`use-canvas-keyboard.ts:140-144`）或从选区 pin 拖出（:540-556）；`planBatchConnections` 规划 valid/partial/invalid（:216-227），commit 汇总跳过数（:229-245）。
- **无既有连线端点拖拽重连**：改接=删旧建新（或走换参考路径）。
- 删除：Delete/Backspace **优先删选中连线**（`use-canvas-keyboard.ts:193-207`，注释：连线点击会为 paint-order 留下节点选中，若不优先会「误删节点而非用户刚点的线」）；或右键菜单（`canvas-context-menu.tsx:290-293`）→ `deleteConnection`（`use-canvas-node-operations.ts:376-386`，删除后 `applyCanvasConnectionPromptSync` 回滚下游提示词）。

### 6.3 键盘（`pages/canvas/use-canvas-keyboard.ts`）

window 捕获阶段监听（:238-239）。全表见 INTERACTION_CATALOG §9；要点：Ctrl/Cmd +/-/0/1/2/3（缩放/100%/适应画布/适应选区）、Ctrl/Cmd+S 保存、Ctrl/Cmd+F 搜索（+Shift 专注模式）、Alt+Shift+F 自动整理、Alt+L 批量连线、? 快捷键中心、Ctrl/Cmd+Z/Shift+Z/Y、Ctrl/Cmd+A/C/V、Delete/Backspace、Esc、V/H 工具；文本编辑目标放行（:97,:131），`[data-canvas-no-zoom]` 控件上只放行 C/V（:132-133）；粘贴系统事件兜底（文本含节点标记→还原节点，:224-236）。

### 6.4 视口控制器（`pages/canvas/use-canvas-viewport-controller.ts`）

- `previewViewport`（:46-50）只写 CSS 变量与 DOM；`commitViewport`（:52-62）删 interacting 标记并 setState。
- fit：`fitCanvasContent`（:109-112）过滤隐藏节点、`fitCanvasSelection`（:114-117，maxScale 1.25）；`lib/canvas/canvas-viewport.ts` `viewportForBounds` padding 96、**maxScale 1（fit 永不放大超 100%）**（:54-71）；`viewportAtScale` 以视口中心为锚 clamp 0.05–8（:73-82）；Agent 生成节点后自动聚焦并计算避开 Agent 面板的最大无遮挡矩形（`unobscuredCanvasArea` :16-28）。
- 动画：`use-canvas-viewport-transition.ts:17-48` 220ms rAF、ease-out cubic（`interpolateViewport` canvas-viewport.ts:84-91）、`prefers-reduced-motion` 直接跳变、新导航指令取消上一段动画；单节点聚焦 scale 夹 0.72/0.78–1.18/1.25（viewport-controller.ts:137-155）；滑杆 `setZoomScale` 带 120ms commit 防抖（:157-164）。

## 7. 渲染性能体系

### 7.1 渲染模型派生管线（`pages/canvas/use-canvas-render-model.ts`）

- 唯一消费点 project.tsx:1899-1927，产出约 40 个派生值（visibleNodes/displayConnections/nodeById/reduceMediaEffects...，:359-397），全部 useMemo。
- `nodeDerivedData` **一次遍历**同时产出折叠 batch 子图、隐藏节点集、frame 子节点、图片节点列表、batch 堆叠位移（:81-137；注释 :78-80 明言避免「把 50k 节点数组走六遍」——50k 是其设计基准）。
- **语义引用稳定化**：拖拽（仅位置变化）时 `semanticNodesRef`+`sameNodeSemanticData` 保持语义节点数组引用不变，使 prompt 引用/资源引用等昂贵派生不重算（:207-213；比较函数 `lib/canvas/canvas-project-domain.ts:402-404`）；空间索引 geometry-unchanged 短路（:161-169）。
- 下游：`CanvasProjectWorldLayers` 整体 memo（canvas-project-world-layers.tsx:103）→ 逐节点 React.memo 逐 prop 浅比较（canvas-node.tsx:588-655）。committed 缩放变化经 `scale` prop 传给所有可见节点（:175），是 commit 时刻集中 re-render 的来源；交互期间不发生。

### 7.2 虚拟化与预算（`lib/canvas/canvas-performance-mode.ts`）

- DOM 预算：`CANVAS_MAX_RENDERED_NODES=720`、`CANVAS_MAX_RENDERED_CONNECTIONS=5000`（:8-9；注释：DOM 预算故意低于连线预算，每张媒体卡都有纹理/合成成本）。
- 缩放分档预算：k<0.14→280、k<0.28→420、否则 720（:40-44）。
- **enter/retain 双边距**：新进入节点须落入 enter 边界（192px，降级 128px）才挂载；已挂载保留到更大 retain 边界（384/640px）防边缘闪烁（:35-38 + use-canvas-render-model.ts:147-158,193-199）；上一帧挂载集合 `renderedNodeIdsRef`；选中与拖拽预览节点强制保留（forcedNodeIds :180-191）。
- 虚拟窗口刷新 64ms 节流（canvas-viewport-render-sync.ts:3-8）。
- 机制是「空间索引查询+预算上限+条件卸载」（直接不渲染），非 visibility/display。

### 7.3 空间索引（`lib/canvas/canvas-spatial-index.ts`）

- 均匀网格哈希，cell 1024 世界单位（:20）；跨格超 256 cell 的大条目进 `largeEntryIndexes` 线性兜底（:21,42-45）；`query(bounds, limit)` AABB 精筛、达 limit 提前返回、**结果按插入序排序保证叠放次序确定性**（:56-107）。
- 三个用途均**只做裁剪不做命中**（命中靠 DOM 事件）：节点视口裁剪（render-model :181-183）、连线裁剪（每线以两端节点包围盒并集建索引，query limit 5000，:272-298；frame 折叠连线重定向 :280-284）、`connectionIdsByNodeId` 反查表支持拖拽时强制显示相关连线（:291-307）。

### 7.4 性能模式三档

- `"auto"|"quality"|"performance"`（`types/canvas.ts:53`），localStorage `canvas-media-performance-mode`（canvas-performance-mode.ts:3,11-26）。auto 判定：节点 ≥80 或媒体节点 ≥32 降效（:28-33）。
- 降效效果（`reduceMediaEffects`）：虚拟化 padding 收紧（192→128、384→640 retain 放宽）、连线层边界 144→96（render-model :139-146）、逐节点关 tilt/滤镜（canvas-project-world-layers.tsx:206、canvas-node.tsx:298）。**不是图片占位**。
- 交互期 CSS 降负：`[data-canvas-viewport-interacting]` 下关 transition/box-shadow/filter/backdrop-filter（globals.css:11407-11419）、关连线动画（:11464-11467）、浮层暂停动画（:11468-11477）。

### 7.5 Leafer 图形层与小地图

- Leafer 层负责连线渲染+交互套件：underlay 场景画连线，overlay 场景画框选矩形/多选包围框/对齐参考线/连线拖拽草稿/批量预览，全部 `hittable:false`（canvas-leafer-graphics-layer.tsx:182-214）。
- viewport 同步=**栅格 rebase + CSS transform 预览**：交互中若缩放比在 [0.85,1.25] 内只对 host div 做 translate3d+scale 合成层预览、不触碰 Leafer 场景树（:419-428；`lib/canvas/canvas-leafer-viewport.ts:7-20` 注释「避免缩放手势逐帧触发矢量重绘」）；超阈值或 commit 才 `syncViewport` + `forceRender`（:99-117,:388-445）；DPR clamp 1–3（:482-484）。
- 小地图（`canvas-mini-map.tsx`）**纯 DOM**：240×160 面板，每可见节点一个绝对定位色块按类型着色（:164-208）；图片缩略图仅当图片节点 ≤24（`MINIMAP_IMAGE_PREVIEW_LIMIT=24` :14）；视口矩形 live 值订阅 preview 事件直写 style 绕过 React（:98-118）；拖地图→`toWorld`→preview/commit 两段（:120-162）；按需挂载（project.tsx:3435 `isMiniMapOpen && !focusMode`）。

### 7.6 媒体预览性能

- 图片：`CachedResourceImage` IntersectionObserver（rootMargin 240px）懒加载 + localforage blob 缓存复用 Object URL（`components/cached-resource-image.tsx:15-100`）；节点内 img lazy/async（canvas-node-content.tsx:688）。
- 视频：静止节点**永不挂 `<video>`**，只渲染静态首帧图（`lib/canvas/canvas-media-preview.ts:4-17`，注释「原始视频 URL 永不返回，宁可用图标占位」）。
- hover 预览（`lib/canvas/canvas-video-hover-preview.ts`）：全局**单解码器租约**（模块级 `stopCurrentPreview` :2）、350ms 延迟、播 3s 自动停、总 deadline 8s（:3-4,42-72）；触发条件苛刻（仅鼠标/无按键/页面可见/非 reduced-motion/容器非 interacting——MutationObserver 监听该属性 :9-23/离屏/wheel/pointerdown/keydown 任一即销毁，且 `removeAttribute("src")+load()` 释放解码器 :17-41,77-81）。
- 主动播放：`preload="metadata"`（canvas-node-content.tsx:476）；`activeMediaNodeId` 保证同一时刻只有一个节点持有播放器（canvas-project-world-layers.tsx:105-108,177）。
- 资源 blob 缓存（`services/resource-blob-cache.ts`）：预算 = `navigator.storage.estimate().quota * 20%`，上限 2GB 下限 64MB、最多 500 条（:27-31,297-307）；并发下载限流 16（:33-34,86-101）；首帧内存 objectURL 同步命中（:42-48）；播放确认后延迟 4s 后台拉全量（:63-84）；接近预算才全量 LRU 扫描、使用中的 objectURL 不淘汰（:254-283）；pagehide 统一撤销（:317-324）。

## 8. 历史与版本

### 8.1 用户级 undo/redo = 实体差异补丁栈

- `pages/canvas/use-canvas-history.ts`：栈元素 `CanvasHistoryPatch` 覆盖 7 面（nodes/connections/chatSessions/activeChatId/appearance/backgroundMode/showImageInfo，:7-15,:34-42）；补丁是**实体级 diff** `{ id, before?, after? }`（存整个实体对象）+ beforeOrder/afterOrder（:17-27,203-248）。
- 提交：编辑 effect 后 180ms debounce 合并、past 上限 50、新提交清空 future（:157-168）；应用期间 `applyingHistoryRef` 防回环，恢复时清空选区/右键菜单（:110-130）；拖拽等指针交互期间 `historyPausedRef` 暂停（selection-controller :214）；项目加载 `resetHistory`（:97-108）。
- 定位：**既非全量快照也非命令模式**，是「按 id 的实体前后像」中间形态；无 per-command 语义标签。

### 8.2 Agent 批次撤销 = 整批 before 快照栈

- `pages/canvas/use-canvas-operation-history.ts`：栈元素 `{ snapshot(完整 before 含 viewport/selection), afterNodes, afterConnections, change{summary,nodeIds} }`（:55,:232），容量 10（:282）；undo 先校验当前 refs 仍等于批次 after——用户继续编辑过则**整栈失效清空**（:246-253,:334-338）；`viewLastAgentChange` 选中并聚焦受影响节点（:357-366）。生成结果到达使 afterNodes 引用失配 → Agent 撤销栈清空，即 Agent 撤销不覆盖生成产物。

### 8.3 CanvasOperation 合同（`lib/canvas/canvas-operation-contract.ts`）

- 8 原语（:8-16）：`add_node / update_node(id+patch) / delete_node(id|ids|nodeType) / delete_connections(id|ids|all) / connect_nodes(幂等去重 :363-370) / set_viewport / select_nodes / run_generation(nodeId+mode+prompt+retry)`。
- 只有 do（纯归约器 `applyCanvasOperations` :316-376）与 label/summary/preview（:238-314），**没有逐操作 inverse/undo/merge**——Agent 撤销靠 §8.2 整批快照。
- 后置事实复核 `verifyCanvasOperations`（:78-204）：对比 before/after FNV-1a 快照哈希（:378-383），逐 op 检查 postcondition（add 计数、字段达标、连线存在、选区、生成 outcome 枚举 `not_started/queued/running/succeeded/failed/cancelled` :416-425 + `resourceReady` :171、节点重叠警告 :206-219），产出中文复核话术（:221-236，如「生成任务已成功，但资源尚未物化到画布，当前不能把它当作可复用素材」）。
- `CanvasSnapshot`（:18-28）：projectId/title/nodes/connections/selectedNodeIds/viewport/revision/stateHash——Agent 感知画布的唯一 read model。
- 明确约定「画布撤销不会取消已提交任务」（:305 批准警告文案）。

### 8.4 项目级版本历史

- UI `pages/canvas/canvas-version-history.tsx`：双 tab「云端历史」（REST `listCanvasHistory`，:70-91，后端 Go `backend/internal/repository/canvas_history.go` 持有）/「本地草稿」（localForage `readCanvasSyncDrafts` :93-112；本地模式只有草稿 tab）；条目元数据 `{ id, revision, nodeCount, connectionCount, reason:"automatic"|"before_restore", contentUpdatedAt }`（`services/api/workspace-data.ts:50-60`）。
- 恢复语义：确认框明示「恢复前会备份当前云端内容…恢复后会生成一个新版本」（:141-146）；先 `persistLocalEdits()` 再 `historyRestoreRef`+重载（`use-canvas-project-lifecycle.ts:384-391`）；实际恢复由后端执行并产生 before_restore 快照。
- 预览：`canvas-version-preview.tsx` 只读整画布渲染快照（节点 id 加 `version-preview:` 前缀、空动作表注入、自适应缩放，:21-126）。
- 本地草稿写入 `preserveCanvasSyncDraft`（`services/canvas-sync-drafts.ts:22-39`）：structuredClone + sameCanvasContent 去重 + 双锁（generation commit lock + canvas persistence lock）。

### 8.5 媒体版本族与回收站

- 版本族=共享 `metadata.versionOfNodeId` 的节点组，各带 `versionLabel`（"A".."Z"，`canvas-layout.ts:253-259`）与 `versionPrimary`；原位重生成成功自动切 primary（`canvas-generation-task-sync.ts:311-320`）；节点左上角版本徽标打开对比 modal，非主版本可「设为主版本」（仅翻标志不删节点，`use-canvas-node-operations.ts:441-447`）。
- `prepareInPlaceMediaVersion`（`canvas-media-versions.ts:29-51`，生成前克隆旧媒体为快照节点）在 v1.5.7 **全仓无调用点**——未接线保留代码（推断：为「版本不丢」预留）。
- 回收站：`stores/canvas/use-canvas-history-store.ts` 是**项目软删除回收站**（最近 200 条含完整项目快照，localForage），`recycle-bin-dialog.tsx` 提供恢复与彻底删除。
- 导出 `lib/canvas/canvas-export.ts`：ZIP（projects.json `{app:"infinite-canvas",version:4,projects:[{project,files,drawingDocuments}]}` + 媒体文件 + 绘图文档；:55-81）；版本历史下载快照时 `includeLocalDrawings:false` 防混入当天笔画（canvas-version-history.tsx:173-174）。

## 9. 生成任务管线

### 9.1 任务生命周期与节点绑定

- 后端任务态 `queued/running/succeeded/failed/cancelled`（`services/api/task-center.ts:371`）；节点 metadata.status `idle/loading/success/error`；批次 item 相位 `waiting→submitting→queued→running→succeeded/failed/cancelled`，batch 相位含 `partial_failed`（`types/canvas.ts:62-64`，推导 `canvas-generation-batch.ts:14-22`）。
- **绑定在节点 metadata**：提交后 `bindGenerationTask` 写 `taskId/clientOperationId/retryOf/attemptGroupId/taskStatus/taskProgress/taskStage/taskProvider...`（`canvas-project-generation.ts:165-186`；入口 `use-canvas-generation.ts:259-280`）；反查用 `task.clientContext.nodeId`（canvas-generation-task-sync.ts:27-29）。
- 进行中判定是纯函数 `isCanvasNodeGenerating`（`canvas-node-task-state.ts:3-11`，注释「历史 taskId 不是锁，只有活跃任务态/提交才是」）。
- 视觉：左上角徽章（loading 脉冲/失败/成功 2s 淡出，canvas-node.tsx:817-853）+ 占位 spinner+阶段文案+已耗时（canvas-node-content.tsx:197-205）+ 图片占位框按请求比例预创建（canvas-image-generation-executor.ts:70-76）。

### 9.2 提交幂等与防重复计费（四层防线）

1. 节点级提交互斥锁 `runCanvasGenerationSubmissionOnce`（`canvas-generation-submission.ts:74-87`，按 nodeId 复用 in-flight Promise，重复点击提示）。
2. 请求指纹+二次确认：`canvasGenerationRequestFingerprint` 对 node/mode/prompt/model/options/workflow/全部引用素材 canonicalize+哈希（:37-72，引用按 storageKey/dataUrl 纳入 :50-57）；同指纹再提交弹「可能再次消耗积分」确认（`use-canvas-generation-executor.ts:84-98,249-250,325-333`）。
3. 运行中拦截：`isCanvasNodeGenerating` 直接拒绝（executor :107-110）；batch 侧「已绑定任务或已有成品的节点绝不重复提交」（`use-canvas-generation-batches.ts:194-195`）。
4. clientOperationId 幂等：`runGenerationOperationOnce` 按其去重**前端并发调用**（`canvas-project-generation.ts:85-100`），id/retryOf/attemptGroupId 随创建 payload 上送（generation-task.ts:314-316）；结果回填 effectKey 幂等（canvas-generation-task-sync.ts:261-309）。**v10 后端勘察修正**：这些字段在后端 Go 代码 **0 命中**——普通任务后端无请求级幂等（inputJSON 原样存储但不消费这些键）；真正的请求级幂等只在 creation 流程（`CreationSubmission.ItemKey`+`Task.CreationSubmissionID` uniqueIndex+事务内重读）与 Cloud Agent（幂等键即任务主键 sha256 前 16 位）存在；后端防「重复产生上游调用」靠「服务端冻结选型 + RouteAttempt 派发 CAS + provider Idempotency-Key + 恢复只读不重建」（详见 §25.2/§25.3）。
- 生成专用 durable commit：`services/canvas-generation-consumer.ts:96-116,447-531` `applyCanvasGenerationTaskNodeEffect` 用 `rebaseCanvasProjects` 把生成效果 rebase 进本地文档并 `recordCanvasStorageDocument`——与 §3.3 戳记体系闭环。

### 9.3 结果回填与失败重试

- 成功：媒体**就地替换目标节点** content 并按结果尺寸居中调几何（locked 节点不动几何，`canvas-generation-task-sync.ts:151-242`）；原位重生成清旧 assetId 防错配（:119-131）；视频对已有视频再生成加入版本族（`canvas-media-generation-executors.ts:40-96`，注释「只有成功结果才能替换当前主版本」）；成功媒体自动同步为项目资产 `ensureCanvasNodeAsset`（use-canvas-generation.ts:282-289,558-578）。
- 文本：空节点就地生成，多余份数右侧兄弟节点阵列+连线（`canvas-text-generation-executor.ts:36-58`）。
- 图片 count>1：root+N 子节点、**每子独立任务**（executor :81-83,182-272）；首张成功子图回填 root content + `primaryImageId`（:216-251）。
- 失败：不清空旧结果（`canvas-generation-layout.ts:47-49`）；失败指纹 `failedPromptFingerprint/failedInputFingerprint` 识别「输入未变的审核类失败」并**阻止自动重试**（`canvas-generation-failure.ts:26-59`；executor :208-211）；提交不确定（524）单独相位与警示图标。
- 重试：`useCanvasGenerationRetry` 从 `generatedFromNodeId` 重建上下文、丢失则用 references 重放、引用丢失直接拒绝（:83-89,176-201,414-416）；`clientOperationId="retry:"+SHA-256(attemptGroupId\0retryOf)`（`canvas-project-generation.ts:150-163`）；重试前 `resetGenerationTaskMetadata` 清旧绑定（:187-211）。
- 刷新恢复：`recoverInterruptedGenerationTasks` 按 taskId 对账 listGenerationTasks(100)——找不到任务→标记 error「页面刷新后找不到对应任务」；孤立 loading→本地中断标记（use-canvas-generation.ts:384-546）；跨项目写串防护 `isCurrentProject` 令牌+恢复协调器（:50-87,502-520）。

### 9.4 批量生成与批量创作表

- generationBatches 队列存源节点 `metadata.generationBatches[]`（上限 20 条，use-canvas-generation-batches.ts:18,82-94）；调度器每 2s：`reconcileBatches` 从节点状态反推 item 状态（**后端成功但媒体未落地不算成功**，:100-154 注释）+ `scheduleWaitingItems` 按 `activeTaskLimit-项目活跃-本地预留` 及 batch.concurrency(1-10) 放行（:156-236,333-346）。
- batch-table（批量创作表）节点：默认操作 try_on（换装）、并发 10、参考图列最多 6 组；行可由连线自动笛卡尔组合（use-canvas-batch-table.ts:28-97）；`generateRows` 为每行创建/复用输出节点（`batchSourceNodeId/batchRowId/batchInputNodeIds`）并 enqueue batch_image（:117-194）。
- 图片批次「翻新」：空占位子节点删除、有内容的子节点「退休」到 root 左侧一列并解除 batchRootId（`canvas-image-batch-retry.ts:9-41`）。

### 9.5 生成布局（`lib/canvas/canvas-generation-layout.ts`）

- 落点判定 `canGenerateMediaInPlace`（:13-25：显式 replace-node / 空内容 / generator 角色 / generated 来源+有提示词）；默认摆位源节点右侧 96px 垂直居中（:86-89）；图片批量子节点 2 列网格（横向 120、间隙 36，:9-11,:51-66）；避让 `findAvailableGenerationGroupPosition` 沿下方/右方迭代取移动更短方向（:68-95）。

### 9.6 上下文引用（连线 + @mention）

- `buildNodeGenerationContext`（`components/canvas/canvas-node-generation.ts:59-137`）：自动输入=入边上游资源节点、上游文本自动拼 prompt（:126-129）；**@mention 命中时切换 composer 模式**只按 mention 集合取素材、不再自动带连线媒体（:84-101）；不可解析 mention 直接报错（:87）。
- **连线数组顺序即引用编号唯一顺序源**（`canvas-resource-references.ts:429-433` 注释）；无入边的资源节点可把自身当 `@图片1`（:383-395）。
- `composerContent`（带 @ 槽位原文）与 `prompt`（生效词）双字段持久化，注释警告不能互相覆盖否则刷新后富引用退化（canvas-generation-submission.ts:28-35）。
- 普通视频模式 promptOnly；声明式工作流（RunningHub/ComfyUI/AutoDL）才把连线媒体当结构化槽位（use-canvas-generation-executor.ts:150-154）。

### 9.7 后端任务同步

- 提交 POST /tasks（payload 含 mode/prompt/config/reference*/metadata，generation-task.ts:300-316）→ `canvas:task-created` 窗口事件（task-center.ts:569-573）。
- **轮询非 SSE**：`subscribeGenerationTasks` 每 taskId 多播订阅，非终态 2s 间隔轮询至终态，连续 5 次查询失败才报错（task-center.ts:247-296,399-445）；每次更新派发 `canvas:task-updated`。
- SSE 仅文本流：`/tasks/:id/text-events`，`after=<sequence>` 游标断点续传（:456-545）。
- 列表游标翻页直至取满（:340-357）；右上角任务浮层 activeOnly、有活跃任务 2s 否则 10s + 窗口事件即时 refetch（use-canvas-active-tasks.ts:15-46）。

## 10. 上传与媒体工具

### 10.1 上传管线

- 入口四类：文件选择器（`use-canvas-upload.ts:347-361,547-569`，目标节点兼容则 replaceNodeMedia）、画布拖放（:571-652：项目章节 JSON → 素材库 assetId → 系统文件；单文件落同类型已有节点矩形内=替换，否则指针处建节点）、上传弹窗（`canvas-upload-modal.tsx:66-96`）、剪贴板粘贴（:483-545）。
- 探测：占位节点即探测——图片 `Image.decode()` 取真实解码尺寸、视频 objectURL+loadedmetadata（15s 超时）（`canvas-file-upload.ts:24-72`）；上传时视频深探测 `captureVideoPoster`（宽高/时长/400px JPEG 封面，串行队列防挤爆解码器，`lib/video-poster.ts:20-112`）；音轨对 MP4/MOV 做 ISO-BMFF `moov/hdlr(soun)` 头解析兜底（video-poster.ts:241-295）。
- **无内容哈希去重**：上传身份客户端预生成 `${prefix}:${userScope}:${nanoid()}` 作 `X-Idempotency-Key`（`services/file-storage.ts:35-36`、`services/api/resources.ts:228-231`，注释「直传和失败后的本地同步必须复用同一上传身份」）；并发防护 `activeUploadsRef`（use-canvas-upload.ts:155-158）。
- 三层存储（`services/workspace-resource-storage.ts:9-15`）：浏览器本地模式 IndexedDB 即持久层；桌面/托管模式后端 canonical（≤50MB multipart、>50MB 8MB 分片会话+合并，失败重开会话重试 2 次，`resources.ts:130-199`）；直传失败且非永久错误→IndexedDB 暂存+`pendingRemoteUpload:true`（`file-storage.ts:118-136`；鉴权/413 等永久错误当场抛出不假装稍后同步，`resources.ts:55-66,205-220`）。上传成功预热读缓存（:102）；原生 `<video>` 无法带桌面令牌，必须认证 fetch 物化成 Blob URL（:156-166）。
- 多文件：串行逐个上传、3 列网格落位（列距 380 行距 300，use-canvas-upload.ts:49-51,363-390）；资产绑定 `ensureCanvasNodeAsset` 回填 assetId（:118-128）；legacy dataURL 先 promote 上传再插节点（:255-272）。

### 10.2 图片工具（`pages/canvas/use-canvas-media-tools.ts`，1123 行）

- 统一模式：工具产出「派生子节点+到源节点连线」，经 `persistMediaNodes`（:155-224）资产绑定+持久化。
- 纯本地 Canvas2D：裁切（归一化 0-1 矩形+8 向手柄，`canvas-node-crop-dialog.tsx:18-119` → `cropDataUrl` canvas-image-data.ts:35-44）；宫格切分（弹窗行列上限 12 但布局校验 `CANVAS_GRID_SPLIT_MAX=5` clamp、预设 2×2~5×5、gap 48 网格排布，`canvas-grid-split.ts:3-49`）；放大（弹窗明示「这不是 AI 超分」、1K/2K/4K 长边、逐倍 step-upscale、硬上限 4096，canvas-image-data.ts:105-159）；标注（brush/矩形/文字+撤销历史，合成 PNG）。
- 调模型：蒙版局部重绘（双层 canvas 手绘蒙版→「白底黑洞」PNG、校验模型 `references.maskSupported`、prompt 强制前缀「只修改蒙版透明区域」、支持 count>1，use-canvas-media-tools.ts:755-914）；视角 angle、布光 lighting、表情 emotion（`canvas-face-detection.ts` MediaPipe worker 找脸→编辑区蒙版→`compositeEmotionImage` 本地回贴）；全景查看节点；反推提示词建文本节点组（:226-255）。

### 10.3 视频工具（ffmpeg.wasm 本地处理）

- 内核懒加载 `@ffmpeg/ffmpeg`+同源发布 `@ffmpeg/core`（注释「核心资产随前端同源发布，避免依赖第三方 CDN」，`canvas-video-merge.ts:11-40`）；精简构建编译期裁掉（`__BEEFTV_HEAVY_MEDIA_ENABLED__` gate，vite.config.ts:14-33 物理删除 mediapipe/tflite/ffmpeg-core 静态资源）；打开 trim/crop 编辑器即预热 `warmFFmpeg`（use-canvas-media-tools.ts:444-459）。
- trim：`-ss` 放 `-i` 后输出侧精确 seek + libx264 veryfast crf20 + aac（注释解释为何不能 stream copy，canvas-video-segment-args.ts:1-5）；原视频保留、子节点带 `videoTrimSource`。
- 音视频分离一次产出两节点：无声视频（整段 `-c:v copy -an`）+ 音轨四级回退 aac copy→libmp3lame→mp3→pcm wav（canvas-video-segment.ts:79-129，适配精简内核缺编码器）。
- 合并：concat demuxer 先 `-c copy` 无损、编码不一致回退转码（canvas-video-merge.ts:51-86）。
- 抽帧不走 ffmpeg：HTMLVideoElement seek + `requestVideoFrameCallback` 确保帧已呈现再 Canvas2D 绘 PNG（canvas-video-frame.ts:73-121）；3 列网格排布避让已有关帧（canvas-video-frame-nodes.ts:19-63）。
- 画面裁切：H.264/yuv420p 偶数对齐归一化（video-crop-geometry.ts:31-44）→ `-vf crop`。
- **输出健全性校验**：`assertUsableSegmentOutput` 手工解析 ISO-BMFF 容器确认 ftyp/mdat/vide/soun 轨且 sample_count>0（canvas-video-segment-args.ts:40-148），防「空壳 MP4」。
- 时间线成片：`lib/timeline/timeline-to-ffmpeg.ts` 纯函数命令规划层；默认后端 ffmpeg 渲染、wasm 离线兜底（editor-export.tsx:1,92,221）。

### 10.4 下载与 H.265

- 文件名纯函数推导（画布名_节点名_日期、MIME/URL 双路嗅探扩展名、Windows 保留名处理，canvas-media-download.ts）；桌面走 Wails `SaveOwnedMedia` 后端落盘、浏览器 file-saver（services/desktop-media-save.ts）。
- H.265 播放靠后端转码副本 `?variant=playback`（resources.ts:302-307）。

## 11. Agent 体系

### 11.1 run 协议与审批

- 云端 Agent（REST+SSE）：`CreateAgentRunInput { conversationId, prompt, canvasId, skillIds, idempotencyKey, permissionMode: "read_only"|"auto"|"request_approval", budget:{maxGenerationTasks,maxVideoSeconds,maxSteps} }`（`services/api/agent.ts:104-119`，read_only 时 budget 强制 0）；run 7 态 `queued/running/waiting_approval/completed/failed/cancelled/rejected`（:67）。
- 服务端工具（展示层清单，非全集）：`canvas_list_node_types / canvas_get_state / task_get / canvas_apply_ops / model_list / generate_media`（+read 类 skills_*，`lib/canvas/agent-tool-presentation.ts:1-29`）+ 项目域 10 个 `project_*`（`services/api/project-agent-tools.ts:16-27`）；另有分镜域（`canvas_read_storyboard/canvas_edit_storyboard/canvas_list_styles/canvas_apply_style`，见 §12.2）与 `canvas_edit_batch_table`（`set_global_prompt`，features.mdx:65，§18）等域工具散布在能力 registry 中（features.mdx:43「节点创建、更新字段、摘要投影和连线限制来自服务端能力 registry」）。
- SSE：`agent_event` + `run_snapshot` 合成快照（**快照只驱动 UI，localSeq 不得当续传游标**，agent.ts:89-90,250-267）；120s 空闲 watchdog + 指数退避重连（:207,:294-301）。
- 审批：`AgentApproval{approvalId, call, callHash?, preview?, decision?}`（:54-62）；决策可附 `mediaSettings`（批准时改参数，:181-183）；预览呈现优先服务端 preview，否则从工具参数重建 fallback——`canvas_apply_ops` 逐 op 生成「新增/修改 N 个节点、建立 M 条引用连线」摘要、节点引用脱敏；`generate_media` 文案「草稿节点和引用连线已创建，尚未提交生成。确认规格后批准才会提交收费任务」（`agent-approval-presentation.ts:78-117`）；面板审批状态机含乐观更新+失败保留待审（canvas-cloud-agent-panel.tsx:602-633）。
- 撤销 `undoAgentCanvasRun` 需 `expectedSnapshotHash`（agent.ts:177-179）。

### 11.2 patch 三路合并与刷新

- `AgentCanvasPatch { canvasId, baseRevision?, revision?, updatedAt, nodes:{before,after}[], connections }`（`lib/canvas/agent-canvas-patch.ts:5-12`）；字段级三路合并（本地未动字段保留、冲突抛「需校准、保留本地编辑」、防原型污染，:29-43）；**生成任务终态保护**：本地订阅者已知终态绝不被 SSE 旧检查点回退成 pending（:67-78）。
- SSE 突发批量应用：40ms 批处理、失败后 ≥1s 节流全量刷新（`services/agent-canvas-sync.ts:5-65`）。
- 画布内容是否变化的判定剔除 viewport/updatedAt（`agent-canvas-snapshot.ts:5-9`，「平移/聚焦不是对 Agent 拥有内容的编辑」）。

### 11.3 上下文预算与计划 UI

- 持久会话历史预算 192KB/48k token 估算，按「用户轮」分组从最旧省略并插入「上下文整理说明」系统消息（声明不得假装记得被省略细节）；live 工具交换不裁剪、超 384KB/96k token 硬失败；`data:` 媒体负载只计数不发送（`agent-context-budget.ts:5-57`）。
- 计划清单取最新一轮 plan（注释记录「钉死在第 1 轮」的实测 bug）、`ask_user` 结构化提问其后出现用户消息即视为已答（`cloud-agent-plan.ts:12-50`）。

## 12. 导演台、分镜与短剧

### 12.1 导演台（Director）

- three.js 3D 摆场/预可视化工作台（`components/canvas/director/canvas-director-workbench.tsx` 942 行）；**每个镜头=一个 Video 画布节点**（`metadata.workflowKind="shot"`，`directorSceneId/directorShotId` 指向项目级 `directorScenes[]` 中的场景，`use-canvas-director.ts:73-99`）。
- `DirectorScene`（`types/director.ts:131-145`）：objects（primitive/model/actor/billboard + transform 关键帧 + 人形骨骼轨道 + 21 种预设姿势）、cameras（焦距/光圈/焦点距离，35mm 换算）、lights、shots（cameraId/duration/fps 24|25|30/景别 6 档/运镜 10 档/prompt/previewNodeId）、activeShotId；默认场景自带 3 灯+默认演员（Xbot.glb）。
- 边界纪律：模式（摆场/姿态/动画/摄影机）是 UI 状态**绝不写入 DirectorScene**（`director-modes.ts:7-9`）；离开动画模式强制停播+关 Auto Key（:56-70）。
- 物化回画布 `applyDirectorOutput`（use-canvas-director.ts:124-218）：beauty 截图上传→创建/复用预览图节点（`workflowKind="reference_set"`）、可选 clay 白膜录屏→视频节点，连线回 shot 节点、退役 depth/normal 引用、`ensureCanvasNodeAsset` 同步资产；上传期间以 store 权威状态复核并发。
- 提示词编译 `compileDirectorPrompt`（`director-prompt-compiler.ts:16-46`）：景别/运镜/相机光学/「演员颜色→角色」映射（按颜色识别身份防换人）/对象坐标姿势/灯光 → 中文视频提示词。
- **与本项目 Director（authoredObjects 基线）架构不同**：BeefTV 是「镜头=节点、场景=项目文档」，本项目是「导演台对象=authoredObjects 便携基线」——仅作对照，不互证。

### 12.2 分镜（Storyboard）

- 分镜=Script 节点 `metadata.storyboard={rows, visibleColumns, referenceNodeIds}`（types/canvas.ts:138-142）；行 21+ 字段（shotNumber/durationSeconds/plotDescription/dialogue/characters/shotSize/emotion/lightingAndAtmosphere/camera/motion/imageGenerationPrompt/videoMotionPrompt/mustHave/continuityOut/negativePrompt/assetBindings/imageNodeId/videoNodeId...，:107-135）；默认行 6s、单表上限 100 行。
- 生成门禁：拆镜前必须有画风节点（`workflowKind="styleboard"` 且 stylePresetId+prompt）且角色卡资产版本齐全，`inspectStoryboardReadiness` 把就绪度/阻塞原因暴露给 Agent（canvas-storyboard-context.ts:19-70）。
- Materializer：每行在 Script 右侧 120px 生成 Image 节点（composerContent=「参考资产 @mention + 提示词」）；连线幂等重建两类语义边 `storyboard-output`（fromHandleId="row:{rowId}"）与 `storyboard-asset-reference`；行 id 回写 imageNodeId/videoNodeId（canvas-storyboard-materializer.ts:7-65, canvas-storyboard-operations.ts 之外 use-canvas-storyboard.ts:262-308）。
- 视频：先首帧后 image_to_video（强校验「所有选中镜头已有首帧」，:490-543）；动作板=12 宫格 action_board；批量提交走 generationBatches（§9.4）。
- 进度推导：images/videos/final 三阶段计数 + 「3/5 · 进行中」标签（canvas-storyboard-progress.ts:32-111）。
- Agent 分镜工具：草稿构建/校验（禁止用正文冒充分镜行）/ops 生成（字段白名单，素材关联与任务状态不可经此改）（canvas-storyboard-operations.ts:7-70）。

### 12.3 workflow builder 与短剧流水线

- `canvas-workflow-builder.ts` 是 **Agent 的 canvas_create_workflow 工具实现**（一次 ops 批量搭流水线），非 UI：节点 kind 9 种（text/script/styleboard/story_input/image/video/audio/character_cards/character_three_view/storyboard_video）、ref 唯一校验、媒体节点必须带 prompt、script 必须带 shots[]→生成 storyboard rows、布局排现有内容右侧 maxX+160、默认链式连线、autoRun 追加 run_generation、identityPrefix 幂等 id（:11-192）。
- 短剧流水线 `createShortDramaPipeline`（canvas-short-drama.ts:25-67）：一键三节点（画风 styleboard/故事梗概 story_input/分镜脚本 storyboard 空行）+ storyboard:context 连线；五步进度推导要求画风/故事**真实连线到分镜脚本**才算完成（:91-92）；空画布才可建，建后 fitView+打开画风选择器（use-canvas-short-drama.ts:37-51）。
- 空态取舍注释（canvas-starter.ts:19-21）：「LibTV 的画布默认直接进入自由节点状态；短剧引导保留为显式选择后的入口」——BeefTV 自己也在对标 LibTV 的空态决策。

## 13. 工作区项目模型与跨产品导入

### 13.1 workspace project 1:N

- `CanvasWorkspaceProjectRecord`（canvas-workspace-project.ts:1-6）；画布经 `workspaceProjectId` 归属；**legacy 无主画布以自身 id 当项目 id** 防历史画布折叠成一团（:9-15）；跨画布收集媒体选封面/选项目展开全部画布（:46-63）。
- 生命周期（use-canvas-project-lifecycle.ts）：新建画布继承 workspaceProjectId（:311-325）、删除跳兄弟画布或列表+清理本地绘图缓存（:327-346）、打开=本地缓存秒开+后台拉最新（:178-208）、viewport 500ms 防抖保存（:292-303）、Agent 服务端变更三路合并不覆盖本地拖拽（:258-277）。

### 13.2 LibTV 导入与像素捕获夹具（与本项目直接相关）

- 导入对象是 LibTV 在线画布的 **32 位 UUID 或链接**（`libtv-import.ts:1-17` 正则 `^[a-f0-9]{32}$`）；抓取/解析在**服务端** `POST /canvas-projects/:id/import/libtv {uuid}`（`services/api/libtv.ts:55-57`），该路由是 hosted-only（`backend/internal/handler/api_test.go:105-108` 列为 desktop 不得暴露；本仓库不含实现，资源域名 `libtv-res.liblib.art`）。
- 返回中间表示 `LibTVImportResult`（libtv.ts:36-53）：仅 image/video 两类节点（x/y/w/h、content、prompt、model、naturalWidth/Height、durationMs、status、metadata `{provider:"libtv", projectUuid, nodeKey, batchId, sourceType...}`）+ connections + 导入统计（multiResultNodeCount/staleNodeCount/reusedFailedNodeCount/placeholderNodeCount/convertedSpecialCount）。
- 前端映射（`pages/canvas/components/libtv-import-dialog.tsx:18-46`）：保留相对位置整体平移到当前视口中心；视频 content 用原始 mp4 URL（剥 OSS 变换参数，`libtv-import.ts:52-66`，注释「旧版导入曾把快照图写进 content」）、preview 加 `image/resize,w_960`、视频加首帧快照 w_400；两步交互「读取画布→确认导入」、保存失败整批回滚（project.tsx:814-831）。
- `libtv-original-*`（layout/media/special-nodes/edges）+ `libtv-current-*`：对一个公开 LibTV 画布（「BLUE NIGHT蓝色奇妙夜」）的**像素级捕获数据**（1440×900、10% 相机视口几何、真实缩略图 URL、连线端点与 SVG path）；`canvas-libtv-fixture.ts` 编译成画布节点夹具，仅经 `?fixture=` 查询参数注入（project.tsx:539-682，「opt-in and never enters a normal project」:63-69）；`?libtvChrome=1` 品牌化顶栏 + `?fixture=libtv-readonly-dense` 只读复刻条（canvas-project-top-bar.tsx:101-157）。
- **判断**：BeefTV 把 LibTV 当对标对象做了导入+复刻审计；其「捕获数据+夹具注入+只读皮肤」三件套与本项目 `docs/research/liblib-*` 采样/verifier 体系互证（推断）。

### 13.3 TapNow 导入

- 同构协议另一源：`app.tapnow.media/tapflow/view/:shareId` 分享链接（`tapnow-import.ts:4-18`）；Result 结构同 LibTV（nodes 多支持 audio|text）；`POST /canvas-projects/:id/import/tapnow`（services/api/tapnow.ts:7-55）；两对话框并列挂载（project.tsx:3028-3029）。

## 14. 后端画布持久化与版本历史（Go，v2 补充）

- 数据表（`docs/content/docs/backend/backend-database.mdx:34-46` + `backend/internal/repository/canvas_history.go`）：
  - `canvas_projects`：当前画布内容 + 递增 `revision`（非空默认 1）；**客户端新建传 0，后续写入按 (用户, ID, 原版本) 原子校验 CAS，成功才 +1**（database.mdx:38）。
  - `canvas_snapshots`：结构 JSON、revision、标题、节点/连线数、字节数、内容时间、备份时间；`(canvas_id, revision)` 唯一；**列表只读摘要列**（`canvasSnapshotSummaryColumns`，canvas_history.go:16,24-29），正文按需加载；**不复制媒体文件**（database.mdx:39）。
  - `canvas_snapshot_resources`：历史快照引用的资源，`(snapshot_id, resource_id)` 联合主键；资源外键禁止删除被引用记录（database.mdx:40；`CanvasHistoryReferencesObject` 还按 endpoint/bucket/object_key 匹配**同物理对象别名**，canvas_history.go:117-124）。
- 保存事务 `SaveCanvasWithSnapshot`（canvas_history.go:39-95）：单事务内完成「Upsert 内容 → 决定是否采样快照 → 引用保护 → 保留清理」。**采样判定**（:48-53）：无历史快照必采；否则 `revision 前进 且 (force 或 上一份快照早于 cutoff)` 才采——cutoff 即「普通备份最短间隔 5 分钟、每画布最多保留 20 份、恢复前强制备份（force）」（database.mdx:42-44）。**revision 与快照非一一对应**（快照按间隔采样，database.mdx:42）。
- 引用保护（:54-69）：快照引用的 resourceIDs（含恢复时 rebind 的 restoredResourceIDs）必须全部处于 `ready`，缺一个即 `ErrCanvasHistoryResourceMissing` 整体回滚。
- 保留清理（:85-89）：按 revision 倒序 offset(limit) 之后最多 100 条列入过期，连同 `canvas_snapshot_resources` 级联删除（:126-134）。
- 「素材+画布」联合发布 `SaveAssetsAndCanvasWithSnapshot`（:97-115）：素材 Upsert 与画布保存同一事务，注释「失败的画布 CAS 不能让应用相信只发布了一半」。
- 资源删除保护：`RequireNoCanvasHistoryReferences`（:148-165）——仍被历史快照引用的媒体延后回收；删除画布时清理该画布快照及引用（database.mdx:44）。
- 恢复语义（database.mdx:44）：**保留当前画布 ID、归属和项目关联，按当前版本 CAS 后形成新版本，不把 revision 改回历史值**——与前端 §8.4 的「恢复后生成一个新版本」闭环。
- 陈旧写拒绝：**旧客户端缺少 revision 的保存返回 428**；「画布关联项目或解除关联同样推进版本，使旧页面的全量保存失效」（database.mdx:42-46）。
- schema 演进：结构版本 23 = `canvas_revision_history`（为既有画布回填 `revision=1` 并新增历史快照与资源引用表，database.mdx:26）；版本 13 `cloud_agent_canvas_mutation` 持久化 Agent 画布变更；版本 10 `creation_runtime` 为任务增加可空唯一 `creation_submission_id`（对应前端 clientOperationId 链路，§9.2）。
- 架构立场（database.mdx:99,104）：`creation_runs` 保存「创作 Agent 的服务端权威状态、执行租约、已批准提案和画布快照」，「客户端会话只作为输入」；**「自由画布可以承载探索节点，但画布 metadata 不作为生产完成度、镜头版本或交付可用性的真相源」**——与本项目「Director authoredObjects 为便携基线、objects 为 runtime 投影」的分层立场同构（推断，对照 AGENTS.md 硬约束）。
- 素材-资源所有权（database.mdx:203-207）：前端先提交素材、再提交带 `assetId` 的画布节点；后端保存画布前校验资源属于当前用户、状态 ready、素材存在且引用同一资源；素材删除反向检查画布引用；账号容量按 (Provider,Endpoint,Bucket,ObjectKey) 物理对象去重；>24h 无引用的 ready 资源经幂等 Worker 物理回收。

## 15. 上游回归断言清单（web/test）与 LibTV 对齐证据（v2 补充）

- 测试形态：混合两类——**纯函数行为测试**（空间索引/虚拟化节流/媒体激活）与**源码文本断言测试**（`readFileSync` 读组件/CSS 源码后 `toContain` 精确字符串），后者把「关键实现细节」钉进预提交门禁（package.json `pretest` 跑 local-* 边界 + canvas-grid-viewport；`test:canvas` 跑 media-performance/title-interaction/spatial-index）。与本项目的静态审计 + verifier 纪律同构（推断）。
- **LibTV 对齐证据（测试名直接命名）**：
  - `web/test/canvas-grid-viewport.test.tsx:93-97`：**「supports the LibTV 800% precision zoom ceiling」**——`viewportAtScale` clamp 到 8 即 LibTV 源站 800% 缩放上限（注意双轨钳制：滚轮 `clampScale` 0.05–2（infinite-canvas.tsx:493-495），程序化缩放 0.05–8（canvas-viewport.ts:73-82））。
  - `web/test/canvas-media-performance.test.ts:66-70`：「does not eagerly load or resize LibTV thumbnails」——`if (importedFromLibTV) return;` 导入的 LibTV 节点不参与急加载/尺寸回写。
  - `canvas-media-performance.test.ts:332-339`：「derives LibTV snapshots」——`libtv-res.liblib.art` 视频URL 推导 `video%2Fsnapshot` 首帧快照；`previewContent===content` 时视为无效（宁空不回退到原视频 URL）。
- 双轨视口的回归钉（canvas-grid-viewport.test.tsx:51-91）：`applyCanvasLiveViewport` 精确断言 `translate3d(x,y,0) scale(k/committedScale)`、四个 CSS 变量写入、**交互期 graphics 事件每帧而 preview 事件为空**、结束后 willChange 清空 + preview + 合成 scroll 各一次、**网格层零写入**（屏幕坐标固定背景是断言目标，:31-49 含 7 组 viewport × 明暗双主题矩阵）。
- 空间索引回归钉（canvas-spatial-index.test.ts）：**50k 节点夹具**（35000 image/14000 video/1000 text，:69-79）查询上界 720；跨格大条目不进桶循环；边界相触不算相交；插入序保序。
- 性能模式回归钉（canvas-media-performance.test.ts:52-64）：`shouldRefreshCanvasVirtualization` 64ms 节流与「未移动不刷新」；enter/retain padding 精确值 128/640。
- 媒体激活与播放回归钉（:27-97）：`resolveActiveCanvasMediaNodeId` 单激活；`InactiveVideoPreview` **不得包含 `<video>` 元素**（静态首帧+播放按钮）；`scheduleResourceBlobCache` 在播放请求时触发；首帧失败可重试。
- 音频节点回归钉（:99-118）：自绘轻量播放器、**禁用原生 `<audio>`**、控制面用 `stopCanvasEvent` 隔离画布手势（pointerdown/mousedown/wheel 全拦截）。
- 视频控制面回归钉（:120-262）：Vidstack（`vds-` 类名）compact 变体的 CSS 合同逐条钉死（音量弹层几何/安全区/控件显隐）；`hasAudio` 推导链（audioTracks/webkitAudioDecodedByteCount/captureStream + ISO-BMFF hdlr 兜底 + 远端 Range 探测，:200-257）——「未解码字节计数不得当作静音证据」「运行时阳性探测可纠正过期静音元数据」两条语义被测试钉死。
- 标题交互回归钉（canvas-node-title-interaction.test.ts）：iframe 仅在 `data-canvas-node-dragging="true"` 时 `pointer-events:none`；拖拽把手 aria 文案「拖动此处移动节点；点击名称可重命名」（即 §4.3 的「图标区拖拽/名称按钮重命名」分工）；只读与锁定节点不接把手。
- @mention 菜单被动预览（canvas-media-performance.test.ts:296-303）：引用菜单视频用 `muted playsInline preload="metadata"` + `currentTime=0.001` 去首帧，不用图标占位。

## 16. 插件运行时与双插件体系（v3 补充）

- **双体系并行**：①前端 6 个编译期内置 TS 插件（`lib/plugins/builtin/`：eagle 素材源、prompt-optimizer、workflows(RunningHub)、ai-art-critique、media-conversion、editor-shell 编辑工作台，`builtin/index.ts:1-6` 副作用 import 注册）；②后端 84 个纯声明式协议包（`plugin-packages/*/manifest.json`，`apiVersion:"beeftv.plugin/v2"`，用 `$ref/$merge/$coalesce/$omitEmpty/$map` 模板表达式声明请求构造与响应路径提取，零可执行代码；由 Go `backend/internal/protocol/manifest.go` 引擎执行，经 `GET /plugins/catalog` 注入前端模型渠道目录，`services/api/plugin-catalog.ts:28-68`）。前端 import 图与 plugin-packages **零交集**。
- manifest 形态（`lib/plugins/plugin-types.ts`）：v1/v2 双版本（:3-4），v2 超集新增 `editorSlots` 与 `timeline.*` 权限（:21,28-32）；`permissions/trusted/configuration.fields/runtime/contributes`（:137-154）；`entry` 字段声明后**从未被读取**（遗留）。`PluginRuntime="declarative"|"sandbox"|"worker"|"trusted-backend"` 四值中前端只消费前两个（且仅作画布节点 renderer 字段），`worker` 无引用（:38）。
- 加载与注册：全部编译期静态导入，无运行时第三方 JS 加载路径（上传插件只进后端，`services/api/plugins.ts:45-50`）；`registerPlugin` 校验 kebab-case/apiVersion/权限去重/至少一种贡献（`plugin-registry.ts:18-50`）；节点贡献链 `registerPluginCanvasNodes`（:67-69）→ `canvasNodeDefinitionFromPlugin`（`node-registry/node-definition.ts:62-77`，`defaultMetadata={pluginId,pluginNodeId,pluginData:{}}`）；创建菜单命令**不单独注册**，从节点注册表过滤 `definition.plugin` 生成并按 `enabledPluginIds` 门禁（`tool-registry.ts:52-68,118-120`、`use-canvas-create-commands.ts:7-11`）。
- 启停传播：权威判定 `isPluginEffectivelyEnabled`（`use-plugin-store.ts:72-79`，服务端 effectiveEnabled → runtimeStatuses → fallback → 本地 installation）；服务器模式 `PUT /plugins/:id/activation`（`plugins.ts:52-55`）；**画布硬门禁**：`canvas-operation-contract.ts:327` 创建插件节点时未启用直接抛错、:336 盖 `pluginId/pluginNodeId` 戳；`canvas-context-discovery.ts:158` 对既有节点同样校验。
- **sandbox renderer 是纯占位**：`canvas-node-content.tsx:92-97` 渲染「插件节点等待隔离运行时」占位 div，无任何 worker/iframe/动态加载实现；`declarative` 分支也只是 schema 驱动的只读字段列表（:98-105）。真实有自定义 UI 的「插件节点」全是宿主内置特判组件（art-critique/media-conversion，:80-81）。
- 安全模型：**无第三方代码在前端执行**（因此无需沙箱）；权限是声明式+fail-closed 校验——宿主服务上下文 `createPluginHostContext`（`services/plugin-host.ts:6-35`，`ai.text` 权限断言、localForage 按 `infinite-canvas:plugin-storage:<id>:` 前缀隔离）、编辑器插槽权限表+未注册即拒渲染（`plugin-permission-check.ts:10-63`）；后端 `manifest.go:75-77` 明文「上传插件只能走声明式路径，宿主绑定保留给随应用发布的 manifest」。iframe 沙箱存在于画布 HTML/SVG **节点**（`sandboxed-frame.tsx:23-36`，只给 `allow-scripts` 不给 `allow-same-origin`，因此放弃 DOMPurify）——与插件体系无关。
- 与 tdcanvas 包对照：TDCanvas 是「无沙箱 ESM 主页面直执行」（见 tdcanvas 包 REPORT「反面教材」第 1 条）；BeefTV 是「前端零第三方执行 + 上传物纯数据声明」——同一扩展性课题的两个极端解。

## 17. framefield-local-runtime 本地伴随进程（v3 补充）

- 独立本地进程，默认 **`http://127.0.0.1:17371`**（`services/local-runtime-session.ts:8` `resolveLocalRuntimeEndpoint`——强制精确 loopback origin：http、127.0.0.1、非空端口、无路径/凭据/查询，`VITE_FRAMEFIELD_LOCAL_RUNTIME_ENDPOINT` 可覆盖但校验同样严格，:10-24）。
- 模块清单（`services/local-runtime.ts:3`）：`canvas-agent`、`dreamina`（即梦）、`portrait-clearance`（人像合规）、`depth-estimation`/`lineart-estimation`/`pose-estimation`；每模块独立 scope 集（:17-25，如 `depth:status/depth:run`、`dreamina:generate`）。
- 会话安全（`local-runtime-session.ts`）：浏览器生成 CryptoKey 密钥对、公钥注册、按 scope 授权的会话（sessionId/keyId/scopes/expiresAt，idb 持久化，:32-46 附近）；status 响应体 **64KB 上限**（`local-runtime.ts:7` `MAX_RESPONSE_BYTES` + 流式累计截断 `readBoundedJson` :47-70）；重定向/opaque-redirect 一律判无效响应（:29-33）。
- 估计模块（`depth-runtime.ts`）：图片转 dataUrl（≤12MB，`MAX_IMAGE_BYTES` :4）→ `POST /depth-estimation/run` → 响应校验 `ok/module/apiVersion` 三重（:31-37）；结果含 `device:"cpu"`、`modelCached/loaded` 状态（模型由本地 runtime 自管缓存）；响应上限 32MB（:5）。pose/lineart 同构（pose-runtime.ts 213 行）。
- 画布接入点：media-conversion 节点的本地图片操作与「深度/线稿/姿态 estimation services」（§附 C，`media-conversion-node.tsx:20-22` imports）、canvas-agent 模块（Agent 本地通道，与云端 Agent 并存）。
- **观察（推断，仅记录不结论）**：TDCanvas 的 canvas-agent 同样使用 loopback 17371 端口（见 tdcanvas 包 SOURCE_ANALYSIS 5.4 节）；两产品在「本地伴随进程 + loopback HTTP + token/会话握手」形态上同构，端口重合是巧合还是共同惯例未考证，不影响本文任何结论。
- 定性：这是 BeefTV 的「重能力外置」通道——浏览器内不做本地推理/敏感登录，全部委托给带 scope 会话的本地进程；与「84 个声明式渠道包走 Go 后端、6 个内置插件走前端」共同构成三层能力分布（前端内置 / Go 后端 / 本地伴随进程）。

## 18. 产品功能清单对照（features.mdx，v4 补充）

> 基准：`docs/content/docs/overview/features.mdx`（359 行，锁定 `85c9686`）。方法：产品文档逐节对照已采源码证据，标注「一致（证据复核）」「新增细节」「超出画布范围」。产品文档自述「真实模型计费与浏览器联调仍待验收」（features.mdx:43 末）——上游自己的诚实状态标记。

### 18.1 与已采证据一致（交叉复核通过）

| 产品功能（features.mdx 节） | 对照结论 | 已采证据 |
|---|---|---|
| 画布保存保护与版本记录（:47-55） | 全部一致：平移/缩放/打开不触发整份保存；冲突停止自动提交保留草稿；快照最短间隔 5 分钟、每画布 20 份、版本号与快照非一一对应；历史只存结构+媒体引用不复制视频；本地绘图笔画不入云端历史；**明示「不提供多人实时协同或自动合并」** | §3.4/§8.4/§14（database.mdx:42-46 与文档逐条吻合） |
| 画布抓手与框选（:71-83） | 一致：默认区域选择、抓手工具切换、Space/中键临时平移不改工具 | §2.3/§6.1/BF-12 |
| 视频悬停预览（:106） | 一致：350ms 延迟、静音预览 3 秒不循环、全局单解码器、离开/操作即停、减弱动态不自动预览 | §7.6/BF-09（数值逐项吻合） |
| 宫格切分（:86,91） | 一致：4/9/16/25 预设 + 5×5 自定义点选，子图按网格排开 | §10.2（`CANVAS_GRID_SPLIT_MAX=5` 与「5×5 自定义」吻合；「弹窗输入上限 12」是 UI 细节） |
| 章节资产提取（:108） | 一致（新增边界细节）：输出必须三类数组齐全、无人章节只产生场景/道具不算失败 | §10.2 表情/反推之外的新边界（canvas-storyboard 域） |
| 画布外观（:280-296） | 一致并扩展：三主题（浅/深/自定义）×三网格；自定义可调背景色/OKLCH 明亮度/网格色/强度 0-100%；可应用到当前画布或存为浏览器账号默认 | §2.4（`canvas-appearance.ts` 归一化 + `readCanvasAppearanceDefault`，use-canvas-store.ts:501,514-515） |
| 自动整理（:298-313） | 一致并精确化：≥2 选中只整理选中；有连线→横向拓扑+文本/图/视/音泳道，无连线→按媒体类型分网格；锁定/容器/折叠批次子节点不动；进历史可撤销 | §4.5（`canvas-layout.ts:13-142` 逐条对应；右键「自适应整理」= `spreadCanvasNodes` 加边距，「不是重排宫格」features.mdx:75） |

### 18.2 新增细节（v4 前未覆盖）

1. **画布智能引用（AutoLink）**（features.mdx:57-61）：节点提示词面板「智能引用」入口 = AutoLink 开关 + 「一键引用全文」批量转换；候选匹配仅覆盖**当前已连接且激活**的画布素材，跳过技能、素材库条目、重名歧义与已有引用；支持 `图1/图片1/image1/image 1` 及独立序号，普通数字文本（「约2秒」）不误判；AutoLink 默认开启、开关为面板临时状态。——补全 §9.6 的 @mention 机制：mention 由**候选匹配器**辅助插入（实现面 `canvas-resource-mention-textarea.tsx`）。对本项目直接相关：这是与 LibTV AutoLink（`LIBTV_AUTOLINK_STATE_MATRIX`）同题的第三份实现样本。
2. **画布手动保存与强制覆盖**（features.mdx:267-278）：「保存」=先本地缓存再云端同步、失败排队重试（平板无键盘场景）；「强制覆盖保存」=云端反复失败（如「画布媒体与素材库记录不一致」）的显式恢复：确认弹窗 → `canvas-asset-repair.ts` 校验画布媒体/时间线片段的素材绑定并重绑（缺失按节点新建）→ 按「素材先于画布」顺序整体推送 → 素材远端冲突采纳远端为基线用本地覆盖；**不绕过后端「画布资源必须被素材记录引用」不变式**。——补全 §13.1 lifecycle（此前仅记 `forceOverwriteRemoteCanvasSync` 入口名）。
3. **提示词放大编辑**（features.mdx:67-69）：图片/视频节点提示词面板放大窗口 `min(1200px, 92vw)`、最小高 200px、右下角对角拖拽、方向键微调、切换节点恢复默认。——新增 UI 面证据。
4. **多角度 3D 编辑器形态**（features.mdx:84-90）：「多角度」是贴在节点下方的 3D 编辑器（天空盒/摄像头/常用角度/方向箭头），拖节点或平移画布面板跟随——补全 §10.2 angle 工具的 UI 形态（`canvas-angle-scene.tsx`）。
5. **批量创作表交互面**（features.mdx:63-65）：全局提示词覆盖各行、空槽点击/拖入上传、缩略图点击替换与跨行跨列交换、参考列拖拽重排、连线到参考端口自动刷新任务行 + 「同步连线」手动增量、Agent 经 `canvas_edit_batch_table.set_global_prompt` 写入、读取带 `globalPrompt` 与按全局提示词的 `generationPreview`。——补全 §9.4。
6. **自由空白画布起点**（features.mdx:252-265）：空画布中央带加号起始框，点击打开与底部工具栏同一命令注册表的添加菜单；自由起点选择按画布持久化（`starterMode`），刷新不重回引导。——补全 §12.3（`canvas-starter.ts:5-22` 的 `starterMode` 字段已录，交互语义此处补全）。
7. **时间线编辑器（剪辑成片）**（features.mdx:325-359）：`/projects/:id/editor`；命令状态机 + **200 层历史**（对照画布本体 50 条补丁栈，§8.1——同一产品两套历史粒度）；fail-closed 权限（`timeline.command` 与全局 `plugins.run` 分开，§16 权限体系的延伸）；8 个内置预设插槽；语音转写走本地 whisper.cpp（`CANVAS_WHISPER_BASE_URL`，未配置明确失败——与 §17 本地伴随进程同型的「重能力外置」）；成片导出服务端 ffmpeg；AI 编辑助手 ≤3 命令直执行、>3 先差异预览（与 Agent 审批预览同哲学，§11.1）。
8. **云端 Agent 记忆与能力面**（features.mdx:41-45）：`remember_lesson` 写入待审、用户自批/导入导出/按日周月压缩相近条目；系统提示只带已批准记忆索引、`recall_lessons` 按 topic 取；运行中可插话（下一步生效）；`plan_update` 待办 + 未完成催办、首次 ≥2 项清单先确认；终态旧轮冻结合同不可变；节点标题与「下一版提示词草稿」可安全修改而不覆盖既有媒体/已提交提示词。——补全 §11（记忆体系 v1-v3 未覆盖）。

### 18.3 超出画布范围（仅登记不展开）

支付订单对账、首页通知、签到加油站、账号容量、渠道排序与别名、注册限流、站点外观皮肤、邮箱找回密码、官方提示词模板目录、提示词优化器（§16 已录插件机制）、Eagle 素材库（§16 已录）、用户诊断包——均为工作台/运营面能力，与画布实现无直接耦合（features.mdx:8-39,94-103,112-145,147-159,221-250）。

### 18.4 对照结论

- 产品文档与源码证据**零冲突**：抽样 7 组数值/语义断言（5 分钟/20 份/350ms/3s/5×5/单解码器/泳道规则）全部与静态阅读吻合——上游文档纪律与其测试纪律（BF-40）同源。
- 画布本体的实现复杂度（§2-§9）在产品文档中**刻意低描述**（只有抓手框选/外观/整理/起点/保存五节），重描述在 Agent/版本保护/时间线等「用户可感知保障」上——产品叙事与工程重心一致（推断）。
- 对本项目新增的直接相关物：**智能引用匹配器**（与 LibTV AutoLink 同题第三样本，候选对照 §9.6/BF-31）与**强制覆盖保存的素材重绑顺序**（「素材先于画布」不变式，对照 `VR-021`）。

## 19. 上游测试套件全景与抽读（v5 补充）

- **规模**：`web/test/` 共 **292 个测试文件**，其中 **111 个以 `canvas` 开头**（`ls web/test | grep -c '^canvas'`）——一个自研画布内核配套 111 个画布回归文件，测试面覆盖本包 §2-§17 的几乎每个机制（名称自描述：connection-create-menu/batch-connection/connected-node-placement/selection/spatial-index/storage-revision/generation-task-sync/local-generation-recovery/image-batch-retry/video-segment-ffmpeg/storyboard-*/workflow-builder/libtv-fixture/toolbar-libtv-navigation/zoom-presets 等）。
- **形态分布**（抽样归纳）：纯函数行为测试（算法域）+ 源码文本合同测试（readFileSync+toContain，BF-40）+ 轻量 DOM/markup 测试（renderToStaticMarkup，canvas-grid-viewport）三类；另有 `test:canvas`/`pretest` 分级门禁（package.json）。
- **抽读 4 件（与包内承重断言直接相关）**：
  1. `canvas-connection-create-menu.test.ts`（34 行）：快速创建菜单钉死**「引用该节点生成」标题 + 7 个命令**（text/image/video/audio/smart-edit/director/script）；后三者在菜单中「暂不可用」置灰——与 §6.2/BF-15 的证据互证。**第二条测试名直接写着「exposes the LibTV-style compact list layout」**：`w-[232px]`、`grid-cols-4`、`--canvas-create-node-height: var(--space-16)`——添加菜单的紧凑列表布局是显式按 LibTV 形态做的（BF-39 的第三处命名级证据）。
  2. `canvas-keyboard-delete.test.ts`（14 行）：Delete/Backspace 块的文本合同（preventDefault + stopPropagation + return）——§6.3/BF-18 的防浏览器后退语义被钉死。
  3. `canvas-local-generation-recovery.test.ts`（25 行）：刷新对账 effect 断言**不包含 `if (localMode)`**（本地/服务器模式统一对账）、孤立 loading 仅在无 taskId 可对账时才标记中断——§9.3/BF-27 的「历史 taskId 不是锁」语义被钉死。
  4. `canvas-libtv-fixture.test.ts`（73 行）：LibTV 捕获夹具契约逐个钉死——只读 dense 夹具 **61 节点（38 image/17 video/6 audio、无 frame）**、分镜夹具 2 frame + 6 个带 parentId 节点、视频夹具 `data:video/mp4;base64` + svg 预览 + 5000ms、音频夹具 wav「中文」、生成中夹具 `taskProgress:42` + `taskStage:"正在生成画面"` + epoch 时间戳——§13.2/BF-37 的夹具清单有了精确数字。
- **对本项目的意义**：111 个测试文件的**命名清单本身**就是上游画布机制的自我索引（哪个机制值得测试 = 哪里有过回归），与本项目 `VERIFICATION_LEDGER` 的台账思路同源；若未来对照实现某一机制，可按名索引上游对应测试作为行为规格参考（推断）。

## 20. 声明式协议引擎与模板表达式语义（v6 补充）

- **设计意图**（`backend/internal/protocol/expression.go:12-14` 包注释）：「Manifest expressions are JSON values with a deliberately small set of $-prefixed operators. They can construct provider payloads **without running plugin code or exposing host objects**.」——这是 BF-41「上传物=纯数据、执行=宿主引擎」安全姿态的引擎级落实。
- **表达式求值**（`evaluateManifestValue` :15-67）：JSON 值递归求值；单键 `$` 前缀对象视为算子；`"${path}"` 整串取路径值；数组求值时**静默丢弃 nil 项**（:32-34）。路径遍历 `manifestPathValue`（:520-540）支持点号+数组下标，**miss 静默返回 nil 不报错**——「响应字段缺失」被当作空值而非异常。`{{path}}` 字符串插值（:503-518）供 URL/模板串用。
- **算子全集（45 个）**（v97 勘误：原记 36 个；按多名单 case 全量展开实测 45 唯一算子名——`$coalesce,$default`、`$map,$filter`、`$eq,$ne,…,$and,$or` 等共享分支是此前漏计主因）：
  - 数据：`$ref`、`$literal`、`${path}`、`{{path}}` 插值
  - 流程：`$coalesce`/`$default`（首个非空）、`$if`、`$switch`、`$omitEmpty`（空则剔除字段）
  - 字符串：`$concat`、`$split`、`$lower/$upper/$trim/$toString/$toInt/$toFloat/$toBool`、`$json`（序列化）、`$dataMime/$dataPayload`（data URL 拆解）
  - 数组：`$concatArrays`、`$map`（as/item+itemIndex/in）、`$filter`（where）、`$indexObject`（**数组→带前缀编号键对象**，带 max 截断——适配「`image_urls.0` 式编号键参数」的渠道）、`$first/$last/$at/$len`、`$sortByOrder`
  - 对象：`$merge`（浅合并）
  - 数学：`$add/$multiply/$divide`（除零报错）`/$min/$max/$ceilStep`（向上取整到步长）
  - 比较/逻辑：`$eq/$ne`（**canonical JSON 串比较**，:474-477）、`$gt/$gte/$lt/$lte/$in/$and/$or/$not`
- **真值语义**（`manifestTruthy` :580-604）：字符串 `"false"/"0"/"no"/"null"`/空白均为假——与前端 `video-player` 的 hasAudio 解析（`canvas-media-performance.test.ts:197` 同规则）跨端一致。
- **适配器生命周期**（manifest.go:412-561）：`BuildCreate/ParseCreate/BuildPoll/ParsePoll/BuildCancel/BuildResult` + Agent 对（`BuildAgent/ParseAgent`）+ 能力旗标 `AgentAvailable/ResultAvailable`；**请求先过 `validateManifestRequest`（fail-closed 规则校验）再构造**（:420-422）。
- **响应解析的容错设计**：`ParseAgent` 全部走**多候选路径数组**（`TextPaths.../ReasoningPaths.../ToolCallIDPaths...`，:467-489）适配同协议各家网关差异；无 ID 的 tool call 用 `sha256(body#index)` 合成 ID（:492-495）。
- **同步二进制响应**（:507-527）：`response.binaryPayload` 时按 `http.DetectContentType` 嗅探 MIME 包成单媒体结果；注释明示「空响应必须失败，不能把空内容伪装成生成成功」；`resultKind` 只认 image/video/audio。
- **兼容 shim 实例**（:427-448）：`newapi-channel-1` 视频能力硬编码「input.prompt 与 input.content 双投影（迁移期两个都发）」——引擎保持纯声明，个别已发布渠道的兼容逻辑以 `metadata.ID` 特判收容在引擎内而非插件里（取舍记录）。
- **对本项目的意义**：若 clone 未来需要「用户自带渠道协议」（对照 BeefTV 84 渠道包的诉求），此引擎给出了完整的最小算子集与容错语义参照；与本项目「模型渠道协议在前端 image/video/audio 协议层实现」的形态不同（BeefTV 把协议层移到了后端数据）。

## 21. 时间线域：命令状态机、200 层历史与 AI 命令契约（v7 补充）

> 基准文件（全读）：`web/src/lib/timeline/editor-commands.ts`（364 行）、`editor-history.ts`（57 行）、`ai-command-schema.ts`（220 行）、`timeline-summary.ts`（72 行）。代码头注释引用 ADR-0002（命令协议）与 ADR-0007（AI 交互决策），**ADR 文档本身不在公共快照中**（`docs/content/docs/` 仅 backend/overview/plugins，全仓 find 无 adr 文件）——编号是内部流程的残留引用（证据边界）。

### 21.1 命令状态机（ADR-0002：时间线唯一修改入口）

- 协议形态：`EditCommand = { op, payload }` 可序列化；handler 是**纯函数** `(state, payload) → TimelineProject`（禁依赖组件实例）；未知 op 或非法 payload 一律抛错（fail-closed）。头注释明示设计目标：「保证可回放、可撤销、可黄金文件测试」（editor-commands.ts:1-4）。
- **12 个内置 op**（:52-65）：`addClip/moveClip/trimClip/splitClip/removeClip/setClipProperty/addSubtitle/removeSubtitle/rebuildSubtitleClips/addTrack/removeTrack/setTrackFlag`。
- 注册表：`createEditorCommandRegistry()` 可建隔离实例（测试/黄金比对用），宿主单例 `getEditorCommandRegistry()`（:339-364）；**插件经宿主 API register 自定义 op，与内建命令共用同一注册表与校验纪律**（同名覆盖、注册顺序即优先级，:12-14）。
- 校验纪律（逐条 fail-closed）：clip 形状断言（id/kind/trackId/nodeId/startMs≥0/durationMs>0，:75-84）；trim 受 `sourceDurationMs` 上界约束（「UI 与命令层同一条规则，防止导出越界」:140-145）；splitAtMs 严格在片段内部（:162-164）；`setClipProperty` 走属性白名单（title/text/volume/fadeInMs/fadeOutMs/subtitleEntryIndex，**结构字段必须走专门命令** :189-198）；字幕重建 id 确定性（`${nodeId}:subtitle:${index}` 原地替换不漂移 :296-318）；addTrack 的 id/order/label 全部由当前状态派生（「同一撤销/重放路径永远得到同一结果」:236）；removeTrack 守卫每类轨道至少保留一条（:252-254）；durationMs 永远从 clips 重算（:98-101）。

### 21.2 快照撤销：200 层 + 结构共享（editor-history.ts 全文）

- `HISTORY_LIMIT = 200` 全量快照双栈（undoStack/redoStack/current，:7-14）；push 旧 current 入栈、清空 redo、超限 shift 最旧（:24-28）；undo/redo 空栈返回 null（调用方保持现状）。
- **关键注释**（:3）：「快照依赖命令层不可变更新：历史中保存的是结构共享的全量对象，**不做深拷贝**」——命令协议的不可变更新使全量快照栈变得便宜。
- 纯函数式结构，供 zustand `set(createEditorHistory(...))` 直接换引用（:2）。

### 21.3 AI 命令契约（ADR-0007：同一注册表约束三方）

- 设计原则（ai-command-schema.ts:1-3）：「**同一份注册表同时约束模型输出和宿主执行**，避免提示词与真实能力列表分叉」「预检使用与正式执行相同的纯函数注册表，保证『模型看见的能力』和『宿主实际允许的能力』一致」。
- `AiCommandPlan {reasoning?, commands}`；**`commands: []` 是合法终态**（只读问答/能力不足），「调用方不应把它当成『执行成功的空修改』」（:69,82）；LLM 输出 JSON 提取容忍 markdown fence 并逐字符数括号（:26-57）。
- **整批 dry-run 预检** `validateAiCommandBatch`（:101-113）：按序 apply 到当前时间线（immutable 无副作用），任何一条触发拒绝规则即**整批拒绝**并返回首个失败位置与原因；「正式执行不得绕过这一步或只提交部分命令」。与 features.mdx「≤3 条直执行、>3 条先差异预览」叠加：8 是 schema 硬上限（`AI_EDITING_MAX_COMMANDS=8` :123），3 是直执行/预览分界。
- 提示词契约同源：`AI_EDITING_OP_CATALOG` 是 12 op 的 LLM 可读 payload 契约（「op 集合与注册表黄金同步（见测试）」:125）；`AI_COMMAND_SCHEMA_VERSION=1` 供 golden 测试与缓存失效对齐（:120）；系统提示词 = 确定性时间线摘要 + op 契约 + 输出约束 + 示例，并约束「所有 id 必须来自时间线摘要，禁止编造」「无法完成时 commands:[] 并在 reasoning 说明缺什么能力」（:194-219）。
- 交互决策分层（features.mdx:341 + §18.2.7）：≤3 条直执行、>3 条先差异预览确认后批量执行——「预览/直执」分界是产品层策略，注册表只管合法性。

### 21.4 确定性时间线摘要（timeline-summary.ts）

- `summarizeTimeline`：中文纯文本摘要，**确定性（无时间戳/无随机）**——同一输入永远同一输出（:1-2）；轨道按 order 排序、旗标（隐藏/静音）；片段逐行列出上限 60 行、超出折叠为「…其余 N 个片段省略」（`SUMMARY_MAX_CLIP_LINES=60` :7,60-66）；标题/文本截断 24 字符（:9）；字幕总字数汇总（:67-70）。消费方：AI 编辑系统提示词 + 诊断。

### 21.5 历史粒度对照：时间线 vs 画布本体 vs Agent 画布操作

| 维度 | 画布本体（§8.1 use-canvas-history） | 时间线（§21.1-21.2） | Agent 画布操作（§8.2/§8.3） |
|---|---|---|---|
| 修改入口 | store action（多点分散） | **命令注册表唯一入口**（ADR-0002） | `CanvasOperation` 8 原语（Agent/工作流） |
| 历史形态 | 实体差异补丁（by-id 前后像 + 顺序） | **全量快照双栈（结构共享、免深拷贝）** | 整批 before 快照（容量 10） |
| 深度 | 50 | **200** | 10 |
| 合并/提交粒度 | 180ms 防抖合并；拖拽期暂停 | 每命令一提交（命令原子性由调用方保证） | 每批次一提交 |
| 语义标签 | 无 per-command 标签 | 命令本身即标签（可序列化 op，可回放/黄金测试） | `summarizeCanvasOperations` 中文摘要 |
| AI/插件共约束 | 无 | **同一注册表约束宿主/AI/插件三方** | 能力 registry（服务端）+ 审批预览 |
| 批量预检 | 无 | 整批 dry-run，任一失败整批拒绝 | `verifyCanvasOperations` 后置复核（事后） |
| 一致性来源 | effect diff（易漏） | 不可变更新 + 确定性 id 派生 | 快照哈希（FNV-1a） |
| undo 失效策略 | 应用期防回环 | 空栈返回 null | 用户接手后引用失配即清栈 |

- **核心洞察（推断）**：BeefTV 在同一产品内并置了三种历史粒度，且时间线域用「命令协议 + 不可变更新 + 结构共享」化解了画布本体在 §8.1 的两难（补丁栈省空间但丢语义、快照栈保真但昂贵）——**结构共享让快照栈的成本趋近补丁栈，同时保住命令语义与黄金测试能力**。画布本体未跟进此方案的原因（推断）：画布编辑入口分散（28+ controller hook 直写 store），先收敛命令入口的改造成本高于时间线（时间线天生是单一编辑器入口）。
- 对本项目的启发：clone 的 history 层若要吸收（对照 BF-21/26），「**命令注册表唯一入口 + 不可变更新 + 结构共享快照栈**」比「实体补丁栈」多买到三样东西：AI/插件同源约束、整批 dry-run、黄金测试可回放；代价是必须先把编辑入口收敛成命令（与 `LIBTV_GRAPH_TRANSACTION_CATALOG` 的事务目录思路同向）。

## 22. 内置插件能力面：六插件逐个档案（v8 补充）

> §16 记录了插件**机制面**（manifest/注册/启停/安全）；本节补**能力面**——六个内置插件逐个全读（eagle.ts 371 行、prompt-optimizer.ts 352 行全文，workflows/ai-art-critique/media-conversion/editor-shell 合计 218 行全文；editor/ 八个插槽面板实现未逐行读，见 §21/§18.2.7 时间线域）。除 editor-shell 用 v2 manifest 外全部为 v1。

### 22.1 eagle（Eagle 素材库连接器，371 行，v0.3.0）

- 贡献：`contributes.assetSources=["eagle"]`（唯一 assetSource 插件）；permissions `asset.read/asset.search/asset.upload/external.open`，`trusted:true`，`runtime.web="trusted-backend"`（eagle.ts:92-114）。
- 架构：**浏览器不直连 Eagle**——所有读写经站点后端代理（`GET /api/plugins/eagle/*`），后端执行私网校验「只允许管理员明确配置的本机服务，不能把该代理变成任意 URL 抓取器」（内嵌文档 :71）。
- 导入映射（:47-53,148-188）：image 用原图（不拿缩略图当成品）；视频缺元数据时 1280×720 **展示兜底不改写原文件**；音频时长以浏览器探测为准；其他文件→model 素材；**文本/实体明确报错**。
- 写回（:192-270）：站点媒体→data URL→Eagle addItem；96MB 上限 + image//video//audio/ MIME 白名单；`autoUploadGenerated` 自动写回生成结果到配置文件夹，且「自动写回失败必须显示为写回失败，不应把『站点已保存』误报为『Eagle 已保存』」（:59）——与本项目「本地缓存≠服务端已保存」同款诚实边界。
- 细节：实例内 folderCache + 创建文件夹后失效（:122-144）；写回文件名无扩展名时按 MIME 推导补全（:224-229）；manifest 内嵌完整 markdown 用户文档（含 FAQ 表 :76-84）——`documentation` 字段承载插件自带文档的用法样本。

### 22.2 prompt-optimizer（AI 提示词优化器，352 行，v0.3.0）

- 贡献：`contributes.aiCapabilities=["prompt-optimizer"]`；permissions 声明 `canvas.read/canvas.write/ai.text`（实际只消费 `ai.text` 服务——**声明比使用宽**，观察记录 :65 vs :325-327）。
- 输出契约：strict tool-call（`optimize_prompt`，`additionalProperties:false`，必填 optimizedPrompt/negativePrompt/changes/assumptions/variants≤2，:25-56）；解析容错（剥 markdown fence + 首尾大括号截取，注释「某些兼容模型会在 JSON 外包一层解释」:283-284）；**失败回退原提示词不覆盖**（`normalizeResult` :312-323）。
- **按模型族的适配 profile（14 个）**：`resolveModelAdaptationProfile` 按 targetModel+targetProtocol 关键词匹配——图片族：Gemini/Imagen、OpenAI（gpt-image/dall-e）、Grok、**Seedream/即梦/火山**、FLUX、SD/SDXL、Midjourney、Ideogram/Recraft（设计文字）、通用兜底；视频族：**Seedance/即梦**、Veo、Kling、通用视频族（runway/minimax/hailuo/wan/ltx/hunyuan 归并一档）（:109-224）。每个 profile 三件套 `promptShape/rules/avoid`，规则具体到「不要套用 SD 权重语法」「中文需求保持中文表达」「有首帧时明确哪些必须保持」。
- 对本项目相关性：即梦/Seedance profile 直接对应 LibTV 生态模型；「模型族→提示词结构规则表」是 `LIBTV_MODEL_CAPABILITY_PROJECTION_MATRIX`（open-canvas 包）的插件化同题样本。

### 22.3 workflows（RunningHub 工作流提供者，44 行，v1.0.0）

- 贡献：`contributes.workflows` 程序化生成 image/video/audio 三个 capability 项（:16-28）；permissions `generation.run/external.open`；runtime backend+web 双 `trusted-backend`。
- 边界：「API Key、工作流参数和字段映射仍由宿主安全保存并提交，**插件本身不接触密钥**」（documentation :35-38）；导出 `workflowProviderPluginEnabled` 供宿主按启停状态过滤工作流能力（:23-25）。

### 22.4 ai-art-critique（AI 审美批改，45 行，v0.1.0）

- **唯一贡献画布节点的内置插件**：`contributes.canvasNodes`（declarative renderer、`acceptsInputKind:"image"`、`showOutputConnection:false`、560×420，:17-27）——§4.2 所述「插件式节点 `"ai-art-critique"`」的注册源。
- **Agent 双钩子**（:29-33）：`agentActions` 注入 `prepareAnalysisNodeAction`（对应 Agent 工具 `canvas_start_art_critique`，准备-用户确认-执行模式）；`readAgentNode` 为 Agent 提供节点读取投影，**内置 stale 检测**——`report.sourceFingerprint` 与上游唯一 image 输入指纹比对，不一致返回 `status:"stale"` 并附话术「已有报告仅在输入指纹一致时返回」（:30-37）。与 media-conversion 节点的 sourceFingerprint stale 机制（§附 C）同构。

### 22.5 media-conversion（媒体转换节点，37 行，v0.1.0）

- 贡献：`contributes.transforms`（media→media，declarative runtime）——transforms 贡献类型的唯一实例。
- 文档即边界（:10-17）：五转换（灰度/Canny/AI 线稿/深度图/姿态骨架）；「AI 线稿使用本机 ControlNet Aux、深度图用本机 Depth Anything V2 Small、姿态用 OpenPose，**不加载 Stable Diffusion 重绘管线**」；「透明抠图和视频高级逐帧模型仍在验证，**会明确提示不可用**」；「只读取当前节点媒体输入，结果保存回当前画布节点本地素材存储」。与 §17 framefield-local-runtime 的 estimation 模块衔接。

### 22.6 editor-shell（剪辑工作台外壳，92 行，v0.1.0，唯一 v2 manifest）

- 唯一 `PluginManifestV2`：permissions 用 v2 新增的 `timeline.read/timeline.command/export.run`；`contributes.editorSlots` 一次声明 8 个插槽（timeline-panel/preview-renderer/inspector/asset-ingest/subtitle-tool/transcription-provider/export-renderer/ai-assistant，:17-38）。
- **声明+指令双轨注册**：manifest 声明贡献面，渲染器经 `registerEditorSlot({pluginId, slot, render})` 模块副作用逐一注册（:44-90）——插槽面板组件（editor-timeline-panel 789 行等八件）留在同一目录，由 shell 聚合（editor/index.ts 注释「editor-shell 单个预设插件贡献全部 8 种 editorSlots」）。

### 22.7 跨插件模式归纳

- **六种声明贡献面**：assetSources / aiCapabilities / workflows / canvasNodes / transforms / editorSlots，加两类指令式钩子（createAssetSource/createPromptOptimizer/agentActions/readAgentNode + editorSlots 的 render 注册）——「manifest 声明能力目录，指令式代码只做实现接线」。
- **documentation 即边界声明**：每个插件的内嵌文档都明确「不做什么」（eagle 不做任意 URL 抓取、workflows 不接触密钥、media-conversion 不加载 SD 管线、art-critique 报告指纹不一致即 stale）——用户文档与安全边界同文书写（推断：与 fail-closed 权限体系配套的沟通纪律）。
- **全部 `trusted:true` + trusted-backend/declarative**：内置插件不走 sandbox 路径（§16），sandbox renderer 占位继续等待第三方场景。
- 运行时形态与 §16 的「声明式贡献 + 编译期内置实现」结论一致；六个插件的代码量分布（371/352/45/44/37/92）显示「连接器/优化器重、节点插件轻（节点 UI 实际由宿主内置组件承担，§16）」。

## 23. 导演台 three.js 内部机制（v9 补充）

> §12 记录了导演台的边界级证据（场景模型/画布绑定/物化）；本节补内部机制。基准：director 域合计约 6400 行 28 文件，重点精读 director-viewport.tsx（1199 行）、director-scene.ts、director-animation-semantics.ts、director-save.ts（443 行）、director-gesture-transaction.ts、director-recovery/repro-*、director-view-modes.ts（362 行）等；包作者抽查 4 处承重断言全部吻合（Canvas 稳定引用/gizmo 冻结/历史 50/草稿键+300ms）。技术栈是 **@react-three/fiber + drei + three-stdlib**，领域逻辑全部抽成纯函数模块（lib 层不持 three 对象，`director-view-modes.ts:13` 注释明示为全库一致约束）。

### 23.1 渲染管线

- **Canvas 配置必须是模块级稳定引用**（`director-viewport.tsx:59-64` 注释：inline literal 会在 context lost 重渲染时让 R3F 在失效 context 上重建 WebGLRenderer 并抛错）：`gl={antialias, preserveDrawingBuffer:true, alpha:false}`、相机初始 `[4.8,2.7,6.8] fov50 near0.05 far500`、`dpr:[1,1.5]`。`preserveDrawingBuffer` 是截图 `toBlob` 的前提。
- **按需渲染**：`frameloop="demand"`（:226-233），所有状态变更后显式 `invalidate()`；仅骨骼控制球对齐用 `useFrame`（:902-925）。Canvas 包在 memo 隔离层内防外层重渲染穿透，重建靠 retryKey remount（:211-248,88-89）。
- **三相机指针切换**：freeCamera（OrbitControls 专属）/camCamera（CAM 取景）/orthoCamera（正交五轴）各为独立实例，切 viewMode 只挪指针绝不读写彼此（:296-305,417-421）；OrbitControls 显式绑 freeCamera 且 CAM/正交下 `enabled=false` 真锁定（:455-459）——「切换不污染相机」。
- WebGL context lost：监听装在 renderer 自己的 canvas 并 `preventDefault`（否则浏览器不补发 restored），恢复序列=复位→重登记→invalidate（`director-recovery.ts:32-100`）。

### 23.2 对象操控：显式 attach + 冻结 + 同对象读回

- gizmo 仅在 `selected && target` 时渲染，`<TransformControls object={target}>` **显式 attach**；拖拽期间 `setFrozen(snapshot)` **冻结声明式 transform**（`transform = frozen || resolved`，:553-557 注释「手势进行中冻结声明式 transform，交由 gizmo 直接改写 Object3D」）；终态后 `readObject3DTransform(target)` **从被操控的同一 Object3D 读回** position/rotation/scale 上抛 `onObjectTransform(id, from, to)`（:588-594,638-640）。
- 骨骼 gizmo 与对象 gizmo **共用同一事务 hook**（rotate 模式、快照/恢复 `bone.quaternion`，:611-636,869-881），避免两套实现漂移；terminateDrag 不写 stdlib 私有字段而是派发真实 `pointerup`（:619-624）。
- **无网格吸附，放置是避让式**：新对象确定性 ring 采样（24 环×12 采样步长 0.75）找空位，耗尽回退「所有占位最右边界之外」（`director-placement.ts:40-89`）；地面拾取用原生 pointermove+Raycaster 与 y=0 平面求交（不走会被物体截断的 mesh 事件，`director-viewport.tsx:346-376`）；骨骼点选=射线到骨骼世界坐标距离 ≤0.12 选最近（:711-729）；控制球可视/命中尺寸屏幕恒定（3.5px/10px，按 DPR 换算 :910-946）。

### 23.3 关键帧与动画：手写分层采样，非 AnimationMixer 驱动

- 插值手写：transform 位置/缩放逐分量 lerp、**rotation 走 Euler→Quaternion slerp→回 Euler**（`director-scene.ts:220-232`）；缓动 step/smooth/linear 按「前一枚关键帧的 easing」作用于区间（:193-198）；骨骼四元数 slerp（:234-241）；upsert/remove 以 epsilon 0.001 判据、未命中返回同引用让调用方跳过历史与保存（:89-156）。
- **骨骼分层合成**（`director-viewport.tsx:1038-1064` + `director-animation-semantics.ts:86-97`）：优先级低到高 = rest×poseDelta 或 motion → 静态 override → 关键帧插值，`target.quaternion.copy(...)` 直接写骨骼。AnimationMixer **只用于 motion clips** 且不自走时钟——播放时 `mixer.setTime((playhead-start)*rate)` 声明式求值（:840-846），其输出作为 motion 层输入参与合成。
- **21 种预设姿势 = 纯数据表**：`directorPoseBoneDeltas` 把每个姿势编译成「骨骼→四元数增量」（如 stand=双上臂 z+1.28 放下手臂），与 rest 相乘合成，不依赖动画资产（`director-scene.ts:267-294`）。
- **Auto Key 双语义**（`director-animation-semantics.ts:55-70`，本域最有特色的设计）：autoKey 开→只 upsert 当前吸附播放头关键帧；autoKey 关→把「渲染值→编辑值」增量（四元数相对旋转 + scale 比率/偏移双通道）**整体搬到 base 和所有已有关键帧**，保证编辑可见且不改未编辑帧的渲染结果。取值/手势起点用 raw playhead、写入用帧格吸附（workbench:200-203）。
- 播放：工作台自有 rAF 按 shot fps 帧格累积步进、取模循环（:232-249）；motion path 可视化（Line+端点球+方向锥）共用同一关键帧数组（viewport:464-492）。

### 23.4 保存管线：立即草稿 + 防抖排空 + revision 确认

- `createDirectorSaveCoordinator`（`director-save.ts:129-443`）：每次 edit `revision+1` → **立即同步**写 localStorage 草稿（键 `director-scene-draft:<sceneId>` 按用户 scope，:136）→ 300ms 防抖进**排空循环**：目标 revision 取最新，成功后 confirmedRevision 前滚、未追平则刷新草稿 base 继续，追平才删草稿（:247-313）。
- 冲突策略靠 `baseUpdatedAt` 基线而非覆盖检测：草稿基线 === 权威 updatedAt 且草稿更新才弹恢复（陈旧残留不提示，`director-save-wiring.ts:56-67`）；`prepareClose` 三态 close / offer-draft-exit / stay（草稿也没写进去则阻止离开，`director-save.ts:367-390`）。
- **localStorage 不可用时显式抛错**，绝不降级进程内 Map——「那会让恢复弹窗撒谎」（wiring:92-122）。flush 回调 = 先 `persistScene` 写回画布 `directorScenes` 再 `await flushPersistence()`（`use-director-save-coordinator.ts:58-68`）；严格区分 canonical 提交（commitScene）与仅镜像（mirrorDraft 不产 revision，workbench:127-148）。

### 23.5 手势事务：一次手势恰好一个终态

- `createDirectorTransaction`（`director-gesture-transaction.ts:26-67`）：begin 抓快照；end 恰好一个终态——**pointerup/window blur/document hidden → commit**（「失焦只是离开，用户已把对象拖到那里」），**Escape/pointercancel → cancel** 恢复快照；非活跃 end 幂等。终态监听常驻安装，绝不按手势条件装拆（:83-114）。
- 工作台层 stagedTransaction：数值滑杆等暂存型手势以整个 DirectorScene 为快照实时写 draft 但不产历史，end(commit) 才推历史并 canonical 提交（workbench:258-286）；普通 commit 前先终结暂存手势防「新动作消费旧 base」（:256-259）。
- 历史 = structuredClone 场景数组、**各封顶 50**（:230 `[...items.slice(-49), …]`、:306/:313 `.slice(0,50)/.slice(-50)`；包作者已核对）；切换选择/卸载前 `end("cancel")`（:295-297）。状态机不变量独立成纯函数 `reduceDirectorGesture`（animation-semantics:104-113）。

### 23.6 恢复与复现基建

- `director-recovery.ts` 是「加载失败 + WebGL 上下文丢失」恢复：模型加载 generation 状态机（晚到旧代回调直接丢弃，**render 阶段即可屏蔽旧资源不依赖 effect 时序** :118-125）；失败对象注册表 loading/ready/unmounted 都必须移除防陈旧重试入口（:46-67）；失败对象退占位人偶 + 「重试加载」角标。
- `director-repro-fixture.ts` 是 **P0 缺陷复现夹具**：确定性离线场景（字面量 id/时间戳、不引用网络资产并有离线校验）+ **15 条手工复现矩阵**（每条 steps/expected，如「blur→commit 一次不重复镜像」「Escape→恢复快照且被取消值绝不发布」:113-129）+ 注入变体（本地手写 base64 glTF、确定性 404 的 .glb 稳定触发失败路径）。`director-repro-runtime.ts` 记录环境快照（版本/commit/浏览器/WebGL capabilities），文本过脱敏（遮 bearer/token/URL/query），WebGL 探测用一次性 canvas + `WEBGL_lose_context` 归还。
- **白名单诊断**（`director-diagnostics.ts`）：11 个稳定码、message 只能来自固定常量表（绝不接收 Error/stack/URL/业务文本）、字段仅白名单枚举|布尔|有界数值|safe-id、未知 code 一律丢弃、1.5s 签名去重（recorder:13-37）。

### 23.7 取景模式（7 种，纯视口状态）

- free/camera/top/front/back/left/right 与一级模式正交；**viewMode 绝不写入 DirectorScene、不产生 undo/历史**（`director-view-modes.ts:12-13`）。
- CAM 取景按活动 shot 相机在 playhead 上插值；**荷兰角保留**：up 向量按相机欧拉角预旋转，且写入时「必须先写 up 再 lookAt，顺序颠倒丢荷兰角」（viewport:503-521）；取景失败确定性回落 free、恢复后回 CAM（view-modes:143-147）。
- 正交五轴取景来自**场景内容包围盒**（旋转后 8 角点 + 相机/灯光位置收点云、margin 1.2），frustum 同时装下水平/竖直两跨度，机位沿视线反推永远在包围盒外（:228-362）。

### 23.8 快捷键、诊断、预览出图

- 快捷键纯函数 `resolveDirectorShortcut`（W/E/R 变换、Del、Ctrl/Cmd+Z/Shift+Z/Y、H、Esc、Space）；焦点在交互控件一律不解析，`releaseDirectorFocusAfterPointer` 在指针激活后 blur 按钮修复「点完按钮 Delete 失效」（`director-shortcuts.ts:79-163`）。
- 预览出图 `capture(mode)`（:1107-1125）：摘 clay 态 → 按 mode 设 `scene.overrideMaterial`（depth/normal/wireframe；clay=整场景换共享白膜材质并跳过带 uniforms 的 ShaderMaterial 否则 drei Grid 逐帧抛错）→ **手动 gl.render 一帧** → `toBlob` → finally 恢复。视频录制 `canvas.captureStream` + MediaRecorder（vp9→vp8→webm 降级），Chrome webm 无时长头用 seek-to-1e6 校验真实时长（:1127-1195）。
- `applyToCanvas` 只采 beauty 静帧，输出前用快照时效校验保证长耗时输出期间场景未被编辑污染（`director-session.ts:31-35`）。

### 23.9 对本项目（liblib-tv）的直接对照

- **gizmo「显式 attach + 同对象读回 + 手势期冻结声明式 prop + 一次手势一个终态」正是本项目 AGENTS.md 硬约束「Director TransformControls must use explicit object attachment and read back the same Three.js object that was dragged; run Batch 77」的成熟参照实现**——BeefTV 在此之上补了「冻结声明式 prop 防手势期 React 回写」与「blur=commit/Escape=cancel 终态分型」两块，值得 Batch 77 契约复核时对照。
- 保存协调器（立即草稿+排空循环+revision 确认+基线恢复）与画布 store 的 400ms 队列（§3.2）是同一「写-合并-确认」哲学在编辑器域的细化版；「草稿基线落后=陈旧残留不弹恢复」的判定与 storageRevision rebase 的 stale 旁观者判定（§3.4）同族。
- 白名单诊断 + 复现夹具矩阵与本项目「稳定码 + verifier 台账」文化同构（BF-45）。

## 24. 时间线几何与画布桥接（v10 补充）

> 补全 §21 之外的 5 个几何/桥接文件（全读）：timeline-build.ts（184 行）、timeline-tracks.ts（54 行）、timeline-placement.ts（196 行）、timeline-snap.ts（61 行）、timeline-view.ts（72 行）。

- **来源标注**：tracks/placement/snap/view 四文件头注释均写明「**移植自 lingji-cut** 的同名文件，按本项目类型精简」——BeefTV 自身也从第三方项目（lingji-cut）移植代码，是继 LibTV 对齐（BF-39）之后的第二个外部 provenance 数据点。
- **画布→时间线单向快照**（timeline-build.ts:1-4 头注释「构建是单向快照：时间线保存后用户可自由拖拽，重新构建不覆盖已有时间线」）：视频/音频节点按画布顺序首尾相接入轨（游标累加，durationMs 缺省 4s 兜底）；视频节点的 `metadata.subtitleEntries` 转成字幕轨片段（相对该视频片段起点偏移、钳制在源时长内、`Math.max(100,…)` 最小时长）；`isNodeInTimeline` 按 nodeId 去重；`syncNodeSubtitlesToTimeline/syncTimelineSubtitleClips` 双向字幕同步（以视频片段为锚点重建、只处理已入轨节点，「避免把未入轨节点的字幕凭空加进时间线」:150-152）。
- **默认三轨** video-1/audio-1/subtitle-1 + `normalizeTimelineProject`（轨道 id 去重、补默认轨、时长=片段末端最大值）（timeline-tracks.ts:5-54）。
- **放置与吸附分离**（头注释明示）：`canPlaceAt` 只做半开区间 `[start, start+duration)` 重叠判定、「不做任何自动 snap/偏移，重叠即 ok=false」（placement:41-58）；`findNearestAvailablePlacement` 扫描全部间隙（首前/中间/末尾∞）取距目标最近的可容纳位置（:78-127）；`findAvailableTrack` 按 order 升序跨视觉/音轨尝试（:134-151）；`clampClipDurationByNeighbors` 用右邻钳制+可选 maxDuration（:154-176）。
- **吸附**（timeline-snap.ts）：候选点吸附播放头或片段起点/终点，阈值 `thresholdPx/pxPerMs` 换算成毫秒（屏幕像素语义，与 BF-14 连线吸附同思路），取最近目标，**并列同值目标全量返回**（供 UI 同时高亮多参考线 :44-52）。
- **视图数学**（timeline-view.ts）：基准 96px/秒、轨道最小宽 960px、zoom clamp 0.02–4 步进 ×1.25、fit 缩放按视口宽/基准宽；标尺刻度 12 档（100ms→300s）保证刻度间隔 ≥64px（:66-73）；时间文案 `mm:ss.d`。

## 25. 后端任务与生成域（v10 补充）

> 只读代理深读 backend 任务域（`internal/app/task_*.go`、`provider_*.go` 约 4900 行 + `internal/repository` + `internal/protocol` 宿主），包作者未逐行复核、抽查方式同前几轮（agent 给出的行号结构完整、与既有 §14/§20 证据交叉一致）。任务域主体不在 `internal/task/`（仅 75 行契约），在 `internal/app/`。

### 25.1 任务生命周期与调度

- 创建即冻结选型：`POST /tasks`（routes.go:18-42，16MB 上限+TraceID）→ `app.CreateTask`（task_creation.go:24-147）——**客户端只提交意图，模型/渠道/协议由服务端目录重新解析并冻结到任务**（LogicalModelID/RevisionID/RouteID/ChannelModelID/RouteRun=1，:106-114）；落库即 `queued`（progress=5，:102）。
- 状态机迁移全部条件更新（CAS）：`ClaimNextTask`（repository.go:211-253）领取「queued 或租约过期的 running 且 next_poll_at 到期」最早任务，置 running/attempts+1/lease（PostgreSQL 锁行、SQLite 条件更新 :210）；`SaveTaskCompletion` 带租约 fence 按期望状态 running 写入（:361-379）；`CancelTaskIfStatus` 条件取消（:391-399）；`RetryTask` 事务内条件重试并 `route_run+1`（local_runtime.go:285-311），业务门禁（审核失败/提交不确定不可重试）在 task_lifecycle.go:34-101——与前端 `canvasGenerationRetryBlocked`（§9.3）对称。
- **三层租约**：任务租约（45s 领取、15s 续租、续租失败放弃保存，task_worker.go:83,146-170）；worker 进程并发槽位租约 `AcquireLease("workers", N, 1min)`（:74，本地 TTL 实现 platform/coordination.go:106-133）；creation_runs 的 ExecutionEpoch/Owner 租约是**前端页面持有创作会话控制权**的另一套（creation.go:200-217）——与 features.mdx「执行租约」对应，与普通任务无关。
- **上游轮询是「同步循环 + defer 回池」而非常驻定时器**：视频任务首次执行内 `runVideoPollLoop`（默认 30s 间隔、容忍 3 次 404/畸形、尊重 Retry-After，provider_video_polling.go:67-131）；前台等待结束仍未完成则 `DeferRunningTaskForProviderPoll` 清租约保 running、`next_poll_at=now+15s` 回池由 ClaimNextTask 再领取回查（task_worker.go:235-248）。
- 取消对账：先落库 cancelled 再异步发上游取消；后台每 5s 对账、最多 41 次、**只有 Gemini Veo 和火山 Ark 支持上游取消**（provider_task_cancellation.go:18-180）；worker 侧对「取消后迟到结果」三重防御（领取后重读/保存前重读/保存冲突识别并发取消）。
- 失败视频任务有人工恢复口 `POST /tasks/:id/query-provider`：10 分钟恢复租约、**只查询不重新 create**、成功补登记产物（provider_task_recovery.go:64-159）。

### 25.2 幂等的后端真相（对 §9.2 的关键修正）

- **`clientOperationId/attemptGroupId/retryOf` 在后端 Go 代码 0 命中**（全后端 grep）：前端上送的字段仅存于 inputJSON 不被消费；普通 `POST /tasks` **无请求级幂等**（每次调用建新任务；`Task.RequestID` 仅 gin 追踪）。
- 真正的请求级幂等两处：**creation 流程**（`CreationSubmission.ItemKey` 稳定键 + RequestHash 去重 + `Task.CreationSubmissionID` uniqueIndex + 执行事务内重读 TaskID 已存在即返回旧任务；重做要求新报价批准）与 **Cloud Agent**（任务 ID=`"ag"+sha256(user\0idempotencyKey)[:16]`，同键不同 fingerprint→409）。
- 后端防「重复产生上游调用」四件套：服务端冻结选型（§25.1）；`RouteAttempt.DispatchState` 派发 CAS（`not_sent→submission_unknown` 只允许一个执行者，accepted 无 providerID 或 submission_unknown 无 ID → 拒绝自动重发，model_router.go:900-966）；provider 幂等键 `uuid.NewSHA1(NS_OID, taskID:attemptID)` 随声明式协议 create 注入 Header（provider_submission.go:13-21）；恢复已有 provider taskID 时绝不进 create 分支（provider_protocol.go:63-65）。
- **未发现积分扣费/退款实现**（grep refund/charge 仅注释；`ApiCallLog.EstimatedCostMicros` 无非测试写入点）——开源后端的「防重复计费」实为**防重复产生上游调用**；计费在 hosted 侧/支付插件（不在本仓库）。

### 25.3 provider 执行路径与上游进度

- 官方声明式接口**只走适配器**（未安装直接报「xx 视频插件未安装」，不回退手写协议，provider_video.go:70-78）；执行链 worker→routeExecutor（注入 submission key）→类型分派→provider.go 解析配置/参考媒体水合/能力校验→`runProtocolAdapterTaskWithPolicy`（§20 引擎宿主：URL 校验/凭证注入/SSRF/超时/大小边界都在宿主 :342-345；鉴权驱动 8 种含 aws-sigv4/tc3 :517-593）；`resultEphemeral:true` 触发宿主下载转 dataURL 持久化。
- 上游百分比回写**单调不回退**（`UpdateTaskProviderProgress`，repository.go:352-359）；前台对 image/video 不再用统一 35% 冒充进度（task_worker.go:193-198）——与前端 taskProgress 语义闭环。

### 25.4 任务与画布的关系（回传通道全景）

- `metadata.nodeId` 无独立列，随 inputJSON 存取，读回时解析为 `Summary.ClientContext{NodeID,ConversationID,Batch,ShotID,...}`（task_output.go:63-120）。
- **普通生成任务完成无服务端推送**（webhook 0 命中；`processTask` 对生成任务恒返回 nil canvasOps，`Result(kind="canvas_ops")` 只是预留存储）：前端 2s 轮询是唯一回填通道。例外：**Cloud Agent 媒体任务由后端与任务同事务直接建画布节点**（cloud_agent_media.go:573-599）。
- 两条推送通道均非任务事件：文本增量 SSE（`/tasks/:id/text-events`）与**画布 revision SSE**（服务端每 250ms 查库、revision 变化推 `event: canvas.updated {"revision":N}` 信号、前端再拉，user_data.go:497-545）——与 §25.1 revision CAS 配套。
- 事件日志双轨：TaskLog（生命周期节点，payload 截断，读口 `GET /tasks/:id/logs`）+ **ApiCallLog 每上游 HTTP 一行**（create|poll|download|cancel、durationMs、脱敏请求响应体），且承担恢复职责——`LatestProviderRequestIDForTask` 从日志补齐上游任务 ID（analytics.go:168-174）；任务失败但无日志时补审计行「request_not_sent/provider_request_unlogged」（task_api_call_log.go:16-90）。
- **对 §9.7 的修正/补强**：前端「轮询非 SSE」的结论得到后端证实（任务事件无推送通道）；「刷新按 taskId 对账恢复」之所以可行，后端依赖是 ApiCallLog 的 provider_request_id 水合 + 任务列表游标。

## 29. provider 域深补：参考媒体水合、鉴权驱动与出站边界（v14 补充）

> 只读代理聚焦深读三个点（provider.go 水合段、provider_protocol.go 鉴权段、outbound 域）。**定位修正**：鉴权驱动实际在 `provider_protocol.go:517-743`（v9/§25.3 曾引 `provider_http_client.go:517-593`，该区间实为 URL 前缀拼接；驱动为 12 种变体而非 8 种）。

### 29.1 参考媒体水合策略

- 两级策略 `{requireURL, preferURL}`（`provider.go:412-415`），决策函数按 interfaceType：基线白名单（ChatCompletion/OpenAI/Claude/Grok/Ark/NewAPI 系等接受远程 URL，:454-472）；**Mask 场景强制 false**（multipart 编辑需真实字节，「不能为了减少下载而擅自改变请求合同」:455-458）；Seedance/NewAPI channel-1 覆盖为内嵌；声明式插件经 `adapter.Metadata().RequiresPublicMediaURLs` 强制 URL（:441-444）。
- 转换链（`hydrateProviderMedia` :741-815）：资源必须 ready；`useObjectURL = requireURL || (preferURL && 对象存储)`。URL 路径：**本地模式 + requireURL 直接拒绝**——「loopback URL 外部模型不可达，不能伪造 public-resource 请求」（:764-769）；否则 HMAC 签名公开 URL（`{publicBase}/api/public/resources/{id}/file/{name}?expires&signature`，TTL 4h，私网 S3 强制 HTTPS，resource.go:36-175）。内嵌路径：按 RuntimePolicy 限长读流转 data: base64，MIME 声明优先、`http.DetectContentType` 兜底。特例：方舟可信素材把自有资源同步到方舟素材库后改写 `reference.URL` 为 `asset://{assetID}`（hosted 方舟视频专属，本地刻意不上传，provider_ark_private_assets.go:59-118）。
- 槽位映射：每参考按数组下标赋 `Order`，视频图带 Role（`videoStartFrameNodeId/EndFrameNodeId` 命中→first_frame/last_frame，否则 reference_image，provider_video.go:624-675）；JSON 视频协议 `image_urls` 排序为**首帧、尾帧、普通参考图**；引擎侧 `$sortByOrder` 稳定排序取槽位（§20）。

### 29.2 鉴权驱动（12 种变体，provider_protocol.go:517-743）

- 默认（Type 空）委托 `applyProviderAuth`（claude→x-api-key+版本头；gemini→x-goog-api-key；其余 Bearer）；none/bearer（header/prefix 可覆盖）/header（必须给 header 名）/query/basic（第二凭证走 SecretField）/anthropic/google-api-key 均 straightforward；**volcengine-v4 用官方 SDK Credentials 签名**（Region 默认 cn-north-1）；**aws-sigv4**：service 默认 bedrock、**region 从 hostname 分段推断**（推不出即报错）、签名前经 GetBody 重读 payload、规范头排除 authorization/user-agent/content-length/expect、AWS4 四轮 HMAC-SHA256（:595-641）；**tc3**：service 默认 hunyuan、规范头仅 `content-type;host` 两项（:643-672）；未知驱动**显式报错不静默降级**（:590-592）。
- 凭证安全：渠道密钥 **AES-256-GCM 加密存储**（密文前缀 `enc:v1:`，密钥为 dataDir/.settings-key 32 字节随机文件 0600，secret_store.go:17-110）；任务落库前 `protectTaskSecrets` 递归加密 apiKey/secret 类字段（:112-139）。
- 日志脱敏（recordProviderRequest + api_call_payload.go）：UpstreamURL 只存 scheme://host+path（query 不入库）；JSON 键含 apikey/accesstoken/authorization/password/secret → `[REDACTED]`；`data:` 值只留摘要；multipart 只留文件名/类型/大小；输出上限 128KB；HTTP 错误文本只留状态码。

### 29.3 出站边界（outbound.go + doBinaryWithConsumer）

- **防 DNS rebinding 的关键设计**：Transport `DialContext` 不信任连接期再解析，而是用与校验**同一策略的 resolveHost 自行解析并直连 addresses[0]**——校验与拨号用同一份解析结果，消除 TOCTOU（outbound.go:250-268）；DNS 解析后逐 IP 拦 loopback/私网/链路本地/多播；逃生口仅 `CANVAS_ALLOW_PRIVATE_UPSTREAMS=1` 或按主机精确放行（:380-398）。
- 重定向最多 5 跳且**每一跳重新过 ValidateOutboundURL**（重定向到私网会被拦）；自定义中转通道更严（禁重定向+保留网段前缀表+HTTP 仅限钉死可信主机）；自定义 header 规范化限 32 个/16KB 并封禁 authorization/cookie/host 与 hop-by-hop、`x-canvas-*`/`x-forwarded-*`（渠道/插件无法覆盖鉴权头，:130-168,242-248）。
- 超时/大小：默认 5min（取 context 剩余）、拨号/TLS 各 15s；响应上限三重强制（Content-Length 预检、LimitReader 逐块计数、终长复查）；渠道熔断打开直接返回、`AcquireChannelSlot` 租约=超时+1min；错误分类（request_cancelled/upstream_timeout/HTTP 状态码）统一进 ApiCallLog。
- **如实观察**：水合阶段 `isPublicMediaURL` 仅判断 http/https 前缀不做 IP 判断——内网拦截完全依赖出站校验+拨号期兜底；签名 URL 的 base 若配内网地址且运维开了逃生口，可被放行（显式运维选择）。
- 对本项目：这层「校验与拨号同源解析 + 重定向逐跳复检 + header 封禁表」是 clone 若引入任何「用户自带渠道」能力时的出站安全参照（对照 §20/§29.2 的声明式协议宿主）。

## 35. 上游前移差异审计（v1.5.7 → v1.5.9，v22 补充）

> 本包研究锚点**维持锁定 `85c9686`/v1.5.7 不变**；本节记录锁定之后上游的前移（2026-09-28 fetch：新增 tag `v1.5.8`/`v1.5.9` 与分支 `codex/video-alignment-20260927`），并标注对本包断言的影响。方法：`git log/diff 85c9686..v1.5.9`（恰好 2 个提交：e8cf506 浅色模式、e2fd1d3 视频素材限制对齐）。**v87 勘误（重跑核对）**：端点恒等（`v1.5.7^{commit}`==`85c9686c87a4…`、`v1.5.9^{commit}`==`e2fd1d3f78fa…`）而 diff 为确定性——实测总量 **62 文件 +2057/-849**（原误记 42 文件 +1590/-477）；分段：`85c9686..v1.5.8` = 23 文件 +234/-177（backend 0 文件），`e8cf506..e2fd1d3` = 41 文件 +1824/-673（含 backend 16 文件）。

### 35.1 v1.5.8「工作区和画布支持浅色模式」

- `CanvasAppearanceMode` 由 `"dark" | "custom"` 扩为 **`"light" | "dark" | "custom"`**；`canvasAppearanceForTheme` 不再强制落 dark、`canvasAppearanceBaseTheme` 不再硬返回 `"dark"`、normalize 接受 light（canvas-appearance.ts）。
- 画布默认外观回落到全局主题：`appearance: appearanceDefault?.appearance ?? { mode: useThemeStore.getState().theme }`（use-canvas-store.ts）。
- **主工具栏恢复「画布外观」面板入口**：v1.5.7 中 `onToggleAppearancePanel: () => {}`（注释「画布外观入口已按产品要求移除」）在 v1.5.8 被撤销——`CanvasAppearanceControls` 重新接线、`appearanceOpen` 浮层状态恢复（canvas-toolbar.tsx）。
- 对本包的影响标注：
  - §31.3 所引「画布外观入口已按产品要求移除，保留类型契约」**仅对锁定提交 v1.5.7 成立**；上游最新已恢复该入口（产品决策回摆的直接证据）。
  - §2.4/§18.1 的「三主题（浅/深/自定义）」表述与 v1.5.9 一致；「外观应用到当前画布或存为浏览器默认」语义不变。

### 35.2 v1.5.9「对齐素材限制与错误提示」

- 主要落点在前端生成链路的**视频参考素材校验与错误文案**：`video-validation.ts`（+82）、`generation-error.ts`（+98）、`model-capabilities.ts`（±97）、`video-provider-seedance.ts`（简化 -85）、`video-provider-newapi.ts`（±8）、`generation-task.ts`（+13）。
- 对本包的影响标注：§9.3 的失败语义（审核类失败指纹阻止重试、提交不确定相位）在锁定提交内成立；v1.5.9 把「参考素材不符合模型限制」的失败原因显式化到错误提示层——方向与 §9.3 的 `generationErrorCode` 体系一致，属增强而非语义反转，未核对到与本包断言冲突的点。
- 后端 `backend/internal` **有 diff**（v87 勘误：原记「无 diff/纯前端发布」不成立）：**16 文件 +1106/-165**——model_capability.go、provider.go、provider_protocol.go、provider_video.go、provider_video_options.go、video_reference_constraints.go（新增）、resource.go、generation/provider_error.go、generation/types.go、repository.go 及 6 个测试文件；性质为「素材限制与错误提示」的**服务端对应实现**（视频参考约束校验 + provider 错误分类/脱敏正则表 gofmt 对齐），与前端 v1.5.9 同主题。本包断言锚定 `85c9686`，不受此 diff 影响；§35.2 前端逐文件行数（+82/+98/±97/-85/±8/+13）经核为「插入+删除总变更行数」口径，与实测 numstat 一致。

### 35.3 处置

- 本包不移动锚点：全部 file:line 断言继续对齐 `85c9686`；§31.3 与 §35.1 的「入口移除→恢复」回摆已双向记录。
- 后续若需对齐 v1.5.9（如实现对照需要浅色画布模式细节），按 open-canvas 包 `UPSTREAM_VERSION_IMPACT_PROTOCOL` 的差异审计流程另行增量，不影响本包既有结论。

## 30. 字幕高亮与 SRT 重分段（v15 补充，时间线域收官）

> 全读：subtitle-highlights.ts（91 行）、subtitle-highlight-service.ts（50 行）、subtitle-highlight-runner.ts（113 行）、srt-parser.ts（67 行）、srt-resegment.ts（131 行）。

- **高亮自校验模型**（subtitle-highlights.ts:5-14）：高亮有效当且仅当 `highlightText === sourceText.slice(start, end)`——存储的是「文本自证」而非裸坐标，字幕文本一变（`entry.text !== sourceText`）即 expired（:21-27）；重分段后重映射规则：highlightText 必须是某新条目 text 的子串，取第一个匹配更新 entryIndex/start/end，**找不到则显式进 dropped**（「通常是跨切分点的关键词」，:39-56）——信息丢失被建模而非静默。
- **LLM 输出双重校验**（service:8-44）：先形状断言（entryIndex 数字/shouldHighlight 布尔/highlightText/start/end），再要求条目存在、再过 `filterValidSubtitleHighlights` 自校验——模型幻觉坐标在两层过滤后无法落地。
- **无模型回退**（runner 同目录 highlights 文件 25-45）：无可用大模型配置时按终止标点（。！？；）取首句作高亮，「保证功能不中断」。
- **批处理 runner**（runner:24-90）：batch 30 条/并发 3 的 **worker 池共享游标**模式；每批节点标记 `${nodeId}:subtitle-highlight:i/N`、metadata `operation:"subtitle_highlight"`；首错短路（后续 worker 见 firstError 即退）+ AbortSignal；进度按已处理条数百分比回调。
- **SRT 解析/序列化**（srt-parser.ts）：容错块解析（<3 行、非整数序号、无时间戳行的块跳过而非整体失败）；序列化时序号归一（非法/缺失用 idx+1）。
- **重分段**（srt-resegment.ts）：断点优先级 **中文标点 > 英文标点 > 空格 > 硬切**，在 `[0.6×target, target]` 窗口内取最靠右（:17-48）；时长按字符数等比分配；**最小时长 300ms 约束**逐段向后推、封顶原条目末尾，「总时长不足时接受违规（不崩溃，不重排）」（:57-77）；最终重编号 1..N（:123-128）。
- 域定位：高亮/AI 请求只写权威节点 subtitleEntries（§28.6「本面板不重复发起 AI 请求」的时间线侧实现）；本域收官后**时间线域全量覆盖**（build/tracks/placement/snap/view/commands/history/ai-schema/summary/highlights/srt）。

## 31. 画布周边边角：选区浮层、节点面板浮层与主工具栏（v16 补充）

> 全读：canvas-workspace-overlays.tsx（288 行）、canvas-toolbar.tsx（375 行）。

### 31.1 选区浮动工具栏（CanvasSelectionToolbar）

- 定位是**命令式直写**：`useLayoutEffect` 里用 `getBoundingClientRect` 算锚点，直接写 `toolbarRef.style.left/top` 与 `classList.toggle("-translate-y-full")`，仅在无 ref 时才走 React state（:47-53）——浮层跟随完全绕过 React 渲染。
- 五路重算触发源：ResizeObserver（锚元素+容器+自身）+ MutationObserver（观察视口层 style 属性变化）+ 订阅 viewport preview 事件 + window resize + 初始（:56-66）。
- 放置上下二选一：上方空间 ≥68px 用 above 否则 below，水平居中并钳制在容器 12px 内边距（:40-46）；`data-canvas-no-zoom` + mousedown/pointerdown stopPropagation 防画布误触（:78-82）。

### 31.2 节点面板浮层（CanvasNodePanelOverlay）

- 宽度自适应缩放：`clamp(round(node.width × k × 1.5), 660, 920)`（:156-159）——面板宽度跟随节点屏宽。
- 双事件订阅维持贴附：`subscribeCanvasGraphicsViewportPreview`（无节流，每帧重算位置 :127）+ `subscribeCanvasNodeDragPreview`（节点被拖时面板跟随 dragOffset :128-131）；贴附优先查真实节点 DOM（`querySelector([data-node-id])` + `CSS.escape`），查不到才按 viewport 数学推算（:115-118）。
- 层级契约：`useCanvasOverlayLayer("node-panel:<id>")` 提供 bringToFront/zIndex，pointerdown/focus capture 都抢前台（:96-101,147-149）；`CANVAS_MAIN_DOCK_CLEARANCE=80` 预留底部 dock 空间；短视口注释「**LibTV reserves only a small gap above the bottom controls**」（:250-252）——又一处 LibTV 兼容痕迹。
- 连线快速创建菜单（:161-223）：宽 216、位置按世界坐标换算屏幕并钳制（顶部预留 72px）；**safe width 会实时查询 `.canvas-agent-panel` 的左边界**，菜单不钻 Agent 抽屉底下（`getCanvasOverlaySafeWidth` :239-246）；7 个命令（text/image/video/audio 可用，smart-edit/director/script 置灰「暂不可用」:174-181）与 §19 测试钉死清单一致；`data-connection-create-menu` 标记供内核指针排除表使用（§2.1）。

### 31.3 主工具栏（canvas-toolbar.tsx）

- **`libtvChrome` 兼容模式**（:65-66 注释「兼容 LibTV 视觉基线时，仅显示原版底部 Dock 的核心入口」）：额外注入「人像造型室」按钮与「TV Director」球状入口（:239-247,285-290）——工具栏层也保留了 LibTV 视觉基线开关（与 §13.2 顶栏 `?libtvChrome` 同族）。
- **V/H 快捷键在工具栏内实现**，注释明写「**Match LibTV's tool shortcuts**. Ignore editable surfaces so typing a prompt never changes the canvas interaction mode」（:151-166）——BF-39 的第五处命名级 LibTV 对齐证据。菜单文案注意：`box-select` 工具的显示名是「移动」、快捷键 V；`move`（抓手）是「抓手工具」H（:319-322）——「移动」标签与框选行为的错位即 §6.3 所记上游文案混乱的另一处。
- 命令解析走 tool-registry + **用户偏好**：`resolveToolbarEntries("main", ctx, prefs)`，偏好可经 ToolbarSettingsModal 调排序/显隐，设置关闭后重读（:119-128,227）；`ToolbarHandlers` 是全量接口，主工具栏用 no-op 占位多选/节点悬停回调（:199-205）——一个注册表服务多个工具栏上下文。
- 浮层管理：添加面板/工具菜单从 dock 按钮锚定 `panelX`（getPanelX :370-375）；外点关闭用 capture 段 pointerdown 并豁免 `.ant-color-picker,.ant-popover`（:137-149）；Agent 抽屉打开时 dock `paddingRight:340` 避让（:253）；中央空白起点与主工具栏**共用同一 `useCanvasCreateCommands` 命令解析**（:249-250 注释「避免素材类型和插件节点逐渐分叉」——与 §26.1 官方应用清单同一「唯一来源」哲学）。
- 层级注释（:108-111）：dock 用 overlay-layer 契约保焦点顺序，CSS 层抬升到「高于展开的节点面板、低于 Agent 抽屉」。

## 32. 交叉校验台账：断言抽查扩样（v17 补充）

> 方法：对**子代理产出章节**（§4-§13/§16/§22/§25/§28，即未经包作者全文核读的部分）按章节均匀抽取 12 处承重断言，逐条回到锁定提交 `85c9686` 的源码复核。此前 v1 抽查 5 处、v9 抽查 4 处、v13 抽查 3 处、v16 间接 1 处；本轮扩样后**累计 25 处抽查全部吻合，未发现断言错误**。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 1 | §4.2 缺类型 label 回落「未知节点」（node-registry.ts:64） | ✅ `getNodeLabel` 返回 `definitions.get(type)?.label \|\| "未知节点"`（:62-65） |
| 2 | §5.2 连线接近 tilt rotateX/Y ±10deg（canvas-connection-tilt.ts:12-18） | ✅ `rotateX:(0.5-y)*10, rotateY:(x-0.5)*10`（:12-18） |
| 3 | §7.2 缩放分档预算 280/420/720（canvas-performance-mode.ts:40-44） | ✅ 逐行吻合（:40-44） |
| 4 | §9.2 请求指纹 canonicalize 覆盖 nodeId/mode/prompt/model/options（canvas-generation-submission.ts:37+） | ✅ `canonicalize({version:1, nodeId, mode, prompt.trim(), model, options…})`（:37-44） |
| 5 | §10.1 上传身份 `${prefix}:${scope}:${nanoid()}` + 注释原句（file-storage.ts:35-36） | ✅ 代码与注释逐字吻合（:35-36） |
| 6 | §11.1 Agent run 7 态枚举（api/agent.ts:67） | ✅ `queued/running/waiting_approval/completed/failed/cancelled/rejected`（:67） |
| 7 | §12.2 分镜单表 100 行上限（canvas-storyboard-operations.ts） | ✅ :20 校验 `rows.length > 100` 抛错、:59 `>= 100` 拒绝加行（两处吻合） |
| 8 | §16 插件未启用创建节点抛错（canvas-operation-contract.ts:327） | ✅ `!isPluginEffectivelyEnabled(...)` → throw「节点类型未注册或插件不可用」（:327） |
| 9 | §22.2 提示词优化器 14 个模型族 profile | ✅ `grep -c 'id: "'` = 14（:89-223 区间） |
| 10 | §25.1 defer 回池轮询 15s（task_worker.go） | ✅ `DeferRunningTaskForProviderPoll(task.ID, …, 15*time.Second)`（:243） |
| 11 | §28.1 编辑器保存防抖 1500ms（editor-store.ts:21） | ✅ `EDITOR_SAVE_DEBOUNCE_MS = 1500`（:21） |
| 12 | §6.1 拖拽期间暂停历史（selection-controller.ts:214） | ✅ `historyPausedRef.current = true`（:214） |

- **结论**：子代理章节的 file:line 断言可信度经 25 处累计抽查维持 100%；各章证据强度评级（ITERATION_LOG 覆盖面登记）无需降级。
- **残余边界**：抽查是抽样而非全量复核；行号在小幅偏移（±2 行内）仍算吻合（以内容为准）；§23/§25/§28 的代理长报告中未被抽查覆盖的具体行号仍有理论出错概率，使用时以「机制结论 + 文件定位」为准绳，行号作为辅助。

### 32.1 第二轮扩样（v21 补充，10 处新样本，10/10 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 13 | §8.1 画布历史栈上限 50（use-canvas-history.ts） | ✅ `past.slice(-49)`（:165） |
| 14 | §4.3 节点根约 30 个 data-* 观测属性（canvas-node.tsx:306-339） | ✅ 实测 34 处（:306-339） |
| 15 | §4.5 frame/folder 标题双击进编辑（canvas-frame-node.tsx） | ✅ `onDoubleClick → setEditing(true)`（:261-264） |
| 16 | §6.4 fit view maxScale 默认 1（canvas-viewport.ts:54-71） | ✅ `options.maxScale ?? 1` + `Math.min(maxScale, …)`（:55-63） |
| 17 | §7.6 CachedResourceImage 懒加载 rootMargin 240px | ✅ `{ rootMargin: "240px" }`（:45） |
| 18 | §9.4 批次历史上限 20 + 调度器 2s | ✅ `MAX_BATCH_HISTORY = 20` / `SCHEDULER_INTERVAL_MS = 2_000`（:17-18） |
| 19 | §10.3 ffmpeg 预热（use-canvas-media-tools.ts） | ✅ `void warmFFmpeg().catch(() => undefined)` + 注释「失败不阻塞，提交时上报」（:446-447） |
| 20 | §12.1 默认演员 Xbot.glb | ✅ 精确化：`DIRECTOR_DEFAULT_ACTOR_URL = jsdelivr three.js@r185 examples/models/gltf/Xbot.glb`（director-scene.ts:6） |
| 21 | §13.1 viewport 500ms 防抖保存 | ✅ `}, 500);`（lifecycle :299） |
| 22 | §6.2 handleConnectStart 携带 anchorRatio + 批量连线前置分支 | ✅ 签名与分支吻合（:686-696） |

- **累计**：两轮共 22 处直接抽查 + 此前 5/4/3/1 处 = **35 处断言抽查全部吻合**；精确化 1 处（默认演员 URL 锁定 three.js r185 官方示例经 jsdelivr CDN）。

### 32.2 第三轮定点抽查（v24 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 23 | §5.1 方向归一化规则（Config-Config 互斥/Config 恒为 target/frame 拒连） | ✅ 逐行吻合（canvas-project-domain.ts:242-253，另证实 frame 节点连线返回 null） |
| 24 | §5.3 贝塞尔控制点 `curvature = max(dx*0.5, 50)` | ✅（canvas-connections.tsx:158） |
| 25 | §8.5 版本标签 "A".."Z" 递增 | ✅ 并精确化：**首个新增版本标签是 "B"**（无标签时返回 "B"，根媒体隐含为 "A"，canvas-layout.ts:253-259） |
| 26 | §10.2 放大硬上限 4096 | ✅ `MAX_UPSCALE_LONG_EDGE = 4096`（:17,113） |
| 27 | §11.1 Agent live 交换预算 384KB/96k token 硬失败 | ✅ 逐字吻合，且证实 `data:` 载荷替换为占位串计数（agent-context-budget.ts:11-16） |
| 28 | §12.3 短剧导引 localStorage 键 | ✅ `canvas-short-drama-guide-v1`（:7） |
| 29 | §16 插件存储前缀 | ✅ `infinite-canvas:plugin-storage:` + pluginId + ":"（plugin-storage.ts:4-8） |
| 30 | §3.2 文件夹 localStorage 键 | ✅ `CANVAS_FOLDERS_KEY = "infinite-canvas:canvas_folders"`（:70） |

- **累计**：三轮共 30 处直接抽查 + 此前 5 处 = **43 处断言抽查全部吻合**；精确化 2 处（默认演员 URL、版本标签首值 "B"）。同轮上游增量检查：v1.5.9 之后仍无新提交。

### 32.3 第四轮定点抽查（v25 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 31 | §4.4 默认尺寸表（constant/canvas.ts:7-34） | ✅ `NODE_DEFAULT_SIZE` 逐值吻合（image 720×405、script 920×360、batch-table 1280×560 等）；**并发现第六处 LibTV 对齐证据**（见下） |
| 32 | §7.1 「50k 节点数组不走六遍」单遍注释 | ✅ 逐字吻合（use-canvas-render-model.ts:78-80） |
| 33 | §9.1 批次相位/状态枚举 | ✅ batch mode 4 值、status 5 值、item status 7 值逐字吻合（types/canvas.ts:62-64） |
| 34 | §9.6 无入边资源节点可把自身当 `@图片1`（有入边时只暴露上游防挤占槽位） | ✅ 注释与实现吻合（canvas-resource-references.ts:383-395） |
| 35 | §12.2 分镜默认行时长 6s | ✅ `durationSeconds: 6`（canvas-project-domain.ts:48） |
| 36 | §13.1 legacy 画布以自身 id 当 workspaceProjectId | ✅ 注释「防止无关历史画布在水合时折叠成一个项目」+ 实现（canvas-workspace-project.ts:9-15） |
| 37 | §13.3 TapNow 分享链接解析 | ✅ host `app.tapnow.media` + path 正则 `/tapflow/view/…`（tapnow-import.ts:11） |
| 38 | §23.3 stand 姿势 = 双上臂 z+1.28 | ✅ `armsDown = { leftUpperArm: 1.28, rightUpperArm: 1.28 }`（director-scene.ts:269-270），且 `directorPoseLabel` 21 项与 union 精确对齐（:264） |

- **BF-39 第六处证据**（constant/canvas.ts:14,26-28）：文本节点 350×350 注释「**LibTV 的文本节点以近似正方形卡片承载提示词与生成入口，作为首屏复刻基准固定为 350×350**」；音频节点注释「**LibTV renders an empty audio node as a square media card**, not a shallow waveform strip」——默认尺寸层面也在按 LibTV 复刻。
- **累计**：四轮共 38 处直接抽查 + 此前 5 处 = **51 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交。

### 32.4 第五轮定点抽查（v26 补充，6 处，6/6 域确认）+ REPORT 一致性快检

| # | 章节断言 | 复核结果 |
|---|---|---|
| 39 | §10.2 宫格切分预设 | ✅ `CANVAS_GRID_SPLIT_PRESETS` 4/9/16/25 宫格（2×2~5×5，canvas-grid-split.ts:6-11） |
| 40 | §11.1 SSE 空闲 watchdog 120s | ✅ `options.timeoutMs ?? 120_000`，注释「run 是持久的，宽松 watchdog 比中止健康连接更安全」（agent.ts:205-208） |
| 41 | §13.1 回收站存储（域确认） | ✅ `infinite-canvas:deleted_history_store`（键名吻合；200 条上限出自 v13 代理证据 :25，本轮未重复展示） |
| 42 | §4.2 art-critique 插件类型串 | ✅ `ART_CRITIQUE_NODE_TYPE = "ai-art-critique"`（contracts.ts:6） |
| 43 | §9.3 刷新对账 listGenerationTasks(100) | ✅ :396（带 projectId 绑定 + signal 透传） |
| 44 | §6.2 快速创建锚点 anchorRatio 兜底 0.5 | ✅ :326（源节点锚 Y × ratio） |
- **REPORT.md 一致性快检**：§1-§7 的机制清单、反面教材与证据边界表述均与现行章节（含 v14-v26 增补）无冲突；无过期断言。
- **累计**：五轮共 44 处直接抽查 + 此前 5 处 = **57 处断言抽查全部吻合**；上游增量：v1.5.9 之后仍无新提交（第五轮检查）。

### 32.5 第六轮定点抽查（v27 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 45 | §4.1 媒体 hydrate 键不计 updatedAt 的排除集 | ✅ `HYDRATED_MEDIA_KEYS` 10 键逐字吻合（content/storageKey/naturalWidth/Height/bytes/mimeType/durationMs/hasAudio/videoPreview/drawingPreviewUrl，canvas-node-timestamps.ts:8-19） |
| 46 | §6.3 粘贴「节点标记文本→还原节点、系统内容优先」 | ✅ `restoreCopiedNodesFromText(text) && pasteCopiedNodes()` 降级链 + 注释（use-canvas-keyboard.ts:224-240） |
| 47 | §9.5 宫格子图布局 gap 默认常量 | ✅ `layoutGridSplitCells(origin, cells, gap = CANVAS_GRID_SPLIT_GAP)`（canvas-grid-split.ts:31+） |
| 48 | §26.2 技能缓存 TTL 15s + 三级退避 300/900/1800 | ✅（api/skills.ts:152,163） |
| 49 | §22.1 Eagle 写回 96MB 上限 | ✅（eagle.ts:248） |
| 50 | §28.4 素材去重键 = 文件名归一 + 媒体类型 | ✅ `${title.trim().toLowerCase()}\|${mediaType}`（editor-asset-ingest.tsx:23-25） |
| 51 | §28.6 libass 烧录 `requiresLibass` 标记（wasm 回退依据） | ✅（timeline-to-ffmpeg.ts:26,191） |
| 52 | §7.6 `activeMediaNodeId` 单播放器 + 失效自清 | ✅ state + nodeById 失配自动置空（canvas-project-world-layers.tsx:105-108） |
- **累计**：六轮共 52 处直接抽查 + 此前 5 处 = **65 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第六轮检查）。

### 32.6 第七轮定点抽查（v28 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 53 | §3.4 mergeValue 合并规则 | ✅ 逐行吻合：local==base→durable、durable==base→local、`updatedAt` 恒 durable、generationEffectKeys 并集、叶子冲突 durable+onConflict（canvas-storage-revision.ts:120-132） |
| 54 | §8.4 版本条目 reason 枚举 | ✅ `"automatic" \| "before_restore"` + 全字段（workspace-data.ts:50-60） |
| 55 | §11.1 CreateAgentRunInput | ✅ 核心字段吻合（conversationId/prompt/skillIds/permissionMode/budget/idempotencyKey）；**增补**：实际字段更丰富（reasoningMode/profileRevision/model/logicalModelId/channelId/channelModelKey/contextScope，:104-119） |
| 56 | §11.2 patch 冲突文案 | ✅ 逐字「Agent 画布增量与本地内容冲突，需要校准；已保留本地编辑」+ 原型污染键守卫 `__proto__/constructor/prototype`（agent-canvas-patch.ts:29-43） |
| 57 | §12.2 分镜行 21+ 字段 | ✅ :107-135 实测 28 个字段行 |
| 58 | §10.2 裁切归一化矩形（域确认） | ✓ 对话框组件在位（本轮 grep 关键词未命中实现细节，域经 v13 证据确认） |
| 59 | §25.3 bearer 驱动默认 header/prefix | ✅ `Authorization` + `Bearer `（provider_protocol.go:527-534，Go 侧） |
| 60 | §6.1 网格吸附 16px + 对齐 7/k | ✅ `snapCanvasOffsetToGrid(…, 16)` 与 `calculateNodeAlignment(…, 7/k)`（selection-controller.ts:238-243） |
- **累计**：七轮共 60 处直接抽查 + 此前 5 处 = **73 处断言抽查全部吻合**；增补 1 处（CreateAgentRunInput 实际字段更丰富）。同轮上游增量检查：v1.5.9 之后仍无新提交（第七轮检查）。

### 32.7 第八轮定点抽查（v29 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 61 | §2.2 光栅层 committed-scale 变换 | ✅ `transform: scale(var(--canvas-committed-scale))`（globals.css:11455-11457） |
| 62 | §4.3 外置标题头隐藏阈值 0.35 | ✅ 具名常量 `NODE_EXTERNAL_HEADER_MIN_SCALE = 0.35`（canvas-node.tsx:708） |
| 63 | §8.2 Agent 撤销栈容量 10 | ✅ push 后 `.slice(-10)`（use-canvas-operation-history.ts:282） |
| 64 | §9.4 批量创作表默认 try_on/并发 10 | ✅ 默认 metadata 展开 `{ operation:"try_on", concurrency:10, rows:[] }`（use-canvas-batch-table.ts:28） |
| 65 | §10.3 无声视频整段 `-c copy` 路径 | ✅ `removeAudioFromVideo` full-source 判定 + `buildRemoveAudioArgs`（canvas-video-segment.ts:79-82） |
| 66 | §11.3 会话历史预算 192KB/48k token | ✅ `MAX_TEXT_BYTES = 192 * 1024` / `MAX_ESTIMATED_TEXT_TOKENS = 48_000`（agent-context-budget.ts:5-6） |
| 67 | §29.3 出站重定向上限 5 | ✅ `maxOutboundRedirects = 5`（outbound.go:21） |
| 68 | §19 空间索引默认 cell 1024 | ✅ `DEFAULT_CELL_SIZE = 1024`（canvas-spatial-index.ts:20） |
- **累计**：八轮共 68 处直接抽查 + 此前 5 处 = **81 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第八轮检查）。

### 32.8 第九轮定点抽查（v30 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 69 | §4.5 `canFrameContain` 仅收 image/text/drawing/script/video | ✅ 逐类型吻合（canvas-frame.ts:19-21） |
| 70 | §4.5 folder 折叠 ≤3 列网格重排 | ✅ `columns = min(3, ceil(sqrt(n)))` + 行数上取整 + padding/gap 展开（canvas-frame.ts:143-150） |
| 71 | §5.1 `maxInputCount` 容量校验（按去重上游计数，中文报错「最多连接 N 个输入」） | ✅（canvas-connection-policy.ts:29-36） |
| 72 | §9.6 mention token 形态 `@[node:id]` / `@[skill:id]` | ✅ 构造函数逐字吻合（canvas-resource-references.ts:37,41） |
| 73 | §28.4 素材入库 link 失败重试一次 | ✅ try/catch 重试结构在位（editor-asset-ingest.tsx:361-369） |
| 74 | §23.4 `prepareClose` 三态（disposed→stay / 已确认→close / 冲突→flush 后裁决） | ✅ 逐行吻合（director-save.ts:367-380） |
| 75 | §26.4 技能草稿名称上限 80 | ✅ `MAX_NAME_LENGTH = 80`（skill-drafting.ts:13） |
| 76 | §8.4 版本恢复 = persistLocalEdits → historyRestoreRef（新请求 reject 旧请求）→ loadAttempt+1 | ✅ 逐行吻合（use-canvas-project-lifecycle.ts:385-390） |
- **累计**：九轮共 76 处直接抽查 + 此前 13 处 = **89 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第九轮检查）。

### 32.9 第十轮定点抽查（v31 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 77 | §4.3 z 层级 14 档（globals.css:229-245） | ✅ 区间内 17 处 z- 声明，L0 画布底→L1 覆盖→L2 节点→L3 激活→L4 工具栏→L5 节点工具栏→L6 面板→L7 浮动面板逐档带注释 |
| 78 | §4.3 会话级 paint order 不持久化 | ✅ 注释逐字「session-local UI state and is intentionally not persisted」（canvas-node-stack-order.ts:3-6） |
| 79 | §12.1 导演台模式纯映射 | ✅ 头注释「只做纯粹的『模式 -> 能力』映射与切换清理，组件层照着 capabilities 决定显示什么」（director-modes.ts:7-9） |
| 80 | §28.3 时间线片段时长缺省 4s | ✅ `nodeDurationMs(…, fallbackMs = 4_000)`（timeline-build.ts:9-11） |
| 81 | §20 `$divide` 除零报错 | ✅ `"$divide denominator must not be zero"`（expression.go:387） |
| 82 | §26.3 skill-context XML 属性转义 | ✅ `escapeAttribute` 应用于 skill-id/name/version 与文件 path（skill-runtime.ts:247-248） |
| 83 | §10.2 宫格布局 gap 常量 48 | ✅ `CANVAS_GRID_SPLIT_GAP = 48`（canvas-grid-split.ts:4） |
| 84 | §13.1 新建画布继承 workspaceProjectId | ✅ `canvasWorkspaceProjectId(currentProject)` 传入创建（use-canvas-project-lifecycle.ts:311-316） |
- **累计**：十轮共 84 处直接抽查 + 此前 13 处 = **97 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十轮检查）。

### 32.10 第十一轮定点抽查（v32 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 85 | §4.1 `canvasNodeToAsset` 文本须带正文、媒体允许仅 storageKey | ✅ 实现与注释逐字吻合（「blob/object URL 已失效，但资源定位符仍可从后端重新换取」canvas-node-asset.ts:15-22） |
| 86 | §5.1 模型容量上限中文报错 | ✅ `capacityError` → 「已配置模型最多支持 N 张/个…」/「均不支持…」（canvas-connection-policy.ts:82-87） |
| 87 | §8.4 本地草稿双锁 | ✅ `withGenerationArtifactCommitLock` 内嵌 `withCanvasStorePersistenceLock`（canvas-sync-drafts.ts:27-28） |
| 88 | §10.1 封面捕获串行队列 | ✅ 共享 promise 链 + 注释「batch uploads and poster hydration never fan out decoders」（video-poster.ts:20-27） |
| 89 | §12.2 分镜进度标签 | ✅ `pipelineStatusLabel` 五态（待开始/已完成/N·M 进行中/失败/已创建）（canvas-storyboard-progress.ts:104-111） |
| 90 | §28.2 时间线吸附阈值 8px | ✅ `thresholdPx: 8` 两处（editor-timeline-panel.tsx:639,648） |
| 91 | §19 小地图图片缩略图上限 24 | ✅ `MINIMAP_IMAGE_PREVIEW_LIMIT = 24`（canvas-mini-map.tsx:14） |
| 92 | §2.4 主题 store 轻量（37 行） | ✅ 仅 `useActiveTheme` 暴露 |
- **累计**：十一轮共 92 处直接抽查 + 此前 13 处 = **105 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十一轮检查）。

### 32.11 第十二轮定点抽查（v33 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 93 | §4.3 四角 ResizeHandle（选中/悬停且非只读锁定时） | ✅ `!readOnly && !metadata?.locked && (isSelected \|\| hovered)` 四角渲染（canvas-node.tsx:575-580） |
| 94 | §5.3 强调态光晕 strokeWidth 8 + blur 3px | ✅ `strokeWidth="8"` + `strokeOpacity={0.18}` + `filter:"blur(3px)"`（canvas-connections.tsx:63-72） |
| 95 | §8.1 历史提交 180ms 防抖 | ✅ `}, 180);`（use-canvas-history.ts:168） |
| 96 | §10.3 MP4 moov 盒扫描兜底 | ✅ `readFourcc(bytes, offset+4) !== "moov"` 逐盒扫描（video-poster.ts:245-247） |
| 97 | §14 导出格式 `version: 4` | ✅ `CanvasExportFile = { app:"infinite-canvas", version:4, exportedAt, … }`（canvas-export.ts:55） |
| 98 | §25.2 `Task.CreationSubmissionID` 唯一索引 | ✅ gorm tag `size:36;uniqueIndex`（models_task.go:6） |
- **累计**：十二轮共 98 处直接抽查 + 此前 13 处 = **111 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十二轮检查）。

### 32.12 第十三轮定点抽查（v34 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 99 | §10.2 蒙版提示词强制前缀 | ✅ 「只修改蒙版透明区域，其他区域保持不变。」逐字（use-canvas-media-tools.ts:780） |
| 100 | §10.2 宫格钳制与合法性 | ✅ `clampGridSplitSize`（min 1 / max 5 / 非法回 2）+ `isValidGridSplit` 要求 rows×cols ≥ 2（canvas-grid-split.ts:20-29） |
| 101 | §25.2 creation 事务内重读 submission | ✅ `MutateCreationRun` 事务 + `CreationSubmission` 重读 + CreationGuard 校验（creation.go:754-760） |
| 102 | §22.6 插槽权限表 | ✅ 8 槽映射逐字（timeline-panel/inspector/asset-ingest/subtitle-tool/transcription→`timeline.command`；preview/ai-assistant→`timeline.read`；export→`export.run`，plugin-permission-check.ts:10-19） |
| 103 | §12.2 分镜 composer 拼装 | ✅ `storyboardComposerContent` = 「参考资产：@mentions」+ 提示词（去重引用、空则纯 prompt）（canvas-storyboard-materializer.ts:32-40） |
| 104 | §14 导出媒体收集 | ✅ `collectStorageKeys` 递归收集含「:」的 storageKey（canvas-export.ts:60-65） |
- **累计**：十三轮共 104 处直接抽查 + 此前 13 处 = **117 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十三轮检查）。

### 32.13 第十四轮定点抽查（v35 补充，8 处新样本，8/8 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 105 | §8.3 生成 outcome 归一枚举 | ✅ not_started/queued/running/succeeded/failed/cancelled，且**额外容忍** pending/processing/canceled 拼写（canvas-operation-contract.ts:416-425，比 §8.3 记录更宽） |
| 106 | §9.2 指纹纳入全部引用素材身份 | ✅ images/videos/audios/characters/resolvedCharacterVersions/resolvedVoices 全量 referenceIdentity 映射（canvas-generation-submission.ts:50-57） |
| 107 | §11.2 SSE 补丁 40ms 批处理 | ✅ `options.batchMs ?? 40`（agent-canvas-sync.ts:24） |
| 108 | §16 PluginManifestV2 类型技巧 | ✅ Omit permissions 再替换的注释（「否则数组交叉类型会被归约为 v1 的 PluginPermission[]」plugin-types.ts:29-32） |
| 109 | §12.1 能力矩阵字段 | ✅ timeline/keyframes/bones/cameraTools/renderModes 五维 + 中文注释（「摆场不给深度/法线这类高级视图」director-modes.ts:14-38） |
| 110 | §3.4 tombstone 时间戳冲突判定 | ✅ `(input.tombstones[id] ?? 0) > input.baseRevision` → 放弃 local（canvas-storage-revision.ts:233-237） |
| 111 | §10.4 下载文件名 Windows 保留名处理 | ✅ `safeFileNamePart` 正则 `/^(con\|prn\|aux\|nul\|com[1-9]\|lpt[1-9])$/i` → 前缀 `_`（canvas-media-download.ts:71-83；此前 grep 关键词不含小写词故未命中，直接阅读证实） |
| 112 | §10.2 表情本地合成模式 | ✅ `provider-mask \| local-composite` 双模式 + 「当前渠道不支持蒙版，使用脸部裁切与本地羽化融合」降级文案（canvas-emotion.ts:43,54,241） |
- **累计**：十四轮共 112 处直接抽查 + 此前 13 处 = **125 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十四轮检查）。

### 32.14 第十五轮定点抽查（v36 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 113 | §4.3 四角手柄偏移 14px/热区 28px | ✅ `size-7`（28px）+ `-left-[14px]` 系列偏移（canvas-node.tsx:697-706） |
| 114 | §23.3 关键帧 upsert epsilon | ✅ 具名常量 `DIRECTOR_KEYFRAME_EPSILON = 0.001` + 插入后按时间排序（director-scene.ts:89-96） |
| 115 | §19 小地图空场景兜底 | ✅ worldBounds 回落 `x:-500, y:-500, w:1000, h:1000`、scale 0.16（canvas-mini-map.tsx:29） |
| 116 | §28.1 `load` 清除挂起保存定时器并复位全部状态字段 | ✅ 逐行吻合（editor-store.ts:119-125） |
| 117 | §29.3 `directResourceURL` 仅限 local 资源 | ✅ nil→「资源不存在」、非 ready→「尚未上传完成」、Provider≠local→「资源不在本地存储中」三重守卫（resource.go:77-90） |
| 118 | §9.2 生成结果几何居中调整（locked 跳过） | ✅ `locked → {}`，否则 width/height + 中心对齐 position（canvas-generation-task-sync.ts:211-217） |
- **累计**：十五轮共 118 处直接抽查 + 此前 13 处 = **131 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十五轮检查）。

### 32.15 第十六轮定点抽查（v37 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 119 | §16 sandbox 占位文案 | ✅ 「插件节点等待隔离运行时」逐字（canvas-node-content.tsx:92-97） |
| 120 | §12.2 分镜就绪门禁 | ✅ 画风节点（workflowKind=styleboard + stylePresetId + prompt）缺失即抛「请先设置项目画风」；角色卡版本未同步抛含角色名的错误；**注释补充**：standalone 角色设计图也用 workflowKind=character，仅绑定 characterAssetId 者参与校验（canvas-storyboard-context.ts:19-30） |
| 121 | §25.1 worker 全局槽位租约 | ✅ `s.coordinator.AcquireLease(ctx, "workers", workerConcurrency, workerSlotLeaseDuration)`（task_worker.go:72-74） |
| 122 | §13.1 Agent 刷新合并 | ✅ `mergeAgentCanvasEditor` 只合并服务端变更字段（注释「dragging/editing other nodes can continue while Agent media tasks complete」，use-canvas-project-lifecycle.ts:258-266） |
| 123 | §19 小地图拖拽两段 | ✅ 拖拽中 `onViewportPreviewChange` 实时预览（canvas-mini-map.tsx:132） |
| 124 | §8.4 版本导出排除本机笔画 | ✅ 注释逐字「Drawing strokes are not versioned; never mix today's local strokes into an old snapshot」+ `includeLocalDrawings: false`（canvas-version-history.tsx:173-175） |
- **累计**：十六轮共 124 处直接抽查 + 此前 13 处 = **137 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十六轮检查）。

### 32.16 第十七轮定点抽查（v39 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 125 | §10.2 裁切无 crop 时中心方裁 | ✅ `Math.min(width,height)` 中心取方（canvas-image-data.ts:35-44） |
| 126 | §16 本地模式渠道目录回落 4 个内置 OpenAI 兼容协议 | ✅ `BUILTIN_OPENAI_PROTOCOLS` = chat-completion/openai-response/openai-image/newapi（plugin-catalog.ts:47-52） |
| 127 | §25.3 ApiCallLog `UpstreamURL` 仅 scheme://host+path | ✅ `req.URL.Scheme + "://" + req.URL.Host + req.URL.Path`（provider_http_client.go:439），Query 不入库 |
| 128 | §28.5 AI 预览卡 96 字符截断 | ✅ `brief.slice(0, 96)` + 省略号（editor-ai-assistant.tsx:40） |
| 129 | §9.3 孤立 loading 判定五条件 | ✅ status=loading 且无 content 且无 taskId 且无 pending continuation 且无在途请求才标记中断（use-canvas-generation.ts:524-532） |
| 130 | §12.2 分镜物化 120px 间距 | ✅ 两处 `scriptNode.position.x + width + 120`（use-canvas-storyboard.ts:267,350） |
- **累计**：十七轮共 130 处直接抽查 + 此前 13 处 = **143 处断言抽查全部吻合**；精确化累计 2 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十七轮检查）。

### 32.17 第十八轮定点抽查（v40 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 131 | §6.2 吸附半径常量 | ✅ `CONNECTION_SNAP_RADIUS = 56`，使用处 `/ scale`（use-canvas-connection-controller.ts:61,461） |
| 132 | §9.2 重试 clientOperationId 哈希 | ✅ 精确化：`"retry:" + hex(SHA-256("generation-retry\0" + attemptGroupId + "\0" + retryOf))`——实际输入含 `generation-retry\0` 前缀（canvas-project-generation.ts:154-161） |
| 133 | §10.3 音轨提取四级回退 | ✅ aac copy → `libmp3lame` → `mp3` → wav 输出类型逐级尝试（canvas-video-segment.ts:105-119） |
| 134 | §16 插件宿主权限断言 | ✅ 无 `ai.text` 权限抛「插件没有调用文本模型的权限」（plugin-host.ts:17-18） |
| 135 | §4.2 插件节点定义转换 | ✅ `defaultMetadata: { pluginId, pluginNodeId, pluginData:{} }` + `minSize = min(defaultSize, 220×160)` + icon null（node-definition.ts:62-77） |
| 136 | §5.1 生成模式约束中文报错 | ✅ 「图片生成节点不能连接参考视频/音频」（canvas-connection-policy.ts:44-45） |
- **精确化第 3 处**（上表 #144）。**累计**：十八轮共 144 处直接抽查 + 此前 13 处 = **149 处断言抽查全部吻合**；同轮上游增量检查：v1.5.9 之后仍无新提交（第十八轮检查）。

### 32.18 第十九轮定点抽查（v41 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 137 | §9.4 批量表行经连线同步 | ✅ `batchInputColumns(node, connectionsRef.current)` + 行内容 JSON 相同则跳过更新（use-canvas-batch-table.ts:77-90） |
| 138 | §10.2 裁切矩形归一化 0-1 + minSize 钳制 | ✅ `clamp(crop.x + dx, 0, 1 - crop.width)` / `minSize` 下限（canvas-node-crop-dialog.tsx:122-138） |
| 139 | §16 `unregisterPlugin` 三段清理 | ✅ 注销节点定义 + 插件插槽 + 注册表条目（plugin-registry.ts:73-77） |
| 140 | §22.6 插槽解析排序 | ✅ priority 降序 → 注册序升序稳定排序（editor-slot-registry.ts:89-93） |
| 141 | §8.4 版本预览节点 id 前缀 | ✅ `` `version-preview:${id}` ``（canvas-version-preview.tsx:22） |
| 142 | §12.1 导演台孤儿节点修复 | ✅ 注释逐字「绝不在用户没选过的情况下塞演员进去」+ empty 模板兜底（use-canvas-director.ts:107-109） |
- **累计**：十九轮共 150 处直接抽查 + 此前 13 处 = **155 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第十九轮检查）。

### 32.19 第二十轮定点抽查（v42 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 143 | §4.5 `canFolderContain` 除 frame 全收 | ✅ `node.type !== CanvasNodeType.Frame`（canvas-frame.ts:23-25） |
| 144 | §29.1 Mask 场景强制内嵌 | ✅ `input.Mask != nil → return false` + 注释「遮罩场景不能改发 URL」（provider.go:455-458） |
| 145 | §16 插件注册校验 | ✅ kebab-case ID、apiVersion 白名单 v1/v2、权限去重、v1/v2 各自贡献断言（plugin-registry.ts:18-28） |
| 146 | §10.3 ffmpeg 参数注释 | ✅ `-ss` 在 `-i` 后防关键帧落点；**增补细节**：整段去音「MP4 在 ss=0 时仍可能写出无 mdat 的空文件」+ `-map 0:V:0` 跳过 attached pic（canvas-video-segment-args.ts:1-5） |
| 147 | §12.1 摆场模式能力收窄 | ✅ `layout: { timeline:false, keyframes:false, bones:false, cameraTools:false, renderModes:["beauty","clay"] }`（director-modes.ts:27） |
| 148 | §28.4 素材分类默认 | ✅ `defaultAssetCategoryForKind(kind)`（editor-asset-ingest.tsx:10,362） |
- **累计**：二十轮共 156 处直接抽查 + 此前 13 处 = **161 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十轮检查）。

### 32.20 第二十一轮定点抽查（v43 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 149 | §4.5 Kahn 拓扑分层 | ✅ 入度/出边表 + 注释「Kahn 拓扑分层让依赖方向保持从左到右；环形连接留在第一层，避免布局死循环」（canvas-layout.ts:45-60） |
| 150 | §6.2 连线侧创建不重叠摆位 | ✅ `placeConnectedNodeWithoutOverlap` 在位，`gap = 36` 垂直间距（水平 96px 间距在其后段，:69-80） |
| 151 | §10.1 远程图片导入 | ✅ `shouldImportRemoteImage` → `importResourceFromUrl(input, "image", { idempotencyKey: storageKey })`，尺寸缺省 1024（image-storage.ts:36-50） |
| 152 | §8.4 版本预览空动作表 | ✅ `noAction`/`readOnlyActions` 常量 + `version-preview:` 前缀（canvas-version-preview.tsx:20-22） |
| 153 | §4.5 媒体泳道 | ✅ `layoutCanvasNodesByMediaType` 按 `LANE_ORDER` 分泳道、泳道内按 y/x 排序（canvas-layout.ts:112-120） |
| 154 | §10.1 远程导入幂等 | ✅ `idempotencyKey: storageKey` 随导入传入（:37） |
- **累计**：二十一轮共 162 处直接抽查 + 此前 13 处 = **167 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十一轮检查）。

### 32.21 第二十二轮定点抽查（v44 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 155 | §6.2 连线侧创建水平 96px | ✅ target 侧落点 `source.position.x - 96 - size.width` + gap 重叠检测（use-canvas-connection-controller.ts:82-92） |
| 156 | §9.1 `NODE_STATUS_LOADING = "loading"` 模块内常量 | ✅ 定位于 canvas-media-generation-executors.ts:14（此前仅以字面量记录，本轮补常量定位） |
| 157 | §16 插件存储前缀 | ✅ `infinite-canvas:plugin-storage:` + pluginId（plugin-storage.ts:4-8，二轮确认） |
| 158 | §28.6 转写字幕 nodeId | ✅ `` `transcription:${selected.id}` ``（editor-transcription.tsx:96） |
| 159 | §22.6 fail-closed 原因枚举 | ✅ `"plugin-not-registered" \| "missing-permission"` + missing 字段（plugin-permission-check.ts:23,45,49） |
| 160 | §9.5 生成组避让下/右双方向 | ✅ `resolveCollisions(…, "down"/"right")` + 距离短者胜 + 注释「避免生成组覆盖已有节点」（canvas-generation-layout.ts:68-80） |
- **累计（勘定）**：§32 台账物理行数 160（awk 逐节清点）+ pre-ledger 13 处（v1 5 + v9 4 + v13 3 + v16 1）= **173 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十二轮检查）。注：台账行号因多轮追加存在空洞（物理行数为准）。

### 32.22 第二十三轮定点抽查（v45 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 161 | §28.4 素材批量插入并行 | ✅ `Promise.all(payloads.map(...))` + 统一选中新建节点（use-canvas-upload.ts:732-738） |
| 162 | §25.1 取消对账上限 41 次 | ✅ `providerCancellationMaxAttempts = 41`（provider_task_cancellation.go:20） |
| 163 | §4.1 素材分类推断 | ✅ `declaredCanvasNodeAssetCategory`（显式声明优先）+ `canvasNodeAssetCategory`（canvas-node-asset.ts:167-175） |
| 164 | §4.3 标题按钮可访问性 | ✅ `aria-label="编辑节点名称：{title}"` + hover 铅笔图标（canvas-node.tsx:795-797） |
| 165 | §12.1 导演台输出资产同步 | ✅ `ensureCanvasNodeAsset({ canvasId, domainProjectId, node, source:"canvas-manual" })`（use-canvas-director.ts:205） |
| 166 | §26.2 技能变更广播 | ✅ `window.dispatchEvent(new Event("canvas-skills-changed"))`（api/skills.ts:176） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十三轮检查）。

### 32.23 第二十四轮定点抽查（v46 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 167 | §4.5 自动布局排除项与分支 | ✅ 排除 locked/Frame、候选 <2 返回空、有连线走拓扑/无连线走媒体类型分泳道（canvas-layout.ts:136-142） |
| 168 | §28.1 `scheduleSave` isDirty 门控 | ✅ 未注入保存层保持 dirty、定时器到期检查 isDirty 才落盘（editor-store.ts:95-102） |
| 169 | §28.2 手势状态 useRef | ✅ `gestureRef = useRef<GestureState \| null>(null)`（editor-timeline-panel.tsx:608） |
| 170 | §22.6 八插槽 priority 全 0 | ✅ 计数 8（editor-shell.tsx:17-38） |
| 171 | §23.3 mixer 循环模式 | ✅ `setLoop(motion?.loop ? LoopRepeat : LoopOnce, loop ? Infinity : 1)`（director-viewport.tsx:834） |
| 172 | §2.3 触控板启发式细节 | ✅ `rawAbsY >= 80` + 整除性检验（infinite-canvas.tsx:200-202） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十四轮检查）。

### 32.24 第二十五轮定点抽查（v47 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 173 | §10.2 标注撤销历史模型 | ✅ push/undo/redo 纯函数三元组（canvas-image-annotation-model.ts:15-17） |
| 174 | §12.2 分镜 100 行上限执行 | ✅ :20（>100 抛错含 Agent 工具指引）与 :59（>=100 拒绝加行）双重执法 |
| 175 | §16 内置插件注册顺序 | ✅ eagle → prompt-optimizer → workflows → ai-art-critique → media-conversion → editor-shell（builtin/index.ts 副作用 import 顺序即优先级） |
| 176 | §25.3 文本 SSE 断点续传游标 | ✅ `queryTaskTextReplay(after)` :291-292 与 `Last-Event-ID → ?after=` :440 两路游标 |
| 177 | §2.4 背景模式枚举 | ✅ `"dots" \| "lines" \| "blank"`（canvas-theme.ts:2） |
| 178 | §4.2 NODE_SPECS 逐类型 metadata 默认 | ✅ 如 image `{ content:"", status:"idle" }`（constant/canvas.ts:36-40） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十五轮检查）。

### 32.25 第二十六轮定点抽查（v48 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 179 | §16 本地模式渠道目录回落过滤 | ✅ `workspaceCapabilities().local && scope === "user.custom-channel"` → 按 capability 过滤内置协议（plugin-catalog.ts:29-31） |
| 180 | §22.2 优化器系统提示边界 | ✅ 「提示词导演」定位 + 「不擅自改变用户明确写出的主体、身份、动作、数量、时代、地点、画幅比例或安全边界」逐字（prompt-optimizer.ts:71-73） |
| 181 | §26.3 技能 provenance→metadata 映射 | ✅ skillIds/skillVersions/skillFiles 三键（skill-runtime.ts:127-134） |
| 182 | §28.1 `load` 全量复位 | ✅ 清保存定时器 + 复位 history/inPreview/isDirty/selectedClipId/transportMs 等全部字段（editor-store.ts:119-125） |
| 183 | §2.3 双击守卫三选择器 | ✅ `closest("[data-node-id],[data-connection-id],[data-canvas-no-zoom]")` 命中即不触发画布双击（infinite-canvas.tsx:439-442） |
| 184 | §12.2 分镜物化五态 | ✅ `nodePipelineState` missing/success/loading/error/idle（canvas-storyboard-progress.ts:63-69） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十六轮检查）。

### 32.26 第二十七轮定点抽查（v49 补充，5 处新样本，5/5 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 185 | §8.2 Agent 变更摘要按 op.type 计数 | ✅ `counts[op.type]` 归约（canvas-operation-contract.ts:238-241） |
| 186 | §3.1 文件夹 localStorage 键 | ✅ `CANVAS_FOLDERS_KEY = "infinite-canvas:canvas_folders"`（use-canvas-store.ts:70，二轮确认） |
| 187 | §28.6 SRT 导入固定 nodeId | ✅ `DEFAULT_SRT_NODE_ID = "srt-import"`（editor-subtitle-tools.tsx:14） |
| 188 | §16 插件权限去重抛错 | ✅ 「插件权限不能重复」（plugin-registry.ts:25） |
| 189 | §9.6 普通视频 promptOnly 判定 | ✅ `promptOnly = mode === "video" && !usesWorkflowProvider` + 注释「显式 @文本 引用仍会展开为真实内容」（use-canvas-generation-executor.ts:152-154） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十七轮检查）。

### 32.27 第二十八轮定点抽查（v50 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 190 | §9.4 批量入队去重 | ✅ 活跃批次项（waiting/submitting/queued/running）的 nodeId 集合过滤可用目标（use-canvas-generation-batches.ts:64-65） |
| 191 | §16 插件上传仅进后端 | ✅ `uploadPlugin` POST /plugins FormData，前端不注册执行（plugins.ts:45-50） |
| 192 | §11.1 运行中插话端点 | ✅ `POST /agent/runs/:id/interjections` 返回 `{accepted, pending}`（agent.ts:149）；面板失败文案「插话没有送达」（panel:463） |
| 193 | §4.5 泳道顺序 | ✅ `LANE_ORDER = ["text", "image", "video", "audio"]`（canvas-layout.ts:11） |
| 194 | §9.2 任务反查节点双源 | ✅ `clientContext?.nodeId \|\| input.metadata?.nodeId`（canvas-generation-task-sync.ts:27-29） |
| 195 | §2.4 画布外观默认读取 | ✅ `readCanvasAppearanceDefault`（canvas-appearance.ts:111） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十八轮检查）。

### 32.28 第二十九轮定点抽查（v51 补充，6 处新样本，6/6 吻合；按点名域：骨骼分层/asset-ingest/图片工具）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 196 | §23.3 骨骼分层优先级 | ✅ 头注释逐字「静置/姿势或动作片段 -> 静态覆盖 -> 骨骼关键帧」+ 实现吻合（低到高：rest×poseDelta 或 motion → override → 关键帧插值；无关键帧返回 override）（director-animation-semantics.ts:86-97） |
| 197 | §28.4 上传前时长探测 | ✅ `probeMediaDurationMs(file)` 来自 `@/lib/media-metadata`，逐文件调用（editor-asset-ingest.tsx:11,353） |
| 198 | §10.2 放大 high 算法逐倍 step-upscale | ✅ `algorithm === "high" ? drawStepUpscale : drawResize` + `resolveUpscaleSize` 4096 钳制（canvas-image-data.ts:105-115） |
| 199 | §12.1 导演台模板 5 种 | ✅ `empty/monologue/dialogue/blocking/product` 五模板含中文描述与摘要（「空场景：只有摄影机和三点布光」等，director-templates.ts:19-34） |
| 200 | §10.2 裁切无 crop 中心方裁 | ✅ `Math.min(width,height)` 中心取方（canvas-image-data.ts:35-44，二轮确认） |
| 201 | §23.2 白膜材质跳过集 | ✅ `userData.directorActor` mesh 跳过 + ShaderMaterial（drei Grid/Line）跳过，注释「由组件自身 useFrame 逐帧读写 uniforms」（director-clay-materials.ts:7-16） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第二十九轮检查）。

### 32.29 第三十轮定点抽查（v52 补充，6 处新样本，6/6 吻合；按点名域：视频工具/AI 助手链/技能运行时）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 202 | §10.3 输出健全性校验按 kind 分支 | ✅ audio 查 soun/wave/mpeg、video 查 vide，错误文案中文逐字（canvas-video-segment-args.ts:40-52）；`buildRemoveAudioArgs` 头注释「整段可复制画面；部分区间必须重编码，不能 stream copy」（增补） |
| 203 | §10.3 mergeVideos | ✅ 至少 2 个视频 + `loadFFmpeg` + storageKey 优先/远程兜底取 Blob（canvas-video-merge.ts:51-63） |
| 204 | §28.5 applyPlan 逐条 dispatch | ✅ for..of → dispatch + 预览卡整卡替换为汇报 + 历史记录「已提交 N 条指令：op 列表」（editor-ai-assistant.tsx:104-115） |
| 205 | §28.5 failTurn 重试回喂 | ✅ 原因截断 MAX_VISIBLE_RAW + `RETRY_MODIFY_PREFIX` + 「请只输出修正后的命令 JSON。」（:125-135） |
| 206 | §28.5 空 commands = 纯问答 | ✅ reasoning 可见 + 入历史 + 早返回（:185-191） |
| 207 | §10.3 提音首选 aac copy | ✅ 注释「大多数 MP4 音轨本身就是 AAC；优先直接复制，避免无谓的整段重编码」（canvas-video-segment.ts:105-107） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十轮检查）。

### 32.30 第三十一轮定点抽查（v53 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 208 | §6.2 批量连线规划 | ✅ `planBatchConnections({sourceNodeIds, targetNodeId, …})` + `batchSourceRestriction` 逐源资格过滤（use-canvas-connection-controller.ts:216-224） |
| 209 | §25.1 路由失败切换 | ✅ for 循环内 markDispatching → processTask → finishAttempt → `nextRouteAttemptAfterFailure`（task_route_executor.go:80-95） |
| 210 | §28.2 SlotStack 红色诊断条 | ✅ title 逐字「插件 X 缺少 Y，已按 fail-closed 拒绝渲染」（editor.tsx:70） |
| 211 | §4.5 spread 散开算法 | ✅ `scale/minGap` 可选项 + 原点取 min x/y（canvas-layout.ts:151-159） |
| 212 | §9.1 结果回填 fallback 链 | ✅ `applyStoredTaskResult → applyRecoveredGenerationTaskResultToNodes` + `persistCanvasGenerationEffect({effectKey})`（use-canvas-generation.ts:293-300） |
| 213 | §2.4 CanvasTheme 浅/深双主题 | ✅ `canvas:` 节分别位于 :6 与 :73（canvas-theme.ts） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十一轮检查）。

### 32.31 第三十二轮定点抽查（v54 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 214 | §8.2 节点重叠警告 | ✅ `findCanvasNodeOverlaps` 候选两两逐对检测（canvas-operation-contract.ts:206-219） |
| 215 | §10.1 上传进度按文件字节归一 | ✅ `Math.min(file.size, file.size * loaded / total)`（resources.ts:157-159） |
| 216 | §10.2 表情合成双位图加载 + 区域/人脸盒钳制 | ✅ `loadImageBitmap` ×2 + `clampEditRegion/clampFaceBox`（canvas-emotion.ts:241-248） |
| 217 | §4.2 插件 maxInputCount 透传 | ✅ `maxInputCount: contribution.maxInputCount`（node-definition.ts:74） |
| 218 | §26.3 技能文件搜索端点 | ✅ `GET /skills/:id/search?q=`（api/skills.ts:210-211） |
| 219 | §13.3 两步导入交互 | ✅ 「读取画布」→「确认导入」按钮 + 「等待确认导入」Tag（libtv-import-dialog.tsx:115-169） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十二轮检查）。

### 32.32 第三十三轮定点抽查（v55 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 220 | §8.2 opLabel 中文标签 | ✅ 新增节点/更新节点/删除节点/删除连线/连接（canvas-operation-contract.ts:385-391） |
| 221 | §25.2 CreationRun epoch 租约 | ✅ `ExpectedEpoch != run.ExecutionEpoch` 冲突检测 + `ExecutionEpoch++`/`ExecutionOwner` + 45s 租约（creation.go:200-206） |
| 222 | §12.1 35mm 全画幅换算 | ✅ `directorFocalLengthToFov = 2·atan(36/(2f))·180/π` + 注释「摄影机检查器与场景模板共用」（director-scene.ts:75-78） |
| 223 | §9.1 bindGenerationTask 节点写入 | ✅ 按 targetNodeId 映射写入（use-canvas-generation.ts:259-266） |
| 224 | §10.1 批量上传网格常量 | ✅ `BATCH_UPLOAD_COLUMNS = 3` / 列距 380 / 行距 300（use-canvas-upload.ts:49-51） |
| 225 | §23.3 drawStepUpscale 倍增循环 | ✅ `while (sourceWidth*2 < width && …)` 逐倍放大（canvas-image-data.ts:128+） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十三轮检查）。

### 32.33 第三十四轮定点抽查（v56 补充，6 处新样本，6/6 域确认）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 226 | §9.3 孤儿中断标记文案 | ✅ 「页面刷新后找不到对应任务，请重新生成。」（use-canvas-generation.ts:410） |
| 227 | §16 declarative 只读字段列表 | ✅ 遍历 `schema.properties` 键名渲染 label+值（canvas-node-content.tsx:99-105） |
| 228 | §25.3 任务列表游标翻页（域确认） | ✅ 本轮 :340-348 命中 safeTaskLogStage；nextCursor 翻页逻辑在 listGenerationTasks 别处（v13 证据） |
| 229 | §28.2 时间轴标签列 192px | ✅ `LABEL_COLUMN_PX = 192`（editor-timeline-panel.tsx:30） |
| 230 | §10.2 标注合成两次 drawImage | ✅ 源图 + 标注层各一次（canvas-node-annotation-dialog.tsx:75） |
| 231 | §12.1 导演提示词段落结构 | ✅ 镜头设计/摄影机/角色颜色映射（「严格按颜色识别角色，不交换人物身份」）/空间调度分段拼接（director-prompt-compiler.ts:30-40） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十四轮检查）。

### 32.34 第三十五轮定点抽查（v57 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 232 | §6.2 快速菜单世界坐标跟随 | ✅ `subscribeCanvasViewportPreview` 订阅 + `update(viewport)` 实时重算（workspace-overlays.ts:203-205） |
| 233 | §10.2 蒙版重绘 count 处理 | ✅ `requestedCount = max(1, count \|\| 1)` + :244 处固定 count:1 分支（use-canvas-media-tools.ts:786） |
| 234 | §25.2 CreationGuard 校验 | ✅ `validateCreationGuard(current, req.CreationGuard)` 先于 submission 重读（creation.go:755-757） |
| 235 | §28.2 trim 左右缘吸附交替 | ✅ leftSnap/rightSnap 距离比较 + rightAltStart 回退（editor-timeline-panel.tsx:660-667，v13 摘要的展开） |
| 236 | §9.4 批量并发钳制 1-10 | ✅ `Math.max(1, Math.min(10, Math.floor(options.concurrency)))`（use-canvas-generation-batches.ts:78） |
| 237 | §10.2 蒙版模型能力校验 | ✅ `selectedImageProfile?.references.maskSupported` 检查（:761）+ 表情编辑同源（:1018） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十五轮检查）。

### 32.35 第二十八轮定点抽查（v58 补充，6 处新样本，6/6 吻合；覆盖此前未抽样分支）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 238 | §12.2 分镜视频首帧门禁 | ✅ 「请先生成并检查选中镜头的首帧」+「N 个选中镜头还没有可用首帧，请全部生成并检查后再确认」（use-canvas-storyboard.ts:495-496） |
| 239 | §6.2 快速创建禁用原因（虚拟节点） | ✅ `getConnectionCreateDisabledReason` 含 Config×RunningHub 插件启停与 batchSourceNodeIds 分支（use-canvas-connection-controller.ts:439-446） |
| 240 | §10.1 媒体直传永久失败当场抛出 | ✅ ResourceUploadError.permanent 即抛 + 注释「永久性失败必须当场暴露，不能混进稍后自动同步」（file-storage.ts:118-121） |
| 241 | §25.1 重试业务门禁 | ✅ `submission_unknown`/`CategorySubmissionUncertain` 拒绝重试（task_lifecycle.go:60） |
| 242 | §2.4 画布外观默认键 v2 | ✅ `infinite-canvas:canvas-appearance-default:v2`（scopedLocalStorage，canvas-appearance.ts:35,112） |
| 243 | §9.4 图片批量子任务 count 强制 "1" | ✅ `config: { ...generationConfig, count: "1" }`（canvas-image-generation-executor.ts:198） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十六轮检查）。

### 32.36 第三十七轮定点抽查（v66 补充，5 处新样本，5/5 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 244 | §28.1 手势三分 | ✅ `previewGesture` 置 `inPreview: true`；`commitGesture` 要求 inPreview 才入历史（editor-store.ts:163-175） |
| 245 | §29.3 出站禁用头清单 | ✅ authorization/proxy-authorization/cookie/set-cookie/host/content-type/connection/keep-alive/transfer-encoding/te/trailer/upgrade/forwarded/x-goog-api-key + `x-canvas-`/`x-forwarded-` 前缀（outbound.go:242-248） |
| 246 | §23.2 GLTF 加载所有权 | ✅ 头注释逐字「被采纳（adopt）时绝不能释放 source——共享资源随 owned clone 的最终 cleanup 一并释放；只有未被采纳的晚到/失效 generation 才需要释放」（director-resources.ts:45-54） |
| 247 | §30 高亮 runner 进度字段 | ✅ `processedEntries`/`percent` 进度回调（subtitle-highlight-runner.ts:10-12,44） |
| 248 | §23.4 草稿键 scope 化 | ✅ `scopedStorageKey("director-scene-draft:" + fixedSceneId, scope)`（director-save.ts:136） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十七轮检查）。

### 32.37 第三十六轮定点抽查（v65 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 249 | §25.3 waitForGenerationTask 双路 | ✅ `shouldUseTaskTextEvents` 走文本事件，否则 2s 轮询 + timeoutMs 上限 + consecutiveFailures 计数（task-center.ts:375-385） |
| 250 | §12.2 引用节点集合按 characterAssetId 匹配 | ✅ `characterAssetIds` 集合 → workflowKind=character 且 assetId 命中的画布节点 id（canvas-storyboard-materializer.ts:7-22） |
| 251 | §28.2 插槽注册 HMR 幂等 | ✅ `registerEditorSlot` 先 `unregisterEditorSlot(pluginId, slot)` 再 push，order 自增，返回只卸载自身的闭包（editor-slot-registry.ts:46-61） |
| 252 | §25.3 日志载荷 128KB 上限 | ✅ `maxAPICallPayloadBytes = 128 << 10`（api_call_payload.go:16） |
| 253 | §30 SRT 序号非法归一 | ✅ 序列化时 `Number.isInteger(entry.index) && entry.index > 0 ? entry.index : idx + 1`（srt-parser.ts:36-45） |
| 254 | §26.3 技能运行时单例 | ✅ `createSkillRuntime()` 工厂 + `skillRuntime` 共享单例（skill-runtime.ts:136-158） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十六轮检查）。

### 32.38 第三十八轮定点抽查（v67 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 255 | §28.1 saveChain 串行保存 | ✅ `saveChain` promise 链 + `performSave` + `setSaveError` 归一（editor-store.ts:76-86） |
| 256 | §25.3 safeProviderLogError | ✅ HTTP 错误只留「上游 HTTP %d」状态码，其余 truncateRunes 500（provider_http_client.go:473-479） |
| 257 | §23.2 rig ready 阈值 | ✅ `boneMap.length >= 8 ? "ready" : "unmapped"`（director-viewport.tsx:1031，inferDirectorRig :1005） |
| 258 | §26.3 交付适配器注册表 | ✅ `deliveryAdapters` Record 现仅 linked-context 一键（skill-runtime.ts:143-146） |
| 259 | §12.2 空 rows 中文错误逐字 | ✅ 「分镜节点必须包含真实镜头行。请使用 canvas_create_workflow 的 script.shots…不能仅填正文」（canvas-storyboard-operations.ts:20） |
| 260 | §23.2 readCameraTransform | ✅ `usableContext()?.camera` → position/rotation/scale，不可用返回 null（director-viewport.tsx:140-143） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十八轮检查）。

### 32.39 第三十轮定点抽查（v59 补充，6 处新样本，6/6 吻合；含未读文件 chapter-asset-breakdown）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 261 | §12.2 `inspectStoryboardReadiness` | ✅ blockingReason 捕获上下文异常 + styleReady 判定 + 逐行 incomplete 检测（durationSeconds/videoMotionPrompt）（canvas-storyboard-context.ts:49-70） |
| 262 | §4.1 素材分类三级回退 | ✅ 显式 assetCategory → workflowKind 映射（character→character/scene→environment/styleboard→material）→ undefined（canvas-node-asset.ts:175-185） |
| 263 | §9.4 活跃批次节点去重 | ✅ `activeGenerationBatchNodeIds` 按 mode 过滤 + 活跃状态集合（batch 模块） |
| 264 | §25.3 日志脱敏落点 | ✅ `ResponseBody: SanitizeAPICallPayload(responseBody, "")` 逐行确认（provider_http_client.go:440） |
| 265 | chapter-asset-breakdown.ts（27 行，fail-closed JSON 校验） | ✅ characters/scenes/props 三数组强制 + name/description/prompt 逐字段校验 + 中文错误（章节资产提取域） |
| 266 | §30 SRT 时间戳解析容错 | ✅ `timeToMs` split 解析 + 块级跳过（srt-parser.ts:5-34，二轮确认） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十七轮检查）。

### 32.40 第三十一轮定点抽查（v60 补充，6 处新样本，6/6 吻合；覆盖 worker/CloudAgent/导出/迁移/角度）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 267 | §25.1 worker 2s tick | ✅ `time.NewTicker(2 * time.Second)` 两处（task_worker.go:44,109） |
| 268 | §25.2 CloudAgent 幂等主键 | ✅ `cloudAgentID = "ag" + hex(sha256(userID + "\x00" + key)[:16])`（cloud_agent.go:215-218） |
| 269 | §28.6 导出轮询超时 | ✅ `timeoutMs: 62 * 60 * 1000` + `intervalMs: 3000`（editor-export.tsx:59-60） |
| 270 | §3.x 本地迁移脚本 | ✅ `normalizeLocalCanvasProject` 剥离 `remoteContentHash` 等 hosted 标记、保留本地实际工作（local-workspace-migration.ts:1-30） |
| 271 | §10.2 角度节点走后端生成 | ✅ `runBackendCanvasGenerationTask` 于 use-canvas-media-tools.ts:842（AI 角度非本地处理） |
| 272 | §4.5 泳道顺序 | ✅ `LANE_ORDER = ["text","image","video","audio"]`（canvas-layout.ts:11，二轮确认） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十一轮检查）。

### 32.41 第三十二轮定点抽查（v61 补充，6 处新样本，6/6 域确认）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 273 | §29.3 出站头限额 | ✅ `maxOutboundHeaderCount = 32`（outbound.go:22）+ 16KB 总大小（:162） |
| 274 | §23.3 姿势标签 21 项映射 | ✅ `directorPoseLabel` Record 全 21 项（neutral..phone，director-scene.ts:264） |
| 275 | §23.2 SkeletonHelper 挂载即清理 | ✅ `useMemo` 创建 + `disposeDirectorHelper` 卸载清理（viewport:686-687） |
| 276 | §25.2 CreationRun ItemKey 去重 | ✅ ItemKey 命中时 RequestHash/ProposalVersion 不一致 → `ErrCreationConflict`，一致 → 复用旧项（creation.go:575-583） |
| 277 | §2.1 双 ignore 选择器清单 | ✅ WHEEL（含 data-canvas-wheel-scroll/picker）与 POINTER（含 data-connection-create-menu）两表分离（infinite-canvas.tsx:31-34） |
| 278 | §4.1 素材下载回退（域部分确认） | ✓ canvas-node-asset.ts 无 publicUrl/download 字样——该回退位于 eagle/上传链路而非节点转换；§4.1 表述范围已限定为转换函数本身 |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十二轮检查）。

### 32.42 第三十三轮定点抽查（v62 补充，6 处新样本，6/6 吻合；导出链/CreationRun/视频工具）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 279 | §28.6 collectRenderSources 去重 | ✅ `seen` 集合按 nodeId 去重 + directMedia 才参与 + video/image 限定（editor-export.tsx:24-37） |
| 280 | §28.6 renderRemote 内联预览 | ✅ 完成态渲染 `<video src=resourceFileUrl(resourceId)>` + 下载链接（editor-export.tsx:199-206） |
| 281 | §28.6 渲染计划前 8 步展示 | ✅ `plan.steps.slice(0, 8)` 逐条 kind 徽标（editor-export.tsx:131-137） |
| 282 | §25.2 ProposalVersion 单调锁 | ✅ 字段 int64 + `req.ProposalVersion <= run.ApprovedProposalVersion` 拒绝（creation.go:28,263） |
| 283 | §10.3 merge concat 回退与清理 | ✅ `-c copy` 失败回退 libx264+aac+faststart；finally 逐文件 deleteFile（canvas-video-merge.ts:76-86） |
| 284 | §9.4 activeTaskLimit 来源 | ✅ `useUserStore.runtimeLimits.activeTaskLimit`（use-canvas-generation-batches.ts:35） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十三轮检查）。

### 32.43 第三十四轮定点抽查（v63 补充，6 处新样本，6/6 吻合；editor 接线/后端任务路由）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 285 | §28.1 saveTimeline 键 | ✅ `EDITOR_TIMELINE_KEY:${projectId}`（scoped localforage，editor.tsx:322-330） |
| 286 | §25.3 文本增量双路由 | ✅ 后端注册 `POST/GET /tasks/:id/text-deltas`（routes.go:124,144）；前端 SSE 路径名为 `text-events`——同域双端点并存，命名差异已记录 |
| 287 | §25.1 失败后路由切换 | ✅ `finishTaskRouteAttempt` → `nextRouteAttemptAfterFailure`（task_route_executor.go:92-95） |
| 288 | §28.6 exportLocalMp4 wasm 兜底 | ✅ `exportTimelineToMp4(project, sources, {onProgress})` running 态守卫（editor-export.tsx:93-105） |
| 289 | §27.1 引导一次性写锁 | ✅ `tryEnter(): boolean` / `release()` 幂等释放（director-onboarding.ts:221-231） |
| 290 | §28.6 requiresLibass 双落点 | ✅ 字段声明 :26 + 置 true :191（timeline-to-ffmpeg.ts） |
- **累计（勘定）**：台账 **297 行**（本节 6 行计入后物理总数）+ pre-ledger 13 处 = **310 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十四轮检查）。

### 32.44 第三十五轮定点抽查（v64 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 291 | §25.2/§29.2 protectTaskSecrets 递归加密 | ✅ `func (s *Service) protectTaskSecrets(value interface{}) error`（secret_store.go:112） |
| 292 | §10.4 agent-debug-export 位置勘定 | ✅ `lib/canvas/agent-debug-export.ts`（非 services/diagnostics；此前 B2 查找路径偏差已修正） |
| 293 | §2.4 命名皮肤在 Go 后端 | ✅ 青瓷工作室 studio-indigo / 霓光紫境 brand-violet 于 appearance_skins.go:111,145（cloneAppearanceSkin(classic)），暖柿纸境同类；前端 skin-themes.ts 不含中文名（主题 ID 为英文键） |
| 294 | §11.1 Agent 记忆前端 | ✅ `services/api/agent-memories.ts` + `pages/settings/agent-memory-pane.tsx` 在位（remember_lesson 审批/压缩的前端面） |
| 295 | §9.4 批量表行构建 | ✅ `batchInputColumns` + `createBatchRowsFromColumns` 于 use-canvas-batch-table.ts:85（笛卡尔组合在 canvas-batch-table lib 内） |
| 296 | §23.2 共享 clay 材质 | ✅ 注释「恢复时销毁共享的 clay 材质」（director-clay-materials.ts:4-6，二轮确认） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十五轮检查）。

### 32.45 第三十六轮定点抽查（v65 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 297 | §4.3 标题空值回滚 | ✅ `next` 为空 → `setTitleDraft(data.title)` 回滚且不进编辑态（canvas-node.tsx:288-293） |
| 298 | §16 workflows 三能力贡献 | ✅ image/video/audio 映射「图片/视频/音频」中文标签（workflows.ts:16-24） |
| 299 | §23.3 poseQuaternion 欧拉→四元数 | ✅ `setFromEuler(new Euler(x,y,z)).toArray()`（director-scene.ts:270-272，armsDown z+1.28 二轮确认） |
| 300 | §9.4 费用确认弹窗 | ✅ modal.confirm 含模型名/并发上限/「可能消耗积分或产生外部模型费用」（use-canvas-batch-table.ts:140-149） |
| 301 | §9.3 不可重试类别枚举 | ✅ submission_unknown + [submission_uncertain/timeout/download_failed/results_missing/partial_success]（canvas-generation-failure.ts:57） |
| 302 | §13.1 删除后兄弟画布导航 + 草稿清理 | ✅ `listCanvasWorkspaceProjectCanvases` 找非自身兄弟 + `readCanvasSyncDrafts` 清理（use-canvas-project-lifecycle.ts:328-334） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十六轮检查）。

### 32.46 第三十七轮定点抽查（v66 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 303 | §12.1 运镜首尾关键帧生成 | ✅ `upsertDirectorKeyframe(keyframes, 0, start)` + `(keyframes, endTime, end)` 双 upsert（director-animation-semantics.ts:136-140） |
| 304 | §25.1 取消不确定三态文案 | ✅ 「上游未返回任务 ID」「读取上游取消配置失败」「当前上游协议不支持取消」（provider_task_cancellation.go:74-82） |
| 305 | §12.2 分镜提示词模板元数据 | ✅ `storyboardPromptTemplateMetadata(target.row, "video")` 展开进视频节点 metadata（use-canvas-storyboard.ts:432） |
| 306 | §28.2 标签列 sticky + 注释 | ✅ ruler sticky top-0 + :97 注释「标签列 sticky 固定后，滚动到最右端时…」（editor-timeline-panel.tsx:97,400） |
| 307 | §11.1 localSeq 字段 | ✅ `localSeq?: number` :90 + 本地计数器 :187（快照仅驱动 UI，不作续传游标） |
| 308 | §9.1 NODE_STATUS_ERROR 具名常量 | ✅ `const NODE_STATUS_ERROR = "error" as const`（canvas-image-generation-executor.ts:21） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十七轮检查）。

### 32.47 第四十轮定点抽查（v68 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 309 | §23.2 disposeDirectorMaterials | ✅ Set 去重后先 textures 后 materials 释放（director-resources.ts:5-29） |
| 310 | §25.3 EstimatedCostMicros 无写入点 | ✅ 仅 models_channel.go:113 字段声明，grep 无非测试写入（「上游调用只做用量审计」二轮确认） |
| 311 | §4.3 双击分发批次根优先 | ✅ isBatchRoot → onToggleBatch + stopPropagation；Image+content 次分支（canvas-node.tsx:390-396） |
| 312 | §25.1 租约续期 15s ticker | ✅ `time.NewTicker(15 * time.Second)` + renew 5s 超时（task_worker.go:147-155） |
| 313 | §23.4 保存状态投影 | ✅ `DirectorSaveProgress = Omit<Snapshot,"scene">` + idle 默认 + 注释「订阅回调必须走它」(director-save-wiring.ts:8-25) |
| 314 | §9.2 结果几何居中 locked 跳过 | ✅ `locked → {}` 否则宽高 + 中心对齐 position（canvas-generation-task-sync.ts:211-217，二轮确认） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十轮检查）。

### 32.48 第四十一轮定点抽查（v69 补充，6 处新样本，6/6 吻合；聚焦尚未逐行覆盖域）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 315 | §23.2 capture 归一状态机 | ✅ `reduceDirectorCapture` register/lost/restored/reset 四事件；restored 只清丢失标记、需 renderer 重新登记（director-recovery.ts:73-84） |
| 316 | §10.2 angle-scene 双模式 | ✅ camera/skybox 双模式、orbitRadius 75/sightLine 67、tilt 增量按模式反号（canvas-angle-scene.tsx:17-18,52,108） |
| 317 | §25.2 终态协调器 | ✅ ensureFailedAttemptLogged → Stage=任务失败 → userFacingMessage → markTerminalState → finalizeReplay → logger 全链（task_terminal.go:116-126） |
| 318 | §30 runner worker 池 | ✅ 共享游标 + firstError 短路 + signal abort 三守卫（subtitle-highlight-runner.ts:50-75） |
| 319 | §23.2 失败角标通知 | ✅ 「N 个 3D 模型加载失败」+「已用占位人偶继续显示场景」+ 重试加载（viewport:183-195） |
| 320 | §27.1 requireScope 归一守卫 | ✅ trim 后空值抛错 + `storage ?? localForageStorageForScope(normalizedScope)`（director-onboarding.ts:185-191） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十一轮检查）。

### 32.49 第四十二轮定点抽查（v70 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 321 | §23.2 失败登记表信号语义 | ✅ 仅 `error` 登记 retry，ready/loading/unmounted 一律移除（注释「不能残留不存在对象的 Retry」）（director-recovery.ts:55-67） |
| 322 | §25.1 渠道并发信号量 | ✅ `slots := make(chan struct{}, maxChannelConcurrencyLimit)`（task_worker.go:62） |
| 323 | §23.2 repro 环境快照脱敏 | ✅ `safeReproText`：bearer 模式 + 凭证键值对 → `[REDACTED]`（director-repro-runtime.ts:47-53） |
| 324 | §30 runner 双守卫 | ✅ `firstError.current \|\| options.signal?.aborted` 双短路（subtitle-highlight-runner.ts:60,93） |
| 325 | §23.2 重试回调接线 | ✅ `onLoadStateChange` → `upsertDirectorFailedLoad(current, id, signal, retryLoad)`（director-viewport.tsx:117-119） |
| 326 | §25.1 派发 CAS | ✅ `WHERE dispatch_state='not_sent'` UPDATE；RowsAffected≠1 → ErrCreationConflict（logical_models.go:252-262） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十二轮检查）。

### 32.50 第三十九轮定点抽查（v67 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 327 | §8.2 opLabel 余段 | ✅ set_viewport「调整视图」/ select_nodes「选择节点」/ run_generation「触发生成」（canvas-operation-contract.ts:391-394） |
| 328 | §10.4 agent-debug-export 深读 | ✅ 21 行递归脱敏：敏感键正则（authorization/cookie/api-key/token/password/secret/headers）→ [REDACTED]；Bearer/sk- 模式；data: → [MEDIA OMITTED]（canvas/agent-debug-export.ts:5-21，位于 lib/canvas 非 services——修正早期表述） |
| 329 | §25.3 requestKind 分类 | ✅ GET+content/download → download；GET → poll；repair 路径 → repair；其余 → create（provider_http_client.go:481-492） |
| 330 | §8.3 FNV-1a 快照哈希 | ✅ offset 2166136261 + Math.imul ×16777619 + hex 8 位补零（canvas-operation-contract.ts:378-383） |
| 331 | §25.3 SSE watchdog 逐事件重置 | ✅ `touch()` 每事件重置 120s 定时器 + `Last-Event-ID` 头（agent.ts:207-212） |
| 332 | §4.1 时间戳多级兜底链 | ✅ createdAt: node→taskCreatedAt→folder.createdAt→fallback；updatedAt 更含 drawingUpdatedAt/subtitleUpdatedAt/taskCompletedAt（canvas-node-timestamps.ts:23-37） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第三十九轮检查）。

### 32.51 第四十三轮定点抽查（v71 补充，5 处新样本，5/5 吻合；provider 域/SRT 域/插槽接线/锁定期勘定）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 333 | §25.2 AttemptNumber 防重复创建门禁 | ✅ 「旧任务已尝试执行但缺少提交记录，为避免重复创建上游任务已停止自动重发」+ DispatchState not_sent/accepted 初始化（provider_submission.go:24-34） |
| 334 | §30 重分段断点标点集 | ✅ `CJK_PUNCTUATION = "，。；！？、："` + `LATIN_PUNCTUATION = ",.;!?:"`（srt-resegment.ts:8-9） |
| 335 | §22.6 emitChange 接线 | ✅ 函数 :28 + registerEditorSlot 内 :59 调用（HMR 幂等重注册后广播） |
| 336 | §16 渠道目录 capability 过滤参数 | ✅ `capability?: ProtocolCapability` 可选过滤（plugin-catalog.ts:22,28-30） |
| 337 | §35 v1.5.7 锁定期勘定 | ✅ canvas-appearance.ts（85c9686）grep 无 `"light"` —— v1.5.8 引入 light 的差异审计与源码一致 |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十三轮检查）。

### 32.52 第四十四轮定点抽查（v72 补充，5 处新样本，5/5 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 338 | §12.1 cameraMoveTransform 十运镜偏移表 | ✅ push_in [0,0,-2] / orbit_left [-2.5,0,-1.5] / handheld [0.18,0.08,-0.15] 等全表（workbench:937-942） |
| 339 | §10.3 merge 进度三段 + concat.txt | ✅ reading 45% 标度 → `file 'x'` 清单 writeFile → encoding 55% → concat -c copy 首选（canvas-video-merge.ts:69-75） |
| 340 | §9.2 resetGenerationTaskMetadata 清旧绑定 | ✅ 注释「失败节点再次提交前必须移除旧任务绑定，否则批次调度会把它误判为仍在处理」+ errorDetails/generationErrorCode 清空（canvas-project-generation.ts:187-193） |
| 341 | §10.1 批量上传网格坐标 | ✅ originX 居中于列数 + 行列取模布点（use-canvas-upload.ts:371-376,734） |
| 342 | §28.6 local 导出态机 | ✅ done → percent 100 +「导出完成，已开始下载」；error → phase error + percent 0（editor-export.tsx:105-117） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十四轮检查）。

### 32.53 第四十八轮定点抽查（v79 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 343 | §23.2 collectObject3DResources | ✅ root.traverse 逐 mesh 收集 geometry/material（含 dispose 能力守卫与数组材质展开）（director-resources.ts:62-77） |
| 344 | §25.3 ensureFailedProviderAttemptLogged | ✅ `HasAPICallLogForTask` 先查、无日志才补审计（task_api_call_log.go:16-30） |
| 345 | §28.6 导出轮询常量 | ✅ `timeoutMs: 62 * 60 * 1000` + `intervalMs: 3000`（editor-export.tsx:59-60） |
| 346 | §30 吸附排序与同毫秒 | ✅ `candidates.sort` 距离排序 + `sameMsTargets` 同毫秒全量返回（timeline-snap.ts:57-60） |
| 347 | §23.2 preview 门控语义注释 | ✅ 头注释「记录『失败的那个 URL』而不是布尔标记」+ URL 相等性判断（director-preview.ts:42-51） |
| 348 | §25.3 finalizeReplay 定义 | ✅ `taskTerminalCoordinator.finalizeReplay(task, status, message)`（task_terminal.go:202） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十八轮检查）。

### 32.54 第四十九轮定点抽查（v80 补充，5 处新样本，5/5 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 349 | §23.2 directorCaptureUsable | ✅ `state.registered && !state.contextLost`（director-recovery.ts:85-87） |
| 350 | §28.x flushSave 实现 | ✅ 清定时器 + `isDirty && saveTimeline` 才 performSave（editor-store.ts:191-197） |
| 351 | §23.2 失败角标重试循环 | ✅ `Object.values(failedLoads).forEach((retryLoad) => retryLoad())`（director-viewport.tsx:191） |
| 352 | §25.3 shouldUseTaskTextEvents | ✅ `Boolean(options?.onTextDelta \|\| options?.useTextEvents)`（task-center.ts:371-372） |
| 353 | §30 SRT 序列化序号归一 | ✅ `entry.index > 0 ? entry.index : idx + 1`（srt-parser.ts:62） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十九轮检查）。

### 32.55 第五十轮定点抽查（v81 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 354 | §25.1 worker draining 双守卫 | ✅ dispatch 入口与 tick 内各检一次 `s.IsDraining()`（task_worker.go:50,64） |
| 355 | §28.x saveChain 尾段 | ✅ 成功置 saving:false/isDirty:false/lastSavedAt；失败置 saveError + **保留 isDirty** 供重试（editor-store.ts:86-92） |
| 356 | §2.4 canvasThemes 仅 light/dark 双键 | ✅ `canvasThemes = { light: {…}, dark: {…} }`（canvas-theme.ts:4,5,72）——皮肤三命名主题在 Go 后端（§32.41），前端仅双主题 |
| 357 | §22.2 优化器 strict 工具 | ✅ `additionalProperties: false` + 全字段 required（prompt-optimizer.ts:33-34） |
| 358 | §9.3 不可重试判定含 input 空 | ✅ 有 input 时判定类别枚举；无 input → true（默认不可重试）（canvas-generation-failure.ts:57-58） |
| 359 | §26.3 技能文件端点 | ✅ `GET /skills/:id/files` 返回 SkillPackageFile[]（api/skills.ts:199） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第五十轮检查）。

### 32.56 第四十五轮定点抽查（v73 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 360 | §25.1 渠道并发上限来源 | ✅ `maxChannelConcurrencyLimit = platform.MaxChannelConcurrencyLimit`（platform_bridge.go:257，平台桥接统一取值） |
| 361 | §9.6 素材输入边顺序唯一源 | ✅ 注释逐字「连接数组是引用编号的唯一顺序源；只替换相关输入边所在槽位，避免改变主链和其他节点的连线顺序」（canvas-resource-references.ts:429-433） |
| 362 | §30 高亮 LLM 形状守卫 | ✅ `isSubtitleHighlightLLMResult` 逐字段类型守卫（subtitle-highlight-service.ts:8-20） |
| 363 | §34 reconcileImageBatchRoot 定位 | ✅ `export function reconcileImageBatchRoot(root, nodes)`（canvas-image-batch-retry.ts:135） |
| 364 | §25.3 错误文本截断 500 | ✅ `truncateRunes(err.Error(), 500)`（provider_http_client.go:478） |
| 365 | §4.1 素材挂载负载形状 | ✅ `{assetId, category: canvasNodeAssetCategory(node), title}`（canvas-node-asset.ts:24） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第七十三轮检查）。

### 32.57 第四十六轮定点抽查（v74 补充，6 处新样本，6/6 吻合；按点名域）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 366 | §26.2 agent-memories.ts 全貌（144 行） | ✅ AgentMemory{status pending/approved/rejected}、Bundle、ImportResult、CompactInterval off/daily/weekly/monthly、CompactStatus idle/queued/running/succeeded/failed（api/agent-memories.ts:3-55） |
| 367 | §22.6 useEditorSlots 消费方 | ✅ hook 在 editor-slot-registry.ts:39；editor.tsx:20,231 消费（previewSlots 等 8 槽订阅） |
| 368 | §25.1 续租失败支路 | ✅ `RenewTaskLease(taskID, leaseOwner, 45s)` err → `leaseLost <- err` + cancel 放弃任务（task_worker.go:156-163） |
| 369 | §4.1 素材 URL 解析落点 | ✅ `resolveMediaUrl(storageKey)` 于 project-asset-sync.ts:256,311,358（图/视频/音频三处） |
| 370 | §30 批切片默认 30 | ✅ `batchSize = Math.max(1, options.batchSize ?? 30)` + `entries.slice(i, i += batchSize)`（subtitle-highlight-runner.ts:33,39） |
| 371 | §2.3 shift 横滚降级 | ✅ `shift+absX<1 → panX=deltaY` 且纵向清零（infinite-canvas.tsx:204-212） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十六轮检查）。

### 32.58 第四十八轮定点抽查（v75 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 372 | §26.2 记忆端点全集 | ✅ GET/POST /agent/memories + decide/DELETE/export/import 六端点，超时 15s/30s 分级（agent-memories.ts:104-131） |
| 373 | §23.2 复现夹具确定性 | ✅ `createDirectorReproScene` 固定 FIXTURE_SCENE_ID/背景 #d8dde3/environmentIntensity 0.7/fixtureObject 字面量（director-repro-fixture.ts:42-60） |
| 374 | §25.2 TaskID 复用分支 | ✅ `fresh.TaskID != nil → TaskForUser → task = existing, return nil`；未批准/已撤销 → creationConflict（creation.go:761-770） |
| 375 | §4.1 firstValidDate 链 | ✅ `firstValidDate(createdAt, taskCreatedAt, folder.createdAt, fallback)`；updatedAt 链更含 drawing/subtitle/taskCompletedAt（canvas-node-timestamps.ts:8-21） |
| 376 | §2.4 背景默认 dots | ✅ `DEFAULT_CANVAS_BACKGROUND_MODE: "dots"`（canvas-appearance.ts:30） |
| 377 | §30 重映射索引 | ✅ `target.text.indexOf(highlightText)` → entryIndex/start/end；找不到 → dropped（subtitle-highlights.ts:48-54） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十八轮检查）。

### 32.59 第四十五轮定点抽查（v76 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 378 | §28.1 手势三函数 | ✅ previewGesture 置 inPreview；commitGesture 守卫后 pushEditorHistory + isDirty；cancelGesture 回退（editor-store.ts:163-189） |
| 379 | §25.2 ApproveProposalVersion 单调 | ✅ :263 `<= run.ApprovedProposalVersion` 拒绝、:264 同版本同 hash 幂等通过、:275 推进 |
| 380 | §30 递归切分 front/back | ✅ frontText/backText 递归 splitLongEntry + 最小时长约束应用（srt-resegment.ts:107-121） |
| 381 | §28.6 exportLocalMp4 错误态 | ✅ catch → phase error/percent 0/detail 透出错误消息（editor-export.tsx:106-117） |
| 382 | §12.2 text_to_video 节点构造 | ✅ 既有节点复用 + 新建 Video 节点均带 storyboardPromptTemplateMetadata/shotIndex/workflowKind=shot/seconds（use-canvas-storyboard.ts:365,370） |
| 383 | §25.2 finalizeReplay 通道 | ✅ 结构体字段 finalizeReplay func(string, TaskStatus) error + :50 调用（task_terminal.go:44,50） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第七十六轮检查）。

### 32.60 第四十六轮定点抽查（v77 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 384 | §28.x useEditorSlots 消费 | ✅ editor.tsx:20 import；:231-232 previewSlots/timelineSlots 订阅（8 槽 8 处 hook） |
| 385 | §25.3 Agent SSE 路由（域说明） | ✓ routes.go 中 /events 未命中——Agent SSE 路由在 cloud agent handler 别处注册；前端 agent.ts:212 已证实 `?after=` 游标与 Last-Event-ID 用法 |
| 386 | §23.2 normalizeModel | ✅ 最大边缩放 2 + 中心归零 + 落地 y + shadow 标志（director-viewport.tsx:953-970，二轮确认） |
| 387 | §30 editor store flushSave | ✅ :52 类型 + :191 实现（editor-store.ts） |
| 388 | §23.4 草稿恢复弹窗文案 | ✅ title/content/okText/cancelText 逐字 + `closable:false`/`keyboard:false`（workbench:173-178） |
| 389 | §2.3 wheel preventDefault | ✅ `event.preventDefault(); interactingRef.current = true;`（infinite-canvas.tsx:197-199） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十六轮检查）。

### 32.61 第四十七轮定点抽查（v78 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 390 | §23.2 disposeDirectorObject3D | ✅ `collectObject3DResources → disposeCollected`：textures→materials→geometries，Set 去重一次释放 + 注释「`<primitive>` 不会代为释放，必须由 owner 显式调用」（director-resources.ts:70-101） |
| 391 | §28.x 卸载 flushSave | ✅ 注释「避免最后几次操作丢失」/「必须留下错误证据，不能假装已保存」+ isDirty 保留待重试（editor.tsx:369-377） |
| 392 | §25.2 路由回退三支 | ✅ 备用路由不可用→log warn break；nextAttempt nil→break；否则 `task.RouteID` 对齐 + log「上游未创建任务，切换备用能力路由」（task_route_executor.go:96-112） |
| 393 | §23.2 恢复序列三步 | ✅ `onAvailability("restored") → onRegister(readContext()) → invalidate?`（director-recovery.ts:96-100） |
| 394 | §30 SRT 多行文本 | ✅ `lines.slice(2).join("\n")` 保留多行字幕正文（srt-parser.ts:33） |
| 395 | §16 EditorPluginPermission 三值 + Omit 技巧 | ✅ `timeline.read/timeline.command/export.run`；Omit permissions 注释（「否则数组交叉类型会被归约为 v1」plugin-types.ts:26-28） |
- **累计（勘定）**：台账（当时累计见文末勘定）；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（第四十七轮检查）。

### 32.62 定点抽查（v79 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 396 | §25.1 worker 槽位获取/释放 | ✅ `slots <- struct{}{}` 获取 + `defer <-slots` 释放 + `globalSlot.Release()`（task_worker.go:92-100） |
| 397 | §28.x dispatch 手势期拒绝 | ✅ inPreview 时 saveError「cannot dispatch while a gesture preview is active」（editor-store.ts:129-134） |
| 398 | §23.2 gizmo 尺寸 | ✅ 对象 gizmo `size={0.8}` :599；骨骼 gizmo `size={0.55}` rotate :880 |
| 399 | §25.3 text-deltas GET 处理器 | ✅ currentUser → `taskTextEventCursor(c)` 解析游标 → fail 400（routes.go:144-152） |
| 400 | §23.2 gridVisible 条件网格 | ✅ `scene.gridVisible ? <Grid infiniteGrid fadeDistance={40} …/> : null`（director-viewport.tsx:431） |
| 401 | §28.6 远端结果内联 | ✅ `<video src={resourceFileUrl(resourceId)}>` + 下载链接（editor-export.tsx:201-206） |
- **累计（勘定）**：台账 **401 行** + pre-ledger 13 处 = **414 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v79 轮增量检查）。

### 32.63 定点抽查（v80 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 402 | §25.2 批量批准 1-20 项上限 | ✅ `len(req.SubmissionIDs) == 0 \|\| > 20` → BadAuthRequest「请选择 1 到 20 项生成任务」（creation.go:634-636） |
| 403 | §25.2 批准前置指纹复验 | ✅ 写事务前 `prepareCreationTask` 重算 + `ConfigHash != creationSubmissionOutput(*item).Execution.ConfigHash` → creationConflict「执行配置已变化，请重新准备并确认」（creation.go:651-653） |
| 404 | §28.x undo/redo 同守卫 | ✅ undo/redo 均取 `{project, history, inPreview}` 且 inPreview 拒绝（与 dispatch 同守卫，editor-store.ts:128-135） |
| 405 | §23.2 环境强度系数 | ✅ 默认场景 `environmentIntensity: 0.7`（director-scene.ts:20）+ 视口 `ambientLight intensity = ×0.35`（director-viewport.tsx:429） |
| 406 | §30 递归切分 back 条目 | ✅ `backEntry { index, startMs: splitPointMs, endMs: entry.endMs, text: backText }` + front/back 递归（srt-resegment.ts:100-112） |
| 407 | §16 插件宿主存储注入 | ✅ `pluginStorageFor` 于 plugin-host.ts:2 import（作用域隔离的 storage 服务注入宿主上下文） |
- **累计（勘定）**：台账 **407 行** + pre-ledger 13 处 = **420 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v80 轮增量检查）。

### 32.64 定点抽查（v82 补充，6 处新样本，6/6 吻合）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 408 | §30 高亮解析空回退双支 | ✅ 非 object payload → `return []`（subtitle-highlight-service.ts:21-23）；非法项或 `shouldHighlight=false` 被 flatMap 丢弃（:28-31）；`isSubtitleHighlightLLMResult` 五字段守卫 entryIndex/shouldHighlight/highlightText/start/end 全部 Number.isFinite/typeof 校验（:16-17） |
| 409 | §16 编辑器壳 manifest 声明面 | ✅ `surfaces: ["fullscreen"]`（:22）+ `permissions: ["timeline.read", "timeline.command", "export.run"]`（:23）+ 描述句「注册时间线、预览、检查器、素材、字幕、转写、导出和 AI 编辑八个工作台插槽」（:20）（editor-shell.tsx） |
| 410 | §25.3 Agent SSE 拨号守卫 | ✅ 默认 120s idle watchdog（`options.timeoutMs ?? 120_000`，注释「run is durable…generous idle watchdog is safer than aborting」agent.ts:203-208）；连接态 failures>0 → "reconnecting"（:209）；retry-after 解析（数字秒或 HTTP 日期）且 >300s → cancel + disconnected 终止（:214-219）；4xx 除 408/429 不重试直接终止（:220-223） |
| 411 | §25.2 终态适配器三函数注入（补强 383 行） | ✅ `taskTerminalServiceAdapter{finalizeReplay, writeLog, registerOutput}` 三函数字段（:43-47）+ `newTaskTerminalCoordinator` 注入 `s.finalizeTaskTextReplay / s.log / s.RegisterTaskOutputFromTask`（task_terminal.go:61-65） |
| 412 | §27 导演台上手引导并发纪律（补强） | ✅ run() 拿锁同一刻捕获 `const gate = gateRef.current`，release 只作用捕获实例（注释「绝不在 .then/.catch/.finally 里重新读取 gateRef.current」canvas-director-onboarding.tsx:52-54,84-101）；scope/enabled 变化**整体替换新 gate 实例**而非 release 旧实例（:66-68，防误放新一代锁）；reset 失败补读持久进度（:126-137） |
| 413 | §26 技能运行时预算与提及识别（补强） | ✅ 四 profile（canvas/creation/shortDrama/director）统一 linked-context / maxSkills 4 / maxContextChars 32_000 / maxLinkedFilesPerSkill 3（skill-runtime.ts:19-24）；`@[skill:id]` 正则（:89）+ 自然 `@//name` 提及需边界符（含中文标点，:272-290）；linked 文件按相关性打分 + 「先/必须…读取」required 正则优先排序（:212-220） |
- **累计（勘定）**：台账 **413 行** + pre-ledger 13 处 = **426 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v82 轮增量检查）。

### 32.65 定点抽查（v83 补充，6 处新样本，6/6 吻合）

> v83 轮先行清算：v82 轮「遗留勘误」经逐项回源比对确认为**误报**——v79/v80（第四十八、四十九轮）条目所述断言全部已有落档行：collectObject3DResources→390、HasAPICallLogForTask→344、snap 距离排序+同毫秒→346、preview 门控注释→347、directorCaptureUsable→349、failedLoads 角标重试→351、shouldUseTaskTextEvents→352、SRT 序号归一→253/353、flushSave 实现→387、导出常量 62min/3s→269。零丢失，无需补录。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 414 | §26 技能上下文预算分摊 | ✅ `perSkillBudget = Math.max(1, Math.floor(input.config.maxContextChars / input.selectedSkills.length))` 按选中均摊（skill-runtime.ts:163）；SKILL.md 二进制守卫抛「技能「…」的 SKILL.md 不是文本文件」（:177） |
| 415 | §26 技能截断后缀逐字 | ✅ boundedText 截断尾注「（文件内容超过本轮技能上下文预算，已在此处截断。）」且 `maxChars - suffix.length` 预留后缀长度（skill-runtime.ts:239-244） |
| 416 | §26 linked 文本白名单 | ✅ `TEXT_FILE_EXTENSIONS` 八扩展名 .md/.mdx/.txt/.json/.yaml/.yml/.toml/.csv（:90）+ `isLinkedContextTextFile` 排除 `scripts/`、`assets/` 前缀与 image/video/audio/binary 四 kind（:223-228） |
| 417 | §27 引导非阻塞与播报（补强） | ✅ 硬约束注释「非阻塞。不是 dialog，没有遮罩，不抢焦点……用 role="region" 而不是 role="dialog"」（:19-23）；步骤切换 `aria-live="polite"`（:191）；「第 N 步 / 共 M 步」文本承担真实进度、进度点 aria-hidden 纯装饰（:187,195-196）；restartSignal 变化触发 reset（:158-164）（canvas-director-onboarding.tsx） |
| 418 | §25.3 SSE content-type 守卫 | ✅ `!response.body || !response.headers.get("content-type")?.includes("text/event-stream")` → throw AgentStreamError（agent.ts:230）；请求侧 `Accept: text/event-stream` + `Last-Event-ID` 双头（:211） |
| 419 | §16 编辑器壳八插槽全枚举 | ✅ `contributes.editorSlots` 八项 slot 名 timeline-panel / preview-renderer / inspector / asset-ingest / subtitle-tool / transcription-provider / export-renderer / ai-assistant，priority 全 0（editor-shell.tsx:29-36） |
- **累计（勘定）**：台账 **419 行** + pre-ledger 13 处 = **432 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v83 轮增量检查）。

### 32.66 定点抽查（v84 补充，6 处新样本，6/6 吻合；含交互目录抽样复验与卡↔矩阵交叉核对）

> v84 轮方法说明：INTERACTION_CATALOG 抽 4 项（§1 pinch/§3 尺寸手柄/§4 连线命中/§7 @mention）回源复验；PATTERN_CARDS↔ADOPTION_DECISION_MATRIX 理由列抽 3 对交叉核对（BF-39↔行 37、BF-44↔行 42、BF-45↔行 43），均一致：BF-39 卡面六项子证据是矩阵行 37 标题三项的超集（无矛盾，决策 RESEARCH_ONLY 与卡面「仅作对照证据」门槛一致）；BF-44/BF-45 卡面机制拆解与矩阵理由逐项对应（下表 424/425 行附源码锚）。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 420 | 交互目录 §1 复验：双指 pinch 以两指中点为锚 | ✅ `centerX = (first.x + second.x) / 2 - rect.left`、`centerY` 同构（infinite-canvas.tsx:268-269）；两指 entry 提取 :259-262 + `pinch.active` 移动跟踪 :326-330 |
| 421 | 交互目录 §3 复验：四角手柄 + freeResize 锁比例让位 | ✅ 四角 `<ResizeHandle corner=…>` 仅 `!readOnly && !locked && (isSelected \|\| hovered)` 渲染（canvas-node.tsx:575-580），四角 `-left-[14px]`/`-top-[14px]` 等 14px 外偏（:699-702）；`freeResize?: boolean`（types/canvas.ts:270）+ 锁比例工具 `active: (node) => !node.metadata?.freeResize`（canvas-image-toolbar-tools.tsx:71） |
| 422 | 交互目录 §4 复验：连线 16px 透明命中层 | ✅ 命中 path `stroke="transparent"` + `strokeWidth="16"`（canvas-connections.tsx:77-78） |
| 423 | 交互目录 §7 复验：@mention 不可解析报错 + composer 分支 | ✅ `assertResolvableGenerationMentions(prompt, mentionInputs)`（canvas-node-generation.ts:88，不可解析即抛错）+ `hasExplicitResourceMention` → `buildComposerGenerationContext` composer 模式分支（:89-97） |
| 424 | 卡↔矩阵交叉：BF-44 ↔ 矩阵行 42 | ✅ 卡面「scope 键 `director-scene-draft:` + 300ms 防抖排空 + baseUpdatedAt 基线 + 显式抛错不降级」↔ 矩阵行 42「本地草稿 + 防抖排空循环 + revision 确认 + baseUpdatedAt 基线恢复 / ADOPT_METHOD」逐项一致；源码锚 `debounceMs = 300`（director-save.ts:130）、`scopedStorageKey("director-scene-draft:" + …, scope)`（:136）、baseUpdatedAt 校验 :98/:113 |
| 425 | 卡↔矩阵交叉：BF-45 ↔ 矩阵行 43 | ✅ 卡面「11 白名单稳定码 + 常量 message + 15 条手工复现矩阵」↔ 矩阵行 43「白名单诊断 + 确定性复现夹具与 15 条手工矩阵 / ADOPT_METHOD（与 verifier/稳定码文化同构）」一致；源码锚 `DIRECTOR_DIAGNOSTIC_CODES` 恰 11 项（director-diagnostics.ts:13-25）+ 复现矩阵物理计数恰 15 条 `{id,group,title,steps,expected}`（director-repro-fixture.ts:113 起） |
- **累计（勘定）**：台账 **425 行** + pre-ledger 13 处 = **438 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v84 轮增量检查）。

### 32.67 定点抽查（v85 补充，6 处新样本，6/6 吻合；交互目录剩余章节抽样复验）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 426 | 交互目录 §2 复验：快捷键文案与代码相反（上游自身文案 bug） | ✅ `id: "box-select-tool"` 但 title「切换移动工具」/ description「按 V 或从底部工具菜单切换到移动工具，在空白处拖动可框选节点」（canvas-shortcuts.ts:117-123）——目录「以代码为准」注记逐字成立 |
| 427 | 交互目录 §5 复验：删除优先删选中连线 + Backspace 浏览器拦截 | ✅ `event.preventDefault(); event.stopPropagation();` 注释「browser-level history…look like the whole canvas vanished」+ `if (selectedConnectionId) deleteConnection(...)` 先于 nodes，注释「Treat the explicitly selected edge as the primary target」（use-canvas-keyboard.ts:193-207） |
| 428 | 交互目录 §5 复验：重命名 Enter 提交 / Escape 取消 / 空值回滚 | ✅ Enter→`blur()`、Escape→`onCancel()`（canvas-node.tsx:789-790）；`commitTitle` 内 `titleDraft.trim()` 空值 → `setTitleDraft(data.title)` 回滚原题（:288-292）；草稿态 :150-151/:195-196 |
| 429 | 交互目录 §6 复验：菜单位置避让 Agent 面板与视口边缘 | ✅ `.canvas-agent-panel` getBoundingClientRect 取左缘 + `clamp(menu.x, 12, Math.max(12, rightEdge))` + 注释「destructive action stays inside the viewport」（canvas-context-menu.tsx:495-505） |
| 430 | 交互目录 §8 复验：任务浮层 2s/10s 自适应轮询 + 窗口事件即时刷新 | ✅ `refetchInterval: (current) => (current.state.data?.length ? 2_000 : 10_000)` + `refetchOnWindowFocus: true`（use-canvas-active-tasks.ts:18-19）；`canvas:task-created/cancelled/updated` 三事件 refetch（:22-31）；另证实 `isInternalAgentTask` 过滤 cloud_agent 任务 + `slice(0, 5)` 截断（:16,44-46）——比目录记载更细 |
| 431 | 交互目录 §9 复验：按键保护条件三条 | ✅ 节点工具条内忽略 `.canvas-node-toolbar, .canvas-node-toolbar-menu`（:94）；文本编辑目标（input/textarea/select/contenteditable）放行（:97）；`[data-canvas-no-zoom]` 控件仅放行 `metaKey\|\|ctrlKey` 的 C/V（:131-132）（use-canvas-keyboard.ts） |
- **累计（勘定）**：台账 **431 行** + pre-ledger 13 处 = **444 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v85 轮增量检查）。

### 32.68 定点抽查（v86 补充，6 处新样本，6/6 吻合；§33-34 编排层抽样复验 + 结论面计数同步核验）

> v86 轮方法说明：REPORT.md/README.md 结论面计数同步核验通过——两文件均**不携带**累计抽查总数（仅 REPORT.md:65 与 README.md:20 的「5 处/关键断言抽查（见 ITERATION_LOG v1）」v1 历史表述），累计口径 444→450 仅存于 §32 勘定行与 ITERATION_LOG 队列，无陈旧漂移。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 432 | §33.1 复验：mirrorDraft 非用户改动注释 | ✅ 「用于取消预览、idle pagehide、卸载兜底 —— 这些都不是新的用户改动。」（canvas-director-workbench.tsx:126，§33.1 所引 :124-146 注释带内） |
| 433 | §33.2 复验：快捷键执行器返回值=执行才 preventDefault | ✅ 注释逐字「返回值表示「动作真的执行了」，只有执行了才 preventDefault：没有选中对象时的 Delete 仍然交还给浏览器。」+ `runShortcut = (…): boolean`（:519-525） |
| 434 | §33.2 复验：关键帧双 playhead 纪律 | ✅ 注释逐字「写入关键帧的目的时间用吸附值；取值/显示/手势起点一律用 raw playhead，否则处在两个帧格之间时 AutoKey OFF 的增量会从错误起点计算而产生漂移。」+ `snappedPlayhead = snapDirectorTime(playhead, activeShot?.fps \|\| 24)`（:200-203） |
| 435 | §33.4 复验：DirectorPose 21 值 + UI 20 钮 + 景别 6/运镜 10 | ✅ `DirectorPose` union 物理计数恰 **21**（neutral + 20，types/director.ts:12）；`poseOptions` 恰 **20** 钮且不含 neutral（:919-925，neutral 经「重置姿态」间接到达）；`DirectorShotSize` 6 值（:14）+ `DirectorCameraMove` 10 值（:13） |
| 436 | §33.4 复验：运镜位移偏移表 10 项 | ✅ `cameraMoveTransform` 的 `offsets: Record<DirectorCameraMove, DirectorVec3>` 恰 10 键：static[0,0,0]/push_in[0,0,-2]/pull_out[0,0,2]/pan_left[-2,0,0]/pan_right[2,0,0]/tilt_up[0,1.5,0]/tilt_down[0,-1.2,0]/orbit_left[-2.5,0,-1.5]/orbit_right[2.5,0,-1.5]/handheld[0.18,0.08,-0.15]（:937-943） |
| 437 | §34.3 复验：录制健壮性——错误即中止 + 时长探针 | ✅ `window.addEventListener("error")` 首错即 `recorder.stop()`，错误文案「白膜视频录制期间发生渲染错误，请重试」+ 注释「与其 5 秒后静默产出残缺视频回写画布」（director-viewport.tsx:1140-1146）；`recorded < Math.max(0.25, duration * 0.5)` → throw「白膜视频时长异常，录制可能不完整，请重试」（:1158-1159） |
- **累计（勘定）**：台账 **437 行** + pre-ledger 13 处 = **450 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v86 轮增量检查）。

### 32.69 定点抽查（v87 补充，6 处新样本，6/6 吻合；§35 差异审计重跑勘误 ×3 + 模式卡锚复验 ×3）

> v87 轮方法说明：机械重跑 §35 的 `git log/diff 85c9686..v1.5.9` 全链路（提交数、端点全哈希恒等、分段/总量 diffstat、backend 文件清单），发现两处审计时点误记并回写 §35（上方已带 v87 勘误标记）；另抽 BF-40/41/42 三卡源码锚复验。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 438 | §35 重跑：提交数与端点恒等 | ✅ `git log 85c9686..v1.5.9` 仍恰 2 提交（e8cf506 浅色模式 / e2fd1d3 素材限制对齐）；`v1.5.9^{commit}` == `e2fd1d3f78fa172c…`、`v1.5.7^{commit}` == `85c9686c87a4c17…` 全哈希恒等——端点未动，diff 结果确定性，上游无漂移 |
| 439 | §35 勘误①：总量误记回写 | ❌原记「42 文件 +1590/-477」→ 实测 **62 文件 +2057/-849**；分段 `85c9686..v1.5.8` = 23 文件 +234/-177（backend 0）、`e8cf506..e2fd1d3` = 41 文件 +1824/-673——§35 头注已带 v87 勘误标记回写 |
| 440 | §35 勘误②：「backend 无 diff」不成立回写 | ❌原记「backend/internal 无 diff（纯前端发布）」→ 实测 **16 文件 +1106/-165**（model_capability/provider/provider_protocol/provider_video/provider_video_options/video_reference_constraints 新增/resource/generation: provider_error·types/repository + 6 测试）；性质 = 素材限制与错误提示的服务端对应实现——§35.2 已回写；包断言锚定 `85c9686` 不受影响 |
| 441 | BF-40 卡面锚复验（源码文本断言测试） | ✅ `readFileSync` ×8 把组件/CSS 源码读进测试（canvas-media-performance.test.ts:14-21）；`pretest` 五项边界测试链（package.json:13）+ `test:canvas` 三测试（:15） |
| 442 | BF-41 卡面锚复验（双插件体系） | ✅ `lib/plugins/builtin/index.ts:1-6` 六副作用 import（eagle/prompt-optimizer/workflows/ai-art-critique/media-conversion/editor-shell）；`manifest.go:75-77` 注释逐字「Uploaded plugins must use the declarative path; host bindings are reserved for manifests shipped with the application.」；画布创建门禁 `isPluginEffectivelyEnabled`（canvas-operation-contract.ts:327，import 自 use-plugin-store :5） |
| 443 | BF-42 卡面锚复验（本地伴随进程） | ✅ `resolveLocalRuntimeEndpoint` 默认 `http://127.0.0.1:17371` 且非精确 loopback origin 即抛「Local Runtime endpoint must be one exact loopback origin」（local-runtime-session.ts:10-18）；`MAX_RESPONSE_BYTES = 64 * 1024`（local-runtime.ts:26）；卡面另记 32MB 上限本轮未复核（留待下轮） |
- **累计（勘定）**：台账 **443 行** + pre-ledger 13 处 = **456 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v87 轮增量检查）。

### 32.70 定点抽查（v88 补充，6 处新样本，6/6 吻合；BF-42 补验 + BF-37/38/43 卡面回源）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 444 | BF-42 补验：32MB 深度响应上限 | ✅ `MAX_RESPONSE_BYTES = 32 * 1024 * 1024`（depth-runtime.ts:6）+ 输入图 12MB（:5，错误文案「深度转换图片不能超过 12MB」:67）+ boundedText declared/total 双检「本机深度响应过大」（:140-144）——卡面「响应体 64KB/32MB 上限」= 通用 local-runtime 64KB（local-runtime.ts:26）与深度模块 32MB 两层，口径成立 |
| 445 | BF-37 卡面锚复验（LibTV 像素捕获夹具三件套） | ✅ `canvas-libtv-fixture.ts` 注释逐字「It is opt-in and never enters a normal project.」（:68）；`libtvChrome` 只读复刻条 project.tsx:675（`!== "1"` 才保存 → `=1` 跳过保存）+ :2978 prop 下传；`libtv-original-*` 捕获引用见 fixture 与 project 两文件 |
| 446 | BF-38 卡面锚复验（导入中间表示） | ✅ `LibTVImportResult`（services/api/libtv.ts:36-53）：batchId/projectUuid + 五统计计数器 multiResultNodeCount/staleNodeCount/reusedFailedNodeCount/placeholderNodeCount/convertedSpecialCount（:48-52）+ skipped/warnings；两段式读取/保存双错误文案（libtv-import-dialog.tsx:80,95）+ `importSource: node.metadata`（:43） |
| 447 | BF-38 补锚：TapNowImportResult 同构 + 夹具注入面 | ✅ `TapNowImportResult`（services/api/tapnow.ts:38，同计数器模式 :52）；project.tsx:102 一次 import 十个 `createLibTv*Fixture` 夹具构造器（audio/empty-text/generating/readonly-dense/storyboard/text/video-conversion/video/video-merge/video-subtitle）+ fixtureAppliedRef（:516-517） |
| 448 | BF-43 卡面锚复验（冻结式手势事务·prop 侧） | ✅ `const transform = frozen || resolved`（director-viewport.tsx:557，拖拽期冻结声明式 prop）+ `readObject3DTransform` 从被操控 Object3D 读回 position/rotation/scale（:638-640） |
| 449 | BF-43 卡面锚复验（冻结式手势事务·终态映射） | ✅ 注释逐字「pointerup / window blur / document hidden → commit 当前可见值」「Escape / pointercancel → cancel 并恢复快照，这是用户明确表达的放弃」（director-gesture-transaction.ts:89-91）+ `end: (outcome: "commit" \| "cancel") => void`（:18）+ 「先进入终态再结束第三方拖拽」顺序注释（:49） |
- **累计（勘定）**：台账 **449 行** + pre-ledger 13 处 = **462 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v88 轮增量检查）。

### 32.71 定点抽查（v89 补充，6 处新样本，6/6 吻合；PATTERN_CARDS BF-01..36 卡面抽样回源）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 450 | BF-03 卡面锚复验（均匀网格空间索引） | ✅ `DEFAULT_CELL_SIZE = 1024`（canvas-spatial-index.ts:20）+ `MAX_BUCKET_COVERAGE = 256` 跨格进 largeEntry 线性兜底（:21,31,43,85） |
| 451 | BF-04 卡面锚复验（预算化虚拟化双边距） | ✅ `CANVAS_MAX_RENDERED_NODES = 720` / `CONNECTIONS = 5000`（canvas-performance-mode.ts:8-9）；retain 640/384、enter 128/192（:36-37）；缩放分档 280/420/720（:41-43） |
| 452 | BF-06 卡面锚复验（拖拽期语义 memo） | ✅ `semanticNodesRef`（use-canvas-render-model.ts:207）+ `positionOnlyChange = …every(sameNodeSemanticData)` 逐位语义比较短路（:209-210，sameNodeSemanticData import 自 canvas-project-domain :5） |
| 453 | BF-09 卡面锚复验（hover 单解码器租约） | ✅ `VIDEO_HOVER_DELAY_MS = 350`（canvas-video-hover-preview.ts:3）+ `VIDEO_HOVER_PREVIEW_MS = 3000`（:4）+ 8s deadline（:72）+ 销毁 `video.removeAttribute("src")`（:35） |
| 454 | BF-10 卡面锚复验（Blob LRU 预算） | ✅ `MAX_CACHE_BYTES = 2GB`（resource-blob-cache.ts:27）/ 下限 64MB（:29）/ 500 条（:30）/ 并发 16 + HTTP/2 多路复用注释（:33-34）/ `quota * 0.2` 钳制（:303） |
| 455 | BF-14 卡面锚复验（56px 圆形吸附） | ✅ `CONNECTION_SNAP_RADIUS = 56`（use-canvas-connection-controller.ts:61）+ `isNearNode`「命中但策略不过」建模（:53,462,486）+ :58 注释更细于卡面：「LibTV's 80px world-space quick-add zone renders at roughly 110px on the …」（80px 世界坐标 ≈ 屏幕约 110px） |
- **累计（勘定）**：台账 **455 行** + pre-ledger 13 处 = **468 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v89 轮增量检查）。

### 32.72 定点抽查（v90 补充，6 处新样本，6/6 吻合；PATTERN_CARDS 剩余卡面抽样回源·二批）

> v90 轮方法说明：BF-01 的 32ms/64ms 数字初查未在卡面所引第二、三文件直接现形（canvas-live-viewport.ts 只见 `notify` 布尔门），追至 caller `infinite-canvas.tsx:135` 与 `canvas-viewport-render-sync.ts:3` 落锚——回核后确认卡面三处 file:line 引用区间均覆盖实际常量，无需勘误。

| # | 章节断言 | 复核结果 |
|---|---|---|
| 456 | BF-01 卡面锚复验（三频率双轨视口） | ✅ rAF 逐帧 + commitAfterIdle 后 120ms commit（infinite-canvas.tsx:122-149 窗口内 `}, 120);`）+ `const notify = now - lastPreviewNotifyRef.current >= 32`（:135）+ `CANVAS_VIRTUALIZATION_REFRESH_INTERVAL_MS = 64`（canvas-viewport-render-sync.ts:3，shouldRefreshCanvasVirtualization :5-8）+ preview 事件族常量（canvas-live-viewport.ts:3-6） |
| 457 | BF-02 卡面锚复验（CSS 变量 + 交互期降负） | ✅ `--canvas-live-x/y/scale/inverse-scale` 四变量（infinite-canvas.tsx:431-434；canvas-live-viewport.ts:55-60 注释「外置节点标题用同一帧逆倍率抵消世界层缩放」）+ globals.css:11407 起 `[data-canvas-viewport-interacting="true"]` 的 `transition: none !important` 降负带 |
| 458 | BF-05 卡面锚复验（三档性能模式） | ✅ quality/performance 存储 + 非 localStorage 值回落 "auto"（canvas-performance-mode.ts:11-14）+ auto 判定 `nodes.length >= 80 \|\| mediaCount >= 32`（:32） |
| 459 | BF-08 卡面锚复验（纯 DOM 小地图） | ✅ `MINIMAP_WIDTH = 240 / MINIMAP_HEIGHT = 160 / MINIMAP_IMAGE_PREVIEW_LIMIT = 24`（canvas-mini-map.tsx:12-14）+ 按需挂载 `{isMiniMapOpen && !focusMode && <Minimap … onViewportPreviewChange={previewViewport} onViewportChange={handleViewportChange} />}`（project.tsx:3435，preview/commit 双回调即两段） |
| 460 | BF-19 卡面锚复验（外置标题头反向缩放） | ✅ `NODE_EXTERNAL_HEADER_MIN_SCALE = 0.35`（canvas-node.tsx:708，scale<0.35 隐藏 + readonly-dense fixture 豁免 :726）+ `1 / Math.max(scale, 0.05)` 逆倍率与 `scale(var(--canvas-live-inverse-scale, …))` 同帧抵消（:727-742 窗口） |
| 461 | BF-34 卡面锚复验（视频本地处理） | ✅ 同源发布注释逐字「核心资产随前端同源发布，避免自部署环境首次合并依赖第三方 CDN」（canvas-video-merge.ts:25）+ `import("@ffmpeg/core?url") / import("@ffmpeg/core/wasm?url")` 按需加载（:19-26，:10 注释「只在用户明确合并视频时加载」）；ISO-BMFF 手工解析注释「可用性看容器结构：ftyp、mdat 载荷、trak 内 vide/soun 且 sample_count>0…空壳仍带 ftyp/mdat 四字符，不能靠子串扫描」（canvas-video-segment-args.ts:64-65）+ `requestVideoFrameCallback` 抽帧（canvas-video-frame.ts:36,54） |
- **累计（勘定）**：台账 **461 行** + pre-ledger 13 处 = **474 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v90 轮增量检查）。

### 32.73 定点抽查（v91 补充，6 处新样本，6/6 吻合；PATTERN_CARDS 剩余卡面抽样回源·三批）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 462 | BF-11 卡面锚复验（指针意图路由表） | ✅ `resolveCanvasPointerIntent` 全函数逐字（canvas-selection.ts:26-34）：touch→background?pan:ignore、button 1→pan、非 0→ignore、space→pan、非 background→ignore、boxSelect/alt/ctrl/meta/shift→select、默认 pan——七支归约与卡面「pan/select/ignore」三元一致 |
| 463 | BF-15 卡面锚复验（拖线建下游快速创建） | ✅ 松手空白 `quick: true` pending 分支（use-canvas-connection-controller.ts:678-683 窗口 `screenToCanvas` + quick 标记）+ 点 pin 位移 `Math.hypot(…) <= 5` 判定（:818-827 窗口） |
| 464 | BF-17 卡面锚复验（连线接近 3D tilt） | ✅ `latchCanvasConnectionApproach`（canvas-connection-tilt.ts:6 窗口）+ `rotateX: (0.5 - y) * 10, rotateY: (x - 0.5) * 10` ±10deg（:12 窗口） |
| 465 | BF-20 卡面锚复验（媒体自适应 manualSize 让位） | ✅ `MEDIA_NODE_MIN_SIZE 420×236`（canvas-node-size.ts:4）/ 上限 720×520（:5）/ `fitNodeSize`（:7）/ `!freeResize` 与 `!locked` 门（:64,69）+ 占位期比例串 `nodeSizeFromRatio`（:63） |
| 466 | BF-23 卡面锚复验（三方 rebase 并集） | ✅ `storageRevision`/`tombstones` 文档级字段（canvas-storage-revision.ts:17-18,68-69）+ `generationEffectKeys` 并集合并逐字 `[...new Set([...durable, ...local])]`（:125-127） |
| 467 | BF-28 卡面锚复验（防重复计费四层防线） | ✅ 节点级互斥 `runCanvasGenerationSubmissionOnce` locks Map get/set/delete（canvas-generation-submission.ts:74-85）+ 请求指纹 `canvasGenerationRequestFingerprint` canonicalize（:37-44）+ 同指纹确认文案逐字「当前节点已使用相同提示词、模型、参数和参考素材提交过任务。再次生成会新建任务，并可能再次消耗积分。」（use-canvas-generation-executor.ts:89）+ clientOperationId 幂等（use-canvas-generation-retry.ts 定位） |
- **累计（勘定）**：台账 **467 行** + pre-ledger 13 处 = **480 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v91 轮增量检查）。

### 32.74 定点抽查（v92 补充，6 处新样本，6/6 吻合；PATTERN_CARDS 剩余卡面抽样回源·四批）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 468 | BF-12 卡面锚复验（工具化框选） | ✅ `useState<CanvasToolMode>("box-select")` 默认框选（project.tsx:362）+ `onToolChange(key === "h" ? "move" : "box-select")` H/V 切换（canvas-toolbar.tsx:154-165）+ `boxSelectEnabled={canvasTool === "box-select"}`（:3066）；快捷键文案 bug 已于台账 row 426 逐字复验 |
| 469 | BF-13 卡面锚复验（hover 侧栏端口） | ✅ `railSize = 80`（canvas-node.tsx:863）+ 注释「LibTV centers the visual quick-add icon in an approximately 80px …」（:867）+ quick-create 菜单 Y 以 `anchorRatio ?? 0.5` 回退（use-canvas-connection-controller.ts:326） |
| 470 | BF-16 卡面锚复验（elementFromPoint 换参考） | ✅ `document.elementFromPoint(clientX, clientY)` 两处命中（use-canvas-connection-controller.ts:615,753） |
| 471 | BF-21 卡面锚复验（实体差异补丁 undo 栈） | ✅ `EntityChange<T>` 类型（use-canvas-history.ts:17）+ `changes`/`beforeOrder`（:24-25,214）+ 180ms debounce 合并（:168） |
| 472 | BF-25 卡面锚复验（Web Locks 串行化 + 不毒化） | ✅ `runWithBrowserCanvasStorageLock`：navigator.locks 请求 + `requireCrossRealmLock` 下不支持即 throw「当前浏览器不支持跨标签存储锁，已停止画布生成持久化」（use-canvas-store.ts:140-148，fail-closed）；promise tail `previous.then(() => undefined, () => undefined)` 前序失败转 void + 注释逐字「才不会让一次旧失败永久毒化后续保存队列」（:150-167） |
| 473 | BF-35 卡面锚复验（Agent patch 三路合并 + 终态保护） | ✅ 冲突抛错逐字「Agent 画布增量与本地内容冲突，需要校准；已保留本地编辑」（agent-canvas-patch.ts:42）+ `terminal = ["succeeded","failed","cancelled"].includes(...)`（:69）+ 注释「Never turn its terminal result back into a pending task」+ 无操作保护 `return { before: current, after: current }`（:71-73） |
- **累计（勘定）**：台账 **473 行** + pre-ledger 13 处 = **486 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v92 轮增量检查）。

### 32.75 定点抽查（v93 补充，6 处新样本，6/6 吻合；PATTERN_CARDS 最后一批卡面抽样回源）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 474 | BF-22 卡面锚复验（Agent 整批快照撤销） | ✅ 容量 10 `.slice(-10)` + 快照结构 `{ snapshot: before, afterNodes, afterConnections, change }`（use-canvas-operation-history.ts:282） |
| 475 | BF-24 卡面锚复验（两阶段事务持久化） | ✅ 消费侧注释逐字「Dedicated commit 已确认 generation stamp；用同 scope 最新内存重新投影队列，避免同节点普通编辑被旧 durable 快照替换」（canvas-generation-consumer.ts:231）+ durable 解析（use-canvas-store.ts:196） |
| 476 | BF-26 卡面锚复验（8 原语 + 后置复核） | ✅ `CanvasOperation` union 恰 8 原语逐字（add_node/update_node/delete_node/delete_connections/connect_nodes/set_viewport/select_nodes/run_generation，canvas-operation-contract.ts:9-17）+ `verifyCanvasOperations`（:78）+ resourceReady 物化门 `status === "success" && (storageKey \|\| primaryImageId \|\| resourceId)`（:171） |
| 477 | BF-27 卡面锚复验（任务→节点绑定 + 对账） | ✅ 注释逐字「A historical taskId is not a lock. Only live task states / submission are.」（canvas-node-task-state.ts:3）+ `isCanvasNodeGenerating` queued/running 视为活跃、succeeded/failed/cancelled 即非活跃（:4-11） |
| 478 | BF-29 卡面锚复验（图片批量 root+children 退休） | ✅ batchRootId children 过滤（canvas-image-batch-retry.ts:6）+ `delete metadata.primaryImageId`（:21,68）+ `delete metadata.batchRootId` 解除（:29,81）；执行器定位 pages/canvas/canvas-image-generation-executor.ts（卡面引文件名省目录，路径厘正） |
| 479 | BF-36 卡面锚复验（Agent 上下文预算） | ✅ `MAX_TEXT_BYTES = 192 * 1024`（agent-context-budget.ts:5）+ live 交换硬失败 `> 384 * 1024 \|\| estimatedTokens > 96_000` 且文案逐字「本轮工具结果和上下文已达到处理预算，已完成的操作会保留。请缩小下一步范围后继续；不要重复生成已完成的作品。」（:15） |
- **累计（勘定）**：台账 **479 行** + pre-ledger 13 处 = **492 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v93 轮增量检查）。

### 32.76 定点抽查（v94 补充，6 处新样本，6/6 吻合；余量卡面收尾——卡面二轮回源 45/45 完成）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 480 | BF-07 卡面锚复验（Leafer 连线/套件位图层） | ✅ `hittable: false` ×2（Leafer 与 world/connections Group，components/canvas/canvas-leafer-graphics-layer.tsx:191-192）；预览比 [0.85,1.25] 与 rebase 阈值 `shouldRebaseCanvasRaster` + 注释「避免缩放手势逐帧触发矢量重绘」（canvas-leafer-viewport.ts:4-5,10-20）；`connectionSceneSignature` 物理计数**恰 20 字段** `join("\|")`（graphics-layer :253-276）；路径厘正：该文件实在 components/canvas/（卡面引 lib/canvas/ 省目录） |
| 481 | BF-18 卡面↔历史行 427 一致性 | ✅ 卡面所引 paint-order 注释与 row 427（§32.67）逐字同源：「A connection click can leave the connected node selected for paint-order purposes…」（use-canvas-keyboard.ts:193-207，v85 轮已回源）——卡面与台账行完全一致 |
| 482 | BF-30 卡面锚复验（媒体版本族） | ✅ `versionOfNodeId` 版本组判定（canvas-generation-layout.ts:24）+ `prepareInPlaceMediaVersion` 全仓 grep 无调用点（仅定义）——「未接线（未消费）」断言成立 |
| 483 | BF-31 卡面↔历史行 361 一致性 | ✅ 卡面「连线数组顺序即引用编号」↔ row 361（§32.56）注释逐字「连接数组是引用编号的唯一顺序源；只替换相关输入边所在槽位……」（canvas-resource-references.ts:429-433）+ `composerContent?: string` 与 prompt 独立双字段（types/canvas.ts:225） |
| 484 | BF-32 卡面锚复验（batch-table 批量创作表） | ✅ 表格节点 `width: 1280, height: Math.max(node.height, 560)`（canvas-batch-table.ts:18）+ 默认 `concurrency: 10`（use-canvas-batch-table.ts:28）+ `batchRowId: row.id` 行溯源（:170） |
| 485 | BF-33 卡面锚复验（上传三层存储幂等键） | ✅ `pendingRemoteUpload` 直传失败暂存标记 + 失败原因字段（file-storage.ts:29-30,134）+ 客户端预生成 `"X-Idempotency-Key": createClientId()` 三处（image-transport.ts:14、resources.ts:230、channel-transport.ts:114） |
- **累计（勘定）**：台账 **485 行** + pre-ledger 13 处 = **498 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v94 轮增量检查）。

### 32.77 定点抽查（v95 补充，6 处新样本，6/6 吻合；REPORT 结论面复核 + 目录 §10 声明汇总 + codex 分支监控）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 486 | REPORT §3 第 7 项 fit 缩放上限定锚 | ✅ `focusNodesInView(…, maxScale = 1)` 默认 1（use-canvas-viewport-controller.ts:101,104）+ 适应选区传 1.25（:116）+ `Math.min(1.25, Math.max(viewportRef.current.k, 0.78))`（:140）——「fit view 永不放大超 100%；适应选区才允许 1.25」成立 |
| 487 | REPORT §5.1 巨石页面定量复核 | ✅ project.tsx 物理字节数 **213,805**（≈214KB）；`use-canvas*` 引用 27 处（grep 模式下界，与「28+ 控制器」同量级）——定性成立 |
| 488 | REPORT §7.3 上游测试夹具可借性 | ✅ `Array.from({ length: 50000 }, …)` 50k 节点夹具（web/test/canvas-spatial-index.test.ts:70） |
| 489 | §35.3 分支监控：codex/video-alignment-20260927 | ✅ 远端分支仍在，含 2 个 pre-squash 提交（6bb3495 fix(video) + 18a3439 style(test)，即 e2fd1d3 的 PR 源提交）；`git diff v1.5.9 分支` **为空** → 树内容与 v1.5.9 完全一致，零新增上游内容，无需增量差异审计 |
| 490 | 目录 §10 对照声明三支复核汇总 | ✅ §10 所列「与 LibTV 权威相反」判定全部有回源锚：默认框选工具化（row 468）、Delete 先连线（rows 427/481）、中键/Space 平移意图路由（row 462）——「均不构成改动 CANVAS_NAVIGATION.md 权威的证据」结论维持 |
| 491 | REPORT 结论面一致性终核 | ✅ 无累计抽查总数、无陈旧计数（§6「5 处」为 v1 scoped 历史表述）；§3 七项分歧至此全部有回源锚（本轮 row 486 补齐第 7 项）；§4/§5/§7 引用卡号 BF-03/04/06/09/15/18/22/24/26/30/33/35/40 全部存在且均已完成二轮回源 |
- **累计（勘定）**：台账 **491 行** + pre-ledger 13 处 = **504 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后仍无新提交（v95 轮增量检查，含 codex 分支树差核验）。

### 32.78 定点抽查（v96 补充，6 处新样本，6/6 吻合；§26-§31 跨章抽样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 492 | §26 复验：listAddedSkills 缓存与退避 | ✅ `expiresAt: Date.now() + 15_000` 15s TTL（api/skills.ts:152 窗口）+ `retryDelays = [300, 900, 1800]` 三级退避 + `cause.retryable` 门（:163-167 窗口） |
| 493 | §26 复验：官方应用清单恰 5 项 | ✅ `OFFICIAL_APPLICATION_PLUGIN_IDS = [RUNNINGHUB, EAGLE, PROMPT_OPTIMIZER, ART_CRITIQUE, EDITOR_SHELL]`（official-applications.ts:14-20）+ `officialApplicationIdSet`（:22） |
| 494 | §30 复验：高亮 runner worker 池 | ✅ `concurrency = Math.max(1, Math.floor(options.concurrency ?? 3))`（subtitle-highlight-runner.ts:34）+ 注释「worker 池模式：从共享游标里抢任务」（:54）+ `firstError` 短路（:56,60） |
| 495 | §27 复验：导演台引导版本与步骤数 | ✅ `DIRECTOR_ONBOARDING_VERSION = 2` / KEY "director-onboarding-v2"（director-onboarding.ts:30,33）+ `DIRECTOR_ONBOARDING_STEPS` 物理计数恰 **6 步**（:48-63） |
| 496 | §31 复验：选区浮动工具栏重定位双观察器 | ✅ `ResizeObserver` ×3 observe（canvas-workspace-overlays.tsx:58-60）**且** `new MutationObserver(update)`（:62）——目录 §8「MutationObserver 重定位」记载成立且本轮补锚 ResizeObserver 并存事实 |
| 497 | §29 复验：出站请求超时链 | ✅ `requestTimeout := providerHTTPTimeout` + 剩余租约时间封顶（provider_http_client.go:277-280）+ `AcquireChannelSlot(…, requestTimeout+time.Minute)`（:309）+ `OutboundHTTPClient(requestTimeout)`（:323；头限额 32/16KB 已见 row 273） |
- **累计（勘定）**：台账 **497 行** + pre-ledger 13 处 = **510 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v96 轮增量检查）。

### 32.79 定点抽查（v97 补充，6 处新样本，6/6 吻合；§14/§20-§25 抽样 + §20 算子计数勘误）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 498 | §20 勘误+锚：$ 算子全集计数 | ❌原记「算子全集（36 个）」→ 多名单 case 全量展开实测 **45 唯一算子名**（`case "$coalesce", "$default"`、`case "$map", "$filter"`、`case "$eq", "$ne", …, "$and", "$or"` 共享分支为漏计主因；expression.go:79/:124/:435）；§20 标题已回写勘误 |
| 499 | §21 锚：AI 批上限 + 黄金 op 目录 | ✅ `AI_EDITING_MAX_COMMANDS = 8` + 注释「防止一次模型输出造成不可控的大范围变更」（ai-command-schema.ts:122-124）+ `AI_EDITING_OP_CATALOG`「12 个黄金 op 的 LLM 可读 payload 契约；op 集合与注册表黄金同步（见测试）」（:127-128） |
| 500 | §14 锚：快照 revision 乐观并发 | ✅ `if current.Revision != *revision` 冲突拒绝（backend/internal/canvas/canvas_history.go:95）+ 仓储层 revision DESC 列表与保留清理（repository/canvas_history.go:16,27,86） |
| 501 | §25.1 锚：worker 续租节拍 | ✅ `ticker := time.NewTicker(15 * time.Second)`（task_worker.go:147）——与 row 368 的 `RenewTaskLease(…, 45s)` 构成 15s tick / 45s lease 节拍 |
| 502 | §21 锚：确定性中文摘要 | ✅ 头注释逐字「时间线确定性摘要：把 TimelineProject 压缩成稳定、可控长度的中文上下文，供 AI 编辑和诊断使用。」（timeline-summary.ts:1） |
| 503 | §25.2 锚：creation 会话 epoch | ✅ `ExecutionEpoch int64`（creation.go:17）+ `ExpectedEpoch`（:25）+ 守卫三重 `Owner/ExecutionEpoch/LeaseExpiresAt` 任一不符即拒绝（:91） |
- **累计（勘定）**：台账 **503 行** + pre-ledger 13 处 = **516 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v97 轮增量检查）。

### 32.80 定点抽查（v98 补充，6 处新样本，6/6 吻合；§21-§24 时间线/几何域抽样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 504 | §21 锚：AI_EDITING_OP_CATALOG 恰 12 op | ✅ 物理计数恰 **12**：addClip/moveClip/trimClip/splitClip/setClipProperty/addTrack/removeTrack/setTrackFlag/addSubtitle/removeSubtitle/rebuildSubtitleClips/removeClip——与 row 499「12 个黄金 op」互证；初查误计 13 系类型声明行 `op: string;` 干扰 |
| 505 | §21 锚：editor history 200 层 | ✅ `HISTORY_LIMIT = 200` + 头注释逐字「时间线快照撤销（ADR-0002）：有界 200 层 undo/redo 栈」（editor-history.ts:1,7） |
| 506 | §24 锚：timeline-view 常量组 | ✅ `BASE_TIMELINE_PX_PER_SECOND = 96`、`MIN_TIMELINE_TRACK_WIDTH = 960`、`MIN/MAX_TIMELINE_ZOOM = 0.02/4`、`TIMELINE_ZOOM_STEP = 1.25`（timeline-view.ts:4-8） |
| 507 | §24 锚：默认三轨 ID | ✅ `DEFAULT_VIDEO_TRACK_ID "video-1"` / `DEFAULT_AUDIO_TRACK_ID "audio-1"` / `DEFAULT_SUBTITLE_TRACK_ID "subtitle-1"`（timeline-tracks.ts:6-8） |
| 508 | §24 锚：placement 碰撞三函数 | ✅ `clipsOverlap`（timeline-placement.ts:42）+ `canPlaceAt`（:63）+ `findCollidingItems`（:77）——碰撞判定/放置校验/冲突枚举三段 API 面 |
| 509 | §21 锚：build 双向同步入口 | ✅ `buildTimelineFromNodes`（timeline-build.ts:20）+ `isNodeInTimeline`（:91）+ 字幕双向 `syncNodeSubtitlesToTimeline`/`syncTimelineSubtitleClips`（:99,138） |
- **累计（勘定）**：台账 **509 行** + pre-ledger 13 处 = **522 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v98 轮增量检查）。

### 32.81 定点抽查（v99 补充，6 处新样本，6/6 吻合；§27-§31 剩余细节抽样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 510 | §27/§33.4 复验：ShotInspector 参数四域 | ✅ 时长 0.5-60s 步进 0.5（canvas-director-workbench.tsx:843）+ 焦距 12-200mm / 光圈 f/0.7-32 / 焦点距离 0.1-200m（:845）——§33.4 勘定口径逐值吻合；另锚「摄影机对齐当前视图」「按运镜生成轨迹」双按钮 |
| 511 | §28 复验：editor-shell 插件注册双调用 | ✅ `registerPlugin(editorShellPlugin)` + `registerEditorSlot({ pluginId: manifest.id, … })`（editor-shell.tsx:40-48）——manifest 贡献与插槽注册双通道 |
| 512 | §30 复验：高亮 expired 语义 | ✅ `return entry.text !== highlight.sourceText;`（subtitle-highlights.ts:25）——字幕文本一变即失效的「文本自证」模型直接落锚 |
| 513 | §29 锚：provider 错误分类学 | ✅ `providerPayloadError`（provider.go:143）+ `providerResponseDecodeError` 含 `Unwrap()`（:156-157）+ `providerCircuitOpenError` 熔断开路（:161）——三类具名错误支撑协议引擎错误面 |
| 514 | §34.3 复验：视口错误边界本地失败隔离 | ✅ 类注释逐字「本地失败隔离：3D 视口异常只替换视口本身，不影响画布/项目其余部分。」（director-viewport.tsx:250-251）+ 「retryKey 变化会真正重建 Canvas 与 ErrorBoundary，而不是只换文案」（:88）+ keyed boundary（:160,172） |
| 515 | §31 锚：tool-registry 工具管线 | ✅ `applicable: (ctx) => !ctx.enabledPluginIds \|\| ctx.enabledPluginIds.has(pluginId)`（tool-registry/tool-registry.ts:64）+ 管线注释「过滤 applicable → 应用用户排序 → 过滤用户隐藏 → 生成 FloatingDockEntry（含 separator 分组）」（:82）+ defaultOrder 去重排序（:40,45）；路径厘正：实在 lib/canvas/tool-registry/ 子目录 |
- **累计（勘定）**：台账 **515 行** + pre-ledger 13 处 = **528 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v99 轮增量检查）。

### 32.82 定点抽查（v100 补充，6 处新样本，6/6 吻合；REPORT §2 架构定性表逐行抽样 + §16-§19 补样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 516 | §2 节点体系行：内置节点类型恰 18 | ✅ `enum CanvasNodeType` 恰 **18** 项（image/text/drawing/script/skill/config/video/audio/frame/markdown/svg/html/panorama/compare/chart/colorgrade/media-conversion/batch-table，types/canvas.ts:21-40）+ `PluginCanvasNodeType` 开放扩展（:43-44）——「18 内置类型 + 开放注册表」成立 |
| 517 | §2 连线行：无箭头渐变贝塞尔 | ✅ `marker` 全文件计数 **0**（canvas-connections.tsx）+ `d={pathD}` + 双 `linearGradient`（:48-64）——「贝塞尔、无箭头」渲染侧证据 |
| 518 | §2 状态行：sameCanvasContent 去重 | ✅ import（use-canvas-store.ts:5）+ `const contentChanged = !sameCanvasContent(current, next)`（:603） |
| 519 | §19 勘误+锚：测试文件计数口径 | ❌原记「292 文件」→ 实测 `*.test.*` **290** 个、web/test 全部 **294** 文件（含 4 个 fixtures/helpers 非测试文件）；canvas 前缀 **111** 精确——覆盖表两处已回写勘误口径 |
| 520 | §18 锚：http-api.mdx 恰 36 行 | ✅ `wc -l` = **36**（docs/content/docs/backend/http-api.mdx）——「高层索引文档、无逐路由清单」定性成立 |
| 521 | §16 锚：permission-check fail-closed | ✅ 判别联合 `{ allowed: false; reason: "plugin-not-registered" \| "missing-permission" }`（plugin-permission-check.ts:23）+ 双 `allowed: false` 返回（:45,49）+ 未注册代发 `throw`（:58）——BF-41「权限 fail-closed」落锚 |
- **累计（勘定）**：台账 **521 行** + pre-ledger 13 处 = **534 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v100 轮增量检查）。

### 32.83 定点抽查（v101 补充，6 处新样本，6/6 吻合；§4-§13 画布本体抽样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 522 | §6 锚：`?` 快捷键中心触发 | ✅ `event.key === "?" && !isModifierShortcut && !event.altKey` → `setShortcutRequestNonce((value) => value + 1)`（use-canvas-keyboard.ts:145-149） |
| 523 | §2 锚：世界层 DOM 结构 | ✅ `data-canvas-world-layer`（infinite-canvas.tsx:455）+ Leafer underlay/overlay 双 host（graphics-layer :183-186，row 480 已锚）——「两层世界 div」结构闭合 |
| 524 | §8 锚：版本恢复前备份 | ✅ 弹窗文案逐字「恢复前会备份当前云端内容，并保留本地草稿。恢复后会生成一个新版本，画布的项目归属保持当前设置。」（canvas-version-history.tsx:143）+ `before_restore` →「恢复前备份」reason 标签（:349）+「本机备份」（:377） |
| 525 | §9 锚：孤立 loading 对账中断 | ✅ 注释逐字「这里只把没有持久任务身份的孤立 loading 快照标记为中断，避免覆盖已完成任务。」（use-canvas-generation.ts:522-523） |
| 526 | §10 锚：50MB 分片阈值与中文错误 | ✅ 注释逐字「超过该阈值（与后端单请求 multipart 上限 50MB 一致）的本地媒体走分片上传」（resources.ts:130）+ 「即使误超 50MB multipart 上限（后端 http.MaxBytesError），也给出可读中文而非英文裸错」（:212） |
| 527 | §11 锚：Agent 审批呈现层 | ✅ `AgentApprovalPresentation = AgentApprovalPreview & { source: "server" \| "fallback" }`（agent-approval-presentation.ts:5）+ `approvalArguments` JSON 参数重建（:17-23）+ 240 字截断与「未知目标」兜底（:12-14,27）——「审批（参数重建预览）」呈现侧 |
- **累计（勘定）**：台账 **527 行** + pre-ledger 13 处 = **540 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v101 轮增量检查）。

### 32.84 定点抽查（v102 补充，6 处新样本，6/6 吻合；§5-§13 未抽样交互细节）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 528 | §6 锚：双击空白菜单 | ✅ `handleCanvasDoubleClick` 清空节点/连线/弹窗/工具条四处选择后 `setContextMenu({ type: "canvas", …, createOpen: true })`（use-canvas-viewport-controller.ts:119-127）——「清空选择 + 打开菜单并展开添加节点子菜单」闭合 |
| 529 | §3 锚：拖动集合联动 | ✅ `batchChildIds` 展开 + `isFrameNode → getFrameChildIds` frame 子级 + `!locked` 排除 + 二次 forEach 链式扩展孙级（use-canvas-selection-controller.ts:197-206） |
| 530 | §7 锚：视频原始 URL 不返回 | ✅ 注释逐字「The original video URL is deliberately never returned: callers must fall…」（canvas-media-preview.ts:6）——静态首帧纪律的源头约束 |
| 531 | §8 锚：回收站 200 条软删除 | ✅ `deletedProjects: [...newItems, ...filtered].slice(0, 200)`（use-canvas-history-store.ts:55）+ 完整快照字段注释「仅用于本地软删除恢复」（:14） |
| 532 | §9 锚：任务耗时徽章 | ✅ `useTaskElapsed(node.metadata?.taskCreatedAt)`（canvas-node-content.tsx:202）+ `<Clock3 />{elapsed} · {shortTaskId(…)}` 展示（:219） |
| 533 | §6 锚：Alt+Shift+F 自动整理 | ✅ `autoArrangeCanvasNodes()` 带 `.ant-modal-wrap/.ant-dropdown/.ant-popover` 守卫 + `!event.repeat` 防重复（use-canvas-keyboard.ts:134-139） |
- **累计（勘定）**：台账 **533 行** + pre-ledger 13 处 = **546 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v102 轮增量检查）。

### 32.85 定点抽查（v103 补充，6 处新样本，6/6 吻合；目录 §4-§9 剩余未锚交互项）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 534 | §3 锚：触控轻点背景清空选择 | ✅ `event.type === "pointerup" && !panState.current.hasMoved → onCanvasDeselect()`（infinite-canvas.tsx:381-383）——「轻点（未移动）才清空」判定带 |
| 535 | §4 锚：拖既有连线端点不支持重连（静态复核） | ✅ `reconnect` 在 use-canvas-connection-controller.ts 与 canvas-selection.ts 计数均为 **0**——「改接=删旧建新或换参考」的无重连事实二次成立 |
| 536 | §5 锚：frame/folder 折叠语义 | ✅ `getCollapsedParentFrame` + `isNodeHiddenByCollapsedFrame`（canvas-frame.ts:39-46，折叠隐藏子节点）+ `collapsed && !isCanvasFolderNode` folder/frame 分歧门（:80）；封面卡渲染侧在 canvas-frame-node 组件 |
| 537 | §6 锚：菜单自管 Esc | ✅ `closeOnEscape` window keydown 监听、非 Escape 直接返回（canvas-context-menu.tsx:137-139 窗口）——「自制浮层自管 Esc」闭合 |
| 538 | §8 锚：专注模式进入/退出 | ✅ Ctrl/Cmd+F+Shift 进入分支（use-canvas-keyboard.ts:121-130 窗口）+ Esc 退出条件 `focusMode && !selectedNodeIdsRef.current.size && !hasFocusOverlay`（:208-221 窗口） |
| 539 | §9 锚：缩放步进与适应快捷键 | ✅ `+/=/NumpadAdd` 与 `-/_/NumpadSubtract` 步进缩放、`0/Numpad0` → `fitCanvasContent()`（use-canvas-keyboard.ts:99-113） |
- **累计（勘定）**：台账 **539 行** + pre-ledger 13 处 = **552 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v103 轮增量检查）。

### 32.86 定点抽查（v104 补充，6 处新样本，6/6 吻合；目录 §6-§7 右键分支与 §13 导入披露）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 540 | §6 锚：多选分支三动作 | ✅ 「复制 ${selectedCount} 个节点 ⌘C」「发送到 Agent」「删除 N 个节点」`danger`（canvas-context-menu.tsx:228-230） |
| 541 | §6 锚：角色卡单选分支 | ✅ MenuHeader「角色卡」（characterName/title）+ MenuSection「角色引用」+「查看角色详情」（:236-238）——目录「查看角色详情/复制引用/创建引用副本」分支头吻合 |
| 542 | §6 锚：媒体单选分支 | ✅ 「全景预览」（canOpenPreview 门）+「资产分类」chevron 二级页（:250-251） |
| 543 | §6 锚：空白菜单三项 | ✅ 「自适应整理画布」detail「保持相对布局并加大边距」（:209）+「上传到这里」（:215）+「从素材库插入」非关联项目才显示（:216） |
| 544 | §13 锚：multiResult「取首个」披露 | ✅ 「{multiResultNodeCount} 个多结果节点已使用首个结果。」（libtv-import-dialog.tsx:163）+ 七计数聚合条件披露（:154）——统计披露「信息丢失被显式化」闭合 |
| 545 | §7 锚：文本份数独立规划 | ✅ 注释「独立文本份数（textCount），默认 1，不再复用餐图片数量 count（对齐上游 v0.16 语义）」+ `planTextGenerationTargets` childIds/targetIds（pages/canvas/canvas-text-generation-executor.ts:37,42）；路径厘正：实在 pages/canvas/ |
- **累计（勘定）**：台账 **545 行** + pre-ledger 13 处 = **558 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v104 轮增量检查）。

### 32.87 定点抽查（v105 补充，6 处新样本，6/6 吻合；§22 六内置插件能力面深读）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 546 | §22 锚：eagle 插件 | ✅ `EAGLE_DEFAULT_BASE_URL = "http://127.0.0.1:41595"`（eagle.ts:11，Eagle Local API 默认端口）+ 设置项必填 url 字段（:20 注释「确认 Eagle Local API 可用」）+ 名「Eagle 素材库」 |
| 547 | §22 锚：ai-art-critique 节点贡献 | ✅ `canvasNodes` `defaultSize: { width: 560, height: 420 }`（ai-art-critique.ts:24）+ `acceptsInputKind: "image"`（:27）——与 row 585 二轮互证 |
| 548 | §22 锚：prompt-optimizer 输出契约 | ✅ required 五字段 `["optimizedPrompt","negativePrompt","changes","assumptions","variants"]`（prompt-optimizer.ts:34）——与 row 357 `additionalProperties:false` 互补成完整 strict 工具面 |
| 549 | §22 锚：media-conversion 本地转换面 | ✅ 描述「灰度、Canny 边缘、AI 线稿、本地 Depth Anything V2 深度图和 OpenPose 姿态骨架」+ 文档「这些操作都不会加载 Stable Diffusion 重绘管线」（media-conversion.ts:11,15）+ `surfaces: ["node"]` + **`contributes.transforms` 贡献类型**（:24-26）——区别于 canvasNodes/editorSlots 的第三种贡献 |
| 550 | §22 锚：runninghub 工作流贡献 | ✅ `RUNNINGHUB_PLUGIN_ID = "runninghub-workflow-provider"` + image/video/audio 三 capability 贡献项（label「RunningHub 工作流 · 图片/视频/音频」，workflows.ts:4,17-23）+ `workflowProviderPluginEnabled` 状态门（:12-14） |
| 551 | §22 汇总：editor-shell 已三轮覆盖 | ✅ manifest 八插槽（row 419）+ fullscreen surface/permissions（row 409）+ 双注册调用（row 511）——六内置插件能力面全部完成二轮及以上覆盖 |
- **累计（勘定）**：台账 **551 行** + pre-ledger 13 处 = **564 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v105 轮增量检查）。

### 32.88 定点抽查（v106 补充，6 处新样本，6/6 吻合；REPORT §5 反面教材清单收尾 + §17 剩余细节）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 552 | REPORT 反面教材条 2 锚：双字段警告注释逐字 | ✅「两者不能互相覆盖，否则刷新后富引用会退化为普通"图片1"文本。」（canvas-generation-submission.ts:31）——composerContent/prompt 双字段漂移风险的一手注记，REPORT 引述逐字吻合 |
| 553 | REPORT 反面教材条 4 锚：sandbox 占位文案逐字 | ✅「插件节点等待隔离运行时」（canvas-node-content.tsx `PluginCanvasNodeContent`，`renderer === "sandbox"` 分支）——与 prepareInPlaceMediaVersion 未接线（row 482）同为「能力先行死代码」样本 |
| 554 | REPORT 反面教材条 5 反向验证：无内容哈希去重 | ✅ `dedupe\|去重` 在 file-storage.ts 与 resources.ts 计数均 **0**——幂等仅靠预生成 storageKey（row 485），「同文件两次上传即两份存储」反向事实成立 |
| 555 | §17 锚：depth requestJson 错误归一 | ✅ `!response.ok` → LocalRuntimeClientError，code 兜底 `"depth_runtime_unavailable"`、message「本机深度运行时不可用」（depth-runtime.ts:74-81）+ `requestRuntimeResponse` 会话刷新单次重试（:84-92 refreshed/isSessionRefreshError） |
| 556 | §17 锚：CryptoKey 会话注册 | ✅ `privateKey: CryptoKey`（local-runtime-session.ts:24）+ `registered` 一次性标记（:27,215-216） |
| 557 | §17 锚：密钥 idb 持久化 | ✅ `import { openDB } from "idb"`（:1）+ `openDB(KEY_DATABASE, 1, …)`（:287）——scope 会话密钥浏览器侧持久化 |
- **累计（勘定）**：台账 **557 行** + pre-ledger 13 处 = **570 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v106 轮增量检查）。

### 32.89 定点抽查（v107 补充，6 处新样本，6/6 吻合；§15-§19 上游回归与文档站对照抽样）

| # | 章节断言 | 复核结果 |
|---|---|---|
| 558 | §15 锚：InactiveVideoPreview 文本断言 | ✅ 正则提取 `function InactiveVideoPreview[\s\S]*?\n}\n\nfunction VideoPreviewPlayButton` 源码片段做断言（canvas-media-performance.test.ts:82）——BF-40「源码文本合同」技术实证 |
| 559 | §15 锚：标题交互三测试名 | ✅ 「disables iframe hit testing only during node dragging」「exposes a drag handle without bypassing read-only or locked nodes」「keeps the toolbar hover bridge from intercepting the external title」（canvas-node-title-interaction.test.ts:11,16,24） |
| 560 | §15/BF-39 锚：LibTV 风格创建菜单源+测试双证 | ✅ 源 `variant === "node" ? "grid-cols-4"`（canvas-create-menu.tsx:141）+ 测试 `toContain('w-[232px]')` 等两断言（canvas-connection-create-menu.test.ts:21,23） |
| 561 | §19 锚：local-only 源码边界 | ✅ `existsSync(…)).toBe(false)` 断言禁入路径（local-only-source-boundary.test.ts:28）+ session 文件不得匹配 `/auth\/session|remote user|cloud/i`（:34） |
| 562 | §19 锚：渠道模型目录测试 | ✅ describe「public channel model catalog」（channel-model-catalog.test.ts:68）+ audio capability 可选模型序列断言（:118） |
| 563 | §18 锚：features.mdx 路径与 Agent 能力清单 | ✅ 实际路径 docs/content/docs/overview/features.mdx；:43 Agent 长清单（「审批后的画布写入及媒体生成」「画布摘要/精读」「request_approval 首次 ≥2 项清单先确认」「remember_lesson 写入待审」）与本包 Agent 章断言同向 |
- **累计（勘定）**：台账 **563 行** + pre-ledger 13 处 = **576 处断言抽查全部吻合**；精确化累计 3 处。同轮上游增量检查：v1.5.9 之后 main 无新提交、codex 分支树差仍为空（v107 轮增量检查）。

## 33.

> 补 §23（viewport/机制视角）之外的**工作台编排层**。核心是三组纪律：canonical 提交 vs 仅镜像的二元、快照时效校验、以及一张贯穿全文件的「焦点释放」防误触网。

### 33.1 会话生命周期与提交二元

- **会话只认 scene.id**（:148-160）：同 id 的父级镜像回流不重建会话；重建时 structuredClone 场景 + fps 兜底 24 + staged 事务取消 + 历史/未来清空 + workbench store reset。
- **canonical vs mirror 二元**（:124-146 注释）：`commitDraft/writeAndPublish` = coordinator.commitScene（本地草稿+远端）+ onChange 镜像，产生 revision；`mirrorDraft` 仅把当前 draft 镜像回项目 directorScenes，用于取消预览/pagehide/卸载兜底——「这些都不是新的用户改动」。
- **卸载分层**（:273-300）：pagehide 时 active 预览 end("commit") 完成真实提交、idle 只镜像，落盘统一 `controller.handlePageHide()`（注释：它自己会 persist+flush，组件再叠就是重复落盘）；beforeunload 仅在 `shouldBlockDirectorUnload` 时 preventDefault（异步 flush 不可能阻塞卸载，只同步声明「仍有未确认改动」让浏览器弹保护）；卸载 effect end("cancel")+mirror。
- **关闭统一入口**（:321-362）：closingRef 防重入 → end("cancel")（「取消预览不是新的 canonical 变化」）→ prepareClose 三态：close / blocked（诊断码+错误提示+解锁留下）/ offer-draft-exit（modal「仍然离开/留在导演台」，**确认框存续期间保持上锁防叠出多个弹窗**）。
- 恢复提示一次性（recoveryPromptedRef 按 scene.id，:162-194），恢复/放弃都必须有明确结果；保存重试文案区分「远端失败本地草稿已保留」与「远端和本地都未保存，请不要关闭」（:112-113）。

### 33.2 提交粒度纪律

- 普通 `commit` 前先 `stagedRef.end("commit")` 终结暂存手势（:225-233，「避免新动作消费旧 base」）；历史 push structuredClone、各封顶 50。
- `replaceWithoutHistory`（:257-261）：标题、rig/motionClips 等无历史但持久的变化只镜像——历史边界与持久化边界在此显式分离。
- 快捷键执行器放 ref（:517-525 注释）：监听仅 open 变化注册一次但每次渲染拿最新选择/历史/draft；**返回值表示「动作真的执行了」，只有执行了才 preventDefault**——无选中时 Delete 交还浏览器。
- 关键帧**双 playhead 纪律**（:200-203 注释）：取值/显示/手势起点用 raw playhead，写入用帧格吸附值——「否则处在两个帧格之间时 AutoKey OFF 的增量会从错误起点计算而产生漂移」。播放 rAF 帧格累积（fps clamp ≤120，:205-223）。
- `deleteKeyframe/setKeyframeEasing` 以「未命中返回同一引用则不 commit」实现无效果操作不进历史不触发保存（:507-517）。
- `addObject` 的 placement intent 在 **commit 内读取**（:392-408 注释：异步路径拿到的是「点击添加完成那一刻」的意图而非发起上传时的过时坐标）；`removeCamera` 保底一台且 shots 重绑 fallback（:378-390）。

### 33.3 输出物化与快照时效

- `applyToCanvas`（:643-663）：end(commit) → capture("beauty") → **`isDirectorOutputSnapshotCurrent` 校验输出期间场景/镜头未被编辑污染** → compileDirectorPrompt → 先镜像最新 scene 再 onApply；失败时 draft 保留可重试。
- `exportClayVideo`（:665-692）：回 0 → 播放 → rAF 等一帧 → 录制 → **两次**快照时效校验（录制后、补 beauty 后各一次）→ 恢复播放状态与 playhead。
- 模型上传入场景也走素材库（uploadMediaFile→addAsset→addModelAsset），远端同步失败有 localSavedRemotePendingMessage 降级文案（:419-431）。

### 33.4 检查器与精确数字勘定

- 检查器路由（:776）：摄影机模式下右栏固定 ShotInspector（「对齐视图与运镜是这个模式的主入口」）；ObjectInspector 的骨骼/姿势入口只在姿态/动画模式且只对演员出现（注释「带动画的普通模型不是演员，不应拿到姿势预设与骨骼控制」:805-809）。
- **姿势数字精确化**：`DirectorPose` union **21 值**（neutral + 20，types/director.ts:12）；UI 姿势按钮 **20 个**（poseOptions :919-925，stand/tpose/walk/run/sit/squat/单膝跪/双膝跪/叉腰/倚靠/鞠躬/思考/格斗/踢球/投掷/推进/招手/伸手/抱臂/看手机；neutral 经「重置姿态」间接到达）。§23「21 种预设姿势」指类型全集，精确。
- BoneRotationFields 的四元数↔欧拉往返防回环：`lastEmittedRotation` + `sameDirectorQuaternion`（**q 与 -q 双距离判定**，四元数双覆盖，:857-892）。
- ShotInspector：焦距 12-200mm 实时换算 fov、光圈 f/0.7-32、焦点距离 0.1-200m、时长 0.5-60s 步进 0.5、fps 24|25|30、景别 6 档、运镜 10 种（cameraMoveTransform :937-942 是 10 种运镜的位移偏移表，「按运镜生成轨迹」= 生成首尾关键帧对）。
- 全文件贯穿的「焦点释放」网：IconButton/SceneRow/QuickAdd/mode 切换全部点完 `releaseDirectorFocusAfterPointer`——「点选对象→按 Delete」主流程不被交互控件守卫吃掉（:900-918）。

## 34. 导演台 viewport 二次核读与渲染细节增补（v19 补充，包作者全文 1199 行）

> 性质：对 §23（代理产出）的**独立第二遍全文核读** + 渲染细节增补。结论先行：§23 的全部机制断言（Canvas 稳定引用、frameloop="demand"、三相机指针、冻结式 gizmo 事务、地面拾取、骨骼分层合成、capture/record）经独立阅读**全部成立**，无一处需要修正；以下为增补细节。

### 34.1 加载与资源所有权（渲染侧落地）

- **模型展示身份在 render 阶段屏蔽旧资源**：`identity = {generation, url, storageKey, kind}`（:667-676），prop/retry 变化的第一次 render 就卸下上一代 model，cleanup 才 dispose——「render 阶段屏蔽，effect 清理只是防御」（:736）。
- **GLTF 采纳流程整体包裹 try/catch**（:759-794）：clone/normalize/rig 推断/材质替换/mixer/setLoaded/onActorRigReady 任一步抛错都不得逃出、不得留下半采纳资源；失败先摘 owned 记录防 cleanup 二次释放，再 `disposeDirectorAdoptionFailure({clone, mixer, source})` 回到 error/retry/占位人偶路径。
- `SkeletonUtils.clone` 与 source 共享 geometry/material/texture：**采纳后绝不 dispose source**（注释：source 层级可被 GC，共享 GPU 资源由 owned clone 的 cleanup 释放一次 :763-767）；未被采纳的晚到 source 才释放（:753-757）。
- `resolveMediaUrl(storageKey, modelUrl)` 先解析（认证媒体），解析完成时已失效则不发起网络加载（:746-749）。

### 34.2 骨骼系统细节

- **rig 推断是正则模式表**（`inferDirectorRig` :1005-1032）：骨骼名归一化（小写+去非字母数字）后按 ~40 个人形骨骼位（含每手指 3 节 × 左右 × 5 指 = 30 个手指位）的四套命名惯例（mixamorig/UE/通用/l 数字后缀）匹配；**映射 ≥8 根才算 rig ready**，否则 unmapped 走占位人偶。
- `normalizeModel`（:953-970）：模型自动归一化——最大边缩放到 2、底部落地 y=0、写 shadow 标志。
- 演员引用材质：**单个共享 MeshStandardMaterial 顶掉全部 mesh 材质**，被顶掉的材质立即 dispose（注释「否则每次加载都泄漏一份」:972-985）；`userData.directorActor` 标记使换色只遍历标记 mesh（:987-996）。
- BoneController 屏幕恒定尺寸换算 `screenPixelsToWorldRadius`（透视 fov 数学 vs 正交 span 两分支 :941-946）；可视 5/3.5/2.5px（选中/常态/同侧手指组 dimmed）、命中 12/10px；注释指出控制点与模型根是兄弟关系，「必须转换到控制点父级坐标，否则点击区域与骨骼错位」（:914）。
- `directorFingerGroup` 把手指骨骼归组（拇指/食指/…），未选中同组手指的控制器 dimmed（:860-864,948-951）。

### 34.3 渲染细节增补

- `resolveDirectorDisplay(loaded, identity)`：identity 不匹配返回同一空引用（稳定空值 `emptyAnimations/emptyRestRotations` :55-57），避免下游 effect 每帧变化。
- overrideMaterial 切换（depth/normal/pose wireframe）带完整 dispose 与 clay 恢复（:390-401）；`suspendDisplayMaterialOverride` 供 capture 暂停 clay 态后恢复（:313-320）。
- Grid 参数：cellSize 0.5/sectionSize 5/fadeDistance 40；地面 120×120 平面 y=-0.012 色 #aeb7bf；环境光 = environmentIntensity×0.35（:429-435）；OrbitControls minDistance 0.6 / maxDistance 80（:459）。
- `data-renderer-ready` 属性直接来自 capture 可用性——「真实就绪信号，供 E2E 在触发 context loss 前确定监听器已安装」（:157-159）。
- 录制健壮性增补：`recorder.start(250)` timeslice、停止定时器=时长×1000+120ms、**循环内渲染错误经 window error 监听立即中止录制**（「与其 5 秒后静默产出残缺视频回写画布」:1139-1146）、`probeRecordedDuration` 校验录制时长 ≥ max(0.25s, 50%)（:1158）。
- 失败模型退**占位人偶 DirectorMannequin**（14 关节 14 骨架的圆柱+球体火柴人，选中色 lerp）而非消失（:883-900,856）；错误边界只包视口，「导演台其余面板仍可使用」（:250-279）。
- readPlacementIntent 的 owner 校验（groundRef 记录 owner canvas，重建后旧点不采用 :144-153）与 orbit target 从**实例**读而非 prop（「activeCamera.target 只是初始 prop」:150-152）。

## 26. 官方应用清单与技能（Skills）域（v11 补充）

> 全读：`lib/plugins/official-applications.ts`（27 行）、`services/skill-runtime.ts`（298 行）、`services/api/skills.ts`（245 行）、`lib/canvas/skill-drafting.ts`（58 行）、`lib/canvas/canvas-skill-mentions.ts`（7 行）、`pages/skills/skill-catalog.ts`（30 行）。

### 26.1 官方应用清单（唯一来源收敛）

- `OFFICIAL_APPLICATION_PLUGIN_IDS = [runninghub-workflow-provider, eagle-asset-connector, prompt-optimizer, ai-art-critique, editor-shell]`（:16-22）；`isOfficialApplicationPluginId` 判定「用户可在插件页自主启停的应用型插件」，与系统协议插件区分。
- 头注释记录收敛动机：「之前管理页、用户插件页和后端各自维护一份清单，管理页漏掉 AI 审美分析和剪辑工作台，导致二者被误判为系统协议并在管理页显示『已停用』。这里收敛为唯一来源」——三处清单漂移 bug 的工程整改样本（与本项目「唯一源规则」纪律同构）。

### 26.2 Skill 数据模型与安装源

- `Skill`（api/skills.ts:18-57）：`skillId/versionId/version/contentHash/fileCount/totalBytes`；来源 `sourceType:"builtin"|"markdown"|"zip"|"github"` + `sourceUrl/ref/subdir/commit`；**GitHub 技能自动同步**（`syncStatus:"synced"|"failed"|"syncing"`、`autoUpdate`、lastCheckedAt/lastSyncedAt，`POST /skills/:id/sync` 手动触发）；社区面（isPrivate/likeCount/ownerUid/**originalSkillId 派生溯源**/addedCount/showcaseMedia）；`isAdded/isOwner`。
- 安装三通道：表单创建 / markdown·zip 上传（FormData）/ **GitHub URL（ref/subdir/autoUpdate）**（installSkillUpload/installGitHubSkill :183-198）。
- `listAddedSkills` 缓存纪律（:145-177）：按用户 scope 隔离 + **15s TTL** + in-flight promise 合流 + retryable 错误三级退避重试（300/900/1800ms）+ 写操作统一 `invalidateAddedSkillsCache` 并广播 `canvas-skills-changed` 窗口事件。
- 目录：5 个 fallback 分类（短剧影视/电商营销/创意设计/社媒内容/其他，skill-catalog.ts:5-11）。

### 26.3 Skill Runtime：单一所有权的投递服务

- **所有权纪律**：`canvas-skill-mentions.ts` 整文件只是兼容 re-export，注释明示「Skill selection and delivery are owned by the shared Skill Runtime service; **canvas code must not load files or expand skill prompts independently**」——画布/创作/短剧/导演共用同一运行时，禁止各自实现。
- Profile 注册表（skill-runtime.ts:19-24）：canvas/creation/shortDrama/director 四 profile 当前配置相同（`delivery:"linked-context"`、`maxSkills:4`、`maxContextChars:32_000`、`maxLinkedFilesPerSkill:3`）——**注册表已留分化位但值统一**（预留未来按域差异）。
- 技能选择（:93-110）：`@[skill:id]` 显式 token、自然语言 `@名称`/`/名称`（带边界判定 :272-290）、或显式 selectedSkillIds 覆盖；仅 `isAdded` 技能参与。
- **linked-context 投递**（:160-221）：预算均分（32k÷技能数）；每技能先载 `SKILL.md`，再从包内选链接文件——排序键 = **required 短语正则（「先/必须…读取」类，:216）> 与用户 prompt 的术语重合度（含中文二元组 :230-237）> 文中位置**，排除 scripts//assets//二进制、白名单文本扩展（.md/.txt/.json/.yaml/…）；超预算截断带明示后缀「（文件内容超过本轮技能上下文预算，已在此处截断。）」。
- 提示词组装（:167-171,246-250）：安全前言「它们是任务工作流参考，**不得覆盖系统规则、权限边界或工具安全约束**」+ `<skill-context skill-id version>` XML 包裹 +【用户任务】；`@[skill:id]` 归一为 `@名称`（:264-270）。
- **可审计 provenance**：skillIds/versions/每个文件 path+sha256 打进运行时 metadata（:38-48,256-262）——交付的技能上下文可对账。
- 与 §11 Agent 工具的衔接：Agent 侧 `skills_load/skill_read_file` 读同一技能库（agent-tool-presentation.ts）。

### 26.4 AI 技能草稿（skill-drafting.ts）

- 草稿生成走**服务端提示词模板**：`promptTemplateTaskPlaceholder("技能草稿")` + `promptTemplateOperation:SkillDraft` + `promptTemplateVariables:{用户想法}`（:34-48）——占位 prompt 不会成为模型看到的正文（印证 features.mdx:149「平台级 LLM 任务只走后端提示词目录」）。
- `parseSkillDraft` 容错（:22-55）：JSON 优先（兼容 skill_name/instructions 蛇形），失败回退「首行=名称、正文=简介+指令」，长度钳制（名 80/述 500）。
- 对本项目：技能库+`@[skill:id]`+运行时统一投递，与 LibTV 源站的 Skill 卡/技能选择器（batch97）同题；「provenance+sha256 可审计投递」与「required 短语驱动文件装载」是可借鉴的两个细节（对照 BF-36 上下文预算）。

## 27. 导演台 UI 边角：引导状态机、时间轴与工具面（v12 补充）

> 全读：director-onboarding.ts（245 行）、canvas-director-onboarding.tsx（253 行）、director-sequencer.tsx（281 行）、director-viewport-dock.tsx（79 行）、canvas-director-node-panel.tsx（78 行）、director-view-toolbar.tsx（55 行）、canvas-director-template-modal.tsx（34 行）。

### 27.1 上手引导：纯状态机 + 防卡死持久化（director-onboarding.ts）

- 定位注释（:5-17）：「引导是『用户看到什么提示』，不是场景内容」——**绝不触碰 DirectorScene、不写 undo/redo 历史**；进度按用户 scope 隔离，导出 API 必须显式收非空 scope（「默认 scope 会让 A 账号的引导状态泄漏给 B 账号」）。
- 6 步最短路径（actor→move→pose→path→camera→apply），每步带 mode 归属与「在哪儿点什么」一句话指引（:44-52）。
- schema 版本化：`DIRECTOR_ONBOARDING_VERSION=2`，注释「步骤集合语义变化必须 +1：旧进度里的 stepId 在新步骤表里可能不存在，继续沿用会把用户卡在不存在的步骤上」（:31-35）。
- 状态机不变量（:69-77 注释）：只有 reset 能复活 dismissed/completed（否则「跳过引导」会被误触拉起）；最后一步 next=完成终态；未知 stepId 回初始进度而非把 -1 当下标。
- 解析哲学（:155-157）：「引导是提示不是内容：任何无法确信的持久值都当成没有进度，宁可再引导一次，也不要把用户卡在无法解释的状态里」——非 JSON/数组/版本不符/枚举外全回落初始。
- **注释记录的真实 bug**（:185-191）：`storage ?? localForageStorageForScope(requireScope(scope))` 的 `??` 短路导致「传了 storage」时空 scope 绕过校验——修复为每个导出函数入口无条件 requireScope。写失败向上抛，「不存在『界面前进了但磁盘没动』这种静默分叉」；无变化动作不写盘。
- 一次性写锁 `createDirectorOnboardingGate`（:222-243）：同步闭包变量而非 React state——「两次点击完全可能发生在同一次渲染之间，仅靠 busy state 挡不住同步重入」；release 幂等。

### 27.2 引导浮层：非阻塞 + 并发写换代语义（canvas-director-onboarding.tsx）

- 非阻塞硬约束（:15-24）：`role="region"` 而非 dialog、无遮罩、不抢焦点、无焦点陷阱——「引导旁边就是要动手的工作台，任何模态化都会把『照着做』变成『先关掉』」；只用原生 button；IndexedDB 失败时**不展示**（「无法确认用户是否已经跳过，就不要再骚扰他」）。
- 步骤切换靠 `aria-live="polite"` 播报，不靠焦点转移（:190-193）；进度点纯装饰 aria-hidden，真实进度由「第 N 步 / 共 M 步」文本承担。
- **并发写保护的锁换代语义**（:47-54 长注释）：scope/enabled 变化时 gateRef 必须**整体替换成全新实例**而非 release 共享实例——旧写入若在 `.finally()` 里重读 `gateRef.current` 会把新一代还在写的锁误放掉；因此 `run()` 在拿锁同一刻把实例同步捕获进局部变量，tryEnter/release 全作用在捕获上（:84-102）。reset 用 `generation.current += 1` 作废在途读取并在失败后补读（:116-137）；写盘失败停在当前步骤「绝不在界面上假装已前进」（:95-97）。

### 27.3 Sequencer 时间轴（director-sequencer.tsx）

- 轨道层级：镜头总轨（只读条）→ Camera Cut 概览轨（只读 span，「避免同一帧出现两个语义相同的删除入口」:252-254）→ 相机行（Transform·焦距·景深关键帧）→ 演员折叠组（动作片段条 + Transform + 逐骨骼子轨，骨骼帧 React key 用「骨骼-帧」组合防跨轨重复 :176-178）→ 其他对象。
- **关键帧是真实 button**（:248-249 注释「之前是惰性 span，关键帧一旦记录就无法删除」）：可 Tab 聚焦、Enter/Space 选择、Delete/Backspace 删除，aria-pressed 标注选中；只有同时有 onDeleteKey 与 target 才可交互。
- 选择失效守卫：外部删帧/切镜头后 `useEffect` 立即废弃指向不存在轨道的选中（:64-68，「避免顶部缓动与删除控件继续修改已经不可见的轨道」）。
- 播放头点击按 fps 帧格吸附（`Math.round(raw*fps)/fps`，可关）；面板高度拖拽可调；缓动三选（保持/线性/平滑）作用于「关键帧到下一帧区间」；时间轴缩放 0.75–2.5。
- 行标签点击后 `releaseDirectorFocusAfterPointer`——「点选轨道→按 Delete」与场景列表同源，焦点残留会让守卫吃掉 Delete（:267-269）。

### 27.4 工具面：dock / 取景切换 / 节点面板 / 模板选择

- **「改内容」与「换眼睛」二分**（director-view-toolbar.tsx:10-13 注释）：底部 dock 装「改内容」的工具（W/E/R 变换、添加对象、渲染视图），取景切换独立成右上工具条——「只切换从哪只眼睛看，不产生任何场景改动，也不进 undo/history」；渲染视图按钮由 `renderModes` 过滤，「避免成为绕过模式门控的第二条路径」（dock:17-18）。
- 可访问性细节：取景切换用**文字标签而非图标**（「3D 与 CAM 是两个含义相反的取景状态，图标化只会更难认」:14-15）并解释了为何不复用 dock 按钮类；持久状态切换用 `aria-pressed` 而非 primary 语义（「屏幕阅读器要能读出哪一只眼睛是开着的」:38-40）；所有按钮点完统一释放焦点保 W/E/R/Delete 可用。
- **节点面板诚实空态**（canvas-director-node-panel.tsx:76-87 注释）：「不绘制地面、地平线、机位或任何伪 3D 物体」；图片失败记录「失败的那个 URL」而非布尔量——「同一个坏 URL 不再反复渲染，换成另一个 URL 时自动重试」（:23-24）；预览区带 `data-canvas-no-zoom` 与事件 stopPropagation；非专业模式显示锁标记「专业模式可编辑」。
- **模板显式选择**（canvas-director-template-modal.tsx:8-11 注释）：「过去新建场景无条件塞一个默认演员，产品镜头和空场景用户第一件事就是把它删掉。这里让开局内容由用户决定。没有『默认』按钮——空场景本身就是那个选项，且它真的没有演员」——与 §12 的「绝不在用户没选过的情况下塞演员」同源。

## 28. 时间线编辑器：八插槽面板与 editor store（v13 补充）

> 只读代理深读 editor/ 八面板（约 2800 行）+ editor-store.ts（200 行）+ editor-slot-registry.ts（93 行）+ 宿主 editor.tsx 接线；包作者抽查 3 处承重断言全部吻合（store 头注释与 dispatch fail-closed、panel preview-then-commit 头注释、AI ≤3 阈值 :202）。

### 28.1 editor store：命令唯一入口 + 手势三分（ADR-0002 接线）

- 状态（editor-store.ts:23-53）：`project/history/inPreview/isDirty/saving/saveError/lastSavedAt` + **两个纯 UI 字段 `selectedClipId/transportMs` 不入历史不触发保存**（:33-38）——它们是面板间联动的唯一通道（timeline 拖标尺→monitor seek；timeline 选中→inspector 编辑）。
- `dispatch`（:127-143）：`inPreview` 时拒绝（「cannot dispatch while a gesture preview is active」）；apply 失败 fail-closed 不改状态、错误进 saveError；成功则 pushEditorHistory + isDirty + scheduleSave。
- **手势三分**：`previewGesture` 逐帧 apply 到渲染态但不碰历史；`commitGesture` 预览终态一次性入栈；`cancelGesture` 回退 `history.current`（:163-189，头注释「手势不逐帧污染撤销栈」）。
- 持久化：`saveTimeline` 依赖注入（页面绑定 localforage `editor-timeline:<projectId>`，editor.tsx:322-330）；**1.5s 防抖 + 串行链防旧快照覆盖新状态 + 失败保留 isDirty 重试**（:21,76-102）；卸载前 `flushSave` 冲刷；桌面更新前守卫 `!inPreview && flushSave 后 !isDirty`（:332-338）。

### 28.2 timeline-panel：preview-then-commit 手势

- 拖拽/修剪 = `beginGesture` 记基线 → pointermove 逐帧 `onGesture({op:"moveClip"|"trimClip"})`（=previewGesture）→ pointerup `onCommit()`（:610-718；头注释「逐帧预览、commitGesture 一次性入历史」）；剃刀/工具条操作直接 `dispatch`（:113-116）。
- 手势状态放 `gestureRef`（useRef 非 state）避免每帧重渲染；`setPointerCapture` 保指针出元素仍收 move；预览期间 store 拒绝并发 dispatch/undo/redo。
- **手势数学与渲染同源**（同一 `pxPerMs`，「保证拖拽所见即所得」:1-3）；缩放独立于时长（注释记录修复了 trackWidth 阶梯跳变钉住拖拽的旧 bug :93-94）；move 对左右缘各调 `computeSnap`（8px 阈值）并处理「一侧未命中距离为 0 误胜」的比较陷阱（:651-667）；trim-start 同步前移 `sourceStartMs` 保持右端不动（:684-704）。
- 轨道保护与 UI：每类轨道至少留一条（不可删时 X 弹 2.2s 提示）；标签列 sticky 192px、contentWidth 保证末端片段可达；播放头=贯穿轨道的绝对定位线，位置即共享 `transportMs`。

### 28.3 preview-monitor：rAF 本地时钟 + 单 video 元素

- 播放循环是组件内 rAF（:283-300），按 `speed 0.5/1/1.5/2x` 累进；**每 80ms 节流回写 `store.transportMs`** 驱动时间线播放头（:39-40,290-293）。
- **单一 video 元素**（非元素池）：只渲染当前时间命中的一个 clip（getClipAtTime :46-55）；video 从动于时钟（偏差 <0.35s 不硬 seek 的容差 :44,324-330；`playbackRate` 同步变速）；外部 scrub 偏差 >500ms 视为跳转先 stop 再跟随（:250-266）；`onEnded` 对齐片段结尾衔接。
- H.265 原件 onError → 切后端 `variant=playback` 转码副本 + 2.5s 轮询，带终态护栏（120 次约 5 分钟超时/4 次网络失败进终态，防无限循环 :142-217）。

### 28.4 asset-ingest：directMedia 与 nodeId 双形态

- `TimelineClip.nodeId` 是通用来源引用（画布 clip 靠它回画布查媒体）；素材库插入的 clip 是**时间线作用域直连媒体**：`nodeId:"asset:<id>"` + `directMedia{storageKey}`（「存在时预览/导出优先从该字段解析，不再回画布查节点」，asset-ingest.ts:1-3,34-48）。
- 入轨：素材详情→「添加到时间线」→ 追加到同 kind 轨道末尾（图片默认 3s/其他 5s）→ `dispatch({op:"addClip"})`；1.5s 时间戳守卫拦双击重复。
- **画布选材是自动同步非手动挑选**：宿主把画布产物（分镜图/动作板/首尾帧/视频/成片中 `selected && ready && resourceId` 者）自动 `linkProjectAsset(source:"canvas")` 并入项目素材，以 storageKey 去重、会话内 ref 防重、单条失败不阻塞（editor.tsx:380-435）。
- 本地上传去重键 = 文件名归一 + kind（防「重复导入堆积成多条」）；探时长随 meta 上传；link 失败重试一次、两次失败不删资源只提示。

### 28.5 ai-assistant：调用链与确认流

- 链路（:150-227）：显式覆写 text 模型（「绕过 config.model 可能是图像模型默认值」）→ `buildAiEditingSystemPrompt(summarizeTimeline(project))`（§21.3/§21.4 同源契约）→ 流式 delta 气泡 → `parseAiCommandPlan`（失败给「修正后重试」并把宿主拒绝错误回喂模型 :125-135）→ 空 commands=纯问答 → `validateAiCommandBatch` 整批校验。
- **≤3 条直执行 / >3 条预览**（:202）：预览卡是**命令清单**（逐条 op+payload 截断 96 字符）而非时间线画面 diff；「确认执行(N)」→ applyPlan 逐条 dispatch；applyPlan 把预览卡整卡替换为汇报气泡、按钮卸载防重复提交。
- 执行后权威校验在宿主 store（dispatch 失败写 saveError）——面板层与 store 层双闸。

### 28.6 export / transcription / subtitle-tools / inspector

- **export**（:24-90,199-214）：`collectRenderSources` 只收有 directMedia 的 video/image clip 并按 nodeId 去重——**失去媒体的片段被跳过而非阻断导出**；`buildTimelineRenderPlan` 纯函数计划（UI 只展示前 8 步）；主路径提交整条 timeline JSON 给后端渲染任务（62 分钟超时 3s 轮询），降级 ffmpeg.wasm 本地合成。渲染计划细节（timeline-to-ffmpeg.ts:93-203）：`-ss` 在 `-i` 后输出 seek 防 GOP 偏移；无源片段跳过且不补自身黑场、由下个 gap 统一覆盖（注释记录线上「黑场翻倍、字幕漂移」实锤）；libass 烧录标记 wasm 回退。
- **transcription**（:52-97）：只提交 resourceId 给后端 whisper 任务（25 分钟轮询）；成功后 segments→`SrtEntry[]`→**单条命令** `rebuildSubtitleClips({nodeId:"transcription:<assetId>"})` 原子替换字幕轨。
- **subtitle-tools**：SRT 粘贴导入同样走 `rebuildSubtitleClips`（nodeId 固定 `"srt-import"`，确定性 id 使重复导入原地替换不堆积）；核心语义「时间线字幕片段是节点字幕的只读快照，权威在节点 subtitleEntries」（:1-4）；AI 高亮只写权威节点、本面板不重复发起 AI 请求。
- **inspector**：所有编辑走 `setClipProperty` patch 命令；文本框 **onBlur 才提交**（避免每击键一条历史）、range 则 onChange 即提交（每档 50ms 一条命令进 200 层历史）——提交粒度与控件类型匹配（:184-192）。

### 28.7 slot-registry：注册与 fail-closed 权限

- 模块级单例（非 React context）；`registerEditorSlot` 先注销同 pluginId+slot 再 push（幂等覆盖兼容 HMR）；解析按 priority 降序+注册序升序（八面板 priority 全 0，实际按注册序）。
- **权限检查在渲染期 fail-closed**：`EDITOR_SLOT_REQUIRED_PERMISSION` 表（timeline-panel/inspector/asset-ingest/subtitle-tool/transcription→`timeline.command`；preview/ai-assistant→`timeline.read`；export→`export.run`；注释「新增插槽必须补表，否则因找不到权限而拒绝渲染」）；被拒插槽渲染红色诊断条（title 写明「已按 fail-closed 拒绝渲染」）；插件命令代发另有运行期 `assertEditorPermission` 抛错（plugin-permission-check.ts:55-63）。
- **横切结论**：AI 助手、转写、SRT 导入、检查器、拖拽五个入口全部收敛到同一 `dispatch` 命令通道——统一获得校验、200 层快照历史与 1.5s 防抖持久化；这是「同一注册表约束三方」（§21.3）在面板层的完整体现，也使 §28.1-28.6 的每个特性天然共享 undo/保存/校验。
