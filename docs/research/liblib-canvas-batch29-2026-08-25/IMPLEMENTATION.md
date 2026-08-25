# Batch 29 Implementation Log

> 状态：核心实现和专项 Playwright 完成；跨批回归待完成。

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

## Implementation History

| Commit | Protection point |
|---|---|
| `08dd360` | source evidence、gap ranking、plan、workflow spec |
| pending | core implementation |
| pending | focused Playwright、screenshots、one-time recognition ledger |
| pending | cross-batch regression、gates、Big Picture and handoff |

## Current Handoff

下一步新增并运行 `scripts/verify-liblib-batch29.py`。实现不得把 source poster
描述成真实解码帧，也不得把 clone overlap slot search 描述成原站精确算法。
