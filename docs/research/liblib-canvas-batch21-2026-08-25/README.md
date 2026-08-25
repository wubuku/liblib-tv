# Batch 21：Seedance 视频参数 Dialog

> 状态：原站结构化证据与四状态截图已审计；计划和组件合同已落档，实施待开始。

## 当前缺口

当前 clone 的普通参数菜单约为 `341x299`，超长参数约为 `341x267`，使用紧凑文本 pill 表达比例、清晰度、音频和数量。原站 DOM 与截图显示它们分别是 `341x445` 和 `341x397` 的高 dialog，包含带比例图标的卡片、整宽 segmented controls、带数值框的时长 slider，以及超长视频时长说明。

这不是细微样式差异：参数 dialog 是 Seedance 生成工作流的核心状态，当前 clone 在密度、层级和空间位置上都明显失真。

## 本批范围

- 对齐普通参数 dialog 的尺寸、相对 panel 位置和控件层级；
- 对齐超长参数 dialog 的尺寸、说明文案和无数量控件状态；
- 保留已有参数集合、`4-30s` / `30-300s` 范围和 `300s = 14700` 本地积分逻辑；
- 增加稳定 selectors 和 Batch 21 Playwright；
- 不扩写未获得精确 DOM 的模型菜单，也不改变 ready-video 工具条。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`VIDEO_PARAMETER_DIALOG.spec.md`](VIDEO_PARAMETER_DIALOG.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [`live-audit.json`](../liblib-seedance-2.5-2026-08-25/live-audit.json)
- [normal params](../../design-references/liblib-original-seedance-params-menu-2026-08-25.png)
- [long params](../../design-references/liblib-original-seedance-long-params-2026-08-25.png)
- [mode menu](../../design-references/liblib-original-seedance-mode-menu-2026-08-25.png)
- [model menu](../../design-references/liblib-original-seedance-model-menu-2026-08-25.png)

