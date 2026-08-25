# Batch 30 Implementation Log

> 状态：已完成。

## Planned Protection Points

1. source evidence、gap ranking、plan 和 workflow spec；
2. menu、panel、store 和 output renderer；
3. focused Playwright、screenshots 和一次性 recognition ledger；
4. cross-batch regression、engineering gates 和 final handoff。

## Implementation History

| Commit | Protection point |
|---|---|
| `ad09f9d` | source evidence、plan、workflow spec |
| `707cec2` | core implementation |
| `65fb88b` | focused Playwright and screenshot ledger |
| closing docs commit | regression, gates and final handoff |

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

## Focused Playwright

新增 `scripts/verify-liblib-batch30.py`，实际通过：

- source-backed trigger、四项顺序和 audio/picture/frame/download 相对位置；
- hover `70ms` 未打开、累计 `140ms` 打开；
- pointer leave `70ms` 保持、累计 `140ms` 关闭；
- `1009x49` toolbar、`160px` menu、trigger-relative center/gap；
- 三项 subject action 的 30 秒 guard 与 no graph mutation；
- matting panel `512x48`、node center 和 `16px` bottom gap；
- close 恢复普通 VideoGenerationPanel；
- submit spinner、disabled state 和 pending graph；
- provider/model/task type/WEBM/source dimensions/duration metadata；
- direct edge、source right `+100` world units、同 Y；
- source selection preservation；
- one-step undo/redo；
- repeated output deterministic non-overlap；
- multi-selection hiding；
- `390x844` natural clipping 和 no document overflow；
- 五张 state screenshot、一次性 contact sheet 和 zero browser errors。

一次性视觉识别已写入
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。未发现 menu 脱锚、
上下浮层错位、output 重叠或移动端 document overflow。

## Cross-Batch Regression

串行通过：

- Batch 9：image/video floating anchor、pan/zoom、多选；
- Batch 15：add-node 与 AudioNode；
- Batch 26：continuation range、target/edge 和 history；
- Batch 27：subtitle modes、rectangle history 和 pending target；
- Batch 28：audio menu/busy/dual outputs；
- Batch 29：frame capture 双入口、三类 metadata、graph 和 history；
- Batch 30：subject menu、duration guard、matting panel、pending graph 和
  history。

Batch 30 增加 subject trigger 和 chevron 后，ready-video toolbar 的当前实测
宽度从 Batch 29 的旧基线 `991px` 变为 `1009px`。因此
`scripts/verify-liblib-batch29.py` 的 desktop/mobile 两处固定宽度断言同步
更新为 `1009px`；其余 Batch 29 几何和行为断言未放宽。回归重写的旧批次
PNG 已恢复到已审核提交版本，没有带入无关 binary churn。

## Engineering Gates

- `npm run check`：通过。
  - ESLint：`0 error`，保留 9 条既有 FrameOS/共享代码 warning；
  - TypeScript：通过；
  - Next.js production build：通过。
- `npm run docs:check`：通过，224 个 Markdown、524 个本地目标。
- `git diff --check`：通过。

## Final State

Batch 30 已形成可独立接力的闭环：

```text
README
  -> SOURCE_EVIDENCE
  -> PLAN / SMART_MATTING_WORKFLOW.spec
  -> IMPLEMENTATION
  -> component specs
  -> SCREENSHOT_ANALYSIS
  -> scripts/verify-liblib-batch30.py
```

继续探索时先读 [`PLAN.md`](PLAN.md)、本目录和 component specs，不要重新
识别本批 contact sheet，也不要恢复 `画面编辑/片段截取/画面裁切` 的无证据
菜单。下一批可从 `主体消除/修改/替换` 的全屏标注器开始，但必须重新提取
工具模式、标注 geometry、候选对象、描述/替换图和提交状态，不能从当前
duration guard 推导完整工作流。
