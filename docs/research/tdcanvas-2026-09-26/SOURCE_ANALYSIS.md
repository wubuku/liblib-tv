# TDCanvas 源码分析（固定版本）

> 研究对象：[`AICoderTudou/TDCanvas`](https://github.com/AICoderTudou/TDCanvas)（本地工作副本 `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`）。
> 本文只记录**源码事实**（file:line 可核对），推断与 clone 决策分别留在 [REPORT.md](REPORT.md) 与 [ADOPTION_DECISION_MATRIX.md](ADOPTION_DECISION_MATRIX.md)。
> 观察日期：2026-09-26；行号对齐锁定提交 `16b3127` 的工作树。

## 0. 版本锚点与上游链

| 项目 | 值 |
|---|---|
| 上游远端 | `https://github.com/AICoderTudou/TDCanvas.git` |
| 本地 origin | `https://github.com/wubuku/TDCanvas.git`（fork） |
| 分支 | `master` |
| 锁定提交 | `16b31273633f983cdbd8de05694ec36d471b2650`（2026-09-15，Merge PR #1 fix/comfyui-workflow-io-bypass） |
| 版本 | `v0.14.0`（`VERSION`） |
| 引入方式 | 本地工作副本（**未建 submodule**；与 open-canvas 协议不同，理由见 ITERATION_LOG） |
| 工作树状态 | 除未跟踪 `docs/drafts/` 外干净，即分析内容 = 锁定提交 |
| 上游的上游 | 基于 `basketikun/infinite-canvas` 二次开发（其 README「开源许可与来源」；上游约 7k star、官网 canvas.best，本项目**未调研过**该上游） |

技术栈（`web/package.json`）：Vite + React 19.2.5 + TypeScript + AntD 6 + Tailwind 4 + Zustand 5 + Tauri 2（`@tauri-apps/api` 2.11）+ localforage + fflate + nanoid + i18next。**没有任何画布库**（无 reactflow/@xyflow/konva/fabric/pixi/d3-zoom）——画布内核完全手写。

目录地图：

```
TDCanvas/
├── web/                     # 前端 + Tauri 桌面壳
│   ├── src/pages/canvas/    # 画布页面（index.tsx 首页 / project.tsx 编辑页 4242 行）
│   ├── src/components/canvas/  # 画布组件（60+ 文件，nodes/builtin-nodes.tsx）
│   ├── src/stores/canvas/   # use-canvas-store / use-canvas-ui-store / use-plugin-store
│   ├── src/lib/canvas/      # 纯函数工具（几何/端口/对齐/导出/注册表/插件运行时）
│   ├── src/services/api/    # aitudou.ts（生成 API）、aitudou-*.ts、canvas-agent.ts
│   ├── src/integrations/comfyui-local/  # ComfyUI 内置集成
│   └── src-tauri/src/       # lib.rs / main.rs / media_cache.rs（Rust）
├── canvas-agent/            # 独立 Node 进程：本地 Agent 通道（HTTP+SSE / stdio MCP 双入口）
├── modules/comfyui-local/   # 独立领域模块（contracts/core/frontend/tauri-plugin）
├── plugins/canvas/          # 画布节点插件（sdk/template/markdown/svg/html/panorama/sticky-note/registry）
└── plugins/tdcanvas/        # Codex 插件（.mcp.json + skills）
```

## 1. 渲染内核

### 1.1 坐标体系

- 视口状态 `ViewportTransform = { x, y, k }`（`web/src/types/canvas.ts:6-10`），存于页面组件 `useState`（`project.tsx:248`），另有 `viewportRef` 镜像（`project.tsx:296, 461-468`）。
- **单一 transform 层**：所有节点与连线放在一个 div 里，施加 `transform: translate(x px, y px) scale(k)` + `origin-top-left`（`td-canvas-surface.tsx:241-248`）；节点自身再用世界坐标 `translate(node.x, node.y)` 定位（`canvas-node.tsx:312-318`）。
- 屏幕→世界：`world = (local - viewport) / k`（`project.tsx:493-503`）；世界→屏幕：`screen = viewport + world * k`（`canvas-node-toolbar-position.ts:3-10`）。
- 初始视口把世界原点放在屏幕中心（`project.tsx:481-484`，仅 store 未恢复时兜底）。

### 1.2 平移 / 缩放（`td-canvas-surface.tsx`）

- **wheel 永远缩放**：不区分 ctrl/cmd/shift；`factor = pow(1.1, -deltaY/100)`，clamp 0.05–5（`td-canvas-surface.tsx:69-89`）。触控板 pinch（合成 ctrl+wheel）同路径，无独立手势处理。
- 缩放锚点 = 鼠标位置（`:79-88`）；UI 缩放滑杆锚点 = 视口中心，range 5–500%（`project.tsx:1207-1218`；`canvas-zoom-controls.tsx:84-95`）。
- 平移 = 中键拖拽或左键拖空白（`td-canvas-surface.tsx:104-118`；空白判定 `!target.closest("[data-node-id],[data-connection-id]")`，`:95`）。rAF 合帧 + window 级 pointermove/up + setPointerCapture（`:106, 159-198`）。
- **Space+拖拽被故意禁用**：Space 按下只 `preventDefault()`，反而不平移（`:50-67, 120-122`）——与 Figma/React Flow 惯例相反。
- 框选 = **ctrl/cmd+左键拖空白**（surface 路由 `:97-102` → `project.tsx:1270-1302`；矩形相交判定 `project.tsx:1506`；shift 为加选）。
- Fit 视图按可见节点包围盒算 k（clamp 0.05–1），280ms easeOutCubic 动画（`project.tsx:1136-1174`）；focusNode 450ms、k clamp 0.05–1.5（`:1176-1203`）。
- antd 弹层与 `[data-canvas-no-zoom]` 内滚轮不缩放不阻止默认滚动（`td-canvas-surface.tsx:71, 93, 200-212`）。
- 无键盘 +/-/0 缩放快捷键（`project.tsx:1735-1807` 键位表见 [INTERACTION_CATALOG.md](INTERACTION_CATALOG.md) §6）。

### 1.3 渲染技术

- 节点 = 普通 DOM div + `transform` 定位 + `contain: "layout style"`（`canvas-node.tsx:308-328`）。
- 连线 = **固定 10000×10000 的 SVG**，放在 transform 层内世界原点处，`overflow-visible` 支持负坐标（`project.tsx:3702`）。
- 连线路径 = 三次贝塞尔，曲率 `max(|dx|*0.5, 50)`，水平出入（`canvas-connections.tsx:36-38`）。每条边 2–4 个 path：16px 透明命中层（`:42-48`）+ 可见描边（选中 3px+光晕 / 常态 2px，`:59-66`）+ 运行态流动虚线（`pathLength=100`，dashoffset 动画 1.45s，`:67-72`；CSS `globals.css:807-837`，尊重 `prefers-reduced-motion`）。
- 拖拽中临时连线 `ActiveConnectionPath`：虚线 5,5，可 snap 目标口（`canvas-connections.tsx:77-92`）。

### 1.4 小地图（`canvas-mini-map.tsx`）

- **纯 div 实现**（非 SVG/canvas），固定 240×160，位于 `bottom-24 left-6 z-50`（`:12-13, 99`）。
- 世界范围 = 节点包围盒 ±500 边距，等比缩放居中（`:32-47`）；节点按 node-registry 的 `minimapColor` 着色，最小 2px（`:115-132`）。
- 视口框 = 由 `(-x/k, -y/k, w/k, h/k)` 反算的世界矩形投影，最小 4px（`:70-84, 133`）。
- 点击/拖拽可导航：pointerdown capture，把视口中心移到点击处世界点（`:86-113`）。

### 1.5 对齐辅助线与吸附（`canvas-alignment-guides.ts` / `.tsx`）

- snap：移动组包围盒 vs 所有静止节点的 start/center/end 三锚点穷举取最近（`:71-86`）。
- 阈值 = **7 屏幕像素**，换算世界阈值 `thresholdPx / max(scale, 0.05)`（`:27-33`）。
- 网格吸附可选（`snapToGrid`，默认关；`project.tsx:266`），world gridStep=16（`CANVAS_GRID_STEP=16`，`project.tsx:149`）。
- 辅助线画在世界坐标覆盖层（z-[4]），线宽 `1/scale` 补偿保持约 1 屏幕像素，长度=视口世界尺寸（`canvas-alignment-guides.tsx:14-29`）。

### 1.6 网格 / 背景（`td-canvas-surface.tsx:262-315`；`globals.css:301-413`）

- 三种模式 `CanvasBackgroundMode = "dots" | "lines" | "blank"`（`canvas-theme.ts:2`）。
- **屏幕空间渲染**（不在 transform 层）：CSS background 点阵/线格；格子尺寸世界 16px 起步翻倍至 ≥8 屏幕像素，位置用 `viewport.x % gridSize` 偏移（`:267-271`）。
- 特色装饰：双层视差 depth 层（0.78x）+ 大气层（0.025x）、指针跟随 radial-mask focus 层（rAF 写 CSS 变量，`:131-157`）、depth 层 11s 漂移、密度按 k 分档 far/standard/near（`:275-277`）。

### 1.7 事件架构与命中

- 分层路由靠 DOM 原生事件 + data 属性：surface 用 `closest("[data-node-id],[data-connection-id]")` 判背景（`td-canvas-surface.tsx:95`）；port 是 48px 命中 div 带 `data-port-id/direction/type`（`canvas-node.tsx:1110-1114`）。
- 节点选择在**捕获阶段**（`onMouseDownCapture`，`canvas-node.tsx:327`），拖拽在冒泡阶段（`project.tsx:1337-1365`），window 级 move/up 收尾，dx/dy 除以 k（`project.tsx:1379-1380`）。
- **连线落点 = JS 几何命中** `getConnectionDropTarget`：世界坐标距离 ≤ `40/scale`（端口）、节点本体命中 padding `32/scale`；优先级 = (命中口 0 < 节点内 1 < 扩展区 2)*1e5 + 距离，节点逆序顶层优先（`project.tsx:147-148, 573-615`）。
- z-index 体系：连线 SVG 0 < 辅助线 z-[4] < Group z-[5] < 普通节点 z-10 < 选中 z-50（`canvas-node.tsx:311`）；框选矩形 z-[100]。

### 1.8 Port 几何（`canvas-node-ports.ts`）

- `CanvasNodePort {id,label,direction,dataType,required?,multiple?,description?,color?}`（`types/canvas.ts:186-195`）；无 ports 定义时回退 legacy 单输入/单输出（`__legacy-input/__legacy-output`，`canvas-node-ports.ts:6-27`）；Group 无 port。
- **等分比例锚点**：第 i 口 `y = node.y + height*(i+1)/(n+1)`，与 UI `top:(i+1)/(n+1)*100%` 一致（`:44-54`；`canvas-node.tsx:1110`）。
- 兼容性：`any` 通配否则小写全等（`:56-61`）；`normalizeConnectionHandles` 校验异节点、方向相对、非 Group、类型兼容，`multiple:false` 输入口限一条入边（`:63-85`）。

### 1.9 视口持久化与性能

- viewport 是项目文档字段（`use-canvas-store.ts:10-23`），变化后 500ms 防抖 `updateProject`（`project.tsx:448-460`）；进入项目恢复（`:384`）。
- 性能：视口裁剪虚拟化（只渲染与视口外扩 280px 相交的节点，`project.tsx:617-628`）；平移/拖拽/氛围光 rAF 合帧；节点 `contain: layout style`；SVG 层 `translateZ(0)`；连线不裁剪（`project.tsx:3703-3709`）。

## 2. 状态模型与持久化

### 2.1 数据模型

```ts
// web/src/stores/canvas/use-canvas-store.ts:10-23
export type CanvasProject = {
    id: string; title: string; createdAt: string; updatedAt: string;
    nodes: CanvasNodeData[]; connections: CanvasConnection[];
    chatSessions: CanvasAssistantSession[]; activeChatId: string | null;
    inputMode?: CanvasInputMode;          // "connections" | "objects"
    backgroundMode: CanvasBackgroundMode; showImageInfo: boolean;
    viewport: ViewportTransform;
};
// web/src/types/canvas.ts:173-181
export type CanvasNodeData = {
    id: string; type: CanvasNodeTypeId; title: string;
    position: Position; width: number; height: number;
    metadata?: CanvasNodeMetadata;        // 开放索引签名 [key: string]: unknown
};
export type CanvasConnection = {
    id: string; fromNodeId: string; toNodeId: string; fromPortId?: string; toPortId?: string;
};
```

- id：项目/媒体 storageKey 用 nanoid（`use-canvas-store.ts:71, 92`；`image-storage.ts:22`）；节点副本用 `${type}-${Date.now()}-...`（`project.tsx:1029`）；连线 id `conn-`+Date.now（`project.tsx:540`）。
- `CanvasNodeMetadata` 约 50 个可选字段：content/prompt/status/storageKey/localPath/providerTask/providerResult/imageHistory/objectReferences/groupId/batchChildIds 等（`canvas.ts:119-171`）。

### 2.2 状态分层：薄 store + 巨型页面

- 11 个 store 中画布核心仅 `use-canvas-store`（项目文档 CRUD + persist，API 仅 createProject/importProject/openProject/renameProject/deleteProjects/replaceProjects/updateProject，`use-canvas-store.ts:25-35`）、`use-canvas-ui-store`（首页 UI，纯内存）、`use-plugin-store`（已装插件，persist）。
- `project.tsx`（4242 行）持约 48 个 useState + 25 个 useRef：nodes/connections/chatSessions/viewport 为当前项目工作副本，其余为交互现场（选中集、连线中、框选、右键、10+ 弹窗、`historyRef` undo 栈、`generationRequestsRef` 生成请求）。
- 设计逻辑：store 只管「文档集合持久化」，高频编辑现场（拖拽每帧 setState）留在页面，随路由重挂载实现项目隔离（`/canvas/:id`，`router.tsx:28-29`）。

### 2.3 undo/redo（页面级全量快照双栈）

- `historyRef = { past: CanvasHistoryEntry[], future: [...] }`（`project.tsx:205`）；快照含 nodes/connections/chatSessions/backgroundMode/showImageInfo/inputMode（`:128-134`）。
- 提交：180ms 防抖合并，引用相等跳过，past 上限 **50**（`slice(-49)`），清空 future（`:405-438`）；`applyHistory`/`undoCanvas`/`redoCanvas`（`:1220-1257`）；`applyingHistoryRef` 防回写。
- 拖拽期间 `historyPausedRef` 暂停 → 整次拖拽合并为一条（`:1362, 1391`）；加载项目清空历史（`:385`）；快捷键 Cmd/Ctrl+Z / +Shift / Ctrl+Y（`:1746-1757`）。

### 2.4 持久化三级漏斗

1. 页面 effect：文档字段任一变化直写 `updateProject`（`project.tsx:440-443`）；viewport 单独 500ms 防抖（`:448-460`）。
2. store persist 自定义 storage：**400ms 防抖 + 同引用去重**（`use-canvas-store.ts:51-60`）。
3. localforage IndexedDB（库名 `tdcanvas`/store `app_state`，读写失败回退 localStorage；`localforage-storage.ts:4-33`）。key：`tdcanvas:canvas_store`、`tdcanvas:asset_store`、`tdcanvas:plugin_store`、`tdcanvas:ai_config_store`、`tdcanvas:theme_store`。
- 二进制独立 objectStore：`image_files`（`image:<nanoid>`→Blob）、`media_files`（`file:<nanoid>`→Blob）；`agent_chat_messages`、`prompt_cache`、`tdcanvas-plugins`（插件沙箱库）、`workflow_library`（ComfyUI）。
- localStorage 小配置：`tdcanvas:aitudou_task_journal:v1`、`tdcanvas:dots-grid-v1:<projectId>`、`tdcanvas:image-quick-tools-v6`、`tdcanvas:side-panel-*`、`tdcanvas:agent-url/token`、`tdcanvas:locale`。
- 全自动保存，无手动保存；`updateProject` 刷新 `updatedAt`。

### 2.5 媒体双轨制与桌面缓存（Rust 侧）

- 用户上传/生成媒体存 localforage Blob；**远程生成产物桌面端额外落盘** `app_local_data_dir/media-cache`（`lib.rs:165-166`）。
- `media_cache.rs`：以 `sha256(source_url)` 为键去重（`:55`），命中直接返回（`:58-65`）；流式下载至 `.incoming-*.tmp` 边下边算 SHA-256，限 1GB（`:24, 68-89`）；文件名 = 净化原名 + 哈希前 12 位（`:548-564`）；索引 `manifest.json` 原子写（`:606-622`）。
- 安全校验：仅 HTTPS、禁凭据、SSRF 防护（拒绝 localhost/内网/保留 IP，DNS 解析后复验，`:388-470`）；mime↔扩展白名单（`:506-546`）。
- `import_legacy_cached_media`（`:133-230`）迁移旧 Web 版 `data/media-cache`（校验路径布局/manifest/字节数/内容哈希）。
- 前端稳定地址：桌面 `asset://`（convertFileSrc，`desktop-runtime.ts:29-31`），Web `/tdtv-media-cache/files/<filename>`（`local-media-cache.ts:120`）。
- 孤儿回收：`cleanupUnusedImages/Media` 以「assets+projects+extra」反查仍被引用的 storageKey 后删除（`use-asset-store.ts:94-100`；`image-storage.ts:89-103`）。

### 2.6 项目生命周期与隔离

- 列表按 `updatedAt` 倒序（`canvas-home.ts:14-16`）；封面**数据推导而非截图**：筛 AI 生成物（`sourceOrigin==="generated"`），优先级 imageHistory 各版本 > providerResult.outputs > 节点 content，取最新（`canvas-home.ts:23-56`）；渲染优先 localPath→storageKey 解析 blob URL，视频取 0.12s 帧（`canvas-project-cover.tsx:11-55`）。
- 打开项目恢复管线：`hydrateCanvasImages(resetInterruptedGeneration(migrateLegacyGenerationNodes(mergeAitudouTaskJournal(...))))`（`project.tsx:375`），随后清空 undo 栈与 pending 定时器（`:385-399`）。
- 中断恢复：journal（localStorage）记录在途任务，加载合回并标 `phase:"stopped"`（`aitudou-task-journal.ts:71-123`）；被中断 loading 节点标 error/stopped（`canvas-generation-helpers.ts:247-267`）。
- 导出 zip（fflate `zipSync level:0`）：`projects/<id>/files/<safeName>.<ext>` + 根部 `projects.json`（manifest `{app:"tdcanvas", version:3}`），递归收集全部 storageKey（`canvas-export.ts:11-32`）；另有单节点导出（`:34-65`）。**`importProject` API 已备好但无 UI 入口**（`use-canvas-store.ts:89-107`）。
- 删除项目/清空画布触发孤儿文件回收；clearCanvas 先 abort 全部生成请求（`project.tsx:1010-1022`）。

### 2.7 图片历史（版本模型）

- `CanvasImageHistoryEntry`（`canvas.ts:104-117`）；上限 **24 条**（`canvas-image-history.ts:4`），合并去重：签名 = `storageKey||localPath||sourceUrl||taskId||content`，id = FNV-1a `image-version-<base36>`（`:50-110`）。
- 版本切换 `imageHistoryMetadataPatch` 回写节点 metadata（`:34-48`）；objectReference 支持 `versionMode:"pinned"` 锁定版本（`canvas-resource-references.ts:174-190`）。
- 恢复链 `recoverRuntimeDiskCopy` 优先级：桌面直读 localPath → 迁移旧缓存 → `asset://` 视为持久 → Web 前缀持久 → 重新 `cacheRemoteMedia` 下载（`canvas-generation-helpers.ts:121-179`）。

### 2.8 主题

- `useThemeStore`（`"light"|"dark"`，默认 dark，`use-theme-store.ts:11-19`）；token 定义 `canvasThemes`：`canvas`（background/dot/line/selectionStroke/Fill）、`node`（label/fill/panel/stroke/activeStroke/text/muted/faint 等）、`toolbar`（panel/border/item/itemHover/activeBg/activeText）（`canvas-theme.ts:4-61`）。
- 消费：surface 写 CSS 变量 `--td-canvas-accent/neutral/vignette` + `data-canvas-theme`（`td-canvas-surface.tsx:215-228`）；grep `canvasThemes` 命中 10 个组件文件。

### 2.9 数据版本/迁移

- 项目文档**无 schema 版本号**、persist 无 migrate；版本化只在边缘（导出 version 3、Rust manifest version 1、localStorage 键自带版本）。
- 实际迁移三处：`migrateLegacyGenerationNodes`（旧 Aitudou/Config 节点按 outputHint 重写为原生 Image/Video/Audio/Text，`project.tsx:3988-4034`）、`migrateCanvasBackgroundMode`（lines→dots 一次性 + localStorage 标记，`:4198-4208`）、`importLegacyCachedMedia`（Rust 侧）。

## 3. 节点体系

### 3.1 类型全集与注册模型

- `CanvasNodeType` 枚举：Image/Text/Config/Video/Audio/Aitudou/Group（`canvas.ts:12-20`）；`CanvasNodeTypeId` 开放字符串，插件用 `"<pluginId>:<name>"`（`:22-23`）。
- **Aitudou 类型是遗留预留**：只在 NODE_SPECS 有规格（`constant/canvas.ts:107-119`），builtin-nodes 未注册（`builtin-nodes.tsx:22-28` 仅 Text/Image/Video/Audio/Config/Group），无创建入口。
- 默认尺寸表（`constant/canvas.ts:14-64`）：Image 620×350、Text 520×300、Config 340×240、Video 660×371、Audio 540×160、Aitudou 380×220、Group 760×480。
- 注册表 `node-registry.ts`（61 行）：两个 Map（definitions/ownerByType）+ zustand `version` 计数触发 UI 重渲（`:8-15`）；API：register/unregister/getNodeDefinition/getNodeSpec（未注册回退 FALLBACK_SPEC 340×240，`:50`）/isRegisteredNodeType。
- 内置注册：Image `#10b981`（keepAspectRatio: !freeResize）、Video `#f97316`（keepAspectRatio 恒 true）、Audio `#a855f7`、Config `#60a5fa`（无输出柄、不进创建菜单）、Group `#94a3b8`；均带 `builtinResource`（`builtin-nodes.tsx:12-39`）。
- **`CanvasNodeDefinition` 是可扩展节点的核心合同**（`types/canvas-plugin.ts:107-136`）：type/title/icon/defaultSize/defaultMetadata/minimapColor/showInCreateMenu/createMenuPlacement/hasSourceHandle/ports(可函数)/hidePanel/transparentBackground/autoOpenPanel/useBuiltinPanel/interactionToggle/forceInteractive/keepAspectRatio/resource/Content/Panel/toolbar/onDoubleClick。

### 3.2 节点渲染结构（`canvas-node.tsx`，1125 行）

- 根 `div[data-node-id]` transform 定位；标题栏悬浮节点上方（native 类 `top-[-40px]`），双击重命名（maxLength 64）。
- 内容区分发优先级：Config 面板 → 生成中玻璃遮罩（保留旧内容 + progress ≤99%）→ 批量根 → loading spinner → error 卡（含「查看错误详情」「重试」）→ 类型渲染表（Text=mention 编辑器/Image=object-cover+批量帧/Video/Audio=原生控件/Group=虚线区）→ 插件 Content → 缺插件占位（`:519-668`）。
- resize 手柄四角 `size-7` 位于角外 -14px（`:470-473, 1091-1100`）；port 圆点左/右外侧按 `(i+1)/(n+1)` 分布，48px 命中层，legacy 口仅 hover/选中/连线时可见（`:476-501, 1102-1125`）。
- 下方面板 `showPanel` 在 `top-full`（native 最小宽 760，`:503-507`）。

### 3.3 尺寸模型（`canvas-node-size.ts`）

- resize limits：min 220×160、max 1600×1200（`:8-13`）；锁比时以宽度驱动，`maxRatioWidth = min(maxWidth, maxHeight*ratio)`（`:17-31`）。
- resize 交互：位移更大的轴驱动；从左/上角拖反向调 position；`keepRatio = (Image && !freeResize) || Video || definition.keepAspectRatio`（`canvas-node.tsx:249-306`）。
- `fitMediaNodeGeometry`：按自然比例 fit 且**居中缩放**（位置补偿，`:44-55`）；`freeResize` 开关关闭时按自然比例回弹高度并保持垂直中心（`project.tsx:1827-1838`）。
- 上传图片 fit 后放大到最小 220×160；视频上限 660×520 最小 320×180（`project.tsx:143-174, 1584-1603`）。

### 3.4 选择 / 复制粘贴 / 删除 / 快捷键

- 选择：`selectedNodeIds: Set`；空白左键清选、**ctrl/cmd+拖空白=框选**、shift=加选；节点点选 shift/meta/ctrl 皆 toggle（`project.tsx:1270-1335`）；capture 阶段先选中保证 textarea/iframe 内点击也选中。
- 拖动联动：选中集 + 选中图片的 batch 子图 + 选中 Group 全部成员（`:1343-1352`）。
- 复制粘贴：内存剪贴板 `{nodes, connections}`（不写系统剪贴板）；连接仅保留两端都在选中集内；粘贴中心对齐画布中心、groupId 重映射、标题加 " Copy"、粘贴后全选；duplicate 偏移 +36,+36；**无 alt-drag 复制**；系统剪贴板兜底（图→图片节点、文→文本节点）（`:1025-1134, 1696-1733`）。
- 删除 `deleteNodes`：展开 batch 子图 → 停生成 → 清 objectReferences/groupId/batchRoot 主图重选 → 删相关连接 → 清 13 项悬空 UI 状态 → `cleanupCanvasFiles`（`:841-893`）；Delete/Backspace 等价，无选中时删选中连接（`:1780-1786`）。
- 快捷键全集（`:1735-1807`）：input/textarea/contenteditable 守卫；Cmd/Ctrl+Z(+Shift)/Y、+A 全选、+C 复制（有文字选区让位浏览器）、+V 粘贴、Delete/Backspace、Escape 清 13 项状态。**无** 缩放/对齐/复制样式类快捷键。
- 右键菜单（`canvas-context-menu.tsx:71-87`）：空白=上传/添加节点/撤销/重做/复制所有/粘贴；节点=制作副本/删除；连接=删除。

### 3.5 Group（几何包含式分组）

- 无显式成员列表：子节点 `metadata.groupId` 指向组；计数扫描（`project.tsx:656-663`）。
- 拖入判定 = **节点中心点**落在组矩形内（`canvas-node-geometry.ts:16-30`），pad=24 收进组内并写 groupId（`:32-47`）；拖组时成员联动（`project.tsx:1347-1351`）。
- Group 无 port、禁与组建连、z-[5] 低于普通节点、虚线边框、点击/复制/粘贴不开面板。

### 3.6 hover 工具条与节点信息

- 定位：水平居中、节点顶上方（标题净空 `(native?48:36)*k+8`；`canvas-node-toolbar-position.ts:3-10`）；仅 hover 或唯一选中时显示，拖动/缩放/设置打开时隐藏。
- 按钮集合（`canvas-node-hover-toolbar.tsx:145-196`）：info/delete 固定；retry（error 态）、saveAsset、download、edit（对话面板）、字号±（10–32）、upload 替换、图片快捷工具集（crop/split/upscale/angle/查看/反推提示词，可经 localStorage `tdcanvas:image-quick-tools-v6` 自定义显隐与标签）+ more（设置 Modal）；插件 `toolbar(ctx)` 注入 extraTools。
- `CanvasNodeInfoModal`：节点 ID/类型/尺寸/位置/状态/本地路径/批量数/提示词/错误详情/原始 JSON（base64 content 脱敏）（`:274-367`）。

### 3.7 生成状态呈现

- `status`: idle|success|loading|error（`canvas.ts:25`）；`providerTask.phase`: idle|queued|running|succeeded|partial|failed|attention|stopped（`:42`）。
- loading 无内容→spinner「生成中」；有内容→磨砂玻璃遮罩+progress；error→`providerTask.message || errorDetails` + 重试；running 节点及连线进入 `runningConnectionIds` 驱动流动光效（`project.tsx:693-707`）。

## 4. 交互与生成工作流

### 4.1 连线建立全流程

port mousedown（`canvas-node.tsx:485/498`）→ `handleConnectStart`（`project.tsx:1809-1818`）→ window mousemove 每帧 `getConnectionDropTarget` 更新吸附（`:1476-1480`）→ mouseup：命中口 `connectNodes`、近节点不兼容仅取消、**落空白弹 ConnectionCreateMenu**（文本/图片/视频/音频，`canvas-create-menus.tsx:16-43`）→ `createConnectedNode` 建节点+边+选中外开面板（`project.tsx:547-566`）。
- `connectNodes` 过 `normalizeConnectionHandles` 全部校验后 push（`:528-545`）。
- 连线仅在 `inputMode==="connections"` 渲染与交互；`objects`（无线引用）模式不渲染连线（`project.tsx:3703, 3760-3761`）。

### 4.2 连线语义 = 上游引用（数据流）

- 资源解析：Image/Video/Audio 的 `metadata.content` 即资源 URL，Text 的 `content||prompt` 即文本（`canvas-resource-references.ts:160-172`）；插件节点按输出端口暴露不同资源。
- 生成输入：连到 Config 则复用 Config 的输入，否则自身入边 + objectReferences 去重合并（`:85-107`）；上游文本直接拼接 `prompt + "\n\n" + upstreamText`，媒体进 referenceImages/Videos/Audios（`canvas-node-generation.ts:38-55`）。
- @mention：`buildNodeMentionReferences` 打标签「图片 N / 视频 N / 文本 N」（`:67-69, 153-158`）；contentEditable chip 输入 `@` 弹候选插缩略图 chip（`canvas-prompt-chip-input.tsx:86-328`）；Config composer 用 `@[node:<id>]` token 序列化。
- Aitudou 原生管线占位符：payload `@Image 1/@Video 1/@Text 1/@Task 1` 由 `injectConnectedReferences` 按模型 inputKind 注入（`aitudou-native-generation.ts:971-1003`）；运行时 `prepareAitudouPayload` 递归解析——文本直取、素材上传后替换公网 URL、task 引用取 taskId（`aitudou.ts:287-320`）。
- 无线模式：`addObjectReference` 写 `{sourceNodeId, versionMode:"latest"}` 且清掉已有连线（`project.tsx:905-923`）。

### 4.3 生成入口

- 原生面板运行按钮/回车（`aitudou-native-generation-panel.tsx:200-214, 489-500`）→ `handleRunAitudou`；旧版提示词面板 → `handleGenerateNode`；文本节点「生成图片」按钮 → 右侧 +96px 新建 Image 节点并连线（不直接生成，进面板确认参数）（`project.tsx:3425-3451`）；重试 → `handleRetryNode`；反推提示词 → 建 `midjourney.describe` Text 节点并连线（`:2462-2495`）。

### 4.4 Aitudou 生成管线（任务状态机）

- API：官方 `https://api.aitudou.net`，非 Tauri 走本地代理 `/tdtv-api/aitudou`；`Authorization: Bearer <API_KEY>`（`aitudou.ts:6-7, 281-285, 683-713`）。
- `runAitudouOperation`（`:111-176`）：操作契约（`aitudou-contract.ts`：通用 8 个 + Midjourney 16 个 + Suno 32 个操作，含 method/path/requestMode/requiredFields/defaultPayload/taskFamily/sync/outputHint）→ prepare（引用上传/占位符解析）→ validate → 按 requestMode 构造 body（json / multipart-upload / multipart-transcription）→ 提取 task_id → `settleAitudouSubmissions`。
- 轮询 `pollAitudouSubmission`（`:567-591`）：family→pollPath 映射（video/image/audio/midjourney/music），间隔 4s、超时 60 分钟、429/5xx 按 Retry-After 退避；abort → `AitudouPollingStoppedError`。状态归一化 phase ∈ queued|running|succeeded|failed|attention；Midjourney MODAL → attention（`aitudou-protocol.ts:41-63`）。
- 批量 `runAitudouOperationBatch`：batchCount 1–4 并行 `Promise.allSettled`；有失败/中断 → `partial`；有 attention → `attention`（`:178-234`）。
- **无远端取消**：只有「停止本地轮询」确认弹窗；停止后 message 记录「远端任务仍可能继续执行并计费」（`project.tsx:2196-2214, 2353-2365`）。
- 提交瞬间写 journal（localStorage），刷新后 `mergeAitudouTaskJournal` 恢复（`aitudou-task-journal.ts:21-123`）。
- 结果持久化 `persistAitudouRunResult`：先磁盘缓存（cacheRemoteMedia）再 IndexedDB，输出 `sourceUrl/localPath/storageKey`，失败分类计数（`aitudou-storage.ts:22-92`）。
- 页面编排 `handleRunAitudou`（`project.tsx:2112-2255`）：节点级锁 + `hasUnresolvedAitudouTask` 守卫**防重复计费**；queued/提交/进度/终态逐段更新 providerTask；不确定中断判定（status>0 的 ApiError / TypeError / 网络正则，`:4185-4190`）。

### 4.5 模型与参数

- 模型清单是**静态代码目录** `AITUDOU_MODEL_PROFILES`（`aitudou-models.ts:102-265`，约 123 个文档条目）：Seedance 2.0/2.5、Seedream v5、Qwen Image 3.0、Wan、Kling、Hailuo、Flux 3、Vidu、Doubao Seed Audio、Kimi、Whisper、Suno 等；每 profile 带 inputKind + constraints（seconds/resolutions/ratios/sizeRatios/maxImages/maxOutputs）。
- inputKind 自动匹配变体：有视频→v2v/edit/motion/multi；有图→i2i（限张数）→i2v→r2v→multi；否则 t2i/t2v（`aitudou-native-generation.ts:517-536`）。
- 尺寸三路径：sizeRatios 顶层 `size`；constraints.ratios 写 `metadata.ratio`（image 支持 adaptive）；Seedream 用虚拟路径 + `SEEDREAM_DIMENSION_TABLE`（19 比例 × 1k/2k 精确像素表）推导 width/height（`aitudou-aspect-dimensions.ts:24-43`）。
- 参考素材：一律物化为 Blob 再上传 `/v1/files/upload` 得 24h 直链（生成 CDN 短时效链必须重传，`aitudou.ts:593-681`）；上限 50MB。
- 价格：面板实时拉价格目录对每个模型报价（`aitudou-native-generation-panel.tsx:108-121, 224-243`）。

### 4.6 结果写回与批量堆叠

- `finishAitudouResult`（`project.tsx:2059-2110`）：主输出回写源节点（无 content 或图片节点时替换 content/mimeType/storageKey/naturalWidth...）；Image 节点全部 image outputs 合入 imageHistory（去重、上限 24）；**其余 outputs 各建新节点**（按 kind 映射类型，6 个一列排布）并与源节点建边；`aitudouOutputSignature` 防重复建节点。
- 旧版管线批量模型：count>1 时建 batch root（`isBatchRoot/batchChildIds/primaryImageId/imageBatchExpanded`）+ N 个 child，root↔source、root→child 连线；空 Image 节点原地替换；堆叠动效/展开收起/设主图（`project.tsx:2819-3239, 664-676, 1870-1921`）。
- 运行中连线流动光效 = 数据在流动的视觉表达（`project.tsx:701-707`）。

### 4.7 图片后处理五对话框

底层全部**原生 Canvas 2D 自研**（`canvas-image-data.ts`），产物 `toDataURL("image/png")` 再转存；远端图先解析 Blob 避免 canvas 跨域污染（`canvas-image-operation-source.ts:37-52`）。

| 对话框 | 能力 | 输出 |
|---|---|---|
| crop | 可拖/8 向 resize 裁剪框、比例预设、缩放平移视口 | 新建子 Image 节点（+96px）+ 连线 |
| split | rows/columns（≤12）、可拖分割线、undo/redo | N 个子节点按网格平铺 + 各自连线 |
| upscale | 目标长边 1K/2K/4K（≤4096）、算法 high（逐级 2 倍）/bilinear/nearest | 新建子 Image 节点 + 连线 |
| angle | 水平/俯仰/相机距离/镜头 CSS 3D 预览 | **走 AI**：image-to-image 模型 + prompt 生成（本地透视变换 `transformAngleDataUrl` 存在但无调用方，遗留代码） |
| mask edit | 画笔蒙版/擦除、笔刷大小、undo/redo | **全库无引用，未接线的死代码** |

### 4.8 工具栏体系 / 双击 / 拖放

- 左侧竖直 Dock（`canvas-toolbar.tsx:137`）：主「+」创建 flyout、搜索、资产、提示词、历史 flyout（undo/redo）、上传、外观 flyout（交互模式 连线/无线、明暗主题、点阵/线格/空白背景、图片信息开关）、删除（选中>0）、清空（确认弹窗）。
- Top bar：logo、汉堡菜单（首页/文档/项目列表/新建/删除当前/导入素材/undo/redo 含快捷键标注）、双击改项目标题、Agent 连接状态点、钱包余额、Agent 开关、快捷键弹窗（`canvas-top-bar.tsx:70-188`）。
- Side panel 三 tab：canvas（节点列表：过滤/聚焦/预览/导出）、assets（资产插入）、prompts（提示词库）；可拖宽（`canvas-side-panel.tsx:72-135`）。
- Zoom controls：小地图开关、连线显隐、网格吸附、重置视图、5–500% 滑杆、快捷键弹窗。
- 双击画布空白 → 该位置弹 NodeCreateMenu；双击节点 → batch 展开/插件 onDoubleClick/图片大图预览/文本进入编辑；双击标题 → 重命名。
- 拖放：图片 jpeg/png/webp、视频 mp4/mov/avi/mkv、音频 mp3/wav/flac（MIME 优先、扩展名兜底），单文件 ≤50MB；落点 40px 阶梯错位建节点，`sourceOrigin:"upload"`（`canvas-upload-material.ts:13-60`；`project.tsx:2772-2791, 1564-1632`）；文件选择器上传到空节点会**原地替换**节点类型。

## 5. canvas-agent：本地 Agent 通道

### 5.1 形态与安全

- 独立 Node 进程（`canvas-agent/package.json` bin `tdcanvas-agent`）：无参=HTTP，`mcp`=stdio MCP（`src/index.ts:5-6`）。
- HTTP 只监听 `127.0.0.1:17371`（`src/config.ts:6`；`src/server/http.ts:422`）；随机 token（`crypto.randomBytes(18)`，`config.ts:21`）+ **Origin 白名单**（首次带 token 连接的 Origin 记入 `~/.tdcanvas/tdcanvas-agent.json` 持久化，未记录 Origin 403；`http.ts:509-529`）。

### 5.2 双入口驱动

- **Codex**：spawn `@openai/codex`（锁 0.146.0）的 `app-server --stdio` 子进程，JSON-RPC（initialize/thread/turn/item，协议文档 vendored 于 `codex-server.md` 2175 行）。
- **Claude Code**：spawn `claude -p --output-format stream-json --allowedTools "mcp__tdcanvas__*"`（`src/agent/claude.ts:11`）。
- MCP server（stdio）不直接操作画布，回环 fetch 本地 HTTP `/api/tools`（`src/server/mcp.ts:28`）；Codex 侧经 `plugins/tdcanvas/.mcp.json` 注册。

### 5.3 桥接协议（SSE 推送 + HTTP 回传）

1. 网页持续 `POST /canvas/state` 上报快照 `CanvasSnapshot {projectId,title,nodes,connections,selectedNodeIds,viewport,clientId}`（`session.ts:305-311`）。
2. 读类工具从缓存快照直接返回（content 截断 240 字符）；写类工具经 **SSE `tool_call`**（带 requestId）下发，30s 超时；网页执行后 `POST /canvas/result` resolve（`session.ts:436-500`）。
3. 协议版本握手：SSE `hello` 事件 `protocolVersion`，两端常量 5，不匹配断开（`session.ts:26`；`local-agent-panel.tsx:71, 361-371`）。
4. 多标签页：turn 期间绑定发起标签页，按焦点序激活（`session.ts:72-74, 310-319`）。
5. 事件全集：hello/ping（15s 心跳）/codex_state/tool_call/codex_approval/agent_event/agent_bootstrap/conversation_changed/workspace_changed/chat_message/agent_log/skills_changed；断线重连可重放运行中 turn 快照（上限 240 条，`session.ts:386-433`）。
6. **写操作二次确认**：`canvas_apply_ops`/`canvas_create_attachment_nodes` 挂起 pendingTool 等用户批准（`agent-event-formatters.ts:493-495`；`local-agent-panel.tsx:782-794`）；Codex 自身审批透传 `codex_approval` 由网页代答；权限模式 request|automatic|full。

### 5.4 操作指令集（与插件共享）

- Agent 高级工具 30 个（`canvas-agent/src/canvas/schemas.ts:10-41`：canvas_get_state/get_selection/export_snapshot/apply_ops/create_*/generate_*/update_*/move/resize/delete/connect/select/set_viewport/run_generation/generation_get_status/prompts_search/assets_*/site_navigate）在 Agent 进程内编译为 `canvas_apply_ops` 下发（`src/canvas/operations.ts:10-71`；如 `canvas_generate_image` = 提示词文本节点 + config 节点 + 连线 + 选中 + run_generation，`@[node:<id>]` 引用）。
- Web 侧 `CanvasAgentOp` 8 种原语（`canvas-agent-ops.ts:8-16`）：add_node / update_node / delete_node / delete_connections / connect_nodes / set_viewport / select_nodes / run_generation；`applyCanvasAgentOps` 为纯函数计算新文档。
- 给 agent 的系统提示词 `agent-instructions.md`：默认只操作当前打开画布、先 get_state、附件必须先建真实图片节点、生成默认用 `canvas_generate_*`。

## 6. 插件系统与 comfyui-local

### 6.1 Manifest 与加载

- 清单即默认导出对象 `CanvasPlugin {id,name,version,description?,minAppVersion?,css?,nodes,setup?}`（`canvas-plugin.ts:148-157`）；`definePlugin` 仅类型帮助（`plugins/canvas/sdk/src/define-plugin.ts:12-16`）。
- 来源四路：官方注册表 URL（`VITE_PLUGIN_REGISTRY_URL`）、本地 `/plugins/index.json` 自动发现（默认禁用）、任意 JS URL 安装（源码缓存可更新/卸载）、dev 模式 `VITE_DEV_PLUGINS`（不落库）（`plugin-loader.ts:61-170`）。
- 持久化 `InstalledPlugin` 于 localforage（`use-plugin-store.ts:6-44`）；启用/停用即时 register/unregister + css 注入/移除 + setup 清理函数。

### 6.2 运行时：**无沙箱，主页面直接执行**

- 加载 = `new Blob([source])` + `createObjectURL` + 动态 `import()`，主文档主线程执行，**无 iframe/Worker**（`plugin-loader.ts:11-23`）；SECURITY.md 明示「可访问页面数据含本地凭证，是有意的扩展性取舍」（`SECURITY.md:21-24`；`plugins/canvas/README.md:168`）；管理器常驻黄色警示。
- PluginRuntime 单例挂 `window.TDCanvasRuntime`：React/jsx/injectCSS/emit/on（`plugin-runtime.ts:7-39`）——插件无需自带 React。
- `CanvasNodeContext` API（`canvas-plugin.ts:42-71`；`plugin-node-context.ts:8-33`）：node/theme/scale/isSelected、updateMetadata/updateNode、图读取（getUpstream/getDownstream 等）、**`applyOps(ops)`（与 Agent 同一指令集）**、事件总线、宿主 AI（generateImage/Video/Text/listModels）、openPanel/closePanel、按 pluginId 命名空间隔离的 storage（localforage）。
- 渲染：节点主体在 canvas-node 内、面板由 use-plugin-host 渲染、hover 工具栏注入 extraTools。
- 示例插件：markdown/svg/html/panorama/sticky-note（单文件 ESM、React external、重依赖 esm.sh 动态 import）；CI 构建到孤儿分支 `plugins-dist` 经 jsDelivr 分发；HTML 插件节点内容放 `sandbox iframe srcDoc`（唯一隔离点）。

### 6.3 comfyui-local（内置集成 = 插件路径最深的示范）

- 独立领域模块（contracts/core/frontend/tauri-plugin），不读 TDCanvas store。
- 只接受 **API Format JSON** 工作流（检测 `nodes/links` 即抛 ui-workflow-not-supported，`workflow-inspector.ts:34-48`）；`inspectComfyWorkflow` 把工作流与运行环境 `/object_info` 合并推导：输入按 valueType 推断（enum/STRING/INT/FLOAT/BOOLEAN/IMAGE/VIDEO/AUDIO + LoadImage 启发式），内部连线不可暴露，媒体/提示词类字段智能推荐（`:140-221`）；输出推 resourceType（IMAGE/VIDEO/AUDIO/text/file/json，MODEL/LATENT 等 opaque 不可序列化）（`:223-396`）。
- 固化为宏节点定义（校验摘要/依赖快照/默认值/控件类型/媒体输入 bypass 集合，`workflow-definition.ts:32-156`）；导入五步向导。
- Tauri 侧启动收敛：原生目录对话框（不接受任意路径）、main.py 必须在目录内、强制 `--listen 127.0.0.1` + 随机空闲端口 + `--disable-auto-launch`、额外参数白名单（拒绝 `--listen=0.0.0.0` 等）、退出树清理（`tauri-plugin/src/lib.rs:414-428, 428-450, 1455-1539`）。
- 执行闭环：前端永远只连 loopback ComfyUI；`runComfyWorkflowNode` = 收集上游资源（媒体上传本地环境）→ 物化 API JSON → `/prompt` 提交 → 轮询 `/history/{id}` → 为每个输出补建/复用结果节点写回 metadata——全程用 `ctx.applyOps`（`execution.ts:21-136`）；节点类型 `comfyui-local:workflow`，动态具名端口（`web/src/integrations/comfyui-local/canvas-node.tsx:38-122`）。

### 6.4 插件与 Agent 的关系

- **共享同一指令集**：`CanvasNodeContext.applyOps` → `applyAgentOps`（与 Agent 写画布同一路径，同样过 use-agent-bridge 的 undo 快照）。
- 反向：Agent `add_node` 可用插件注册的节点类型（`isRegisteredNodeType` 校验，未知回退 text）。

## 7. 证据边界与未决问题

- 全部结论来自**静态源码阅读**（锁定 `16b3127`），未做运行时审计（无浏览器 DOM/网络采样）；行为断言（如动画时长、命中半径手感）未经实机复核。
- **未与上游 `basketikun/infinite-canvas` 做 diff** → 已在 v2 完成，见 [UPSTREAM_DIFF_AUDIT.md](UPSTREAM_DIFF_AUDIT.md)：机制归属（继承 vs 原创）已建立，且发现上游（v0.19.0）比 TDCanvas（v0.14.0）更新，两仓双向演化。
- 已发现的死代码/未接线：Aitudou 节点类型（NODE_SPECS 有、未注册）、`importProject`（API 有、无 UI）、mask-edit 对话框（无引用）、`transformAngleDataUrl`（无调用方）、**chatSessions（v2 证实：完整数据链但无任何聊天 UI，见 §8.1）**。
- ~~`chatSessions` 助手面板未深挖~~ → v2 已覆盖（§8.1）；首页/资产库/提示词库/侧栏/Rust 命令面/i18n/lightbox 已覆盖（§8.2-8.8）。
- 行号随上游演进而老化；引用前应 `git log -1` 复核 HEAD 是否仍为 `16b3127`。

## 8. v2 补遗：周边表面

### 8.1 chatSessions 画布 AI 助手 = 无 UI 的遗留子系统（v2 关键发现）

- 类型齐备：`CanvasAssistantReference`/`CanvasAssistantImage`/`CanvasAssistantMessage`（role 含 user/assistant/system/tool/error，带 references）/`CanvasAssistantSession`（`types/canvas.ts:205-231`）。
- 数据链完整：挂在每个项目（`use-canvas-store.ts:17, 34, 79`）；打开项目经 `hydrateAssistantImages` 把 base64 落盘 image-storage（`project.tsx:376-394`）；纳入 undo 历史（`:129-130, 1228-1229`）；删除节点/清空画布参与孤儿图片回收（`:890, 1022, 318-320`）。
- **但全库无任何聊天 UI 消费它**：不存在会话列表/创建/切换/发送组件；`insertAssistantImage/insertAssistantText`（`project.tsx:3453-3491`）唯一调用方是资产插入 `handleAssetInsert`（`:3494-3520`）。
- 真实 AI 助手走 Agent 体系（`use-agent-store.ts:5-27`；`local-agent-panel.tsx` SSE + `use-agent-bridge.ts:43-74` applyOps 回写），与 chatSessions 无交集。

### 8.2 首页（`pages/canvas/index.tsx`）

- `?mode=new` 自动建项目、`?mode=recent` 进最近项目、`choose` 透传给 agent 面板；new/recent 渲染 "opening" 过渡（`:30-57`）。
- 分区：hero（kicker/标题/创建按钮 + 最近项目背景 showcase）+ 最近项目区（多选时批量导出/批量删除，否则「删除全部」；空态）（`:104-197`）+ 删除确认弹窗（`:200`）；指针驱动氛围光 CSS 变量（`:68-91`）。
- 卡片操作：打开/多选 checkbox/导出/重命名/删除/统计行 nodes+connections/更新时间（`canvas-project-card.tsx:27-105`）。
- showcase = 纯装饰演示壳（`canvas-home-showcase.tsx:26-150`：轨道流光 SVG、12 粒子、假 prompt/reference 浮窗、带 "live" 徽标的结果卡内嵌真实最近项目缩略；IntersectionObserver 可见时才播动画）。
- preview = SVG 线框图：前 18 节点归一化到 100×62、连线最多 24 条贝塞尔、image/video 渐变高亮（`canvas-project-preview.tsx:28-84`）。

### 8.3 资产库

- `AssetKind = text|image|video`（`use-asset-store.ts:10`）；API：addAsset/updateAsset/removeAsset（删后触发 cleanup）/replaceAssets/cleanupImages（`:77-100`）；persist `tdcanvas:asset_store`，读取时做 dataUrl→storageKey 迁移（`:41-67`）。
- 存为资产入口五路：节点 hover 工具栏「加入资产」（`project.tsx:2407-2456`）、侧栏上传、提示词页存文本、Agent 站点工具（`agent-site-tools.ts:155-178`）、资产管理页。
- 插入画布 `handleAssetInsert`：text→文本节点、video→规格节点、image→`uploadImage`+读元数据+视口中心建图节点（`project.tsx:3494-3520`）。
- 管理页 `pages/assets/index.tsx`：keyword/kind 过滤、分页、Drawer 表单、批量下载 zip、导入导出（`asset-transfer.ts`，唯一使用 readZip 的地方）。

### 8.4 提示词库

- 源模型：用户自建 JSON 源（name/url），**`DEFAULT_PROMPT_SOURCES = []` 无内置预设**（`prompt-source-presets.ts:23`）；刷新间隔档 [0,30,60,360,1440] 分钟（`use-prompt-source-store.ts:18`）；builtIn 源不可覆盖/删除。
- 取数：每源 localforage 缓存 `prompt-source:{id}`，TTL 1h，过期或签名变化后台刷新、失败回落旧缓存（`prompts.ts:48-124`）；60s 心跳调度器只刷到期源（`use-prompt-source-scheduler.ts:13-32`）。
- 画布内入口：节点 prompt 面板书本按钮 → PromptSelectDialog 选词回填（`canvas-prompt-library.tsx:10-30`）；独立页 `pages/prompts/index.tsx` 分类/标签/无限滚动/存为资产。

### 8.5 侧栏 canvas tab（`canvas-side-panel.tsx:157-296`）

- 类型过滤（all/image/video/text/audio/config/group）+ 关键字搜索（title+content+prompt）；单击聚焦、图片 Eye 大图预览、右缘状态点（success/loading/error）；多选模式 + 全选/清空 + 批量导出 `exportCanvasNodes`。
- 面板宽度指针拖拽 220–480px、持久化 `tdcanvas:side-panel-width`；首次访问默认收起（`tdcanvas:compact-shell-v1`）。

### 8.6 Rust 命令面（`src-tauri/src/lib.rs`，media_cache 之外）

- `frontend_ready` / `splash_animation_complete`：闪屏揭示主窗（4s 动画兜底/10s 强制揭示，`:57-71, 176-190`）。
- `open_downloads_directory`（平台 explorer/open/xdg-open，`:73-89`）；`open_aitudou_registration`（打开注册页，`:91-107`）；`allow_download_directory`（把自定义下载目录加入 fs scope，`:109-137`）；`cache_remote_media` / `import_legacy_cached_media`。
- 无剪贴板/自定义更新器命令（updater 用官方插件 + `desktop-updater` feature）；插件注册 http/dialog/fs/process + `tdcanvas_comfyui_local`（`:143-154`）。
- 前端封装 `desktop-runtime.ts`：`platformFetch` 桌面走 tauri http、`desktopFileUrl`=convertFileSrc（`asset://`）、`readDesktopFileBlob`、`syncDesktopWindowTheme`、`saveBlobToDownloads`（自动防重名 + 自定义下载目录 `tdcanvas:download-directory`）。

### 8.7 i18n

- 仅 zh-CN（默认）与 en-US；`tdcanvas:locale`；顶栏「中/EN」切换（`user-status-actions.tsx:53-57`）；zh-CN 1867 行 / en-US 1909 行，canvas 命名空间 ≈540 key 为最大段（`i18n/index.ts:12-25`）。

### 8.8 图片大图预览

- 双击图片 → antd Modal 纯 `<img>` contain 预览（maxHeight 80vh），**无缩放/平移/对比**（`project.tsx:3953-3963`）。
- `use-image-editor-viewport`（1–4x、指针锚缩放、Space/中键平移、fit）的真实消费方是 crop/split/mask 三个编辑对话框，非 lightbox。
