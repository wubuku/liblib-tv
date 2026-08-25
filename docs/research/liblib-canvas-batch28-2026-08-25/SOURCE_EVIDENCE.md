# Batch 28 Source Evidence

> 采样日期：2026-08-25  
> 页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. Evidence Boundary

本批重新请求了当前 canvas HTML，并从页面实际声明的静态 chunk 中提取音视频分离代码。

无登录 Playwright 会被重定向到 `https://www.liblib.tv/` 首页，因此：

- 本批没有把匿名页面当作画布 DOM 证据；
- 没有新增原站 dropdown 或结果节点截图；
- menu state、busy state、校验和 graph handoff 主要来自当前线上 bundle；
- 视觉背景复用已有登录态 ready-video toolbar 截图；
- 未由 DOM/screenshot 测量的结果节点距离必须标为 clone calibration。

## 2. Current Bundle Set

### Toolbar

`2jbcm5mok_bay.js` 中 `VideoNodeToolbar`：

- dropdown shell：
  - `minWidth: 160px`；
  - `borderRadius: 12px`；
  - `padding: 6px`；
  - item `fontSize: 13px`；
  - item `padding: 8px 10px`；
  - trigger 高 `32px`，带 `12px` chevron。
- audio items 顺序：
  1. `avSeparateMenuLabel`；
  2. `vocalExtractLabel`；
  3. `backgroundExtractLabel`；
  4. `sfxExtractLabel` 仅在 `SHOW_VOCAL_SPLIT_SFX_UI` 为 true 时出现。
- busy 时：
  - trigger disabled；
  - icon 替换为 spinner；
  - label 替换为 `separatingLabel`；
  - chevron 隐藏。

同一当前 bundle 中：

- `SHOW_VOCAL_SPLIT_SFX_UI = false`；
- `avSeparateMenuLabel = 音视频分离`；
- `vocalExtractLabel = 人声提取`；
- `backgroundExtractLabel = 背景音提取`；
- `sfxExtractLabel = 音效提取`；
- `separatingLabel = 分离中`；
- `separateAvTooltip = 分离内嵌音轨为独立音频节点`。

因此当前可见菜单是三项，不是 clone 现有的人声/背景音/音效三项。

### Video node orchestration

`15epcn_e-6pl6.js` 中：

- `onSeparateAvClick` 执行本地音视频分离，导出音频与无声视频；
- `onVocalSplitClick("vocals" | "background")` 进入服务任务；
- `isSeparatingAv || isVocalSplitting` 共同驱动 toolbar busy；
- 人声分离 client guard：
  - duration 大于 `180s`：`视频时长超过 3 分钟，暂不支持人声分离`；
  - `hasAudioTrack === false`：`当前视频无音轨，无法使用人声分离`；
- 音效分支仍保留 modal state 和 handler，但 toolbar feature flag 关闭，不能据此把入口显示出来。

### Output topology

`1l_h2-a5rbvk3.js` 中：

- mode label：
  - `vocals -> 人声`；
  - `background -> 背景音`；
  - `sfx -> 音效`。
- audio node：
  - type `AUDIO`；
  - name `${sourceName}_${audioLabel}`；
  - 位于 source 右侧；
  - edge `source video -> audio`。
- silent video：
  - type `VIDEO`；
  - name `${sourceName}_无声`；
  - 位置以 audio node 为右侧查找 anchor；若无 audio 则以 source 为 anchor；
  - edge 仍为 `source video -> silent video`，不是 `audio -> silent video`。
- audio 与 silent video 在一个 snapshot 中创建；
- 创建结束后选择最后一个有效输出，通常是最右侧 silent video。

服务允许只返回 audio 或只返回 silent video；当前 clone 不模拟失败矩阵，只实现可审查的“双输出成功路径”。

## 3. Existing Screenshot Reuse

- [`../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md) 已记录 ready-video 顶部处理工具条。
- Batch 9 已记录 toolbar 的 node-relative anchor、pan/zoom 和 natural clipping。
- Batch 27 已记录当前 clone ready-video、dropdown 和 derived graph 的视觉上下文。

旧截图把入口记为 `音频分离`；当前 bundle 的 trigger 取第一项 `音视频分离` 作为 label。对本批运行态文案，以当前 bundle 为准。

## 4. Source Fact / Inference / Clone Decision

### Source fact

- 当前可见 menu 为 `音视频分离 / 人声提取 / 背景音提取`。
- `音效提取` 受 false feature flag 控制，不可见。
- busy trigger 显示 spinner 和 `分离中`。
- 人声/背景音限制为 `<=180s` 且需有音轨。
- 成功可创建 audio 与 silent video。
- audio 和 silent video 都由 source video 连出。
- audio 先创建，silent video 以 audio 为位置 anchor，最终选择最后输出。
- graph outputs 共用一次 snapshot。

### Inference

- clone 沿用当前 `350x140` AudioNode 与 `512x288` VideoNode 尺寸。
- clone 使用固定 `120` world-unit 横向间距表达 `findClosestRightFlowPosition` 的右侧拓扑；原站精确碰撞避让值未由 DOM 测量。
- 无声视频使用 pending/resource placeholder，而不复用 source poster 冒充已完成像素处理。

### Clone-only decision

- busy 使用短本地 timer，使 loading state 可观察；不模拟真实任务耗时。
- 每次 action 固定产出 audio + silent video 的代表性成功路径。
- audio node 使用本地 waveform placeholder，不播放分离后的真实音频。
- output metadata 保存在 Zustand 内存，刷新后丢失。
