# Batch 45 Upstream Archaeology

## Fixed Checkout

```text
research/upstream/storyai-3d-director-desk
commit 8c8bd361790be4d37158a7430365e65546e358fe
```

This is an MIT-licensed LibTV-oriented replication and a design reference. It
is not evidence of current LibTV behavior.

## Borrowable Data And Store Contracts

### Crowd identity

The upstream stores `crowdId` and `crowdLabel` on every member character.
Selection is modeled separately as:

```text
selectedCrowdId
selectedObjectId
selectedObjectIds
```

Selecting a crowd resolves all member IDs and exposes the group as the active
character-inspector context.

### Array creation

`getCrowdCharacterPositions(rows, columns, spacing)`:

- clamps rows/columns to at least one;
- clamps spacing to at least `0.1`;
- creates a centered X/Z grid;
- places each character at Y `0`.

`addCrowdCharacters` assigns one stable crowd ID/label to every generated
member, selects the whole crowd and returns the created IDs.

### Group transform

`getCrowdAnchorTransform` uses the average member position and the first
member's rotation/scale.

`applyCrowdTransformPatch`:

- computes position, rotation and scale deltas from the old anchor;
- scales each member offset from the anchor;
- rotates the offset X, then Y, then Z;
- applies translation plus the rotated offset;
- adds the rotation delta to each member;
- multiplies each member scale by the anchor scale ratio.

The clone should borrow the concept and verify finite deterministic output. It
must not describe this exact math as recovered LibTV behavior.

## Borrowable UI Contracts

### Object tree

`ObjectTreePanel.tsx`:

- aggregates crowd members into one `Users` row;
- supports expand/collapse;
- previews member rows below the group;
- selects the entire crowd when its row or member preview is clicked;
- keeps Shift multi-selection distinct from crowd selection.

### Viewport

`SceneRoot.tsx` renders all members as ordinary objects and attaches a separate
empty `CrowdTransformRig` at the derived anchor. The gizmo moves the anchor;
the store fans the result out to members.

This separation is directly useful for the current R3F clone because it avoids
reparenting meshes under a transient Three.js group and keeps Zustand as the
source of truth.

### Creation panel

`ViewportToolbar.tsx` uses a compact dialog with:

```text
添加群众阵列
共N人
行数 × 列数
间距
取消
添加
```

It normalizes draft values only when applying.

## Non-Portable Or Missing Areas

- The upstream has no animation timeline and therefore no group tracks,
  keyframes or playback contract.
- It stores group identity redundantly on members rather than as the explicit
  `characterGroups` entity observed in current LibTV code.
- It allows whole-crowd pose/color editing beyond this batch's minimum source
  closure.
- It has persistence, clipboard and undo machinery that should not be pulled
  into the current clone as part of this focused batch.

## Adaptation Decision

Use an explicit `DirectorCharacterGroup[]` collection in the clone, with stable
member IDs and optional crowd metadata. Borrow the upstream's derived-anchor
and fan-out transform pattern. Add a clone-owned typed group timeline track
because current LibTV proves that entity while the upstream does not provide
one.
