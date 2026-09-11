# Batch 387 — 循环确认：/project 变更回归 + jimeng 健康（`CONFIRMATION_RECORDED`）

> 状态：全部门禁绿；无产品代码变更。liblib.tv 画布页恢复重测：
> `RECOVERY: still-broken` 维持。

## 确认内容

- /project 页变更回归：168（侧栏 7 条 + 顶部横幅）/ 148（项目卡
  封面）/ 150（卡片布局）/ 21 全绿；
- jimeng batch 1 验证器绿（并行路线健康）；
- `npm run check` 0 errors / 0 warnings（编译成功）；
- docs check 942 文件通过。

## 待外部条件的队列（不变）

- liblib.tv 画布页恢复 → BLOCKED_SOURCE 三项补采（Hailuo 系条件
  分解、480P 档批量、Style Video 费率）+ 故事板 CLONE_DECISION
  替换 + PAR-004 phase 2 源站对照 + DEC-048 采样裁决；
- jimeng batch 5-8 源站级深化对照（随并行路线节奏）。

## 后续候选

- 源站恢复重测（probe-source-recovery.py 心跳）；
- 相机运动预设 append 语义的产品裁决跟进（DEC-048）。
