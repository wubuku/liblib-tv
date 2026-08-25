# Batch 28：音视频分离多输出工作流

> 状态：已完成。当前 bundle 证据、核心实现、专项 Playwright、跨批回归、工程门禁与最终索引均已落档。

## 批次前缺口

当前 clone 的 ready-video 工具条包含一个 `音频分离` dropdown：

- 菜单只有 `人声提取`、`背景音提取`、`音效提取`；
- 三项都只在顶部工具条写入临时文字；
- 不显示 source busy state；
- 不创建音频节点、无声视频节点或连接边；
- `音效提取` 在当前线上 feature flag 中实际不可见，属于旧 clone 的脑补。

2026-08-25 当前线上 bundle 支持的可见菜单为：

1. `音视频分离`；
2. `人声提取`；
3. `背景音提取`。

成功结果可包含独立音频节点和无声视频节点。两个结果都从 source video 连出；无声视频按 audio 结果右侧继续放置，最终选择最右侧结果。

## 本批范围

- 对齐当前三项菜单，移除未开放的音效入口；
- 复刻 `分离中` toolbar busy state；
- 新增 source-backed audio/silent-video graph transaction；
- 区分音轨、人声、背景音命名和 metadata；
- 让 graph create 成为一次 undo/redo；
- 补专项 Playwright、截图台账、跨批回归和工程门禁。

## 阅读顺序

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
2. [`PLAN.md`](PLAN.md)
3. [`AUDIO_SPLIT_WORKFLOW.spec.md`](AUDIO_SPLIT_WORKFLOW.spec.md)
4. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 组件规格

- [`../components/AudioNode.spec.md`](../components/AudioNode.spec.md)
- [`../components/VideoProcessingToolbar.spec.md`](../components/VideoProcessingToolbar.spec.md)
- [`../components/VideoNode.spec.md`](../components/VideoNode.spec.md)

## 原型边界

本批不下载或解码真实视频，不提取音轨，不调用人声分离服务，不上传输出，也不轮询任务。clone 只复刻当前可确认的菜单、busy feedback、结果节点类型、命名、拓扑、选择和 history 合同。
