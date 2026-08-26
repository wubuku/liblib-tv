# Batch 52 源站证据与 clone 决策

## 1. 采用的源站事实

本批复用 2026-08-26 已归档证据，不重复识图：

| 事实 | 证据 |
|---|---|
| 当前标准 toolbar 为 `1092.5x49`、13 个 button | [`../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md) |
| 顺序是 9 个文字动作 + 标注/旋转/下载/预览 | 同上与 [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md) |
| top gap 为 `10 + 24 * zoom` | [`../components/LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) |
| Preview 是 page-level `MediaPreviewOverlay` | [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#10-图片工具态与预览浮层) |
| Preview 关闭后 selection、toolbar、panel 和参数不变 | 同上 |
| active authoring tool 替换标准双浮层 | [`../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md) |

源站当前按钮顺序和尺寸：

```text
人像质感调节 178
全景 62
多角度 75
打光 62
九宫格 91
高清 78
元素编辑 88
图层分离 88
宫格切分 104
标注 32
旋转 32
下载 32
预览 32
```

## 2. 时序边界

仓库中另有标注为 2026-08-27 的只读 freshness 记录。当前会话日期是
2026-08-26，因此本批保留该文档的原始 provenance，但不把未来日期记录
当成本轮当前日期事实。Batch 52 的实施授权只依赖 2026-08-26 已完成的
DOM、bundle 和 live state 合同。

## 3. Batch 52 前的 clone 事实

- Batch 51 已完成 top host 的 zoom-aware geometry；
- `ImageToolbar` 在 Batch 52 前固定 `900.5px`，只有 7 个文字动作和撤销/重做；
- `ImageNode.runAction` 把多数旧动作统一映射为 `addDerivedNode`；
- 当前没有 page-level image preview state；
- 普通 page keyboard handler 会在 Escape 时清空 selection，不能直接复用为
  Preview Escape；
- 没有 active image tool 的 toolbar replacement state。

## 4. Batch 52 后的 clone 状态

- 当前 toolbar 已为 `1092.5x49`，包含 13 项 source-shaped actions；
- `预览` 已打开 page-level `ImagePreviewOverlay`，不改变 selection、graph、
  Prompt、viewport 或 history；
- `元素编辑`、`图层分离`、`标注`、`下载` 仍保留独立 disabled 入口；
- `旋转` 的 media-backed image 入口已由 Batch 56 提升为
  `旋转与镜像` 派生节点的 bounded graph slice；无媒体图片仍 disabled；
- Batch 10/11 的历史断言仍保留 compatibility 价值，不覆盖当前 action set。

## 5. Clone 决策

- 当前 toolbar 可见壳层按 source action identity 更新；
- Preview 完整实现，因为它是只读、证据完整且不需要 graph mutation；
- 未完成的高风险动作先保持独立身份，不执行错误的派生节点或远端任务；
- 后续标注/元素编辑 batch 必须替换标准 toolbar/panel，而不是在其上新增第三层；
- 不增加 viewport clamp，不因 `1092.5px` 宽度在边缘裁切而平移 toolbar。

Batch 52 的实施和验证结果见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)，
截图唯一识图结果见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。
