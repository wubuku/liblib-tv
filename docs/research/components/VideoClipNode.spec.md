# VideoClipNode

## Purpose

`src/components/nodes/VideoClipNode.tsx` is the dedicated `视频编辑 Beta` / `智能剪辑` node. It must remain separate from `ShotBreakdownNode` and from the video generation panel.

## Contract

- React Flow type: `video-clip`
- Default world size: `350x350`
- Default title: `智能剪辑 1`
- Empty message: `空空如也，请连接视频节点后操作`
- Modes: `讲解视频`, `批量广告`, `口播视频`, `素材混剪`
- Empty prompt placeholder: `描述想剪成什么效果`
- Default settings: `16:9 · 720P · 30s`
- Submit remains disabled until the prompt has content
- Node body and Prompt editor are separate surfaces

## Node Structure

The `350x350` node contains:

- external title only; no internal `智能剪辑 Beta` header;
- scissors empty icon;
- source-confirmed connection message;
- `尝试：`;
- four mode commands in a single-column list.

It does not contain a textarea, reference row or footer.

## Edit Panel

`src/components/VideoClipEditPanel.tsx` is mounted only for a single selected node:

- `660x191` screen size;
- node-centered;
- inverse-scaled by `1 / zoom`;
- source semantic `16 * zoom` lower gap;
- `+参考`, expand, Prompt, mode, output settings and circular submit;
- naturally clipped at viewport edges;
- hidden during multi-selection.

## Interaction Model

Click-driven local prototype:

1. Select one of the four node-level suggestion modes.
2. Enter a Prompt in the lower panel.
3. Use the reference entry and settings affordances as local UI placeholders.
4. Enable the send command once the Prompt is non-empty.

There is no backend edit job or generated media persistence in this repository.

Verification: `scripts/verify-liblib-batch25.py`.
