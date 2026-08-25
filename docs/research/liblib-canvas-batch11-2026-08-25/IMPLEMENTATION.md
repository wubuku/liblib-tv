# Batch 11 实施结果：画布壳层浮层互斥与生命周期

## 1. 实施内容

- `uiStore` 新增 `PrimaryPanel` 和 `activePrimaryPanel`，统一承载 `move/toolbox/material/character/history/tutorial`。
- `LeftSidebar` 不再保存局部 `activePanel`，改为使用 `uiStore`。
- `toggleAddNodePanel`、`toggleShortcutsPanel`、`toggleCanvasDropdown`、`toggleAssetPanel`、`toggleSharePanel`、`toggleAgent` 和主入口面板 action 统一清理其他顶层 overlay。
- `setEditorMode("storyboard")` 先清理已有 overlay，再打开 Agent；切回工作台时关闭 Agent。
- `closeAllPanels()` 现在可以真正清理底部主面板、顶层菜单和 Agent。
- 为当前面板增加 `data-liblib-overlay` 稳定选择器，作为浏览器验证合同。
- 未修改节点、边、viewport、面板内容、生成 mock 或 FrameOS。

## 2. 关键实现决策

### Store 集中状态

`LeftSidebar` 的局部 state 会让页面级 Escape 和模式切换无法关闭面板。将它提升到 `uiStore` 后，所有顶层入口可以共享相同的互斥清理路径，同时仍保留 LibTV 自己的 UI store 边界。

### 互斥而非层层覆盖

每个顶层入口打开时都使用 `closedOverlayState` 清除其他入口。角色库和历史等带遮罩 Modal 仍由自身遮罩阻止底层点击；用户需要先关闭 Modal，再操作底部工具条。Batch 11 的脚本对此有明确步骤，不把遮罩拦截误判为互斥失败。

### 整理确认卡保持独立

整理确认卡是 `page.tsx` 的事务反馈，不属于主入口浮层。它仍由 organize snapshot 控制，避免把节点布局恢复流程耦合到通用 overlay store。

## 3. 验证结果

命令：

```bash
python3 scripts/verify-liblib-batch11.py
```

结果：

```text
Batch11 Playwright verification passed: mutually exclusive LibTV overlays,
Escape cleanup, storyboard Agent lifecycle, graph preservation, mobile
overflow, screenshots, console.
```

覆盖：

- 工具箱 → Agent → 分享 → 资产管理 → 画布下拉 → 添加节点 → 快捷键 → 角色库 → 教程；
- Modal 关闭后继续切换底部入口；
- Escape 清理全部顶层入口；
- 分镜/工作台模式切换与 Agent；
- 节点数 `10`、边数 `11` 保持不变；
- `929x874` 与 `390x844`；
- console error 和 page error 为零。

第一次脚本运行发现角色库 Modal 遮罩拦截底部按钮点击，随后将测试修正为先关闭 Modal；这属于测试流程修正，不是产品实现回退。

## 4. 证据

- Desktop：[liblib-clone-batch11-overlay-lifecycle-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch11-overlay-lifecycle-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch11-overlay-lifecycle-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch11-overlay-lifecycle-mobile-390-2026-08-25.png)
- Script：[verify-liblib-batch11.py](../../../scripts/verify-liblib-batch11.py)
