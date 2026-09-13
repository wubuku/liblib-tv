# Batch 474 — VR-022 Slice E：BITMAP_EDITOR 会话基线捕获（annotate）

> 状态：`IMPLEMENTATION_RECORDED`（editor session/commit/history 合同
> Slice E 的 BITMAP_EDITOR 会话信封子项；clone-only；心跳批次）。
>
> 证据：`scripts/verify-liblib-batch443.py`（sessionBaseline 断言扩展）、
> `docs/design-references/liblib-clone-batch443-annotate-mapping-929-2026-09-14.png`。

## 变更

- **`ImageAnnotateState.sessionBaseline`**：打开标注编辑器时冻结
  会话基线——`{mediaId: imageUrl, width, height, mediaRevision, fit}`，
  即声明的 full-media 平面 + 修订 + fit 政策（§8.1 capture 的
  clone 侧子集：route/canvasId/nodeId 已在状态中）。
- `ImageNode` 打开标注时捕获基线。

## 验收（verify-liblib-batch443.py 扩展，SCRIPT_RECORDED_PASS）

- 打开标注 → sessionBaseline 与声明平面一致（mediaId = imageUrl、
  mediaRevision ≥ 1、fit = contain）；
- batch 443 原有 fit-transform/彩色标记断言保持绿；
- npm run check exit 0。

## 后续（VR-022）

Slice F（Annotate 纵切）与 Slice G/H 为 source-evidence/授权后范围。
