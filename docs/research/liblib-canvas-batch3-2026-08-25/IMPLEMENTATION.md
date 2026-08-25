# LibTV 画布 Batch 3 实施记录

> 状态：已完成（源码、构建、浏览器回归和文档已完成）  
> 日期：2026-08-25

## 1. 本轮实际实施

### 画布 history

`src/store/canvasStore.ts` 新增按画布隔离的 `historyByCanvas`：

- 最多保留 50 个图快照；
- `undo` / `redo` 支持 `Cmd/Ctrl+Z`、`Cmd/Ctrl+Shift+Z` 和 `Cmd/Ctrl+Y`；
- 新建/派生/复制/删除节点、节点数据更新、添加/删除连线、整理画布进入 history；
- 节点拖动只在 `onNodeDragStop` 入栈一次；
- 通过拖动开始快照避免“拖动完成后再记录当前状态”导致撤销无效；
- 选择、普通 `setViewport`、面板开关不进入 history；
- 画布复制现在保留并重映射内部连线，不再清空边。

### 节点复制

- `Cmd/Ctrl+D` 复制当前选中节点；
- 复制节点偏移 `40x40` 并自动选中；
- 同时复制原节点的入边/出边，把端点映射到副本；
- `TextNode` 的编辑结果在失焦时写回 `canvasStore`，因此可以撤销/重做；
- `Escape` 编辑文本会放弃草稿，不写入 store。

### 快捷键闭环

`src/app/page.tsx` 与 `KeyboardShortcutsDialog` 已同步：

- `Tab` 打开添加节点面板；
- `Option/Alt+Shift+F` 整理画布；
- `V` / `H`、删除、缩放和适应画布保留；
- 面板删除了当前克隆尚未实现的成组、连线、生成和 Option+拖动等宣传项。

## 2. 证据纠偏

本轮特别复查了已有截图，避免把通用编辑器行为当作 LibTV 事实：

- `liblib-original-canvas-menu-2026-08-25.png` 是画布下拉菜单，不是右键上下文菜单；
- `liblib-original-shortcuts-2026-08-25.png` 证明了快捷键命令，但不证明存在可见 history dock；
- `liblib-original-2026-08-25-desktop.png` 的底部画布工具条没有额外的撤销/重做按钮。

因此：

- 节点/空白处右键菜单已从本批默认 UI 移除；
- 可见撤销/重做 dock 已从本批默认 UI 移除；
- [`CONTEXT_MENU.spec.md`](CONTEXT_MENU.spec.md) 保留为待实时证据确认的候选规格；
- history 作为快捷键和内部命令能力实现，不声称是新增的原站视觉部件。

## 3. 当前验证

已完成：

- `npx tsc --noEmit --pretty false`
- `npm run lint -- --quiet`
- `npm run check`
- Playwright Chromium：桌面 `1440x900` 与移动 `390x844`
- 桌面初始节点数 `10`
- `Cmd+D` 节点数 `10 -> 11`
- 对带 3 条关联边的图片节点执行 `Cmd+D`，连线数 `11 -> 14`；撤销恢复为 `11`
- `Cmd+Z` / `Cmd+Shift+Z` 恢复复制前后状态
- `Option/Alt+Shift+F` 显示“是否保留此次整理结果？”确认浮层
- 文本节点编辑写回并可撤销
- 移动端页面无横向溢出
- 移动端快捷键面板无横向溢出
- 浏览器控制台错误数 `0`

所有检查均通过。Lint 的完整输出仍有仓库既有 9 个 warning，但本轮没有新增 error。

验证截图：

- `docs/design-references/liblib-clone-batch3-desktop-baseline-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-shortcuts-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-add-node-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-duplicate-redo-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-organize-preview-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch3-shortcuts-mobile-390-2026-08-25.png`

## 4. 已知边界

- history 只存在 Zustand 内存，刷新后丢失；
- 尚未实现真实系统剪贴板；
- 尚未实现原站快捷键中的成组、解组、连线、生成、Option+拖动；
- 这些未实现项不再出现在快捷键面板中，避免克隆行为与文案不一致。
