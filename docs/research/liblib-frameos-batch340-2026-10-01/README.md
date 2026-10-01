# Batch 340（2026-10-01）：组内复制副本的分组归属（修两处 reconcileGroups 缺陷）

## 结论一句话

`duplicateNode` 产生的副本落在源节点 +40/+40，**常常在分组盒内**，但此前
**不加入该分组** —— 视觉上「在组里」、实际不是成员。修这一处时又暴露
`reconcileGroups` 的两个独立缺陷（一律判「未变」）。三处一起修，14/14 PASS。

## 运行时证据（修复前）

```js
groupMembersAfterDup : ['text-1','text-2']      ← 副本没入组
dupJoinedGroup       : false
dupInsideBoxBefore   : true                     ← 但它在盒里！
INCONSISTENT         : true
// 删掉被复制的成员后：
groupMembersAfterDelete: ['text-2']             ← 副本既不在组、又被盒排除
boxAfter             : {x:33,y:68,w:356,h:256}  ← 盒塌缩，副本孤零零落在外面
```

用户表现：组里复制一个节点，它**看起来属于组**；删掉原成员后，组缩小，
副本被留在组外 —— 但它的位置还在原组盒区域里，视觉错位。

## 修复 1：`duplicateNode` 让落盒内的副本入组

```ts
const containing = state.groups.find(
  (g) => g.memberIds.includes(id) && 点在新副本位置落在 g 盒内);
```

命中则把 `newId` 追加进 `memberIds` 并重算盒。

## 修复 2 & 3：`reconcileGroups` 的两个独立缺陷

修 1 时 `dup:box-recomputed` 断言失败（盒 737、应为 777），逐层挖出两处：

### 缺陷 A —— 「未变」判定用了**已打过补丁**的集合

原判定 `memberIds.every((id,i) => id === g.memberIds[i])` 拿 `g.memberIds`
与**它自己**比 → **恒为「未变」** → 永远保留陈旧盒、永远不剪枝。

修法：增加 `previousMemberIds` 参数，由调用方传入**变更前**的成员集合。

```ts
reconcileGroups(groups, nodes, previousMemberIds?)   // 按 group id
```

`duplicateNode` 传 `state.groups.map(g => [g.id, g.memberIds])`（变更前的）。

### 缺陷 B —— 「数量相同即未变」漏判「内容不同」

补上 `g.memberIds.every(id => nodes.some(n => n.id === id))`，
防止「长度相同但成员已换」被误判为未变（删一个又加一个的等长场景）。

> 这两处是**同一个函数里的一对镜像错误**：
> A 判「永远没变」，B 判「变了也当没变」。
> Batch 328 引入该函数时只测了「删成员」这一条路径；
> Batch 340 第一次走「加成员」路径，才把它们暴露出来。
> **同一函数的不同分支，往往藏着互为镜像的缺陷** —— 只测一条路径等于没测。

## CLONE_DECISION

源站对「复制组内节点」的归属如何处理**未采样**（源站被人机验证阻塞，
见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。本批修的是**克隆自身一致性**
（副本位置与分组归属必须自洽），**不是源站对齐声明**。

## 验证器

`scripts/verify-frameos-batch340.py` — **14 项断言全 PASS，0 诊断**：

1. 副本落在盒内 → 自动成为成员，成员数 2→3；
2. 盒按新成员集重算（断言到具体坐标，盒 = 全部成员 bbox + 28）；
3. 删除原成员后分组**仍含副本**，盒不塌缩；
4. 副本不在任何组盒内时不被误塞进分组；
5. 撤销两步完整回退（成员集与盒都还原）；
6. 重做恢复副本与成员关系；
7. 控制台/页面错误为 0。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch340-dup-group.py`（只读，可重复运行）。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 341：`reconcileGroups` 这次的教训（不同分支藏镜像缺陷）适用于
  其它共享工具函数 —— 特别是 `arrangeGroup` / `moveGroup` / `pasteNodeFromClipboard`
  这些同样操作分组成员的路径，它们各自是否也只被单路径测过？
