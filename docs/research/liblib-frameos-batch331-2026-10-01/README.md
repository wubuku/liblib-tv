# Batch 331（2026-10-01）：撤销栈按画布隔离（跨画布撤销会灌入上一张画布的节点）

## 结论一句话

撤销快照不记录来自哪张画布，而 `setBreadcrumb` 换画布时**只**清 `groups`/选中态、
**不重置** `past`/`future` → 在画布 A 上做的动作，可以在画布 B 上「撤销」，
把 A 的 nodes/edges/groups **整份灌进 B**。实测 B 从 0 节点变成 A 的 7 个节点。
已按画布隔离。

## 运行时证据（修复前）

```js
// 1) 在画布 A（7 节点）上 addNode → 产生一条 past 快照
afterAddOnA : { nodeCount: 8, pastDepth: 1 }
// 2) 切到画布 B（0 节点）
onB.bIds    : []
// 3) 在 B 上按一次撤销
afterUndoOnB: { bIds: ['text-1','text-2','video-1','video-2','video-3',
                       'image-1','image-2'] }   ← B 变成了 A 的 7 个节点
```

`reconcileGroups(prev.groups, prev.nodes)`（Batch 329 引入）在此**帮了倒忙**：
它拿着 A 的节点去收敛 A 的分组，一切自洽 —— 缺陷不在收敛逻辑，而在于
**根本不该把 A 的快照应用到 B**。

## 一个自我订正：首版探针漏判

第一版探针直接在空 `past` 上切画布再撤销，结论是 `VERDICT: B-clean`。
**这是漏判，不是修复生效** —— `past` 为空时 `undo` 本就是 no-op。
必须先在 A 上制造一条快照（`addNode`）才能复现。已把「先造快照」写进
探针与验证器的前置步骤，避免后人重蹈。

## 修复

1. 新增 `HistoryEntry` 类型，快照带 **`canvasKey`**（`project/scene/canvas`）；
   `pushHistorySnapshot` 统一写入当前画布 key。
2. **`setBreadcrumb` 换画布时清空 `past`/`future`** —— 撤销本就不该跨画布生效，
   这是语义上的正解。
3. `undo`/`redo` 遇到 `canvasKey` 不匹配的快照 → **拒绝并清空该侧栈**（兜底，
   覆盖运行中热切换等边界）。

`canvasKey` 缺失（Batch 331 之前的旧快照）按「与当前画布同源」处理，向后兼容。

## 验证器

`scripts/verify-frameos-batch331.py` — **19 项断言全 PASS，0 诊断**：

1. 换画布后 `past`/`future` 被清空；
2. 换画布后按撤销**不注入**上一张画布的节点（B 仍是 0 节点）；
3. 分组同样不跨画布泄漏；
4. `canvasData` 持久层未被污染（B 的 fixture 仍为空）；
5. 切回 A，A 的 fixture 基线节点一个不少、且不含 B 的节点；
6. **同画布内撤销/重做逐步正确**：undo1 撤分组、undo2 撤建节点、
   redo1 恢复节点、redo2 恢复分组；
7. 控制台/页面错误为 0。

第 6 项按真实栈深逐步断言，而非「一次撤销回到原状」——
setup 做了两个动作（`addNode` + `createGroup`），栈深 2，需要两步撤销两步重做。

证据：`runtime-audit.json`（本目录）。
复现探针：
- `scripts/probe-frameos-batch331-canvas-switch.py`（症状：节点被灌入另一张画布）
- `scripts/probe-frameos-batch331b-pollution.py`（含「先造快照」前置，避免漏判）

## 顺带记录的既有行为（非本批缺陷）

`canvasData` 只在 `setBreadcrumb` 时从 `MOCK_CANVASES` 写入，**不回写实时编辑**。
因此切走再切回，本地新增的节点与分组会消失。这是原型既有的 mock 边界
（本原型不实现持久化），**不在本批范围**，但验证器已按此正确的不变式书写断言，
以免后人误判为新缺陷。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 332：`canvasData` 不回写实时编辑 —— 切画布丢失本地改动。
  需先确认源站是否持久化画布内编辑（**源站不可访问时不得凭空发明**）；
  若按克隆一致性补齐，必须显式标注为 clone-only 决策。
