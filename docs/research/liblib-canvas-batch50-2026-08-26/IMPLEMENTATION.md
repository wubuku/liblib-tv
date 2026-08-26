# Batch 50 实施记录

> 状态：计划已落档，待实施。

## 保护上下文

- [`PLAN.md`](PLAN.md)：选择理由、范围、状态副作用和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：LibTV unknown、clone fact、
  upstream fact 分层；
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)：固定上游 shell/
  keyboard 结构；
- [`DIRECTOR_WORKSPACE_SHELL.spec.md`](DIRECTOR_WORKSPACE_SHELL.spec.md)：
  clone 行为契约；
- 上一批 [`../liblib-canvas-batch49-2026-08-26/IMPLEMENTATION.md`](../liblib-canvas-batch49-2026-08-26/IMPLEMENTATION.md)：
  视口 gizmo 已收口，改动必须保持其 capture/path/phone guard。

## 进度

- [x] Batch 50 计划与证据边界
- [x] upstream shell/keyboard 代码考古
- [ ] `viewportPanelsCollapsed` session-local state
- [ ] Director toolbar 全屏/恢复侧栏 command
- [ ] desktop shell geometry 与 mobile drawer recovery
- [ ] workspace focus owner 与 page shortcut isolation
- [ ] focused Playwright、截图台账和一次视觉识别
- [ ] 跨批回归与 repository gates
- [ ] commit/push

## 实施决定

- 不使用 Browser Fullscreen API；
- 不把 UI collapse 写入普通 graph/history；
- 不为 source 未证实的 Director shortcut 创造新命令；
- 不修改 `docs/design-references/` 历史证据，新增截图只属于 Batch 50；
- 若 source evidence 仍不足，成熟度结论只写 clone-owned bounded contract。

## 接力

实施中断时先读本文件和 [`PLAN.md`](PLAN.md)，再查看当前
`DirectorDesk.tsx`、`DirectorViewport.tsx`、`directorStore.ts` 和
`src/app/page.tsx` 的对应 selector；不要重复识别 Batch 49 截图。
