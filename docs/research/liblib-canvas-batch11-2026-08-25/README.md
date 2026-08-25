# Batch 11：画布壳层浮层互斥与生命周期

> 日期：2026-08-25
> 范围：LibTV clone 的顶层导航、底部入口面板、资产抽屉、Agent、分享和编辑模式切换。
> 目标：让一次只存在一个主操作浮层，避免不同入口同时覆盖画布或互相遮挡。

## 为什么做这一批

Batch 1 已经按原站几何复刻了工具箱、素材库、角色库、历史和快捷键等入口；Batch 7-10 又增加了整理确认卡、节点编辑器和 Seedance 面板。当前代码的视觉组件已经较多，但面板开关分散在：

- `uiStore` 中的多个布尔值；
- `LeftSidebar` 的局部 `activePanel`；
- `TopNavBar` 的分享/Agent 状态；
- `CanvasTabDropdown` 的画布下拉状态。

因此 `closeAllPanels()` 无法真正关闭 `LeftSidebar` 的局部面板，打开 Agent、分享、资产管理或快捷键时也可能留下旧面板。这个问题不一定改变单张截图，但会在连续操作中破坏画布的层级和工作流。

## 证据边界

### Source fact

- 原站画布壳层由顶部浮动导航、底部主工具条和底部画布工具条组成，入口面板覆盖在画布上方，而不是使用多个永久侧栏。
- 原站主工具入口面板的几何和触发关系已记录在 [`../liblib-live-2026-08-25/BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)。
- 当前研究结论要求主入口状态互斥；该结论已写入 [`../BEHAVIORS.md`](../BEHAVIORS.md)。
- 分镜模式会打开 Agent，工作台/分镜是顶部的模式切换，见 [`../../BIG_PICTURE.md`](../../BIG_PICTURE.md)。

### Current-code fact

- `LeftSidebar` 在本地维护 `activePanel`，`uiStore.closeAllPanels()` 无法关闭它。
- `TopNavBar`、`AssetManagerPanel`、`CanvasTabDropdown` 和 `KeyboardShortcutsDialog` 使用不同的布尔开关。
- 现有 `toggle*` action 大多只切换自身，不关闭其他顶层 overlay。

### Clone decision

- 将底部主工具条面板的选择提升到 `uiStore.activePrimaryPanel`。
- 通过 `uiStore` 的互斥 action 统一关闭其他顶层 overlay。
- 不把 LibTV 与 FrameOS 合并，也不引入通用 `mode` flag。
- 不改变面板内部内容、尺寸、生成 mock 或原站未知的业务行为。
- 整理确认卡是画布操作反馈，不纳入主浮层互斥状态；它在整理事务结束前独立存在。

## 批次验收

- 打开任意一个底部主入口面板后，再打开另一个，前者卸载。
- 打开 Agent、分享、资产管理、画布下拉、添加节点或快捷键时，其他顶层入口卸载。
- 进入分镜模式时 Agent 打开；回到工作台时 Agent 关闭。
- `Escape` 能关闭所有顶层面板，包括 `LeftSidebar` 面板。
- 面板切换不改变节点数、边数和画布 viewport。
- 桌面与 390px 视口无横向溢出，浏览器 console/page error 为零。

## 关联

- 计划：[PLAN.md](PLAN.md)
- 组件/状态合同：[OVERLAY_LIFECYCLE.spec.md](OVERLAY_LIFECYCLE.spec.md)
- 实施结果：[IMPLEMENTATION.md](IMPLEMENTATION.md)
- 截图台账：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
