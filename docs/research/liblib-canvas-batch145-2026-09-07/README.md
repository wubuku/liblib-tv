# Batch 145：视频面板默认状态对齐（时长/模式标签）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 144。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md)（16:9·720P·5s·1个 = 135，模式触发器 文生视频）。

默认时长 6s→5s；默认模式触发器显示 全能参考→文生视频。模型触发器保持
2.5（源站触发器显示 2.0 的完整选中态待菜单补采）。batch21/22 时长与几何
断言随采样迁移。

## 完成定义

1. `verify-liblib-batch21/22/125.py` 复跑通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。
