# Batch 25：智能剪辑空态与节点下方 Prompt 面板

> 状态：计划已落档，待实施与验证。

## 批次前缺口

当前 `VideoClipNode` 把内部标题、四模式网格、参考、Prompt textarea 和 footer 全部塞进 `350x350` 节点本体。原站截图与 live DOM 显示：

- 节点本体是“未连接视频”的空态说明和四个尝试入口；
- 选中节点后，`+参考`、Prompt 和 footer 位于节点下方的独立 `660px` 面板；
- 面板和节点中心对齐、保持屏幕尺寸，并遵守已确认的 `16 * zoom` 下方间距。

## 本批范围

- 重构 `VideoClipNode` 为 source-shaped 空态；
- 新增独立 `VideoClipEditPanel`；
- 移除节点内部 clone-only 标题栏、模式网格、参考、Prompt 和 footer；
- 保留四个源站模式、空 Prompt disabled submit 和本地反馈；
- 验证 panel 锚定、zoom、drag、multi-selection 和移动端自然裁切。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`VIDEO_CLIP_EMPTY_WORKFLOW.spec.md`](VIDEO_CLIP_EMPTY_WORKFLOW.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [source selected video-clip screenshot](../../design-references/liblib-original-seedance-video-edit-node-2026-08-25.png)
- [`live-audit.json`](../liblib-seedance-2.5-2026-08-25/live-audit.json)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- 当前组件规格：[`../components/VideoClipNode.spec.md`](../components/VideoClipNode.spec.md)

## 原型边界

本批不实现真实视频连接解析、智能剪辑、素材上传、生成任务、积分、账户资产或持久化。四模式和提交只改变本地 UI 状态。
