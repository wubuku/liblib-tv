# Big Picture: LibTV + FrameOS Canvas Clones

> 本文回答“这个仓库整体在做什么、两条克隆路线如何组织、哪些是当前实现、哪些只是研究证据或原型占位”。
>
> **当前实现的信息优先级**：当前运行态与 `src/` 源码 > 原站截图/原始提取数据 > research 总结文档 > 模板 README。历史研究文档可能保留旧实现或原站观察，出现冲突时不要直接照抄。
>
> **克隆流程的指引**：`.claude/skills/clone-website/SKILL.md` 是共享源文件，`.codex/skills/clone-website/SKILL.md` 是同步后的 Codex 技能副本。它们规定如何从目标 URL 产出研究证据、组件规格和实现；修改共享技能后需运行 `node scripts/sync-skills.mjs`。
>
> **当前 LibTV 原站基线**：[`research/liblib-live-2026-08-25/README.md`](research/liblib-live-2026-08-25/README.md) 汇总了本轮登录态原站复核、结构化抽取、缺口分级和价值排序。旧 LibTV research 文档表示更早的采样时点。

## 1. 项目本质

这是一个面向 **AI 画布产品逆向研究** 的前端原型仓库，不是 LibTV 或 FrameOS 的完整业务系统。

仓库同时维护两条平行实验：

- **`/`：LibTV 画布克隆**。重点是视频故事板工作流、异构节点、连线反馈、素材/角色/运镜等编辑器外壳。
- **`/frameos/*`：FrameOS（帧界）画布克隆**。重点是深色无限画布、AI Prompt 操作、节点浮动工具、缩略地图、面包屑和编辑器级快捷键。

它的核心价值不只是“有两个页面”，而是保留一条可复用的验证链：

```text
原站可观察行为
  -> 截图、DOM、computed style、原始 JSON
  -> 页面拓扑 / 行为 / 设计令牌 / 组件规格
  -> React + React Flow 原型实现
  -> 本地运行、截图对照、交互回归
```

因此，这个仓库更接近 **产品研究实验室 + 可执行规格**，而不是生产应用。

### 1.1 `clone-website` 技能的角色

`clone-website` 是这个仓库执行网站克隆时的**流程控制面**。当输入一个或多个目标 URL 后，它要求按以下阶段推进：

```text
Pre-flight
  -> 浏览器工具与 URL 可访问性检查
  -> 基础项目 build 检查

Reconnaissance
  -> desktop/mobile 截图
  -> 字体、颜色、meta、全局模式和素材提取
  -> scroll/click/hover/responsive 全量交互扫描
  -> PAGE_TOPOLOGY + BEHAVIORS

Foundation
  -> 全局 tokens、字体、类型、SVG、本地 assets
  -> build 验证

Component loop
  -> 按页面区域逐个提取 computed styles 和所有状态
  -> 先写 component spec
  -> 再把小任务派给独立 worktree 中的 builder
  -> 持续合并并验证 build

Assembly + Visual QA
  -> 组装页面级布局和交互
  -> 原站/克隆在 1440px 与 390px 下逐段对比
  -> 重新验证 scroll/click/hover 等行为
```

它有几个不可降级的约束：

- 必须使用浏览器自动化；不能只根据用户截图或主观印象实现。
- 必须提取真实内容、字体、图片、视频和 SVG，包括叠层素材。
- 必须先判定交互由 click、scroll、hover、time 中哪一种机制驱动。
- 必须覆盖默认态之外的所有关键状态和响应式断点。
- 每个 builder 开工前必须已有 `docs/research/components/*.spec.md`。
- builder 任务应足够小；规格超过约 150 行时要继续拆分。
- foundation 先串行建立，组件提取与构建随后可在隔离 worktree 中并行。
- 每次合并都要保持 build 可用，最终还必须做视觉和交互 QA。

因此三类内容各有职责：

| 层级 | 位置 | 职责 |
|---|---|---|
| 流程指引 | `.claude/skills/clone-website/SKILL.md` | 规定“怎么研究、怎么拆分、怎么构建、怎么验收” |
| 证据与规格 | `docs/research/`、`docs/design-references/` | 保存“原站实际是什么样、如何行为” |
| 可运行实现 | `src/`、`public/` | 保存“当前克隆实际做到了什么” |

技能本身不是应用运行时依赖，也不是原站事实数据库。它负责组织工作；具体事实仍应来自当次浏览器提取结果。

## 2. 明确的非目标

当前仓库没有以下生产能力：

- 后端 API、数据库、鉴权、文件存储或协作同步
- 真正的 AI 图片/视频生成服务
- 可恢复的持久化项目数据
- 完整的上传、下载、计费、会员或桌面端集成
- 与原站相同的数据协议和业务权限系统

绝大多数状态只存在于浏览器内存。刷新页面会回到 mock 初始数据。

## 3. 系统全景

```text
Next.js App Router
├── RootLayout
│   ├── globals.css                    LibTV tokens + React Flow 全局规则
│   ├── /                              LibTV client canvas
│   │   ├── ReactFlow controlled graph
│   │   ├── LibTV node components
│   │   ├── DeletableEdge
│   │   ├── liblibOrganize             整理拓扑、fallback 与 viewport 计算
│   │   ├── canvasStore                画布数据
│   │   └── uiStore                    面板与显示设置
│   │
│   └── /frameos
│       ├── frameos layout
│       │   └── frameos-canvas.css     FrameOS scoped overrides
│       ├── /frameos                   redirect
│       └── /frameos/canvas/[id]       FrameOS client canvas
│           ├── ReactFlow controlled graph
│           ├── FrameOS node shell + 3 renderers
│           ├── FrameosEdge
│           ├── floating editor UI
│           └── frameosStore           画布、UI、history、generation mock
│
├── public/images                      两条路线的本地 mock 素材；liblib-panels 可由审计脚本重建
└── docs
    ├── research                       原站观察、提取数据、组件规格
    └── design-references              原站与克隆迭代截图
```

两条路线都是大型 Client Component。Next.js 主要负责路由、布局、构建和静态资源交付；编辑器逻辑基本都在浏览器中执行。

## 4. 两条路线的当前边界

| 维度 | LibTV | FrameOS |
|---|---|---|
| 入口 | `/` | `/frameos` 重定向到 `/frameos/canvas/demo` |
| 页面控制器 | `src/app/page.tsx` | `src/app/frameos/canvas/[id]/page.tsx` |
| Store | `canvasStore` + `uiStore` | `frameosStore` |
| 已注册节点 renderer | 8 种：script/image/text/video/script-execution/storyboard-group/shot-breakdown/video-clip | 3 种：text/image/video |
| 初始运行态 | 10 节点、11 边；桌面 53%、紧凑视口 28% | 7 节点、5 边 |
| 边 renderer | `DeletableEdge` | `FrameosEdge` |
| 主题 | 深灰 + 青色强调 | 更深黑底 + 蓝色强调 |
| 多画布模型 | `canvases[]` + `activeCanvasId` | breadcrumb key + mock `canvasData` |
| 交互成熟度 | 壳层、主控制、模式、关键抽屉和一级内容面板已闭环；后端仍是 mock | 编辑器命令和浮层较多，但不少仍是 mock 或未闭环 |

`/frameos/canvas/[id]` 的 `[id]` 当前只是路由占位符。页面没有用它加载不同数据，任意 ID 都进入同一组前端 mock 状态。

## 5. LibTV 运行模型

### 5.1 页面控制器

`src/app/page.tsx` 将 `canvasStore` 中当前画布的 `nodes` / `edges` 作为 React Flow 的受控输入：

```text
React Flow change
  -> applyNodeChanges / applyEdgeChanges
  -> setNodes / setEdges
  -> 更新 active canvas
  -> React Flow 重新渲染
```

页面还负责：

- 注册 8 个节点组件和 `DeletableEdge`
- 建立新连线
- 处理节点选择、画布空白点击和键盘删除
- 支持多选/框选、成组/解组，以及选择集合的移动和复制事务
- 在选择工具中用空白拖动框选；`H` 持久抓手、`V` 恢复选择、按住 `Space` 临时平移
- 监听 `delete-edge` CustomEvent
- 同步 React Flow viewport 与实际缩放百分比
- 在 `929px+` 使用原站 53% 构图，在 `768px-` 使用原站 28% 紧凑构图
- 整理时调用 `liblibOrganize`，按保存的原站截图重建素材、执行/分镜、分组/视频和剧本的语义拓扑，并显示左下保留/还原卡
- 组合顶部浮动导航、底部主工具条、底部画布控制、资产/Agent 抽屉和快捷键弹窗
- 编排六个不同拓扑的一级入口面板，并保持入口互斥
- 在工作台与分镜模式之间切换；分镜模式会同步打开 Agent

### 5.2 状态边界

`canvasStore` 管：

- 画布列表、当前画布
- 每个画布的 nodes、edges、viewport
- group hierarchy；当前原站视频组通过 `parentId` 包含相对 `(62,62)` 的失败视频
- 当前选中节点 ID 集合，以及用于兼容单节点浮层的主选中节点 ID
- 增删改节点、边和画布

`uiStore` 管：

- 面板显隐
- grid/minimap/edge/snap 开关
- 工作台/分镜模式、移动/抓手工具
- 分享弹层、Agent 抽屉
- 与 React Flow viewport 同步的 zoom 百分比

部分短生命周期 UI 仍保留在组件本地状态中，例如主工具条的当前内容面板、缩放菜单和顶部项目名。这意味着 LibTV 当前不是单一、完整的编辑器状态机，而是 **画布数据 store + UI store + 局部组件状态** 的组合。

整理预览快照也属于页面局部状态。节点位置变化进入 `canvasStore` 的 graph history，viewport 只随预览快照恢复，不进入通用 undo/redo。

### 5.3 节点系统

LibTV 节点各自直接实现卡片、Handle 和专属交互，没有统一 NodeShell：

- `ScriptNode`：剧本文本
- `ImageNode`：按原站尺寸渲染图片和悬浮元数据；顶部工具条使用 React Flow `NodeToolbar` 锚定节点并保持屏幕尺寸，底部编辑面板挂在节点内并用 `1 / zoom` 反向缩放。编辑面板按空白、提示词、带参考图三种源站状态呈现，高价值工具会创建连接到源图片的派生节点
- `TextNode`：文本
- `VideoNode`：既保留当前项目中的失败视频，也支持就绪视频、Seedance 2.5 生成面板、处理工具条、片段重拍和智能续写
- `ScriptExecutionNode`：步骤状态
- `StoryboardGroupNode`：图片组/视频组背景容器；当前视频组是真实 parent，失败视频是相对 `(62,62)` 的 child，图片组为空
- `ShotBreakdownNode`：逐帧拉片素材、拆解维度和本地结果卡
- `VideoClipNode`：智能剪辑 Beta 四模式空态

当前初始画布按原站结构化数据放置 10 个节点和 11 条边。`AddNodePanel` 展示原站的 9 个节点入口；逐帧拉片与视频编辑已有专用 renderer，导演台、音频等尚未专门实现的类别仍映射到最接近的原型节点。

视频组父子关系不是根据画面猜测：原站视频组 DOM 有 `.parent`，当前 xyflow v12 只在 `parentLookup` 有 child 时添加该 class；失败视频与组的绝对坐标差又是 `(62,62)`。clone 因此用真实 `parentId` 表达该关系。group 复制会带 descendants，单独复制 child 会转成顶层副本，删除 group 会级联 child 与相关边。

图片节点浮层不能使用页面固定坐标。原站的上工具条与下编辑器都以选中节点的屏幕中心为锚点；前者由 React Flow 在非缩放层定位，后者位于节点内部并反向缩放。它们允许超出画布边界后被裁切，不会为了保持可见而重新居中到浏览器视口。

## 6. FrameOS 运行模型

### 6.1 页面控制器

FrameOS 页面同样使用受控 React Flow，但承担了更多编辑器编排：

- 节点/边 change、连接和选择
- 连接中的有效目标视觉状态
- 全局键盘快捷键
- 节点和画布右键菜单
- 删除确认和 Toast
- Header、ToolRail、MapDock、PromptEditor、浮动工具条等 overlay 组合

FrameOS 必须在 `applyNodeChanges` 后重新应用 `selectedNodeId` 对应节点的 `selected: true`。这是 xyflow v12 在本项目中的关键兼容处理，删除后会导致选中态和选中节点浮层消失。

### 6.2 Store 是原型状态机，不是持久化模型

`frameosStore` 同时包含：

- 当前 nodes / edges
- breadcrumb 和 mock 多画布数据
- selectedNodeId
- undo / redo 栈
- minimap、菜单、帮助、调试态
- prompt、模型选择
- 删除确认
- 30 秒 generation mock

但它仍有明确原型边界：

- `setNodes` / `setEdges` 不会把修改同步回 `canvasData`
- `setBreadcrumb` 从常量 `MOCK_CANVASES` 重新取数据
- history 只覆盖部分命令，不是完整事务日志
- `generations[]` 尚未形成任务历史，主要使用 `currentGeneration`
- Store 支持 8 种 node kind，但页面只注册 text/image/video 三种 renderer

因此，FrameOS 的“多画布”和“历史”应理解为交互演示，不是可靠的数据层。

### 6.3 节点与浮层

text/image/video 三种节点共用 `FrameosNodeShell`，由它统一：

- 浮动标题与双击重命名
- 左右 Handle
- 选中 class
- resize Handle 外观

React Flow v12 不会把 `node.style` 作为自定义节点 prop 传入。节点尺寸应从 store 中的 node 或 `props.measured` 获取，不能依赖 `props.style`。

选中节点后：

- `FrameosNodeFloatingToolbar` 用节点 DOM 的 `getBoundingClientRect()` 每帧跟随节点
- `FrameosPromptEditor` 当前固定在视口右下方，不跟随节点
- `FrameosNodeEditPanel` 仅在 `isDebugMode` 为 true 时显示

当前没有可见的 DEBUG 开关；需要通过 `window.__frameos_store.getState().toggleDebugMode()` 或代码触发。旧文档中“右下角 DEBUG 按钮”的描述已经过时。

## 7. 实际共享与刻意隔离

### 真正共享

- `@xyflow/react` 的画布、Node、Edge、Handle 基础能力
- Next.js / React / TypeScript / Tailwind 工具链
- Zustand 的状态管理方式
- `cn()` utility
- 本地资源组织和逆向研究方法
- 一些全局 React Flow CSS 基础规则

### 刻意隔离

- 两套 store
- 两套节点数据语义
- 两套路由壳和工具布局
- 两套节点 renderer
- 当前的两套边 renderer：LibTV `DeletableEdge`、FrameOS `FrameosEdge`
- 两套视觉 token 和局部 CSS

不要用一个 `mode` 字段统一两条路线。它们相似的是编辑器基础设施，不是业务状态。

共享 CSS 仍然是高风险区域。`globals.css` 对所有 React Flow 元素生效，FrameOS 再用 `.frameos-canvas` 覆盖；修改 Handle、Edge、selection 等规则时必须同时检查两个路由。

## 8. 研究资料如何阅读

### LibTV

- `docs/research/liblib-live-2026-08-25/README.md`：当前事实基线、缺口审计、价值排序和本轮范围
- `docs/research/liblib-live-2026-08-25/BATCH_1_PANELS.md`：六个主工具栏入口面板的差距、优先级和验证
- `docs/research/liblib-seedance-2.5-2026-08-25/BACKGROUND.md`：外部调研中关于 LibTV 有什么的持久化背景知识
- `docs/research/liblib-seedance-2.5-2026-08-25/`：Seedance 2.5 近期能力的线索、原站复核、实施计划与结果历史
- `docs/research/liblib-live-2026-08-25/*.json`：10 节点、11 边与首屏 DOM 的结构化抽取
- `docs/research/PAGE_TOPOLOGY.md`：页面区域与层级
- `docs/research/BEHAVIORS.md`：交互目录
- `docs/research/DESIGN_TOKENS.md`：颜色、尺寸、阴影
- `docs/research/components/*.spec.md`：组件级规格

### FrameOS

- `docs/research/frameos/*.json`：从原站提取的结构化原始数据
- `docs/research/frameos/original-*.png`：原站状态截图
- `PAGE_TOPOLOGY.md` / `BEHAVIORS.md` / `DESIGN_TOKENS.md`：研究总结
- `IMPLEMENTATION.md` / `RUNBOOK.md`：某一实施阶段留下的经验文档

### 视觉迭代

`docs/design-references/` 混合保存：

- 原站参考
- 克隆过程截图
- bug 诊断截图
- 阶段性“final”截图

文件名里的 `final` 不代表当前源码仍与该截图一致。判断现状应重新运行页面。

## 9. 当前原型成熟度

| 方面 | 当前判断 |
|---|---|
| 视觉研究 | 资料丰富，包含原站截图、计算样式、原始 JSON 和大量迭代图 |
| 画布基础 | Pan/zoom/drag/connect 已由 React Flow 支撑 |
| 节点交互 | 两条路线都有可操作节点；LibTV 的逐帧拉片/智能剪辑已有专用节点，其余未实现入口使用显式原型映射 |
| 编辑器命令 | LibTV 的添加、移动模式、缩略图、连线、吸附、缩放、整理、资产、分享、Agent、分镜模式和一级内容面板已闭环 |
| 数据生命周期 | 内存 mock；刷新丢失；画布切换也不是可靠持久化 |
| AI 能力 | 仅 prompt UI 和计时 generation mock |
| 自动化验证 | `npm run check` 可用；现有 FrameOS E2E 尚未接入依赖且选择器已漂移 |
| 部署 | Next standalone build + Dockerfile / compose，可作为纯前端原型部署 |

当前快照中仍存在的主要原型边界：

- 根 `README.md` 和 `package.json` 仍保留通用 website-cloner 模板身份
- LibTV 内容库已具备原站拓扑和本地真实样例素材，但账户数据、下载和生成调用仍是 mock
- LibTV 分镜模式和 Agent 是可验证的前端原型，没有接入真实任务、模型或历史数据
- LibTV 未实现后端生成、上传、分享链接、项目持久化和协作权限
- LibTV 的整理位置针对当前 10 节点项目使用截图反推映射；未知节点只有稳定 fallback，不代表已复刻原站通用布局算法
- FrameOS `duplicateNode` 已构造副本对象但没有把它加入 nodes，复制快捷键当前不会新增节点
- FrameOS Prompt 顶栏的“删除连线”当前调用的是删除节点逻辑
- 旧 E2E 仍查找 `.floating-toolbar`、`.canvas-footer-prompt`、`.debug-toggle` 等历史选择器

这些不是 Big Picture 的目标功能，而是说明仓库仍处于持续研究和原型迭代阶段。

## 10. 修改项目时的推荐路径

### 修改某条路线

1. 先确认目标是 LibTV 还是 FrameOS。
2. 读对应 route page，确认 renderer 和 overlay 的真实挂载关系。
3. 读对应 store，确认状态归属和 mutation point。
4. 对照原站证据，而不是只对照旧实施文档。
5. 修改后至少检查两个路由是否仍可渲染。

### 修改共享 React Flow 样式

1. 检查 `globals.css`
2. 检查 `frameos-canvas.css` 的覆盖关系
3. 验证 Handle 是否仍可拖拽连接
4. 验证 edge hover/selection
5. 验证节点 selected 状态和浮层

### 增加节点类型

仅在 store/type 中加入 kind 不够。必须同时补齐：

- 类型定义
- 默认数据和尺寸
- React Flow renderer
- `nodeTypes` 注册
- 添加节点入口
- 类型专属工具栏/Prompt 行为
- 视觉和交互验证

## 11. 推荐阅读顺序

新接手项目时：

1. 本文
2. `AGENTS.md`
3. 对应 route page
4. 对应 store
5. 对应节点组件或 `FrameosNodeShell`
6. 对应 research 行为/拓扑文档
7. 原站截图与原始提取数据

如果旧文档与代码冲突，先确认当前运行态，再决定是代码回归还是文档过时。不要默认其中任一方天然正确。

## 12. 本轮验证基线

- `npm run check`：lint、typecheck、production build 通过；lint 有 9 个既有 warning，集中在 FrameOS 和 `CustomHandle`
- `python3 scripts/verify-liblib-batch4.py` 到 `verify-liblib-batch8.py`：多选/成组、移动/复制、导航手势、整理预览和视频组 hierarchy 全部通过
- `/` 运行态：10 节点、11 边；边关闭后 DOM 为 0 条，重新开启恢复 11 条
- 桌面 `929x874`：53% 视口，主工具条 `338x49`，画布控制 `273x40`
- 整理预览 `929x874`：28% 视口；关键节点位置在 `3px` 容差内，左下确认卡约 `168x88`
- 整理预览 `1440x900` / `390x844`：约 46% / 10%，无页面横向溢出
- 视频组：原站 `.parent` class 与相对 `(62,62)` 已复刻；parent/child drag、group/child copy、级联删除和 history 通过
- 平板 `768x900` 与手机 `390x844`：28% 视口；手机主/次工具条分别位于 `y=743/792`
- minimap：开关后渲染 `150x110`；zoom 菜单、吸附和点阵开关可操作
- 资产管理：`240px` 左抽屉，桌面画布从 `929px` 收缩为 `689px`，列出 10 个节点
- Agent：`340px` 右抽屉；分镜模式自动打开并渲染故事板列
- 图片选中态：页面级 `900x49` 工具条和 `660x274` 编辑面板，包含原站提示词与生成参数
- 六个主入口面板：桌面锚点与原站一致；角色应用可创建可见节点；`390x844` 无检测到的标签溢出
- 添加、分享、整理保留/还原、整理后 undo/redo、工作台/分镜切换均完成浏览器交互验证
- `/frameos/canvas/demo` 运行态：7 节点、5 边
- FrameOS 选中节点后浮动工具条与 PromptEditor 可见
- 浏览器巡检未捕获 page error；开发态仅出现 Next Image LCP 提示，已为首屏画布图设置 eager loading
- `e2e/frameos.spec.ts` 未运行：仓库未安装 `@playwright/test`，且测试选择器与当前实现不一致
