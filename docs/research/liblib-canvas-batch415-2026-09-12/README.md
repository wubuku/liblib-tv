# Batch 415 — 恢复重测心跳（`CONFIRMATION_RECORDED`）

> 状态：liblib.tv 恢复重测 `RECOVERY: still-broken` 维持（第二十三
> 次探测）；jimeng 路线无新 batch 提交（batch 13 后稳定），工作区
> 仅有其截图再生产物（不碰）。无代码变更。

## 记录

- 探测：`scripts/probe-source-recovery.py` → `still-broken`；
- freshness §10.2b 日志按机制追加；
- BLOCKED_SOURCE 三项与故事板 CLONE_DECISION 替换继续等待源站
  渲染恢复（PAR-005 §10 在案）。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- jimeng batch 5-8 源站级深化对照（随并行路线节奏）；
- 相机运动预设 append 语义的产品裁决跟进（DEC-048）。
