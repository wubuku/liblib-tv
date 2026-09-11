# Batch 372 — 恢复重测与复测日志表（`CONFIRMATION_RECORDED`）

> 状态：源站恢复重测 `RECOVERY: still-broken` 维持；freshness §10
> 新增复测运行日志表（5 次重测的时间线台账）。无代码变更。

## 本批内容

- 运行 `scripts/probe-source-recovery.py`：`still-broken` 维持
  （第 5 次重测）；
- freshness §10 新增 **10.2b 复测运行日志表**：记录 2026-09-11 至
  09-12 的五次重测（挂接批次、结果、备注），后续重测按行追加，
  为恢复时机的判定提供完整时间线。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng 后续 batch 对照巡检（随其节奏）；
- 相机运动预设 append 语义的产品裁决跟进。
