# Batch 155 — 5分钟超长视频芯片时长范围修复（30..300）

## 问题

Batch 128 的芯片联动把时长设为 300s，但参数菜单的滑杆范围由
`mode === "long-video"` 单独驱动（常规模式 4..30）——点完芯片后打开参数菜单
会出现半态：滑杆 thumb 被钳制在 30、状态值仍是 300、拖动即回落 ≤30。

## 修复（CLONE_DECISION）

- `isLongRange = isLongVideo || attempt === "5分钟超长视频"`；时长范围与参数
  菜单布局（data-video-params-mode=long）按 isLongRange 切换。
- 取消 5 分钟芯片时时长钳回 ≤30（源站取消联动未采样，Batch 128 契约保留：
  仅断言 aria-pressed）。
- 积分公式不变（长视频模式的 49/s 仅由 mode 驱动；芯片状态 Auto→46/s，
  与 Batch 153 源站直证 230=5×46 一致）。

## 验收

- `verify-liblib-batch155.py`：10 checks 通过（芯片 300s 标签 → 菜单 long 布局/
  滑杆 30..300/值 300 → 取消钳制回常规）。
- 相邻回归绿：21 / 22 / 125 / 128 / 149。
- `npm run check`：0 errors、8 warnings（既有基线）。
