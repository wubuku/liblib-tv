# Batch 33：超长视频画布过程图

> 状态：计划已落档，等待实施。目标是把原先仅存在于生成面板内部的四步
> 只读预览，推进为 source-linked、可撤销的画布级过程图。

本批复用 2026-08-25 登录态参数审计和外部文章保存的过程图截图，不重复
识别整张截图。证据能够确认：

```text
超长视频 Beta
  -> 30-300s 参数
  -> 查看生成过程
  -> 素材 / 镜头 / 候选结果 / 最终成片的画布关系
```

但证据不能确认精确节点数量、标签、坐标、后端拆段协议或真实任务状态。
因此本批只实现 request-shaped 的前端 graph handoff，并把所有校准值明确
标成 clone-only。

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：登录态参数事实、文章截图事实
   和未确认项。
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：一次性截图识别台账；
   后续先读文字，不重复打开整图。
3. [`PLAN.md`](PLAN.md)：价值排序、实施边界和验收标准。
4. [`LONG_VIDEO_PROCESS_GRAPH.spec.md`](LONG_VIDEO_PROCESS_GRAPH.spec.md)：
   graph transaction、节点层级、metadata 和选择器。
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、提交和后续接力记录。

## Scope

- 长视频提交从面板局部反馈升级为画布 graph transaction；
- source video、素材、镜头计划、候选批次、汇聚处理和最终成片的层级；
- prompt、模型、比例、清晰度、时长、音频、预计积分等 request metadata；
- 重复提交避让、source selection 和 atomic undo/redo；
- 专项 Playwright、截图 ledger、跨批回归和工程门禁。

## Boundary

本批不实现真实 Seedance 任务、自动拆段、镜头分析、候选选择、拼接、上传、
计费、轮询、任务 ID 或完成媒体。过程节点只表达前端请求和等待态，不伪造
已生成结果。
