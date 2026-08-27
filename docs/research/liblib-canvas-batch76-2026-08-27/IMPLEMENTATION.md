# Batch 76 实施与验证记录

> 状态：`IMPLEMENTED / REGRESSION_PENDING`。
>
> 建档日期：2026-08-27。

## 1. 实施范围

Batch 76 已增加：

- `src/lib/directorOwnerReconciliation.ts`
  - 从全部 canvas/node 收集 typed owner；
  - stable reachability signature避免位置/尺寸更新重复 effect；
  - planner 输出 preserved/tombstone/already-tombstoned/active-invalidated；
  - invalid/duplicate owner归一化，结果按 structured owner key确定排序。
- `src/store/directorStore.ts`
  - `reconcileProjectOwners()` 将不可达 registry records一次性 tombstone；
  - active tombstone前保留 memory history/capture archive；
  - `clearTombstonedProjectOwner()` 清理 project/session/runtime/history/
    capture/clipboard projection；
  - async context额外要求 active registry session identity完全匹配。
- `src/app/page.tsx`
  - 订阅所有 canvas 的 owner signature；
  - active invalidation先关闭 Director shell，再同步 tombstone registry；
  - shell卸载两帧后清理 R3F/store projection；
  - ordinary canvasStore transaction保持无 Director依赖。
- `src/components/director/DirectorDesk.tsx`
  - export/capture surface读取 async context时验证 active registry session。

## 2. Focused Verifier

新增：

- `scripts/verify-liblib-batch76.mjs`
- `scripts/verify-liblib-batch76.py`
- [`runtime-audit.json`](runtime-audit.json)

Pure corpus 已通过：

1. all-canvas owner collection；
2. inactive source delete；
3. inactive canvas delete；
4. active source delete；
5. invalid/duplicate normalization；
6. deterministic ordering；
7. registry idempotency；
8. tombstoned reopen rejection；
9. delayed async owner stale。

Fresh-page Playwright 已通过：

- owner A active、owner B inactive、owner C cross-canvas；
- inactive B source delete只 tombstone B；
- inactive canvas delete只 tombstone C；
- active A source delete同步失效 session并关闭 shell；
- runtime、capture viewer、gesture、phone recording、history projection 和
  clipboard清理；
- rename/switch/unrelated delete不误伤；
- repeated reconciliation不再增加 generation；
- graph undo恢复 source node但不 untombstone project；
- persistence envelope保留；
- ordinary node delete保持一条 graph history；
- zero screenshots、zero console/page/request errors。

## 3. 调试结论

初版 active cleanup 在 registry tombstone后立即 reset Director store。Playwright
捕获到 R3F event manager在 shell卸载窗口尝试连接 null target。最终实现改为：

```text
close shell owner
  -> tombstone registry/session synchronously
  -> async context becomes stale synchronously
  -> wait for R3F shell teardown
  -> clear Director store projection
```

该顺序同时保持 async correctness 和 renderer lifecycle安全。

## 4. 待完成

- Batch 67-76 current gate跨批回归；
- docs check、`git diff --check`、`npm run check`；
- governance/traceability/coverage/ledger更新；
- 最终 commit/push 与 clean-worktree确认。
