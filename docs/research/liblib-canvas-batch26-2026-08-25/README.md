# Batch 26：智能续写两阶段工作流

> 状态：已完成；证据、计划、实现、专项截图、跨批回归和工程门禁均已落档。

## 批次前缺口

当前 clone 把 `智能续写` 当作 `片段重拍` 的一个分支：

- 点击后直接显示重拍 filmstrip 和完整 Prompt editor；
- 默认预选 `24-28s`；
- 用户在源视频节点上直接填写 Prompt；
- 不创建续写目标节点，也不创建 source-to-target edge。

当前线上 bundle 明确显示另一套两阶段流程：

1. 在源视频下方打开独立时间线，截取 `4-30s` 的前置视频；
2. 点击 `确认续写` 后，在源节点右侧创建新的续写视频生成节点并连接 edge；
3. 新节点使用 Seedance 2.5 / 全能参考，并显示续写来源与时间范围。

## 本批范围

- 从 `SegmentReshootPanel` 移除 clone-only 的续写分支；
- 新增 source-shaped `VideoContinuationSelector`；
- 支持起点、终点和整段区域拖动，约束为 `4-30s`；
- 确认后以单次图事务创建续写视频节点和连接边；
- 续写目标节点显示来源/range 前缀和专用 Prompt placeholder；
- 支持本地“退出续写模式”，保留节点并移除续写 edge/元数据；
- 补专项 Playwright、截图台账、跨批回归和工程门禁。

## 阅读顺序

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
2. [`PLAN.md`](PLAN.md)
3. [`VIDEO_CONTINUATION_WORKFLOW.spec.md`](VIDEO_CONTINUATION_WORKFLOW.spec.md)
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据入口

- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- [`../components/VideoProcessingToolbar.spec.md`](../components/VideoProcessingToolbar.spec.md)
- [`../components/SegmentReshootPanel.spec.md`](../components/SegmentReshootPanel.spec.md)
- [`../components/VideoContinuationSelector.spec.md`](../components/VideoContinuationSelector.spec.md)

## 原型边界

本批不裁剪或上传真实视频，不执行合规校验、Seedance 调用、积分扣除、任务轮询或跨会话保存。目标是忠实复刻当前原站可确认的画布拓扑、阶段切换、控件层级和本地交互合同。

## 结果摘要

- 独立 selector：`660x56`，`8 * zoom` node gap，`4-30s` range。
- graph handoff：确认后创建 empty video target 和 source-to-target edge。
- target Prompt：来源/range 前缀、专用 placeholder、固定 `2.5 / 全能参考`。
- clear：保留 target，移除 continuation metadata 和声明 edge。
- 专项验证：`scripts/verify-liblib-batch26.py`。
- 回归：Batch 9、21、23、25、26，`npm run check`，`npm run docs:check`。
- Git 保护点：`1b601d2`、`d598f2d`、`ecde7ea`。
