# Batch 79: Director Whole-Project Duplicate

> 状态：`WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS`。
>
> 建档日期：2026-08-28。
>
> 实施完成日期：2026-08-28。

Batch 79 规划解决一个已经被多轮 Director 研究确认的高价值缺口：
普通 LibTV `duplicateCanvas` 会复制 React Flow 图，但不会把画布中
`script-execution` 节点对应的 Director project 一并深拷贝。当前 clone
因此只能做到“新画布 + 新 Director owner + 默认 project reset”，不能做到
用户理解的“复制整个导演台项目”。

## 入口

- [`PLAN.md`](PLAN.md)：范围、合同、切片、fixture、verifier 和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、专项验证、跨批回归和边界；
- [`../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  owner/project/session/persistence/duplicate 总合同；
- [`../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  Director command/history/delete、reference closure 和 one-entry/zero-partial 边界；
- [`../liblib-canvas-batch75-2026-08-27/`](../liblib-canvas-batch75-2026-08-27/)：
  同 project clipboard 的 identity remap 参考与反例；
- [`../liblib-canvas-batch76-2026-08-27/`](../liblib-canvas-batch76-2026-08-27/)：
  owner reachability、tombstone 和两阶段 teardown 边界；
- [`../LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md)：
  本批拟新增的 fixture 身份和 reset 要求。

## 重要边界

- 这是 clone-owned correctness 规划，不是 LibTV 原站 duplicate 语义的证明；
- StoryAI/Open Canvas 只能提供结构启发，不能替代 LibTV source evidence；
- 本批不移动 submodule、不接后端、不实现真实资源复制、不操作共享源站；
- target 复制 authored document 和 stable resource descriptor，不复制 history、
  active session、runtime、clipboard 或 capture bytes；
- local/ephemeral resource、tombstone、损坏 document 和未知引用均在 mutation
  前拒绝；
- persistence 写失败显式返回 `COMMITTED_SESSION_ONLY`，不伪造 durable success。
