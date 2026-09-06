# Batch 128：尝试芯片驱动设置联动

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 127。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md) 联动采样补充。

尝试芯片选择联动设置：`5分钟超长视频` → `Auto · 720P · 300s · 1个`；
`首尾帧生成视频` → `Auto · 720P · 5s · 1个`。取消选择保持当前设置
（源站取消联动未采样，CLONE_DECISION）。

## 完成定义

1. `verify-liblib-batch128.py` 5 checks、`0/0/0` diagnostics 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

300s 超出 clone 参数菜单时长上限（30s）为已记录近似；源站参数菜单
在尝试模式下的展开态未采样。
