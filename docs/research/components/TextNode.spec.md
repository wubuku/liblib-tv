# TextNode Specification

## Overview

- **Target file:** `src/components/nodes/TextNode.tsx`
- **Type ID:** `text`
- **Interaction model:** Click to edit text inline.

## DOM Structure

```
<div className="bg-[#212121] rounded-xl border min-w-[200px] max-w-[300px] overflow-visible flex flex-col">
  <Handle type="target" position={Left} id="target" />
  <Handle type="source" position={Right} id="source" />

  <header>
    <TextIcon />
    <span>文本</span>
  </header>

  <div className="p-3">
    {isEditing ? (
      <textarea autoFocus ...>
    ) : (
      <div onClick={() => setIsEditing(true)}>
        {content || "点击编辑文本..."}
      </div>
    )}
  </div>
</div>
```

## Data Shape

```ts
interface TextNodeData {
  content: string;
}
```

## States & Behaviors

| State | Trigger | Effect |
|-------|---------|--------|
| Idle | - | Shows content text; click the body to create a local draft from `data.content`. |
| Editing | Click the body | Textarea with autofocus; keystrokes update the component-local draft only. |
| Blur commit | Focus leaves the textarea | If the draft differs, calls `canvasStore.updateNodeData(id, { content })`, then exits. |
| Escape cancel | `Escape` while editing | Attempts to discard the draft and exit without calling the explicit commit function. |

The previous statement that text never reaches `canvasStore` is obsolete. Current
runtime commits through `updateNodeData`, which records one graph snapshot whenever
the target node exists.

## Editor Session Boundary

[`../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md`](../LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md)
classifies this surface as `INLINE_MULTILINE` and is authoritative for future
baseline、dirty、cancel/blur guard、no-op and graph-history behavior.

Current known gaps:

- no captured field/node version or baseline drift policy;
- Escape-triggered unmount versus blur ordering is not protected by an explicit
  cancel reason;
- graph undo clears selection and may unmount the editor;
- native text undo and graph undo ownership relies on the page editable-target
  guard rather than a typed editor-session result.

## Files Referenced

- `src/components/nodes/TextNode.tsx`
