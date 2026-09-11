# Batch 346 — batch 39 时序抖动修复：确定性轮询（`VERIFIER_FIXED`）

> 状态：batch 39 从 sweep 失败恢复**确定性全绿**（三连跑通过）；
> 台账 §5.z3 已更新。无产品代码变更。源站恢复探测：
> `RECOVERY: still-broken`。

## 根因与修复

- sweep 失败形态：`assert state["timeline"]["currentTime"] > 0.2`；
- 插桩实测：点击播放后 320ms 采样得 `currentTime=0.277、
  isPlaying=true`——时间线**在正常推进**，旧失败系起播延迟时
  固定等待采到 <0.2 的边缘值（时序抖动，非产品缺陷、非媒体
  伪影——修正 batch 184 模式对本例的归因）；
- 修复：固定 320ms 等待改为 **5s 超时轮询**（120ms 步进），确定性
  等待时间线推进越过阈值；三连跑全部通过。

## 源站状态

`RECOVERY: still-broken`——BLOCKED_SOURCE 三项维持阻塞。

## 验收

- batch 39 三连跑全绿；台账 §5.z3 更新（39 → 已修复转绿）；
- 邻位验证器 40/41/46 复跑维持已归档失败（预期）；
- docs check 通过；无产品代码变更。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 40/41/46 维持归档（byte_size 媒体伪影族 / transform 导入漂移 /
  bounded Director），除非未来清扫出现形态变化。
