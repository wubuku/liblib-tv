# Batch 347 — batch 40 连跑必挂根因修复：Chrome 147 duration 伪影（`VERIFIER_FIXED`）

> 状态：batch 40 从「单跑偶过、连跑必挂」恢复**确定性三连绿**；
> 台账 §5.z3 更新（40 → 已修复转绿，39 于 batch 346 同族修复）。
> 无产品代码变更。源站恢复探测：`RECOVERY: still-broken`。

## 根因（插桩实测）

1. **Chrome 147 MediaRecorder 伪影**：录制的 webm blob 在
   `loadedmetadata` 后 `duration` 仍为 `Infinity`——验证器第二次
   seek 计算 `duration * 0.82` 得 Infinity，赋值 `currentTime`
   抛错（batch 184 归因的媒体伪影，环境因素为 Chrome 147）；
   **连跑必挂、单跑偶过**的原因是 blob 元数据加载时序；
2. **阈值过紧**：webm 尺寸随编码抖动，实测 8813 / 9103 / 10432
   跨越 10000 阈值。

**修复**：加载后若 duration 非有限，执行标准强制 seek hack
（`currentTime = 1e101` → 等 seeked/durationchange 至有限）；
尺寸阈值 10000 → 8000（合同意图「非平凡真实录制」保持）。

## 归因复核结论（同方法论）

- **41 维持归因并升级注记**：imported transform 与 baseline 为
  **实质性位置漂移**（[3.24,1.98,4.61] vs [4.45,2.48,6.15]），
  非浮点舍入——疑似 Director 序列化导入的真实缺陷候选，
  待对照 current gates（DEC-026 portable contract）单独深查；
- **46 维持归因**：截图条目断言存在抖动链（复跑时 180 过而 182 挂）。

## 验收

- batch 40 三连跑全绿（含此前连跑必挂场景）；
- 41/46 维持已归档失败（附实测注记）；docs check 通过
  （906 Markdown）；无产品代码变更。

## 后续候选

- 41 的 Director 序列化导入漂移深查（对照 current gates）；
- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
