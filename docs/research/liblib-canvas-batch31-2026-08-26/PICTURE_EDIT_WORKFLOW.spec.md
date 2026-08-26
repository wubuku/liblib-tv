# Picture Edit Workflow Specification

## Goal

把 ready-video 的三项主体编辑做成一个共享、可验证的标注编辑器：

```text
source video
  -> picture edit mode
  -> normalized marks
  -> mode-specific validation
  -> local analysis state
  -> pending edited video
```

## Component Contract

Target: `src/components/PictureEditPanel.tsx`

Props:

```typescript
interface PictureEditPanelProps {
  zoom: number;
  mode: PictureEditAction;
  currentTime: number;
  onCancel: () => void;
  onConfirm: (marks: PictureEditMark[]) => void;
}
```

The component owns editor-local history. It must not write graph history for each
pointer move. Graph history is written only by `createPictureEdit` after submit.

## Mark Contract

All geometry is normalized to the source video body:

```typescript
interface PictureEditMark {
  id: string;
  tool: PictureEditTool;
  frameSeconds: number;
  relX: number;
  relY: number;
  width: number;
  height: number;
  points?: Array<{ x: number; y: number }>;
  candidate: string;
  description?: string;
  replacement?: {
    source: "upload" | "history";
    label: string;
  };
}
```

Geometry rules:

- point creates a centered `0.08 x 0.08` marker;
- box creates a normalized rectangle with a minimum `0.02` side;
- brush creates a normalized polyline and a bounding box;
- eraser removes the selected mark, then selects the nearest remaining mark;
- all coordinates clamp to `[0,1]`;
- every mark captures `currentTime` at creation.

The geometry values and candidate labels are clone calibration, not extracted
segmentation output.

## Mode Contract

| Mode | Label | Limit | Submit requirements |
|---|---|---:|---|
| `subjectRemove` | 主体消除 | 4 | at least one mark |
| `subjectModify` | 主体修改 | 4 | every mark has non-empty description |
| `subjectReplace` | 主体替换 | 2 | every mark has replacement |

When no marks exist, submit is disabled with `请先标记主体`.
When modify has an empty description, submit is disabled with `请补充每个主体的修改描述`.
When replace has no replacement source, submit is disabled with `请为每个主体选择替换图`.

## UI Contract

The panel is a node-anchored lower editor using the existing `660px` lower editor
width and `1 / zoom` counter-scale. This width is a clone calibration selected to
reuse the verified LibTV lower-editor anchor; it is not claimed as source geometry.

Visible groups:

```text
header: close / mode label / mark count / help
tools: point / box / brush / eraser
history: undo / redo / reset
marks: selected mark candidate + mode-specific fields
footer: cost placeholder / cancel / submit
```

The video body has a normalized mark overlay while the editor is open. Mark overlays
must sit above the poster but below controls, block React Flow drag, and preserve
natural viewport clipping.

## Interaction Contract

- Click a tool to make it active.
- Point click creates one mark.
- Box drag creates one mark.
- Brush drag creates one polyline mark.
- Click a mark selects it.
- Drag a selected mark moves its geometry.
- Eraser click removes the selected mark or the mark under the pointer.
- `撤销` / `重做` operate on editor-local mark snapshots.
- `重置` removes all marks and clears fields.
- Modify description is per selected mark.
- Replace `本地上传` and `历史图库` set local replacement metadata.
- `Escape` cancels the editor without graph mutation.

## Graph Handoff

`onConfirm` calls:

```text
canvasStore.createPictureEdit(sourceId, mode, marks)
```

The store:

1. clones the current graph as one history snapshot;
2. resolves source absolute position;
3. places a `512x288` pending video at source right `+100` world units;
4. creates one direct source edge;
5. stores mode, marks, source label, frame times, descriptions/replacements and
   edge ID in request-shaped metadata;
6. keeps source selected for repeated editing;
7. clears redo history through the normal graph transaction.

Repeated outputs use the existing deterministic vertical slot search.

## Pending Result

The result renderer shows:

```text
主体消除结果 / 主体修改结果 / 主体替换结果
主体编辑 · 等待媒体资源
```

It must not reuse the source poster or imply segmentation, replacement or video
rendering has completed.

## Stable Selectors

- `[data-picture-edit-panel]`
- `[data-picture-edit-mode]`
- `[data-picture-edit-count]`
- `[data-picture-edit-tool]`
- `[data-picture-edit-mark-overlay]`
- `[data-picture-edit-mark]`
- `[data-picture-edit-description]`
- `[data-picture-edit-replacement]`
- `[data-picture-edit-upload]`
- `[data-picture-edit-history="undo"]`
- `[data-picture-edit-history="redo"]`
- `[data-picture-edit-reset]`
- `[data-picture-edit-submit]`
- `[data-picture-edit-submit-status]`
- `[data-picture-edit-submit-reason]`
- `[data-picture-edit-output]`
- `[data-picture-edit-source-id]`
- `[data-picture-edit-edge-id]`
