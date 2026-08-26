# Batch 39 Source Evidence

## 1. Current LibTV Vocabulary

Observation date: August 26, 2026.

The current locale chunk remains:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
```

Its direct key/value sequence is:

```text
directorMotionPathPosition: 位置
directorMotionPathRotation: 旋转
directorMotionPathScale: 缩放
directorMotionPathOrientToPath: 绑定对象沿路径朝向
directorMotionPathReset: 重置
directorMotionPathResetOffset: 重置偏移
```

The keys are specifically motion-path properties, not generic object-transform
translations. This directly supports adding a path-level transform surface and
two distinct reset commands.

## 2. Runtime Search Limit

The target canvas HTML referenced 108 script sources. A current cross-chunk
search for:

```text
directorMotionPathPosition
directorMotionPathReset
directorMotionPathResetOffset
```

found all three only in the locale chunk. No business chunk exposed the literal
keys or readable implementation around them.

Therefore current evidence does **not** establish:

- whether path position is absolute, pivot-based or an additive offset;
- which pivot the source uses;
- Euler order or degree/radian storage;
- uniform versus per-axis scale;
- negative/zero scale handling;
- whether `重置` restores geometry, transform, both or only one field;
- whether `重置偏移` is global or per-axis;
- exact panel geometry, numeric range, step or transform gizmo behavior.

## 3. Existing Replication Reference

The fixed upstream submodule remains at:

```text
8c8bd361790be4d37158a7430365e65546e358fe
```

`applyCrowdTransformPatch` in
`research/upstream/storyai-3d-director-desk/src/editor/store/directorStore.ts`
is a useful implementation reference:

- it obtains a stable group anchor;
- derives translation, rotation delta and scale ratio;
- scales offsets around the anchor;
- applies X, then Y, then Z rotation;
- writes rounded serializable object transforms back to Zustand.

This proves the upstream replication already uses a pure-state group-transform
pattern compatible with the current clone's store boundary. It does not prove
LibTV motion-path semantics.

## 4. Existing Clone Foundation

Batch 38 supplies:

- local serializable anchors with relative handles;
- deterministic anchor-to-polyline rebuilding;
- R3F anchor/handle controls;
- existing arc-length playback and orient-to-path;
- helper-free capture;
- store-level input ownership during path editing.

Batch 39 can add a path transform without changing the timeline sampler if
`path.points` continues to be the final world-space derived polyline.

## 5. Clone Calibration Required

The implementation must label these as clone decisions:

- one fixed pivot captured as the creation-time anchor centroid;
- `transform.position` as an additive world-space offset;
- positive per-axis scale clamped to `0.05..20`;
- degree values with X→Y→Z rotation;
- `重置偏移` restoring identity transform while preserving edited anchors;
- `重置` restoring the creation-time anchor snapshot plus identity transform;
- path-local anchor fields while R3F displays and drags world-space controls;
- no path-level TransformControls in this batch.
