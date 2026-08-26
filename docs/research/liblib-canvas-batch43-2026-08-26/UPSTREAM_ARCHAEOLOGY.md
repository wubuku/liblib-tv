# Batch 43 Upstream Archaeology

## Fixed Reference

```text
research/upstream/storyai-3d-director-desk
commit: 8c8bd361790be4d37158a7430365e65546e358fe
```

The repository is an existing LibTV-oriented replication and an implementation
reference, not official LibTV source.

## Reusable Object Look-At Shape

The upstream camera schema stores:

```text
targetMode: "manual" | "object"
targetObjectId?: string | null
target: [x, y, z]
```

`CameraPanel.tsx` presents a custom `注视目标` chooser with `手动坐标` plus
visible focusable scene objects. Selecting an object records its stable ID and
derives a focus point. Editing a coordinate switches back to manual mode.

`directorStore.ts` refreshes cameras focused on an object whenever that object
moves. Removing a target falls back to manual target state. This is a useful
state-ownership pattern because the relationship remains serializable and
Three.js refs do not enter the store.

## What The Upstream Does Not Supply

Repository-wide source search at the fixed commit found no:

- `跟随目标` relationship;
- follow offset;
- first-person/third-person follow mode;
- follow-versus-path guard;
- follow-versus-phone-camera guard.

The camera renderer calls `lookAt(target)` and the store keeps object targets
fresh, but it does not move the camera with a target. Camera follow must
therefore be designed for this clone rather than copied from upstream.

## Portability Decisions

| Upstream idea | Decision | Reason |
|---|---|---|
| stable object target ID | reuse | deterministic and serializable |
| derived focus point | reuse shape, recalibrate values | current clone has known primitive kinds |
| automatic refresh after object movement | extend through timeline sampling | followed targets can be animated |
| target removal fallback | defer until Director object deletion exists | current clone has no delete workflow |
| custom dropdown CSS | do not copy | no source geometry and different local design system |
| Three.js camera refs in store | reject | current architecture keeps runtime refs in R3F |

## License Boundary

The upstream code is MIT at the fixed commit. This batch borrows architecture
ideas and names exact reused concepts in documentation; it does not copy model
assets or external catalog content.
