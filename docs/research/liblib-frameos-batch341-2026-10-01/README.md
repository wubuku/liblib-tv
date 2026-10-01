# Batch 341（2026-10-01）：分组盒几何不变式对所有写路径生效（不再只挂在少数 action 上）

## 结论一句话

Batch 340 修好了 `reconcileGroups` **函数内部**的两处缺陷，但那个函数只挂在
`removeNode` / `duplicateNode` / `undo` / `redo` 四条 action 上 —— **别的路径
根本不调用它**。本批把「分组盒 == 存活成员包围盒 + 28」提升为 store **写入口的
强制不变式**，并去掉 `reconcileGroups` 里那条把「成员没变」误当成「盒不用动」的
短路。三条实测失败路径一次性全绿。

## 运行时证据（修复前）

探针 `scripts/probe-frameos-batch341-group-geometry.py`，修复前输出：

```
--- S1 一键整理 后 ---
  [STALE] actual={'x':33,'y':5,'w':737,'h':319}
          expected={'x':32,'y':32,'w':676,'h':256}  drift=['x','y','w','h']
  organize 生效痕迹: pastDepth 2, 坐标已变 60,60 / 380,60   ← 整理确实执行了
--- S2 拖拽成员 后 ---
  [STALE] actual={'x':32,'y':32,'w':676,'h':256}
          expected={'x':352,'y':32,'w':936,'h':856} drift=['x','w','h']
--- S3 面板删除 后 ---
  [STALE DANGLING=['text-1']] actual={'x':352,'y':32,'w':936,'h':856}
          members=['text-1','text-2']                   ← 已删节点仍在成员集
```

修复后同探针：`S1_organize_stale / S2_drag_stale / S3_panel_delete_dangling`
全部 `false`。

## 三条路径的来源（都是**代码审计**找出来的，不是猜的）

| 场景 | 入口 | 用户可达性 |
|---|---|---|
| 一键整理 | `FrameosMapDock` → `organizeNodes` | ✅ 真实按钮（验证器里就是**真点**） |
| 拖拽成员 | `page.tsx` `onNodesChange` → `setNodes` | ✅ 拖动画布 |
| 面板删除 | `FrameosNodeEditPanel` → `setNodes(filter)` | ⚠️ 仅 debug 模式（`isDebugMode`，**全仓没有任何 UI 入口**能打开） |

第三项是重点：它和 Batch 328 修过的 `removeNode` 是**同一处缺陷的两条路径**
—— 右侧面板直接 `setNodes(nodes.filter(...))` 绕开了 action。修一条漏一条，
正是 Batch 340 写下的那条教训本身。

## 修复 1：`reconcileGroups` 无条件重算

原来的短路只看 `memberIds`：

```ts
const unchanged = prevMemberIds.length === g.memberIds.length && ...
if (unchanged) return [g];        // ← 保留原盒
```

**成员整体移动时 `memberIds` 一个字都不会变** → 永远判「未变」→ 盒永远不重算。
整理和拖拽栽的正是这个。

改为无条件按存活成员重算，并**逐个核对**了前提：`createGroup` / `arrangeGroup`
算出的盒都等于「成员包围盒 + 28」；`moveGroup` 是盒与成员**同量平移**，
平移不改变「盒 = 包围盒 + 28」这个关系。所以无条件重算不会覆盖它们的结果。

`previousMemberIds` 参数随之**变得多余并被删除** —— 它当初只为喂那条短路而存在。
Batch 340 的「缺陷 A/B」是在给一个错误前提（成员没变 ⇒ 盒没变）打补丁。

## 修复 2：不变式收敛到 store 的**唯一写入口**

```ts
export const useFrameosStore = create<FrameosCanvasState>((rawSet, get) => {
  const set = (partial, replace) => {
    const prev = get();
    rawSet(partial, replace);
    enforceGroupGeometry(get, rawSet, prev);   // 任何 action 写完都收敛一次
  };
  return ({ ... });
});
```

不逐条路径补调 `reconcileGroups`（那正是 Batch 328 犯的错），而是包住 `set`
——**将来新加的 action 也不可能再漏**。与 Batch 329（13 处手写历史快照 →
单一 `pushHistorySnapshot`）、Batch 333（多处写 localStorage → 单一订阅）
是同一个判断：不变式只该有单一出口。

两个必要的细节：

- **重入守卫** `enforcingGroupGeometry`：收敛过程里的写回不再触发收敛，否则无限递归。
- **无净变化返回同一对象**：Batch 333 的持久化订阅按**引用**判断变更，若每次
  都新建 groups 数组，它会把同样的内容反复写进 localStorage。`reconcileGroups`
  值没变时返回原对象，外层再用 `groupsEqual` 结构比较决定是否写回。

显式签名而非 `(...args) => rawSet(...args)`：zustand 的 `setState` 是**重载**的
（partial / replace 两形态），rest 展开会丢重载解析报 TS2769。

## CLONE_DECISION

源站是否允许把成员拖出分组、是否自动退组，**未采样**（源站被人机验证阻塞，
见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。「拖动成员时盒跟随成员」是**按克隆
自身不变式**推出来的，本批**未**发明任何「拖出即退组」的行为。

## 验证器

`scripts/verify-frameos-batch341.py` — **22 项断言全 PASS，0 诊断**：

1. 一键整理（**真实点击按钮**）后盒重算到成员 bbox + 28；
2. 拖拽成员后盒跟随；
3. 面板删除后无悬空成员、成员集收缩、盒按存活成员收缩；
4. 无净变化时分组对象**引用不变**（守住 Batch 333 的持久化订阅）；
5. `moveGroup` 平移后盒仍 = bbox + 28；
6. `arrangeGroup` grid / horizontal / vertical 三种模式后盒 = bbox + 28；
7. 撤销后分组与成员集一并还原；
8. 控制台/页面错误为 0。

**变异测试（证明断言非恒真）**：临时注释掉 `enforceGroupGeometry(...)` 一行后
重跑，验证器如期失败于 `organize:box-recomputed`
（`box={'x':33,'y':5,'w':737,'h':319} expected={'x':32,'y':32,'w':676,'h':256}`）。
改绿色断言前先证它会红 —— Batch 208 的教训。

回归：`328 / 329 / 330 / 331 / 332 / 333 / 340` 七批全部 PASS。

证据：`runtime-audit.json`（本目录）。
复现探针：`scripts/probe-frameos-batch341-group-geometry.py`（只读，可重复运行）。

## 遗留观察（不在本批范围）

- `FrameosNodeEditPanel` 的删除按钮在 debug 模式可达，而 `toggleDebugMode`
  在全仓**没有任何 UI 入口**。这是可达性问题不是数据一致性问题，留作候选。
- `moveGroup` 每帧调用会连带触发 Batch 333 的持久化订阅每帧写 localStorage。
  属既有行为，本批未扩大范围。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 342：`FrameosNodeEditPanel` 全套快捷操作（复制节点 / 锁定位置）
  是否都是空壳？`toggleDebugMode` 无入口是否意味着整块 debug UI 是死代码。
