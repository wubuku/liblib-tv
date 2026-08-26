# LibTV UI 状态层级与转换合同

> 目的：为后续 LibTV UI/UX 复刻定义“哪个状态属于哪一层、如何切换、何时改变 graph”。
> 本文只做研究和设计合同，不授权修改 `src/`，不把 Open Canvas 的 UI 当作 LibTV 视觉事实。

## 1. 核心判断

LibTV 画布不是一组相互独立的浮动元素，而是五层状态共同投影：

```text
L0 page shell
  ├── 顶部导航 / 底部画布工具 / drawers / dialogs
L1 canvas graph
  ├── React Flow viewport
  ├── nodes / edges / handles
  └── graph selection
L2 selected-node controls
  ├── standard toolbar above selected node
  └── generation/edit panel below selected node
L3 active authoring tool
  ├── annotate canvas
  ├── interactive element edit
  ├── rotate/mirror draft
  └── layer composition editor
L4 page-level media view
  └── preview overlay
L5 process/result graph
  └── derived media, analysis outputs, task/process nodes
```

最容易出现错误的地方是把不同层压成一个 `isOpen` 或一个 `addDerivedNode` 回调。源站事实表明：

- L2 的标准 toolbar 和 generation panel 同时服务一个选中节点，但使用不同的定位合同；
- L3 会替换 L2，而不是在 L2 上再堆一个第三浮层；
- L4 是 page-level preview，位于节点之上，关闭后恢复原选择；
- L5 的节点/边变化必须与 L2/L3 的 UI 状态分开记录；
- 空白点击、多选和 active tool 都有明确的浮层卸载规则。

## 2. 状态层级

### 2.1 L0：页面壳层

| 状态 | 典型元素 | 作用域 | 对节点选择的影响 |
|---|---|---|---|
| Canvas shell | 顶部导航、主入口、底部工具条、画布控制 | page fixed / canvas fixed | 一般不改变 selection |
| Drawer | 资产管理、Agent、分享等 | page overlay + canvas reflow | 可能改变可见画布宽度，不应接管节点浮层 |
| Modal/dialog | 快捷键、确认、危险操作 | page-level modal | 应阻断底层点击和快捷键 |
| Preview | 图片/视频媒体预览 | `fixed inset-0` | 节点仍在后面；关闭后回到原选中态 |

L0 的事实和互斥关系见 [`BEHAVIORS.md`](../BEHAVIORS.md)、[`MainEntryPanels.spec.md`](../components/MainEntryPanels.spec.md) 和图片动作矩阵。Open Canvas 的 Panel 只能启发分层，不替换这些 LibTV 合同。

### 2.2 L1：画布 graph 层

L1 保存并呈现：

- nodes、edges、node data、parent/child 关系和 viewport；
- selected node(s)；
- React Flow 的真实 Handle 和 edge path；
- 派生节点、分析结果、长视频过程节点和版本关系。

selection 是 graph/UI 的共同输入，但不是所有 selection 变化都产生 graph mutation：

| 事件 | graph 变化 | UI 变化 |
|---|---|---|
| 点击单个图片/视频节点 | 无 | 显示该节点的 L2 surfaces |
| 点击空白 | 无 | 卸载所有单节点 surfaces |
| Meta/多选 | 无 | 隐藏单节点 surfaces |
| pan/zoom | 无 | 重新计算节点和浮层 screen rect |
| 节点拖动 | 更新 node position | surfaces 继续跟随或在失去 selection 时卸载 |
| 预览 | 无 | 打开 L4 page overlay |
| 进入可能产生输出的工具 | 可能 | 从 L2 转到 L3 或 L5 |

### 2.3 L2：标准选中节点控制层

标准图片/视频状态是一个成对关系：

```text
selected node
├── top standard toolbar
└── bottom generation/edit panel
```

二者共同条件是“单个节点被选中且没有 active tool”，但不共享 containing block：

| Surface | Source anchor | Screen size | 层级事实 |
|---|---|---:|---|
| ImageToolbar | node center + node top | 当前 `1092.5x49` | React Flow `NodeToolbar`/非缩放层 |
| ImageEditPanel | node center + node bottom | `660px` 宽，高度依内容态 | node 内 absolute + inverse zoom |
| Video processing toolbar | ready-video node context | source action set 尚需 ready fixture | 不得用失败视频推断 |
| Video generation panel | selected video node bottom | `660px` 宽 | node 内 absolute + inverse zoom |

图片标准双浮层的精确公式见 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)。

### 2.4 L3：active authoring tool

active tool 的共同特点是：

1. 标准 L2 toolbar 被专用 toolbar 替换；
2. 标准底部 generation panel 卸载；
3. 节点本体或专用 surface 承载草稿/标记；
4. Escape、关闭、丢弃或保存决定是否回到 L2；
5. 只有提交/保存/任务完成时才允许产生 L1/L5 mutation。

已确认的状态：

| Tool | 当前源站观察 | 退出边界 | graph 风险 |
|---|---|---|---|
| Annotate | `536x49` 专用 toolbar、DPR2 canvas；标准 panel 不存在 | Escape 恢复 L2；保存未执行 | 空态低；绘制后待确认 |
| Element edit | `272x44` toolbar、stage、mask/guide、`400x50` record panel | Escape 恢复 L2；有效 record 后才可生成 | 空态低；提交中高 |
| Rotate/mirror | bundle 有 local draft 和 dirty modal；共享 fixture 入口产生了“旋转与镜像”派生节点 | 已用撤销恢复；未继续深入 | 高，入口不是纯 UI |
| Layer separation | composition editor；splitting/redrawing/merging/task 状态 | 需要任务/丢弃/完成边界 | 高，禁止共享画布试探 |

完整证据和安全边界见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)。

### 2.5 L4：page-level preview

预览不是节点的第三个控制面板，而是 L0 page overlay：

- `fixed inset-0`，黑色半透明背景；
- 内容区域以 viewport 为约束，媒体保持自身比例；
- 关闭后标准节点选择和 L2 surfaces 恢复；
- 当前现场没有发生 graph、Prompt、参考图或任务变化。

源站 close button 的可访问性不足属于源站缺陷；clone 后续可复刻几何和生命周期，但应提供可访问名称。

### 2.6 L5：过程与结果 graph

片段重拍、逐帧拉片、超长视频和图片派生结果都可能进入 L5。L5 不应被误写为 L2 的局部 loading：

```text
source version
  -> operation draft
  -> task/process state
  -> candidate/result version
  -> downstream reference
```

对 clone 而言，L5 可以使用本地 mock，但必须保留 source ID、操作类型、时间范围、版本和 graph transaction 边界，不能用一个最终 URL 覆盖全部历史。

## 3. 状态图

```text
U0 no selection
  ├── select one image/video -> U1 standard selected
  ├── select multiple -> U2 multi-selected
  └── open preview from an existing result -> U4 preview

U1 standard selected
  ├── pan / zoom / node drag -> U1 with new rects
  ├── empty click -> U0
  ├── multi-select -> U2
  ├── preview -> U4
  └── active tool entry -> U3 authoring

U3 authoring
  ├── Escape / close / discard -> U1
  ├── local draft -> U3 with records
  ├── explicit submit/save -> U5 process/result
  └── graph-mutating entry -> U5 after transaction

U5 process/result
  ├── source remains selected -> U1 or U3 according to tool
  ├── new result selected -> U1 on new node
  ├── pending/error -> U5 with visible status
  └── undo/redo -> prior graph/UI state

U4 preview
  └── close / Escape -> the unchanged selection state before preview
```

这张图把“打开工具”和“生成结果”明确分开。任何 clone 实现都不能在入口点击时默认跳到 U5。

## 4. 转换与副作用合同

| 转换 | UI 层变化 | node data | nodes/edges | 需要事务 |
|---|---|---|---|---|
| U0 -> U1 | 挂载 L2 toolbar/panel | no | no | no |
| U1 -> U2 | 卸载单节点 L2 | selection only | no | no |
| U1 -> U3 empty | 替换 L2 为专用 editor | local draft/session | no | no |
| U3 -> U1 discard | 恢复标准 L2 | 丢弃未提交 draft | no | no |
| U1 -> U4 | 挂载 page overlay | no | no | no |
| U1 -> U5 task | 显示 task/process state | operation metadata | maybe | yes |
| U1 -> derived result | 新结果节点/边或 patch | result/version data | yes | yes |
| U5 -> undo/redo | 恢复 graph 与 selection | restore snapshot | restore | yes |

“maybe”表示当前源站仍需针对具体动作确认；clone-only 实现必须把具体选择写清楚，不能含糊地复用一个通用回调。

## 5. 位置、层级和事件规则

### 5.1 几何

- L2 toolbar 和 panel 的水平中心都等于 selected node 的 screen center；不等于浏览器中心；
- toolbar 当前 source formula 是 `nodeTop - 24 * zoom - 10` 加 `translateY(-100%)`；
- panel 外边界到 node bottom 的 screen gap 是 `16 * zoom`；
- source 允许负 x/y 和 React Flow 容器自然裁切；不做 viewport clamp；
- active tool 的专用 toolbar/stage 必须重新取证，不能套用标准 toolbar 公式；
- 一个 viewport snapshot 内同时读取 node、toolbar、panel、zoom，不能混用 stale DOM 和 store 数据。

### 5.2 层级

建议把层级理解成“职责顺序”，而不是任意增大 z-index：

```text
canvas background/edges
  < node body/handles
  < standard node toolbar/panel
  < drawers and dialogs
  < page-level preview/modal
```

具体 z-index 仍以当前 clone CSS 和源站 DOM 取证为准。任何新增层都必须说明其 containing block、pointer-events、滚轮事件和 Escape 所属状态。

### 5.3 事件

- node body 点击负责 selection；
- toolbar/panel 内部控件必须阻止误触发 node drag/reselection；
- panel 输入区使用 `nodrag nowheel nopan` 保护文本编辑；
- Handle 必须是实际连接入口，不能用装饰层拦截连接拖拽；
- active tool 的 canvas pointer events 只作用于当前编辑 session；
- page preview 打开时，底层 canvas 不应继续接收生成/拖拽快捷键。

## 6. 研究到实施的决策规则

后续 agent 处理任意 LibTV 入口时，按下面顺序回答：

1. 入口属于 L0、L2、L3、L4 还是 L5？
2. 点击入口是否只改变 UI，还是会改变 node data/nodes/edges？
3. 若进入 L3，标准 L2 两个 surface 是否同时卸载？
4. 若进入 L5，source version、operation、task、result 和 undo/redo 边界是什么？
5. 该状态是否已有源站事实，还是只有文章线索、bundle 推断或 clone-only 选择？
6. 对应回归脚本验证的是历史快照还是当前合同？

如果第 1-4 项无法回答，停止编码设计，先更新证据矩阵。不得用“先做一个看起来像的弹窗”填补状态未知。

## 7. 验证合同

获得编码授权后，至少需要覆盖：

### Standard selection

- 单选图片/视频只出现一组标准双浮层；
- 空白点击卸载两层；多选隐藏两层；切换节点不残留旧层；
- pan、zoom、node drag 后中心和 gap 仍满足当前合同；
- 边缘负坐标自然裁切，不擅自回到浏览器中心；
- node、toolbar、panel 来自同一 frame 的 rect；

### Active tool

- annotate/element edit 入口替换 L2，而不是增加第三浮层；
- Escape/close/discard 恢复原选择和 L2；
- 空态不会改变 nodes/edges；
- 有效草稿提交前不创建“完成结果”节点；
- rotate/layer separation 只在 disposable fixture 上验证 graph delta；

### Process/result

- 任务状态不覆盖用户编辑状态；
- 派生节点/边操作是单一可撤销事务；
- source ID、时间范围、operation 和版本可追溯；
- 结果回到画布后，选择态和对应浮层有明确规则；
- repeated submit、undo/redo 和 mobile clipping 有独立断言。

## 8. 未决与停止条件

| 未决项 | 当前状态 | 停止条件 |
|---|---|---|
| ready-video 工具条完整顺序/几何 | 当前共享项目只有失败视频 | 不为取得结果而修改共享项目；等待安全 ready fixture |
| Auto Link ghost 精确视觉 | 静态 bundle 已确认状态链，未在共享项目输入 | 不输入/接受；等待空白项目或授权 |
| 标注绘制后 dirty/save | 空态已验证，保存未执行 | 需要 disposable fixture |
| 旋转 dirty modal | 入口已证明可能 graph mutation，已撤销 | 不在共享项目继续点击 |
| 图层分离任务状态 | bundle 有任务链，未 live 进入 | 需要任务/积分/副本授权 |
| source 当前 z-index 精确值 | 需要场景化 computed style | 不用 clone z-index 反推源站 |

## 9. 相关文档

- [`NEXT_RESEARCH_PLAN.md`](NEXT_RESEARCH_PLAN.md)：批准的研究-only 路线。
- [`LIBTV_FEATURE_GAP_MATRIX.md`](LIBTV_FEATURE_GAP_MATRIX.md)：五项主推能力总矩阵。
- [`LIBTV_VERIFICATION_COVERAGE.md`](LIBTV_VERIFICATION_COVERAGE.md)：现有回归覆盖和历史断言边界。
- [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)：双浮层几何合同。
- [`LibTVAutoLink.contract.md`](../components/LibTVAutoLink.contract.md)：Auto Link 数据和状态合同。
- [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)：图片动作副作用矩阵。
- [`UIUX_TRANSLATION.md`](../open-canvas-2026-08-26/UIUX_TRANSLATION.md)：Open Canvas 启发和 LibTV 边界。

