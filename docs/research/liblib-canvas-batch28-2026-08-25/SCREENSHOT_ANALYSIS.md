# Batch 28 Screenshot Analysis

## 1. Source Visual Reuse

本批规划阶段没有重复识别原站整图。

复用：

- Batch 24 ready-video toolbar 视觉记录；
- Batch 9 top toolbar node-relative anchor；
- Batch 15 AudioNode 本地 renderer；
- Batch 27 ready-video dropdown、derived graph 和移动端视觉上下文。

当前 bundle 将 trigger label 暴露为 `音视频分离`。旧截图记录的 `音频分离` 只代表旧采样画面；运行态文案以 2026-08-25 当前 bundle 为准。

## 2. Clone Ledger

专项脚本已生成：

| File | Viewport / state |
|---|---|
| [`liblib-clone-batch28-audio-menu-929-2026-08-25.png`](../../design-references/liblib-clone-batch28-audio-menu-929-2026-08-25.png) | three-item source menu |
| [`liblib-clone-batch28-audio-busy-929-2026-08-25.png`](../../design-references/liblib-clone-batch28-audio-busy-929-2026-08-25.png) | spinner + 分离中 |
| [`liblib-clone-batch28-audio-graph-929-2026-08-25.png`](../../design-references/liblib-clone-batch28-audio-graph-929-2026-08-25.png) | source + audio + silent video |
| [`liblib-clone-batch28-audio-mobile-390-2026-08-25.png`](../../design-references/liblib-clone-batch28-audio-mobile-390-2026-08-25.png) | natural canvas clipping |
| [`liblib-clone-batch28-audio-contact-sheet-2026-08-25.png`](../../design-references/liblib-clone-batch28-audio-contact-sheet-2026-08-25.png) | four-state ledger |

## 3. One-Time Contact-Sheet Recognition

识别对象：
`liblib-clone-batch28-audio-contact-sheet-2026-08-25.png`。

采样条件：

- clone route `http://localhost:3000`；
- 2026-08-25；
- desktop `929x874`、mobile `390x844`；
- Chromium device scale factor `1`；
- states：menu、busy、fit-view output graph、mobile menu。

### Desktop menu

- 顶部工具条保持 selected-ready-video 的 node-relative 横条结构。
- `音视频分离` trigger 有 waveform icon、label 和下 chevron。
- dropdown 水平居中在该 trigger 下方，不再使用共享 right offset。
- 菜单从上到下为 `音视频分离 / 人声提取 / 背景音提取`。
- 菜单没有 `音效提取`，三项 icon、文字基线与行高一致。
- dropdown 覆盖在 source video 上方，z-order 清晰，没有被 video body
  或 lower generation panel 截断。

### Busy

- action 后 dropdown 关闭。
- waveform icon 替换为 spinner，label 改为 `分离中`，chevron 消失。
- busy entry 保持在原 trigger 位置，没有引起 toolbar 高度或相邻命令
  的明显跳动。
- source video 与 lower generation panel 在 timer 期间保持可见。

### Output graph

- fit-view 中从左到右依次为 source video、audio result、silent-video
  result，三者顶边对齐。
- AudioNode 使用 mode-specific `独立音轨结果`、waveform placeholder、
  `00:30` 和 source copy。
- silent video 使用深色 muted placeholder，不复用 source poster，也没有
  subtitle pending copy。
- silent video 是唯一青色选中节点；source 与 audio 未选中。
- 可见连接表达 `source -> audio` 与 `source -> silent video`。较长的
  direct edge 从 audio 下方/后方穿过是该双 source-edge 拓扑的自然结果，
  不是 `audio -> silent video`。

### Mobile

- `920px` screen-sized toolbar 自然跨出 `390px` viewport，两侧被画布裁切。
- audio dropdown 仍以可见 trigger 为锚点，没有回到页面右侧或脱离 trigger。
- menu、video body、lower panel 和 bottom toolbar 的 z-order 可辨识。
- DOM 断言确认 document/body 均无横向 overflow；裁切发生在 canvas
  viewport 内。

## 4. Evidence Classification

### DOM + screenshot fact

- clone menu 与 trigger 中心一致、宽 `160px`、垂直 gap 约 `7px`。
- 三项菜单、busy copy、silent selection 和 mobile clipping 与脚本断言一致。
- output graph 为两条 source edge。

### Source-backed behavior

- 三项 current menu、无 SFX、busy label、output naming、双 source-edge、
  最右结果 selection 来自当前线上 bundle。

### Clone-only visual decision

- `120` world-unit 两段横向 gap。
- CSS waveform、muted placeholder 和 `600ms` busy timer。
- 本批 output graph 截图是 clone 验证，不是原站像素证据。

## 5. Re-inspection Rule

contact sheet 已于 2026-08-25 识别一次，结果已写入本文件。后续除非截图
或实现变化，不重复识别整图；先复用以上文字记录。
