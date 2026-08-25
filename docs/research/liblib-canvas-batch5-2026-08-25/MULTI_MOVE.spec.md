# 组件规格：LibTV 多选与分组移动事务

## Goal

让 React Flow 的移动事件与 `canvasStore` 的 graph history 保持一致。用户拖动一个节点、多个节点或 group 时，视觉移动范围和一次撤销的范围必须相同。

## Interaction model

- 选择工具下拖动节点；
- React Flow 在拖动期间持续发送 position changes；
- store 可在拖动期间接收临时位置；
- drag stop 只负责用拖动开始前的 snapshot 记录一次事务；
- 不记录 viewport 和 selection。

## Required behavior

### 多选顶层节点

假设拖动前选择集合为 `A`、`B`：

1. 两个节点都收到相同的画布位移；
2. 拖动结束时 store 保留 `A`、`B` 的最终 position；
3. history 只新增一个拖动前 snapshot；
4. undo 恢复 `A`、`B` 的旧 position；
5. redo 恢复 `A`、`B` 的新 position。

### group

假设 group `G` 有 children `A`、`B`：

1. 拖动 `G` 后，`G` 与 `A`、`B` 的绝对位移一致；
2. `A.position`、`B.position` 仍是相对 `G` 的坐标；
3. group 的 parentId 不被清除；
4. undo/redo 不把 child 平移两次；
5. 不在节点组件内创建额外的固定定位浮层。

## Data contract

```ts
interface DragTransaction {
  snapshot: GraphSnapshot;
  nodeIds: string[];
}
```

`nodeIds` 用于记录审计和测试意图；最终位置以当前 store graph 为准，不手工根据鼠标 delta 重算 React Flow 已处理的父子关系。

## Evidence boundary

本规格是对当前 clone 的事务修复，不声称已经从原站 DOM 中提取出内部 group 拖动算法。原站只提供“画布节点可编辑/可移动”的产品级证据。

