# Batch 451 — VR-021 Slice B：instance 租约台账 + fake materializer（确定性结局）

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> Slice B；纯/实例域、无 provider/storage/network；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch451-lease-ledger-929-2026-09-13.png`、
> `scripts/verify-liblib-batch451.py`。

## 变更

- **`src/lib/libtvMediaLease.ts`（新）**：
  - `LibTVMediaLeaseLedger`：instance 域租约台账，五类 resourceClass ×
    五类 ownerKind（§6.4 schema 原样）；**release 恰好一次语义**——
    releasedAt 仅首记，重复调用递增 releaseCount 返回
    `already-released`；`transfer` 盖 transferredAt 并换主，已释放/
    已转移租约拒绝再转；
  - `LibTVFakeMaterializer`：确定性结局（§21 Slice B）——相同内容
    指纹的第二次物化 = `duplicate` 返回首个 locator（不新建租约）；
    `fail` → `MEDIA_MATERIALIZATION_FAILED`；`stale`（owner 不存续）
    → `MEDIA_ATTEMPT_SUPERSEDED` 且不建租约；`ok` 物化 locator 并
    在台账 acquire 一条 `SESSION_RESULT_URL` 租约（INGRESS_OPERATION
    持有、可转 GRAPH_REFERENCE_REGISTRY）。
  - settle() 由调用方手动驱动——零定时器、零网络。
- **page.tsx**：只读 window 诊断暴露（台账/物化器工厂）。

## 验收（verify-liblib-batch451.py，SCRIPT_RECORDED_PASS）

- **exactly_once_release**：首释放 released，二释放 already-released、
  releaseCount=2、releasedAt 不变（200）；
- **transfer**：转移盖戳 400 + 换主 GRAPH_REFERENCE_REGISTRY；已释放
  租约拒绝转移；未知 leaseId false；
- **materializer**：ok 物化 + 恰好 +1 租约；duplicate 同 locator；
  fail/stale 的稳定 reason 精确；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-021）

Slice C（Add Resource 多文件纵切：runtime provisional cohort + 一次
accepted-success 图事务，本地 fixture 物化器）。
