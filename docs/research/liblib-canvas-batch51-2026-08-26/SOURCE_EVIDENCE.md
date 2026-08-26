# Batch 51 源站与 clone 证据边界

## 1. Source evidence

以下事实沿用已归档的 2026-08-26 source audit，不在本批重复识图：

| 事实 | 类型 | 证据 |
|---|---|---|
| 标准图片 top host 以 node screen center 为 `left` | `SOURCE_FACT` | [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md#35-源站-chunk-对顶部-host-定位的直接证据) |
| top host 的 pre-transform top 为 `nodeTop - 24 * zoom - 10` | `SOURCE_FACT` | 同上，production chunk 静态结构 |
| host 使用 `translateX(-50%) translateY(-100%)` | `SOURCE_FACT` | 同上 |
| 因此 toolbar bottom 到 node top 的 screen gap 为 `10 + 24 * zoom` | `INFERENCE_FROM_SOURCE_FACT` | 同上 |
| source 在约 28%/34%/41%/50% 的 top gap 约为 `16.794/18.152/19.778/22px` | `SOURCE_FACT` | 同上，live DOM rect |
| bottom panel 宽 `660px`、gap 为 `16 * zoom`、允许自然裁切 | `SOURCE_FACT` | [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) |

## 2. Clone evidence

当前 clone 在本批修改前：

- `ImageToolbar` 使用 React Flow `NodeToolbar position=Top align=center
  offset=16`；
- `ImageEditPanel` 使用节点内 absolute wrapper、`-bottom-[17px]` 和
  `scale(1 / zoom)`；
- Batch 9 verifier 把图片 top gap 固定断言为 `16px`；
- 图片 toolbar 仍是旧的 `900.5px` action set。

这些是 `CLONE_FACT`，不能被误写成当前 source contract。

## 3. Freshness boundary

本轮没有新的 authenticated browser source observation。原因是当前会话
暴露的工具集中没有可调用的有头浏览器控制接口；不能读取用户已登录的
in-app browser tab，也不能用未登录的独立浏览器替代它。

因此：

- 不更新 `liblib-live-2026-08-25/` 或现有 dated source JSON；
- 不把 Batch 51 的 clone 截图当作 source screenshot；
- 不声称 Director shell、“全屏”或当前 source action set 已完成 freshness
  复核；
- 现有 source contract 足以授权本批的窄 clone geometry correction；
- 后续有头浏览器可用后，按
  [`LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`](../LIBTV_SOURCE_FRESHNESS_REINSPECTION.md)
  做一次只读 reinspection，并另建 dated report。

## 4. Decision

本批只采用高置信、低副作用的几何映射：

```text
React Flow NodeToolbar offset = 10 + 24 * live viewport zoom
```

不把动作集合、active tool 和 graph mutation 绑定到这个几何修正中。
