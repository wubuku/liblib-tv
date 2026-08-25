# Batch 23：片段重拍时间带与 Prompt 编辑器

> 状态：原站文章流程图与当前线上 bundle 证据已完成专项审计；计划和规格已落档，实施结果待补录。

## 当前缺口

当前 clone 把片段计数、时间带和关闭按钮塞进一个自创的 `660x286` 标题面板，并要求用户必须输入修改意图后才能提交。原站流程图显示时间带是编辑器上方的独立层，编辑器本身沿用生成器的“参考 / 标记 / 角色库 + Prompt + footer”结构；当前线上 bundle 还明确支持“留空 = 原样重跑一次”。

## 本批范围

- 把 4 秒片段时间带从编辑器面板中拆成独立上层；
- 移除没有源证据的“片段重拍”标题栏；
- 增加 source-shaped 参考视频缩略项、inline 视频/range token 和生成器 footer；
- 保留 `0/5` 到 `5/5` 的片段选择上限；
- 修正空意图提交语义；
- 只产生本地任务反馈，不伪造重拍结果或模型调用。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`SEGMENT_RESHOOT_EDITOR.spec.md`](SEGMENT_RESHOOT_EDITOR.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [source article flow](../liblib-seedance-2.5-2026-08-25/evidence/segment-reshoot-flow.png)
- [`live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- 当前组件规格：[`../components/SegmentReshootPanel.spec.md`](../components/SegmentReshootPanel.spec.md)

