# LibTV 画布 Batch 7：整理预览忠实度

> 建档日期：2026-08-25  
> 状态：计划与规格已落档，实施中  
> 目标：根据已保存的原站整理预览截图，纠正当前 clone 的节点拓扑、缩放构图和确认卡位置。

## 为什么做这一批

当前 clone 已经支持 `Option/Alt+Shift+F` 和“整理画布”入口，但它只把普通节点按三列网格铺开，再把分组推到最右侧。这个结果与原站截图的语义拓扑、缩放和确认状态都明显不同。

本批只处理证据充分、影响直接的整理预览：

- 左侧素材列；
- 中间剧本执行与分镜结果；
- 右侧图片组、视频组和组内视频；
- 更右上方剧本；
- 左下两行确认卡；
- 还原、保留和 history 回归。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、价值排序、范围和验收标准
- [`ORGANIZE_CANVAS.spec.md`](ORGANIZE_CANVAS.spec.md)：整理拓扑、viewport 与 fallback 规格
- [`ORGANIZE_CONFIRMATION.spec.md`](ORGANIZE_CONFIRMATION.spec.md)：确认卡几何、层级和交互规格
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和后续接力记录

## 证据入口

- 原站整理预览：`docs/design-references/liblib-original-organize-preview-2026-08-25.png`
- 当前 clone 旧整理预览：`docs/design-references/liblib-clone-batch3-organize-preview-desktop-2026-08-25.png`
- 当前项目节点身份与尺寸：`docs/research/liblib-live-2026-08-25/README.md`
- 原站结构化节点数据：`docs/research/liblib-live-2026-08-25/full-canvas-audit.json`

## 证据边界

原站截图直接证明屏幕构图和确认卡视觉，但没有保存整理完成后的 DOM transform。规格中的世界坐标由截图、已知节点尺寸和截图中的约 `28%` 缩放反推，是本 clone 的实现候选，不登记为原站 DOM 原始事实。

