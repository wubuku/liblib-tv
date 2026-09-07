# Batch 172 — 画布右键菜单（源站 2026-09-07 CDP 补采 + 实装）

## 源站事实（2026-09-07 CDP 采样，`source-context-menu-dom.json` / `source-context-menu-open.png`）

- 触发：空白画布右键（`react-flow__pane` 空白处，点击点 (1500,300)）。
- 结构两层：全屏透明点击层 `fixed inset-0 z-index: var(--z-panel)` +
  菜单容器 `fixed z-index: calc(var(--z-panel) + 1)`，`left/top` 精确等于
  右键点击点。
- 菜单容器内联样式：`flex-direction: column; gap: 4px; min-width: 196px;
  padding: 8px; border-radius: 16px; background: var(--canvas-controls-bg,
  #262626); border: 0.5px solid var(--canvas-controls-border, #363636);
  box-shadow: var(--canvas-shadow-menu, 0 8px 32px rgba(0,0,0,.15))`。
- 六个按钮行（高 32、padding 0 8px、13px、圆角 8px、hover 背景过渡 120ms），
  顺序：上传 / 保存到我的资产 / 添加节点 /（0.5px 分隔线）撤销⌘Z /
  重做⇧⌘Z /（分隔线）粘贴⌘V。快捷键 span `font-size: 12px; opacity: .4;
  margin-left: 24px`。
- 空白画布（无选择、无历史）禁用态：保存到我的资产、撤销、重做均为
  `disabled` + `opacity: 0.3`；上传/添加节点/粘贴可用。整体 196×238。
- 更早采样：节点右键为同一菜单。

## 实施

- 新组件 `src/components/CanvasContextMenu.tsx`：backdrop（z-[62]，mousedown
  与右键均关闭）+ 菜单（z-[63]，`left/top` = 点击点，`min-w-[196px] gap-1
  p-2 rounded-2xl border-[0.5px] border-[#363636] bg-[#262626]
  shadow-[var(--canvas-shadow-menu)]`）；`data-canvas-context-menu` /
  `data-canvas-context-item={label}` 稳定选择器；Escape（capture）仅关菜单。
- `src/app/page.tsx`：ReactFlow 增加 `onPaneContextMenu` / `onNodeContextMenu`
  （节点右键先 `selectNode`）；撤销/重做接 store `undo()`/`redo()`；可用态由
  `historyByCanvas[activeCanvasId].past/future` 派生；保存到我的资产以
  `selectedNodeIds` 门控。
- clone-only 决策：源站 `--z-panel` 映射为 clone 面板层级 z-62/63；
  上传/保存到我的资产/粘贴三项点击仅关闭菜单（无后端），与 AddNodePanel
  的本地原型占位策略一致；添加节点打开既有 AddNodePanel（源站行为未直接
  点击验证，推断项）。

## 验收

- `verify-liblib-batch172.py`：15 checks 一次通过（初始关闭/打开/196 宽/
  点击点定位/六项顺序/快捷键/双分隔线/空白禁用态/Escape 关闭/添加节点开
  面板/节点右键态/撤销删节点回归/0 console error）。
- 相邻回归绿：batch160/164/165/166/167/170/171 全过。
- `npm run check`：0 errors、8 warnings（既有基线）。
- 不证明：上传/保存/粘贴点击后的源站后续行为（需后端与实点采样）。

## 源站重探备注

本次采样窗口 `visibilityState=visible` 且菜单为纯 React 状态挂载，完整
DOM 可采——此前「菜单类不可采」结论仅适用于 rAF 门控的 floating-ui/
Mantine 弹层，右键菜单不在其列。
