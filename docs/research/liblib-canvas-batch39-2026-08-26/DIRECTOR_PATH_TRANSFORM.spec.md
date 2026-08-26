# Director Path Transform Specification

## 1. Serializable Contract

Each path adds:

```ts
interface DirectorMotionPath {
  pivot: DirectorTuple3;
  transform: DirectorTransform;
  initialAnchors: DirectorMotionPathAnchor[];
  anchors: DirectorMotionPathAnchor[];
  points: DirectorTuple3[];
}
```

`transform.position` is an additive offset, `transform.rotation` stores degrees
and `transform.scale` defaults to `[1, 1, 1]`. `pivot` and
`initialAnchors` are creation snapshots and remain serializable.

## 2. Forward Transform

For a local point `P`:

```text
offset = (P - pivot) * scale
rotated = rotateZ(rotateY(rotateX(offset)))
world = pivot + transform.position + rotated
```

For a relative handle vector, omit pivot and translation:

```text
worldHandle = rotateZ(rotateY(rotateX(handle * scale)))
```

The transformed anchors feed the existing cubic path builder. `path.points`
remains the final world-space polyline consumed by playback.

## 3. Inverse Transform

R3F controls emit world positions. Before updating local geometry:

1. subtract `pivot + transform.position`;
2. apply inverse Z, inverse Y and inverse X rotations;
3. divide by positive scale;
4. add `pivot` for anchor positions;
5. omit pivot addition for relative handles.

Forward/inverse round trips must remain finite within `0.001`.

## 4. Scale And Numeric Safety

- Non-finite input falls back to the current value.
- Position and rotation remain finite without arbitrary visual clamping.
- Scale is positive and clamped per axis to `0.05..20`.
- All transform updates rebuild world anchors and sampled points immediately.
- The current playhead is resampled after every update.

## 5. Reset Semantics

### 重置偏移

- preserves `anchors`, anchor types and handles;
- restores position `[0,0,0]`, rotation `[0,0,0]`, scale `[1,1,1]`;
- rebuilds points from the edited local geometry.

### 重置

- restores a deep copy of `initialAnchors`;
- restores the identity transform;
- restores the creation-time pivot;
- selects the first restored anchor;
- rebuilds points and live playback.

These two behaviors are clone calibration because runtime source behavior was
not recovered.

## 6. Inspector

- Path-level `位置`, `旋转` and `缩放` appear before the anchor list.
- Every row uses XYZ numeric fields with semantic path-transform selectors.
- `重置偏移` is the primary compact reset command.
- `重置` is visually secondary and explicitly restores the creation snapshot.
- Anchor fields remain path-local; path transform fields own whole-geometry
  placement.

## 7. R3F And Capture

- Lines, anchors, handles and handle guides use transformed world coordinates.
- Anchor/handle TransformControls commit through the inverse transform.
- Object TransformControls remain suppressed while a path control is selected.
- Authoring helpers remain absent from camera view and exported PNG captures.

## 8. Responsive Contract

- Transform rows use the existing three-column numeric field pattern.
- Both reset commands remain reachable through Inspector internal scrolling.
- `390x844` keeps the 288px right drawer and zero document overflow.
