# 组件规格：LibTV Grouping

## 证据结论

原站快捷键面板直接展示：

- `成组`：`G`
- `合并分镜组`：`⌥G`
- `解组`：`⇧G`

原站结构化审计直接展示两个 group node，其中一个包含 `parent` class。但现有资料没有记录执行命令后的 DOM、子节点相对位置和组内移动规则。

因此本规格只定义一个可逆的 React Flow 原型数据关系，不把它描述成原站已复测的完整行为。

## 成组

触发：

- 选中至少两个普通节点；
- 按 `G`；
- 输入焦点在 `input`、`textarea` 或 `[contenteditable=true]` 时不触发。

事务：

1. 计算选中节点的绝对包围盒；
2. 外扩 `32px` 作为 group 边界；
3. 创建 `storyboard-group` 节点；
4. 将选中节点改为 `parentId: groupId`；
5. 将子节点位置改成相对 group 左上角的坐标；
6. 保留所有现有边，不自动添加 group 边；
7. 成组后只选择 group 节点。

限制：

- 已有 `storyboard-group` 节点不参与普通成组；
- 不创建嵌套 group；
- 选中少于两个普通节点时不产生任何变化。

## 解组

触发：

- 选中一个 group 节点，按 `Shift+G`；
- 或选中 group 的一个/多个子节点，按 `Shift+G`；
- 找不到 group 时不产生变化。

事务：

1. 找到目标 group；
2. 把每个子节点的相对坐标加上 group 绝对坐标；
3. 删除子节点的 `parentId`；
4. 删除 group 节点；
5. 保留所有现有边；
6. 选中解组后第一个恢复的子节点。

## History

- 成组是一个 graph snapshot；
- 解组是一个 graph snapshot；
- selection、面板和视口不入 history；
- undo/redo 后清除选择，避免引用已删除的 group 或 child。

## 视觉边界

默认 group 壳层采用当前已存在的图片组节点视觉作为低风险复用：

- `430x452` 只是默认尺寸，不是固定组尺寸；
- `rounded-[20px]`；
- `bg-white/10`；
- `border-white/10`；
- `z-index: -1001`；
- 标题为本地原型文案“组合节点”。

未来只有在重新取得原站分组交互截图后，才调整为更具体的组内排布和命令浮层。

