# LibTV 画布 Batch 4：多选与分组命令

> 建档日期：2026-08-25  
> 当前状态：研究规格已完成，源码实施进行中  
> 目标：补齐 LibTV 画布中高价值的多选、框选、成组/解组命令闭环。

## 本批决策

本批只实现能够由现有证据和当前 React Flow 架构共同支撑的能力：

1. 框选和多选节点；
2. 保留一个主选中节点，兼容现有图片/视频浮层；
3. `G` 成组；
4. `Shift+G` 解组；
5. 成组/解组进入当前画布的 undo/redo history；
6. 快捷键面板恢复已经被原站直接展示、且本批实际可用的命令。

本批暂不实现：

- `Option/Alt+G` “合并分镜组”；
- `L` 连线快捷键；
- `Option/Alt+拖动` 节点复制和创建副本；
- 未被实时观察到的分组弹出层、自动排列、组内缩略图和组标题编辑；
- 锁定、隐藏、真实系统剪贴板。

## 文档索引

| 文档 | 用途 |
|---|---|
| [`PLAN.md`](PLAN.md) | 缺口、证据、价值排序和验收标准 |
| [`MULTI_SELECTION.spec.md`](MULTI_SELECTION.spec.md) | 多选/框选的状态与交互契约 |
| [`GROUPING.spec.md`](GROUPING.spec.md) | 成组/解组的数据关系、快捷键和 history 边界 |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | 本批实际改动、验证结果和接力记录 |

## 证据边界

### 直接原站证据

- `docs/research/liblib-live-2026-08-25/panel-audit.json` 的快捷键面板文本直接包含：
  - 成组 `G`；
  - 合并分镜组 `⌥G`；
  - 解组 `⇧G`；
  - 连线 `L`；
  - 复制节点和连线 `D`；
  - 新建节点 `Tab`；
  - 节点复制 `Option+拖动`；
  - 创建副本 `Option+拖动`。
- `docs/research/liblib-live-2026-08-25/canvas-audit.json` 和 `full-canvas-audit.json` 直接记录了两个 `react-flow__node-group`：
  - 图片组：`430x452`、圆角 `20px`、半透明背景；
  - 视频组：`722x460`、圆角 `4px`、`#212121` 背景；
  - 其中一个节点带有 `parent` class。

### 当前无法直接证明的行为

现有审计没有保存“选择多个节点后点击成组”的 DOM 变化、组内子节点相对坐标、组移动联动、解组后的边界计算或“合并分镜组”的交互过程。因此这些行为在本批以可逆、最小的前端原型契约实现，不声称是原站已验证的像素级事实。

## 当前克隆的起点

- `canvasStore` 只有 `selectedNodeId`；
- `page.tsx` 把 React Flow 的 `selectionOnDrag` 打开，但渲染时强制所有节点按单选重建 `selected`；
- 已有 `storyboard-group` 类型和两个静态组节点；
- history 已支持图快照，但 selection 不应进入 history。

## 接力入口

下一位 agent 先读本 README、`PLAN.md`、`MULTI_SELECTION.spec.md` 和 `GROUPING.spec.md`，再读：

- `src/store/canvasStore.ts`
- `src/app/page.tsx`
- `src/components/nodes/StoryboardGroupNode.tsx`
- `docs/research/liblib-canvas-batch3-2026-08-25/IMPLEMENTATION.md`

