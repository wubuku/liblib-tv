# Batch 43: Director Camera Look-At And Follow

> Status: planned. Current LibTV source vocabulary, the complete current chunk
> search, upstream archaeology and the bounded clone contract are recorded
> before implementation.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): current LibTV camera labels,
   conflict contracts and runtime-evidence limits.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): reusable object
   look-at behavior from the fixed existing replication.
3. [`PLAN.md`](PLAN.md): value ranking, implementation sequence and acceptance
   criteria.
4. [`DIRECTOR_CAMERA_FOLLOW.spec.md`](DIRECTOR_CAMERA_FOLLOW.spec.md):
   serializable state, Inspector, runtime sampling and conflict contract.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): live progress, commits,
   verification and interruption handoff.

## Batch Goal

```text
select a camera
  -> choose coordinate, rotation or object look-at
  -> optionally choose a scene object as the follow target
  -> tune follow offset and first/third-person view
  -> move or animate the target
  -> see the camera view follow deterministically
  -> prevent incompatible path and phone-camera authoring
```

## Evidence Discipline

- **LibTV source fact:** current locale contracts directly prove
  `注视目标`, `手动坐标`, `手动旋转`, `跟随目标`, `不跟随`,
  `跟随偏移`, `跟随视角`, `第三人称` and `第一人称`.
- **LibTV source fact:** current locale contracts explicitly block preset
  camera motion, path drawing and phone virtual-camera use while following.
- **Runtime limit:** all 108 current public canvas chunks contain these
  symbols only in the locale chunk. This batch has no authenticated follow
  state screenshot, DOM/CSS extraction or source implementation.
- **Existing replication fact:** the fixed upstream project implements manual
  or object look-at with live target refresh, but it has no camera-follow
  model.
- **Clone decision:** implement a deterministic serializable relationship
  layer over the existing object/timeline model. Keep offset coordinates,
  focus heights, first-person forward math and layout as explicit clone
  calibration.

## Scope Boundary

This batch does not claim source-exact camera math, collision avoidance,
handheld damping, path-plus-follow blending, imported skeleton head sockets or
exact source panel geometry. It does not add source `预设运镜`; it only guards
the clone's existing motion-path authoring surface where the source contract
proves an incompatibility.
