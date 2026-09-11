# Batch 366 — PAR-011 面板互斥矩阵研究（`RESEARCH_RECORDED`）

> 状态：只读代码考古完成，互斥矩阵写入 parity backlog
> §4.10b。无 src 变更（DEC-015 合规）。源站恢复重测：
> `RECOVERY: still-broken` 维持。

## 结论摘要

- 主面板（toolbox/material/character/history/tutorial）经单一
  `activePrimaryPanel` 天然互斥——无冗余布尔；
- 独立覆盖层（add-node/dropdown/asset/share/agent/notification/
  user-menu/zoom/shortcuts）为独立布尔维度，部分共存属设计；
- `closeAllPanels` + `OverlayState` Pick + `closedOverlayState`
  常量提供整体确定性重置；
- 死状态扫描（batch 360）：57 字段全部被引用。

**PAR-011 定案**：uiStore 部分**无清理对象**（现状即最简形态）；
剩余 deferred 仅组件级 unmounted state 审计（另行排队）。

## 验收

- docs check 通过（924 Markdown）；无 src 变更。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 组件级 unmounted state 审计（PAR-011 残余，低优先）；
- jimeng 后续 batch 对照巡检。
