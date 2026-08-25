# Batch 19 Screenshot Analysis

## 1. 原站 minimap

### 文件

- 路径：`docs/design-references/liblib-original-minimap-2026-08-25.png`
- 来源：LibTV 登录态画布
- 采样日期：2026-08-25
- 文件尺寸：`929x874`
- 交互状态：工作台、完整画布构图、zoom 文案 `28%`、minimap 打开
- 识图次数：1

### Source fact

- minimap 外框约为：
  - `x=151`
  - `y=711`
  - `width=151`
  - `height=109`
- 底部画布工具条顶边约为 `y=822`，minimap 与工具条之间约 `2px`。
- minimap 位于“缩略图”按钮上方，不在画布右下角。
- 外层为深灰圆角矩形，圆角视觉约 `10px`。
- 内部节点表现为 7 个以上的中灰矩形块；没有节点标题、缩略图、边或文字。
- 当前 viewport 以浅灰矩形 outline 表示；outline 内部仍能看到深色画布。
- minimap trigger 处于 active 背景状态。
- minimap 覆盖在画布节点之上，但没有覆盖中央主工具条。

### Geometry estimate

| Item | Estimate |
|---|---:|
| minimap | `151x109px` |
| left | `151px` |
| bottom | `54px` |
| toolbar gap | `2px` |
| radius | `~10px` |
| node color | `~#626262` |
| panel background | `~#262626` |
| viewport outline | `~#747474` |

颜色为截图视觉估计，不是 DOM computed style。

### Inference

- minimap 的水平锚点来自底部画布工具条中的缩略图按钮。
- minimap 属于画布局部控件，因此资产抽屉改变 canvas 起点时应随 canvas 区域移动。

### Unknown

- 截图不能证明 minimap 是否支持拖动 viewport、滚轮缩放或点击跳转。
- 没有保存原站 minimap 的 hover、关闭动画、资产抽屉同时打开或移动端打开状态。
- 没有从原站 DOM 提取 minimap 的精确色值和 box shadow。

### Re-inspection rule

除非需要确认 minimap 内部交互、移动端状态或精确 DOM 样式，不再重新打开此截图。后续先读本文件。

