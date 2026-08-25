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
- minimap 位于“缩略图”按钮上方，不在画布右下角；两者左边缘近似对齐。
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

- minimap 的水平锚点来自底部画布工具条中的缩略图按钮左边缘。
- minimap 属于画布局部控件，因此资产抽屉改变 canvas 起点时应随 canvas 区域移动。

### Unknown

- 截图不能证明 minimap 是否支持拖动 viewport、滚轮缩放或点击跳转。
- 没有保存原站 minimap 的 hover、关闭动画、资产抽屉同时打开或移动端打开状态。
- 没有从原站 DOM 提取 minimap 的精确色值和 box shadow。

### Re-inspection rule

除非需要确认 minimap 内部交互、移动端状态或精确 DOM 样式，不再重新打开此截图。后续先读本文件。

## 2. Clone verification

### 文件

- `docs/design-references/liblib-clone-batch19-minimap-desktop-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch19-minimap-asset-drawer-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch19-minimap-mobile-390-2026-08-25.png`
- 识图方式：三图合并为一次性临时 contact sheet 后统一检查

### Desktop `929x874`, fit-view `28%`

- 完整画布构图与原站证据图处于相同 zoom 状态。
- minimap 实测为 `x=152, y=710, w=150, h=110`。
- minimap 底边为 `y=820`，底部画布工具条顶边约为 `y=822`，保留约 `2px` 间距。
- minimap 左边缘与 active 缩略图按钮左边缘误差小于 `12px`。
- 深灰面板、灰色节点块和浅灰 viewport outline 均清晰；没有渲染节点文字、缩略图或边。
- fit-view 后 viewport outline 更新，说明 minimap 仍由 React Flow 当前 viewport 驱动。

### Asset drawer `929x874`

- 240px asset drawer 打开后，minimap 从 `x=152` 移到 `x=392`。
- 缩略图 trigger 同步右移 `240px`，两者左边缘相对误差保持不变。
- minimap 位于收缩后的 React Flow canvas 内，没有被 drawer 裁切或覆盖。

### Mobile `390x844`

- minimap 实测为 `x=128, y=627, w=150, h=110`。
- minimap 底边 `y=737`，中央主工具条顶边 `y=743`，保留 `6px` 间距。
- 两条底部工具条都可见、可点击；页面无横向溢出。
- minimap 会覆盖其下方的画布内容。这是局部浮层的自然结果，不是控件重叠。

### Visual conclusion

clone 已消除右下角错误定位，并在与原站可比的 `28%` 状态下呈现相同的局部层级：按钮上方深灰 minimap、低对比节点块和明确 viewport outline。移动端位置属于本批 clone-only 避让决策，不声称为原站实测。
