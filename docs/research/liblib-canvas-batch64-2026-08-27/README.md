# Batch 64：Asset Drawer Host-Resize Anchor Preservation

> 状态：`SCRIPT_RECORDED_PASS`。
>
> 建档日期：2026-08-27。
>
> 前置实现：[`../liblib-canvas-batch63-2026-08-27/`](../liblib-canvas-batch63-2026-08-27/)
>
> 对应合同：[`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)

## 目标

在 Asset drawer 打开、关闭或转入 Canvas dropdown 时，保持旧 React Flow host
中心下的 flow point 出现在新 host 中心，避免既有图内容随 drawer DOM 插入/移除
发生可见跳动。

本批覆盖：

- lower-left Asset toggle 打开/关闭；
- Asset drawer 显式 X 关闭；
- Asset drawer canvas-context 转入 Canvas dropdown；
- current canvas / current React Flow instance / newest operation guard；
- desktop `929x874` 与 mobile `390x844`；
- graph/history/selection zero mutation；
- 与 Batch 63 actual-host default add 的组合。

本批不覆盖：

- LibTV source exact drawer anchor policy；
- browser resize/orientation、Agent drawer 或 Storyboard layout；
- live/stable viewport phase 全量分离；
- pan/zoom animation interruption、host epoch framework；
- canvas generation schema、React Flow remount race；
- Open Canvas Quick Add/drop/pending connection。

## 接力入口

- [`PLAN.md`](PLAN.md)：价值排序、证据边界、实施切片和验收；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图复用与 DOM 量测计划；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码、验证、边界和 checkpoint；
- [`../liblib-canvas-batch63-2026-08-27/IMPLEMENTATION.md`](../liblib-canvas-batch63-2026-08-27/IMPLEMENTATION.md)：
  actual-host default add 的已实现前置；
- [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md)：
  host resize correctness default 与 source decision queue。
