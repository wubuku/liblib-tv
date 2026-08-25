# VideoProcessingToolbar

## Purpose

`src/components/VideoProcessingToolbar.tsx` is the selected-ready-video top toolbar. It is rendered with React Flow `NodeToolbar`, not as a fixed page toolbar.

## Commands

`高清`, `片段重拍`, `逐帧拉片`, `智能续写`, `智能去字幕`, `音视频分离`, `画面编辑`, download poster, preview, undo, redo.

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
- Edit commands still open a local prototype action menu.
- Toolbar pointer/click events stop propagation so clicking a command cannot reselect or overwrite a newly created derived node.

## Positioning

`NodeToolbar position="top" offset={16}`. Width is `920px`, height is `49px`, and the toolbar remains screen-sized through React Flow's toolbar layer.

Each dropdown is absolutely anchored to its own trigger wrapper, centered below the
button with a `7px` trigger-to-menu gap and a fixed `160px` screen width. It must
not use a shared right offset because that detaches subtitle/audio/edit menus from
their initiating controls.
