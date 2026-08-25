# Batch 22：Seedance Source-visible 模型菜单

> 状态：已实施；专项 Playwright、Batch 9-22 跨批回归和完整工程门禁均通过。

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
- [clone default 2.5](../../design-references/liblib-clone-batch22-model-menu-default-929-2026-08-25.png)
- [clone selected Fast](../../design-references/liblib-clone-batch22-model-menu-fast-929-2026-08-25.png)
- [clone mobile](../../design-references/liblib-clone-batch22-model-menu-mobile-390-2026-08-25.png)
- [clone contact sheet](../../design-references/liblib-clone-batch22-model-menu-contact-sheet-2026-08-25.png)
- 可执行验证：[`scripts/verify-liblib-batch22.py`](../../../scripts/verify-liblib-batch22.py)

## 完成结果

- menu 从约 `330x216` 修正为 `380x410`，相对 generation panel 为 `left 0/top -176.7`。
- source-visible 集合从四项修正为七项，并移除无本批证据的 `Kling O3`。
- 前五项 premium 与所有 estimate 形成稳定行列；仅 selected row 展开已确认 description。
- 2.5 与 Fast 两个已确认 selected state、参数 dialog handoff 和 390px viewport fit 均受自动化保护。
- 模型 tile 仍是近似 icon，七项不被描述为完整或真实可调用模型库。
