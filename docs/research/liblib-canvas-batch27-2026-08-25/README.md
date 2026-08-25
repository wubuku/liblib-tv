# Batch 27：智能去字幕两模式工作流

> 状态：已完成；证据、计划、实现、专项截图、跨批回归和工程门禁均已落档。

## 批次前缺口

当前 clone 的 `智能去字幕` 只有顶部下拉菜单。点击 `智能去字幕` 或 `框选去字幕` 后：

- 只在顶部工具条右侧留下临时文字；
- 不打开源站的节点下方紧凑生成条；
- 不在视频画面上建立区域框选 session；
- 不创建右侧去字幕目标视频和 source-to-target edge。

当前线上 bundle 已提供完整的两模式合同：

1. `智能去字幕` 直接打开紧凑生成条；
2. `框选去字幕` 同时打开生成条与视频内区域编辑层；
3. 区域模式支持多框、选择、移动、缩放、删除、undo、redo 和 reset；
4. 确认后创建 `视频一键去字幕-{nodeLabel}` pending 视频节点并连接 edge。

## 本批范围

- 将顶部去字幕入口从临时反馈接入真实工作流状态；
- 新增 source-shaped `SubtitleErasePanel`；
- 新增视频画面内多区域编辑层；
- 用单次图事务创建 pending 去字幕视频和连接边；
- 区分 smart / region 的目标节点提示；
- 补专项 Playwright、截图台账、跨批回归和工程门禁。

## 阅读顺序

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
2. [`PLAN.md`](PLAN.md)
3. [`SUBTITLE_ERASE_WORKFLOW.spec.md`](SUBTITLE_ERASE_WORKFLOW.spec.md)
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 组件规格

- [`../components/SubtitleErasePanel.spec.md`](../components/SubtitleErasePanel.spec.md)
- [`../components/VideoProcessingToolbar.spec.md`](../components/VideoProcessingToolbar.spec.md)
- [`../components/VideoNode.spec.md`](../components/VideoNode.spec.md)

## 原型边界

本批不识别真实字幕，不擦除视频像素，不计算真实积分，不上传媒体，不提交模型任务，也不轮询生成结果。目标是忠实复刻可确认的画布入口、区域编辑、下方控制条、图事务与 pending 状态。

## 结果摘要

- 两模式入口：`智能去字幕` / `框选去字幕`。
- 紧凑 panel：`48px` 高、node-relative inverse-scale anchor。
- region editor：多框、选择、移动、四角 resize、undo、redo、reset。
- graph handoff：pending target、source edge 和 metadata 单事务创建。
- 专项验证：`scripts/verify-liblib-batch27.py`。
- 回归：Batch 9、21、23、25、26、27，`npm run check`，`npm run docs:check`。
- Git 保护点：`281f6e8`、`c2fdd9a`、`445e703`。
