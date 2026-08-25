# Batch 19：缩略图锚点与视觉校准

> 状态：已完成原站证据审计与实施计划，代码和验证结果见本目录后续记录。

## 当前缺口

原站截图中的 minimap 是底部画布工具条“缩略图”按钮的上方浮层。当前 clone 使用 React Flow 默认 `bottom-right`，因此在位置、与触发按钮的关系和视觉层级上都不忠实。

## 本批范围

- 把 minimap 从右下角移到缩略图按钮上方；
- 校准 `150x110px` 尺寸、背景、圆角、节点块和 viewport outline；
- 保留现有显隐开关；
- 处理资产抽屉和 390px 视口下的相对位置与页面溢出；
- 不增加没有原站直接证据的 minimap 内点击、拖拽或滚轮缩放。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)：缺口排序、范围和验收标准。
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站截图的一次性识图记录。
3. [`MINIMAP.spec.md`](MINIMAP.spec.md)：组件和几何合同。
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施与验证结果。

## 证据

- 原站截图：[liblib-original-minimap-2026-08-25.png](../../design-references/liblib-original-minimap-2026-08-25.png)
- 当前原站总体审计：[liblib-live-2026-08-25](../liblib-live-2026-08-25/README.md)

