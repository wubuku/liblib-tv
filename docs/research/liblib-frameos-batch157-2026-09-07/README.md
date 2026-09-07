# FrameOS Batch 157 — 右键菜单端到端验证 + 行为表修正

## 状态勘误

`docs/research/frameos/BEHAVIORS.md` 的缺失表将「右键菜单」标记为 ❌ 暂未实现，
但 `FrameosContextMenu` 已实现并接线（`frameos/canvas/[id]/page.tsx:534`，
节点/画布两个 `openContextMenu` 调用点）。本 batch 补上端到端验证并修正文档。

## 实施

- `FrameosContextMenu.tsx` 增加稳定选择器：`data-frameos-context-menu`、
  `data-frameos-context-item={label}`（clone-only 约定，风格一致）。
- `verify-frameos-batch157.py`（12 checks）：节点右键菜单三项可见 → 创建副本
  生效且菜单关闭；画布空白右键 → 添加文本节点生效；Esc 关闭；0 diagnostics。

## 验收

- `verify-frameos-batch157.py`：12 checks 通过。
- `npm run check`：0 errors、8 warnings（既有基线）。
