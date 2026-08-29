# Batch 92：Director 本地资源生命周期与 session lease

- [`PLAN.md`](PLAN.md)：本批范围、排序、决策和验收矩阵。
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施结果、验证命令和证据边界。
- [`runtime-audit.json`](runtime-audit.json)：fresh-page Playwright 结构化结果。

> 本批只处理 clone-owned Director local-resource reliability；不把上游
> StoryAI、Open Canvas 或当前 clone 的实现推断为 LibTV 原站 source-exact
> resource protocol。

## 结果

`FOCUSED_RUNTIME_RECORDED_PASS`。本地模型 descriptor、attempt、owner-scoped
lease、deferred release、终态 error invariant 和有限 OBJ/FBX materialization
已收口；Batch 82 历史 verifier 已按当前 owner/lease 合同适配并通过。

## 主要入口

- 实现：[`directorLocalResourceLifecycle.ts`](../../../src/lib/directorLocalResourceLifecycle.ts)、
  [`directorLocalModelMaterializer.ts`](../../../src/lib/directorLocalModelMaterializer.ts)、
  [`directorStore.ts`](../../../src/store/directorStore.ts)、
  [`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)
- 专项 verifier：[`verify-liblib-batch92.mjs`](../../../scripts/verify-liblib-batch92.mjs)、
  [`verify-liblib-batch92.py`](../../../scripts/verify-liblib-batch92.py)
- 历史兼容 verifier：[`verify-liblib-batch82.py`](../../../scripts/verify-liblib-batch82.py)

