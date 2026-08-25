# Batch 27 Screenshot Analysis

## 1. Source Visual Reuse

本批规划阶段没有重复识别原站整图。

复用事实：

- [`../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md) 已记录 ready video 顶部工具条存在 `智能去字幕`；
- Batch 9 已记录 video top/bottom overlay 的 node-relative anchor；
- Batch 26 已记录当前 clone ready video、顶部工具条和 compact lower workflow 的视觉上下文。

本批新增 panel 与 region geometry 直接来自线上 bundle：

- panel `absolute -bottom-4`、`w-max`、`px-2 py-2`；
- close `32x32`、region tools `32x32`、submit `28x28`；
- region border `#0690ae`、fill `rgba(7, 184, 221, 0.15)`；
- 选中 region 的 edge/corner resize layer。

## 2. Clone Screenshot Ledger

专项脚本已生成：

| File | Viewport / state |
|---|---|
| [`liblib-clone-batch27-subtitle-smart-929-2026-08-25.png`](../../design-references/liblib-clone-batch27-subtitle-smart-929-2026-08-25.png) | smart compact panel |
| [`liblib-clone-batch27-subtitle-region-929-2026-08-25.png`](../../design-references/liblib-clone-batch27-subtitle-region-929-2026-08-25.png) | two regions, one selected |
| [`liblib-clone-batch27-subtitle-target-929-2026-08-25.png`](../../design-references/liblib-clone-batch27-subtitle-target-929-2026-08-25.png) | pending target + edge |
| [`liblib-clone-batch27-subtitle-mobile-390-2026-08-25.png`](../../design-references/liblib-clone-batch27-subtitle-mobile-390-2026-08-25.png) | natural clipping |
| [`liblib-clone-batch27-subtitle-contact-sheet-2026-08-25.png`](../../design-references/liblib-clone-batch27-subtitle-contact-sheet-2026-08-25.png) | four-state ledger |

## 3. One-Pass Visual Analysis

识别时间：2026-08-25。只检查了 contact sheet 一次；下面结论是本批后续复用的视觉记录。

### Smart compact panel

- **截图事实**：ready video 保持蓝绿色选中边框，上方标题和尺寸信息不被遮挡。
- **截图事实**：`智能去字幕` 下方面板水平居中于节点，和视频底边之间留有清晰间距，没有漂移到节点内部或工具条区域。
- **截图事实**：面板是单行紧凑结构；close、分隔线、模式名、积分占位和白色 submit 从左到右排列，所有文字和图标完整可见。
- **DOM / Playwright 支撑**：面板高 `48px`，close 为 `32x32`，submit 为 `28x28`，节点间距为 `16 * zoom`。

### Region overlay and panel

- **截图事实**：两个蓝绿色半透明矩形都限制在视频画面内；右上矩形为选中态，四角 resize handle 清晰可见。
- **截图事实**：下方面板仍以节点中心为锚点；region 工具组比 smart 更宽，但没有与节点 handle、底部播放控制或全局底栏重叠。
- **截图事实**：help 浮层位于下方面板上方，覆盖视频下部而不遮挡 panel controls；深色背景与三条说明文案均可读。
- **截图事实**：overlay、视频原生播放控件、节点连接 handle、help 和 panel 的层级关系稳定，没有互相截断。
- **DOM / Playwright 支撑**：进入 region 后节点被聚焦到 `zoom >= 1`；矩形使用画面相对坐标，选中、移动和四角 resize 已由专项断言覆盖。

### Pending target graph

- **截图事实**：source 与 pending target 水平排布，连接边从 source 右侧 handle 到 target 左侧 handle，未穿过两节点正文。
- **截图事实**：target 保持蓝绿色选中边框，标题、尺寸和 `框选区域生成去字幕视频` 空态文案完整可见。
- **截图事实**：fit-view 后两个节点、连接边和底部全局工具栏都在视口内，没有遮挡。
- **DOM / Playwright 支撑**：target 与 source 的逻辑间距为节点宽度加 `120 * zoom`，目标节点、edge 和 metadata 在一个 graph transaction 中创建。

### Mobile natural clipping

- **截图事实**：`390x844` 下仍使用桌面尺寸的视频节点，节点左右自然超出视口；画面中心、help 文案和 region panel 的主要 controls 可见。
- **截图事实**：region panel 也按节点中心定位并被视口自然裁切，而不是脱离节点后挤压成多行。
- **截图事实**：底部全局工具栏保持独立、完整且不被节点 overlay 覆盖。
- **DOM / Playwright 支撑**：`documentElement` 和 `body` 均无页面级横向 overflow；裁切发生在画布视口内部。

### Review result

- 未发现 Batch 9 所指出的上下浮层乱位回归。
- 未发现文字、按钮、节点 handle 或全局工具栏之间的不合理重叠。
- 移动端保留的是已记录的 source-like natural clipping；这不是自适应缩小方案，也不应在无新增原站证据时“优化”。

## 4. Re-inspection Rule

contact sheet 已完成一次性识别。后续除非截图或实现变化，不重复识别整图；只检查缺失的最小 crop/state。
