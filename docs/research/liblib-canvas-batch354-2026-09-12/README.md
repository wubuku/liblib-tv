# Batch 354 — batch 49 定案：两处时序抖动修复（`VERIFIER_FIXED`）

> 状态：batch 49 从 sweep 失败恢复**确定性三连绿**；台账 §5.z3
> 更新（49 → 已修复转绿）。无产品代码变更。源站恢复探测：
> `RECOVERY: still-broken`。

## 根因与修复（插桩实证）

1. **gizmo 隐藏窗口竞态**：截图流程中 gizmo 组件卸载（isCapturing
   → return null）、完成即重新挂载——`wait_for(hidden)` 在点击后
   才起跑，挂载早已完成 → 30s 超时。修复：点击前挂
   MutationObserver，确定性记录「截图中 gizmo 卸载」事件替代
   事后 hidden 等待；
2. **轴位切换动画未 settle**：`assert_axis_position` 在相机动画
   过渡途中读 gizmo 快照（run3 实测 y-negative 读到 +Y 侧过渡态）
   ——加 3s settle 轮询（150ms 步进）。

## AGED_GATE 清算进度（batch 335 sweep 13 项 → 已清算 8 项）

| 状态 | 验证器 | 修复批次 |
|---|---|---|
| 已转绿 | 29 / 39 / 40 / 41 / 46 / 48 / 49 / 64 | 338 / 346 / 347 / 348 / 349 / 351 |
| 维持归档 | 6（marquee 历史化）、57（LIBTV-VR-009 local slice）、61（LIBTV-VR-016 之外）、89（移动面板生命周期取代） | — |

## 后续候选

- 57/61/89 三项按需深查（57 连接元组、61 语料、89 已有 339 结论）；
- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
