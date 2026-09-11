# Batch 393 — OVERLAY catalog §3.3 兼容状态审计（`AUDIT_RECORDED`）

> 状态：§3.3 的 8 项兼容状态对照现版代码逐项核实——**全部维持**
> （无一项因 batch 332-372 而改变）。无产品代码变更。源站恢复
> 重测：`RECOVERY: still-broken` 维持。

## 审计结果（逐项对照现版调用者）

| 兼容状态 | 现版核实 | 判定 |
|---|---|---|
| isToolboxPanelOpen / toggleToolboxPanel | uiStore 外无直接调用者；LeftSidebar 经通用 `togglePanel("toolbox")` 走 `activePrimaryPanel` 权威 | 维持（与权威重复） |
| isMaterialPanelOpen / toggleMaterialPanel | 同上（material） | 维持 |
| isCharacterPanelOpen / toggleCharacterPanel | 同上（character） | 维持 |
| isHistoryPanelOpen / toggleHistoryPanel | 同上（history） | 维持 |
| isTutorialPanelOpen / toggleTutorialPanel | 同上（tutorial） | 维持 |
| isNotificationOpen / toggleNotification | 仍无调用者 / mount owner | 维持 |
| isUserMenuOpen / toggleUserMenu | 仍无调用者 / mount owner | 维持 |
| showGrid / toggleGrid | route 读 showGrid 渲染 Dots；toggleGrid 无 shell 入口（网格吸附是 snapToGrid） | 维持 |

## 结论

- 「获得编码授权前只记录不删除」的处置**维持**；
- batch 341 的 shell 入口走通用 togglePanel 路径，与这组旧
  boolean/action 无交集——§3.3 判定不受近期批次影响。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 获得编码授权后的 §3.3 兼容状态清理（专项）。
