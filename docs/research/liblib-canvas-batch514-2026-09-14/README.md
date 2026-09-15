# Batch 514 — VR-010 Slice B：history isolation focused browser 层

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。按合同 §10.2
> （import UI 尚不存在，browser 范围即 history isolation）：经真实 UI
> 事务（AddNodePanel 生成历史 fixture attach，batch 478 流）验证
> 一命令一步、undo/redo 恢复内容（assetId 相等）且选择不残留陈旧、
> 新命令清空 redo future、缩放不进 history、零 console 错误。

## 发现（未修，留档）

- **viewport undo-echo 异常**：经缩放菜单 zoom（不进 history，past/
  future 恒 0——§6 隔离正确）后，空栈 Control+z 仍把已提交的
  store viewport 打回旧值（0.426→0.526）。undo() 本身对空栈为
  no-op 不触 viewport——回写来自 VGP viewport reconciliation 路径。
  按 AGENTS.md 硬约束（viewport 逻辑需源证据）不在本批修改；
  作为 BLOCKED_SOURCE 观察项留档于 runtime-audit.json。

## 实施中修正的验证器误设

- attach 后 AddNodePanel 关闭动画期（~600ms）为 blocking foreground
  surface，会吞快捷键——场景间需等面板退场；
- 普通空白左键拖拽为 no-op（batch 77 语义），视口变更用缩放菜单；
- 重复 attach 同一 fixture 是去重 no-op（零 history），场景需换资产。

## 内容

- `scripts/verify-liblib-batch514.py`（4 场景）；
- `runtime-audit.json`：本目录。
