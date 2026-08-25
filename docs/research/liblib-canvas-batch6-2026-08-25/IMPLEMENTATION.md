# LibTV 画布 Batch 6 实施记录

> 状态：源码实施、跨批回归和完整工程检查完成  
> 最后更新：2026-08-25

## 已确认

- 原站快捷键面板直接展示 `Space`、`V`、`H`；
- 当前快捷键面板也展示这三项；
- 当前页面只有 `V/H` keydown，没有 Space 生命周期；
- 当前固定 `panOnDrag` 与 xyflow v12 的 `selectionOnDrag` 互斥；
- 因此本批同时处理临时抓手与框选恢复。

## 已实施

### 页面导航状态

- `page.tsx` 新增瞬时 `isSpacePressed`；
- `effectivePan = canvasTool === "pan" || isSpacePressed`；
- `Space` keydown 进入临时抓手并阻止页面滚动；
- `Space` keyup、window blur、document hidden 清除临时抓手；
- 输入框、textarea 和 contenteditable 内 Space 不被全局快捷键劫持；
- `H` 持久切换抓手，`V` 持久恢复选择；
- `Cmd/Ctrl+V` 不再误触选择工具。

### React Flow 手势仲裁

- `panOnDrag={effectivePan}`；
- `selectionOnDrag={canvasTool === "select" && !effectivePan}`；
- `nodesDraggable={canvasTool === "select" && !effectivePan}`；
- `panActivationKeyCode={null}`，避免内建 Space 与页面状态重复处理；
- 页面增加 `data-canvas-tool` 和 `data-temporary-pan` 作为无视觉副作用的自动化状态钩子。

## 验证

### Batch6 专项

```bash
python3 scripts/verify-liblib-batch6.py
```

通过：

- select 模式拖动出现 `.react-flow__selection`；
- 框选命中图片节点，viewport 未平移；
- `H` 后 pane drag 平移；
- `V` 后恢复 select；
- select 下按住 Space 临时平移，松开后持久工具仍为 select；
- textarea 内 Space 不进入临时抓手；
- window blur 清除临时抓手；
- `390x844` 无横向溢出；
- 控制台错误为 0。

生成截图：

- `docs/design-references/liblib-clone-batch6-marquee-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch6-space-pan-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch6-mobile-390-2026-08-25.png`

### 跨批回归

```bash
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
```

全部通过。Batch4 多选/分组、Batch5 拖动/复制没有回归。

### 完整工程检查

```bash
npm run check
```

通过：

- lint 0 error，保留仓库既有 9 个 warning；
- TypeScript 通过；
- Next.js production build 通过；
- `/`、`/frameos`、`/frameos/canvas/[id]` 完成构建。

## 行为边界

- 原站证据确认 Space/V/H 命令存在，但没有保存按下期间的精确 class diff；
- 临时状态实现和 blur 恢复是当前 clone 的可靠前端契约；
- viewport 仍不进入 graph history；
- 没有修改 FrameOS 的导航手势。

## 下一批候选

需要新的原站实时证据后再评估：

1. `L` 快捷键连线流程；
2. `Option/Alt+拖动` 复制流程；
3. `Option/Alt+G` 合并分镜组；
4. 右键节点/空白画布菜单；
5. group 的真实拖动与标题编辑状态。
