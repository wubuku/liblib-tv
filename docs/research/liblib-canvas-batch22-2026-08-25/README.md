# Batch 22：Seedance Source-visible 模型菜单

> 状态：原站模型菜单已完成聚焦截图审计与像素边界测量；计划和规格已落档。

## 当前缺口

当前 clone 的模型菜单约为 `330x216`，只有四项，所有行都显示说明，并包含原站截图中未出现的 `Kling O3`。原站截图可见的菜单约为 `380x410`，包含七个模型；非选中行紧凑，只有选中行展开说明。

## 本批范围

- 使用原站截图可见的七个模型替换当前四项；
- 移除没有本批原站证据的 `Kling O3`；
- 对齐约 `380x410` 的 menu geometry 和 generation panel 左边缘；
- 实现“选中行展开说明、其他行紧凑”的信息层级；
- 保留模型选择为本地前端 state，不声称模型可真实调用；
- 不声称七项是完整模型库。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`VIDEO_MODEL_MENU.spec.md`](VIDEO_MODEL_MENU.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [source model menu](../../design-references/liblib-original-seedance-model-menu-2026-08-25.png)
- [`live-audit.json`](../liblib-seedance-2.5-2026-08-25/live-audit.json)
- Batch 21 菜单上下文：[`../liblib-canvas-batch21-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch21-2026-08-25/SCREENSHOT_ANALYSIS.md)

