# Batch 29 Implementation Log

> 状态：已完成。

## Planned Protection Points

1. source evidence、gap ranking、plan 和 workflow spec；
2. toolbar/player/store/image-node core implementation；
3. focused Playwright + screenshot ledger；
4. cross-batch regression + final handoff。

## Core Implementation

### Store transaction

- 新增 `VideoFrameCaptureKind` 与 `VideoFrameCaptureMetadata`。
- `createVideoFrameCapture` 在一次 history transaction 中创建一个
  `512x288` image result 和一条 direct source edge。
- first/current time 会 clamp；last 使用 `duration - 0.05`，无 duration
  时拒绝创建。
- source 若位于 group 内，先转换为 absolute canvas position。
- 首个 output 使用 source right `+100` world units、同 Y。
- 重复 capture 保持同列，按 `288 + 48` world units 向下搜索空 slot。
- transaction 完成后 source 保持唯一 selected。

### Toolbar and player entries

- 顶部 frame group 已插入 `画面编辑` 后、download divider 前。
- trigger 为 `截取首帧` + chevron，menu 顺序为首、尾、当前。
- toolbar 从旧 clone 固定 `920px` 改为 source-shaped `w-max`；新增命令后
  当前 desktop 运行宽度为 `991px`。
- 播放栏增加可调 playhead、`28x28` camera current-frame shortcut 和
  hover menu。
- player hover menu 使用 `bottom-full right-0` 与 `8px` hover bridge。
- 成功后 source body 显示短生命周期 `{name}已截取，并添加到画布`。

### Image result

- output 使用 source poster 作为明确标注的 prototype bitmap。
- ImageNode 暴露 kind/source/time/name/alt/edge selectors。
- 图片 alt 使用 capture metadata 的 source-backed alt。
- 点击 output 后仍进入普通 ImageToolbar + ImageEditPanel，不创建独立
  frame node renderer。

### Browser smoke

2026-08-25 headless Chromium `929x874`：

- top toolbar 宽 `991px`；
- frame menu 宽 `160px`，menu/trigger center delta `0px`；
- first output gap 为 `100` world units、Y delta `0`；
- repeated last output 与 first output 不重叠；
- last metadata 为 `29.95s`；
- player hover menu 为首、尾、当前三项；
- camera click 在 `12.5s` playhead 创建 current result；
- source 始终是唯一 selected；
- console/page error 为 `0`。

## Focused Playwright

新增 `scripts/verify-liblib-batch29.py`，实际通过：

- top frame group source order 和画面编辑/download 相对位置；
- `991x49` toolbar、`160px` dropdown、trigger-relative center/gap；
- first/last/current 的 time、name、alt 和 image alt；
- source-to-image direct edge 和 metadata edge ID；
- first output `100` world-unit gap、同 Y；
- repeated output deterministic non-overlap；
- source selection preservation 和连续 capture；
- local `12.5s` playhead；
- player camera direct-current shortcut 和 hover 三项 menu；
- one-step undo/redo；
- output 重新选择后的普通 ImageToolbar/ImageEditPanel；
- multi-selection hiding；
- `390x844` natural clipping 和 no document overflow；
- 五张 state screenshot、一次性 contact sheet 和 zero browser errors。

一次性视觉识别已写入 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。
未发现工具条换行、dropdown 脱锚、player menu 遮挡、output 重叠或浮层错位。

## Cross-Batch Regression

串行通过：

- Batch 9：image/video floating anchor、pan/zoom、多选；
- Batch 15：add-node 与 AudioNode；
- Batch 26：continuation range、target/edge 和 history；
- Batch 27：subtitle modes、rectangle history 和 pending target；
- Batch 28：audio menu/busy/dual outputs；
- Batch 29：frame capture 双入口、三类 metadata、graph 和 history。

这些脚本共享 `http://localhost:3000`，因此没有并行运行。回归重写的旧批次
PNG 和 Batch 29 动态渲染差异均恢复到已审核提交版本，没有带入无关 binary
churn。

## Engineering Gates

- `npm run check`：通过。
  - ESLint：`0 error`，保留 9 条既有 FrameOS/共享代码 warning；
  - TypeScript：通过；
  - Next.js production build：通过。
- `npm run docs:check`：通过，218 个 Markdown、514 个本地目标。
- `git diff --check`：通过。

## Implementation History

| Commit | Protection point |
|---|---|
| `08dd360` | source evidence、gap ranking、plan、workflow spec |
| `e6f7ca5` | toolbar/player/store/image-node core implementation |
| `d85e2b1` | focused Playwright、screenshots、one-time recognition ledger |
| final docs commit | cross-batch regression、gates、Big Picture and handoff |

## Final State

Batch 29 已形成可独立接力的闭环：

```text
README
  -> SOURCE_EVIDENCE
  -> PLAN / FRAME_CAPTURE_WORKFLOW.spec
  -> IMPLEMENTATION
  -> component specs
  -> SCREENSHOT_ANALYSIS
  -> scripts/verify-liblib-batch29.py
```

本批没有声称实现真实视频解码或上传。下一批高价值候选是 `画面编辑`、
`深度动作捕捉` 和 source-backed `高清视频`；必须重新遵循 source evidence
-> spec -> implementation -> focused Playwright 的顺序。
