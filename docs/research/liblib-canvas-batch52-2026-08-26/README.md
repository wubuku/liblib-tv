# Batch 52：当前图片工具条与只读预览

> 状态：计划已落档（2026-08-26）。本批把标准图片选中态从历史
> `900.5x49` 工具条升级到当前源站的 13 项动作集合，并实现证据完整、
> 无 graph 副作用的 page-level 图片预览。

## 目标

```text
single selected image
  -> current 9 text actions + 4 icon actions
  -> 1092.5x49 measured toolbar snapshot
  -> preview opens fixed page overlay
  -> close / Escape restores unchanged selection and graph
```

## 文档入口

- [`PLAN.md`](PLAN.md)：范围、风险、实现顺序和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：源站事实、clone 差距和证据时序边界；
- [`../components/ImagePreviewOverlay.spec.md`](../components/ImagePreviewOverlay.spec.md)：
  Preview 的页面层级、几何和生命周期合同；
- `IMPLEMENTATION.md`：实施后补充代码、验证、截图台账和 commit/push。

## 本批边界

- 当前 13 项按钮顺序、test id、按钮尺寸和 toolbar 总尺寸按源站 DOM 证据实现；
- 继续使用 Batch 51 的 `10 + 24 * zoom` 顶部 host 公式；
- Preview 是本批唯一新增的完整动作闭环；
- 元素编辑、图层分离、标注、旋转和下载保留独立动作身份，但在对应专用
  batch 完成前不得复用 `addDerivedNode` 或伪造远端成功；
- 不修改视频、FrameOS、Director、Auto Link 或真实 provider。

