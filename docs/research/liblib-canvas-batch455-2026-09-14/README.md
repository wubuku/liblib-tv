# Batch 455 — VR-021 Slice E：Shot 源生命周期（§9.2 状态机 + 源身份冻结 + 聚合重置）

> 状态：`IMPLEMENTATION_RECORDED`（media ingress/resource lifecycle 合同
> Slice E；本地 fixture、无 provider run；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch455-shot-lifecycle-929-2026-09-14.png`、
> `scripts/verify-liblib-batch455.py`。

## 变更

- **`reduceLibTVShotSourceLifecycle`（libtvMediaIngress.ts 新增纯
  reducer）**：§9.2 六态 EMPTY / LOCAL_PREVIEW / MATERIALIZING /
  DURABLE_READY / SESSION_READY / FAILED；冻结 sourceRef
  `{mediaId, mediaRevision}`；**聚合重置**——新源身份的
  preview-acquired 重启生命周期（reason `SOURCE_CHANGED_RESET`）；
  非法迁移稳定拒绝（NOT_IN_LOCAL_PREVIEW / NOT_MATERIALIZING /
  NOT_DURABLE_READY / MATERIALIZE_IN_PROGRESS）。
- **Shot 源诚实化**：`BreakdownStatus` 新增 `local-preview`——视频派生
  （createBreakdown）与组件内上传（仅 component URL，§9.2「不得声称
  durable readiness」）均标 `local-preview` 并冻结 sourceRef；
  `mediaRevision` 沿用 batch 443 基线。
- **page.tsx**：reducer 只读诊断暴露。

## 验收（verify-liblib-batch455.py，SCRIPT_RECORDED_PASS）

- **lifecycle_unit**：主链 EMPTY→LOCAL_PREVIEW→MATERIALIZING→
  DURABLE_READY→SESSION_READY 与 FAILED(DECODE_ERROR) 精确；源变更
  聚合重置 + 新 sourceRef；非法迁移稳定拒绝；
- **fixture_local_preview**：真实逐帧拉片派生节点 status =
  `local-preview`、sourceRef 冻结（mediaRevision ≥1）、sourceName 在位；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-021）

Slice F（Director data/blob 收敛：字节预算 + 租约转移 + 图/历史
可达性）。
