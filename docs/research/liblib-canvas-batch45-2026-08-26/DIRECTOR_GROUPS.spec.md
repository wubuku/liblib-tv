# Director Groups And Crowds Specification

## Evidence Classification

| Contract | Basis |
|---|---|
| explicit character-group entity | current LibTV business chunk |
| group/ungroup commands | current LibTV locale |
| crowd rows, columns, spacing and count | current LibTV locale |
| expandable group row | current LibTV locale |
| typed group timeline track/keyframe | current LibTV locale and business chunk |
| group member offsets | current LibTV business chunk |
| centered X/Z crowd array | fixed upstream, clone calibration |
| average-position group anchor | fixed upstream, clone calibration |
| panel CSS and limits | clone calibration |

## Domain Contract

```ts
interface DirectorCharacterGroup {
  id: string;
  label: string;
  characterIds: string[];
  crowd?: {
    rows: number;
    columns: number;
    spacing: number;
  };
}
```

Rules:

- only character IDs are accepted in Batch 45;
- groups contain at least two existing, unique characters;
- one character can belong to at most one group;
- ungroup removes the entity, not its characters;
- deleting/unbinding a group also removes its group timeline track;
- crowd metadata is descriptive and serializable, not the source of member
  identity.

## Selection Contract

- normal object selection clears group selection and selects one object;
- Shift object selection toggles membership in `selectedObjectIds`;
- selecting a group sets `selectedGroupId`, selects all members and keeps one
  member as `selectedObjectId` for compatibility;
- clicking a grouped character in the viewport selects its group;
- empty viewport clears object and group selection;
- motion-path authoring keeps its existing selection guard.

## Group Transform Contract

- group transform is represented by a derived anchor;
- member meshes remain normal scene objects;
- a separate empty R3F group owns `TransformControls`;
- commit fans anchor translation/rotation/scale out to member transforms;
- Inspector axis edits use the same store action as the viewport gizmo;
- auto-keyframe records the resulting group anchor;
- all stored values must remain finite and rounded consistently.

## Crowd Creation Contract

The panel contains:

```text
添加群众阵列
共N人
行数 × 列数
间距
取消
添加
```

Clone-calibrated limits:

- rows: `1..6`;
- columns: `1..8`;
- spacing: `0.6..3`;
- total: at most `24`.

The panel must normalize values on submit, create a centered X/Z array away
from the existing lead character, close itself and select the new group.

## Tree Contract

- ungrouped characters remain under `角色`;
- groups appear under `群众` when they have crowd metadata and under `角色组`
  otherwise;
- each group row uses a group icon, count and expand/collapse control;
- member previews are indented and select the group;
- search matches group labels and member names;
- the current group is visibly selected.

## Inspector Contract

When a group is selected:

- header reads `分组属性`;
- type label is `群众` or `角色组`;
- name is editable;
- member count and crowd shape are visible;
- position, rotation and scale axis fields edit the derived anchor;
- no individual pose panel is shown.

## Timeline Contract

```ts
{
  kind: "group";
  groupId: string;
  objectId: string; // compatibility target, equal to groupId
  keyframes: Array<{
    id: string;
    time: number;
    value: DirectorTransform;
  }>;
}
```

The track label is `${group.label} · 分组`. Selecting the track selects the
group. Adding/upserting a keyframe captures the current derived group anchor.
Sampling applies the anchor transform to stable member offsets.

Group motion paths are disabled in this batch because current source evidence
does not yet bound their semantics.

## Test Selectors

The implementation exposes:

```text
data-director-group-id
data-director-group-selected
data-director-group-expanded
data-director-group-member-id
data-director-group-action
data-director-crowd-trigger
data-director-crowd-panel
data-director-crowd-rows
data-director-crowd-columns
data-director-crowd-spacing
data-director-crowd-count
data-director-group-inspector
data-director-group-transform-field
data-director-group-rig
data-director-track-kind="group"
data-director-track-group-id
```
