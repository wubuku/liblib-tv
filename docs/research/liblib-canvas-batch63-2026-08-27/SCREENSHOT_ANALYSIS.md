# Batch 63 截图识别台账

> 当前结论：`NO_NEW_SOURCE_SCREENSHOT_REQUIRED` / `CLONE_DOM_COLLISION_RECORDED`。
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

## 3. 实施期 DOM 量测

2026-08-27 的 focused Playwright 首轮在 `929x874`、资产抽屉打开状态发现：

| 区域 | DOM-backed rect |
|---|---|
| actual React Flow host | `x=240..929`，宽 `689px` |
| 左下次级工具条 | `x=256..527`，宽 `271px` |
| 底部主入口工具条 | `x=295.5..633.5`，宽 `338px` |
| 两工具条水平重叠 | 约 `231.5px` |

直接交互结果：次级工具条的“资产管理”文字层截获“添加节点”点击，导致 asset-open
default add 无法由用户触发。该结论来自 DOM rect、Playwright hit-test 失败日志和
实际点击，不需要重新识别源站或 clone 截图。

修复首轮验证还发现 `toggleAddNodePanel()` / `togglePrimaryPanel()` /
`setPrimaryPanel()` 会展开包含 `isAssetPanelOpen=false` 的统一关闭态，因此即使
触发成功，创建前也会先关闭 drawer 并把 host 恢复全宽。资产抽屉是本批需要持续
量测的 layout surface，不应被 Add Node / Character 的 transient-surface 互斥误关。

本批采用 clone correctness 修复：

- 桌面资产抽屉打开时，主入口工具条跟随 actual host center；Batch 64 regression
  将窄桌面改为 screen-space center floor，避免与完整次级工具条碰撞；
- 次级工具条保持完整宽度和 minimap/zoom trigger 的 `+240px` drawer follow；
- 移动端继续使用上下两行工具条，不做 host-center 横移；
- Add Node 与 primary panel 的开关保留当前资产抽屉，其他 transient overlay 仍关闭；
- 不声称这是 LibTV 源站 exact responsive policy。

## 4. 证据边界

本批的 actual host center 是 clone correctness floor，不是 LibTV 源站观察结论。
source exact add selection、auto-pan、panel open/close anchor preservation 继续
标记为 `SOURCE_UNKNOWN` 或 decision queue。
