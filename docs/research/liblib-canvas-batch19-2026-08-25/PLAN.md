# Batch 19 计划：缩略图锚点与视觉校准

## 1. 缺口与价值

| 缺口 | 当前 clone | 原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 锚点错误 | React Flow 默认右下角 | minimap 位于底部工具条缩略图按钮上方 | 5 | 修复 |
| 几何不稳定 | inline `150x110`，其余使用组件默认 margin/position | 截图约 `150x110`，与工具条相距约 `2px` | 4 | 建立 CSS 合同 |
| 视觉粗略 | `#202020`、默认 viewport stroke | 深灰面板、灰色节点块、清晰 viewport outline | 4 | 校准 |
| 抽屉联动未验证 | minimap 与 asset drawer 没有专项合同 | 工具条会随 canvas 区域右移 | 4 | 验证相对锚点 |
| 移动端可能遮挡双工具条 | 默认 bottom-right 容易与底栏冲突 | 无 minimap 打开态移动端源站截图 | 3 | clone-only 避让 |
| minimap 内交互未知 | React Flow 支持 pannable/zoomable | 当前截图只证明可见状态 | 2 | 不扩展 |

## 2. 实施步骤

1. 为 React Flow `MiniMap` 增加稳定 `liblib-minimap` class 和 source-shaped visual props。
2. 使用 `bottom-left` panel，并通过全局 CSS：
   - desktop：`left: 152px`、`bottom: 54px`；
   - 390px：保持水平可见，并抬高到双工具条上方。
3. 设置 `150x110px`、约 `10px` 圆角、深灰背景、低对比节点块和浅灰 viewport outline。
4. 保留 `showMinimap` 开关，不启用 `pannable`、`zoomable` 或点击跳转。
5. 新增 Batch 19 Playwright：
   - 初始隐藏；
   - trigger pressed 状态；
   - desktop 几何和样式；
   - asset drawer 后与 canvas/trigger 同步右移；
   - 390px 无溢出且不覆盖底部工具条；
   - 再次点击隐藏；
   - console/page error。
6. 更新行为、组件清单、Harness、Big Picture 和 CHANGELOG。

## 3. 事实边界

### Source fact

- 原站截图 viewport 为 `929x874`，当前 zoom 文案为 `28%`。
- minimap 可见框约为 `x=151, y=711, w=151, h=109`。
- minimap 位于底部画布工具条正上方，靠近“缩略图”触发按钮。
- 面板为深灰圆角矩形；内部只显示灰色节点块和浅灰 viewport outline，不显示边或文字。

### Inference

- minimap 是相对底部画布工具条按钮定位的局部画布控件，而不是右下角全局 dock。
- 资产抽屉打开后，minimap 应与 React Flow canvas 区域和底部工具条一起右移。

### Clone-only decision

- 390px 视口把 minimap 抬高到两条底部工具条上方。
- 不启用 React Flow 的 minimap pan/zoom/click 能力，直到取得原站交互证据。

## 4. 验收标准

- `929x874` 下 minimap 为 `150x110px`，左边约 `152px`，底部约 `54px`。
- minimap 水平中心与缩略图按钮中心误差不超过 `12px`。
- viewport outline、节点块、背景和圆角与保存的原站截图同一视觉层级。
- 打开资产抽屉后，minimap 与触发按钮都右移约 `240px`，相对中心误差保持稳定。
- `390x844` 下 minimap 不覆盖两条底部工具条，不产生页面级横向溢出。
- toggle、console、Batch 18 zoom menu 和 Batch 17 asset drawer 不回归。

