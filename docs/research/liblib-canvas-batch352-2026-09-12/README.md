# Batch 352 — batch 44 考古定案：预设 append 纯拼接自始如此（`ARCHAEOLOGY_RECORDED`）

> 状态：batch 44 完成 git 考古与代码对照，归因**成立并补全证据链**
> （台账 §5.z3 更新）。无产品代码变更。源站恢复探测：
> `RECOVERY: still-broken`。

## 深查结论

- 实测：pull-out 预设 append 后轨道为 [0,1,2,…,8]（每秒一键），
  旧合同期望 [0,4,6,8]——差异为残留键 1,2,3,5,7 未被清除；
- 代码对照：`applyCameraMotionPreset` 的 append 分支为
  `[...track.keyframes, ...generated.slice(1)]` **纯拼接**，无清除
  逻辑；
- **git 考古**：该函数仅三次提交（8125872 引入 → 2c6ed22 锁定保护
  → 306786d 选择权威），合并逻辑从未变过——「清除冲突键」行为
  **从未存在**，batch 44 的 [0,4,6,8] 期望从未与实现匹配过；
- **定案**：非回归、非新缺陷。现代化前置问题是产品设计裁决
  （append 是否应清除窗口内冲突键），归入 LIBTV_UIUX_PARITY_BACKLOG
  性质而非验证器修复。台账 §5.z3 补全考古证据链。

## 后续候选

- 相机运动预设 append 语义的产品裁决（清除冲突键与否）；
- 48/49/57/61 深查（同方法论，各一轮）；
- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
