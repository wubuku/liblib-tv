# Batch 388 — jimeng 截取帧下拉对照（`REVIEW_RECORDED`）

> 状态：jimeng 截取帧下拉对照完成——**已实现且与源站 1:1 一致**
> （并行路线自行覆盖，无需干预）。liblib.tv 恢复重测：
> `RECOVERY: still-broken` 维持（第 10 次重测）。无代码变更。

## 对照（源站 2026-09-12 截图 vs clone JimengNodeToolbar）

- 源站截取帧下拉（截取帧按钮下方）：三项——**首帧 / 尾帧 / 自定义**
  （带图标）；
- clone：`JimengNodeToolbar` 截取帧 dropdown menu = ["首帧", "尾帧",
  "自定义"]，锚在按钮下方居中（SOURCE_FACT 注释在案）；
- 自定义延伸：batch 9 `JimengFramePicker` 胶片帧条 + 播放头 +
  确认（未截取禁用）——覆盖「自定义」分支的交互深化。

## 源站状态

liblib.tv：`RECOVERY: still-broken` 维持（第 10 次重测；
probe-source-recovery.py 在库，复测日志 §10.2b 随批次追加）。

## 后续候选

- liblib.tv 恢复重测 → BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng batch 9+ 对照巡检（随并行路线节奏）；
- 相机运动预设 append 语义的产品裁决跟进（DEC-048）。
