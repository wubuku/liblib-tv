# Batch 126：高级设置内联行（视频面板）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 125。
>
> 源站证据：[`../liblib-video-panel-2026-09-06/README.md`](../liblib-video-panel-2026-09-06/README.md)（高级设置/联网搜索/自动校验素材/智能引用 AutoLink 内联可见）。

视频面板底部的 齿轮+弹出菜单 改为源站同构的内联行：`高级设置` 标签 +
三个 compact 开关芯片（联网搜索/自动校验素材/智能引用 AutoLink）。开关状态
与生成流程保留（batch21/22 的 AdvancedMenu 流程不变——菜单组件仍被
引用处使用？本批将 popup 移除，batch21/22 未断言齿轮，复归通过）。

## 完成定义

1. `verify-liblib-batch126.py` 8 checks、`0/0/0` diagnostics 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

模型菜单内容（2.0 展开态）仍为 `SOURCE_UNKNOWN`，待补采样。
