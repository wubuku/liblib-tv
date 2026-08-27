# LibTV UI Overlay Runtime Catalog

> 审计基线：clone commit `6b3ebfe`，静态审计日期 2026-08-27。
> 范围：当前 `/` 路由、`uiStore`、page shell、top-level overlays 和节点相对浮层。
> 本文记录当前 clone 的实际运行语义，不授权修改 `src/`，也不把 clone 行为自动提升为 LibTV 源站事实。

## 1. 目的与证据边界

现有文档已经分别回答：

- Batch 11 当时设计了哪些 top-level overlay 互斥规则；
- 当前 LibTV 源站的图片节点上下浮层采用什么几何合同；
- UI 层级如何区分 page shell、selected-node controls、active tool 和 graph result；
- graph action 如何进入 history。

仍缺少的是一张从“当前用户命令”反查“实际 state、挂载 owner、关闭路径和副作用”的运行时目录。本文填补这一层，避免后续 agent：

1. 把历史设计合同误读成当前代码事实；
2. 把 `uiStore` 中未挂载的兼容字段误读成现有产品入口；
3. 用同一种 outside-click、Escape 或定位机制处理全部浮层；
4. 把 page-level overlay 和节点相对 toolbar/panel 混为一类；
5. 在 Director、storyboard 或 modal 打开时忽略潜在的后台快捷键和隐形状态。

本文使用以下证据标签：

| 标签 | 含义 |
|---|---|
| `CLONE_RUNTIME` | 由基线 commit 的 route/store/component 静态代码直接支持。 |
| `SOURCE_FACT` | 由当前专项源站合同及其 DOM/bundle/截图证据支持。 |
| `HISTORICAL_CONTRACT` | 某个 Batch 的设计或 recorded-pass 快照，只对其切片负责。 |
| `INFERENCE` | 从多个运行时事实推导的工程风险或后续验证假设。 |
| `CLONE_DECISION` | prototype 当前局部选择，不代表源站必须如此。 |

本轮没有重新操作 LibTV 源站，也没有运行会写截图的浏览器脚本。审计从 `6b3ebfe` 开始；随后稳定提交的 Batch 47 和新建的 Batch 48 Director model-library slice 不在本目录的代码审计范围内。

## 2. Big Picture

当前 clone 至少有五类视觉 surface，不能用一个 `isOpen` 模型理解：

```text
S0 top-level page surfaces
  -> uiStore 互斥 overlays、drawers、menus、dialogs

S1 independent route-local feedback
  -> organize keep/restore confirmation

S2 selected-node surfaces
  -> selected image/video toolbar above node
  -> generation/edit panel below node

S3 active authoring surfaces
  -> subtitle, matting, picture edit, continuation, depth motion...

S4 full-screen workspace
  -> DirectorDesk and its own nested panels/viewers
```

关键区别：

- S0 的 transient 互斥由 `uiStore` action 在写入时实现；Batch 63 起 Asset drawer
  对 Add Node / primary panel 作为可并存 layout surface 保留；
- S1 不进入 `closedOverlayState`，可以和 S0 并存；
- S2/S3 由节点 selection 和组件 local state 驱动，不进入 top-level overlay store；
- S4 有独立 Escape 优先级，但并未完全隔离 page global shortcuts；
- 节点上下浮层同时使用 React Flow `NodeToolbar` 和节点内 inverse-scale 两种锚点体系。

## 3. `uiStore` 的实际权威状态

### 3.1 Top-level overlay state

`closedOverlayState` 重置以下状态：

```text
isAddNodePanelOpen
isCanvasDropdownOpen
isAssetPanelOpen
isToolboxPanelOpen
isMaterialPanelOpen
isCharacterPanelOpen
isHistoryPanelOpen
isShortcutsPanelOpen
isTutorialPanelOpen
isNotificationOpen
isUserMenuOpen
isSharePanelOpen
isAgentOpen
isZoomMenuOpen
activePrimaryPanel
```

多数 `toggle*` action 先展开这份关闭态，再设置自己的目标状态。Batch 63 的
`toggleAddNodePanel`、`togglePrimaryPanel` 和 `setPrimaryPanel` 使用
`closeTransientOverlays(state)`，保留当前 `isAssetPanelOpen`；因此“打开一个
top-level surface 会关闭其他 surface”仍是 **write-side convention**，而不是
discriminated union 或 selector 强制得到的不可破坏状态。

### 3.2 当前实际挂载权威

| 状态 | 当前运行时角色 | 结论 |
|---|---|---|
| `activePrimaryPanel` | `LeftSidebar` 挂载 move/toolbox/material/character/history/tutorial | 六个主入口的唯一渲染权威。 |
| `isAddNodePanelOpen` | `LeftSidebar` -> `AddNodePanel` | 当前有效。 |
| `isCanvasDropdownOpen` | `CanvasTabDropdown` 自挂载 | 当前有效。 |
| `isAssetPanelOpen` | `page.tsx` -> `AssetManagerPanel` | 当前有效。 |
| `isShortcutsPanelOpen` | `page.tsx` -> `KeyboardShortcutsDialog` | 当前有效。 |
| `isSharePanelOpen` | `TopNavBar` -> local `SharePanel` | 当前有效。 |
| `isAgentOpen` | `page.tsx` -> `AgentDrawer` | 当前有效。 |
| `isZoomMenuOpen` | `BottomToolbar` 自挂载 | 当前有效。 |
| `activeDirectorNodeId` + `activeDirectorCanvasId` | `page.tsx` -> `DirectorDesk` | 当前有效，但不属于 `closedOverlayState`；Batch 58 已补 canvas-bound owner cleanup。 |

### 3.3 未挂载或冗余兼容状态

| 字段/action | 调用者审计 | 风险 |
|---|---|---|
| `isToolboxPanelOpen` / `toggleToolboxPanel` | `uiStore` 外无调用者；renderer 只读 `activePrimaryPanel` | 与实际权威重复，未来可能产生状态漂移。 |
| `isMaterialPanelOpen` / `toggleMaterialPanel` | 同上 | 同上。 |
| `isCharacterPanelOpen` / `toggleCharacterPanel` | 同上 | 同上。 |
| `isHistoryPanelOpen` / `toggleHistoryPanel` | 同上 | 同上。 |
| `isTutorialPanelOpen` / `toggleTutorialPanel` | 同上 | 同上。 |
| `isNotificationOpen` / `toggleNotification` | `uiStore` 外无调用者或 mount owner | 不应写入当前产品 surface 清单。 |
| `isUserMenuOpen` / `toggleUserMenu` | `uiStore` 外无调用者或 mount owner | 不应写入当前产品 surface 清单。 |
| `showGrid` / `toggleGrid` | route 读取 `showGrid`，但 `toggleGrid` 无当前 UI caller | 网格默认显示，但用户当前无法通过 shell 关闭。 |

这些字段是 `CLONE_RUNTIME` 的兼容残留，不是 `SOURCE_FACT`。获得编码授权前，只记录，不删除。

## 4. Top-level Surface Directory

### 4.1 Primary entry surfaces

| Surface | 命令与 owner | 状态/挂载 owner | 关闭路径 | 运行副作用 |
|---|---|---|---|---|
| Move | centered toolbar；`LeftSidebar` | `activePrimaryPanel="move"`；`LeftSidebar` | 重复 trigger；选择 V/H；另一个 top-level action；page Escape | V/H 更新 `canvasTool`；无 graph history。 |
| Toolbox | centered toolbar；`LeftSidebar` | `activePrimaryPanel="toolbox"`；`LeftSidebar` | X；重复 trigger；另一个 top-level action；page Escape | “使用”只更新组件 local `usedPresetId`。 |
| Material | centered toolbar 或 AddNode 素材 submenu | `activePrimaryPanel="material"`；`LeftSidebar` | 选择任一 entry；重复 trigger；另一个 top-level action；page Escape | 当前 entry 只关闭面板，不创建节点。 |
| Character | centered toolbar；`LeftSidebar` | `activePrimaryPanel="character"`；`LeftSidebar` | X；backdrop `mousedown`；另一个 top-level action；page Escape | “应用至画布”调用 `addNode("image")` 后关闭，是 graph transaction。 |
| History | centered toolbar；`LeftSidebar` | `activePrimaryPanel="history"`；`LeftSidebar` | X；backdrop `mousedown`；另一个 top-level action；page Escape | tab/zoom/batch/favorite 均为 local state；“使用/下载/查看”尚无 graph action。 |
| Tutorial | centered toolbar；`LeftSidebar` | `activePrimaryPanel="tutorial"`；`LeftSidebar` | 重复 trigger；另一个 top-level action；page Escape | 四个入口当前无业务 handler。 |

Primary surface 的关闭策略并不统一：Character/History 是有 backdrop 的 page modal；Toolbox/Material/Move/Tutorial 是 anchored surface，且后四者没有 outside-pointer listener。

### 4.2 Other top-level surfaces

| Surface | 命令与 mount owner | 关闭路径 | 数据/布局副作用 |
|---|---|---|---|
| Add node | centered `+`；`LeftSidebar` -> `AddNodePanel` | trigger；document `mousedown` outside；创建节点后；切到 Material；page Escape；另一个 transient action；Asset drawer 可保留 | 普通 entry 经 page-owned actual-host callback 调用 `addNodeAtFlowCenter`；上传/生成历史仅 local status。 |
| Canvas dropdown | TopNav 或 Asset context；`CanvasTabDropdown` | trigger；document `mousedown` outside；local document Escape；完成 canvas action；另一个 top-level action | 修改 project/canvas lifecycle；不进入 active graph 的 undo/redo history；切换后按 multi-canvas manifest 关闭、重绑或保留其他 surface。 |
| Asset drawer | lower-left command；`page.tsx` -> `AssetManagerPanel` | trigger；X；点击 drawer canvas context 转入 Canvas dropdown；page Escape；多数 top-level action；Add Node/primary panel 保留 | 改变页面横向布局；条目点击只更新 graph selection；Batch 63 default add 使用当前 drawer-open host；Batch 64 的 page-owned layout transaction 在 trigger/X/Canvas-context 路径保持旧 host-center flow anchor，并以 current operation/canvas/instance/viewport guard 避免 stale viewport commit。 |
| Shortcuts | centered keyboard command；`page.tsx` -> dialog | trigger；X；page Escape；另一个 top-level action | 纯展示；文案与实际 handler 差异见 shortcut crosswalk。 |
| Share | TopNav；`TopNavBar` local mount | trigger；page Escape；另一个 top-level action | publish/link 只写 local status；无 outside-close 和 X。 |
| Agent | TopNav 或 storyboard mode；`page.tsx` -> `AgentDrawer` | drawer close command；page Escape；另一个 top-level action；切 workbench | drawer 占据右侧 340px；skill/composer 只写 local state/status。 |
| Zoom | lower-left percent；`BottomToolbar` local mount | trigger；document capture-phase `pointerdown` outside；page Escape；另一个 top-level action | zoom/fit/preset 改 viewport，菜单保持打开；不进入 graph history。 |

### 4.3 Close-path crosswalk

| Surface | Re-trigger | Explicit X/close | Outside pointer | Backdrop | Global Escape | Action completion |
|---|---:|---:|---:|---:|---:|---:|
| Move | yes | via tool choice | no | no | yes | tool choice |
| Toolbox | yes | yes | no | no | yes | no |
| Material | yes | via entry | no | no | yes | entry |
| Character | write-side toggle | yes | backdrop only | yes | yes | apply |
| History | write-side toggle | yes | backdrop only | yes | yes | no |
| Tutorial | yes | no | no | no | yes | no |
| Add node | yes | no | yes, `mousedown` | no | yes | create/transition |
| Canvas dropdown | yes | no | yes, `mousedown` | no | local + global | most canvas actions |
| Asset drawer | yes | yes | no | no | yes | canvas-context transition |
| Shortcuts | yes | yes | no | no | yes | no |
| Share | yes | no | no | no | yes | no |
| Agent | trigger hidden while open | yes | no | no | yes | no |
| Zoom | yes | no | yes, capture `pointerdown` | no | yes | commands keep open |

`CLONE_RUNTIME` 结论：后续不能新增一个“通用 overlay wrapper”后默认给所有 surface 同样的 backdrop/outside/Escape 语义。先确定目标 surface 的源站类别和 interaction contract。

## 5. Independent Route-local Surface

### Organize confirmation

`organizeSnapshot` 是 `page.tsx` local state，不属于 `uiStore.closedOverlayState`：

- 整理画布先写 node positions 和 viewport，再显示“保留/还原”；
- “还原”恢复操作前 nodes 和 viewport；
- “保留”只清除 local snapshot；
- 打开任何 top-level surface 不会清除 confirmation；
- page Escape 会清 selection 和 top-level overlays，但不会清除 confirmation；
- confirmation 可以与 Share、Agent、Asset、primary panel 或 modal 状态并存，只受实际 z-index/pointer ownership 影响。

这是有意的 `HISTORICAL_CONTRACT`（Batch 7/11）和当前 `CLONE_RUNTIME`，不能因为它“看起来像弹窗”就加入 top-level mutual exclusion。

## 6. Mode And Full-screen Boundaries

### 6.1 Storyboard and Agent

`setEditorMode("storyboard")` 会清除 top-level overlays 并打开 Agent；`setEditorMode("workbench")` 会清除它们并关闭 Agent。但这只是进入模式时的 transition，不是持续 invariant：

- storyboard 中可以用 Agent 自己的 close command 关闭 Agent；
- storyboard 中打开任意其他 top-level surface，也会因 `closedOverlayState` 关闭 Agent；
- 上述操作不会把 `editorMode` 改回 workbench。

因此准确表述是“进入 storyboard 时打开 Agent”，不是“storyboard 永远挂载 Agent”。

### 6.2 Director

`openDirectorDesk(nodeId, canvasId)` 会先清除普通 overlays，再设置
`activeDirectorNodeId + activeDirectorCanvasId`。Director 根 surface 是
`fixed inset-0; z-index:100`，拥有自己的 nested panel/viewer 和 Escape 状态机。

但 Director owner 不在 `closedOverlayState` 中：

- 普通 overlay action 不会自动关闭 Director；
- page global handler 在发现 Director active 时对全部普通画布快捷键提前返回，由 `DirectorDesk` 与 nested owner 处理；
- `closeAllPanels()` 本身会清 Director，但 page Escape 的 Director 分支不会调用它；
- Batch 50 已记录 Tab、Space、Delete 和 undo 不穿透普通画布；
- Batch 58 的 route reconciliation 会在 active canvas 变化或 owner node 消失时关闭
  Director；该 UI-only close 不写 graph/history。

当前剩余边界不是“普通 page shortcut 仍穿透”，而是完整 focus trap/return、nested listener precedence 和 source-exact Director keyboard 仍未知。跨 surface selection/focus/command policy 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。

### 6.3 Node-bound owner reconciliation (Batch 58)

图片 Preview、Annotate、Element Edit 和 Director 都属于带 owner 的 session
surface。当前 clone 的 owner identity 是：

```text
{ canvasId, nodeId }
```

route 每次观察 active canvas ID 或 active node 集合变化时，调用纯函数
`reconcileLibTVUiOwners`：

- owner canvas 与 active canvas 不同，立即失效；
- owner node 不在 active canvas，立即失效；
- owner 仍有效时不重复 close；
- close action 只修改 `uiStore`，不调用 graph setter、history 或 viewport；
- 图片 authoring 还保留“必须单选 owner node”的既有 selection boundary。

这是 `CLONE_RUNTIME` / `CLONE_DECISION`，由 Batch 58 local fixture 验证；不写成
LibTV 源站删除语义。源站删除确认、远程资源回收、Director workspace 持久化和
undo 后是否恢复 session overlay 仍未确认。

对于普通选中的图片标准双浮层，Batch 60 增加了更窄的 node-local owner
合同：`ImageToolbar` 与 `ImageEditPanel` 暴露相同的
`data-owner-node-id`，selection 迁移后只保留当前节点的一组 surface。
panel wrapper 不 blanket 捕获 pointer；textarea、按钮和 popover 控件显式
保持可交互。这是 clone-owned 的命中策略；相邻节点被可编辑 panel 覆盖时，
源站实际如何 routing 仍未验证。

## 7. Selected-node And Authoring Surfaces

### 7.1 Mount rule

图片和 ready-video 的标准单节点 surface 使用：

```text
showSingleNodeEditor = React Flow selected && canvasStore.selectedNodeIds.length <= 1
```

- 单选显示节点相对 toolbar/panel；
- 多选隐藏单节点 surface；
- 空白点击通过 selection 清除卸载它们；
- 它们不进入 `uiStore` top-level mutual exclusion；
- modal/drawer 打开通常不会自动取消 selection，因此节点 surface 可以保留在其下方。

### 7.2 Mixed anchoring strategies

| Surface | 当前 clone anchor | 缩放处理 | 备注 |
|---|---|---|---|
| Image toolbar | React Flow `NodeToolbar`, `Position.Top`, `offset=16` | React Flow 非缩放 toolbar host | 当前 action set 宽约 `900.5px`。 |
| Image edit panel | selected node 内 `absolute`, centered, `bottom:-17px`, `translateY(100%)` | `scale(1 / zoom)` | panel 固定 screen width `660px`。 |
| Video toolbar | React Flow `NodeToolbar`, `Position.Top`, `offset=16` | React Flow host | 只在 ready 且没有某些 active tool 时挂载。 |
| Video generation/reshoot/continuation/edit panels | selected node 内 absolute bottom anchor | 多数使用 `scale(1 / zoom)` | active tool 决定哪个 panel 替换 generator。 |
| Smart matting / depth motion | React Flow `NodeToolbar`, `Position.Bottom`, `offset=16` | React Flow host | 宽度由 measured node width clamp。 |
| Video clip edit panel | selected node 内 absolute bottom anchor | `scale(1 / zoom)` | 没有标准 top processing toolbar。 |

这是节点上下浮层容易“位置乱掉”的直接工程背景：视觉上都在节点附近，但 containing block、transform 和 measured-size 依赖并不相同。

### 7.3 Source contract versus current clone

`SOURCE_FACT`（当前专项合同）：

- 标准图片 toolbar 水平中心等于 selected node screen center；
- 当前源站 top host 满足 `nodeTop - 24 * zoom - 10` 再 `translateY(-100%)`；
- 当前源站标准 toolbar 为 content-sized，已观察宽 `1092.5px`；
- bottom panel 水平中心相同，外间距为 `16 * zoom`，screen width 为 `660px`；
- active authoring tool 会替换标准 surface，而不是叠出第三套通用面板。

`CLONE_RUNTIME`：

- 图片 top toolbar 仍使用历史 `NodeToolbar offset=16` 和七个文字动作，宽 `900.5px`；
- bottom panel 使用节点内 inverse scale，并以 `-17px` 补偿边框；
- Smart matting/depth motion 又改用 bottom `NodeToolbar`；
- 当前多种策略是既有实现事实，不证明它们都满足最新 source formula。

精确几何和证据必须回到 [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)，不能从本目录表单独推出新的 offset。

### 7.4 Foreground editor close is not commit

S2/S3 surface 的 mount/close owner 与 editor draft/commit owner 必须分开：面板被 selection、Escape、X、canvas switch、owner delete 或 unmount 卸载，只证明 surface 生命周期结束，不证明 draft 已提交、异步任务已接受或资源已持久化。当前 Text/Picture/Subtitle/image-mode/config/request surface 的 blur/cancel/submit timing 并不统一；有些 local history 正常，有些命令 disabled，有些 enabled-looking command 没有 handler。

后续每个 foreground editor 都必须声明 profile、session/baseline/draft、native/local/graph undo、close policy 和 typed commit result。Dirty draft 遇到 baseline/source drift 不得被 effect 静默覆盖；commit/no-op/conflict/async-accepted 决定 surface 是关闭、保留还是把 failure/retry 交给另一 reachable owner。正式 authority 是 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)；本目录只保留 mount/close/anchor 的 runtime 投影。

## 8. Keyboard, Focus And Pointer Ownership

### 8.1 Page global handler

page handler 先跳过 `input`、`textarea` 和 contenteditable target，再处理 canvas shortcuts。其影响是：

- 在 prompt/input 中按键通常不会触发 canvas delete/group/Tab 等命令；
- 在 overlay 的普通 button、section 或 backdrop 上按键仍可能触发 page shortcuts；
- Character/History/Shortcuts 当前没有 source-exact focus trap；Batch 62 已在 clone page 层为 blocking foreground surface 建立 keyboard boundary，第一层 Escape 只关闭一个 surface并保留 selection；
- Canvas dropdown 的 local Escape 和 page global Escape 仍需 source-exact 复核；Batch 62 的 clone resolver 将其纳入单层 Escape，但不据此推导源站 compound behavior；
- active authoring surface 的 capture-phase Escape handler可能比 page handler更早消费状态，必须按组件单独审计。

帮助文案与运行 handler 的完整差异见 [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)。

Canvas dropdown 的“菜单关闭”不是 canvas switch lifecycle 的完整含义。切换还必须同步分类 selection、node-bound surface、page-local organize/drag/connection/viewport transient、project preference、async observation 和 resource owner；权威 owner manifest 见 [`LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md`](LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md)。Batch 58 只覆盖其中四类 node-bound owner，不能据此推断所有 top-level/page-local state 都已隔离。

本目录只回答 surface 在哪里挂载、由谁关闭和如何定位，不单独决定命令结果应该投影到哪个 surface。`COMPLETED/REJECTED/FAILED/STALE/CONFLICT` 的 typed disposition、stable reason、primary persistent owner、transient announcement、clear/retry/dedupe 和 canvas/route isolation 以 [`LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md`](LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT.md) 为权威；不能因为已有 overlay mount owner，就为每个结果重复增加 toast，也不能把 local status timer 当成 graph/history 状态。

### 8.2 Pointer policy

- AddNode/CanvasDropdown 使用 bubble-phase document `mousedown`；
- Zoom 使用 capture-phase document `pointerdown`；
- Character/History 依赖 backdrop `mousedown`，panel 内 stop propagation；
- node toolbar/panel 通过 `nodrag`、`nopan`、`nowheel` 和 pointer propagation guard 保护编辑；
- Share、Agent、Asset、Move、Toolbox、Material、Tutorial、Shortcuts 没有统一 outside-pointer policy。

`INFERENCE`：未来如果统一使用 click-away helper，必须保留 event type、capture phase、trigger containment 和 React Flow drag ownership，否则可能在 pointerdown 阶段提前卸载 Handle、节点 toolbar 或 submenu。

## 9. Runtime Risks And Documentation Decisions

| ID | 当前事实/风险 | 文档决策 | 编码前闸门 |
|---|---|---|---|
| UI-01 | Primary panel 同时存在一个实际 authority 和五组冗余 boolean/action | 标记为兼容残留，不列为 surface | 搜索所有外部 caller；迁移后再删除。 |
| UI-02 | Notification/UserMenu 有 store state，无 mount owner | 标记为 unmounted | 先取得源站入口证据和产品需求。 |
| UI-03 | `toggleGrid` 无 UI caller | 记录为不可达设置 | 不因 action 存在就补一个按钮。 |
| UI-04 | Storyboard -> Agent 是 transition，不是 invariant | 修正文案 | verifier 覆盖手动关闭 Agent 后的 storyboard。 |
| UI-05 | Batch 50 已隔离 Director 与全部普通 page shortcuts；完整 focus trap、focus return、nested listener 和 source-exact 语义仍未关闭 | 保留 recorded isolation，删除旧“只隔离 Escape”表述 | 以 Batch 50 和 selection/focus static audit 为事实入口，按正式 selection/focus/context contract 收口跨 surface authority。 |
| UI-06 | Batch 62 已阻断 clone page 的 Delete/Tab/group/undo 等普通 canvas keyboard，但 focus trap、target-scoped drawer containment 和 source exact policy 仍未知 | 更新为 partial closure | 保留 Batch 62 verifier；后续逐 surface 取得 source contract。 |
| UI-07 | Outside-close policy 逐组件不同 | 保留差异，不抽象成默认行为 | 逐 surface 取得 source contract。 |
| UI-08 | 节点上下 surface 混用 `NodeToolbar` 与 inverse scale | 指向精确定位合同 | 同 frame 读取 node/toolbar/panel/viewport rect。 |
| UI-09 | 当前图片 toolbar 仍是历史 action set/width | 标记为 source delta | 先更新 action contract，再判断 offset。 |
| UI-10 | Organize confirmation 独立于 overlay store | 保持独立目录 | 验证和 modal/drawer 并存，不误并入 closeAll。 |
| UI-11 | foreground editor surface close、draft cancel、graph commit 与 async acceptance 当前缺共同 owner | 指向 editor session contract，不用通用 overlay close 推导提交 | 按 profile 验证 cancel-blur guard、no-op/one-history、dirty drift、failure/retry 和 enabled-control honesty。 |

## 10. Future Verification Matrix

获得编码授权后，overlay 相关批次至少应覆盖：

### Top-level lifecycle

1. 每个 top-level trigger 打开正确的唯一 surface；organize confirmation 除外。
2. 重复 trigger、X、outside、backdrop、Escape 和 action-complete 按本文矩阵关闭。
3. 一个 top-level action 关闭其余 top-level state，但不清 organize confirmation。
4. Canvas/Asset transition 不产生短暂的无 owner open state。
5. Storyboard 中手动关闭 Agent 后仍保持 storyboard，并明确这是预期还是待修正。

### Keyboard and Director

1. modal 前台时 Delete、Tab、group、undo/redo 是否应到达 canvas 有明确断言。
2. Director 前台时 page shortcuts 不产生未声明的后台 overlay 或 graph delta。
3. nested Director viewer/panel 的 Escape 优先于关闭 workspace。
4. editable target guard 不吞掉组件自己需要处理的 Escape/Enter。

### Selected-node surfaces

1. 单选只显示一组标准上下 surface；多选和空选卸载。
2. pan、zoom、drag 后 node、top toolbar、bottom panel 使用同一 frame 的 rect。
3. top/bottom 中心与 source gap formula 分别断言，不以浏览器中心代替 node center。
4. active tool 替换标准 L2，不叠加第三 surface。
5. pointerdown、wheel、text editing 不误触发 node drag/pan/selection clear。
6. foreground editor close/cancel/no-op/commit/async-accept 各有可区分结果；local/native/graph undo 每次只消费一层。

## 11. Maintenance Rules

发生以下变化时更新本文：

- `uiStore` 新增、删除或重命名 overlay state/action；
- page/TopNav/LeftSidebar/BottomToolbar 改变 mount owner；
- outside-click、Escape、focus 或 backdrop 语义变化；
- storyboard/Agent 或 Director/page shortcut ownership 变化；
- selected-node surface 的 anchor strategy 或 mount condition 变化。

不要在本文复制每个面板的视觉像素和完整业务动作。视觉尺寸回到组件 spec；graph delta 回到 graph transaction catalog；源站当前几何回到 overlay positioning contract。

Selection、DOM focus、listener phase 和 command context 的 fixed baseline 见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_STATIC_AUDIT_2026-08-27.md)，正式 selection/context/focus lifecycle 权威见 [`LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md`](LIBTV_SELECTION_FOCUS_COMMAND_CONTEXT_CONTRACT.md)。

Overlay catalog 只登记 mount/close/position owner；actual host frame、six coordinate domains、live/stable viewport、host resize and gesture/placement generation 以 [`LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) 为权威。Selected-image 的 exact toolbar/panel 数字仍回到 [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)，不能从 Open Canvas 菜单/Panel 数字或 generic clamp 推导。

Foreground editor 的 session/baseline/draft、native/local/graph undo、commit/cancel/async/resource handoff 以 [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md) 为权威。本目录中的 close path 不能单独证明 semantic acceptance 或 durable save。

## 12. Related Documents

- [`liblib-canvas-batch11-2026-08-25/OVERLAY_LIFECYCLE.spec.md`](liblib-canvas-batch11-2026-08-25/OVERLAY_LIFECYCLE.spec.md)：top-level exclusion 的历史设计合同。
- [`liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`](liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)：L0-L5 状态层级和 source/clone 边界。
- [`components/LibTVOverlayPositioning.contract.md`](components/LibTVOverlayPositioning.contract.md)：当前图片上下浮层精确源站几何。
- [`LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md`](LIBTV_SHORTCUT_RUNTIME_CROSSWALK.md)：help/handler/context 对照。
- [`LIBTV_GRAPH_TRANSACTION_CATALOG.md`](LIBTV_GRAPH_TRANSACTION_CATALOG.md)：graph/history 副作用目录。
- [`LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)：foreground editor session、local history、commit/close 和 `VR-022` 权威。
- [`LIBTV_UIUX_PARITY_BACKLOG.md`](LIBTV_UIUX_PARITY_BACKLOG.md)：把本目录风险放入当前价值、证据、授权和 fixture 优先队列。
- [`PAGE_TOPOLOGY.md`](PAGE_TOPOLOGY.md)：page shell 和 z-index 区域。
