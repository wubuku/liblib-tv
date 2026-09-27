# Batch 545 — 场景树条目右键菜单

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-28 CDP 补采
> （liblib-source-exploration-2026-09-25 截图 47-director-rightclick-tree.png
> + DOM token 采样）：右键场景树条目（机位1）弹出五项上下文菜单。

## 源站实测（SOURCE_FACT）

菜单五项（自上而下）：**打组**（组图标）/ **显示/隐藏**（眼图标）/
**锁定/解锁**（锁图标）/ **创建副本**（副本图标）/ **删除**（垃圾桶图标，
破坏性红色调）。视口空白区右键无菜单（合成 contextmenu 未触发可见
面板，SOURCE_INCONCLUSIVE——不做画布视口右键克隆）。

## clone 合同

- 树条目 `onContextMenu` → 选中该对象 + 定点弹出
  `data-director-tree-context-menu`（fixed 定位于指针处，w-128px）；
- 五项动作全部接既有 store 同源实现：打组 → groupSelectedCharacters；
  显示/隐藏 → updateObject visible 翻转；锁定/解锁 → toggleObjectLocked；
  创建副本 → copyDirectorSelection + pasteDirectorClipboard（对象数 +1）；
  删除 → deleteDirectorEntity DELETE_OBJECT；
- 外部 mousedown / ESC 关闭；动作后自动关闭；
- 视口右键不做克隆（源站行为 SOURCE_INCONCLUSIVE，留待后续真实
  指针事件补采）。

## 内容

- `src/components/director/DirectorObjectTree.tsx`（右键菜单实现）；
- `scripts/verify-liblib-batch545.py`（12 检查：五项可见、可见性翻转、
  锁定翻转、副本 +1、ESC 关闭）；
- 回归：batch 536/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
