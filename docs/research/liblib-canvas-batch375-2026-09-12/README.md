# Batch 375 — PAR-005 状态挂钩（`DOC_RECORDED`）

> 状态：PAR-005 状态行更新为 `PARTIAL_RECORDED`（Batch 359/366 的
> 2026-09-12 劣化观察 + 复测脚本入库已挂接）；§4.6 新增指向
> freshness §10 的链接。无 src 变更。源站恢复重测：
> `RECOVERY: still-broken` 维持。

## 内容

- priority queue 中 PAR-005 行：状态注记补全（劣化观察 §10、
  复测脚本 `scripts/probe-source-recovery.py` 在库）；
- §4.6 段新增指向 freshness §10 的链接与 §8 补采流程指引。

## 验收

- docs check 通过（932 Markdown）；无代码变更。

## 后续候选

- liblib.tv 恢复重测 → BLOCKED_SOURCE 三项补采与 CLONE_DECISION
  替换（恢复即按 §8 checklist 执行）；
- jimeng 后续 batch 对照巡检（随其节奏）。
