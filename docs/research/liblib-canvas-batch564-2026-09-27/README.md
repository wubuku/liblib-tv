# Batch 564 — 机位跟随目标 ↔ 预设运镜联动（端到端验证批）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：截图 47
> （摄像机面板「跟随目标」字段）+ 时间线「预设运镜」trigger 的
> 「跟随目标时不可使用预设运镜」禁用语义（DirectorTimeline 既有实现）。

## 合同（既有实现的端到端验证批，零产品代码改动）

- 跟随目标未设置 → 预设运镜 trigger 可用；
- `updateCamera(cameraId, { followTargetId: characterId })`（真实动作）→
  trigger disabled + 「跟随目标时不可使用预设运镜」警告 span 可见；
- `followTargetId: null` 清除 → trigger 恢复可用、警告消失；
- 零产品代码改动，纯 verifier 形式化该联动合同（对照源站跟随语义）。

## 内容

- `scripts/verify-liblib-batch564.py`（7 检查：初始可用、跟随设置、
  禁用+警告、清除恢复）；
- 回归：batch 70/547/553 全绿；typecheck 净。
- `runtime-audit.json`：本目录。
