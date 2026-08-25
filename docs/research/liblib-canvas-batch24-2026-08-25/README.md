# Batch 24：逐帧拉片持久化结果组

> 状态：计划已落档，待实施与验证。

## 当前缺口

当前 clone 的逐帧拉片输入节点已覆盖视频素材、三个拆解维度和本地完成状态，但把结果放在选中节点下方的 `660x260` tab 浮层中。源文章截图显示，结果会作为画布上的持久化媒体组展开，而不是依赖分析节点继续保持选中。

当前实现还包含没有源证据的 tabs、勾选状态、`加入参考` footer、`分析完成 · 本地示例结果` 和只展示 `S01-S04` 的简化结果。

## 本批范围

- 对齐 ready 输入节点的素材标签、时长/分辨率和预览层级；
- 保留 bundle 已确认的上传、从画布选择、维度和 running 文案；
- 把完成结果改为画布上的三个分镜组、一个动态组和一个音乐节点；
- 覆盖 `S01-S08`、`M01-M03` 和 BGM 波形；
- 一次完成作为一个可撤销/重做的画布事务；
- 删除 clone-only 的选中态结果浮层。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`SHOT_BREAKDOWN_WORKFLOW.spec.md`](SHOT_BREAKDOWN_WORKFLOW.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [source entry screenshot](../liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-entry.png)
- [source output screenshot](../liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-output.png)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- [`live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
- 当前组件规格：[`../components/ShotBreakdownNode.spec.md`](../components/ShotBreakdownNode.spec.md)

## 原型边界

本批不调用真实上传、逐帧分析、Seedance、积分、账户资产或持久化 API。结果媒体使用仓库本地素材；本地短暂 running 状态只用于演示前端状态转换，不声称复刻原站任务耗时。
