# ImageAnnotateMode

## Purpose

复刻 LibTV selected image 的空标注 active-tool 状态。该组件不是 page
modal，也不是 graph node result；它替换普通图片的标准上下双浮层。

## State Ownership

- `uiStore.imageAnnotate`：当前 active image canvas/node identity 和媒体描述；
- `canvasStore`：不写入 active state，不产生 graph history；
- `ImageNode`：决定 standard/annotate render branch；
- `ImageAnnotateToolbar`：节点上方专用 toolbar；
- `ImageAnnotateSurface`：节点本体上的 canvas overlay。

## Source Contract

```text
standard toolbar + standard bottom panel
  -> annotate toolbar 536x49
  -> bottom panel absent
  -> canvas overlay with DPR2 backing
  -> Escape/close
  -> standard toolbar + standard bottom panel
```

The source empty state was observed at `929x874` with a `536x49` toolbar and a
canvas CSS rect of approximately `194.117x97`, backed by `388x194` pixels.

## Required DOM

```text
[data-image-annotate-toolbar]
[data-image-annotate-surface]
  [data-image-annotate-canvas]
[data-image-annotate-close]
[data-image-annotate-save]
[data-image-annotate-undo]
[data-image-annotate-redo]
```

The current production bundle confirms the empty-state control set: pencil, rect,
text, color, line width, undo, redo and save. The clone only implements the local
tool/color/width state in this batch; non-empty stroke and save semantics remain
separate contracts.

## Behavior

- only one selected image may own the active state;
- opening annotate hides standard toolbar and `data-image-edit-panel`;
- Preview and top-level panels are mutually exclusive with annotate;
- Escape and close restore the standard selected-image state;
- empty annotate does not alter nodes, edges, selection, Prompt, viewport or
  history;
- undo/redo are disabled in the empty state; save remains enabled as a
  source-shaped control but has no clone-side effect in this batch;
- the surface does not create a result node or call a provider.
- Batch 58 also closes the surface when its owner node disappears or the active
  canvas changes; the cleanup is UI-only and does not enter graph history.

The enabled-looking inert Save command is retained here as a historical/current
clone fact, not an accepted final interaction. It violates future correctness
invariant `LIBTV-EDS-I-031` in
[`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md).
Future work must either implement a source-evidenced `BITMAP_EDITOR` handoff or
make Save unavailable; this specification does not authorize either code change.

## Responsive

- toolbar remains node-centered and may naturally clip at viewport edges;
- surface follows the transformed node;
- document must not gain horizontal overflow;
- mobile does not promote the surface to a page-level fixed overlay.

## Verification

The primary verifier is `scripts/verify-liblib-batch53.py`. Batch 10/11 preserve
adjacent historical image-panel and top-level overlay lifecycle contracts;
Batch 52 preserves the current standard action shell and Preview.
