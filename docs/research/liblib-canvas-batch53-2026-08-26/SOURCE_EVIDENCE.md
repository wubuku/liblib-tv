# Batch 53 源站证据与 clone 决策

## 1. 证据来源

本批复用 2026-08-26 已归档的当前登录态源站观察，不重复操作共享画布。
主要证据：

- [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)
- [`LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)
- [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#10-图片工具态与预览浮层)

本批不把 Batch 52 clone 截图当作源站证据，也不重新识别相同的源站状态。
收尾阶段另对当前生产 chunk 做了静态组件审计，用于补齐 live 空态观察
没有展开的工具语义。

## 2. 已确认的空态合同

收尾阶段的静态审计锁定了当前生产 chunk 中 `AnnotateToolbar` 的可见
control contract：默认工具为 `pencil`，默认颜色为 `#ff0000`，颜色板为
`#ffcc00 #ff7a00 #ff2d55 #ff0000 #8e5cff #3a86ff #ffffff`，线宽范围为
`1..40`，默认值为 `4`。这部分是当前 production bundle 的静态证据，不把
本地 clone 的旧实现或按钮命名当作源站事实。

在源站 `图片4` 选中态进入 `标注` 后：

| 元素 | 已知事实 |
|---|---|
| 标准 toolbar | 卸载 |
| 专用 toolbar | `536x49`，节点中心对齐 |
| 专用 toolbar controls | 关闭+`标注`、`画笔`/`矩形`/`文字`、颜色、线宽、`撤销`、`重做`、`保存`；空态仅 undo/redo disabled，保存 enabled |
| 标准 bottom panel | 不存在 |
| drawing canvas | 覆盖图片节点，CSS rect `194.117x97` |
| canvas backing | `388x194`，DPR2 |
| 退出 | Escape 后专用 toolbar/canvas 消失，标准双浮层恢复 |
| graph | 空态没有绘制、保存、上传、生成或 graph mutation |

专用 toolbar 的 8 个按钮及线宽 input 已由 production chunk 静态审计补齐：
按钮是关闭+`标注`、pencil、rect、text、color、undo、redo、save；线宽是
独立 range input。空态仅 undo/redo disabled，save 仍 enabled。仍未确认的
是非空 stroke、dirty、save/upload/result transaction，而不是这些 control
的存在与空态 enabled/disabled 边界。

## 3. clone 状态合同

```text
uiStore.imageAnnotate = {
  nodeId,
  imageUrl,
  width,
  height
} | null
```

该状态属于 UI active-tool 层，不进入 `canvasStore` graph snapshot。只有当
未来批次取得保存/提交证据后，才允许增加 stroke、dirty、upload 或 result
transaction。

## 4. 几何映射

- active toolbar 使用独立 `NodeToolbar`，宽度 `536px`、高度 `49px`；
- horizontal anchor 是 selected image node center，不是 browser viewport center；
- 不增加第三层 panel；标准 bottom editor 在 active state 中卸载；
- canvas 使用 node 内 absolute inset 覆盖媒体；
- canvas backing size = CSS client rect × `2`，只为复现 source DPR contract；
- 不增加 viewport clamp、page-level fixed overlay 或移动端重定位。

## 5. 风险边界

- 空态是低风险 clone slice；
- 任何 pointer drawing、save、download、upload、task、history 或 output node
  都超出本批授权；
- `closeAllPanels` 和 Escape 必须清理 active annotate，不能留下透明 canvas；
- Preview 与 annotate 互斥；打开任一状态都先关闭另一状态。
