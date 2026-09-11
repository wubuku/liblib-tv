# Batch 379 — 心跳验证（`HEARTBEAT_RECORDED`）

> 状态：恢复重测 `RECOVERY: still-broken` 维持（第 6 次）；关键
> 验证器族抽样全绿。无代码变更。

## 抽样验证（本批全绿）

39（346 轮询修复）/ 40（347 duration hack）/ 46（349 命名迁移）/
57（355 TextNode 把手 id 产品修复）/ 6（362 Shift 框选语义）/
44（361 纯拼接语义迁移）/ jimeng batch 1——**历史修复项持续稳定**。

## 源站状态

`RECOVERY: still-broken` 维持（PAR-005 §10 在案，复测脚本
`scripts/probe-source-recovery.py` 在库）。BLOCKED_SOURCE 三项与
CLONE_DECISION 替换继续等待。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng 后续 batch 对照巡检（随其节奏）；
- 相机运动预设 append 语义的产品裁决跟进（DEC-048）。
