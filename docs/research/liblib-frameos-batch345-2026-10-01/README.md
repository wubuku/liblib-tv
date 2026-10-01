# Batch 345（2026-10-01）：⌘Z / ⌘⇧Z 谎报成功（+ 一个让它「无法被测」的元缺陷）

## 结论一句话

`page.tsx` 的 ⌘Z 分支此前是 `undo(); showToast("已撤销", "info");` ——
而 `undo()` 在撤销栈为空时**直接 return，什么都没做**。于是用户看到
「已撤销」，画布纹丝不动。这条比 Batch 344 的右键菜单**更容易撞上**：
Batch 333 刻意只持久化内容、不持久化历史，所以**每次刷新后撤销栈必然为空**，
刷新后的第一次 ⌘Z 必然撒谎。

## 运行时证据

修复后（探针 `scripts/probe-frameos-batch345-undo-toast.py`）：

```
干净起点: {past: 0, future: 0, nodes: 7}
空栈按 ⌘Z   → toast=['没有可撤销的操作']        store.undo()=False
空栈按 ⌘⇧Z  → toast=['没有可重做的操作']        store.redo()=False
加节点后     → {past: 1, nodes: 8}
真按 ⌘Z    → toast=['已撤销']  nodes 8→7        ← 文案与事实一致
再按 ⌘Z    → toast=['没有可撤销的操作']
```

**变异测试**（把修复改回 `undo(); showToast("已撤销")`）复现出缺陷原文：

```
AssertionError: batch345 check failed: undo:empty-not-claimed toasts=['已撤销']
```

## 元缺陷：这个谎**此前根本无法被测出来**

第一次跑探针时 toast 数组恒为 `[]` —— 不是缺陷不存在，是**抓不到**。
`FrameosToast` 的 toast 元素只有内联样式、**没有任何标识属性**，而 toast 文案
正是「UI 是否谎报成功」的**唯一证据**。

> 也就是说：在补上标识之前，即使有人想给这条写验证器，也只能写成空断言 ——
> 而空断言正是 Batch 336 门禁要清理的东西。**可测性和缺陷同等重要**：
> 测不了的东西，坏了也没人知道。

修：给 toast 元素加 `data-frameos-toast` / `data-frameos-toast-variant`，
与仓库里已有的 `data-frameos-context-menu` / `data-frameos-node-search-input`
等约定一致。

## 修复

`undo()` / `redo()` 从 `() => void` 改为 `() => boolean`，**如实报告是否真的执行**：

```ts
if (past.length === 0) return false;          // 空栈
if (prev.canvasKey && prev.canvasKey !== here) { …; return false; }  // 跨画布拒绝
… set(…); return true;                          // 真的撤销了
```

调用方据此选文案：

```ts
showToast(undo() ? "已撤销" : "没有可撤销的操作", "info");
showToast(redo() ? "已重做" : "没有可重做的操作", "info");
```

tsc 全绿证明**没有任何其它地方依赖旧的 void 返回**。

> 顺带修掉一个更隐蔽的撒谎路径：Batch 331 的跨画布拒绝会 `set({past:[], future:[]})`
> 却**没有撤销任何东西**。此前那条路径也照样弹「已撤销」—— 而它同时**清空了整条
> 撤销历史**。现在它返回 `false`，不再谎报。

## 验证器

`scripts/verify-frameos-batch345.py` — **15 项断言全 PASS，0 诊断**：

1. `undo()` / `redo()` 返回**布尔**（不再是 void）；
2. 空栈时返回 `false`；
3. 空栈按 ⌘Z：toast **不含**「已撤销」；
4. 空栈按 ⌘Z：toast 说「没有可撤销的操作」；
5. 空栈 ⌘Z 不改变任何状态；
6. 空 future 按 ⌘⇧Z：不含「已重做」，说「没有可重做的操作」；
7. **真**编辑后按 ⌘Z：说「已撤销」**且节点数真的减少**（文案与事实一致）；
8. 真撤销后 `future` 确实入栈；
9. 撤销耗尽后再按 ⌘Z：回到「没有可撤销的操作」；
10. ⌘Z 后按 ⌘⇧Z：说「已重做」**且节点数真的恢复**；
11. toast 元素可被选择器寻址（可测性修复本身）；
12. 诊断零错误。

第 7/10 条特意把**文案**和**数据变化**绑在一起断言：只验文案仍可能是一句
空话，必须同时验画布真的变了。**断言要绑真实性质。**

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch345-undo-toast.py`（只读，可重复运行）。

## 全仓同类扫描（未修，记录在案）

顺着 Batch 344 的线索扫了 frameos 目录下所有 `showToast`，剩余 mock：

| 位置 | 文案 | 判断 |
|---|---|---|
| `FrameosGroupCanvas:121` | 已复制分组 (mock) | 源站未采样做什么 → 不发明 |
| `FrameosGroupCanvas:126` | 已创建分组副本 (mock) | 同上 |
| `FrameosGroupCanvas:252` | 批量连线 (mock) | 同上 |
| `FrameosGroupToolbar:259` | 已存为模板 (mock) | 同上 |
| `page.tsx:509` | 已设置为资产图 (mock) | 同上 |

这些都**带着 `(mock)` 字样**，与 Batch 344 那条「假装成功」性质不同 ——
它们至少自认是占位符。真正的「假成功」已全部处理。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- `generations` 死状态字段（从未写入也从未读取）。
- `FrameosNodeEditPanel` 两个空壳按钮 + 整面板无 UI 入口（源站对齐问题）。

## 插曲：门禁第一次抓到本会话新增的违规者

写「toast 可寻址」那条断言时我图省事写了
`page.locator("[data-frameos-toast]").count() >= 0` ——
**Batch 336 建立的恒真断言门禁当场把它抓了出来**：

```
Found 1 vacuous assertion(s):
  [VACUOUS_COUNT] count() >= 0 恒真（计数不可能为负）
      check("toast:addressable", page.locator("[data-frameos-toast]").count() >= 0,
Assertion quality gate FAILED
```

改成真实性质：触发 toast 后 `count() >= 1`、文案与探针读到的一致、且
`data-frameos-toast-variant` 暴露出来。

> 这是本会话里门禁**第一次抓到我自己新写的代码**。门禁对自己人一样有效 ——
> 这正是它值得存在的原因：写断言的人和审断言的人不是同一个视角。
