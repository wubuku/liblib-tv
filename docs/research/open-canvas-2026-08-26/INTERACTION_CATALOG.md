# Open Canvas 交互模式目录

> 用途：把 `ZeroLu/open-canvas` 固定版本中的交互机制整理成后续 LibTV UI/UX 复刻可检索、可验证的研究输入。
> 本文不是 Open Canvas 功能清单，也不是 LibTV 的实现规格。LibTV 源站观察决定最终视觉和行为；Open Canvas 只提供结构、状态建模、坐标计算和测试设计方面的启发。

## 1. 研究边界

### 1.1 证据分层

| 标记 | 含义 | 可执行范围 |
|---|---|---|
| `SOURCE_FACT` | 固定 submodule `cf3a906` 中可由源码直接复核的事实 | 可作为 Open Canvas 的实现事实引用 |
| `RUNTIME_FACT` | 官网或公开应用入口本次只读观察到的事实 | 仅说明公开运行态，不覆盖登录后能力 |
| `INSPIRATION` | 对当前 LibTV 有价值的抽象启发 | 需要回到 LibTV 源站重新取证 |
| `INFERENCE` | 由两类证据推导出的工作假设 | 不能直接编码，必须设计验证场景 |
| `CLONE_DECISION` | 当前项目在未改变 LibTV 源站合同前提下的暂定选择 | 等待授权和源站证据后才可实施 |

### 1.2 固定参考

- 上游 submodule：[`research/upstream/open-canvas`](../../../research/upstream/open-canvas)。
- 研究 commit：`cf3a906bb8c35bb940d3267497e7f394b8f42582`。
- 上游主工作区：[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx)。
- 当前 LibTV 入口：[`src/app/page.tsx`](../../../src/app/page.tsx)。
- 本文观察日期：2026-08-26。
- 当前实施边界：只研究和记录；没有获得用户明确授权前，不修改 `src/`，不把 Open Canvas 代码搬入 clone。

## 2. 总体模型：交互是一条状态链

Open Canvas 的可迁移价值不是某个按钮或颜色，而是把一次画布动作拆成可追踪的链：

```text
输入事件
  -> 屏幕坐标 / flow 坐标转换
  -> 当前选择、菜单模式或 pending connection
  -> graph mutation / node data mutation
  -> 校验、状态反馈、保存标记
  -> React Flow 重绘和下游输出选择
```

后续 LibTV 研究也采用这条链，但每一层都要同时标注 LibTV 源站事实。特别是“节点点击后上方工具条、下方参数面板”的问题，不能只看两个元素的 CSS；必须确认它们的 anchor、层级、选择生命周期和 viewport 更新是否属于同一条状态链。

## 3. 模式 A：选中生命周期与双浮层

### 3.1 Open Canvas `SOURCE_FACT`

固定版本在 studio shell 中为选中的可编辑图片单独计算两组 screen anchor：

- editor anchor 从 `selectedNode.measured.width/height` 回退到 node `width/height`，以 live viewport 的 `x/y/zoom` 将 flow position 转成屏幕位置；`left` 是节点中心，`top` 是节点底部再加 18px；编辑器宽度按容器宽度限制在 360-820px。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964)。
- action anchor 使用同一节点中心和 live viewport，`top` 位于节点顶部上方 12px。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6015)。
- 两个浮层都以 React Flow `Panel position="top-left"` 渲染，但 action 使用 `translate(-50%, -100%)`，editor 使用 `translateX(-50%)`；结构相同不等于定位规则相同。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6396)。
- 选中态不是只由 DOM `:focus` 决定，而是从 graph 的 selected node 和节点数据派生；节点内容、动作浮层和编辑浮层分别有自己的显示条件。

这里可复核的关键关系是：**同一 live viewport、同一节点中心、分别计算顶部和底部 anchor**。这比“两个浮层都设 `left: 50%`”更强，但不意味着 LibTV 也应该使用 page-level Panel。

### 3.2 当前 LibTV `SOURCE_FACT`

- [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L42) 使用 `useViewport().zoom`，并以 `selected && selectedNodeCount <= 1` 决定单节点编辑器是否显示。
- 顶部 [`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx#L33) 使用 React Flow `NodeToolbar`，`position=Top`、`align=center`；clone 当前 `offset=16` 只是实现值，源站标准 host 的直接合同是 `nodeTop - 24 * zoom - 10` 加 `translateY(-100%)`，见 [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](LIBTV_OVERLAY_MULTIZOOM_MATRIX.md#35-源站-chunk-对顶部-host-定位的直接证据)。底部 [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L101) 是节点内部绝对定位并做 `scale(1/zoom)`。
- 当前项目已经有明确的 LibTV 合同：顶部工具条和底部编辑器不是可以随意互换的两个通用 Panel。参见 [`ImageNode.spec.md`](../components/ImageNode.spec.md#selected-state) 和 [`ImageEditPanel.spec.md`](../components/ImageEditPanel.spec.md#positioning-contract)。
- 画布空白点击会清空选择，节点点击会选择节点；当前入口行为见 [`page.tsx`](../../../src/app/page.tsx#L388)。

### 3.3 `INSPIRATION` 与 `INFERENCE`

Open Canvas 提醒我们把以下数据作为一个几何合同共同测量：node rect、node measured size、viewport、toolbar rect、editor rect、z-index 和 pointer-events。当前 clone 若仍出现上下浮层错位，优先验证坐标系和更新时序，而不是凭视觉增加 offset。

尚未确认的根因包括：

1. React Flow `NodeToolbar` 使用的 measured rect 与节点子树使用的业务宽高是否不同；
2. `useViewport()`、store viewport 和 React Flow 内部 viewport 是否在拖动/缩放期间有一帧分叉；
3. NodeToolbar 内部 transform 是否和子面板的 inverse scale 发生叠加；
4. 从单选切换多选、拖动选区、点击空白和边缘裁剪时，两个浮层是否拥有同一个卸载时刻。

这些是 `INFERENCE`，不是已经证实的 bug 原因。

### 3.4 `CLONE_DECISION`

- `LIBTV-UIX-01` 继续作为 P0：先重取 LibTV 源站在桌面、缩放、拖动、边缘和移动端的矩形证据。
- 保留 LibTV 当前“顶部 NodeToolbar + 节点内底部编辑器”的架构；只可借鉴 Open Canvas 的统一 anchor 数据和测量方法。
- 在没有新的源站证据前，不加入页面中心对齐、自动避让、边缘 clamp、浮层重排或新的 z-index 层。

### 3.5 Selection 不等于 focus 或 command context

Open Canvas 的 selected flags 同时服务 editor、count、copy 和 delete，clone 则已把 node selection 分离成 session IDs，却仍让 edge selection 留在 stored edge record。两侧都不能仅凭“节点高亮”推出当前键盘 owner：editable target、foreground surface、local capture listener、Director workspace 和 browser/native command 还需要独立 context。

完整 fixed audit 见 [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)。在正式合同前，`LIBTV-UIX-01` 的 selection lifecycle verifier 继续只证明浮层 mount/unmount，不升级为 edge-selection、focus trap 或 shortcut precedence 已完成。

## 4. 模式 B：新增节点、菜单模式与连线入口

### 4.1 Open Canvas `SOURCE_FACT`

`openQuickAddMenu` 不是一个只有布尔值的弹窗。它保存：

- 菜单模式：`quick-add`、`pane`、`connection`、`node`、`edge`；
- 菜单在 canvas viewport 内的 x/y；
- 鼠标释放点经过 `screenToFlowPosition` 转换后的 flow position；
- 可选的 `nodeId`、`edgeId` 和 `pendingConnection`；
- 菜单宽高按模式分支，再以 20px padding 做 viewport 内的 clamp。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4144)。

画布左上角的加号属于画布级 Panel；点击时先读取 trigger rect，再以 trigger 中心打开菜单，同时直接添加 text、note、image、video、audio 的快捷入口。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6259)。

连线入口有两条：

1. 从节点 Handle 点击触发 connection menu，并保存 source node/type/handle；
2. `onConnectEnd` 发现有 source、没有 target、释放点位于 React Flow pane 时，以释放点打开 connection menu，并保存 pending connection。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6046)。

选择菜单中的节点后，Open Canvas 先按 flow position 创建节点，再根据 pending connection 的方向决定 source/target 和 handle，连接失败通过 toast 反馈，最后关闭菜单。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4925)。

### 4.2 Handle 和 Edge 的边界

- Open Canvas 使用真正的 React Flow `Handle` 作为连接入口，节点内还区分普通输出、style reference、omni reference 等语义端点。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3235)。
- 连接模式允许更宽松的方向输入，但 graph 层仍负责合法化、去重和环检测；不能把可拖拽视觉入口等同于“所有连接都合法”。参见 [`validation.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/validation.ts#L418)。
- Framework delta 也不是连接 command：固定 12.11.1 的 edge change 只有 select/add/remove/replace，reconnect 是独立 callback。Open Canvas 用 current store state 是正面模式，但 generic non-select apply 会把 semantic mutation 混进框架 transport；LibTV 精确转译见 [`../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md`](../LIBTV_REACT_FLOW_CHANGE_ROUTING_CONTRACT.md)。
- Edge 有可见 path 和较宽的透明 hit path；hover/selected 状态改变可见线，点击 hit path 删除边。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3515)。

### 4.3 当前 LibTV 映射

当前 LibTV 已有 `LeftSidebar`、`AddNodePanel`、React Flow Handle 和连接 store，但这些组件的视觉和连接方向仍由 LibTV/FrameOS 各自合同决定。Open Canvas 的“菜单保存 pending connection，再一次性创建节点和边”可以作为事务语义的启发；不能直接改变当前 clone 的 Handle 位置，也不能改变既有 edge flow effect。

### 4.4 `LIBTV-UIX-02` 验证合同

在开始编码前，应在 LibTV 源站记录：

| 场景 | 必须确认 |
|---|---|
| 点击节点右侧连接入口 | 菜单锚定 Handle、节点还是鼠标 |
| 从 Handle 悬空拖到画布 | 释放后是否出现菜单，菜单是否带 pending connection |
| 创建新节点 | 新节点的 flow position、自动连边、选择态和浮层 |
| 非法连接 | 禁止连接、视觉反馈、toast、静默失败或回滚 |
| 删除节点/边 | 相关连接菜单、工具条、编辑器是否同步关闭 |
| 移动端 | Handle、菜单和拖拽是否退化为点击流程 |

停止条件：没有源站证据时，只记录 Open Canvas 的模式，不实现新的 LibTV 连接 UX。

## 5. 模式 C：视口、平移、缩放与空间落点

### 5.1 Open Canvas `SOURCE_FACT`

- React Flow 的 `onMove` 持续更新 `liveViewport`，`onMoveEnd` 再写入 store；这样浮层在移动过程可跟随，保存只在动作结束时提交。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6223)。
- 画布允许指定鼠标按键平移、框选和部分选中，关闭滚轮缩放，缩放范围为 0.25-1.8，并提供 MiniMap/zoom Panel。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6244)。
- 创建节点和粘贴节点都把屏幕点用 `screenToFlowPosition` 转换成 flow 坐标；没有把浏览器中心当作永恒画布坐标。创建节点的中心落点见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4887)。
- 加节点菜单的屏幕坐标和节点 flow 坐标是同一动作的两种投影：菜单服务于当前 viewport，节点数据服务于 graph 持久化。

### 5.2 `INSPIRATION`

后续 LibTV 取证需要把“画布空间”和“屏幕浮层空间”分开记录：

```text
flow position + node measured size + viewport
  -> node screen rect
  -> node-level toolbar/editor anchor

pointer clientX/clientY + viewport
  -> flow position
  -> new node / pending connection
```

两条转换链共享 viewport，但不共享同一个 CSS containing block。这个区分是诊断双浮层错位和新增节点落点偏差的最小模型。

### 5.3 当前 LibTV `CLONE_DECISION`

当前 LibTV 的 `BottomToolbar`、缩放菜单、MiniMap 和入口面板已有独立研究合同，见 [`BottomToolbar.spec.md`](../components/BottomToolbar.spec.md) 和 [`MainEntryPanels.spec.md`](../components/MainEntryPanels.spec.md)。后续不能因为 Open Canvas 把控件放在 React Flow `Panel`，就把 LibTV 的节点级浮层也提升到同一层。

`LIBTV-UIX-07` 的验收重点是：画布级控件、节点级浮层、modal/drawer 的事件边界互不串层；缩放改变时，所有依赖 viewport 的元素连续跟随；节点创建位置在源站允许的裁剪策略内保持一致。

2026-08-27 fixed audit 已将本模式从一般启发细化为 6 个 coordinate domains、`OC-053..060` 和 `LIBTV-VGP-001..016`：当前 clone default add 使用 window center 而非 actual host center；V/H/Space blur/visibility cleanup 是应保留的正面 island；viewport/organize/drag/connection transients 仍缺 canvas generation。完整事实与 formal-contract queue 见 [`../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md)。

## 6. 模式 D：复制、粘贴、重复与派生

### 6.1 Open Canvas `SOURCE_FACT`

Open Canvas 的 clipboard payload 是可版本化的 graph 子集：

- payload 带 `version: 1`，节点只保留 id、type、position 和规范化 data；
- 边只保留两端都在选区内的内部边，不把外部依赖隐式复制；
- paste 时创建 id map，重写内部边两端 id，并以视口中心为基准叠加偏移；
- 连续粘贴使用递增偏移，避免新旧节点完全重叠；
- copy/paste 在可编辑输入框或图片预览打开时跳过，避免抢夺文本输入的系统快捷键。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3896) 和 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4402)。

当前固定版本的 store 还会检查最大节点数，并把粘贴作为一次 graph mutation；因此“复制”不是只复制 DOM，也不是只复制当前选中图片。见 [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L339)。

### 6.2 当前 LibTV 映射

当前 LibTV 已有更丰富的 clone-only graph 语义：

- [`canvasStore.ts`](../../../src/store/canvasStore.ts#L492) 会建立新 id、复制内部边，并处理父子/分组关系；
- `duplicateSelectedNodes` 会更新选中状态并记录历史；
- 删除选择会同步处理后代节点和相关边；
- 业务节点可能包含派生图片、视频、导演捕获等领域字段。

因此 Open Canvas 只提供“子图快照、ID 重写、内部边闭包、视口中心偏移、输入事件隔离”的启发，不能替换当前 store 的领域逻辑。

### 6.3 `LIBTV-UIX-12` 验证合同

源站取证应覆盖：单节点复制、多节点复制、带边复制、含派生节点复制、连续粘贴、粘贴后选择态、撤销/重做、输入框内快捷键和移动端降级。重点不是复制按钮长什么样，而是复制后节点、边、媒体引用和浮层状态之间的关系。

停止条件：没有确认 LibTV 的跨画布/跨项目剪贴板边界前，不把 Open Canvas 的 JSON payload 直接引入 clone。

## 7. 模式 E：媒体输出历史与当前候选

### 7.1 Open Canvas `SOURCE_FACT`

Open Canvas 将媒体结果放在节点 data 中，而不是只保留最后一张图：

- image 节点有 `imageOutputs` 和 `selectedImageIndex`；
- video 节点有 `videoHistory` 和 `selectedVideoIndex`；
- 选择候选会更新选中 index、当前媒体和下游可引用的结果；
- 上传/生成结果会合并进历史数组，并保持选中结果可回显。类型合同见 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L84)，交互读取见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L3991)。

### 7.2 当前 LibTV 映射与风险

当前 LibTV 的生成后动作大量采用“派生新节点”的产品语义，同时已有图片/视频节点数据和历史字段的研究。两种语义不能仅凭字段名判定等价：

| 问题 | 需要回到 LibTV 源站确认 |
|---|---|
| 多个候选 | 同一节点轮播、节点内网格还是新建节点 |
| 当前候选 | 下游边引用当前 index，还是引用不可变输出 |
| 重试 | 覆盖当前输出、追加历史还是生成派生节点 |
| 删除 | 删除当前候选是否影响整个节点和下游引用 |
| 复用参数 | 回选候选后，顶部工具条和底部编辑面板是否保持状态 |

这形成 `LIBTV-UIX-13`；在源站未证明前，只将 Open Canvas 作为数据建模启发，不把候选历史做成可见 clone 功能。

## 8. 模式 F：运行状态、保存状态与反馈

### 8.1 Open Canvas `SOURCE_FACT`

Open Canvas 把节点/任务运行状态与画布保存状态拆开：

- 节点状态包括 `idle`、`queued`、`running`、`success`、`error`；run 状态包括 `pending`、`running`、`success`、`failed`、`canceled`；
- store 的保存状态包括 `idle`、`saving`、`saved`、`error`、`conflict`，并另存 `isDirty`、revision、saveError 和 lastSavedAt；
- 编辑节点时可以使 graph dirty，而不会把任务状态误写成 saving；保存冲突会阻止继续写入并要求加载最新版本。见 [`types.ts`](../../../research/upstream/open-canvas/shared/lib/canvas/types.ts#L11) 和 [`canvas-store.ts`](../../../research/upstream/open-canvas/shared/stores/canvas-store.ts#L38)。
- studio shell 使用 debounce 保存，源码中当前观察到的延迟为 1200ms。见 [`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L4868)。
- execute 前会保存 graph 并提交 revision，非 terminal run 以 run ID 轮询，server patch 推进 revision 与 saved baseline；但 fixed patch 不比较 expected current run/source version/field owner，不能把这条路径直接当 stale-safe 模板。见 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)。

### 8.2 `INSPIRATION`

这套拆分适合用来检查 LibTV 原型中的反馈是否含义混杂：生成中、节点参数已改、画布正在保存、保存失败、网络失败和 provider 未配置不应该共用一个 loading 图标。对于纯前端 prototype，可以模拟可见状态，但不应借 Open Canvas 的状态名暗示真实后端已接通。

### 8.3 `LIBTV-UIX-14`

后续验证要记录状态转移和 UI 可操作性：

```text
参数编辑 -> 节点 dirty -> 运行 queued/running -> 结果 success/error
                 \-> 画布 saving -> saved/error/conflict
```

每条转移都要确认节点是否仍可拖拽、工具条/编辑面板是否仍可定位、异步结果回来时是否覆盖用户的新输入。没有真实服务端时，测试必须明确标为 mock/local 行为。

状态转移记录还不够。Graph-producing completion 必须另记 operation/run/result/source-version identity、current/stale/duplicate/invalid disposition、field owner、selection/history delta 和 resource owner；对应 `LIBTV-UIX-14` 的机械 verifier 是 `LIBTV-VR-015`，状态语义 verifier 仍是 `LIBTV-VR-007`。

## 9. 模式 G：画布级控件与节点级控件的层级

### 9.1 Open Canvas `SOURCE_FACT`

Open Canvas 将左上角新增节点、左下角 MiniMap/zoom、选中节点 action/editor、modal 和 preview 分到不同的 React Flow/DOM 层。其 studio shell 同时处理这些层，意味着层级合同必须由数据和事件边界维持，而不能靠组件出现顺序猜测。

### 9.2 当前 LibTV `CLONE_DECISION`

当前项目已有以下边界：

```text
应用导航 / 左侧入口 / 底部工具
  -> React Flow 节点和边
    -> ImageNode 顶部 NodeToolbar
    -> ImageNode 内部底部 ImageEditPanel
  -> modal / drawer / preview
```

Open Canvas 的 Panel 结构只能启发“画布级控件不应侵入节点内容”，不能改变 LibTV 原站已取证的 dual overlay 层级。后续所有视觉回归都要同时测 pointer-events、z-index、拖拽命中和滚轮事件。

## 10. 模式 H：空状态、配置与 onboarding

### 10.1 Open Canvas `RUNTIME_FACT` / `SOURCE_FACT`

此前官网只读审计观察到，公开入口把落地页、画布列表、空画布和 provider key 设置分成不同步骤；未登录或未配置 key 时可以看到产品骨架，但不能将其当作已具备真实生成通道。路由和 runner 的静态边界见 [`RUNTIME_AUDIT.md`](RUNTIME_AUDIT.md) 与 [`REPORT.md`](REPORT.md)。

### 10.2 对 LibTV 的研究价值

Open Canvas 提供了一个信息架构问题：空状态、导入、新建、设置、帮助、生成前配置和节点编辑器应不应该共享同一层。LibTV 是否有等价 onboarding 仍需源站取证，暂定形成 `LIBTV-UIX-16`，不因上游存在而新增 LibTV 首屏流程。

### 10.3 多画布 lifecycle 与 owner 切换

固定版本还把画布列表摘要、URL `canvasId`、完整 graph/viewport hydrate、删除后的 registry fallback 和保存 revision 分开。正面启发是 identity first、整份 document hydrate 和 per-canvas viewport；反面启发是异步 save response 即使请求 URL 绑定旧 ID，本地 `finishSave/failSave/enterConflict` 仍需再次核对当前 in-memory owner。该结论形成 `LIBTV-UIX-17`，不能被简化成 dropdown row 是否高亮。

当前 clone 已有 per-canvas graph/viewport/history、切换清 selection 和 Batch 58 node-bound owner cleanup；Batch 65 已关闭 demo responsive preset 覆盖 stable viewport，并验证 target stored viewport restore、current/old canvas callback guard 和 invalid viewport zero mutation。仍需处理 invalid active target、organize/drag/connection transient 的统一 generation/host epoch、delayed graph writer 与 resource owner。完整静态审计和 switch manifest 见 [`../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](../LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。

### 10.4 Command outcome 与 feedback surface

固定版本的 root toast、node status/error、save/conflict banner、field error/pending control 是不同 owner。List CRUD 还区分 navigation-visible success、same-value/cancel silent、pending、confirm 和 terminal toast。值得借的是 outcome-sensitive projection；localized message lookup、owner-less async toast 和多文件逐项 toast 是反例。

当前 clone 的 connection reason、local status、VideoNode timer 和 Director persistent surface 不能继续只按组件各自定义。该结论形成 `LIBTV-UIX-18`：先记录 disposition/reason/owner/primary surface，再验证 clear/retry/switch/delete/dedupe/accessibility；不因 Open Canvas 使用 Sonner 就新增 LibTV global toast。完整合同见 [`../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](../LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md)。

### 10.5 Selection、focus 与 command context

固定版本的 selected flags、editable guard、local editor state 和 Radix focus delegation 说明 selection、keyboard 与 focus 有可分离 owner；同时，conflict gate、弱 Escape/default propagation 和组件库边界说明这些局部机制不能代替统一优先级。

当前 clone 的 node projection、edge selected field、page bubble shortcut、modal capture guard 和 Director foreground isolation 已形成多个 island。固定静态审计已记录 Batch 50 后 Director 会隔离全部普通 page shortcut，而不是旧文档描述的仅 Escape。该结论形成 `LIBTV-UIX-19`：先归一化 active node/edge/primary selection，再按 editable/surface/modal/Director/route 解析 top context；一次 Escape 只退一层，close 后焦点只返回仍有效 owner。正式合同见 [`../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](../LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。

### 10.6 Viewport、coordinate、gesture 与 placement authority

固定 Open Canvas 把 Quick Add 的 screen surface position 与 flow placement point 分开；普通 Add Node 读取 actual container center；`onMove` 提供 live viewport，`onMoveEnd` 更新 stable viewport；add/drop/paste/duplicate/pending connection 使用 entry-specific placement。它也暴露 permissive normalize、窄 host clamp、gesture cancel 和逐文件 drop 非原子反例。

当前 clone 有 per-canvas viewport、V/H/Space cleanup、drag one-history、derived/duplicate/organize placement 和 source-shaped overlay formulas，但 default add 使用 browser window center，live/stable/bootstrap 未显式分权，viewport/organize/drag/connection transient 缺 canvas generation。该结论形成 `LIBTV-UIX-20`：actual host + typed domain + current viewport phase + named gesture/placement owner 共同决定空间结果；不增加 Quick Add/drop/pending connection。正式合同见 [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)。

## 11. 对比矩阵：什么可以借鉴，什么不能搬

| 主题 | Open Canvas 固定版本事实 | 当前 LibTV 已知合同 | 后续动作 | 状态 |
|---|---|---|---|---|
| 选中双浮层 | measured node + live viewport + 两个 screen anchor | 顶部 NodeToolbar、底部节点内 panel、允许源站裁剪 | 重取源站 rect 并定位坐标系 | P0 `UIX-01` |
| Handle 连线 | 真实 Handle、pending connection、菜单可创建并连边 | 现有 Handle/edge effect 不能擅改 | 取证源站连接入口和失败反馈 | `UIX-02` |
| 节点/控制分层 | 节点内容、Handle、Panel、modal 分层 | LibTV 节点内 toolbar/editor 已有边界 | 测事件命中和 z-index | `UIX-03` |
| 视口变换 | live viewport 跟随，screen/flow 双坐标 | LibTV 有独立 viewport/底部工具合同 | 建立场景矩阵 | `UIX-07` |
| 复制粘贴 | versioned subgraph、内部边、ID map、中心偏移 | LibTV 有父子/派生/历史领域逻辑 | 比对源站复制行为 | `UIX-12` |
| 媒体历史 | image/video history + selected index | LibTV 需确认候选与派生节点语义 | 源站生成后取证 | `UIX-13` |
| 运行/保存 | 两套状态枚举、dirty/conflict、debounced save | 当前主要是 prototype/mock | 只复刻可见反馈 | `UIX-14` |
| 响应式 | landing mobile 已观察，studio 完整行为未证实 | 当前项目有 desktop/mobile 研究记录 | 对照 390px/929px | `UIX-15` |
| onboarding | key、空状态、导入、新建有入口分层 | LibTV 是否存在等价流程未证实 | 只做源站观察 | `UIX-16` |
| 多画布 lifecycle | summary/full record、URL/not-found、hydrate、per-canvas viewport、delete/run cleanup | clone 有 dropdown 与局部 owner cleanup，源站产品语义未证 | 建 switch manifest 并验证 old-owner callback | `UIX-17` |
| command feedback | toast、node error、save banner、field/pending 分层；cancel/noop 非必 toast | clone reason/string/timer/Director islands，exact source visual 未证 | 建 disposition/reason/primary-surface matrix | `UIX-18` |
| selection/focus/context | selected flags、editable guard、local editor、Radix delegation；弱 Escape/conflict gate 反例 | clone node/edge/listener/modal/Director islands，exact source multi-select/focus 未完整 | 建 validated selection + context precedence + focus-return matrix | `UIX-19` |
| spatial authority | screen/flow 双锚点、actual host、live/stable viewport、entry placement；normalize/clamp/drop 反例 | clone viewport/navigation/placement/overlay islands，default add/phase/generation 仍 partial | 建 actual-host + six-domain + gesture/placement owner matrix | `UIX-20` |

## 12. 后续 batch 合同

### `LIBTV-UIX-09`：选中生命周期状态机

把单选、多选、拖动、平移、缩放、空白点击、边缘裁剪和移动端作为一个状态机取证；交付 DOM rect 表、截图、节点 measured 尺寸、viewport 和浮层卸载时序。

### `LIBTV-UIX-10`：连接入口与 Quick Add

记录 Handle、悬空连线、连接菜单、节点创建、自动连边、失败反馈和菜单关闭；交付事件序列和 source/target/handle 语义表。

### `LIBTV-UIX-11`：视口坐标合同

记录所有新增节点、菜单、浮层和预览的 screen/flow 坐标来源；交付 zoom/pan 场景矩阵，明确哪些元素反向缩放、哪些元素保持屏幕尺寸。

### `LIBTV-UIX-12`：复制、粘贴与重复

验证子图闭包、边、父子关系、媒体引用、选择态、历史和快捷键隔离；交付可复现的图前后快照。

### `LIBTV-UIX-13`：输出候选和媒体历史

验证同节点候选、派生节点、重试、回选和下游引用关系；没有源站证据时只保持研究状态。

### `LIBTV-UIX-14`：运行与保存反馈

区分参数错误、运行失败、保存失败、冲突、provider 未配置和本地 mock；验证状态变化不破坏双浮层和拖拽。

### `LIBTV-UIX-15`：响应式退化

至少覆盖 390px、768px、929px、1440px；不以 Open Canvas landing page 的 mobile 结果推断 studio 行为。

### `LIBTV-UIX-16`：空状态与 onboarding

只在 LibTV 源站确认存在对应入口后，记录空画布、导入、配置、帮助和首次生成前流程。

### `LIBTV-UIX-17`：多画布 owner reconciliation

验证 A/B 独立 graph/viewport/history、selection 和 node-bound surface 清理、project preference 保留、page transient generation、无效 target、active/inactive/final delete，以及旧 viewport/async callback 不写入 B。源站未证的 URL、save/conflict 和最后删除 fallback 只保留为 Open Canvas 启发。

### `LIBTV-UIX-18`：命令 outcome 与 feedback owner

验证 reject/noop/start/complete/fail/stale/duplicate 的 stable reason、zero-history feedback、field/node/surface/canvas primary owner、timer/retry/dedupe、switch/delete/unmount、desktop/mobile geometry、accessibility 和 LibTV/FrameOS route isolation。Exact toast/invalid style/timeout 未有源站证据时保持 research gate。

### `LIBTV-UIX-19`：选择、焦点与前台命令上下文

验证 node/edge/primary selection 对 active graph 的归一化、editable/canvas/node-control/modal/Director/route 优先级、明确 dispatch result、一次 Escape 只退一层、focus acquire/contain/return/fallback、switch/delete/undo/unmount stale-owner cleanup，以及 selection/focus zero semantic history。Exact multi-select、edge action、Escape 和 focus visual 未有源站证据时保持 research gate。

### `LIBTV-UIX-20`：actual-host 空间权威与 entry placement

验证 client/host/flow/node/media domain、actual React Flow host、live/stable/bootstrap/target viewport、pan/zoom/drag/connection/organize session owner、host resize、default/derived/duplicate placement、selected overlay same-frame composition、viewport zero semantic history 和 graph command exact one-step history。Exact source add/fit/zoom/resize/drop 未有证据时保持 research gate；Open Canvas Quick Add/drop/pending connection 保持 absent。

## 13. 验证矩阵

| 维度 | 最小证据 | 失败时先查什么 |
|---|---|---|
| 选中浮层 | 选中前后截图 + 三个 DOM rect + viewport | 选择生命周期、containing block、transform |
| 拖动/平移 | pointer 序列 + 中间帧截图 | live viewport 是否持续更新 |
| 缩放 | 28%/53%/100%/180% rect 表 | 哪一层应 inverse-scale，哪一层由 React Flow 管理 |
| 菜单落点 | 触发点、菜单 rect、创建节点 flow position | screen/flow 转换和 clamp 是否混用 |
| 连线 | source/target/handle/边结果 | Handle 事件是否被装饰层拦截、方向是否归一化 |
| 复制粘贴 | graph 前后 JSON、选择态和位置 | ID map、内部边、父子关系、历史事务 |
| 媒体结果 | 输出数组、selected index、下游引用 | 当前候选和派生节点是否被混为一谈 |
| 状态反馈 | 状态转移日志 + operation/result envelope + 可操作性 | run/save 是否混淆；stale/duplicate completion 是否覆盖 draft、selection、history/resource |
| 焦点/命令上下文 | activeElement + context stack + dispatch/Escape trace | editable guard、listener phase、foreground owner 或 return target 是否分叉 |
| 移动端 | 390px screenshot + hit target | 不要从桌面 clamp 推导移动端布局 |

## 14. 明确禁止事项

1. 不把 Open Canvas 的视觉样式、provider 名称或菜单文案当作 LibTV 规格。
2. 不因为上游使用 page-level `Panel`，就替换 LibTV 的节点内 `ImageEditPanel`。
3. 不改变当前项目已取证的 LibTV edge flow effect、Handle 位置和边缘裁剪策略。
4. 不为完成研究而输入 provider key、上传真实媒体、执行付费生成或修改官网画布。
5. 不在未获授权前修改 `src/`；本轮只产生研究文档和索引更新。

## 15. 结论

对后续 LibTV 复刻最有价值的 Open Canvas 启发可以浓缩为三条：

1. 把交互动作建模为“事件 → 坐标 → 状态 → graph/data mutation → 反馈”的可追踪链；
2. 把节点尺寸、viewport、screen anchor、层级和事件命中作为同一份几何/交互合同；
3. 把运行状态、保存状态、媒体候选和复制子图作为显式数据，而不是依赖临时 DOM 或单一 loading 状态。

最终复刻仍由 LibTV 原站证据裁决。当前最高价值顺序是先解决双浮层几何，再验证连接/视口，再研究媒体历史与状态反馈；所有批次都必须留下 `SOURCE_FACT`、`OPEN_CANVAS_INSPIRATION`、`INFERENCE`、`CLONE_DECISION` 和验证记录。
