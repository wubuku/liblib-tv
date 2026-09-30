# Batch 330（2026-10-01）：分组重命名 / 改色 的撤销覆盖

## 结论一句话

Batch 329 补齐了 `createGroup` / `ungroup` / `arrangeGroup` 的撤销，但
`renameGroup` / `setGroupColor` 仍只改 state 不入栈 → **重命名和改色不可撤销**。
已补齐，并顺带堵上一个新发现的问题：无净变化的提交会白占一格撤销。

## 运行时证据（修复前）

```
rename : changedState=true  pushed=false  undoRestores=false   组1 → 探测组B 后撤销不回退
color  : changedState=true  pushed=false  undoRestores=false   #64748b → #ff0000 后撤销不回退
move   : changedState=true  pushed=false  undoRestores=false   整组位移撤销不回退
```

（`move` 的 `pushed=false` 是**正确**的，详见下方「为什么不改 moveGroup」。）

## 修复

`renameGroup` / `setGroupColor` 改用 Batch 329 引入的 `pushHistorySnapshot(state)`，
并加**无净变化不入栈**的守卫：

- `renameGroup`：空名 / 去空白后与原名相同 → 直接 return，不入栈；
- `setGroupColor`：与原色相同 → 直接 return，不入栈。

### 为什么加这个守卫

第一版修复只是简单加 `pushHistorySnapshot`，随即在写验证器时暴露出副作用：
`renameGroup(gid, '   ')` 虽然**状态不变**（名字仍是原名），却照样入栈 ——
用户按一次撤销只会被消耗掉、什么也没发生。空提交（重复点确认、同色重复点）
在真实使用中很常见，不该占用撤销格。同色重复点色板更典型。

守卫让「入栈」与「状态确实变了」严格等价。

## 为什么不改 `moveGroup`

`moveGroup` 在拖拽过程中**每帧**调用（`FrameosGroupCanvas` 的 `onMove`）。
若在 action 内入栈，一次拖拽会产生数十~数百条历史，直接灌爆 20 格栈 ——
这正是 Batch 189/232 处理节点拖拽时的老问题。

整组拖拽的可撤销性由 **UI 层**保证：手势开始（位移 > 2px）时调一次
`pushHistory()`（`FrameosGroupCanvas.tsx:70`），之后逐帧只改位置不入栈 ——
与节点拖拽同一模式。验证器把这条当作**必须成立的不变式**来测：
一次 `pushHistory` + 6 次 `moveGroup`，历史深度只 +1，且一次撤销精确回原位。

## CLONE_DECISION（重要）

**源站是否把分组重命名 / 改色 / 整组拖拽视为可撤销动作，本批未采样** ——
源站被「确定你不是机器人」阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。

因此本批**不是源站对齐声明**，而是**克隆内部一致性**决策：Batch 329 之后
成组 / 解组 / 排列已可撤销，同层级的组操作却不可撤销，自相矛盾。补齐后
「分组相关操作一律可撤销」成为一致规则。恢复源站访问后需复核并按真实语义调整。

## 验证器

`scripts/verify-frameos-batch330.py` — **22 项断言全 PASS，0 诊断**：

1. 重命名入栈 / 撤销还原旧名 / 重做恢复新名；
2. 改色入栈 / 撤销还原原色 / 重做恢复新色；
3. **无净变化不入栈**：空名、同名、同色三种情况历史深度均不变；
4. **整组拖拽历史不灌爆**：6 次 `moveGroup` 后深度只 +1；
5. 拖拽撤销后**分组盒与全部成员位置一并还原**；
6. 成员数与分组存续（Batch 329 行为保持）；
7. 控制台/页面错误为 0。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch330-group-history.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 分组动作的撤销覆盖至此**已完整**（成组/解组/排列/重命名/改色/整组拖拽）。
- 候选 Batch 331：同一类「入栈遗漏」是否还存在于**非分组**路径 ——
  例如 `beginResize` 之外的手势、或 `toggleMinimap` 类纯 UI 状态是否被误入历史
  （反向问题：不该入栈却入了，导致撤销"无事可做"）。需先探针枚举全部 action
  的入栈行为，再决定是否立项。
