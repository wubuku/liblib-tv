# StoryboardGroupNode Specification

## Overview

- **Target file:** `src/components/nodes/StoryboardGroupNode.tsx`
- **Type ID:** `storyboard-group`
- **Interaction model:** React Flow parent/background container; selectable, draggable and connectable.
- **Current source project:** one empty image group and one video group containing the failed video node.

## Variants

### Image group

- `430x452`;
- translucent `rgba(255,255,255,0.1)` surface;
- `20px` radius;
- source node `g-245IDFh8sB` has no child and therefore no React Flow `.parent` class.

### Video group

- `722x460`;
- `#212121` surface;
- `4px` radius;
- source node `g-EFbbHpwq5w` has React Flow `.parent`;
- failed video `v-UGQZzZOpbv` is its child at relative `(62,62)`;
- child world size is `622x350`.

Both variants:

- use `border-white/10`;
- place the title `32px` above the shell;
- expose left target and right source handles;
- use source `z-index: -1001`;
- show cyan border/ring when selected.

## Data Shape

```ts
interface StoryboardGroupData {
  title?: string;
  variant?: "image" | "video";
  groupKind?: "selection";
}
```

The group component does not render thumbnails itself. Children are independent React Flow nodes linked by `parentId`.

## Hierarchy Evidence

Original live DOM:

```text
video group class: ... parent draggable
image group class: ... draggable
```

xyflow v12 adds `.parent` only when `parentLookup.has(groupId)`, and `parentLookup` is populated by child nodes with `parentId`.

See:

- `docs/research/liblib-canvas-batch8-2026-08-25/VIDEO_GROUP_PARENTING.spec.md`
- `docs/research/liblib-live-2026-08-25/full-canvas-audit.json`

## Clone Transactions

- dragging a group moves its children in screen/world absolute space;
- child positions remain relative to the group;
- copying a group copies/remaps its descendants;
- copying only a child detaches the copy to a top-level absolute position;
- deleting a group cascades to descendants and related edges;
- `Shift+G` removes a selected group and restores child absolute positions.

The cascade/re-group rules are clone graph invariants; they are not claimed as direct original-site command observations.
