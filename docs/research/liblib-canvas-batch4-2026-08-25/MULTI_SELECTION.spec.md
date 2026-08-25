# 组件规格：LibTV Multi-Selection

## 目标

把当前只有单一 `selectedNodeId` 的画布选择模型扩展为“多选 + 主选中节点”，同时不破坏图片/视频节点的单选浮层。

## 状态契约

```ts
selectedNodeIds: string[];
selectedNodeId: string | null; // 兼容既有单节点面板的主选中节点
```

- `selectedNodeIds` 为空时，`selectedNodeId` 必须为 `null`；
- `selectedNodeIds` 只有一个元素时，该元素就是 `selectedNodeId`；
- 多选时 `selectedNodeId` 是最后一次加入选择的节点；
- 点击空白清空两个字段；
- 切换画布、undo、redo、删除后清除无效选择；
- selection 不进入 history。

## 交互

### 单击

- 普通单击节点：只选择该节点；
- `Meta`/`Control` 单击：切换该节点的选择状态；
- 点击空白：清空选择；
- 选择多个节点时，不显示单节点 ImageToolbar、ImageEditPanel 或 VideoGenerationPanel。

### 框选

- `V` 选择工具下，拖动画布空白区域进入框选；
- 使用 React Flow `SelectionMode.Partial`，节点与框选区域有部分交集即可进入选择；
- `H` 抓手工具下不进入框选；
- 框选完成后通过 `onSelectionChange` 写回 store。

## 视觉

- 继续使用现有节点各自的 selected 边框；
- 不新增原站未证实的多选外框、批量浮动工具条或右键菜单；
- group 节点被选中时使用现有 cyan 边框和轻微光晕。

## 事件边界

- React Flow 的 selection change 由 `onSelectionChange` 接收；
- `onNodesChange` 处理位置、删除和尺寸变化时不得用闭包旧节点覆盖新增节点；
- store 内部节点对象不保存 selection 作为持久事实，渲染层按 `selectedNodeIds` 派生 `selected`。

