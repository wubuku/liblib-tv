# Batch 74 计划：Director Durable Project Persistence

> 状态：`COMPLETE / PERSISTENCE_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 实施 checkpoint：`d68285b`。

## 1. 目标

在现有 Director V1 document、registry 和 runtime adapter 之上，完成一个
clone-owned browser-local persistence slice：

1. typed storage envelope、stable owner key、project/generation/fingerprint；
2. strict load/normalize，区分 missing、corrupt、future、mismatch；
3. save failure/quota 时 zero-partial，内存 session 继续工作；
4. reload 后恢复同一 authored document 和 time-zero runtime projection；
5. stale save completion 不覆盖更新后的 project；
6. session/runtime/UI/resource-byte exclusion 可验证；
7. ordinary canvas graph/history 与 Director persistence 隔离。

## 2. 实施切片

### Slice A：storage contract

- [x] 新增 `src/lib/directorProjectPersistence.ts`；
- [x] 定义 storage envelope、load/save result、failure reason；
- [x] 定义 clone-owned key，避免不同 route/canvas/source/project 串场；
- [x] 只依赖 `unknown` + strict `decodeDirectorProjectDocument`；
- [x] 注入 storage adapter，便于 pure verifier 模拟 corrupt/future/quota。

### Slice B：registry/store integration

- [x] registry open 时先读取 owner-scoped persisted envelope；
- [x] 只在 decode、identity、generation guard 全部通过时恢复；
- [x] 新 project 和 canonical mutation commit 触发 persistence request；
- [x] close/reopen、A/B owner、refresh 恢复同一 project；
- [x] stale save completion 不改变 current persistence status；
- [x] 失败只记录 persistence outcome，不生成 semantic history entry。

### Slice C：runtime diagnostics

- [x] 暴露最小 browser diagnostic snapshot；
- [x] 记录 storage status、last failure、saved fingerprint/generation；
- [x] 不暴露或持久化 selection、playhead、panel、Three.js refs、Blob/File；
- [x] 保持现有 async authority snapshot 独立。

### Slice D：focused verifier

- [x] pure V1 envelope round-trip；
- [x] missing storage creates new document；
- [x] corrupt/future/owner/project mismatch reject with zero replacement；
- [x] quota/write failure preserves memory session；
- [x] stale save completion ignored；
- [x] reload restores authored document and runtime time-zero projection；
- [x] UI/session/runtime fields absent from serialized payload；
- [x] ordinary canvas graph/history unchanged；
- [x] diagnostics/page/request errors 为零，截图写入为零。

### Slice E：治理与回归

- [x] 更新 Director project/session contract；
- [x] 更新 verifier manifest、fixture catalog、verification ledger、
  traceability、decision register；
- [x] 更新 Big Picture、Agent Task Map、HARNESS、docs hubs、CHANGELOG；
- [x] 运行 Batch 67-74 focused gates；
- [x] 运行 `npm run docs:check`、`git diff --check`、`npm run check`；
- [x] 记录实施结果、commit/push，并确认主工作区干净且无额外 worktree。

## 3. Fixture

### Pure aliases

```text
owner A = libtv / canvas-A / source-A
project A = P-A, generation 3, document fingerprint D-A
owner B = libtv / canvas-B / source-B
storage key = route + canvas + source + project
```

覆盖：

- valid envelope；
- missing；
- malformed JSON/object；
- future schema；
- owner mismatch；
- project mismatch；
- generation/fingerprint stale completion；
- write failure / quota。

### Fresh-page scenarios

1. Director authored object/camera/timeline edit -> reload -> document restored；
2. A/B owner persistence isolation and A-B-A continuity；
3. corrupt payload rejected without replacing valid memory/default state；
4. future schema and owner/project mismatch rejected；
5. simulated storage write failure leaves current edit visible；
6. serialized payload has no selection/playhead/panel/phone/Three.js/blob fields；
7. ordinary canvas graph/node/edge/history remains unchanged；
8. no console/page/request errors and no new screenshots.

## 4. 验收停止条件

只有全部满足才标记 `PERSISTENCE_FOCUSED_PASS`：

- storage adapter 是独立、可注入、typed 的 authority boundary；
- load 经过 strict decode/normalize，失败为 zero-partial；
- owner、project、schema、generation、fingerprint 隔离正确；
- fresh reload 恢复 authored document，不恢复 session/runtime/UI；
- stale save 不覆盖 current project；
- quota/write failure 不破坏当前内存 session；
- capture bytes、Blob/File/Object URL 和 Three.js refs 不进入 envelope；
- Director persistence 不写普通 canvas graph/history；
- Batch 67-74、docs check、`npm run check` 全部通过；
- 文档明确 clone-owned decision、LibTV source unknown 和后续边界；
- `master` 与 `origin/master` 同步且工作区干净。

## 5. 暂不解决

- IndexedDB、backend/cloud sync、remote conflict merge；
- schema migration beyond current V1；
- durable history/undo stack；
- stable upload/materialization、真实 mesh/panorama loader；
- ordinary canvas graph persistence；
- inactive-owner tombstone reconciliation；
- copy/paste identity remap；
- LibTV authenticated Director 的 source-exact persistence/API/UI。
