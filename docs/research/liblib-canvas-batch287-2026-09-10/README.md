# Batch 287 — 画布切换下拉结构对照确认（源站 2026-09-10）

> 状态：`CONFIRMED_NO_STRUCTURAL_DRIFT`（∨ 子菜单内容 SOURCE_UNKNOWN）。

## 结构对照（batch 286 采样 vs clone CanvasTabDropdown）

| 源站要素（batch 286） | clone 状态 |
|---|---|
| 「画布」header | ✓ `text-sm font-medium` 画布 header |
| [+] 新建画布按钮 | ✓ `data-canvas-new`（aria-label 新建画布） |
| 画布列表行 | ✓ 有序列表（max-h-60 滚动） |
| 行尾 ∨ 子菜单 | ✓ 每画布操作菜单：在新窗口打开 / 重命名画布 / 复制画布 / 删除画布（删除带确认框、多画布时显示） |

## SOURCE_UNKNOWN

- 源站 ∨ 子菜单的具体操作项（重命名/删除/移动/复制——自动化探测受
  下拉会话状态干扰，两次尝试未稳定展开）；clone 的四项操作集为
  batch 30 时代合同，维持。

## 验收

- docs check 通过；无画布节点操作；无代码变更。
