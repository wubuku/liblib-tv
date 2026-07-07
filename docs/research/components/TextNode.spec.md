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
| Idle | — | Shows content text; click anywhere to start editing. |
| Editing | Click the body or already focused | Textarea with autofocus. |
| Blur save | Click outside or press `Escape` | Exits edit mode; content persisted in component state. |

**Note:** Text changes stay in local state; not propagated to `canvasStore`. To persist, wire `onChange` to `useCanvasStore().updateNodeData(id, { content })`.

## Files Referenced

- `src/components/nodes/TextNode.tsx`
