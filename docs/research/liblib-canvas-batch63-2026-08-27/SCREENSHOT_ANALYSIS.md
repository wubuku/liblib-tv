# Batch 63 截图识别台账

> 当前结论：`NO_NEW_SCREENSHOT_REQUIRED_FOR_PLAN`。
>
> 记录日期：2026-08-27。

## 1. 已有证据

| 证据 | 本批用途 |
|---|---|
| `LIBTV_VIEWPORT_COORDINATE_GESTURE_STATIC_AUDIT_2026-08-27.md` | 固定 browser-window center 与 actual host mismatch |
| `LIBTV_VIEWPORT_COORDINATE_PLACEMENT_CONTRACT.md` | 固定 `HOST_CENTER` strategy、坐标域和 graph/history 边界 |
| Batch 17 asset drawer records | 固定资产抽屉改变普通画布 host 宽度/位置的 clone layout |
| Batch 59/60 records | 保护普通 graph、overlay owner 和 desktop/mobile bounds |

## 2. 预期视觉影响

本批只改变新节点的 `FLOW_WORLD` placement。既有节点、节点尺寸、颜色、工具条、
下方面板、边效果、React Flow controls 和抽屉皮肤不应改变，因此计划阶段不重做
截图识别。

实施验证优先读取：

- `.react-flow` host `DOMRect`；
- 新节点 DOM `DOMRect`；
- `flowToScreenPosition` 得到的 flow center；
- graph/history/selection；
- overflow 与 browser diagnostics。

若 asset drawer open/close 导致已有节点、图片双浮层或底部工具条出现额外视觉
变化，先在本文件追加具体 viewport、state、最小 crop 和识图结论，再实施修复。

## 3. 证据边界

本批的 actual host center 是 clone correctness floor，不是 LibTV 源站观察结论。
source exact add selection、auto-pan、panel open/close anchor preservation 继续
标记为 `SOURCE_UNKNOWN` 或 decision queue。
