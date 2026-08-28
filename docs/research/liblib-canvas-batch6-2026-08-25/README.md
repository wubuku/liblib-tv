# LibTV 画布 Batch 6：导航手势闭环

> 建档日期：2026-08-25  
> 状态：历史批次完成；空白框选子合同已被 Batch 77 source runtime audit supersede
> 目标：让原站快捷键面板已经公开的 `Space`、`V`、`H` 与当前画布真实行为一致，并恢复被 pan 配置覆盖的框选。

## 本批结论

原站 `panel-audit.json` 直接记录：

- 移动画布，键盘 `Space`；
- 移动 `V`；
- 抓手工具 `H`；
- 触控板与鼠标导航入口。

当前克隆的问题不是缺一个文案，而是交互模型冲突：

- 快捷键面板展示 `Space`，页面没有临时抓手状态；
- `panOnDrag` 始终为 `true`；
- xyflow v12 在 `panOnDrag === true` 时会关闭 `selectionOnDrag`；
- 因此 Batch4 虽声明框选，空白左键拖动仍优先平移；
- `H` 与 `V` 只切换节点是否可拖，未形成完整的 pane drag 模式。

本批修正这些已有承诺，不新增未经实时观察的右键菜单、对齐线或导航动画。

2026-08-28 的登录态源站核对显示，`V` 下空白左键拖动实际是 no-op，而不是
框选。因此 Batch 6 的框选实现仍保留用于历史追溯，但不再代表当前 clone
的 source-aligned 行为。当前导航权威见 [`docs/CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md)
和 [`liblib-canvas-batch77-2026-08-28/`](../liblib-canvas-batch77-2026-08-28/)。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、价值排序、范围和验收标准
- [`NAVIGATION_GESTURES.spec.md`](NAVIGATION_GESTURES.spec.md)：`Space` / `V` / `H` 与 pane drag 状态机
- [`MARQUEE_SELECTION.spec.md`](MARQUEE_SELECTION.spec.md)：选择工具下的框选契约
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和接力记录

## 证据边界

### 直接原站证据

- `docs/research/liblib-live-2026-08-25/panel-audit.json` 的快捷键面板文本；
- 原站画布可平移、缩放，并提供移动/抓手工具入口。

### 当前代码/依赖证据

- `src/app/page.tsx` 当前固定 `panOnDrag`；
- `node_modules/@xyflow/react/dist/esm/index.js` 明确把 `_selectionOnDrag` 计算为 `selectionOnDrag && panOnDrag !== true`；
- `panActivationKeyCode` 支持关闭内建处理，由页面维护可审计的临时状态。

### 不进入本批

- 不推断原站 Space 按下时的精确 cursor CSS；
- 不实现右键拖动画布；
- 不实现触控板手势的浏览器级自定义算法；
- 不把 viewport 写入 graph undo/redo；
- 不修改 FrameOS 路线。
