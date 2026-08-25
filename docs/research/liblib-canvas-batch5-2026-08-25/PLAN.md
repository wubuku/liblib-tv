# LibTV 画布 Batch 5 计划：移动与复制事务

> 建档日期：2026-08-25  
> 原则：先复核已有行为，再实现能闭环的最小事务；不以推断补写原站事实。

## 1. 缺口盘点

| 候选缺口 | 当前克隆 | 证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 多选拖动 | React Flow 可能移动所有选中节点，但 drag stop 只显式收尾一个节点 | Batch4 的 `selectedNodeIds` + 当前 `onNodeDragStop` | 5 | 实现并验证 |
| group 拖动 | 使用 `parentId`，但没有专项验证 group/child 的相对位置与 history | 当前 store 数据契约 | 5 | 实现并验证 |
| 多选复制 | `Cmd/Ctrl+D` 只复制 `selectedNodeId` | 原站快捷键“复制节点和连线” + Batch4 多选 | 5 | 实现 |
| 带父子关系复制 | `duplicateNode` 可能保留旧 `parentId` | 当前 `duplicateNode` 实现 | 4 | 随多选复制修复 |
| Option/Alt+拖动复制 | 未实现 | 原站文案存在，流程未取得实时证据 | 4 | 暂缓 |
| L 快捷键连线 | 未实现 | 原站文案存在，端点选择流程未取得实时证据 | 4 | 暂缓 |
| Option/Alt+G 合并分镜组 | 未实现 | 原站文案存在，业务语义未取得实时证据 | 3 | 暂缓 |

## 2. 实施范围

### P0：移动事务

1. drag start 记录开始时的 graph snapshot 和移动集合；
2. drag stop 以 React Flow 当前最终节点状态为准，不重新覆盖其他已移动节点；
3. 多选拖动最多生成一个 history step；
4. group 拖动后 child 的相对位置保持稳定；
5. group/child undo、redo 后位置与 parentId 恢复一致。

### P0：选择集合复制

1. 增加 `duplicateSelectedNodes()`；
2. 单选快捷键复用同一入口；
3. 多选普通节点整体偏移 `40x40`；
4. 多选只复制选择集合内部的边，并将端点映射到副本；单选保留已有的所有关联边语义；
5. 复制 group 时连同其 children 一起复制，并重映射 `parentId`；
6. 复制结果作为一次 history 事务并整体选中。

## 3. 数据决策

- 复制偏移仍沿用已有 `40x40`，不改变单节点复制的视觉习惯；
- 多选复制边只保留 source 与 target 都在选择集合内的边，避免把外部图结构意外复制成重复边；单选沿用已有的所有关联边语义；
- 复制 group 时 group 和子节点一起复制；复制子节点但未选择其 group 时，按普通顶层节点复制并解除旧 `parentId`，避免产生孤儿引用；
- 位置以 React Flow 在当前 viewport 下写回 store 的最终值为准；
- history 仍按 graph snapshot 记录，不把 selection 和 viewport 写入 history。

## 4. 不做

- 不引入剪贴板 API；
- 不实现 Option/Alt+拖动；
- 不实现嵌套 group；
- 不重写原站 group 的视觉壳层；
- 不修改 FrameOS route/store；
- 不根据本批行为推断原站未观测到的 group 业务语义。

## 5. 验收标准

### 移动

- 多选两个顶层节点拖动后，两个节点都移动；
- drag stop 只新增一个 history step；
- `Meta+Z` 一次撤销整个拖动，`Meta+Shift+Z` 一次重做；
- group 拖动后 group 与 child 的绝对视觉位移相同；
- group 拖动后 child 相对 group 的坐标不变；
- group 拖动 undo/redo 后 parentId、位置和节点数一致。

### 复制

- 单选 `Meta+D` 行为不回归；
- 多选 `Meta+D` 节点数按选择数增加；
- 选择集合内部边按副本端点映射增加；
- 单选普通节点关联边复制结果保持兼容；group 选择遵循结构复制规则；
- 复制结果整体被选中，图片/视频单节点浮层不出现；
- `Meta+Z` / `Meta+Shift+Z` 对复制是单步恢复；
- 复制 group 及 children 不产生旧 parentId 引用。

### 回归

- `npm run check` 通过；
- `/` 桌面 `1440x900` 和移动 `390x844` 无横向溢出；
- `/frameos/canvas/demo` 构建和首屏不回归；
- 控制台错误为 `0`；
- 验证截图和脚本写入 `docs/design-references/` 与 `scripts/`。
