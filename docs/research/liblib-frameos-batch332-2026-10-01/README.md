# Batch 332（2026-10-01）：canvasData 回写实时编辑（切画布不再丢弃本地改动）

## 结论一句话

`setBreadcrumb` 换画布时用 `MOCK_CANVASES` 的 fixture 覆盖目标画布，
**从不把离开画布的实时 nodes/edges/groups 写回 `canvasData`** → 本地新增、
移动、删除的节点和分组，在切走再切回后**全部丢失**。已修为切走前写回。

## 运行时证据（修复前）

```js
A='测试作品/测试项目/画布 1'  B='测试作品/测试项目/画布 3'
start     : 画布 A, 7 节点
afterAdd  : 画布 A, 8 节点      ← 在 A 上新增了一个节点
onB       : 画布 B, 0 节点      ← 切到 B
backOnA   : 画布 A, 7 节点      ← 切回 A，新增的节点消失了
```

不只是新增：移动的坐标、删除的结果、分组、连线同样在往返后回到 fixture 状态。
用户在 A 上编辑 → 切到 B 看一眼 → 切回 A，**编辑内容凭空消失**，且没有任何提示。

## 修复

`setBreadcrumb` 切走前把当前实时状态写入 `canvasData[prevKey]`：

```ts
const canvasData = {
  ...state.canvasData,
  [prevKey]: { nodes: state.nodes, edges: state.edges, groups: state.groups },
};
const data = canvasData[key] ?? MOCK_CANVASES[key] ?? { nodes: [], edges: [] };
```

- 目标画布**优先读已保存数据**（含本次切走保存的），未编辑过的画布仍回落到 fixture；
- `canvasData` 类型新增可选 `groups` —— 分组属于画布，一并保存与恢复。

## CLONE_DECISION

源站是否持久化画布内编辑**未采样**（源站被「确定你不是机器人」阻塞，
见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。本原型此前根本不跨画布保存编辑，
属于**内部数据丢失**，任何交互式原型都不应有。本批修的是这个洞，
**不是源站对齐声明**；恢复访问后仍需复核源站真实语义。

## 一个连带影响：Batch 331 验证器需要更新

331 的第 4 项断言「切回 A 后节点数 == 7（fixture 基线）」，
在 332 修好后**必然失败** —— 因为新增的节点现在正确地存活了（8 个）。
这不是回归，而是**旧断言描述的是缺陷本身**。

已把 331 的该项改成它真正关心的不变式：「**不混入 B 的节点**」
（跨画布污染的判据），并去掉对 fixture 基线数的硬编码。
教训：**断言要绑定真实性质，不要绑定缺陷的副作用。**

## 验证器

`scripts/verify-frameos-batch332.py` — **17 项断言全 PASS，0 诊断**：

1. 新增节点往返后存活；
2. 移动节点坐标往返后保持；
3. 删除节点往返后仍然被删除；
4. 连线往返后存活；
5. 分组往返后存活（成员集逐项比对）；
6. 另一张画布内容不受影响，且不含 A 的节点；
7. 未编辑过的画布仍回落到 fixture（不因回写而变空）；
8. **面包屑计数口径一致**：下拉里当前画布显示的「N 节点」= 实时节点数
   （此前当前画布用实时值、其他画布用陈旧 fixture，同一列表内口径矛盾）；
9. 控制台/页面错误为 0。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch332-canvas-persist.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 333：`canvasData` 目前只存内存，**刷新页面仍丢失全部编辑**。
  Batch 208 已覆盖「刷新后内容持久、历史清空」的**画布内**行为，但跨画布编辑
  的持久化尚无覆盖。需先确认源站刷新语义（**不得凭空发明**）；
  若按克隆一致性补齐须标注 clone-only。
