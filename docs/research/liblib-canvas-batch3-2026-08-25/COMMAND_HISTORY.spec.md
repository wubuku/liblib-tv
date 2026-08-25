# 组件规格：Canvas Command History

## Overview

画布 history 是跨节点类型的命令基础。它记录当前画布的 `nodes` 和 `edges` 图快照，不记录选中态、面板显隐和普通视口移动。

## State Contract

```text
historyByCanvas[canvasId] = {
  past: GraphSnapshot[],
  future: GraphSnapshot[]
}
GraphSnapshot = {
  nodes: Node[],
  edges: Edge[]
}
```

- 每个画布独立 history；
- `past` 最多保留 50 个快照；
- 新命令写入 `past` 并清空 `future`；
- 撤销把当前图放入 `future`，恢复 `past` 最后一个图；
- 重做把当前图放入 `past`，恢复 `future` 第一个图；
- 恢复图后清除选中节点，避免选中浮层引用已删除节点；
- `setViewport`、`selectNode`、UI 面板开关不入栈；
- React Flow 的持续 selection change 不入栈；
- 节点拖动只在 `onNodeDragStop` 入栈一次。

## Command Boundaries

| 命令 | 是否入栈 | 备注 |
|---|---:|---|
| 添加节点 | 是 | 包括右键坐标添加 |
| 添加派生节点 | 是 | 节点和新边作为一个事务 |
| 删除节点 | 是 | 关联边一起删除 |
| 复制节点 | 是 | 节点和可选关联边一起复制 |
| 添加/删除连线 | 是 | 单次操作一个快照 |
| 更新节点数据 | 是 | 面板提交或文本编辑结束时 |
| 拖动节点 | 是 | 只在结束时记录 |
| 整理画布 | 是 | 一次整理作为一个事务 |
| 选择节点/取消选择 | 否 | 纯 UI 状态 |
| 缩放、平移、适应屏幕 | 否 | 不污染编辑历史 |
| 打开/关闭面板 | 否 | 不污染编辑历史 |

## Visual Contract

本批不新增强制的历史浮层。撤销/重做通过快捷键和右键命令闭环；未来若原站实时证据确认存在可见 history dock，再单独提取几何。

## Failure Boundaries

- 刷新页面后 history 丢失，这是当前项目的内存原型边界；
- 不序列化函数、DOM 或 React Flow 实例；
- 不把局部图片/视频编辑器的按钮自动映射到画布 history。

