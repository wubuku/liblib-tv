# Batch 572 — 引导气泡收起状态跨重载持久化对齐

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 571
> （截图 58）——气泡收起状态跨浏览器重载持久；batch 556 的挂载级
> coachDismissed 与源站语义不符，本批对齐。

## 合同

- `DirectorTimeline` coachDismissed 初始化自
  `localStorage["director-timeline-coach-dismissed"]`；跳过/下一步经
  `dismissCoach()` 写入 "1"（storage 不可用时降级为会话内收起）；
- 收起后重载页面/重启浏览器 → 气泡不再出现（源站跨重启持久语义，
  localStorage 同为持久存储）；
- 全新上下文（无 storage）→ 气泡再现（首访引导）。

## 内容

- `src/components/director/DirectorTimeline.tsx`（localStorage 初始化 +
  dismissCoach 写入）；
- `scripts/verify-liblib-batch556.py`（迁移至持久化合同：收起 → 重载
  → 仍收起；替代原「每次挂载再现」断言）；
- 回归：batch 556/563/566/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
