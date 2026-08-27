# Batch 65：Responsive Viewport Bootstrap Ownership

> 状态：`PLAN_RECORDED`。
>
> 建档日期：2026-08-27。
>
> 前置实现：[`../liblib-canvas-batch63-2026-08-27/`](../liblib-canvas-batch63-2026-08-27/)、
> [`../liblib-canvas-batch64-2026-08-27/`](../liblib-canvas-batch64-2026-08-27/)
>
> 对应合同：[`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)

## 目标

把 `desktopViewport` / `compactViewport` 明确限制为 demo canvas 的首次 bootstrap，
防止用户已经平移、缩放或经 layout transaction 得到的 stable viewport 在：

- desktop/mobile breakpoint 切换；
- active canvas 切出再切回；
- stale React Flow viewport callback；

这些场景中被固定 preset 或错误 canvas owner 覆盖。

本批是 clone-owned viewport correctness，不是 LibTV source exact responsive
policy。它不实现完整 `LIVE/STABLE` reducer、browser resize center-anchor、
gesture cancel、持久化或 Open Canvas hydrate。

## 接力入口

- [`PLAN.md`](PLAN.md)：价值、静态事实、实施切片、验收和停止条件；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图复用与运行证据策略；
- `IMPLEMENTATION.md`：完成后的代码、验证、边界和 checkpoint；
- Batch 63：actual-host default add；
- Batch 64：Asset drawer host-resize center anchor；
- `LIBTV-GI-047/061/063/066` 与 `LIBTV-GC-081/082/089`：本批治理入口。
