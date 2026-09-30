# Batch 328（2026-10-01）：分组完整性 — 删除分组成员后的悬空引用与陈旧分组盒

## 结论一句话

`removeNode` 只过滤 `nodes`/`edges`，**不维护 `groups`**：被删节点仍留在
`groups[].memberIds` 里（悬空成员），分组盒 `x/y/w/h` 也从不重算。删除分组成员后，
覆盖层仍按旧几何绘制（比实际成员大一圈），而排列/拖拽/解组都基于**错误的成员集**
计算。已加 `reconcileGroups()` 修掉。

## 运行时证据（修复前）

对两个节点成组（`组1`，盒 737×319），再删掉其中一个成员：

```json
{
  "memberIds": ["text-1", "text-2"],
  "dangling": ["text-1"],          ← 节点已删，仍在成员表里
  "boxUnchanged": true,            ← 盒仍是删除前的 737×319
  "liveMembers": ["text-2"]        ← 实际只剩 1 个成员
}
```

真实用户路径同样中招：成组 → 选中组内节点 → Delete。成员消失后分组框原地不动，
用户看到的是一个明显偏大的空壳分组。

## 为什么这是缺陷而不是设计

- `createGroup` / `arrangeGroup` 都以 `memberIds` 为**唯一事实来源**去 filter
  `nodes`（`arrangeGroup`：`get().nodes.filter((n) => group.memberIds.includes(n.id))`）。
  悬空 id 不会报错，只会让成员集**静默偏小** —— 排列后分组盒与成员不匹配。
- 源站语义不存在此问题：分组是服务端实体，成员删除会同步更新分组。
  本项属**克隆侧数据一致性缺陷**，不改变任何已采样的源站可见行为。

## 修复

`src/store/frameosStore.ts` 新增 `reconcileGroups(groups, nodes)`，在 `removeNode`
中调用：

1. 按存活 `nodes` 过滤 `memberIds` → 消除悬空引用；
2. 成员集合变化时按「存活成员 bbox + 28」重算 `x/y/w/h`；
3. 成员**全部**被删 → 该分组随之消失（`flatMap` 返回空）；
4. 分组消失时同步清空 `selectedGroupId`，不留下指向不存在分组的选中态；
5. 成员集合未变时原样返回，避免无谓的重算抖动。

## 修复后（同一探针）

```json
{
  "memberIds": ["text-2"],
  "dangling": [],                 ← 悬空引用清零
  "box": {"x":33,"y":68,"w":356,"h":256},   ← 紧贴剩余成员
  "boxUnchanged": false           ← 几何已重算
}
```

737×319 → 356×256，正好是单个 300×200 成员加 28 padding 的两倍。

## 验证器

`scripts/verify-frameos-batch328.py` — **17 项断言全 PASS，0 诊断**：

1. 删除成员后 `memberIds` 无悬空引用、分组不被误删；
2. 分组盒按剩余成员精确重算（断言到具体坐标，不只是「变了」）；
3. 成员删空 → 分组消失且 `selectedGroupId` 被清空；
4. 撤销可恢复被删节点，且成员集**不回到悬空状态**；
5. 排列（水平/宫格）后分组盒恒等于「存活成员 bbox + 28」；
6. 无分组时普通删除不受影响；
7. 控制台/页面错误为 0。

第 5 项最初写成「排列一定改变分组盒」，被断言失败后改正：单成员做水平/宫格排列
**本就不应改变几何**（单元素布局 = 自身 bbox + 28）。断言改为不变式
「盒 = 存活成员 bbox + 28」——这才是真正该保证的性质。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch328-group-integrity.py`（只读，可重复运行）。

## 已知遗留（未在本批处理）

`undo`/`redo` 的历史快照只存 `{nodes, edges}`，**不含 `groups`**。因此撤销一个
「成组」动作不会恢复分组本身（`createGroup` 也未入历史栈）。这是既有设计，
改动会影响 batch251 的分组历史断言，故本批**只修删除路径的一致性**、不扩展历史
快照。列为 Batch 329 候选。
