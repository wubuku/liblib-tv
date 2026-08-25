# 组件规格：LibTV Marquee Selection

## Goal

恢复选择工具下的空白拖动框选，使 Batch4 的多选/成组命令有可重复的鼠标入口。

## Dependency fact

xyflow v12 当前实现：

```text
_selectionOnDrag = selectionOnDrag && panOnDrag !== true
```

因此不能同时把 `panOnDrag` 固定为 `true` 并声称空白左键拖动用于框选。

## Interaction contract

### Select mode

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

## Verification

- 自动化在 select 模式拖出覆盖目标节点的矩形；
- 检查 selection drag 期间出现 `.react-flow__selection`；
- 松开后检查至少目标节点 selected；
- 记录 viewport/节点屏幕位置，确保 select 框选没有平移；
- 再用 H/Space 执行同样 pane drag，检查 viewport 确实平移。

