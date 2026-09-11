# Batch 365 — jimeng 并行路线对照巡检（`REVIEW_RECORDED`）

> 状态：对照巡检完成，**全部合规、无需干预**。源站恢复重测
> （probe-source-recovery.py）：`RECOVERY: still-broken` 维持。

## 巡检结论（jimeng 路线，batch 8 态）

1. **store 隔离合规**：jimeng 组件/app 零引用 canvasStore 与
   frameosStore（AGENTS.md 硬约束「Keep canvasStore and
   frameosStore separate」精神的扩展遵守）；
2. **验证器**：`verify-jimeng-batch1.py` 通过（batch 1 合同绿）；
3. **typecheck**：全工作区 0 错误（batch 347 记录的 typecheck
   阻塞已由并行开发者消除）；
4. **证据纪律合规**：README 按 DEC-003 分层（SOURCE_FACT /
   CLONE_DECISION / BLOCKED_BY_FIXTURE），提取方式、viewport、
   Chrome 版本与只读边界均有记录。

## 关键澄清

jimeng 路线的源站是 **jimeng.jianying.com**（即梦/Dreamina，
独立站点）——与 liblib.tv 是不同源。**liblib.tv 的渲染劣化
（PAR-005 §10）不影响 jimeng 路线的源采样**，两条路线的
BLOCKED/可用状态相互独立。

## 后续候选

- liblib.tv 恢复重测（probe-source-recovery.py，恢复即补采
  BLOCKED_SOURCE 三项）；
- jimeng 后续 batch 的对照巡检（随其节奏）；
- 相机运动预设 append 语义的产品裁决跟进（batch 352 记录）。
