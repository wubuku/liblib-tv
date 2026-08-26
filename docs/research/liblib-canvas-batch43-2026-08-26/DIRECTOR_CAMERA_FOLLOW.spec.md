# Director Camera Look-At And Follow Specification

## Interaction Model

The feature is selection-driven and time-aware:

```text
camera selection
  -> Inspector relationship edit
  -> serializable camera configuration
  -> ordinary object/timeline sampling
  -> second-pass camera relation resolution
  -> R3F camera view
```

Inspector edits are click/input-driven. Camera movement is reactive to target
object state and timeline time.

## Serializable Camera Contract

```ts
type DirectorCameraLookAtMode = "coordinate" | "rotation" | "object";
type DirectorCameraFollowView = "third-person" | "first-person";

interface DirectorCameraRelation {
  lookAtMode: DirectorCameraLookAtMode;
  lookAtObjectId: string | null;
  followTargetId: string | null;
  followOffset: DirectorTuple3;
  followView: DirectorCameraFollowView;
}
```

The relation is stored beside existing `fov` and `target` camera data. No
Three.js object, vector, quaternion or matrix enters Zustand.

## Resolution Order

1. Sample every object's transform/camera/pose tracks independently.
2. Build a stable ID map from the sampled objects.
3. Resolve object look-at for cameras with `lookAtMode: "object"`.
4. Resolve camera follow from the sampled target transform.
5. Preserve camera-track FOV while relation-derived position/target override
   the sampled camera position/target.

This order ensures a camera follows the animated target state at the same
playhead instead of the target's initial scene state.

## Clone-Calibrated Math

- Character focus uses its sampled position plus a scaled upper-body height.
- Props focus around a primitive-specific center offset.
- Follow offsets rotate around the target's sampled Y rotation so the rig is
  target-relative.
- Third person places the camera at target focus plus rotated offset and looks
  at target focus.
- First person places the camera near target focus plus rotated offset and
  looks forward along target Y rotation.
- All outputs are finite rounded tuples. Invalid targets preserve the camera's
  last ordinary sampled values.

These are prototype decisions, not recovered LibTV formulas.

## Inspector Contract

### 注视目标

Chooser options:

- `手动坐标`
- `手动旋转`
- each visible character or prop, using its stable object ID

Coordinate and object modes show `注视坐标`. Object mode keeps the coordinates
read-only as derived feedback. Rotation mode relies on the existing camera
rotation fields.

### 跟随目标

Chooser options:

- `不跟随`
- each visible character or prop

When active, show:

- `跟随偏移` XYZ inputs;
- `跟随视角` segmented control;
- `第三人称`;
- `第一人称`;
- exact path conflict hint.

## Conflict Contract

While a camera has `followTargetId`:

- preset path creation is rejected;
- pencil/pen path drawing is rejected;
- the path entry is disabled with
  `请先关闭机位跟随，再绘制轨迹`;
- phone virtual-camera local connection and recording are rejected with
  `请先关闭机位跟随，再使用手机运镜`.

Existing paths and camera tracks are not deleted when follow is enabled. They
remain serialized and become available again after follow is disabled.

## Responsive Contract

- Camera controls use the existing internally scrolling Inspector.
- Segmented first/third-person controls keep stable height and two equal tracks.
- Long target names truncate inside their chooser.
- At `390x844`, the mobile Inspector drawer remains above the timeline and
  within document width.

## Verification

Focused Playwright must verify:

- exact source labels and serialized modes;
- actual WebGL pixel changes for coordinate, rotation and both follow views;
- animated-target scrub and playback;
- finite values and stable target IDs;
- camera FOV composition;
- path and phone conflict guards;
- follow disable recovery;
- desktop/mobile geometry and zero browser errors.
