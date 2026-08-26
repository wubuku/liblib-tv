# Open Canvas 对 LibTV UI/UX 复刻的持续启发

> 定位：面向后续 LibTV UI/UX 复刻 batch 的研究转译文档。Open Canvas 是启发来源，不是 LibTV 的视觉真相；LibTV 原站取证优先于 Open Canvas 源码和官网。

## 1. 使用原则

### 1.1 三层事实纪律

后续每个 UI/UX 结论都分成三层：

1. **LibTV 源站事实**：决定 clone 最终长什么样、怎么交互；
2. **Open Canvas 启发**：提供可迁移的组件分层、状态建模、坐标计算或验证方法；
3. **clone-only 决策**：因为当前 prototype 的边界、可测试性或安全需要而做的实现选择。

Open Canvas 的任何结论都不能直接升级为 LibTV 源站事实。它能帮助我们发现“为什么浮层会乱”“为什么参数和节点状态容易分叉”，但不能告诉我们 LibTV 的精确像素、文案或交互意图。

### 1.2 推荐的研究顺序

```text
LibTV 当前问题
  -> LibTV 源站操作与 DOM/截图证据
  -> Open Canvas 源码中的同类机制
  -> 共同的抽象问题
  -> clone-only 实施决策
  -> 小批次实现与回归
```

反向顺序会产生两个风险：把 Open Canvas 的 alpha 行为误当作 LibTV 规格，或为了复用抽象而改变已有的 LibTV edge flow effect、面板位置和移动端退化规则。

## 2. 当前最高价值启发：浮层是坐标合同，不是 CSS 偏移

### 2.1 Open Canvas 的实现启发

固定 commit 的 `CanvasStudioShell` 对 selected editor/action overlay 分别计算锚点：

- 读取 `selectedNode.measured.width/height`，再回退到 node width/height；
- 使用 live viewport 的 `x/y/zoom` 将 flow position 转成 canvas screen position；
- 编辑器以节点中心为 `left`，以节点底部为 `top`，另加 18px gap；
- Image action toolbar 以节点顶部为 `top`，使用 `translate(-50%, -100%)` 放在节点上方；
- 编辑器宽度由容器宽度计算，范围为 360-820px；
- 两个浮层都是 React Flow `Panel position="top-left"`，但共享同一套节点中心和 viewport 语义。

证据：[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L5964)、[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6015)、[`canvas-studio-shell.tsx`](../../../research/upstream/open-canvas/shared/blocks/canvas/canvas-studio-shell.tsx#L6396)。对应声明为 OC-018。

启发不是这些具体数字，而是：**节点尺寸来源、viewport 来源、screen anchor、浮层层级和边缘策略应该由一份可复核的合同共同决定**。

### 2.2 LibTV 的源站合同不能被替换

当前项目已有 LibTV ImageNode 的源站复刻合同：

- 顶部 `ImageToolbar` 使用 React Flow `NodeToolbar`，`position=Top`、`align=center`；当前生产 host 的 source positioning 是 `nodeTop - 24 * zoom - 10` 加 `translateY(-100%)`，所以 screen gap 为 `10 + 24 * zoom`，而不是 clone 当前 `offset=16` 的完整合同；
- 工具条在画布缩放时保持屏幕尺寸，但宽度由当前动作集合决定：2026-08-25 的历史快照为 `900.5x49`，2026-08-26 的当前五节点快照统一为 `1092.5x49`；
- 工具条中心等于选中 ImageNode 的屏幕中心，不等于浏览器窗口中心；
- 底部 `ImageEditPanel` 是 ImageNode 的子节点，使用 `left:50%`、`bottom` 负偏移和 `scale(1/zoom)` 保持屏幕尺寸；
- 原站允许靠近边缘时被 React Flow 容器裁剪，不做水平居中或强行 clamp。

当前工具条外层 DOM 使用 `w-fit`；新增 `元素编辑 / 图层分离` 两个 `88px` 动作及两个 `8px` 间距，完整解释了 `192px` 宽度增量。证据：[`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md)、[`ImageNode.spec.md`](../components/ImageNode.spec.md#selected-state)、[`ImageEditPanel.spec.md`](../components/ImageEditPanel.spec.md#positioning-contract)。对应声明为 OC-020。

因此，Open Canvas 的“集中计算 screen anchor”可以启发后续实现，但不能把 LibTV 的底部面板改成 Open Canvas 的 page-level Panel，也不能为了避免裁剪而把浮层移动到浏览器中心。

### 2.3 当前 clone 的诊断假设

当前 clone 的结构已经是“ImageNode 内部挂底部编辑器 + NodeToolbar 挂顶部工具条”：

- [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L42) 根据选中状态和选择数量决定是否显示两个层；
- [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L125) 挂载 `ImageToolbar`；
- [`ImageNode.tsx`](../../../src/components/nodes/ImageNode.tsx#L166) 挂载 `ImageEditPanel`；
- [`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx#L33) 采用 `NodeToolbar`；
- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L101) 采用节点内绝对定位和反向缩放。

若仍出现“上方工具条和下方面板位置乱”，后续应优先验证以下假设，而不是立即改 offset：

1. 两个浮层是否使用了不同的节点尺寸来源（React Flow measured size vs. 业务 data width/height）；
2. 顶部工具条由 React Flow 管理、底部面板由 node DOM 管理，是否在 viewport 更新时出现一帧不同步；
3. `zoom` 是否来自同一个 live viewport，还是一个来自 store、一个来自 React Flow hook；
4. NodeToolbar 的内部 transform 与 ImageEditPanel 的 `scale(1/zoom)` 是否叠加或抵消错误；
5. 多选切换、节点拖动、空白点击和边缘裁剪是否触发了不同的 selected state；
6. 节点实际尺寸变化后，底部 panel 的固定高度/宽度是否仍与源站合同一致。

这些是待取证假设，不是已确认的 bug 根因。当前 clone 的结构事实对应 OC-019；“结构已存在”不能升级为“所有 viewport 场景都正确”。

2026-08-26 的五节点复测已经排除一个旧假设：`900.5` 和 `1092.5` 不是由图片内容态切换。当前生产 chunk 又确认了顶部 host 的 `10 + 24 * zoom` 定位公式。当前更高价值的 clone 缺口是工具条动作集合、末端图标语义、`w-fit` sizing mode 和该垂直公式落后于源站；剩余几何风险集中在拖动/平移时序和 100% virtualization 边界，不应再次凭感觉改 offset。

## 3. 启发转译矩阵

| Open Canvas 机制 | 可迁移的抽象 | LibTV 必须遵守的源站事实 | 后续研究/实现批次 |
|---|---|---|---|
| measured node + live viewport 计算浮层 | 统一 screen anchor contract | ImageToolbar 置顶、ImageEditPanel 节点内置底；允许裁剪 | `LIBTV-UIX-01` |
| `<Handle>` 作为真实连接入口 | 语义化连接锚点，避免装饰层拦截拖拽 | 不改变现有 LibTV handle 位置和 edge flow effect | `LIBTV-UIX-02` |
| `BaseCanvasNode` 与独立 editor panel | 节点内容和编辑控制分层 | ImageNode 的顶部/底部层级由源站截图决定 | `LIBTV-UIX-03` |
| imageOutputs/videoHistory + selected index | 媒体历史是节点状态，不是临时弹窗状态 | 先查 LibTV 是否展示多输出/历史，再决定是否引入 | `LIBTV-UIX-04` |
| model-options 能力矩阵 | 参数可见性由模型能力驱动 | 以 LibTV 当前模型菜单和参数面板为准 | `LIBTV-UIX-05` |
| dirty/saving/conflict | 明确保存状态而非单一 loading | 只有需要真实持久化时才引入 clone 语义 | `LIBTV-UIX-06` |
| Canvas Panel + minimap/zoom | 画布级 controls 与节点级浮层分离 | 服从现有 `BottomToolbar` 和 `MainEntryPanels` 合同 | `LIBTV-UIX-07` |
| onboarding / empty state | 首次使用的状态机和入口分层 | LibTV 当前入口是否存在同等流程需另取证 | `LIBTV-UIX-08` |

## 4. 后续 UI/UX 研究批次

### `LIBTV-UIX-01`：选中节点双浮层几何

**优先级：P0。**

先不编码，完成以下证据矩阵：

| 场景 | 必测内容 |
|---|---|
| 选中普通图片 | node rect、toolbar rect、editor rect、两者中心和 gap |
| 节点拖动 | pointer down/move/up 过程中两个浮层是否同步 |
| 画布平移 | React Flow viewport 改变后 rect 是否连续跟随 |
| 28%/53%/100% zoom | toolbar/editor 是否保持源站屏幕尺寸 |
| 节点靠近四条边 | 是否裁剪、裁剪区域是否与源站一致 |
| 切换另一张图片 | 旧浮层是否卸载，新浮层是否一次性出现 |
| 多选/空白点击 | 单节点浮层是否完全隐藏 |
| 390px 移动端 | 是否按源站裁剪/退化，不做擅自居中 |

**交付物**：截图、DOM rect 表、anchor 公式、`SOURCE_FACT`/`INFERENCE`/`CLONE_DECISION` 三栏记录。

**停止条件**：若没有新的源站证据，只能修正已知坐标系错误，不能引入新的 clamp、自动避让或页面级重排。

**当前进展**：28% zoom 下的五图片节点、三种 panel 高度、边缘裁剪和工具条时间版本差异已经落入 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md)。剩余几何重点为多 zoom、拖动/平移和选择卸载时序；当前六个新增/末端动作已进入下一份状态矩阵。

六动作中的 preview 和空 annotate 已完成安全 live 复测，其他动作已从当前 bundle 还原状态与副作用，见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md)。关键修订是：active image tool 会替换标准工具条、隐藏底部生成面板并在节点上挂编辑 surface；因此 `editingImageTool` 必须进入 `UIX-01` 的几何/生命周期矩阵，不能把所有动作都实现为一次 `addDerivedNode`。标准工具条的顶部定位公式已由当前 chunk 确认，后续只需验证 clone 的 React Flow transform 映射。

### `LIBTV-UIX-02`：连接语义与 Handle

Open Canvas 的重要启发是连接应同时具备：真实 Handle、类型兼容性、非法反馈、边去重和环检测。对 LibTV 后续工作，只研究与当前原站相符的连接入口：

- handle 是否始终可见，还是 hover/选中时出现；
- 连接菜单是从 handle、边中点还是鼠标释放点打开；
- 节点生成后是否自动选中、自动定位或自动连边；
- 删除节点/边时是否同步关闭相关浮层。

不能因为 Open Canvas 使用左右 handles，就直接改变当前 LibTV 的连接方向和边动效。

### `LIBTV-UIX-03`：节点内容层与控制层

从 Open Canvas 借鉴层级，而不是复制视觉：

```text
画布层
├── 画布级导航/工具/缩放/缩略图
├── React Flow 节点和边
│   ├── 节点内容
│   ├── 节点状态/进度
│   └── 真实连接 Handle
├── 选中态节点控制
│   ├── 顶部操作工具条
│   └── 底部参数编辑器
└── modal / drawer / preview 等跨节点层
```

对 LibTV，层级合同必须与已有研究一致：`ImageToolbar` 不得被底部编辑器遮挡，底部编辑器不能拦截节点拖拽，modal 打开时必须有明确的事件隔离和关闭规则。参考 [`MainEntryPanels.spec.md`](../components/MainEntryPanels.spec.md#interaction-contract)。

### `LIBTV-UIX-04`：媒体输出历史

Open Canvas 把 `imageOutputs`、`videoHistory` 和 selected index 放进节点 data，这提示我们研究 LibTV 的“生成后继续操作”是否需要历史状态：

- 生成多个候选时，候选属于当前节点还是新节点；
- 重新选择候选后，顶部工具条和底部参数是否复用；
- 下游引用指向当前选中结果还是固定输出版本；
- 删除/重试/派生节点时，历史是否保留。

只有 LibTV 源站存在对应交互时，才把它升级为 clone 功能；否则只作为未来产品能力研究，不进入视觉复刻批次。

### `LIBTV-UIX-05`：模型能力驱动参数

Open Canvas 的 `model-options.ts` 说明一个可复用的工程原则：模型选择、场景和可用字段应形成能力矩阵。转译到 LibTV 时需要先建立：

| 能力维度 | 需要从 LibTV 取证的内容 |
|---|---|
| aspect ratio | 菜单选项、默认值、切换后 node/editor 高度 |
| resolution | 显示名称、互斥关系、是否影响 credits 文案 |
| duration | Seedance/视频节点的可见时长和限制反馈 |
| reference mode | 首帧、尾帧、首尾帧、视频/图片引用入口 |
| output count/history | 单输出、候选网格、历史回选 |
| unsupported state | 字段隐藏、禁用、解释文案还是 toast |

先完成这张表，再决定是否抽象成当前 clone 的纯数据模块；不要把 Open Canvas 的 provider/model slug 直接带入 LibTV。

### `LIBTV-UIX-06`：保存与运行反馈

Open Canvas 把 `idle/queued/running/success/error` 和 `dirty/saving/saved/conflict` 分开，这对 LibTV 的启发是状态语义应可观察：

- 运行状态不要覆盖保存状态；
- 失败要区分参数错误、任务失败、网络失败和本地 mock；
- 保存中不能让节点拖拽或浮层位置失去响应；
- 异步结果回来时不能覆盖用户后续编辑。

当前项目若仍是前端原型，只保留可见状态和 mock 行为，不在未授权情况下引入 provider、持久化或真实任务轮询。

### `LIBTV-UIX-07`：画布级控件

Open Canvas 将 add node、minimap、zoom 等作为 React Flow `Panel`，当前 LibTV 已有自己的 `LeftSidebar`、`BottomToolbar`、zoom menu、minimap 和 modal 合同：

- [`BottomToolbar.spec.md`](../components/BottomToolbar.spec.md) 规定缩略图、缩放和底部工具条的桌面/移动布局；
- [`MainEntryPanels.spec.md`](../components/MainEntryPanels.spec.md) 规定主入口面板互斥和 backdrop 行为；
- [`BEHAVIORS.md`](../BEHAVIORS.md) 是现有行为索引。

后续借鉴重点应是“画布级和节点级控制互不串层”，而不是统一两个项目的视觉样式。

### `LIBTV-UIX-08`：空状态与 onboarding

官网和 Open Canvas 应用入口把空状态、Key 设置、导入 JSON、新建画布拆成明确步骤。对 LibTV，只有在源站存在类似首次使用流程时才复刻；否则可以借鉴信息架构中的：

1. 空状态应说明当前画布可做什么；
2. 主操作应只有一个明确入口；
3. 设置/帮助/导入不应与节点编辑器共享同一浮层层级；
4. 跳过和继续的状态需要可复现，不依赖隐式 session。

## 5. 可复用的研究记录模板

后续每个 batch 的研究文档可以采用以下结构：

```markdown
# <batch>: <交互名>

## Source target
- LibTV URL / route / login state / observation date
- Open Canvas source file and fixed commit, if used as inspiration

## Interaction steps
1. ...

## Measurements
| state | node rect | overlay rect | viewport | notes |
|---|---:|---:|---|---|

## SOURCE_FACT
- 只写源站直接观察到的事实。

## OPEN_CANVAS_INSPIRATION
- 只写上游源码提供的方法或结构启发。

## INFERENCE
- 说明从两类证据得到的推断。

## CLONE_DECISION
- 明确当前 clone 选择、非目标和原因。

## Verification
- screenshot / DOM selector / viewport matrix / script
```

## 6. 长期优先级

| 优先级 | 方向 | 原因 | 当前状态 |
|---|---|---|---|
| P0 | LibTV 双浮层几何和选中态生命周期 | 当前已知视觉缺陷，直接影响可信度 | 先取证，待授权编码 |
| P1 | 节点/编辑器/画布层级合同 | 降低浮层互相遮挡和事件穿透 | 研究合同可先写 |
| P1 | 模型能力矩阵与参数面板 | 支撑近期 Seedance/视频亮点复刻 | 先建立 LibTV 证据表 |
| P1 | Handle/连接菜单/派生节点 | 决定工作流是否可用 | 不能改变现有边效果 |
| P2 | 媒体历史和结果回选 | 影响连续创作效率 | 需源站证据 |
| P2 | 运行/保存状态可视化 | 让 prototype 状态诚实可读 | 暂不接真实 provider |
| P3 | BYOK/onboarding/provider 视觉 | Open Canvas 特色明显但非当前 LibTV 核心 | 仅作旁证 |

## 7. 完成定义

本转译文档在当前阶段完成的标准是：

- 已明确 Open Canvas 的启发边界，不覆盖 LibTV 源站事实；
- 已将浮层问题转成坐标、层级、状态生命周期和边缘策略四类可验证问题；
- 已映射当前 clone 的已有实现和研究合同；
- 已建立未来 UI/UX batch、研究模板和停止条件；
- 未修改业务代码，未把上游 provider 或 graph runtime 接入当前项目。

本文件应与 [`REPORT.md`](REPORT.md)、[`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md)、[`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md) 和当前 LibTV 组件规格共同阅读。
