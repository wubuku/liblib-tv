# Batch 80：Director Durable Tombstone 与安全资源清理

> 状态：`DURABLE_TOMBSTONE_FOCUSED_PASS`。
>
> 建档日期：2026-08-28。

Batch 80 延续 Batch 76 的 owner reachability 和 Batch 79 的 whole-project
duplicate，解决 clone-owned Director project 被 graph/source/canvas 删除后仍可
通过 browser-local persistence 恢复、transient capture bytes 残留以及本地模型
descriptor 无法按引用安全释放的问题。

## 入口

- [`PLAN.md`](PLAN.md)：范围、决策、fixture、验证和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码变更、验证结果和 checkpoint；
- [`runtime-audit.json`](runtime-audit.json)：fresh BrowserContext 结构化结果；
- [`../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  Director current gate；
- [`../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  owner、session、document、persistence 和 lifecycle 总合同。

## 重要边界

- 这是 clone-owned browser-local lifecycle policy，不是 LibTV 原站删除/恢复
  语义的 source-exact 证明；
- durable tombstone 只阻止 clone 的 project reopen/save resurrection，不接后端、
  账户资产、云同步或真实资源 provider；
- 只有 tombstone 成功写入后才清除该 project 的 history/capture archive 和
  不再被其他 live/session-only project 引用的 local model descriptor；
- storage write 失败保持 session-only continuity，不伪造 durable cleanup 成功；
- 不改变普通 canvas graph undo 的历史语义，也不把 graph undo 自动解释为
  Director project restore。

## 相关代码

- [`src/lib/directorProjectPersistence.ts`](../../../src/lib/directorProjectPersistence.ts)
- [`src/lib/directorProjectRegistry.ts`](../../../src/lib/directorProjectRegistry.ts)
- [`src/store/directorStore.ts`](../../../src/store/directorStore.ts)
- [`scripts/verify-liblib-batch80.mjs`](../../../scripts/verify-liblib-batch80.mjs)
- [`scripts/verify-liblib-batch80.py`](../../../scripts/verify-liblib-batch80.py)
