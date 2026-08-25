# LibTV 画布 Batch 5：移动与复制事务

> 建档日期：2026-08-25  
> 状态：规划、实施、专项验证和完整工程检查完成  
> 目标：在 Batch4 的多选/分组基础上，补齐最容易被真实编辑操作击穿的移动与复制闭环。

## 本批结论

Batch4 已经把选中集合、成组、解组和批量删除接通，但页面层的拖动收尾仍以一个 `node` 为单位，节点复制快捷键也只读取 `selectedNodeId`。这会导致：

- 多选拖动可能在数据层与视觉层不一致，或产生重复 history；
- 拖动 group 时无法明确保证子节点与 group 的相对关系；
- 多选后执行 `Cmd/Ctrl+D` 只复制主选中节点，用户看到的选择集合与实际命令范围不一致；
- 复制带 `parentId` 的节点时，旧父节点 ID 可能被错误保留。

本批只修复这些已有交互的事务边界，不新增没有实时原站证据的视觉或业务语义。

## 证据分层

### 直接原站证据

- 原站快捷键面板显示“复制节点和连线 `D`”；
- 原站快捷键面板显示成组、解组等选择集合命令；
- 原站是 React Flow 风格的可拖动画布，节点和连线构成统一图。

### 当前代码证据

- `page.tsx` 在 `onNodeDragStart` 记录 graph snapshot，在 `onNodeDragStop` 写入 history；
- `canvasStore.duplicateNode()` 只接收一个 `nodeId`；
- Batch4 新增 `selectedNodeIds`，但 `Cmd/Ctrl+D` 仍读取 `selectedNodeId`；
- group/child 使用 `parentId` 与相对位置表达。

### 未决策/不进入本批

- `Option/Alt+拖动` 的复制触发时机与视觉反馈；
- `L` 连线快捷键的起止端点选择流程；
- `Option/Alt+G` 合并分镜组的业务语义；
- 原站 group 拖动的具体 DOM 实现和组壳层细节。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、价值排序、范围和验收标准
- [`MULTI_MOVE.spec.md`](MULTI_MOVE.spec.md)：多选/group 拖动与 history 契约
- [`DUPLICATE_SELECTION.spec.md`](DUPLICATE_SELECTION.spec.md)：选择集合复制契约
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和遗留风险

## 接力入口

后续会话先读取本目录，再读取：

1. `docs/research/liblib-canvas-batch4-2026-08-25/IMPLEMENTATION.md`
2. 本批 `PLAN.md`
3. 本批 `IMPLEMENTATION.md` 的最后状态
