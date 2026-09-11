# Batch 371 — 文档新鲜度巡检：HARNESS/DEVELOPMENT/ARCHITECTURE（`DOC_RECORDED`）

> 状态：三文档新鲜度巡检完成——**无过期现状陈述**，无需修改。
> 源站恢复重测：`RECOVERY: still-broken` 维持。

## 巡检结论

| 文档 | 检查项 | 结果 |
|---|---|---|
| HARNESS.md | 面板宽/积分超市/关键元素/marquee 旧值 | 命中均为**历史批次台账行**（按时间记录当时所为），非现状断言——保留 |
| DEVELOPMENT.md | 面板/宽度/storyboard/uiStore 旧值 | 无命中；状态归属指引（canvasStore/uiStore/本地）仍准确 |
| ARCHITECTURE.md | 同上 | `activePrimaryPanel` 互斥、store 职责表、节点锚定策略均为现行描述 |

## 源站状态

`RECOVERY: still-broken` 维持（PAR-005 §10 + 复测脚本
`scripts/probe-source-recovery.py` 在案）。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng 后续 batch 对照巡检；
- 相机预设语义产品裁决跟进。
