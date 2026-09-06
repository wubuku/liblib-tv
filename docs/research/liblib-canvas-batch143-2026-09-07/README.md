# Batch 143：视频面板默认时长 6s→5s（源站对齐）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 142。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md)（16:9·720P·5s·1个 = 积分 135）。

视频生成面板默认时长从 6s 改为 5s（源站 09-06 采样：16:9·720P·5s·1个），
batch21 的时长 input/芯片断言随采样迁移。

## 完成定义

1. `verify-liblib-batch21.py`（时长迁移后）与 `verify-liblib-batch125.py` 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。
