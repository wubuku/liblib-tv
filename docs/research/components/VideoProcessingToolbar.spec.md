# VideoProcessingToolbar

## Purpose

`src/components/VideoProcessingToolbar.tsx` is the selected-ready-video top toolbar. It is rendered with React Flow `NodeToolbar`, not as a fixed page toolbar.

## Commands

`高清`, `片段重拍`, `逐帧拉片`, `智能续写`, `智能去字幕`, `音视频分离`,
`主体消除`, `截取首帧`, download poster, preview, undo, redo.

## Behavior

- `高清` toggles a local visual enhancement state.
- `片段重拍` and `智能续写` switch the lower editor.
- `逐帧拉片` creates a linked `shot-breakdown` node through `canvasStore.addDerivedNode`.
- `智能去字幕` opens a two-item dropdown with `智能去字幕` and `框选去字幕`; either item enters the dedicated subtitle workflow rather than writing temporary feedback.
- The subtitle entry tooltip is `AI一键去除视频字幕，仅支持中英文字幕`.
- `音视频分离` opens the current three-item source menu in this order:
  `音视频分离`, `人声提取`, `背景音提取`.
- The first audio item tooltip is `分离内嵌音轨为独立音频节点`.
- Audio processing replaces the icon with a spinner, changes the trigger copy to
  `分离中`, hides the chevron and disables the trigger until the graph transaction
  completes.
- The currently feature-flagged-off `音效提取` entry is not rendered.
- `主体消除` opens the current source-order picture-edit menu:
  `主体消除`, `主体修改`, `主体替换`, `智能抠像`.
- The trigger uses the first item label instead of a generic `画面编辑` label.
- The former clone-only `片段截取 / 画面裁切` items are removed.
- The three subject-edit entries first run source validation. The current 30-second
  Add Node fixture displays the source copy `视频大于15秒，暂不支持该功能`
  without changing the graph.
- `智能抠像` opens a compact lower panel; generate creates one linked pending
  video with request-shaped matting metadata.
- `截取首帧` opens the source-order frame menu:
  `截取首帧`, `截取尾帧`, `截取当前帧`.
- A frame command creates one linked image output while preserving source
  selection. See Batch 29 for metadata, time and overlap contracts.
- Toolbar pointer/click events stop propagation so clicking a command cannot reselect or overwrite a newly created derived node.

## Positioning

`NodeToolbar position="top" offset={16}`. The source toolbar uses content width
(`w-max`); with the current command set it is `991px` wide and `49px` high. It
remains screen-sized through React Flow's toolbar layer.

Each dropdown is absolutely anchored to its own trigger wrapper, centered below the
button with a `7px` trigger-to-menu gap and a fixed `160px` screen width. It must
not use a shared right offset because that detaches subtitle/audio/edit menus from
their initiating controls.

The four dropdown groups support the source hover model (`100ms` open and `120ms`
close) while retaining click toggle for keyboard/test reachability.
