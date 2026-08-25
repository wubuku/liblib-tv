# Video Group Parenting Spec

## 1. 原站直接证据

### DOM class

`full-canvas-audit.json`：

```text
g-EFbbHpwq5w:
react-flow__node react-flow__node-group nopan selectable parent draggable

g-245IDFh8sB:
react-flow__node react-flow__node-group nopan selectable draggable
```

视频组有 `parent`，图片组没有。

### xyflow v12 机制

当前依赖源码 `@xyflow/react` 的 `NodeWrapper`：

```text
isParent = parentLookup.has(id)
className.parent = isParent
```

`@xyflow/system` 的 `parentLookup` 只在遍历到带 `userNode.parentId` 的 child 时写入。

因此原站视频组的 `.parent` 不是视觉命名，它证明至少有一个节点以该组 ID 作为 `parentId`。

### 坐标

原站结构化审计：

```text
视频组绝对位置 = (2374, -12)
失败视频绝对位置 = (2436, 50)
差值 = (62, 62)
```

尺寸：

```text
视频组 = 722 x 460
失败视频 = 622 x 350
```

child 以 `(62,62)` 放入 parent 后：

```text
right remainder = 722 - 62 - 622 = 38
bottom remainder = 460 - 62 - 350 = 48
```

该几何与原站组内卡片视觉一致。

## 2. Clone 数据合同

```ts
{
  id: "g-EFbbHpwq5w",
  type: "storyboard-group",
  position: { x: 2374, y: -12 },
}

{
  id: "v-UGQZzZOpbv",
  type: "video",
  parentId: "g-EFbbHpwq5w",
  position: { x: 62, y: 62 },
}
```

- parent 必须出现在 child 之前，满足 xyflow v12 的 adoption 顺序；
- 不设置 `extent: "parent"`；
- child 的 DOM transform 仍是计算后的绝对 `(2436,50)`，与原站审计一致；
- 图片组继续没有 child。

## 3. 移动与 History

### 拖动 parent

- React Flow 只更新 parent 的 `position`；
- child 的相对 `position` 保持 `(62,62)`；
- child 的 `positionAbsolute` 随 parent 改变；
- 页面 drag transaction 记录 parent 的移动；
- undo/redo 恢复 graph snapshot 后，child 绝对位置自动恢复。

### 拖动 child

- 只更新 child 的相对 `position`；
- parent 不移动；
- 本批不设置 extent，因此不限制 child 是否能离开 parent 边界；
- 一次 child drag 仍是一个 history step。

## 4. 整理

`organizeLiblibNodes()`：

- 顶层视频组使用 Batch7 的 source-like 位置；
- child 不进入已知绝对位置映射或 fallback；
- child 保持相对 `(62,62)`；
- viewport bounds 使用 parent hierarchy 计算 child 的绝对位置。

Batch7 文档中的失败视频绝对候选应在本批后理解为：

```text
organized video absolute = organized group position + (62,62)
```

而不是独立写入的顶层坐标。

## 5. 重新成组

当前 clone 的 `G` 是前端原型命令。为了让已有 child 仍能参与：

1. 对每个选中普通节点递归计算当前绝对位置；
2. 用绝对包围盒创建新 group；
3. 将选中节点的 `parentId` 改为新 group；
4. 用 `absolutePosition - newGroup.position` 得到新相对坐标；
5. 原 parent 保留；若失去唯一 child，则成为空组；
6. 不创建嵌套 group。

这是 clone 兼容规则，不声称是原站 `G` 的内部实现。

## 6. 删除

删除一个 group 时必须展开其所有 descendants：

```text
requested delete IDs
  -> recursively include node.parentId in delete IDs
  -> remove nodes
  -> remove edges touching any removed node
```

- 删除 child 不自动删除空 parent；
- 批量删除与单节点删除使用同一 descendant 规则；
- history 保存删除前完整 graph；
- undo 恢复 parent、children 和 edges。

这是受控图数据的完整性要求。

## 7. 复制与派生

### 复制 group

- 自动纳入 descendants；
- parent 与 child ID 都更新；
- copied child 指向 copied parent；
- child 保持相对 position。

### 单独复制 child

- parent 不在复制集合时，副本转成顶层节点；
- 副本绝对位置为原 child 绝对位置加 `(40,40)`；
- 清除旧 `parentId` 和 `extent`；
- 保留 Batch5 的单节点关联边复制语义。

### 派生节点

- `addDerivedNode` 使用 source 的绝对世界位置；
- 新派生节点仍创建为顶层节点；
- 避免把 child 的相对 `(62,62)` 错当成画布绝对坐标。

## 8. 证据边界

直接原站事实：

- 视频组有 `.parent`；
- 图片组没有 `.parent`；
- 两个绝对坐标与尺寸；
- 当前页面使用 React Flow class 约定。

当前 clone 决策：

- 不设置 extent；
- 级联删除；
- parented child 重新成组；
- 派生节点为顶层；
- history 与复制事务的具体边界。

