# ImageElementEditMode

## Purpose

复刻 LibTV selected image 的空元素编辑 authoring mode。它是 node-local L3
状态：替换标准图片 toolbar/panel，但不产生 graph result。

## State Ownership

- `uiStore.imageElementEdit`：active image node identity 和媒体描述；
- `canvasStore`：不保存 active tool，不产生 graph history；
- `ImageNode`：执行 `standard / annotate / element-edit` 互斥渲染；
- `ImageElementEditToolbar`：固定尺寸 top toolbar 和空态 tools；
- `ImageElementEditSurface`：跟随 node 的 stage、guide 和 fixed-size record panel。

元素编辑与标注必须是两个独立 typed state。它们虽然都属于 active image
authoring，但 toolbar、surface、history、保存/生成边界不同。

## Source Contract

```text
standard toolbar + standard generation panel
  -> element edit toolbar 272x44
  -> edit stage covers image media
  -> full-stage initial mask + guide
  -> 400x50 empty record panel
  -> Escape/close
  -> standard toolbar + standard generation panel
```

源站 live 几何：

| Element | Rect / relation |
|---|---|
| toolbar | `272x44` |
| toolbar -> stage | `52px` vertical gap |
| stage | `250.211x141.711` on the audited source node |
| record panel | `400x50` |
| stage -> record panel | `12px` vertical gap |
| horizontal anchor | toolbar/stage/panel centers agree within DOM rounding |

## Required DOM

```text
[data-image-element-edit-toolbar]
  [data-image-element-edit-close]
  [data-image-element-edit-tool="point"]
  [data-image-element-edit-tool="box"]
  [data-image-element-edit-tool="brush"]
  [data-image-element-edit-brush-size]
  [data-image-element-edit-undo]

[data-image-element-edit-mode]
  [data-image-element-edit-stage]
    [data-image-element-edit-mask]
    [data-image-element-edit-guide]
  [data-image-element-edit-record-panel]
    [data-image-element-edit-empty]
    [data-image-element-edit-generate]
```

## Behavior

- only one selected image owns the active mode;
- opening element edit closes Preview/Annotate and other top-level overlays;
- active mode unmounts `data-image-toolbar` and `data-image-edit-panel`;
- `point` is the default active tool;
- point/box/brush and brush size are local empty-state UI only;
- empty undo and generate are disabled;
- Escape or close unmounts the mode and restores the same selected image;
- selection change/clear closes the mode;
- active mode owns Delete/Backspace/Tab/Space/undo/redo/duplicate so commands do
  not reach the graph;
- empty mode does not alter nodes, edges, selection, Prompt, viewport or history.

## Geometry

- toolbar remains `272x44` screen pixels and is centered above the node;
- toolbar uses the source-observed `52px` gap for this dedicated branch;
- stage is `absolute inset-0` over image media and follows React Flow transforms;
- record panel remains `400x50` screen pixels via inverse zoom;
- record panel center follows node center and keeps approximately `12px` screen gap
  below stage;
- toolbar and record panel may naturally clip at viewport edges;
- no viewport clamp or page-level fixed promotion is allowed.

## Visual Boundary

- stage keeps the source image visible beneath a translucent editing mask;
- guide text is exactly `标记你想要修改的对象`;
- empty record text is exactly `编辑内容待添加`;
- unknown exact source icon SVGs may use current lucide approximations;
- no selection contour, brush stroke, recognized object, record card or result image
  is shown without new source evidence.

## Verification

Primary verifier: `scripts/verify-liblib-batch54.py`.

Adjacent regressions:

- Batch 53: annotate replacement and active-image shortcut ownership;
- Batch 52: current standard toolbar and Preview;
- Batch 10/11: historical image panel and top-level overlay lifecycle.

