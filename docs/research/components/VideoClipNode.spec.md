# VideoClipNode

## Purpose

`src/components/nodes/VideoClipNode.tsx` is the dedicated `视频编辑 Beta` / `智能剪辑` node. It must remain separate from `ShotBreakdownNode` and from the video generation panel.

## Contract

- React Flow type: `video-clip`
- Default world size: `350x350`
- Default title: `智能剪辑 1`
- Modes: `讲解视频`, `批量广告`, `口播视频`, `素材混剪`
- Empty prompt placeholder: `描述想剪成什么效果`
- Default settings: `16:9 · 720P · 30s`
- Submit remains disabled until the prompt has content

## Interaction Model

Click-driven local prototype:

1. Select one of the four editing modes.
2. Enter a prompt.
3. Use the reference entry and settings affordances as local UI placeholders.
4. Enable the send command once the prompt is non-empty.

There is no backend edit job or generated media persistence in this repository.
