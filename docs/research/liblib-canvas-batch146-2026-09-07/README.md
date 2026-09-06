# Batch 146：运镜下拉菜单（12 项影视运镜预设）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 145。
>
> 依据：CLONE_DECISION——通用影视运镜术语（推/拉/摇/移/跟/升降/环绕/变焦/固定），源站交互未采样。

视频面板工具行「运镜」按钮从无行为芯片改为可展开下拉菜单：12 项运镜预设
（推镜/拉镜/左摇/右摇/上仰/下俯/跟拍/升降/环绕/推进/拉远/固定），选中后
显示 ✓ 标记，点击外部关闭。`CLONE_DECISION` 级别，源站交互细节待补采。

## 完成定义

1. `verify-liblib-batch146.py` 19 checks、`0/0/0` diagnostics 通过。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。
