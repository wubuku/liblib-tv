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
| Store | `canvasStore` + `uiStore` + `directorStore` | `frameosStore` |
| 已注册节点 renderer | 11 种：script/image/text/video/script-execution/storyboard-group/shot-breakdown/shot-breakdown-result/video-clip/audio/long-video-process | 3 种：text/image/video |
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

- 注册 11 个节点组件和 `DeletableEdge`
- 建立新连线
- 处理节点选择、画布空白点击和键盘删除
- 支持多选/成组/解组，以及选择集合的移动和复制事务；历史 Batch 6
  曾实现空白框选，但 2026-08-28 源站 runtime 核对后已由 Batch 77 supersede
- 普通滚轮/触摸板滚动平移，中键拖动平移；`H` 持久抓手、`V` 恢复选择、
  按住 `Space` 临时平移；`Command/Control` + wheel 或触摸板 pinch 缩放
- `V` 下空白左键拖动是 no-op；当前操作入口见 [`CANVAS_NAVIGATION.md`](CANVAS_NAVIGATION.md)
- 监听 `delete-edge` CustomEvent
- 同步 React Flow viewport 与实际缩放百分比
- 在 `929px+` 使用原站 53% 构图，在 `768px-` 使用原站 28% 紧凑构图
- 整理时调用 `liblibOrganize`，按保存的原站截图重建素材、执行/分镜、分组/视频和剧本的语义拓扑，并显示左下保留/还原卡
- 组合顶部浮动导航、底部主工具条、底部画布控制、资产/Agent 抽屉和快捷键弹窗；Agent 打开时顶部导航避让右抽屉，资产抽屉打开时项目/画布上下文进入左抽屉且 mode 控件避让其右边界
- 编排六个不同拓扑的一级入口面板，并保持入口互斥
- 在工作台与分镜模式之间切换；分镜模式会同步打开 Agent，并将当前画布投影为“关键元素”资源栏与“图片 / 视频”故事板列
- 从 `3D导演台` 节点按需载入全屏 R3F 工作区；主 React Flow 保持挂载，
  截图通过一个原子 graph transaction 回流为 image node + source edge；
  工作区底部的 typed timeline 可 scrub/playback 并确定性驱动场景与机位；
  transform/camera track 还可绑定预设运动路径和 cubic-Bezier 速度曲线；
  角色支持关节化 R3F mannequin、20 个 source-named 姿势预设、SAM 分组调节
  和可与 transform 同时采样的独立 pose track；机位支持手动坐标/旋转/对象
  注视、目标跟随、第一/第三人称，并在所有普通轨道采样后解析目标关系；
  相机轨道还支持七种 source-named 预设运镜的替换/追加生成和 follow/
  no-room guards

StoryAI 借鉴与 Director 当前进展已有独立跨批次权威：固定上游、能力对照、
运行态复核、证据边界和后续路线见
[`storyai-3d-director-desk-2026-08-27/`](research/storyai-3d-director-desk-2026-08-27/README.md)。
当前结论不是“功能未够多”，而是可见能力已经超过上游，下一阶段应优先补
per-project scene、生产级资源生命周期和统一 Director gate；clone-owned 的版本化项目
持久化、严格 JSON 导入/导出、资源清理和 owner 生命周期 focused pass 已经落地，
但不能写成 LibTV 原站的 source-exact 行为；
领域 undo/redo、完整 pointer lifecycle 与 reference-aware delete 已先形成
clone-owned focused pass。
Batch 66 已将这项判断进一步固化为 `DEC-040`、两份 Director authority contract、
17-script current verifier manifest 和 `LIBTV-VR-024`。Batch 67 已实现独立
`DirectorProjectDocumentV1`、strict decode/normalize/encode、当前 state snapshot
adapter 和 17-case pure corpus；它明确排除 selection/playback/panel/phone runtime、
capture bytes、Three.js refs 与 graph projection。当前日常 gate 是 Batch 67 pure
codec + Batch 68 owner/session + Batch 69 authored/runtime + Batch 70
command/history + Batch 71 pointer lifecycle + Batch 72 reference delete +
Batch 73 async authority + Batch 74 browser-local persistence + Batch 75
clipboard identity remap + Batch 76 owner reachability + Batch 78 pointer
cancellation + Batch 59 browser smoke + Batch 94 focus containment when Director
focus behavior changes。Batch 68 已建立
route/canvas/source owner、per-owner in-memory project、fresh session/generation、
A/B/cross-canvas restore 和 memory capture sidecar，单例跨 node 串场风险已在同步
focused slice 关闭。Batch 69 又把 portable `authoredObjects` 与当前 R3F/timeline
`objects` projection 分开，seek/playback/path sampling 不再污染 project snapshot，
对象/相机/姿态编辑及 close/reopen 恢复已有 focused verifier。Batch 70 又落地 typed
project-local command result、bounded `past/future`、undo/redo、redo truncation、
repeated gesture coalescing 和 close/reopen history continuity；当前真实 adapter
只覆盖 object/group TransformControls 与 speed curve。Batch 71 已补齐 Inspector/
pose/camera/path/free-draw 的 focused pointer lifecycle；Batch 72 又补齐
reference-aware delete 的关系闭包、相机回退、资源阻断/级联和 exact
delete/undo/redo。Batch 73 又为 capture、animation export 和 phone take import
补齐 operation/attempt、owner/session/generation、source/request fingerprint、
terminal convergence 和 export Blob URL transfer/release。Batch 74 已为
Director 增加 browser-local versioned envelope、
strict reload restore、stale save、坏数据零替换和 storage-failure
`SESSION_ONLY` continuity。Batch 75 又增加 project-scoped session clipboard、
typed entity closure、two-pass ID/reference remap、camera detach/freeze、stable
resource alias、one-entry paste history 和 guarded `Cmd/Ctrl+C/V`。inactive-owner
reconciliation 已由 Batch 76 以 all-canvas live owner planner、inactive
source/canvas one-time tombstone、active shell/session/runtime 两阶段 cleanup、
graph undo 不复活 project 和 retained persistence boundary 完成 focused pass。
Batch 78 又补齐 Curve Editor、Phone Vcam 和 Timeline scrub 的
pointercancel/blur/visibility/unmount cleanup、pointer capture release、
begin-result ownership 与 stale-pointer prevention，并修复跨 owner/canvas
  teardown 时 R3F Canvas 异步初始化访问 null event source 的问题。Batch 79 又把
  `duplicateCanvas` 接到 graph/Director whole-project two-pass plan：复制
  authored document、project-local identity 和 stable resource descriptor，清空
  target history/session/runtime/clipboard，并对 local/ephemeral resource 和未知
  引用 zero-partial reject。Batch 80 又为不可达 Director owner 增加 strict
  browser-local durable tombstone：旧 save 不得复活，active/inactive cleanup
  只有在 durable 成功后才清理 history、capture sidecar 和不再共享的 local
  descriptor；Batch 81 又增加 strict V1 project JSON import/export：导入前 strict
  decode，成功后只重绑定当前 owner/project，保留内部 entity/reference identity，
  排除 capture/runtime/UI bytes，并进入一条可撤销的 Director history；非法文件
  zero-partial，同文档导入为 no-op。Batch 59、67-81 当前闸门串行回归和全量项目
门禁已通过。普通画布 async/persistence、remote storage、生产级复杂资源
materialization 和 source parity 仍未完成；Batch 82 补了 Director session-local
有限 OBJ/FBX materialization，Batch 83 又补了 clone-owned Director command
feedback projection，Batch 90 又补了 project/session outcome diagnostics 与
scene semantic command，Batch 91 又将对象属性、相机设置和角色组的高频
direct writers 收口到 typed command、persistence、one-entry history 与 name
draft/commit，Batch 92 又补了 local resource strict descriptor/decoded-byte
budget、owner-scoped lease 和 deferred/final release；Batch 93 最终验证了
Director 桌面/移动端 shell、R3F、对象树、Inspector、Timeline、close/reopen、
普通画布跨批 slices 和 Batch 59/67-92 current gates。这些
  focused pass 不能写成完整 backend project authority，也不能写成 LibTV
  source-exact 行为。Batch 94 又补齐 Director workspace 与移动端
  tree/Inspector drawer 的 Tab/Shift+Tab containment、focus return、editable
  boundary 和 inactive drawer `aria-hidden`/`inert`，并以桌面/移动端 fresh
  BrowserContext 记录 `0/0/0` diagnostics。它是 clone-owned focus reliability，
  不改变普通画布的 selection/focus 合同，也不产生 LibTV source-exact focus
  证据。

Batch 95 又完成了普通画布图片节点到 Director 的最小 host handoff：只收集当前
`script-execution` 节点的直接上游、已有 `imageUrl` 的图片，使用 typed
`DirectorCanvasMediaInputV1` 投影到当前 Director session；Inspector 支持默认、
切换和清除，R3F 使用不可交互的环境球预览，source stale 会自动清除，portable
project/history/localStorage 不写入该 session-only 选择。普通 `ImageNode` 与
Director `TextureLoader` 共用明显非法 base64 data URL 预检，故障反馈可见且
desktop/mobile/failure diagnostics 均为 `0/0/0`。这仍不等于普通画布真实上传、
asset registry、panorama 生成或 LibTV 原站的 Three.js/R3F、DOM/CSS 和
panorama 协议证据；相关实现与边界见
[`research/liblib-canvas-batch95-2026-08-29/`](research/liblib-canvas-batch95-2026-08-29/)。

Batch 96 又补齐了 Director 多机位与 Shot 的 clone-owned authoring slice：
camera 继续是 Director object，Shot 作为独立 portable `DirectorShotRecordV1`
记录 camera、时间范围和 capture provenance；旧 V1 文档缺少 `shots` 时派生
默认 Shot，新 camera 以一条 command 同时创建 camera、track 和 Shot。Shot
切换同步 active camera、selection 和 timeline，但不新增 history；名称/时段
编辑支持一条可撤销 history，同值/非法输入分别 no-op/reject。capture gallery
按 Shot 分组，camera 删除会修复 Shot、capture provenance、selection 和最后机位
保护，clipboard/whole-project duplicate 也重写 Shot 引用。该批在
`1440x900`/`390x844` 和 reload/import/export 上通过，且 diagnostics 为
`0/0/0`；它不证明 LibTV 原站存在相同 Shot schema、时段语义、DOM/CSS 或
source parity，详见
[`research/liblib-canvas-batch96-2026-08-29/`](research/liblib-canvas-batch96-2026-08-29/)。

Batch 97 又把 Agent 抽屉对齐 2026-09-05 登录态源站：头部动作集合（含两个
disabled 态）、源站命名 Skill 卡与换一批、composer
添加附件/选择模型/Skill/生成模式/Send 五控件、单列表双分区的选择模型目录
菜单（图片 7 + 视频 8，premium 角标 6 项）与生成模式菜单（默认自动）。
菜单均为本地 state，不接真实 Agent/模型调用；模型行选中语义等服务行为仍是
`SOURCE_UNKNOWN`。证据与合同见
[`research/liblib-live-2026-09-05/`](research/liblib-live-2026-09-05/README.md)
与 [`research/liblib-canvas-batch97-2026-09-05/`](research/liblib-canvas-batch97-2026-09-05/README.md)。

Batch 98 又把添加节点面板对齐同日源站：`视频编辑` 更名 `智能剪辑`，脚本入口
拆成 `脚本 NEW`（本地 status 占位）与 `脚本（旧版） Beta`（既有创建路径）双
flyout，素材库子菜单按早已登记的缺口改为 `风格库/特效库`，并新增
`搜索画布节点` 本地过滤；上传/从生成历史选择仍是本地 status，不构成 media
ingress 运行时授权。证据与合同见
[`research/liblib-canvas-batch98-2026-09-05/`](research/liblib-canvas-batch98-2026-09-05/README.md)。

Batch 99 又把快捷键帮助面板对齐同日快照：创作栏补齐 合并分镜组/连线/生成/
节点复制/创建副本 并全面补上 ⌘ 键帽，删除移到其他栏，其他栏新增
`画布节点搜索 ⌘F` 并移除 Windows 重做行；运行时 handler 一个未动，
帮助文案与运行时的差异由
[`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](research/LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)
按 2026-09-05 复核显式记录。证据见
[`research/liblib-canvas-batch99-2026-09-05/`](research/liblib-canvas-batch99-2026-09-05/README.md)。

Batch 100 又为空画布补上同日源站空态：「双击画布 / 自由生成节点」提示与
故事脚本生成、角色三视图、全能参考生视频、音频生视频四个快捷芯片；clone
经画布下拉切到既有空画布 `canvas-1` 即可到达，芯片点击只给诚实本地
status，不接生成服务。证据见
[`research/liblib-canvas-batch100-2026-09-05/`](research/liblib-canvas-batch100-2026-09-05/README.md)。

### 5.2 状态边界

`canvasStore` 管：

- 项目级名称，以及画布列表和当前画布
- 每个画布的 nodes、edges、viewport
- group hierarchy；当前原站视频组通过 `parentId` 包含相对 `(62,62)` 的失败视频
- 当前选中节点 ID 集合，以及用于兼容单节点浮层的主选中节点 ID
- 增删改节点、边和画布

`uiStore` 管：

- 面板显隐
- grid/minimap/edge/snap 开关
- 工作台/分镜模式、移动/抓手工具
- 分享弹层、Agent 抽屉；Agent 内容包含源站命名 Skill 推荐（含换一批）、通知提示、composer 五控件（添加附件/选择模型/Skill/生成模式/Send）、选择模型目录菜单（图片 7 + 视频 8，premium 角标）、生成模式菜单和本地 composer 状态
- 与 React Flow viewport 同步的 zoom 百分比
- 当前打开的导演台来源节点 ID；导演台内部场景状态不进入 `uiStore`

`directorStore` 管可序列化的场景、对象、选择、活动机位、视角、transform
模式、画幅、九宫格、截图记录、角色 rig，以及 transform/camera/pose typed tracks、
playhead、播放/循环/缩放、关键帧选择、auto-keyframe、运动路径和轨道级
速度曲线，以及机位 look-at/follow 关系和预设运镜的最后应用/错误元数据。时间轴采样会先计算关键帧值，再以 cubic-Bezier 重映射进度并按
弧长采样启用的绑定路径；非相机对象可选用路径切线接管 Y 旋转。pose 轨道
对稀疏控制值执行有限插值，并按 object + kind 与 transform 轨道组合。结果
形成普通 serializable object/camera values 后，才按 sampled stable object ID
解析对象注视和第一/第三人称跟随，同时保留 camera track FOV；再由 R3F 消费。Three.js renderer、
camera、Object3D refs 和 geometry 属于 R3F 组件运行时，不能写入 Zustand。

顶层浮层选择已集中到 `uiStore.activePrimaryPanel`，并由同一组互斥 action 协调添加节点、快捷键、画布下拉、资产抽屉、分享、Agent 和缩放菜单。项目名与画布 CRUD 进入 `canvasStore`；画布下拉只保留编辑草稿和行级更多菜单，资产/历史等面板仍保留筛选/使用态等短生命周期局部状态。因此 LibTV 当前仍是 **画布数据 store + UI store + 局部组件状态** 的组合，但项目/画布导航与页面级 overlay 已有明确边界。

普通 LibTV graph 目前还没有单一 node data schema authority：11 个 renderer、8 个公开创建入口、legacy `src/types/canvas.ts`、default-data switch 和各 node component interface 并不一致；history、selection duplicate 与 canvas duplicate 对 nested `data` 仍主要是浅复制。`sourceNodeId/edgeId`、拉片 `resultNodeIds/sourceBreakdownId`、长视频 `processId`、Director capture/export ID 和 repo/https/data/blob media 具有不同身份与生命周期，不能只按 `*Id` 后缀重写。当前固定事实见 [`LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md)，未来 type/version/operation registry、aggregate 和 portability 设计见 [`LibTVNodeDataIdentity.contract.md`](research/components/LibTVNodeDataIdentity.contract.md)；两者均未授权或实现 runtime codec。

删除也不是单纯过滤 node/edge：当前 runtime 只展开 `parentId` descendants 并删除 incident edges，surviving node data 不修复，因此 shot 双向引用、process cohort、nested `edgeId/sourceNodeId`、node-bound overlay 和 media resource owner 都可能脱节。Open Canvas 固定版本只证明集中删除、conflict no-op、selected node/edge 与 incident edge 一次 mutation 的方法，不能覆盖 LibTV 的领域关系。完整影响、correctness floor、source/product decision queue、`GRAPH-DELETE-01` 和 `LIBTV-VR-013` 见 [`LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md`](research/LIBTV_GRAPH_DELETE_REFERENCE_REPAIR_MATRIX.md)；runtime planner 尚未授权。

Graph authority 也不是一个 `addEdge` 就能覆盖：Batch 57 只关闭 React Flow connection 与 programmatic `addEdge` 的本地结构切片；派生动作、拉片/长视频多节点命令、duplicate、`setNodes/setEdges`、React Flow changes 和 undo/redo 仍通过不同入口直接写 graph。Open Canvas 固定版本采用 store local guard、serialization/full-graph validation、API validation、revision 和 server patch 多层边界，但其 clipboard paste 与 framework delta 也存在旁路，不能照抄。当前入口盘点、T0-T5 信任等级、full-draft command plan、`GRAPH-ENTRYPOINT-01` 和 `LIBTV-VR-014` 见 [`LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`](research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md)；runtime 仍为 partial，未授权集中重构。

React Flow transport 已进一步单独收口：clone 与 Open Canvas 都锁定 `@xyflow/react@12.11.1`，但 union 中的 node/edge `add/remove/replace` 是语义 graph change，不应因为框架 reducer 支持就从 callback 旁路命名 command；edge 在该版本没有非 selection 的 T1 variant。Batch 61 已实现 whole-batch classifier、current active-canvas snapshot routing、node/edge session selection、existing-node finite position/passive measurement allowlist、semantic zero-partial reject 与 history/copy runtime-field sanitation，并通过 `LIBTV-VR-016` focused corpus 及相邻回归。精确 taxonomy、reducer precedence 和剩余 resize/reconnect/portable codec 边界见 [`LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](research/LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md) 与 [`liblib-canvas-batch61-2026-08-27/`](research/liblib-canvas-batch61-2026-08-27/)；runtime 是 focused pass，不代表所有 graph ingress 已统一。

多画布 lifecycle 也不能只看 `canvases[] + activeCanvasId`：当前 graph/viewport/history 已按 canvas 保存，selection 会在切换时清空，Batch 58 的四类 node-bound owner 也会失效；Batch 65 又把 demo responsive preset 限制为首次 bootstrap，并验证 target stored viewport restore、current/old canvas callback guard 和 invalid viewport zero mutation。但 `setActiveCanvas` 仍不拒绝未知 ID，route-local organize/drag/connection transient 没有统一 canvas generation/host epoch，delayed graph writer 和 resource owner 仍可能在执行时 late-read active canvas。Open Canvas 的 URL canvasId、summary/document 分层、hydrate 全量替换和 delete-run cleanup 可借方法；其 old-route in-flight save response 没有 expected current canvas guard，又是不能照抄的反例。完整 owner manifest、CRUD/switch plan、`CANVAS-LIFECYCLE-01` 和 `LIBTV-VR-017` 见 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)；runtime 目前 partial，最终 invalid target、删除/fallback/panel/resource 和 generic late-callback 语义仍待实现或 source/product 决定。

命令反馈也不是“需要时弹一条 toast”：当前 clone 的 graph connection 已有稳定 rejection reason 但 page 静默丢弃，Share/Agent/Add Node/智能剪辑各自保存 string-only local status，VideoNode 用多个 timer chip，Director 则有更完整的 progress/error/retry surface。Open Canvas 可借的是 transient toast、node status/error、save/conflict banner 和 form field error 的分层；其中文 message 字符串匹配 i18n、无 canvas/operation owner 的 async toast 是反例。Outcome disposition、reason/copy 分离、primary surface、owner lifecycle、`COMMAND-FEEDBACK-01` 和 `LIBTV-VR-018` 见 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](research/LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)；精确 LibTV toast/invalid style/timeout 仍需 source evidence，普通 LibTV route 不自动复用 FrameOS toast。

Selection、focus 和 keyboard context 也必须分权：Batch 61 已让 node/edge selection 共用 active-session authority，并以 React Flow change routing 作为唯一 framework selection ingress；Batch 62 又完成 validated command snapshot、editable/IME guard、blocking foreground shortcut suspension、单层 Escape 和 canvas focus fallback 的 clone-owned focused pass。未完成的 primary identity、plain/additive/marquee precedence、mixed node+edge editor gating、modal focus trap、Asset/Agent containment 和 source-exact modal/focus 仍保持边界。Batch 50 已隔离 Director 与普通 page shortcuts。Open Canvas 可借 local editor/clipboard guard，selected flags/conflict coupling、weak Escape 和 framework default destructive key 是反例。统一 selection/focus/context 的长期合同、`SELECTION-FOCUS-CONTEXT-01` 和 `LIBTV-VR-019` 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](research/LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)；Batch 62 的实施和证据入口见 [`research/liblib-canvas-batch62-2026-08-27/`](research/liblib-canvas-batch62-2026-08-27/)；精确 LibTV modal/shortcut/focus visual 仍需 source evidence。

异步结果是这套 authority 的下一层，而不是一个 generic node patch：committed clone 没有普通画布网络任务或 run store，逐帧拉片、音视频分离、深度/抠像/主体编辑和长视频主要在 component timer 后直接创建 graph。Batch 73 已把 Director capture、animation export 和 phone take import 接到 clone-owned operation/attempt/result authority，并验证 stale/duplicate/invalid 零 mutation 与 export resource exactly-once；它没有把普通 timer 升级成 task backend。Open Canvas 的 descriptor/run/poll/server-patch/revision 结构值得借鉴，但固定实现没有比较 expected current run、source media version 或 field owner，terminal run 与 graph projection 也分成独立写入。当前 operation identity、stale/duplicate disposition、selection/history/resource 收敛、`ASYNC-INGRESS-01` 和 `LIBTV-VR-015` 的设计权威是 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)；当前短 timer 只表示 `PROTOTYPE_LATENCY`，不表示真实任务已接通。

这里的“集中”只描述当前有效入口，不代表 `uiStore` 已经没有兼容残留：toolbox/material/character/history/tutorial 仍各保留一组无外部调用者的 boolean/action，Notification/UserMenu 有 state 但没有 mount owner，`toggleGrid` 也没有当前 shell 入口。逐 surface 的 mount owner、outside/backdrop/Escape 差异、storyboard/Director 边界和节点相对锚点策略统一记录在 [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)。

资产管理不是账户资产后端。它读取 active canvas，把 `parentId` 投影为一层节点树，并提供本地排序、类型筛选和 label 搜索；`资产` tab 仍只是当前画布 image/video 节点的派生视图。

整理预览快照也属于页面局部状态。节点位置变化进入 `canvasStore` 的 graph history，viewport 只随预览快照恢复，不进入通用 undo/redo。

### 5.3 节点系统

LibTV 节点各自直接实现卡片、Handle 和专属交互，没有统一 NodeShell：

- `ScriptNode`：剧本文本
- `ImageNode`：按原站尺寸渲染图片和悬浮元数据；clone 顶部工具条使用 React Flow `NodeToolbar` 锚定节点并保持屏幕尺寸，Batch 52 已对齐当前源站内容自适应的 `1092.5x49`、13 动作；顶部 host 继续使用 `10 + 24 * zoom`，底部编辑面板挂在节点内并用 `1 / zoom` 反向缩放。预览动作打开 page-level 只读 overlay，关闭后恢复同一 selection/graph；标注、元素编辑、旋转、图层分离和下载暂以独立 disabled 入口保留。五个初始图片节点保留空白、提示词、带参考图等源站状态；有直接截图证据的“全景”会创建连接到源图片的空 `720°全景图` 节点和专用单参考图 panel；视频帧结果继续复用普通图片 renderer 和上下浮层
- `TextNode`：文本
- `VideoNode`：既保留当前项目中的失败视频，也支持就绪视频、Seedance 2.5 生成面板、处理工具条、片段重拍、智能续写、智能/框选去字幕、音视频分离、首/尾/当前帧截取、智能抠像、主体编辑、深度动作捕捉和长视频过程图提交
- `ScriptExecutionNode`：保留历史 type id 的 `3D导演台` 入口；CTA 进入独立
  R3F authoring surface，不再显示脑补的三步脚本状态
- `StoryboardGroupNode`：图片组/视频组背景容器；当前视频组是真实 parent，失败视频是相对 `(62,62)` 的 child，图片组为空
- `ShotBreakdownNode`：逐帧拉片素材、拆解维度和本地完成命令
- `ShotBreakdownResultNode`：完成后持久存在的三组分镜、动态和音乐结果组；维度决定创建范围，整批节点/边可一次撤销
- `VideoClipNode`：智能剪辑未连接视频空态和四个单列尝试命令；单选时挂载 `660x191` 节点下方 Prompt panel

当前初始画布按原站结构化数据放置 10 个节点和 11 条边。`AddNodePanel`
展示原站的 9 个节点入口；逐帧拉片、视频编辑和音频已有专用 renderer。
导演台入口会打开 lazy-loaded R3F 三栏工作区，支持真实场景、机位、画幅、
helper-free PNG capture、真实浏览器动画录制和图片/视频节点回流；底部时间轴支持 typed track、
关键帧生命周期、scrub/playback/loop/zoom、Inspector/gizmo auto-keyframe
和场景/相机/角色姿势确定性采样。角色 Inspector 提供 source-named
`属性 / 姿势` tabs、20 个姿势预设和六组 SAM 控制；姿势修改在当前
playhead 自动 upsert 独立 `姿态` 关键帧，同一角色的 transform 与 pose
轨道可并行组合。已选 transform/camera 轨道还能创建直线/圆环/矩形路径，在 R3F
世界空间显示轨迹与锚点，驱动对象或机位沿路径播放，并用线性/平滑/缓入/
缓出/缓入缓出或自定义 Bezier 控制速度；helper-free capture 会隐藏这些
编辑辅助。机位 Inspector 还支持 `手动坐标 / 手动旋转 / 对象注视` 与
`不跟随 / 第一人称 / 第三人称`；跟随期间保留既有路径和轨道，但阻止新路径、
预设运镜及手机运镜，关闭后恢复普通采样。动画导出会把完整时间轴映射到所选时长，裁切当前画幅，通过
`captureStream`/`MediaRecorder` 生成当前会话可播放的 WebM blob，再以一个
视频节点和 source edge 原子回流；MP4、远端上传和刷新后持久化不在当前
前端原型范围。长视频提交会额外创建独立的过程节点图。
音频 renderer 可以表达普通本地预览或音轨/人声/背景音 split result，但
waveform 仍是 CSS placeholder，不解析真实音频。

视频组父子关系不是根据画面猜测：原站视频组 DOM 有 `.parent`，当前 xyflow v12 只在 `parentLookup` 有 child 时添加该 class；失败视频与组的绝对坐标差又是 `(62,62)`。clone 因此用真实 `parentId` 表达该关系。group 复制会带 descendants，单独复制 child 会转成顶层副本，删除 group 会级联 child 与相关边。

图片和视频节点浮层不能使用页面固定坐标。原站的上工具条与下编辑器都以选中节点的屏幕中心为锚点；前者由 React Flow 在非缩放层定位，后者位于节点内部并反向缩放。它们允许超出画布边界后被裁切，不会为了保持可见而重新居中到浏览器视口。下方面板与节点外边界的屏幕间距是 `16 * zoom`；clone 因节点壳有 `1px` border，使用 `bottom: -17px` 补偿盒模型，不能把这个实现值误写成原站 CSS。

AutoLink 也不能继续按 clone 当前的固定候选弹窗理解。当前源站把开关放在图片/视频生成面板的高级设置中，并用全局本地偏好共享状态；connected/reference assets 形成候选池，Prompt 内先出现不改写正文的 ghost suggestion，再由点击、`Tab` 或 `Shift+Tab` 接受为结构化 mention badge。正式媒体 badge 保存 stable node ID、media type 和当前 ordinal，“图片 1/2”只是 reference order 的显示投影。当前 clone 的 `陈默/咖啡` 固定数组、一次接受全部和字符串前缀写回均为已知 fidelity gap，详见 [`LIBTV_AUTOLINK_STATE_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)。

双浮层的 zoom 合同也需要拆开理解：当前源站下方 panel gap 在直接测得的 28%/34%/41%/50% 分别是 `16 * zoom`，顶部 toolbar 仍保持 `1092.5x49` 和 node-center；生产 chunk 已确认其 host top 是 `nodeTop - 24 * zoom - 10`，再用 `translateY(-100%)` 抬起自身高度，因此 gap 约为 `16.794/18.152/19.778/22px`。100% 离屏时还会触发可见节点 DOM 卸载。clone 的 `NodeToolbar offset=16` 和单档回归不能代表全部源站行为，详见 [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](research/open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)。

画布空间也不能继续用同一种 `{x,y}` 理解。Open Canvas 的 Quick Add 会把菜单的 container-local 坐标和节点的 flow 坐标分开，pan/zoom 期间使用 live viewport、结束后才更新稳定 viewport；它同时暴露了 permissive viewport normalization、窄容器 clamp、gesture cleanup 和逐文件 drop 非原子等反例。当前 clone 的 V/H/Space blur/visibility cleanup 是可保留的正面 island；Batch 63 已把 Add Node 与 Character Library 从 browser window center 迁移到 actual React Flow host center；Batch 64 让 Asset drawer open/close/X/Canvas-context 保持旧 host-center flow anchor；Batch 65 又把 desktop/compact preset 限制为首次 bootstrap，用户 viewport 在 breakpoint 和 A/B canvas switch 后由 stored viewport 恢复，stale/invalid callback zero mutation。三批都验证 graph/history/selection 边界，窄桌面工具条碰撞只在 screen space clamp，不改 graph anchor。固定事实见 [`LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](research/LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)，focused runtime 见 [`liblib-canvas-batch63-2026-08-27/`](research/liblib-canvas-batch63-2026-08-27/)、[`liblib-canvas-batch64-2026-08-27/`](research/liblib-canvas-batch64-2026-08-27/) 与 [`liblib-canvas-batch65-2026-08-27/`](research/liblib-canvas-batch65-2026-08-27/)；正式权威进一步定义 `CLIENT/HOST_LOCAL/FLOW_WORLD/NODE_LOCAL/SCREEN_OVERLAY/MEDIA_NORMALIZED` 六域、actual host frame、`BOOTSTRAP/LIVE/STABLE/TARGET` viewport phase、gesture owner、entry-specific placement、resize reconciliation、`LIBTV-FIX-LOCAL-VIEWPORT-COORDINATE-01` 和 `LIBTV-VR-020`，见 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](research/LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)。整体 runtime 仍 partial：viewport/organize/drag/connection transient 仍缺统一 canvas generation/host epoch，完整 live/stable endpoint、browser resize anchor、derived/duplicate/organize/selected-overlay composition 与精确 source add/resize/zoom 行为仍待证。

媒体接入同样不是“选择文件后给 node 写一个 URL”。Open Canvas 固定版本提供了 client/server validation、metadata probe、multipart materialization、digest-key reuse 和 normalized descriptor 的可借路径；它也暴露了 accept/probe classifier drift、node-first placeholder、逐文件部分提交、autosaved running、无 freshness/cancel/resource cleanup 等反例。2026-08-27 LibTV source 只读 DOM 又证明 Add Resource upload、Generated History、风格/特效 Material Library、Canvas/Personal/Agent Asset Manager 是不同资源域，Shot Breakdown 另有单 `video/*` source entry。当前 ordinary clone 的 upload/history 仍是 mock，Shot Breakdown 用 component object URL preview 却提前标 ready；Director 已由 Batch 82 增加独立的 typed local-model resource descriptor、lease/status 和有限 OBJ/FBX materialization，但这仍是 session-local island；Batch 83 的 command feedback 只在 Director foreground owner 内提供 clone-owned projection，不等于 ordinary media ingress 已有统一反馈；“我的素材库/预设素材库”不能继续当 current source fact。正式权威将 immutable ingress intent、local bytes/lease、stable asset、node reference、provisional/semantic projection 分权，并定义 ten entry profiles、cohort transaction、last-known-good replace、reachability/release、`LIBTV-FIX-LOCAL-MEDIA-INGRESS-01` 和 `LIBTV-VR-021`，见 [`LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md`](research/LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT.md)。ordinary runtime 仍 missing/partial，真实 provider/storage/upload/persistence 保持边界外，精确 source limits/progress/cancel/placement/register/restore 仍待 disposable fixture；生产级 Director cache/provider/复杂依赖也不在 Batch 82 范围。

前台编辑器也不是“打开 panel 后连续写 `updateNodeData`”。Open Canvas 的 inline/rich/bitmap editor 分开 local draft、bitmap history 和 graph save owner，证明 editor 内部试错应与画布语义提交分层；它的 active-draft resync、40 个 full `ImageData` entry、Restore 折叠、close-first JPEG upload、node-ID-only patch 和 caller 忽略 no-op/conflict result 则是明确反例。当前 clone 的 Text、Prompt/config、Annotate、Element、Picture、Subtitle、Range、Reshoot、Camera 与 VideoToolbar 形成十类成熟度不一的 island：有的具备 gesture coalescing/深拷贝 local history，有的 local-only，有的 enabled-looking command 没有 handler，graph gateway 又没有 semantic equality no-op。正式权威将 session/baseline/draft、native/local/graph undo、sync commit、async/resource handoff、close/cancel/focus 和 honest unavailable 分权，并定义 40 条 invariant、`LIBTV-FIX-LOCAL-EDITOR-SESSION-01` 与 `LIBTV-VR-022`，见 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)。runtime 仍 fragmented，精确 source blur/Enter/Escape/outside/restore/save/close 继续等待 disposable fixture；本文档不授权 runtime 修改。

媒体几何也不能压缩成一组 `width/height` 或一个全局 `object-fit`。Open Canvas 的 selected output、request-aspect card、cover node/candidate、contain detail 和 measured anchor 提供了可借方法，但其 media descriptor 缺 per-output intrinsic dimensions、image/video probe 不对称、edited output ratio drift 和 optional serialized dimensions 又是反例。当前 clone 的 ordinary/derived/Director image、video poster/full media、Preview 与 Annotate/Element/Picture/Subtitle surface 分别持有互相冲突的尺寸和 crop 假设；一个 landscape 节点局部看起来正确，不代表 portrait/square/mixed-output/editor round-trip 正确。正式权威将 intrinsic media、selected output、generation request、semantic frame、passive measurement、surface rendition、editor media space 和 export output 分权，定义 cover/contain transform、frame/rendition profile、measurement epoch、42 条 invariant、`LIBTV-FIX-LOCAL-MEDIA-RENDITION-01` 和 `LIBTV-VR-023`，见 [`LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md`](research/LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT.md)。runtime 仍 fragmented，source portrait/square/video/mixed-output/resize 仍需 `OC-EQ-009` disposable fixture；passive measurement 不进入 semantic history，本文档不授权 runtime 修改。

图片工具条动作不能共享一个凭想象推导的流程。“全景”已经由原站点击态确认：创建空派生节点、source edge、单参考图和 `2:1 · 标准画质 · 2K · 1张` 专用 panel；其 `700x350`、`+120/-110` 和 `660x252` 是截图反推参数。Batch 52 已完成只读 Preview 的 page-level 生命周期；元素编辑空态也已确认会替换标准双浮层并提供 point/box/brush authoring surface；旋转入口在当前共享 fixture 中则实际触发了“旋转与镜像”派生节点并由一次撤销恢复，因此必须按可能发生 graph mutation 的高风险动作处理。多角度、打光、九宫格、高清、宫格切分尚未逐动作采样，当前通用派生行为只是旧 prototype，不得写成原站事实。

Seedance 视频参数不能压缩成普通下拉列表。原站普通和超长参数分别是 `341x445`、`341x397` 的高 dialog；比例使用 5+2 glyph cards，清晰度、音频和数量使用整宽 segmented controls，时长带当前值框。超长模式切换到 `30-300s`、移除数量并保留时长说明；`300s` 对应的 `14700` 只是本地原型中的 source-shaped 积分显示。

Seedance 模型菜单当前只表达截图可见集合，不表达完整模型库。原站证据支持七项顺序、estimate、前五项 premium 和 selected-only description；clone 使用 `380x410` 菜单并复现 2.5/Fast 两个已确认展开态。其他模型说明、真实可用性、计费和原始 SVG logo 都不在证据范围内。

片段重拍不能被实现成一个带自创标题栏的普通表单。文章流程图和当前 bundle 共同支持“独立 4 秒时间带 + 生成器式 Prompt editor”的结构、最多五段、视频/range token，以及未选区间时“留空 = 原样重跑一次”。clone 使用 `660x56` filmstrip 和 `660x252` editor，并继续遵守节点锚定、反缩放与自然裁切合同；缩略帧和提交结果仍是本地 mock。

智能续写不是片段重拍的单选分支。当前线上 bundle 支持“先截取 `4-30s` 前置视频，再创建右侧续写目标”的两阶段模型：第一阶段是节点下方 `660x56` 连续 timeline，使用 `8 * zoom` gap，支持 start/end/region drag；确认后以一次 history transaction 创建 empty video target 和 source edge。目标节点显示来源/range 前缀、专用 Prompt placeholder，并锁定 `Seedance 2.5 / 全能参考`；退出续写只清 metadata 和声明 edge，不删除目标。真实裁剪、上传、合规、模型调用和持久化仍不在原型范围内。

智能去字幕也不是工具条中的临时反馈。当前线上 bundle 支持 `智能去字幕` 和 `框选去字幕` 两种模式：两者都打开节点下方 `48px` 紧凑生成条；region 模式还会把 source 聚焦到至少 `zoom:1`，在视频画面内建立多矩形选择层，并提供 move、corner resize、undo、redo 和 reset。确认后 clone 用一次 history transaction 创建 `视频一键去字幕-{sourceLabel}` pending target 与 source edge，并记录 mode、normalized regions、model 和 request mode。真实字幕检测、像素擦除、积分、上传、任务提交和轮询不在原型范围内。

音视频分离也已经从临时菜单反馈变成画布 graph workflow。2026-08-25 当前 bundle 的可见入口是 `音视频分离 / 人声提取 / 背景音提取`，`音效提取` 受 false feature flag 控制，因此 clone 不再显示该项。提交后 trigger 短暂进入 spinner + `分离中` disabled state，再由一次 history transaction 创建 mode-specific audio result 与 `{source}_无声` pending video；两条 edge 都从 source video 发出，silent video 只是位置上排在 audio 右侧并成为最终 selection。精确的 `120` world-unit gap、`600ms` timer、CSS waveform 和 muted placeholder 属于 clone calibration；真实下载、解码、上传、分离服务、轮询和 partial-output/failure 矩阵不在原型范围内。

视频帧截取也不能只在工具条写一行反馈。当前线上 bundle 同时提供顶部
`截取首帧 / 截取尾帧 / 截取当前帧` 工具组，以及 player camera
“点击截当前帧、hover 显示同组三项”的入口。首帧取 `0s`，尾帧取
`duration - 0.05s`，当前帧取 playhead；结果命名/alt 分别为
`首帧/视频首帧`、`尾帧/视频尾帧`、`截图/视频截图`。clone 用一次
history transaction 创建一个普通 image 和一条 direct source edge，首个
位置严格使用 source right `+100` world units、同 Y，并保留 source
selection 以连续截取。重复结果的 `288 + 48` 纵向 slot、local range
playhead、`1400ms` feedback 和 source poster bitmap 都是 clone
approximation；真实 video seek、canvas PNG、CORS、上传和 resource
replacement 不在原型范围内。

ready-video 工具条原先的 `画面编辑 / 片段截取 / 画面裁切` 没有当前原站
证据，现已按 bundle 纠正为 `主体消除 / 主体修改 / 主体替换 / 智能抠像`。
默认 `30s` fixture 上前三项复刻原站 `>15s` 限制且不修改 graph；智能抠像
打开节点下方 `512x48` 紧凑 panel，并用一次 history transaction 创建
`512x288` pending video 和 direct source edge。source 继续保持 selected，
重复结果纵向避让。provider/model/task/WEBM/source dimensions/duration 等
字段是 request-shaped metadata；`--` power、pending body 和 spinner 明确
表达前端原型边界，不声称真实抠像、透明视频、计费、上传或任务轮询。主体
消除/修改/替换现在共享 `PictureEditPanel`：在 source-compatible duration
下提供 normalized point/box/brush 标记、橡皮、逐标记描述/替换图校验、
本地 undo/redo/reset 和 `分析中` 提交态；提交后创建带 request-shaped
`pictureEdit` metadata 的 pending video 与 direct source edge。候选标签、
替换图入口、标记视觉样式和 pending media 仍是 clone-only prototype，不
声称真实识别、分割、上传或视频处理。

深度动作捕捉来自当前 bundle 中可复核的 `depthMapRef*` 字符串：标题、
节点命名模板、`清晰度`、时长限制占位符、确认文案和用途说明属于 source
fact；入口相邻关系、panel 几何、`720P / 1080P` 枚举和 pending media 属于
clone calibration。默认 30 秒 fixture 只显示独立 guard；开发态
`?duration=10` 可打开节点下方 panel，并以一次 history transaction 创建
source-linked pending reference video。输出不复用 source poster，也不伪造
真实深度媒体、task ID 或未确认的时长限制值。

逐帧拉片结果也不是选中分析节点下方的 tab panel。文章 output screenshot 显示三组 `S01-S08` 分镜、`M01-M03` 动态和 BGM 作为画布内持久结果 surface 纵向展开。clone 用 `shot-breakdown-result` 顶层节点表达这些结果，并把 source 完成状态、结果节点和派生边写成一次 history transaction；尺寸和 edge 数量是截图驱动的实现推断，不冒充原站 DOM fact。

通用“视频编辑 Beta”同样不能把全部交互塞进节点本体。原站 `350x350` `video-clip` 节点只显示未连接视频提示和四个单列尝试命令；选中态的 `+参考`、Prompt、默认模式、输出参数和发送位于节点下方约 `660x191` 的独立 panel。clone 复用既有反缩放锚定合同，并保持 multi-selection hide 和 viewport 自然裁切。

截图识别结果必须及时文本化。先搜索 batch 的 `SCREENSHOT_ANALYSIS.md` 和组件规格，已有记录能回答时不得重复打开整张截图；新识图需记录路径、viewport/state、结构、几何、证据等级和未确认区域。

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
- `docs/research/liblib-seedance-2.5-2026-08-25/LIBTV_FEATURE_GAP_MATRIX.md`：LibTV 主推能力的源站呈现、clone 差距、价值排序和授权闸门
- `docs/research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`：现有回归脚本对当前源站合同的覆盖、历史断言和授权后测试队列
- `docs/research/liblib-seedance-2.5-2026-08-25/NEXT_RESEARCH_PLAN.md`：获批的研究-only 执行顺序、安全边界、产出和授权门槛
- `docs/research/liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`：LibTV UI 状态层级、浮层替换、预览和 graph mutation 转换合同
- `docs/research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`：当前 overlay state、mount owner、关闭路径、键盘边界、Director 例外和节点锚点策略
- `docs/research/LIBTV_UIUX_PARITY_BACKLOG.md`：当前全路由 UI/UX 差距、价值/证据/风险排序、依赖、工作波次和 batch entry template
- `docs/research/liblib-seedance-2.5-2026-08-25/LIBTV_DEPENDENCY_RISK_QUEUE.md`：五项主推能力的共享底座、依赖关系、风险登记和研究优先级队列
- `docs/research/liblib-seedance-2.5-2026-08-25/LIBTV_RESEARCH_GO_NO_GO.md`：编码授权前的继续研究、授权条件、fixture 规格和停止闸门
- `docs/research/liblib-live-2026-08-25/*.json`：10 节点、11 边与首屏 DOM 的结构化抽取
- `docs/research/PAGE_TOPOLOGY.md`：页面区域与层级
- `docs/research/BEHAVIORS.md`：交互目录
- `docs/research/DESIGN_TOKENS.md`：颜色、尺寸、阴影
- `docs/research/components/*.spec.md`：组件级规格
- `docs/research/components/LibTVOverlayPositioning.contract.md`：图片节点双浮层的 screen/flow 定位合同与后续验证断言
- `docs/research/components/LibTVAutoLink.contract.md`：Auto Link 的候选、ghost、structured mention 和 graph 事务合同
- `docs/research/LIBTV_GRAPH_MUTATION_ENTRYPOINT_TRUST_MATRIX.md`：普通 graph 全写入口 T0-T5 authority、full-draft plan 与旁路审计
- `docs/research/LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`：异步 operation/run/result identity、stale/duplicate disposition、field/history/resource 收敛合同

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
| 编辑器命令 | LibTV 的添加、移动模式、缩略图、连线、吸附、缩放、整理、资产、分享、Agent 本地交互、数据驱动分镜模式和一级内容面板已闭环 |
| 数据生命周期 | 绝大多数画布/Director 状态仍是内存 mock；Batch 48 的 `我的模型` descriptor 例外地写入 clone-owned browser `localStorage`，Batch 82 又在 session 内有限 materialize OBJ/FBX，Batch 83 在 Director 内增加 presentation-only command feedback，但这些都不等于项目云端持久化或生产资产；Batch 50 的 workspace collapse 仍是 session-local UI state |
| AI 能力 | 仅 prompt UI 和计时 generation mock |
| 自动化验证 | `npm run check`、文档链接检查和 LibTV Batch 4-33、35-50、52-83 Playwright/pure verifiers 可用；当前 Director reliability manifest 覆盖 Batch 59、67-83；现有 FrameOS E2E 尚未接入默认门禁且选择器已漂移 |
| 部署 | Next standalone build + Dockerfile / compose，可作为纯前端原型部署 |

当前快照中仍存在的主要原型边界：

- 根 `README.md` 和 `package.json` 已对齐当前 LibTV + FrameOS 原型身份，但仓库仍保留历史迁移记录和通用工具命名
- LibTV 内容库已具备原站拓扑和本地真实样例素材，但账户数据、下载和生成调用仍是 mock
- LibTV 分镜模式、Agent 和分享是可验证的前端原型；分镜模式已绑定当前画布节点，Agent/分享已有本地状态，但没有接入真实任务、模型、发布或历史数据
- LibTV 未实现后端生成、上传、分享链接、项目持久化和协作权限
- LibTV 的整理位置针对当前 10 节点项目使用截图反推映射；未知节点只有稳定 fallback，不代表已复刻原站通用布局算法
- FrameOS `duplicateNode` 已构造副本对象但没有把它加入 nodes，复制快捷键当前不会新增节点
- FrameOS Prompt 顶栏的“删除连线”当前调用的是删除节点逻辑
- 旧 E2E 仍查找 `.floating-toolbar`、`.canvas-footer-prompt`、`.debug-toggle` 等历史选择器

这些不是 Big Picture 的目标功能，而是说明仓库仍处于持续研究和原型迭代阶段。

## 10. 修改项目时的推荐路径

### 修改某条路线

1. 先确认目标是 LibTV 还是 FrameOS。
2. 若目标是“下一项复刻什么”，先从 [`LIBTV_UIUX_PARITY_BACKLOG.md`](research/LIBTV_UIUX_PARITY_BACKLOG.md) 选择一个有界 slice，并检查 authorization/fixture/parallel-WIP 状态。
3. 读对应 route page，确认 renderer 和 overlay 的真实挂载关系。
4. 读对应 store；涉及普通 LibTV graph 时同时读 [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](research/LIBTV_GRAPH_TRANSACTION_CATALOG.md)，涉及 page/node overlay 时读 [`LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md`](research/LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md)，确认状态归属、mount owner 和 mutation point。
5. 对照原站证据，而不是只对照旧实施文档。
6. 修改后至少检查两个路由是否仍可渲染。

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
- `python3 scripts/verify-liblib-batch9.py`、`batch15.py`、`batch21.py`、
  `batch26.py` 到 `batch33.py`、`batch35.py` 到 `batch48.py` 串行通过：浮层、Add Node、Seedance 参数、
  续写、去字幕、音视频分离、视频帧截取、智能抠像、主体编辑、深度动作捕捉
  和长视频过程图没有跨批回归；导演台真实入口、R3F 像素、机位/画幅、
  helper-free capture、回流 history、移动抽屉、typed timeline、关键帧、
  scrub/playback/loop/zoom、auto-keyframe、预设运动路径、沿路径朝向、
  速度曲线、铅笔/钢笔路径、锚点/Bezier 控制柄编辑、取消保护和移动端
  Inspector 内部滚动，以及路径整体位置/旋转/缩放、world/local 控制提交、
  `重置偏移`/`重置` 区分、真实 WebM 字节/解码/动态帧差、画幅输出、视频
  回流 selection/history、移动导出面板、手机虚拟机位、关节角色、20 个
  姿势预设、SAM 控制、transform + pose 轨道组合、三类机位注视、目标跟随、
  第一/第三人称、FOV 组合、路径/手机互斥与关闭跟随后恢复通过
- Batch 44：七种 source-named 预设运镜、替换/追加、无空间/follow guards、
  路径保留禁用、真实 R3F 像素变化、desktop/mobile 弹层边界和零浏览器错误
- Batch 45：角色 group/crowd 创建、Shift 多选成组、group transform、typed
  group track、scrub/play 像素变化、ungroup 保留和移动端边界已记录通过
- Batch 46：摄像机截图 tabs、空态/分组图库、active selection、全屏 viewer、
  zoom/Escape、单张/批量回画布、清空确认、已回流节点保留和移动端边界已记录通过
- Batch 47：模型库 trigger、五类 tab、clone-owned proxy cards、可序列化 prop
  插入、tree/Inspector selection、R3F 像素变化、`我的模型` 空态、Escape/outside
  dismissal 和移动端边界已记录通过；真实模型/环境资产加载不在有界合同内
- Batch 48：浏览器本地 FBX/OBJ descriptor、非法扩展名过滤、localStorage
  持久化/刷新恢复、重复加入场景、关联实例清理、桌面/移动端边界和
  zero-browser-error 已形成 recorded pass；该批只覆盖 proxy/catalog，不覆盖
  真实 mesh loading、上传和云端持久化
- Batch 82：在 Batch 48 fixture 域补齐 typed local resource descriptor/provenance、
  attempt freshness、loading/ready/failed/canceled/released、有限 OBJ/FBX
  materialization、parse-failure proxy retention、retry/cancel/release 和 UI
  status feedback；生产级 loader/cache、复杂纹理依赖、远程上传和 source-exact
  资源语义仍未实现
- Batch 83：把 Director typed `DirectorCommandResult` 的 disposition/reason 投影到
  fixed-header primary status surface；rejected/stale/conflict/meaningful no-op 可见，
  committed generic success 隐藏，ARIA status、mobile containment、zero-history feedback
  boundary 和 zero diagnostics 已通过。该 slice 是 clone-owned Director reliability，
  不证明 LibTV source feedback taxonomy，也不关闭 ordinary canvas unified feedback。
- Batch 49：Director viewport native coordinate gizmo 的六方向 snapshot、
  Camera mode recovery、path/phone guard、capture hiding 和 dual WebGL bounds
  已形成 recorded pass；不证明 LibTV source-exact renderer/CSS
- Batch 50：Director workspace 侧栏折叠/恢复、viewport 扩展、mobile drawer
  recovery、focus owner、普通画布快捷键隔离、editable-target guard 和
  Escape layering 已形成 recorded pass；不证明 source exact shell 或完整
  focus trap
- Batch 30：subject menu 四项顺序、`100/120ms` hover 时序、30 秒 guard、
  `512x48` panel、`16px` gap、pending graph、metadata、重复避让、source
  selection、单步 undo/redo 和 `390x844` 裁切均通过；toolbar 当前按
  content width 布局并验证 `49px` 高度和 source-center anchor，不再锁定
  历史 `1009px` 总宽度
- Batch 31：三类主体编辑共享标注器、point/box/brush/eraser、normalized
  mark/frame time、modify/replace 校验、局部 undo/redo/reset、`分析中`、
  pending graph、direct edge、重复槽位、source selection、多选隐藏、
  `390x844` 裁切和零浏览器错误均通过。
- Batch 32：默认 30 秒 guard、10 秒 panel、720P/1080P、busy、effective
  duration metadata、pending graph、direct edge、重复槽位、source selection、
  单步 undo/redo、多选隐藏、`390x844` 裁切和零浏览器错误均通过。
- Batch 29：顶部 frame menu `160px` 且 trigger center delta `0px`；
  player camera `28x28`；首个 output gap `100` world units、同 Y；
  first/last/current metadata、direct edge、重复避让、source selection、
  单步 undo/redo、普通图片浮层和 `390x844` 裁切均通过
- `npm run docs:check`：文档与本地图片链接通过
- Batch 77：普通画布 wheel/middle/Space/H/V/blank no-op/modifier zoom
  与 Director 真实 TransformControls pointer drag 的专项门禁
- Batch 78：Director Curve/Phone Vcam/Timeline pointer cancellation，以及跨
  owner/canvas R3F Canvas teardown 的专项门禁
- Batch 82：Director local resource descriptor/provenance、attempt freshness、
  finite OBJ/FBX materialization、parse-failure proxy retention、retry/cancel/release
  和 zero-diagnostic 的专项门禁
- Batch 83：Director command outcome/reason projection、ARIA feedback surface、
  committed/no-op/rejected behavior、mobile header geometry 和 zero-history boundary
  的专项门禁
- Batch 97：Agent 抽屉 2026-09-05 源站对齐（头部/disabled、源站 Skill 卡、
  composer 控件、模型目录菜单、生成模式菜单、Escape 分层、本地反馈）与
  `0/0/0` diagnostics 的专项门禁；batch14 两处断言已按 replacement 协议更新
- Batch 89-92：Director scene/add-camera、project/session-scene command、
  object/camera/group command 和 local resource owner/lease lifecycle 的专项门禁；
  均以 clone-owned reliability 为边界，不等价于 LibTV source parity
- `python3 scripts/verify-liblib-batch4.py` 到 `verify-liblib-batch9.py`：多选/成组、移动/复制、导航手势、整理预览、视频组 hierarchy 和节点浮层锚定全部通过
- `/` 运行态：10 节点、11 边；边关闭后 DOM 为 0 条，重新开启恢复 11 条
- 桌面 `929x874`：53% 视口，主工具条 `338x49`，画布控制 `273x40`
- 整理预览 `929x874`：28% 视口；关键节点位置在 `3px` 容差内，左下确认卡约 `168x88`
- 整理预览 `1440x900` / `390x844`：约 46% / 10%，无页面横向溢出
- 视频组：原站 `.parent` class 与相对 `(62,62)` 已复刻；parent/child drag、group/child copy、级联删除和 history 通过
- 选中浮层：Batch 52 图片 node/toolbar/panel 中心误差保持 `0px`，当前 toolbar `1092.5x49`、top gap `10 + 24 * zoom`；图片 panel `660px`、bottom gap `16 * zoom`。Batch 10/11 仍保护历史面板和 overlay lifecycle 合同
- 平板 `768x900` 与手机 `390x844`：28% 视口；手机主/次工具条分别位于 `y=743/792`
- minimap：开关后在缩略图按钮上方渲染 `150x110`，资产抽屉打开时与 canvas 同步右移，390px 下避让双工具条；zoom 菜单按原站提供放大/缩小/适合屏幕/50/100/800
- 资产管理：`240px` 左抽屉，桌面画布从 `929px` 收缩为 `689px`；显示项目/当前画布上下文、10 项 source-order 层级树和本地筛选/搜索
- Agent：`340px` 右抽屉；分镜模式自动打开，并将当前画布渲染为关键元素栏与图片/视频故事板列
- 分镜模式：`画布 2` 初始状态为 5 个图片卡、1 个失败视频卡、1 个脚本关键元素；卡片选择、空画布和 `390x844` 内部滚动通过 Batch 13 验证
- Agent/share：Agent source-shaped header/2×2 Skill/通知/composer，分享“发布与分享”两项命令和桌面导航避让通过 Batch 14 验证
- 图片选中态：节点锚定当前 `1092.5x49`、13-action 工具条和 `660px` 编辑面板，包含原站提示词与生成参数；Preview 是独立 page-level overlay
- 六个主入口面板：桌面锚点与原站一致；角色应用可创建可见节点；`390x844` 无检测到的标签溢出
- 添加、分享、整理保留/还原、整理后 undo/redo、工作台/分镜切换均完成浏览器交互验证
- `/frameos/canvas/demo` 运行态：7 节点、5 边
- FrameOS 选中节点后浮动工具条与 PromptEditor 可见
- 浏览器巡检未捕获 page error；开发态仅出现 Next Image LCP 提示，已为首屏画布图设置 eager loading
- `e2e/frameos.spec.ts` 未运行：仓库未安装 `@playwright/test`，且测试选择器与当前实现不一致
