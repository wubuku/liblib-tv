# batch 741 — canvasStore 54 个命令的历史栈普查：**33 记账 / 17 只 set / 4 皆无**；拖动节点可撤销，但记账的不是搬运那条路

## 起点

739/740 证明了**删除能撤**（手柄删边、Delete 删节点各 push 1 条，undo 逐项精确）。
但那只是 54 个命令里的 2 个。本批把「哪些命令记账、哪些不记账」整个普查，
并查清一个没问过的问题：**拖动节点到底记不记账**。

全部读数来自 clone，**不碰源站**。

## 口径：三个数，不能揉成一个

| 口径 | 数 | 含义 |
|---|---|---|
| 命令总数 | **54** | store 对象 `canvasStore.ts:1020..4072` 的顶层函数键（9 个状态字段不算） |
| **记账** | **33** | 函数体内含 `pushHistory(` —— 每个都必然同时含 `set(` |
| **改 store 但不记账** | **17** | 有 `set(` 没有 `pushHistory(` |
| **两者皆无** | **4** | 2 个转发器 + 2 个纯 getter |
| `pushHistory` 调用点 | **33** | 与命令级 33 **逐个相等**（两个独立口径互证） |

### 静态扫描的第一版有三个错（都靠对账抓出来，不是靠重读源码）

1. **多行参数表的函数归错桶**。`addNodeAtFlowCenter: (` 这种参数跨 3 行的键被当成
   单行函数收尾，函数体因此落到**下一个**命令名下。后果：`addNode` 被算成「记账」
   （它一行 `pushHistory` 都没有），而真正记账的那 **12 个**多行参数函数
   （`addDerivedNode` / `createVideoContinuation` / `createSubtitleErase` /
   `createVideoFrameCapture` / `createDepthMotionCapture` / `createLongVideoProcess` /
   `createPictureEdit` / `createDirectorCapture` / `createDirectorAnimationExport` /
   `completeShotBreakdown` / `submitLibTVEditorSessionCommit` / …）**一个都没数到**。
2. **状态字段把命令吞了**。`projectName: "未命名工作区"` 这类字段**没有 `=>`**；
   扫描器一路读到 `:1030` 第一个 `=>` 才停 ⟹ 把 `setProjectName:1030` 整个吞掉。
   命令实为 **54** 个、不记账 **17** 个，不是 53 / 16。
3. **`pushHistory` 在 `:506` 是模块级函数定义，不是命令**。按行号区间配对会跨界。

修正后的解析器：**先扫到 `=>`（途中撞到新的顶层 key 就判定为状态字段并跳过），
再从箭头行做括号配平**，并在 `}));` 处停止。
声明区（`interface CanvasState` `:282..453`）**0 命中** `pushHistory`。

## 决定性读数

### ① 33 个记账命令里，2 个是**条件记账**

```
setNodes: (nodes, options?) => { … historyByCanvas:
      options?.recordHistory ? pushHistory(state.historyByCanvas, currentCanvas, options.historySnapshot)
                             : state.historyByCanvas }        canvasStore.ts:3408-3411
setEdges: 同构                                                   canvasStore.ts:3432-3435
```

⟹ **31 个无条件 + 2 个条件**。「33 个记账」这个数本身还要再拆一层。

### ② 「命令自己不记账」≠「用户拿不到撤销条目」

`addNode:1252` 与 `addNodeAtFlowCenter:1260` 归在「两者皆无」——一行 `set(` 都没有，
只 `get().addNodeAtPosition(...)`。但 `addNodeAtPosition:1577` 是记账的：

```
addNode('text')  ⟹  节点 10→11、past 0→1
```

⟹ **静态桶只描述「这个函数自己写不写历史」，不描述用户可见行为。**

### ③ headline：**拖动节点可撤销，但记账的不是搬运的那条路径**

第一次跑出来的读数是 `past 0→1`，与「不记账」的推断相反。当时只把结论硬写进
print 文案、没去查**谁记的账**。给 54 个命令套一层调用日志的探针给出真相：

| 阶段 | 走的命令 | 记账？ |
|---|---|---|
| 拖动途中（× 11） | `routeReactFlowChanges:3535` → `APPLIED_TRANSPORT`（`libtvReactFlowChangeRouting.ts:395`） | **每次都真写 store，一次都不记账** |
| 拖动**停下**（× 1） | `page.tsx:1501 onNodeDragStop` → `setNodes(nodes, {recordHistory:true, historySnapshot})` | **这唯一一次才记账** |

探针原样读到的记账参数（`historySnapshot` 里就是**拖动前**的位置 `x:2112, y:656`）：

```json
{"recordHistory":true,"historySnapshot":{"nodes":[{"id":"g-245IDFh8sB","position":{"x":2112,"y":656},…
```

⟹ **一次拖动 = 11 次中间路由零记账 + 停下时压成 1 条**。
`transaction.snapshot` 是 `onNodeDragStart` 时 armed 的拖动前快照，
所以 undo 用它恢复时**坐标逐项精确**（10/10 全回位，`future=1`）。
多选拖动（选中 2 个一起拖）同样**只记 1 条**，undo 后两个都逐项回位。

**`moved` 守卫**：按下 → 不动 → 松手，坐标真变 0 个、`past` 0→0，一条历史都不留。

### ④ `removeCanvas` 删历史桶，而它自己不记账

```
canvasStore.ts:1095  historyByCanvas: Object.fromEntries(
                       Object.entries(get().historyByCanvas).filter(([canvasId]) => canvasId !== id))
```

实测（canvas-2 是对照组，各记 1 条；临时画布 canvas-3 也记 1 条）：

| | `historyByCanvas` 的键 | canvas-2 条目数 |
|---|---|---|
| 删之前 | `{canvas-2: 1, canvas-3: 1}` | 1 |
| `removeCanvas(canvas-3)` 之后 | `{canvas-2: 1}` | **1（没被动）** |

⟹ 删一张画布 = 连它的撤销历史一起消失，而删画布这个动作**自己也没有条目可撤**
（它落在「17 只 set」桶里）。canvas-3 同时进了 `removedCanvases`（回收站）。

### ⑤ `undo()` 只恢复 `nodes`/`edges`，从不恢复画布名

```
canvasStore.ts:3688  canvases: state.canvases.map(c => c.id === activeCanvasId
                           ? { ...c, nodes: previous.nodes, edges: previous.edges } : c)
```

实测：记账一次（`past=1`）→ 改名 → `undo()` ⟹ 节点 11→10（**图撤了**），
名字仍是 `'b741 改过的名字'`（**改名没撤回来**）。

## 17 个「改 store 但不记账」的命令

画布管理 8 个：`setProjectName:1030`、`addCanvas:1036`、`restoreCanvas:1051`、
`purgeRemovedCanvas:1069`、`removeCanvas:1075`、`renameCanvas:1101`、
`setActiveCanvas:1109`、`duplicateCanvas:1124`
选区 4 个：`selectNode:3439`、`selectNodes:3464`、`selectEdges:3484`、`selectElements:3500`
视图与出图 1 个：`selectNodeOutput:3740`
运行时写入 1 个：`routeReactFlowChanges:3535`（**拖动搬运走它**，见 ③）
视口 1 个：`setViewport:3727`
历史自身 2 个：`undo:3673`、`redo:3700`

## 撤回的三条

- **「拖动节点不记账 / 移动节点不可撤销」** —— 读数是 `past 0→1`，与推断相反。
  记账发生在 `setNodes(recordHistory)` 上，不发生在 `routeReactFlowChanges` 上。
- **「53 个命令 / 16 个不记账」** —— 状态字段 `projectName` 把 `setProjectName` 吞了。
- **「多行参数表的函数归错桶」** —— 见「静态扫描的第一版有三个错」第 1 条。

另外撤回一处**没有证据的归因**：C6c(b) 里「挪 8px 再精确回同一屏幕原点」后节点坐标
仍差 3.8 个流程单位（@zoom 0.526 ≈ 2 屏幕像素），第一版把它归因于 `snapToGrid`。
残余不是 20 的倍数、起点 2112 也不是 ⟹ **这个归因没有证据**。
那次拖动确实真动了，记账是对的；**成因未取证**。

## 判据（13/13）

| | 判据 | 读数 |
|---|---|---|
| C1 | 54 命令 = 33 记账 / 17 只 set / 4 皆无；33 个调用点逐个对平；声明区 0 命中 | `{fns:54, both:33, setonly:17, neither:4, call_sites:33}` |
| C2 | `addNode` 是转发器；`setProjectName` 被吞后才找回来；`createStoryScriptPair` 确实记账 | 见 runtime-audit |
| C3 | `setNodes`/`setEdges` 条件记账，其余 31 个无条件 | `conditional: ["setNodes","setEdges"]` |
| C4 | 转发器 `addNode`：节点 +1 且 `past` 0→1 | `{n0:10, n1:11, p0:0, p1:1}` |
| C5 | 纯选择 `selectNode`：`past` 不变（基线 0） | `{p0:0, p1:0}` |
| C6 | 一次拖动 = 多次 `routeReactFlowChanges`(全不记账) + 1 次 `setNodes(recordHistory)` | `routeCalls:11, setNodesCalls:1, past 0→1` |
| C6b | 拖动后 `undo()`：坐标逐项精确回拖动前 | `undoExact 10/10, future 1` |
| C6c | 空拖（按下-不动-松手）：一条历史都不留 | `stillMoved 0, past 0→0` |
| C6d | 多选拖动：仍只记 1 条，undo 后全部逐项恢复 | `selected 2 个, past 0→1, undoExact 10/10` |
| C7 | `updateNodeData`：`past` +1 | `{p0:0, p1:1}` |
| C8 | `setNodes`：`recordHistory` 开关真的分两路 | `{noFlag:0, flag:1}` |
| C9 | `removeCanvas`：只删那一桶（对照组 canvas-2 不受影响）、画布进回收站 | `{canvas-2:1, canvas-3:1} → keys ['canvas-2']` |
| C10 | 改名 + `undo()`：图撤了、名字没撤回来 | `nodes 11→10, name 不变` |

## 不声称

- 不声称源站对移动 / 改名 / 删画布是否记账 —— 未取证。
- 不声称拖动记账（1 次拖动压 1 条）是缺陷还是有意设计 —— 未取证。
- `MAX_HISTORY = 50` 的上限行为（超过 50 条时截断）未测。
- 17 个不记账命令只逐条验了 `selectNode` / `renameCanvas` / `removeCanvas` 三条。
- `onNodeDragStop` 里 Batch 436 的跨画布守卫（armed 基线画布 ≠ 当前画布 ⟹ 不记账）未测。
- 拖动中途切画布、拖动中改尺寸（`dimensions` 变化走 `hasTransport` 的另一半）未测。
- 「挪出去再回同一屏幕原点」为何留下 3.8 个流程单位的残余 —— 成因未取证。

## 验收器

`scripts/verify-liblib-batch741.py` — 静态普查 + 7 组运行时读数，
两轮连跑逐字段一致。运行时读数全部取自 clone 的 `window.__libtv_store`。
