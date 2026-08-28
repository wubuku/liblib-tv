# 组件规格：LibTV Marquee Selection

> 历史 clone-only 规格：本页记录 Batch 6 曾经实施的空白框选入口，
> 不再是当前 LibTV parity 合同。2026-08-28 登录态源站测试中，`V` 下空白
> 左键拖动是 no-op，当前实现已关闭 `selectionOnDrag`。请以
> [`docs/CANVAS_NAVIGATION.md`](../../CANVAS_NAVIGATION.md) 和
> [`Batch 77 source audit`](../liblib-canvas-batch77-2026-08-28/SOURCE_NAVIGATION_AUDIT_2026-08-28.md)
> 为当前行为入口。

## Historical Goal

恢复选择工具下的空白拖动框选，使 Batch4 的多选/成组命令有可重复的鼠标入口。

## Dependency fact

xyflow v12 当前实现：

```text
_selectionOnDrag = selectionOnDrag && panOnDrag !== true
```

因此不能同时把 `panOnDrag` 固定为 `true` 并声称空白左键拖动用于框选。

## Historical Interaction Contract

### Select mode (superseded)

- `canvasTool === "select"`；
- 未按 Space；
- 空白左键拖动显示 `.react-flow__selection`；
- `SelectionMode.Partial`：节点与框选区域部分相交即可进入选择；
- viewport 不应随本次空白拖动平移。

### Pan mode

- `canvasTool === "pan"` 或 Space 临时抓手；
- 空白左键拖动平移；
- 不显示 selection rectangle；
- 不改变 `selectedNodeIds`。

## Selection state

- `onSelectionChange` 继续写入 `selectedNodeIds`；
- 单选浮层只在选择集合大小不超过 1 时显示；
- selection 本身不进入 graph history。

## Historical Verification

- 自动化在 select 模式拖出覆盖目标节点的矩形；
- 检查 selection drag 期间出现 `.react-flow__selection`；
- 松开后检查至少目标节点 selected；
- 记录 viewport/节点屏幕位置，确保 select 框选没有平移；
- 再用 H/Space 执行同样 pane drag，检查 viewport 确实平移。

## Current Replacement

- `V` 下节点本体仍可拖动；
- `V` 下空白左键拖动不平移、不显示 `.react-flow__selection`；
- 中键、`H` 左键和 `Space` 左键分别承担源站已核实的平移入口；
- 当前 focused verifier 是 `scripts/verify-liblib-batch77.py`。
