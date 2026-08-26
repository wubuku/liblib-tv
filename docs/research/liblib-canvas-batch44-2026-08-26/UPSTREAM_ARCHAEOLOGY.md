# Batch 44 Upstream Archaeology

## Fixed Reference

```text
research/upstream/storyai-3d-director-desk
commit 8c8bd361790be4d37158a7430365e65546e358fe
```

## Search Result

The fixed replication was searched across schema, store, camera panel, canvas
and tests for:

```text
预设运镜
替换运镜
追加运镜
camera motion preset
orbit / half arc / push in / pull out
pedestal / truck / spiral
timeline / keyframe
```

It contains no animation timeline, camera keyframes, replace/append camera
motion or matching preset vocabulary.

## Adjacent Reusable Facts

- `DirectorCameraShot` keeps serializable transform, target and FOV.
- `CameraPanel` edits position and look-at target but has no motion authoring.
- `DirectorCanvas` performs temporary spherical camera placement only for
  four/twelve-view screenshot capture. That is capture sampling, not a
  persistent motion preset and must not be ported as source behavior.

## Reuse Decision

No upstream preset algorithm or UI is reusable. Batch 44 should use the
clone's stronger existing foundation:

- typed `DirectorCameraKeyframeValue`;
- deterministic camera-track interpolation;
- current camera relationship resolver;
- timeline selection, playback and stable test selectors.

The upstream absence is important evidence: all preset geometry and
replace/append mechanics in this batch are local prototype decisions.
