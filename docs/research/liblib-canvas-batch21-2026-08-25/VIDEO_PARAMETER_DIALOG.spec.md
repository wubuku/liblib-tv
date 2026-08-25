# Video Parameter Dialog Specification

## Scope

- `src/components/VideoGenerationPanel.tsx`
- normal Seedance parameters
- long-video Seedance parameters

## Anchor contract

Both dialogs remain inside the node-anchored `VideoGenerationPanel` and open upward from the params footer trigger.

```text
normal
  width: 341px
  height: 445px
  left relative to panel: ~82px
  top relative to panel: ~-211.7px

long
  width: 341px
  height: 397px
  left relative to panel: ~90px
  top relative to panel: ~-163.7px
```

The implementation may express this through trigger-relative offsets, but Playwright verifies the resulting panel-relative geometry.

## Normal content

```text
比例
  Auto | 16:9 | 4:3 | 1:1 | 3:4
  9:16 | 21:9

清晰度
  480P | 720P | 1080P

视频时长                           6 s
  [4s ------------------------- 30s]

生成音频
  开启 | 关闭

生成数量
  1个 | 2个 | 4个
```

## Long-video content

- same ratio and resolution controls;
- duration range `30-300s`;
- current duration value box;
- source-shaped helper copy below the slider;
- audio segmented control;
- no count control.

## Stable selectors

- `[data-video-params-trigger]`
- `[data-video-params-menu]`
- `[data-video-ratio-option]`
- `[data-video-resolution-option]`
- `[data-video-duration]`
- `[data-video-duration-value]`
- `[data-video-audio-option]`
- `[data-video-count-option]`
- `[data-video-long-hint]`
- `[data-video-credits]`

## Non-goals

- No backend generation or billing.
- No model-menu completeness claim.
- No exact source SVG glyph extraction.
- No changes to ready-video processing commands.

