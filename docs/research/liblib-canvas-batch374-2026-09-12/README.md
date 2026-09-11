# Batch 374 — PAR-004 phase 1：clone 键盘与焦点所有权清单（`RESEARCH_RECORDED`）

> 状态：只读代码盘点完成（DEC-015 合规，无 src 变更）。源站侧
> 对照待恢复（`RECOVERY: still-broken` 维持）。

## 1. 页级键盘 handler（`page.tsx` canvas keydown）

| 键 | 行为 |
|---|---|
| Escape | 关 add-node 面板/canvas dropdown 等覆盖层（825/844/877 多段） |
| Delete / Backspace | 删除选中节点/边（870） |
| Tab | toggleAddNodePanel（901） |
| Meta+0 / Meta+(+|=) / Meta+- | 适合屏幕/放大/缩小（917-925） |
| Meta+Z / Meta+Shift+Z | undo/redo |
| G / Shift+G | group / ungroup |

## 2. Surface 级键盘/指针隔离

| Surface | 局部处理 |
|---|---|
| AgentDrawer | onKeyDown Escape + stopPropagation（仅当内部 menu 打开，235） |
| HistoryPanel | 容器 mousedown stopPropagation（outside-close 隔离，53） |
| DirectorDesk | Escape + activeMobilePanel → closeMobilePanel（432）；Delete/Backspace（467）；zoom preset stopPropagation（328/334） |
| 其余（Share/Shortcuts/Tutorial/Toolbox/Material/Character/AddNode） | 依赖页级 Escape / document mousedown outside（catalog §4.3 crosswalk 在案） |

## 3. 焦点所有权

| 域 | 机制 |
|---|---|
| 画布 | `data-libtv-canvas-focus-root`（tabIndex -1）+ pane 点击 `focusCanvasRoot`（1020） |
| Director | `useDirectorFocusContainment`（DirectorDesk:31）+ `data-director-focus-scope="tree"/"inspector"` 双 aside + inert 互斥（645-700 区域） |
| Agent | 无 focus containment/trap（仅 menu Escape 隔离）——PAR-004 待决项 |

## 4. PAR-004 gap 清单（源站侧对照全部待恢复）

1. 源站各 top-level surface 的初始焦点目标与焦点恢复目标；
2. 源站是否使用 focus trap（Tab 环绕限制）与 trap 范围；
3. 源站 Escape 优先级链（drawer menu → drawer → page）的完整顺序；
4. Director 双 aside 的焦点行为与源站对照。

## 验收

- docs check 通过（932 Markdown）；无 src 变更。
