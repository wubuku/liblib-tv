# Batch 110：既有漂移 verifier 标注为 HISTORICAL_CONTRACT

> 状态：`DOCS_RECORDED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 109（`batch/109-freshness-recheck`）。

依据 Batch 108 的基线归因（12 个 verifier 在 `86673b6` 同样失败），把
batch6/9/40/41/44/46/48/49/51/72/74/75 标注为
`AGED_GATE / HISTORICAL_CONTRACT`，并在
`LIBTV_VERIFIER_REPLACEMENT_MAP.md` 新增 §4.z 登记处置。纯文档与脚本头
标注，无运行时行为变更。

## 处置内容

1. 12 个脚本顶部加 `AGED_GATE / HISTORICAL_CONTRACT` 头注（证据指向
   Batch 108 归因与 replacement map §4.z）。
2. replacement map §4.z：漂移清单、取代关系（Batch 59、67-96 current
   gates / Batch 77 supersede / VR-001 队列）与重新启用条件。
3. VERIFICATION_LEDGER / HARNESS / research README / docs index 同步。

## 边界

- 不删除、不改写任何断言逻辑（历史快照对照仍可运行）；
- 当前通过口径以 `LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST` 与 Batch
  97-108 专项 verifier 为准。

## 完成定义

1. `npm run docs:check` 通过；`npm run check` 通过（脚本仅加注释）。
2. 特性分支 commit/push。
