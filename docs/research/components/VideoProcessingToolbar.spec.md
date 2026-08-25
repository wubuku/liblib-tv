# VideoProcessingToolbar

## Purpose

`src/components/VideoProcessingToolbar.tsx` is the selected-ready-video top toolbar. It is rendered with React Flow `NodeToolbar`, not as a fixed page toolbar.

## Commands

`高清`, `片段重拍`, `逐帧拉片`, `智能续写`, `智能去字幕`, `音频分离`, `画面编辑`, download poster, preview, undo, redo.

## Behavior

- `高清` toggles a local visual enhancement state.
- `片段重拍` and `智能续写` switch the lower editor.
- `逐帧拉片` creates a linked `shot-breakdown` node through `canvasStore.addDerivedNode`.
- Subtitle, audio, and edit commands open local action menus.
- Toolbar pointer/click events stop propagation so clicking a command cannot reselect or overwrite a newly created derived node.

## Positioning

`NodeToolbar position="top" offset={16}`. Width is `920px`, height is `49px`, and the toolbar remains screen-sized through React Flow's toolbar layer.
