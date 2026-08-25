# Batch 21：Seedance 视频参数 Dialog

> 状态：已实施；专项 Playwright、Batch 9-21 跨批回归和完整工程门禁均通过。

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
- [clone normal](../../design-references/liblib-clone-batch21-video-params-normal-929-2026-08-25.png)
- [clone long](../../design-references/liblib-clone-batch21-video-params-long-929-2026-08-25.png)
- [clone mobile](../../design-references/liblib-clone-batch21-video-params-mobile-390-2026-08-25.png)
- [clone contact sheet](../../design-references/liblib-clone-batch21-video-params-contact-sheet-2026-08-25.png)
- 可执行验证：[`scripts/verify-liblib-batch21.py`](../../../scripts/verify-liblib-batch21.py)

## 完成结果

- normal dialog 从约 `341x299` 修正为 `341x445`。
- long dialog 从约 `341x267` 修正为 `341x397`。
- 相对 generation panel 的位置分别校准到约 `+82/-211.7` 和 `+90/-163.7`。
- ratio cards、resolution、duration value/slider、audio/count 与 long helper 形成可操作闭环。
- 模式 disabled 状态和 `300s / 14700` 本地反馈继续受自动化保护。
- 模型菜单完整清单仍未纳入本批，不把截图可见部分误写成完整原站模型库。
