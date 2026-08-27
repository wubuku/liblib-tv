# Batch 76 Director Owner Reachability Static Audit

> 状态：`STATIC_AUDIT_COMPLETE / IMPLEMENTATION_PENDING`。
>
> 日期：2026-08-27；代码基线：`30f071b`。

## 1. 事实分层

| 事实 | 分类 | 结论 |
|---|---|---|
| `DirectorProjectRegistry.tombstone(owner)` 已增加 generation、标记 `TOMBSTONED` 并清 active session | `CLONE_FACT` | registry 已有正确的 runtime invalidation primitive |
| tombstoned owner 的 `open()` 返回 `PROJECT_TOMBSTONED` | `CLONE_FACT` | 不需要新增 fallback/rebind 行为 |
| `directorStore.closeSession()` 只保存并关闭 active session | `CLONE_FACT` | inactive records 无法通过该 action 清理 |
| `reconcileLibTVUiOwners()` 只接收 active canvas/node IDs | `CLONE_FACT` | 可关闭前台 shell，但看不到后台 source/canvas 删除 |
| `canvasStore.removeNode/removeSelectedNodes/removeCanvas` 不通知 Director registry | `CLONE_FACT` | source/canvas lifecycle 与 Director owner authority 尚未接通 |
| persistence adapter 支持 storage `removeItem`，但 authority 没有 durable tombstone/delete command | `CLONE_FACT` | 本批不得私自删除 envelope |
| 正式合同默认 source/canvas delete 先 tombstone，不绑定 fallback canvas | `DECISION` | clone correctness floor 已明确 |
| LibTV authenticated source 的 Director delete/recovery UI 未取证 | `SOURCE_UNKNOWN` | 本批不能宣称 source-exact UX |

## 2. 当前失败模式

### 2.1 Active owner

当前 active source 被删除时，page UI effect 会调用 `closeSession()`：

- shell 和 active session 被关闭；
- registry record 变为 `CLOSED`，不是 `TOMBSTONED`；
- graph undo 或同 ID 重建后仍可恢复旧 Director project；
-旧 async identity 只依赖 session close 变 stale，owner deletion intent 未记录。

### 2.2 Inactive owner

当 project B 已创建后切回 project A，再删除 B source 或 B canvas：

- page effect 看不到 B；
- B registry record保持 `CLOSED`；
- B persistence envelope保持可加载；
- 以后同 owner key 打开时会恢复一个已失去 graph owner 的 project。

### 2.3 Canvas deletion

`removeCanvas()` 移除 canvas 与 graph history owner，但不枚举其 Director records。
若只监听 active Director owner，删除后台 canvas 会留下全部 Director projects。

## 3. 选择的 authority boundary

本批采用 page-owned adapter：

```text
canvasStore.canvases
  -> all live { route, canvasId, sourceNodeId } owners
  -> pure reconciliation planner(registry snapshot)
  -> directorStore.reconcileProjectOwners()
  -> registry.tombstone(owner)
  -> active projection cleanup when required
```

理由：

- `canvasStore` 保持普通 graph/lifecycle 的单一事务与 history 语义；
- Director registry/store拥有自身 project/session/runtime 副作用；
- page 已承担 UI owner reconciliation，可组合两类 owner snapshot；
- pure planner 可独立验证，避免依赖 React effect timing 推导 correctness。

## 4. Live owner 定义

Director owner identity 是 `route=libtv + canvasId + sourceNodeId`。只要 graph 中
仍存在对应 node，该 owner 对已创建 registry record就是 live；本批不按 node
type、title 或当前 UI capability 猜测 owner。

只枚举 registry 已知 owner，再与全部 canvas node keys 比较：

- live key -> preserve；
- missing key + `ACTIVE/CLOSED` -> tombstone；
- missing key + `TOMBSTONED` -> no-op；
- registry 未见的新 graph node -> 不创建 project。

这避免把所有普通 node 误当 Director project，也允许未来 Director 可从多个
source node type 打开，而不把 UI capability 规则复制到 lifecycle planner。

## 5. Active cleanup

active owner 被 planner 判定 missing 时：

1. registry 直接 tombstone，不先 `close()` 保存；
2. generation 增加，active session 清空；
3. Director store 清除 project/session owner、capture viewer、gesture、playback、
   phone recording、clipboard 和 command projection；
4. project-local history/archive、capture archive 和 persistence envelope暂时保留；
5. page 同步关闭 Director shell。

不先保存的原因是 owner 已失效；被动 reconciliation 不应把 deletion 后的 stale
UI/runtime snapshot提升为新的 durable canonical save。

## 6. Idempotency 与误伤防护

- planner 输出按 structured owner key 排序；
- duplicate live owners 归一化；
- `TOMBSTONED` record不再输出；
- repeated effect 不增加 generation；
- canvas rename不改变 canvas ID；
- active canvas switch不改变全局 live owner set；
- unrelated node delete只影响不存在对应 registry record 的 key；
- graph undo不会自动 untombstone。

## 7. 风险与后续决策

1. memory tombstone 在 reload 后丢失，而 retained envelope 可能恢复旧 project；
2. graph undo 可恢复 source node，但本轮明确不恢复 Director project；
3. persistence/history/capture archive 继续占用 browser memory/storage；
4. resource bytes 和 Blob URL 需要单独 reachability/lease authority；
5. whole-canvas duplicate 仍需新 owner/project/ID remap transaction；
6. exact LibTV delete confirmation、recovery 和 retention policy仍未知。

这些风险必须在实施结果中继续显式记录，不能把
`OWNER_REACHABILITY_FOCUSED_PASS`解释为 durable deletion complete。
