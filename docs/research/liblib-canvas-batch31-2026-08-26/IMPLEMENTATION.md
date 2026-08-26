# Batch 31 Implementation Log

> 状态：计划已落档，等待主体编辑器实现。

## Planned Protection Points

1. source evidence、缺口排序、workflow spec 和 component spec；
2. mark 类型、PictureEditPanel、VideoNode 接线和 store graph transaction；
3. focused Playwright、clone screenshot ledger 和零浏览器错误；
4. 跨批回归、工程门禁、最终 handoff 和 commit/push。

## Current State

- Batch 30 已完成主体菜单纠偏和智能抠像。
- 默认 ready-video fixture 为 `30s`，三项主体编辑目前仍只显示 source-backed
  `视频大于15秒，暂不支持该功能`。
- Batch 31 已将可实施的 mark/tool/mode contract 写入：
  - [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
  - [`PLAN.md`](PLAN.md)
  - [`PICTURE_EDIT_WORKFLOW.spec.md`](PICTURE_EDIT_WORKFLOW.spec.md)
  - [`../components/PictureEditPanel.spec.md`](../components/PictureEditPanel.spec.md)

## Interruption Handoff

下一步先实现 `PictureEditPanel` 和 `PictureEditMark` 类型，再接入
`VideoNode` 的 `picture-edit` active tool。不要把 `subjectRemove`、
`subjectModify`、`subjectReplace` 拆成三个互不一致的 panel，也不要把本地
候选对象或替换图写成原站识别/图库结果。

本批没有新增原站截图；继续探索前先读 `SOURCE_EVIDENCE.md` 和
`SCREENSHOT_ANALYSIS.md`，只有出现新的视觉问题才使用最小 crop。
