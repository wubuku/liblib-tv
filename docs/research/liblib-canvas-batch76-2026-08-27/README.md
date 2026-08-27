# Batch 76: Director Owner Reachability Reconciliation

> 状态：`OWNER_REACHABILITY_FOCUSED_PASS`。
>
> 建档日期：2026-08-27；代码基线：`30f071b`。

## 1. 背景

Batch 67-75 已建立 Director strict document、owner/session、authored/runtime、
command/history、pointer lifecycle、reference-aware delete、async authority、
browser-local persistence 和 project-scoped clipboard。

当前最高价值的可靠性缺口是 inactive owner reconciliation。现有 page effect
只检查 active canvas 的前台 UI owner；source node 或整个 canvas 在后台被删除后，
Director registry record 仍保持 `ACTIVE/CLOSED`，旧 project 也可能被重新打开。

## 2. 本批边界

本批实现 clone-owned、memory-only owner reachability reconciliation：

- 从全部 `canvases[].nodes` 构造 live Director owner set；
- registry 中不再可达且尚未 tombstone 的 owner 只 tombstone 一次；
- active owner tombstone 后清理 session/runtime/history projection/clipboard；
- inactive owner tombstone 不影响当前 foreground project；
- repeated reconciliation、rename、switch 和 unrelated delete 幂等且零误伤；
- delayed Director result 因 generation/session 失效变 stale；
- 普通 graph delete 仍只产生原有 graph history，不增加 Director history。

本批不删除 browser persistence envelope、资源字节或 stable asset，也不定义 graph
undo 后复活 Director project。上述 durable cleanup/restore policy 保留为独立决策。

## 3. 当前实施结果

专项 focused verifier 已通过：

- pure planner 覆盖 all-canvas collection、active/inactive/cross-canvas、
  invalid/duplicate、deterministic ordering 和 repeated reconciliation；
- fresh-page Playwright 覆盖 inactive source delete、inactive canvas delete、
  active source delete、rename/switch/unrelated delete、graph undo 和 retained
  persistence；
- active delete 先同步 tombstone registry/session，再在 Director shell 卸载后
  清理 R3F/runtime/history/clipboard projection；
- store 与 DirectorDesk async context 都要求 active registry session identity；
- tombstoned owner reopen返回 `PROJECT_TOMBSTONED`；
- ordinary source delete 仍只有一条 graph history；
- zero screenshots、zero console/page/request errors。

跨批与全量结果：

- Batch 59、Batch 67-76 均串行通过；
- `npm run docs:check`、`git diff --check`、`npm run check` 均通过；
- Batch 68 当前兼容断言已从 active-delete `CLOSED` 校正为
  `TOMBSTONED`，并等待两阶段 shell teardown 后再断言 runtime 清空；
- 治理、fixture、traceability、coverage 与 verifier manifest 已同步；
- zero screenshots、zero console/page/request errors。

## 4. 入口

- [`STATIC_AUDIT_2026-08-27.md`](STATIC_AUDIT_2026-08-27.md)：当前代码、合同和风险审计；
- [`PLAN.md`](PLAN.md)：实施切片、fixture、验证和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：待补实施、回归和 checkpoint 记录；
- [`../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：正式 owner/session authority；
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：`LIBTV-VR-024` current gate 入口。

## 5. 证据边界

本批是 clone reliability implementation，不是 LibTV source-exact deletion UX
结论。不会从 StoryAI/Open Canvas 推导 source 的删除提示、恢复入口、持久化
tombstone、资源回收或 undo 语义，也不新增可见 UI。
