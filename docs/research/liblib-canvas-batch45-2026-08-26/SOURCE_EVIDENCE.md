# Batch 45 Source Evidence

## 1. Current Artifacts

Observation date: 2026-08-26.

Target:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

| Artifact | Size | SHA-256 |
|---|---:|---|
| decoded current locale | `343745` bytes | `58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277` |
| current Director domain chunk `1pw97ep85si5l.js` | `117106` bytes | `b48eae8be87a79ae1625c0a85f9e8ecee9257b74e27a074c35028eb3a510d170` |

The business chunk was downloaded with the same current canvas shell/chunk set
used by Batch 43 and Batch 44.

## 2. Exact Current Vocabulary

```text
directorTimelineGroupKeyframe: 分组关键帧
directorTimelineGroupFallback: 分组
directorTimelineSelectTargetToAddTrack: 选中角色、道具或分组后建立轨道
directorCharacterGroupAutoLabel: 角色组{index}
directorShortcutGroup: 打组
directorShortcutUngroup: 解组
directorContextMenuGroup: 打组
directorContextMenuUngroup: 解组
directorCollapseGroup: 收起分组
directorExpandGroup: 展开分组
directorCrowdNxM: 群众 ({rows}x{cols})
directorCrowdN: 群众 ({n}人)
directorCrowd3x3: 群众 (3x3)
directorAddCrowdArray: 添加群众阵列
directorCrowdTotalN: 共{n}人
directorRows: 行数
directorCols: 列数
directorSpacing: 间距
directorCrowd3Label: 群众（3人）
directorCrowd3Desc: 一排3个素体人偶
directorCrowd5Label: 群众（5人）
directorCrowd5Desc: 一排5个素体人偶
directorMultiSelectCharacterHint: 已选中 {count} 个角色，修改将同步应用到全部选中对象
```

This directly proves:

- selected scene elements can be grouped and ungrouped;
- groups are expandable tree entities rather than only selection decoration;
- a crowd array has rows, columns, spacing and a computed person count;
- groups are valid timeline targets with a distinct group-keyframe kind;
- the source also supports multi-character selection.

## 3. Current Domain-Model Evidence

The current Director business chunk contains these serializable structures:

```text
scene.characterGroups
scene.animation.groupTracks
groupTrack.targetId
groupTrack.memberOffsets
```

The source scene serializer explicitly normalizes absent groups to:

```text
characterGroups: scene.characterGroups ?? []
```

The timeline empty-state check counts:

```text
animation.groupTracks.length
```

Timeline parsing accepts a group track only when its `targetId` exists in the
provided group ID set. It preserves:

```text
id
targetId
keyframes
interpolation
speedCurve
speedCurveSegments
motionPathId
motionPath
memberOffsets
```

`memberOffsets` is parsed as a map from member ID to a 3D vector. This is strong
evidence that LibTV treats group animation as a typed target with stable
member-relative placement.

## 4. Current Group Import Contract

The current scene-analysis/import code generates:

```text
characterGroups: [
  {
    id,
    label,
    characterIds
  }
]
```

The accepted model input uses character indexes in `members`, resolves them to
stable character IDs, de-duplicates them and drops groups with fewer than two
valid members. Its prompt contract also states:

- one group must contain at least two characters;
- one character should not be repeated across groups;
- principal characters needing individual operation should stay outside a
  crowd group;
- groups enable whole-group selection and movement.

The current scene summary exports each group as:

```text
{
  id,
  label,
  members: [...]
}
```

Newer scene records may expose typed `members`; older records fall back to
`characterIds`.

## 5. What Current Evidence Does Not Prove

The downloaded source does not yet establish:

- exact crowd-panel geometry, breakpoint behavior or trigger placement;
- numeric min/max limits for rows, columns and spacing;
- exact array offset relative to existing scene objects;
- exact group anchor formula;
- exact transform composition order;
- whether ordinary manual grouping accepts props or only characters in every
  source path;
- exact group-row visibility/lock aggregation behavior;
- exact keyframe interpolation UI and group motion-path behavior.

These areas must remain clone calibration or explicitly attributed upstream
borrowing.

## 6. Implementation Boundary

Batch 45 will implement the source-proven core:

- serializable character-group entities;
- multi-character selection and group/ungroup;
- crowd array creation;
- expandable group rows;
- whole-group transform;
- typed group timeline tracks and keyframes.

It will not claim source parity for crowd limits, geometry, persistence,
clipboard, undo or group motion paths.
