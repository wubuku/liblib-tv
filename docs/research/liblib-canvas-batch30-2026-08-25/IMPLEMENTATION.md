# Batch 30 Implementation Log

> 状态：核心实现完成，等待专项 Playwright 与回归。

## Planned Protection Points

1. source evidence、gap ranking、plan 和 workflow spec；
2. menu、panel、store 和 output renderer；
3. focused Playwright、screenshots 和一次性 recognition ledger；
4. cross-batch regression、engineering gates 和 final handoff。

## Implementation History

| Commit | Protection point |
|---|---|
| `ad09f9d` | source evidence、plan、workflow spec |
| pending | core implementation |
| pending | focused Playwright and screenshot ledger |
| pending | regression, gates and final handoff |

## Core Implementation

### Source-backed toolbar correction

- 删除无证据的 `画面编辑 / 片段截取 / 画面裁切`。
- 新增 `主体消除` trigger 和四项 source-order menu。
- subtitle、audio、picture-edit、frame 四组共用 `100ms` open /
  `120ms` close hover timers。
- click toggle 继续可用，避免只支持鼠标 hover 的不可达状态。

### Subject validation

- 三项 subject action 进入同一个 `selectPictureEdit` 入口。
- 当前 Add Node `30s` fixture 命中精确 source copy：
  `视频大于15秒，暂不支持该功能`。
- guard 不创建 node/edge，也不写 history。
- `<2.5s` 的 duration 文案也按 source key 结构保留；valid-duration
  full editor 不在本批伪装实现。

### Smart matting panel

- 新增 `SmartMattingPanel`，使用 React Flow `NodeToolbar` 锚定节点下方。
- width 按 source clamp 到 `360..560px`，当前 `512px` node 得到
  `512x48px` panel。
- panel 包含 close、`智能抠像`、未计算 power `--`、generate/spinner。
- 打开 panel 时普通 VideoGenerationPanel 卸载；close 恢复 generator。

### Graph transaction

- 新增 `SmartMattingMetadata` 和 `createSmartMatting`。
- 单次 transaction 创建 `512x288` pending VIDEO 与 direct source edge。
- output 名称 `${sourceLabel}-智能抠像`，model
  `volcano-portrait-matting`，generator type `PICTURE_EDIT`。
- request-shaped metadata 保存 provider、task type、WEBM、source
  resolution/duration 和 edge ID。
- 首个 output 使用 source right `+100` world units；重复结果复用现有
  deterministic vertical slot search。
- source selection 保留，transaction 只写一个 history snapshot。

### Pending renderer

- Smart matting output 使用独立 pending body：
  `智能抠像结果 / 智能抠像 · 等待媒体资源`。
- 不复用 source poster，不伪造透明通道媒体。
- DOM 暴露 source、edge、provider、model、format、dimensions 和 duration。

## Browser Smoke

2026-08-25 headless Chromium `929x874`：

- hover `70ms` 未打开，累计 `130ms` 后 menu 可见；
- menu 顺序为消除、修改、替换、智能抠像；
- default 30 秒 guard 精确显示且 graph 保持 `1 node / 0 edge`；
- panel 为 `512x48px`，与 source 同左边界，下方 gap `16px`；
- submit spinner 可观察；
- output graph 为 `2 nodes / 1 edge`；
- output 的 screen-space gap 折算约 `101` world units，Y 仅有边框取整差；
- source 保持唯一 selected；
- console/page error 为 `0`。

## Handoff

若会话在专项验证前中断，新增 `scripts/verify-liblib-batch30.py` 并从
[`PLAN.md`](PLAN.md) 第 2 节第 6 项继续；不要重新识别旧截图，也不要恢复
`画面编辑/片段截取/画面裁切` 的无证据菜单。
