# Batch 31 Screenshot Analysis Ledger

> 状态：规划阶段未新增原站截图，也未重复识别 Batch 30 contact sheet。

## Reused Evidence

主体编辑器的可执行事实来自：

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch30-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch30-2026-08-25/SCREENSHOT_ANALYSIS.md)
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)

这些记录已经覆盖菜单入口、duration guard 和智能抠像，不需要再次打开整张
旧截图。

## New Screenshot Policy

实施后只识别本批新增的 clone 状态截图一次，并把：

- viewport、state 和截图路径；
- panel/mark overlay 的层级；
- tool、counter、字段和 disabled reason；
- node anchor、natural clipping 和 output graph；
- source fact、inference、clone-only calibration；

写回本文件。后续回归先读本节，不重复识别同一 contact sheet。
