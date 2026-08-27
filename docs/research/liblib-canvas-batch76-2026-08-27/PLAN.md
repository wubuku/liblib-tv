# Batch 76 计划：Director Owner Reachability Reconciliation

> 状态：`OWNER_REACHABILITY_FOCUSED_PASS`。
>
> 日期：2026-08-27；代码基线：`30f071b`。

## 1. 目标

关闭 inactive source/canvas 删除后的 Director registry/session 泄漏：

1. pure owner-reachability planner；
2. 全部 canvas/node 构成的 live owner authority；
3. registry record 一次性 tombstone；
4. active session/runtime/clipboard cleanup；
5. inactive deletion 与 foreground project 隔离；
6. delayed async completion stale；
7. ordinary graph/history 和 persistence cleanup 边界可验证。

## 2. 实施切片

### Slice A：pure planner

- [x] 新增 `src/lib/directorOwnerReconciliation.ts`；
- [x] 定义 live owner、tombstone owner、preserved owner 和 active invalidation；
- [x] 只处理 registry 已存在且非 `TOMBSTONED` 的 record；
- [x] owner key 复用 structured `route/canvas/source` identity；
- [x] invalid/duplicate live owner 输入归一化，输出 deterministic；
- [x] pure planner 不读 Zustand、DOM、storage 或 React Flow。

### Slice B：store authority

- [x] `DirectorState` 增加 owner reconciliation action；
- [x] 对 planner 返回的 owner 逐个调用 registry `tombstone()`；
- [x] active owner 失效时清理 project/session/runtime gesture/capture/clipboard；
- [x] inactive tombstone 不切换或重置当前 foreground project；
- [x] 不删除 persistence envelope、history archive、capture archive 或资源；
- [x] repeated reconcile 不重复增加 generation。

### Slice C：page lifecycle adapter

- [x] page 订阅全部 canvas 的稳定 owner reachability projection；
- [x] graph/source delete、canvas delete 和 graph undo 后运行 reconcile；
- [x] 前台 UI owner cleanup 与 registry reconciliation 保持分层；
- [x] active Director owner invalid 时关闭 Director shell；
- [x] rename、switch、unrelated node mutation 不误伤 registry；
- [x] 不把 Director side effect写进 `canvasStore.remove*` transaction。

### Slice D：focused verifier

- [x] pure active/inactive/cross-canvas owner planner corpus；
- [x] source delete active owner -> tombstone + shell/session cleanup；
- [x] source delete inactive owner -> tombstone only；
- [x] canvas delete -> tombstone canvas 内全部 records；
- [x] unrelated node delete、canvas switch、rename -> preserve；
- [x] repeated reconciliation -> same generation/snapshot；
- [x] tombstoned owner reopen -> `PROJECT_TOMBSTONED`；
- [x] delayed async result -> stale/zero mutation；
- [x] ordinary graph delete remains one graph history step；
- [x] persistence envelope retained and reload boundary explicitly recorded；
- [x] diagnostics/page/request errors 和 screenshots 均为零。

### Slice E：治理与回归

- [x] 更新 Director project/session contract；
- [x] 更新 verifier manifest、fixture、ledger、traceability、decision register；
- [x] 更新 coverage、Big Picture、Agent Task Map、HARNESS、hubs、CHANGELOG；
- [x] 运行 Batch 67-76 focused gates；
- [x] 运行 `npm run docs:check`、`git diff --check`、`npm run check`；
- [x] 记录实施结果、commit/push，确认唯一主 worktree 干净。

## 3. Fixture

```text
canvas A:
  source A -> active Director project PA
  source B -> inactive Director project PB
  unrelated node U

canvas B:
  source C -> inactive/foreground-switchable project PC
```

场景：

1. 删除 active source A；
2. 前台打开 A、后台删除 source B；
3. 前台打开 A、删除整个 canvas B；
4. 删除 unrelated node U；
5. switch/rename canvas 不改变 reachability；
6. 对同一 graph snapshot 连续 reconcile 两次；
7. tombstone 后尝试 reopen B/C；
8. 删除 owner 后完成旧 capture/export/phone attempt；
9. graph undo 恢复 source node，但 project 保持 tombstone；
10. reload 后 browser persistence envelope 仍存在，但本批不将 memory tombstone
    宣称为 durable。

## 4. Authority 与历史边界

| 动作 | graph history | Director history | registry | persistence |
|---|---:|---:|---|---|
| source delete | 原有 1 step | 0 | owner tombstone | retain |
| canvas delete | 原 lifecycle 语义 | 0 | canvas records tombstone | retain |
| repeated reconcile | 0 | 0 | no-op | 0 |
| unrelated delete/switch/rename | existing semantics | 0 | preserve | 0 |
| graph undo after tombstone | existing 1 step | 0 | still tombstoned | retain |

Reconciliation 是 derived lifecycle repair，不是可 undo 的 Director semantic
command。真正 durable delete、tombstone marker、restore 或 resource release
必须由后续显式合同决定。

## 5. 验收停止条件

只有全部满足才升级为 `OWNER_REACHABILITY_FOCUSED_PASS`：

- pure planner 对 active/inactive/cross-canvas/duplicate/idempotent 场景确定；
- 全 canvas reachability 而非 active canvas 被用作 authority；
- active invalidation 清理 session/runtime/clipboard，inactive invalidation 不误伤；
- tombstoned owner 不能 reopen，旧 async completion stale；
- graph/history 保持原有事务数量，Director history 零新增；
- storage/resource 不被隐式删除，reload/undo 边界明确标注；
- Batch 67-76、docs check、`npm run check` 全部通过；
- 文档明确 clone-owned decision 与 source unknown；
- commit/push 完成，`master == origin/master` 且唯一 worktree 干净。

## 6. 暂不解决

- durable tombstone 写入 persistence envelope；
- localStorage/IndexedDB/backend record 删除；
- graph undo 后 Director project restore/recreate；
- capture bytes、Blob URL、stable asset 或 model resource release；
- whole-project source/canvas duplicate；
- ordinary canvas persistence/async ingress；
- LibTV source-exact deletion confirmation、toast、modal 或 recovery UI。
