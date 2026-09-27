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
- **算子全集（36 个）**：
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

> 本包研究锚点**维持锁定 `85c9686`/v1.5.7 不变**；本节记录锁定之后上游的前移（2026-09-28 fetch：新增 tag `v1.5.8`/`v1.5.9` 与分支 `codex/video-alignment-20260927`），并标注对本包断言的影响。方法：`git log/diff 85c9686..v1.5.9`（恰好 2 个提交：e8cf506 浅色模式、e2fd1d3 视频素材限制对齐；42 文件 +1590/-477）。

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
- 后端 `backend/internal` 无 diff（本次前移为纯前端发布）。

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

## 33. 导演台 workbench 编排层精读（v18 补充，包作者全文 942 行）

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
