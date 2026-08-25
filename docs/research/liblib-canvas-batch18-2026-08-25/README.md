# Batch 18：缩放菜单结构与生命周期

> 日期：2026-08-25
> 范围：LibTV clone 底部画布工具条的缩放百分比入口和菜单。
> 目标：按原站截图修正菜单结构，并让它参与统一 overlay 关闭生命周期。

## 当前缺口

- 菜单顶部错误渲染 `缩小 / 百分比 / 放大` 三段控制；原站顶部是单行当前百分比。
- clone 在菜单底部增加 `点阵网格`，保存的原站缩放菜单没有该项。
- `isZoomOpen` 是 `BottomToolbar` 局部 state：
  - `Escape` 不一定关闭；
  - 打开资产、画布菜单或其他一级 overlay 时可残留；
  - `closeAllPanels` 无法清理。
- `BottomToolbar.spec.md` 仍写“54% zoom No-op”，与运行态明显冲突。

## 证据入口

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站缩放菜单的一次性识图。
- [`ZOOM_MENU.spec.md`](ZOOM_MENU.spec.md)：结构、命令和生命周期合同。
- [`../../design-references/liblib-original-zoom-menu-2026-08-25.png`](../../design-references/liblib-original-zoom-menu-2026-08-25.png)：原站证据。
- [`../liblib-canvas-batch9-2026-08-25/`](../liblib-canvas-batch9-2026-08-25/)：zoom 后节点浮层锚定回归。

## 边界

- 缩放命令继续调用页面已有 `onZoomBy`、`onZoomTo`、`onFitView`。
- viewport 不进入 graph undo/redo history。
- `showGrid` store 能力保留，但不继续伪装为原站缩放菜单项。
- 不重写 React Flow wheel/pinch 行为。

## 导航

- [`PLAN.md`](PLAN.md)
- [`ZOOM_MENU.spec.md`](ZOOM_MENU.spec.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
