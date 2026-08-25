# Video Clip Empty Workflow Specification

## Scope

- `src/components/nodes/VideoClipNode.tsx`
- `src/components/VideoClipEditPanel.tsx`
- React Flow type `video-clip`

## Node contract

- world size: `350x350`;
- external title: `智能剪辑 1`;
- empty message: `空空如也，请连接视频节点后操作`;
- helper label: `尝试：`;
- mode commands:
  - `讲解视频`
  - `批量广告`
  - `口播视频`
  - `素材混剪`
- commands use a single-column list with a small leading icon;
- no textarea, reference row or footer inside the node.

Stable selectors:

- `[data-video-clip-node]`
- `[data-video-clip-empty]`
- `[data-video-clip-mode]`

## Edit panel contract

The panel is mounted inside the selected node but inverse-scaled:

```text
selected video-clip node
└── VideoClipEditPanel
    position: absolute
    left: 50%
    bottom: -17px in the bordered clone shell
    translate: -50% 100%
    width: 660px
    height: 191px
    transform: scale(1 / zoom)
```

This yields:

- node/panel screen centers are equal;
- screen size remains `660x191`;
- screen gap is `16 * zoom`;
- viewport edges clip the panel naturally;
- multi-selection hides the panel.

Panel content:

- `+参考`;
- expand command;
- Prompt placeholder `描述想剪成什么效果`;
- footer mode;
- `16:9 · 720P · 30s`;
- disabled submit until Prompt has content.

Stable selectors:

- `[data-video-clip-edit-panel]`
- `[data-video-clip-reference]`
- `[data-video-clip-prompt]`
- `[data-video-clip-mode-setting]`
- `[data-video-clip-output-setting]`
- `[data-video-clip-submit]`
- `[data-video-clip-status]`

## Prototype boundary

- mode changes are local;
- reference action only reports that a video connection is required;
- submit only creates local feedback;
- no real edge-to-input resolution, editing task, media output, billing or persistence.
