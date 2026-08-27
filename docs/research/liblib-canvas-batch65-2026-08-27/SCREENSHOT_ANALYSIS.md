# Batch 65 截图与运行证据台账

> 当前结论：`NO_NEW_SOURCE_SCREENSHOT_REQUIRED`。
>
> 记录日期：2026-08-27。

## 1. 复用证据

| 证据 | 本批用途 |
|---|---|
| [`../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md`](../LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md) | 固定 responsive effect、per-canvas viewport 和 stale callback 缺口 |
| [`../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md`](../LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md) | `§7.4` bootstrap boundary、`GC-081/082/089` |
| Batch 63 runtime audit | desktop/mobile bootstrap 与 actual host placement 基线 |
| Batch 64 runtime audit | Asset layout viewport commit、current canvas guard 和 zero graph history |
| Batch 18/19 screenshot ledger | zoom/minimap 的响应式工具条基线 |

## 2. 为什么不重新识图

本批问题是 owner 与状态覆盖，不是新的像素、文案、图标或层级问题。验证应优先
记录：

- viewport exact `{x,y,zoom}`；
- breakpoint、active canvas 和 owner；
- callback disposition；
- graph/history/selection before/after；
- host/body overflow 和 browser diagnostics。

已有截图无法证明 callback 属于哪个 canvas，也无法证明 preset 是否覆盖了
user-owned viewport。重复打开整图不会增加本批证据。

## 3. 允许新增视觉证据的条件

只有出现以下情况才保存最小截图或 crop：

- 跨 breakpoint 后 React Flow surface 出现空白、非预期裁切或工具条重叠；
- DOM rect 与 viewport 数值无法解释可见节点跳动；
- Batch 18/19/63/64 的既有响应式断言出现新的视觉回归。

新增后必须记录 viewport size、active canvas、ownership、before/after viewport、
截图路径、DOM-backed 事实与未确认区域。

## 4. 证据边界

本批没有新的 LibTV source responsive runtime trace。desktop/compact preset 是
clone 的 source-shaped fixture；“bootstrap 只执行到 stable viewport 出现”为
conservative clone correctness default，不声明原站使用同一 owner schema、
breakpoint、resize anchor 或持久化策略。
