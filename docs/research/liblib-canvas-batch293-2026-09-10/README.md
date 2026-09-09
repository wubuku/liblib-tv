# Batch 293 — clone ⌘A 合同检查：与源站一致（源站 2026-09-10 对照）

> 状态：`CONFIRMED_NO_DRIFT`（无代码变更）。

## 对照结果

| 环境 | ⌘A 行为 | Ctrl+A 行为 |
|---|---|---|
| 源站（batch 292） | 未全选（sel 保持 1） | inert |
| **clone** | **未全选（sel 1→1）** | inert |

**⌘A 全选在两边都不存在**——batch 292 的 ⌘A SOURCE_UNKNOWN 在 clone 侧
同样成立，行为一致，无需对齐。（源站 ⌘A 未全选的成因仍
SOURCE_UNKNOWN——可能需 pane 焦点或该功能缺失。）

## 其余快捷键对照（batch 292 已证，复述）

⌘C/⌘V 粘贴 ✓ 双边、⌘Z 撤销 ✓ 双边、Delete/Backspace/Escape ✓ 双边。

## 验收

- 无源站操作；无代码变更；docs check 通过。
