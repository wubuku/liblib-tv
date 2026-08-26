# Batch 32 Screenshot Analysis Ledger

> 状态：实施前台账。当前没有新增原站深度动作捕捉截图；先登记已有字符串
> 证据和 clone 截图计划，避免把未识别画面写成事实。

## Reused Evidence

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch28-2026-08-25/SOURCE_EVIDENCE.md`](../liblib-canvas-batch28-2026-08-25/SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch29-2026-08-25/PLAN.md`](../liblib-canvas-batch29-2026-08-25/PLAN.md)
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)

## Recognition Policy

实施后只识别本批新增 clone contact sheet 一次，并记录：

- viewport、duration state、resolution state 和截图路径；
- toolbar trigger、node-anchored panel、source summary 和 pending output 层级；
- default guard、busy、submit、graph undo/redo 和 mobile clipping；
- source fact、inference、clone calibration 和 clone-only decision；
- 未取得的原站 geometry 不通过 clone 截图补写。

## Planned Screenshots

| State | Planned path | Status |
|---|---|---|
| default 30s guard | `docs/design-references/liblib-clone-batch32-depth-guard-929-2026-08-26.png` | pending |
| 10s panel 720P | `docs/design-references/liblib-clone-batch32-depth-panel-720p-929-2026-08-26.png` | pending |
| 10s panel 1080P | `docs/design-references/liblib-clone-batch32-depth-panel-1080p-929-2026-08-26.png` | pending |
| pending graph | `docs/design-references/liblib-clone-batch32-depth-graph-929-2026-08-26.png` | pending |
| mobile clipping | `docs/design-references/liblib-clone-batch32-depth-mobile-390-2026-08-26.png` | pending |
