# Batch 343（2026-10-01）：边完整性不变式（与 Batch 341 同构）+ 持久损坏的放大效应

## 结论一句话

边有一条和分组完全同构的不变式——「每条边的两端都指向存活节点」——而剪边只
存在于 `removeNode` 一处。绕过它的路径留下的悬空边**被 Batch 333 的持久化写进
localStorage 并在刷新后存活**：一个内存里的潜在缺陷被**固化成了持久损坏**。
收进同一个写出口后，悬空边归零，且已写坏的存档会被**自动治愈**。

## 运行时证据（修复前）

探针 `scripts/probe-frameos-batch343-edge-integrity.py`：

```
[对照组 removeNode] edges 5 → 3, dangling=[]                      ← 剪了
[路径   setNodes]   edges 3 → 3, dangling=[e-video1-image1,
                                            e-video1-video3]      ← 没剪
  渲染出的 .react-flow__edge: 0 (边 3)                            ← 渲染不出来
持久化里的悬空边: ['e-video1-image1', 'e-video1-video3']           ← 写进去了
刷新后 dangling: 仍在                                             ← 活过了刷新
判定: setNodes_leaves_dangling=true, dangling_survives_reload=true
```

React Flow 对指向不存在节点的边**一条都渲染不出来**（0 条），所以用户看不见；
但它在 store 里、在 localStorage 里、跨刷新还在。**看不见的损坏比看得见的错更危险**
——它会一直累积，且没有自愈路径。

## 同一路径上的第三个问题：删了不可撤销

`setNodes` 是 `set({ nodes })`，**不 pushHistory**。所以面板删除：

| | 悬空边 | 入撤销栈 | 选中态清理 |
|---|---|---|---|
| `removeNode` | ✅ | ✅ | ✅ |
| 手写 `setNodes(filter)` | ❌ | ❌ | 手搓 |

即面板把手写了一遍 `removeNode` 已有的一切语义，还少了三样。

## 修复 1：并入 Batch 341 建立的同一个出口

`enforceGroupGeometry` → **`enforceGraphInvariants`**，现在收敛两条不变式：

1. 分组盒 == 存活成员包围盒 + 28（Batch 341）
2. 每条边的两端都指向存活节点（Batch 343）

副产品：**已经写坏的存档会被治愈** —— `restorePersistedCanvas()` 载入时同样经过
这个出口，旧存档里的悬空边在加载时就被清掉了。

## 修复 2：面板改用 `removeNode`

```diff
- setNodes(nodes.filter((n) => n.id !== selectedNode.id));
+ removeNode(selectedNode.id);
```

与其逐条补齐悬空边/历史/选中态，不如直接用本来就有这三条语义的 action。
**这是删代码，不是加代码** —— 和 Batch 328/341 的方向一致：
真正的问题一直是「同一件事被手写了好几遍」。

## 验证器

`scripts/verify-frameos-batch343.py` — **13 项断言全 PASS，0 诊断**：

1. 对照：`removeNode` 仍剪边（防回归）；
2. `setNodes` 路径不留悬空边；
3. 受害节点的边被剪掉；
4. **无关的边一条不少**（防过度剪枝）；
5. 面板删除（真实 UI 点击）后无悬空边；
6. 面板删除**入了撤销栈**（删除可撤销）；
7. 撤销后节点与它的边**一起回来**；
8. 持久化里没有悬空边；
9. 刷新后没有悬空边；
10. 刷新前后节点数/边集合**一致**；
11. 拖拽节点后边集合一字不差（纯位置变更不得动边）；
12. 诊断零错误。

**变异测试**：注释掉边收敛那三行后，验证器如期失败于
`setNodes:no-dangling (dangling=['e-text2-image1'])`。

写验证器时我把 `reload:nodes-restored` 改掉了：最初拿**初始 fixture 的 7 个节点**
当基准，但那时已经删过两个节点，断言把「删没删」和「刷新丢没丢」两件事混在一起。
改成拿**刷新前**的快照做基准 —— **断言要绑真实性质，不绑一个会过期的常数**
（Batch 208 的教训，第二次用上）。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch343-edge-integrity.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- `FrameosNodeEditPanel` 的「复制节点」「锁定位置」两个 `ActionButton` 仍无
  onClick（空壳），且整面板只在 `isDebugMode` 下渲染而 `toggleDebugMode`
  全仓无 UI 入口 —— 属源站对齐问题，先记录不动。
- store 的 `generations` 字段**从未被写入也从未被读取**（死状态），
  `startGeneration` 只写 `currentGeneration`。
