# Batch 50 源站与证据记录

## 1. 当前证据分层

### LibTV authenticated source

本批没有重新对 LibTV authenticated Director shell 做新的 DOM/CSS 取证。
因此以下结论不能写成 LibTV source fact：

- “全屏”是否折叠面板；
- 面板折叠后的 exact width/z-index/animation；
- Director workspace 是否为 dialog、application 或其他 ARIA role；
- source 的 Escape、focus trap 和 page shortcut ownership。

Batch 50 的 source-side 风险保持 `UNKNOWN`，不通过 clone 当前实现反推。

### Clone current fact

当前 clone 的 `DirectorDesk`：

- 使用 fixed full-screen workspace；
- desktop 左侧 `220px` 对象树、右侧 `288px` Inspector 永远参与 main
  的 `left/right` inset；
- mobile 使用 tree/Inspector mutually-exclusive drawers；
- workspace 只在 window bubble listener 中处理 Escape；
- 普通 LibTV page keyboard handler 只对 Escape 检查 Director active，其他
  Delete/Space/Tab/undo/duplicate/tool shortcuts 仍可能收到事件；
- Director 没有 desktop sidebars collapsed state。

### Upstream borrowable fact

固定上游 `8c8bd361790be4d37158a7430365e65546e358fe`：

- `ViewportToolbar.tsx` 将 `全屏` 绑定到
  `toggleViewportPanelsCollapsed`；
- `DirectorDeskShell.tsx` 为 collapsed 状态加
  `is-sidebars-collapsed`，并给 sidebars `aria-hidden`；
- CSS 在 collapsed 状态 `display: none` 两侧 sidebar；
- `App.tsx` 的 `isEditableShortcutTarget` 让 input/textarea/select/
  contenteditable 不接收全局 command shortcut；
- toolbar tests 明确“全屏”不进入 browser fullscreen。

## 2. 允许的 clone 决策

- 把 collapsed state 作为 Director session UI state；
- desktop 由 parent layout 控制 rails 是否占位；
- mobile 的 drawer trigger 负责恢复可见 panel 状态；
- page keyboard handler 在 Director active 时直接 return，保留 Director
  内部 handlers 的局部优先级；
- workspace root 作为 focus owner，但不伪造完整 focus trap；
- 不修改 graph/history 或 director object schema。

## 3. 证据入口

- [`PLAN.md`](PLAN.md)
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)
- [`DIRECTOR_WORKSPACE_SHELL.spec.md`](DIRECTOR_WORKSPACE_SHELL.spec.md)
- [`../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md`](../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md)
- [`../liblib-canvas-batch49-2026-08-26/MATURITY_ASSESSMENT.md`](../liblib-canvas-batch49-2026-08-26/MATURITY_ASSESSMENT.md)
