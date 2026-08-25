# 组件规格：LibTV 选择集合复制

## Goal

把快捷键面板中“复制节点和连线 `D`”与 Batch4 的多选状态接起来，使命令作用于当前选择集合，而不是只作用于 primary selected node。

## Interaction model

- 触发：画布焦点下 `Meta/Control + D`；
- 输入焦点在输入框、文本框或 contenteditable 时不触发；
- 单选和多选共用 `duplicateSelectedNodes()`；
- 复制完成后副本成为新的整体选择；
- 一次复制只产生一个 graph history step。

## Graph rules

### 普通节点

- 每个选中节点复制一份；
- position 在画布坐标中偏移 `{ x: 40, y: 40 }`；
- 多选时仅复制 source/target 均在选择集合内的边；
- 单选普通节点时保留已有行为，复制该节点的所有入边/出边，未选中的另一端仍指向原节点；
- 新边 source/target 映射到对应副本 ID。

### group

- 若选择集合包含 group，则自动纳入该 group 的直接 children；
- group 与 children 一起复制；
- 复制后的 children 使用新 group ID；
- 选择集合只包含 child、未包含 group 时，复制 child 为顶层节点并清除旧 parentId；
- 不创建跨副本连接到原始节点的边。
- 选择 group 时只复制 group/children 内部边，不把 group 内部节点的边复制到原节点。

## Visual rules

- 不添加新的复制提示条；
- 副本选中后遵循现有图片/视频单节点浮层规则；
- 多个副本同时选中时隐藏图片/视频单节点编辑浮层；
- 不改变已有 `40x40` 单节点副本偏移。

## Evidence boundary

原站直接证据只覆盖快捷键命令名称；上述集合边界、组复制和偏移是为了让当前前端原型形成可逆、可测试的编辑器事务，不应记录为原站内部实现事实。
