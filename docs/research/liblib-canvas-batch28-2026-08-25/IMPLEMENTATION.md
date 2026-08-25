# Batch 28 Implementation Log

> 状态：已完成。

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

## Focused Playwright

新增 `scripts/verify-liblib-batch28.py`，实际通过：

- current menu 顺序、mode selectors、AV tooltip 与 no-SFX；
- trigger-relative menu geometry；
- busy spinner、`分离中`、disabled、hidden-chevron 与重复点击 guard；
- `av / vocals / background` 三种双输出 transaction；
- mode-specific filename、result copy、duration 与 metadata；
- `source -> audio`、`source -> silent video`，且无
  `audio -> silent video`；
- top-aligned `120` world-unit clone geometry；
- final silent-video selection；
- graph single-step undo/redo；
- multi-selection hiding；
- `390x844` natural clipping 与 no document overflow；
- 四张 state screenshot、一次性 contact sheet 与 zero browser errors。

首轮脚本失败来自动态 `.selected` locator 在 graph transaction 后解析到
silent-video；改为固定 source ID locator 后，产品行为无需修改。

## Cross-Batch Regression

串行通过：

- Batch 9：image/video floating anchor、pan/zoom、多选；
- Batch 15：add-node 与 AudioNode；
- Batch 26：continuation range、target/edge 和 history；
- Batch 27：subtitle modes、rectangle history 和 pending target；
- Batch 28：audio menu/busy/dual outputs。

这些脚本共享 `http://localhost:3000`，因此没有并行运行。回归重写的旧批次
PNG 属于动态渲染差异，已恢复到审核过的提交版本，未带入无关 binary churn。

## Engineering Gates

- `npm run check`：通过。
  - ESLint：`0 error`，保留 9 条既有 FrameOS/共享代码 warning；
  - TypeScript：通过；
  - Next.js production build：通过。
- `npm run docs:check`：通过，212 个 Markdown、500 个本地目标。
- `git diff --check`：通过。

## Implementation History

| Commit | Protection point |
|---|---|
| `be5e0d9` | source evidence、gap ranking、plan、workflow spec |
| `26af8d2` | toolbar/store/node implementation and component specs |
| `6ab9de0` | focused Playwright、screenshots、one-time recognition ledger |
| final docs commit | cross-batch regression、gates、Big Picture and handoff |

## Final State

Batch 28 已形成可独立接力的闭环：

```text
README
  -> SOURCE_EVIDENCE
  -> PLAN / AUDIO_SPLIT_WORKFLOW.spec
  -> IMPLEMENTATION
  -> component specs
  -> SCREENSHOT_ANALYSIS
  -> scripts/verify-liblib-batch28.py
```

本批没有声称实现真实媒体处理。下一批高价值候选仍是 `画面编辑`、视频
首/尾帧提取和深度动作捕捉；必须重新遵循 source evidence -> spec ->
implementation -> focused Playwright 的顺序。
