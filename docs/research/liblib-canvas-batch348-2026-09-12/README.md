# Batch 348 — batch 41 导入漂移定案：验证器读错层，数据层无损（`VERIFIER_FIXED`）

> 状态：batch 41 从 sweep 失败恢复**确定性三连绿**；台账 §5.z3
> 更新（41 → 已修复转绿）。无产品代码变更——四层转储实证数据层
> 无损。源站恢复探测：`RECOVERY: still-broken`。

## 深查结论（四层转储实证）

导入完成后同时转储 objects / authoredObjects / phoneVcam.baselineCamera /
源相机 transform 轨道四层：

| 层 | 值 | 判定 |
|---|---|---|
| authoredObjects.transform | **[4.45, 2.475, 6.15]** | 与验证器基线**精确一致**——导入的数据层还原无误 |
| objects.transform（运行时投影） | [3.504, 2.077, 4.854] | 投影含残留 phone-pose——**设计行为** |
| phoneVcam.pose | yaw -33.9 / pitch 12.6 / roll -9.0 | 录制残留姿态 |
| 源相机 transform 轨道 | null（不存在） | 排除脏关键帧假设 |

**定案**：现架构下导入完成后活动相机保持 phone-pose 控制态
（status "imported" 在 `applyPhoneVcamPose` 允许列表），运行时投影 =
基线 + 残留姿态。这与 AGENTS.md 的分层架构一致：
**authoredObjects 是可移植创作基线，objects 是其运行时投影**。
旧验证器断言读的是 objects 投影层——合同意图（导入不损坏源数据）
并未发生，损坏假设不成立。

## 修复（验证器迁移）

batch 41 的 `imported["source"]` 从 `state.objects` 改为
`state.authoredObjects`——断言迁至 authored 数据层，保留「导入不改动
源相机」的合同意图。三连跑全绿。

## 验收

- batch 41 三连跑全绿；台账 §5.z3 更新（41 → 已修复转绿）；
- docs check 通过（907 Markdown）；无产品代码变更。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 46 的截图条目抖动链深查（同方法论）；
- 新表面随源站更新巡检。
