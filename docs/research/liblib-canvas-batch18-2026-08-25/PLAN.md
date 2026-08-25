# Batch 18 计划：缩放菜单结构与生命周期

## 1. 缺口与价值

| 缺口 | 当前 clone | 原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 顶部控制结构错误 | `- / % / +` 三段 | 单行 `28 %` | 5 | 改为百分比状态行 |
| 菜单项污染 | 额外 `点阵网格` | 原站截图无该项 | 4 | 从菜单移除 |
| Escape 不统一 | 局部 `useState` | 页面级局部浮层应可退出 | 5 | 迁入 `uiStore` |
| overlay 可共存 | 其他入口不清理 zoom | 原站截图一次只显示一个菜单 | 5 | 纳入 closed overlay state |
| 规格过时 | 文档仍写 No-op | 当前已有实际命令 | 4 | 重写组件合同 |

## 2. 实施步骤

1. `uiStore` 增加 `isZoomMenuOpen`、`toggleZoomMenu`、`closeZoomMenu`，并纳入 `closedOverlayState`。
2. `BottomToolbar` 删除局部 zoom state，使用 store 控制。
3. 按原站顺序渲染：
   - 当前百分比行；
   - 放大 / 缩小 / 适合屏幕与快捷键；
   - 分隔线；
   - 50% / 100% / 800%。
4. 移除缩放菜单中的点阵网格项；保留 `showGrid/toggleGrid` store API。
5. 增加外部点击关闭，避免点击菜单自身误关闭。
6. 添加 Batch 18 Playwright：结构、zoom 数值、fit/fixed zoom、Escape、外部点击、与资产抽屉互斥、移动端溢出、console。
7. 更新 BottomToolbar 规格、行为、Harness、CHANGELOG、Big Picture。

## 3. 事实边界

### Source fact

- 原站截图在 `28%` 状态打开缩放菜单。
- 菜单约 `188px` 宽，锚定在缩放按钮上方。
- 顶部为 `28` 和右侧 `%` 的状态行。
- 命令顺序：放大、缩小、适合屏幕、50%、100%、800%。
- 快捷键文案：`⌘ +`、`⌘ -`、`⌘ 0`。
- 截图中没有点阵网格项。

### Inference

- 缩放菜单是与画布菜单、资产抽屉同级的局部 overlay，应由统一 Escape/互斥生命周期清理。

### Clone-only decision

- 放大/缩小/固定缩放后菜单保持打开，以兼容当前 Batch 9 连续观察与截图合同。
- 外部点击通过菜单 ref 判定；这属于 clone 的可验证关闭实现。

## 4. 验收标准

- 菜单包含 6 个源站命令和单独百分比状态行，不含网格开关。
- 放大/缩小按 `0.1` 变化；50/100/800 和适合屏幕可用。
- zoom 操作不关闭菜单；Escape、外部点击会关闭。
- 打开资产管理或其他顶层 overlay 会关闭 zoom；打开 zoom 会清理其他 overlay。
- Batch 9 浮层 zoom 回归、Batch 11 overlay、Batch 17 资产抽屉不回归。
- 桌面与 390px 无页面级横向溢出。
