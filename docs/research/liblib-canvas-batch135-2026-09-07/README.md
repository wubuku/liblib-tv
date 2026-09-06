# Batch 135：视频面板积分比例因子落地

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-07。
>
> 上一批 checkpoint：Batch 133。

依据 Batch 130 采得的两个积分数据点（16:9·720P·5s·1个=135、
Auto·720P·5s·1个=230），将普通分支积分公式从 `时长×46×数量` 修正为
`时长×数量×比例因子`（16:9→27/s，Auto→46/s；其余比例未采样，沿用 46/s）。
超长视频分支（49/s）无采样漂移，保持不变；batch21 的 5520（21:9 态）与
14700（超长态）断言不受影响并复跑通过。

## 完成定义

1. `verify-liblib-batch125/128.py` 复跑通过（积分随联动更新）。
2. `npm run check`、`npm run docs:check` 通过。
3. master commit/push。

公式仅校准两个采样点；其余比例/分辨率/模型的定价为 `SOURCE_UNKNOWN`。
