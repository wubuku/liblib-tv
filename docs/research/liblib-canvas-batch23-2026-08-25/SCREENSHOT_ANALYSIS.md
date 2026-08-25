# Batch 23 Screenshot Analysis

## 1. Source article flow

### 文件

- `docs/research/liblib-seedance-2.5-2026-08-25/evidence/segment-reshoot-flow.png`
- 来源：外部 LibTV Seedance 2.5 功能文章中的流程截图
- 入库尺寸：`1104x886`
- 状态：四个片段重拍连续状态组成的 2x2 拼图
- 采样日期：2026-08-25
- 识图次数：1

### Source screenshot fact

- 四个 quadrant 使用同一个 ready video 节点与下方编辑流程：
  1. 未选片段，计数 `0/5 个片段`；
  2. 首个 `4.0s` 片段被 cyan outline 选中，计数变为 `1/5 个片段`；
  3. Prompt 自动出现源视频与 `00:00-00:04` range token；
  4. 用户在 token 后输入“改为女孩从门缝里面走出来，然后走出镜头”。
- 片段时间带是独立圆角 surface，位于 Prompt editor 上方，中间有可见间距。
- 时间带由连续缩略帧组成；selected 区间覆盖在缩略帧上，而不是把整条视频均分成彼此分离的卡片。
- Prompt editor 没有“片段重拍”标题栏。
- editor 顶行可见 `参考`、`标记`、`角色库` 和右侧展开命令。
- Prompt 区左上有源视频 reference tile，带约 `30.1s` 时长。
- range 以独立灰色 chip 呈现；视频引用也有独立 token 视觉。
- Footer 可见 `2.5` 与 premium 标识、`720P · 1个`、音频控制、积分/字数区域和圆形 submit。

### Pixel-backed inference

- 该文件是文章排版后的四状态拼图，每个 quadrant 内 UI 已缩放。
- filmstrip/editor 的宽度一致；editor 高度约为其宽度的 `0.38-0.40`。
- 这些比例可指导 clone 密度，但不能当作 source DOM rect。

### Unknown

- 原始 viewport、zoom、DOM rect 和字号没有保留。
- 不确认 filmstrip 的滚动、拖拽选择或 hover 行为。
- 截图只直接展示首个 `4.0s` 区间，不展示多区间的具体排布方式。
- 没有真实任务完成后的结果节点。

## 2. Bundle-backed behavior

`live-script-string-evidence.json` 直接确认：

- `segmentRemakeDurationLimit`：源视频不少于 4 秒；
- `segmentRemakeRangeCount`：`{current}/{max} 个片段`；
- `segmentRemakeNoRanges`：未选择片段时编辑整段视频；
- `segmentRemakeWholeIntentPlaceholder`：留空可原样重跑；
- `segmentRemakePromptRange` 和 `segmentRemakePromptRangeWithIntent`：range 与 intent 的投影语义。

这些是当前线上代码文本证据，不等价于在当前项目中成功提交任务。

## 3. Current clone code audit

- 单一 `660x286` surface 同时包含：
  - `44px` clone-only 标题栏；
  - 内嵌 `62px` 分段卡片；
  - Prompt 与 footer。
- 时间段是八个彼此分离、等宽的按钮，不是连续 filmstrip。
- Prompt 只是纯文本段落，没有 source video tile、视频 token 或 range chip。
- submit 在 `intent.trim()` 为空时 disabled，与 bundle 的整段重跑语义冲突。

## 4. Re-inspection rule

实施前不再打开该图。后续优先读取本文；只有原始截图、源 DOM、filmstrip 拖拽行为或真实结果态进入范围时才重新采样。

