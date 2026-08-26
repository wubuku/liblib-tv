# Batch 39 计划：导演台路径整体变换与重置

## 1. 缺口与价值排序

| Candidate | Current clone | Source evidence | Value | Decision |
|---|---|---|---:|---|
| path position | absent | exact path key/label | 5 | implement |
| path rotation | absent | exact path key/label | 5 | implement |
| path scale | absent | exact path key/label | 5 | implement |
| reset offset | absent | exact path key/label | 5 | implement |
| full reset | absent | exact path key/label | 4 | implement with calibrated snapshot semantics |
| world/local anchor inversion | absent | required by existing R3F controls | 5 | implement |
| path-level TransformControls | absent | no runtime evidence | 3 | defer |
| animation video export | absent | direct guide | 5 | next batch after path maturity |

## 2. Source / Replication / Clone Boundary

### LibTV source fact

- Motion paths have direct `位置`, `旋转`, `缩放`, `重置` and `重置偏移`
  localization keys.
- The properties belong to the path namespace and coexist with path name,
  enabled state, anchor types and orient-to-path.

### Existing replication fact

- The fixed upstream has no motion-path domain.
- It does contain a pure serializable group-transform algorithm around a stable
  anchor, applying scale and X→Y→Z rotations before translation.

### Clone decision

- Use a creation-time centroid pivot.
- Keep editable anchors local and derive transformed world anchors/points.
- Store degree rotations and positive per-axis scale.
- Define `重置偏移` as identity transform only.
- Define `重置` as creation-snapshot geometry plus identity transform.
- Keep path-level editing numeric in this batch; no guessed whole-path gizmo.

## 3. State Boundary

```text
DirectorMotionPath
  pivot
  initialAnchors[]
  anchors[]
  transform
    position offset
    rotation degrees
    positive scale
  points[] <- transformed world polyline

R3F
  transformed world anchors/handles
  inverse transform on control commit
```

No Matrix4, Euler, Quaternion or Vector3 enters Zustand.

## 4. Implementation Steps

1. Add pure pivot, deep-clone, forward/inverse tuple transform helpers.
2. Extend path fixtures and free-draw commits with pivot/transform/snapshot.
3. Rebuild `path.points` from transformed world anchors.
4. Convert R3F anchor/handle rendering to world anchors and inverse commits.
5. Add store actions for path transform field updates and two reset commands.
6. Add exact source-labeled Inspector controls with stable selectors.
7. Add Batch 39 Playwright for math, live sampling, reset distinctions,
   transformed R3F controls, capture and mobile layout.
8. Inspect screenshots once, update stable docs and run Batch 35-39 regression.

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-path-transform-field]` | path position/rotation/scale row |
| `[data-director-path-transform-axis]` | XYZ path transform input |
| `[data-director-path-reset-offset]` | identity transform command |
| `[data-director-path-reset]` | creation snapshot restore |
| `[data-director-motion-path-pivot]` | semantic serialized pivot |
| `[data-director-motion-path-world-anchor]` | transformed anchor evidence |

Batch 38 anchor/handle selectors remain stable.

## 6. Acceptance Criteria

- Every created preset/pencil/pen path has a finite pivot, identity transform and
  deep-cloned initial anchor snapshot.
- Position offset translates every world anchor, point and sampled object by the
  same delta.
- Rotation and scale preserve the fixed pivot and deterministically rebuild
  path points.
- Scale cannot become zero, negative or non-finite.
- R3F anchor/handle controls render at transformed world positions and commit
  back to local anchors through the inverse transform.
- Path-local anchor numeric editing remains coherent under a non-identity path
  transform.
- `重置偏移` preserves edited anchors while restoring identity transform.
- `重置` restores initial anchors, pivot and identity transform.
- Playback and orient-to-path consume transformed points.
- Capture contains no path/anchor/handle helpers.
- Desktop and `390x844` preserve internal scrolling and zero document overflow.
- Batch 35-38 remains green with no new console, page, request or WebGL errors.

## 7. Out Of Scope

- claiming source pivot, transform order, numeric ranges or reset semantics;
- path-level TransformControls or draggable pivot;
- negative scale and path mirroring;
- path transform keyframes/history/persistence;
- animation video export and virtual camera;
- exact source panel geometry.

## 8. Status

- [x] Current source vocabulary and cross-chunk limit recorded
- [x] Upstream group-transform reference recorded
- [x] Transform/reset contract and selectors documented
- [x] Pure transform math and path schema
- [x] R3F world/local control conversion
- [x] Inspector controls and store actions
- [x] Focused Playwright and screenshot ledger
- [x] Cross-batch regression, stable docs and final quality gate
