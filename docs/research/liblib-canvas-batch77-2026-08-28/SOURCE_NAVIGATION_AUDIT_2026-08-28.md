# Batch 77 LibTV Source Navigation Audit

> 日期：2026-08-28。
>
> 目标：核对普通 LibTV 画布的拖动、缩放、鼠标按钮、键盘工具和 macOS
> 触摸板事件路径。范围是只读 viewport/UI 行为，不创建、删除、移动或连接源站
> graph 节点。

## 1. 采集环境

| 项目 | 值 |
|---|---|
| Source URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| 登录态 | 用户已登录的有头 Chrome/CDP session |
| Viewport | `1200x829` CSS px |
| DPR | `2` |
| Baseline | 源站“适合屏幕”后约 `translate(115.032px, 161.723px) scale(0.302727)` |
| Safe pointer | `(1040, 650)`，命中 `.react-flow__pane` 空白区域 |
| 证据类型 | DOM/computed style + Playwright pointer/wheel runtime；本次不依赖截图识别 |

每项测试后都使用源站缩放菜单的“适合屏幕”恢复 viewport，并点击空白区域清除
selection。没有触发节点拖动、文件选择、上传、生成、连线、删除或保存。

## 2. Source UI facts

源站底部导航可见：

- `移动` 按钮；
- `快捷键` 按钮；
- `缩放选项` 按钮，基线项目显示约 `30%`；
- 缩放菜单项：`放大⌘+`、`缩小⌘-`、`适合屏幕⌘0`、`缩放至50%`、
  `缩放至100%`、`缩放至800%`。

快捷键面板的可见文本包含：

```text
移动 V
抓手工具 H
移动画布 / 键盘 Space
移动画布 / 触控板
移动画布 / 鼠标
缩放 / 触控板
缩放 / 鼠标 cmd
适应画布 0
```

快捷键面板是宽屏横向四列；在当前窄视口下变成单列/多行滚动容器。源站帮助
文本与缩放菜单在 fit-view modifier 上不完全一致，运行时结果见第 4 节。

## 3. Test protocol

每次输入都在空白 pane 点 `(1040,650)`，然后读取：

- `.react-flow__viewport` 的 `translate(x,y) scale(zoom)`；
- pane cursor 和工具按钮 label；
- visible selected node 数量；
- visible selection rectangle 数量。

拖动均为从 `(1040,650)` 到 `(1130,700)`，wheel 使用 `deltaX/deltaY=240`。
这组数字用于判断方向和比例，不作为产品常量。

## 4. Runtime matrix

| 输入 | Source result | 关键观测 |
|---|---|---|
| 普通纵向 wheel | 平移 | `y: 161.723 -> -78.2767`，`zoom` 不变 |
| 普通横向 wheel | 平移 | `x: 115.032 -> -124.968`，`zoom` 不变 |
| `Command` + vertical wheel | 缩放 | `zoom: 0.302727 -> 0.217048`，平移围绕指针调整 |
| `Control` + vertical wheel | 缩放 | `zoom` 降到 `0.1`，命中当前最小 zoom |
| `V`/移动 + 空白左键拖动 | no-op | viewport 不变；拖动中无 visible selection rectangle；松开后无 selection |
| 默认模式 + 中键拖动 | 平移 | `x:+90, y:+50`，zoom 不变 |
| `Space` 按住 + 左键拖动 | 平移 | 按住期间工具 label 为 `抓手工具`、pane cursor 为 `grab`；松开恢复 `移动` |
| `H` + 左键拖动 | 平移 | 工具 label 为 `抓手工具`、pane cursor 为 `grab`；`x:+90,y:+50` |
| `V` + 空白左键拖动 | no-op | 工具 label 为 `移动`，pane 恢复选择 cursor，viewport 不变 |

## 5. Fit-view modifier resolution

先通过源站缩放菜单进入 `100%`，再分别测试：

| 输入 | Source result |
|---|---|
| plain `0` | 不执行 fit；仍约 `100%`，仅发生很小的浮点/动画收敛 |
| `Command+0` | 执行 fit；恢复约 `30%` |

因此当前 clone 保留 `Command/Ctrl+0` handler，并在操作指南中明确记录帮助面板与
缩放菜单的 source 文案差异。不能根据帮助面板的纯文本快照把 plain `0` 接成 fit。

## 6. Clone parity decision

代码核对前，clone 曾有三项高置信偏差：

1. 默认 `panOnScrollSpeed` 为 React Flow 默认值，`delta=240` 只移动约 `120px`；
2. `selectionOnDrag` 开启，`V` 下空白拖动会显示 clone-only selection rectangle；
3. `panOnDrag` 只允许当前 effective tool 的左键，默认选择模式不支持中键平移。

Batch 77 修正为：

```tsx
panOnScroll
panOnScrollSpeed={1}
zoomOnScroll
panOnDrag={effectivePan ? [0, 1] : [1]}
selectionOnDrag={false}
```

修正后的 clone 同一输入矩阵观测：

- 普通纵/横 wheel 分别改变 `y/x` 约 `-240`；
- `Command`/`Control` wheel 缩放；
- 默认中键拖动 `x:+90,y:+50`；
- `V` 空白左键拖动无 viewport/selection 变化；
- `Space`、`H` 左键拖动平移；
- `V`/`H` 的持久工具状态与源站 label 语义一致。

这是行为 parity 结论，不是 source-exact cursor bitmap、内部 React Flow 版本或
完整 source selection model 的结论。

## 7. Remaining boundary

- 本次没有用真实物理触摸板硬件；macOS 触摸板语义由 Chromium wheel/pinch 事件
  路径和源站帮助文案共同核对。用户操作步骤见 [`docs/CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md)。
- 本次没有拖动源站节点，因此不声明 source node-drag history/selection 细节。
- 源站快捷键面板的 `适应画布 0` 与运行时 `Command+0` 不一致，保留为 source
  UI 文案 drift，不用 clone-only 猜测覆盖。
- 源站默认选择 cursor 是内联 SVG data URI；本批只保证工具/手势行为，不把
  cursor bitmap 当作功能合同。

