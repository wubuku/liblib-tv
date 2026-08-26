# Director Character Pose And SAM Track Specification

## 1. Purpose

Add a real character-pose authoring loop to the existing director workspace:

```text
character rig state
  -> articulated R3F rendering
  -> source-named preset and SAM controls
  -> typed pose keyframes
  -> deterministic pose interpolation
  -> composition with the same object's transform track
```

## 2. Serializable Rig

```ts
interface DirectorCharacterRig {
  posePresetId: DirectorPosePresetId | null;
  controls: Record<string, number>;
}

interface DirectorPoseKeyframeValue {
  posePresetId: DirectorPosePresetId | null;
  controls: Record<string, number>;
}
```

Controls are sparse and finite. Missing channels sample as zero. Browser,
Three.js `Object3D`, Euler and mesh references never enter Zustand.

## 3. Articulated Mannequin

The selected character keeps its existing object transform and color. Its
primitive becomes a nested procedural rig with:

- root/body offset and rotation;
- torso rotation;
- head/neck rotation;
- left/right shoulder, elbow and wrist groups;
- left/right hip, knee and foot groups.

Each child segment is attached to its parent group so proximal rotation moves
the complete distal chain. The exact capsule/sphere dimensions, face details
and Euler mapping are calibrated from the upstream implementation to fit the
existing scene, not claimed as LibTV geometry.

## 4. Inspector Contract

Only a selected character shows `属性 / 姿势` tabs.

`属性` preserves the existing name, visibility, color and transform controls.

`姿势` contains:

1. `姿势预设`: 20 source-named compact buttons;
2. active state metadata;
3. `姿势调节`;
4. `SAM 骨骼姿势`;
5. six collapsible source-named groups;
6. calibrated range inputs labeled with source bone names and motion channels.

Preset application replaces the sparse control map. Manual control edits
preserve other channels and set `posePresetId` to `null`.

## 5. Pose Track Contract

```ts
type DirectorTimelineTrack =
  | TransformTrack
  | CameraTrack
  | PoseTrack;
```

A pose track:

- uses `kind: "pose"`;
- targets one character object;
- is labeled `<character name> · 姿态`;
- stores pose values at timeline times;
- supports selection, deletion, add/delete keyframe, previous/next seek and
  the existing speed curve;
- never owns a motion path.

The first pose edit creates the track. Later edits at the same playhead replace
that keyframe; edits at a new playhead insert another.

## 6. Sampling And Composition

Pose interpolation:

1. remap timeline time through the track speed curve;
2. find adjacent keyframes;
3. build the union of both sparse control maps;
4. linearly interpolate every channel, using zero for a missing value;
5. keep preset identity only at an exact endpoint and use `null` between
   different presets.

Timeline application groups all tracks by object and composes by kind:

```text
base object
  -> transform/camera sample and optional motion path
  -> pose sample into characterRig
  -> one final object
```

Track array order must not cause one kind to erase another.

## 7. Evidence Labels

- **Source-backed:** visible Chinese vocabulary, 20 names, six groups,
  14 bone labels, distinct pose keyframe/track semantics.
- **Upstream-backed:** sparse controls, nested R3F rig, four-column preset
  grid and grouped sliders.
- **Clone-calibrated:** mesh dimensions/materials, channel mapping, ranges,
  steps, default expanded groups, linear interpolation and responsive CSS.
