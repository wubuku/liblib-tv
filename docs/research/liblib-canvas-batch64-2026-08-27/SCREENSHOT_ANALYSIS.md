# Batch 64 截图与 DOM 识别台账

> 当前结论：`NO_NEW_SOURCE_SCREENSHOT_REQUIRED_FOR_PLAN`。
>
> 记录日期：2026-08-27。

## 1. 复用证据

| 证据 | 本批用途 |
|---|---|
| Batch 63 `SCREENSHOT_ANALYSIS.md` | desktop/mobile drawer closed/open host rect 与固定工具条碰撞量测 |
| Batch 17 screenshot ledger | Asset drawer 结构、宽度、desktop/mobile 既有 clone 基线 |
| `LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md` | 固定 host resize 未声明 anchor policy 的 clone 缺口 |
| `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md §7` | 固定 clone correctness default 和 source decision queue |

## 2. 已知 DOM 几何

Batch 63 的可复用量测：

| viewport/state | React Flow host |
|---|---|
| desktop closed | `x=0,y=0,width=929,height=874` |
| desktop Asset open | `x=240,y=0,width=689,height=874` |
| mobile closed | `x=0,y=0,width=390,height=844` |
| mobile Asset open | `x=240,y=0,width=150,height=844` |

在 zoom `1` 且 viewport `x=0` 时，若不 reconcile：

- desktop host local center 从 `464.5` 变为 `344.5`，需要 target viewport
  `x=-120` 才能保持旧 center flow anchor；
- mobile host local center 从 `195` 变为 `75`，同样需要 `x=-120`；
- 关闭 drawer 时 target viewport 应恢复 `+120` delta。

这些是坐标公式和 clone DOM facts，不是截图推断。

## 3. 验证期识别策略

不新增截图，优先记录：

- drawer action 前后 host `DOMRect`；
- deterministic node `DOMRect` 与 host center；
- captured/target/current viewport；
- active canvas、selection、graph/history；
- stale/current operation disposition；
- overflow 与 browser diagnostics。

只有出现节点、双浮层或工具条无法由 DOM rect 解释的视觉异常时，才保存最小
必要 crop，并立即在本文件补 state、viewport、证据类型和识别结论。

## 4. 证据边界

本批不具备新的 LibTV source drawer/viewport runtime trace。实现只采用 formal
contract 已授权的 conservative clone correctness default；source exact
left/client/center anchor、动画、auto-pan 和 mobile degradation 继续
`SOURCE_UNKNOWN`。
