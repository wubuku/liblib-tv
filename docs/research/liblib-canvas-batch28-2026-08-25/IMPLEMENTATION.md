# Batch 28 Implementation Log

> 状态：核心实现完成；专项 Playwright 与完整回归待执行。

## Planned Protection Points

1. source evidence、gap ranking、plan 和 workflow spec；
2. toolbar/store/node core implementation；
3. focused Playwright + screenshot ledger；
4. cross-batch regression + final handoff。

## Core Implementation

### Store transaction

- 新增 `AudioSplitMode`、`AudioSplitOutputKind` 与
  `AudioSplitMetadata`。
- `createAudioSplit` 在一次 history transaction 中创建：
  - mode 对应的 `350x140` audio result；
  - `512x288` silent-video result；
  - `source -> audio` 与 `source -> silent video` 两条 edge。
- source 若位于 group 内，先转换为 absolute canvas position。
- audio 与 silent video 各自保存其 direct edge ID。
- 完成后只选择最右侧 silent video；一次 undo/redo 负责整批结果。

### Toolbar and node states

- trigger 已从错误的 `音频分离` 改为 `音视频分离`。
- menu 当前只有 `音视频分离 / 人声提取 / 背景音提取`，移除了
  feature flag 关闭的 `音效提取`。
- 第一项 tooltip 为 `分离内嵌音轨为独立音频节点`。
- 本地 `600ms` timer 只用于呈现 spinner、`分离中`、disabled 和
  hidden-chevron busy state。
- subtitle/audio/edit dropdown 改为各自 trigger-relative anchor，不再
  共用错误的 toolbar right offset。
- AudioNode 显示 mode-specific result label 与 source label。
- pending silent video 使用 muted resource placeholder，不进入 subtitle
  pending branch，也不复用 source poster。

### Focused smoke

2026-08-25 headless Chromium `929x874`：

- TypeScript、定向 ESLint 与 `git diff --check` 通过；
- audio menu 与 trigger 中心差 `0px`；
- menu 宽 `160px`，trigger-to-menu gap 约 `7px`；
- 三项顺序与 tooltip contract 正确，不存在 SFX item；
- busy state 可观察且 trigger disabled；
- 完成后共 `3` nodes / `2` edges / `2` split outputs；
- 两条 edge 都匹配 `Edge from {sourceId} to ...`；
- console/page error 为 `0`。

## Pending

- 新增 Batch 28 Playwright；
- 运行跨批回归与完整门禁；
- 更新 Big Picture、component specs 和 HARNESS。
