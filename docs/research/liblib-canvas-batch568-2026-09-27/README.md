# Batch 568 — 时间线当前时间可编辑输入

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 552/567
> （截图 48/55）——时间线左控制簇时间为**可编辑带边框输入**（0.00）与
> 时长输入（10.00 s）；clone 此前为只读文本。

## 合同

- 当前时间改为 input（`data-director-timeline-time` 保留）：输入秒数 +
  Enter → `setTimelineTime` seek，钳制 [0, duration]；
- key 绑定 currentTime（播放/seek 时显示同步）；
- 时长保持只读 label（`data-director-timeline-duration`）；
- 非法值（NaN）忽略。

## 内容

- `src/components/director/DirectorTimeline.tsx`（时间 input + duration
  label 拆分；重复 setTimelineTime 选择器清理）；
- `scripts/verify-liblib-batch568.py`（6 检查：seek、超界/负值钳制、
  时长 label）；
- 回归：batch 553/556/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
