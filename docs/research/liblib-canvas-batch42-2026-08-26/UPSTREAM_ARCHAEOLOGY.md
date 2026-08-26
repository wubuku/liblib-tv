# Batch 42 Upstream Pose Archaeology

## 1. Fixed Reference

```text
path: research/upstream/storyai-3d-director-desk
commit: 8c8bd361790be4d37158a7430365e65546e358fe
```

High-value files:

- `src/editor/schema/poseSchema.ts`
- `src/editor/presets/mannequinPosePresets.ts`
- `src/editor/panels/CharacterPanel.tsx`
- `src/editor/runtime/mannequin/ProceduralMannequin.tsx`
- `src/editor/runtime/mannequin/mannequinPose.ts`
- `src/editor/runtime/mannequin/mannequinParts.tsx`
- `src/editor/schema/directorProject.ts`
- `src/editor/store/directorStore.ts`

## 2. Reusable Facts

The upstream project:

- defines the same 20 preset IDs and Chinese labels found in the current
  LibTV locale;
- stores a serializable `CharacterRigState` with a preset ID and sparse named
  numeric controls;
- replaces the control map when applying a preset and clears preset identity
  when a single control is edited;
- renders a procedural mannequin through nested R3F groups for body, torso,
  head, shoulders, elbows, wrists, hips, knees and feet;
- exposes `属性 / 姿势` tabs, a four-column preset grid and grouped continuous
  range controls;
- clamps calibrated Euler controls before converting degrees to radians.

These are facts about the upstream replication, not proof of LibTV's current
DOM, CSS, geometry or internal implementation.

## 3. Missing Upstream Capability

Repository-wide archaeology finds no animation timeline, typed pose track,
pose keyframe sampling or transform-plus-pose track composition. The upstream
project therefore cannot supply the most important Batch 42 contract:

```text
one character
  + transform track
  + independent pose track
  -> one composed sampled object
```

That integration must be designed against this repository's existing
`directorStore` and `DirectorTimeline`.

## 4. Reuse Decisions

| Upstream idea | Decision | Boundary |
|---|---|---|
| sparse named rig controls | adapt | implementation shape only |
| nested procedural mannequin | adapt to existing scene scale/materials | geometry is clone-calibrated |
| same 20 preset values | adapt as initial calibrated values | names are source facts; angles are not |
| properties/pose Inspector tabs | adapt | exact geometry is not source fact |
| four-column preset grid | adapt | upstream fact only |
| grouped sliders | adapt using LibTV SAM group/bone names | channels/ranges are calibrated |
| body-type system | defer | no source need for this bounded batch |
| crowd pose actions | defer | separate higher-level feature |

## 5. Integration Risks

1. Current `applyTimelineAtTime` uses a `Map<objectId, track>` and silently
   drops all but one track per object. It must compose track kinds.
2. Current transform recording finds the first object track; once a pose track
   exists it must explicitly find the primary transform/camera track.
3. Motion paths apply only to transform/camera tracks and must not become
   available for pose tracks.
4. Sparse pose maps need zero-default interpolation across the union of keys.
5. Three.js runtime objects must remain outside Zustand; only rig values and
   keyframes belong in the store.
