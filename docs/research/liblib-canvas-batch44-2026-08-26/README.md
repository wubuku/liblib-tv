# Batch 44: Director Preset Camera Motion

> Status: complete. Source vocabulary, bounded clone contract, implementation,
> focused browser verification and screenshot interpretation were completed on
> 2026-08-26.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): exact current source labels,
   conflict copy and extraction limits.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): fixed replication
   search and explicit absence of camera-motion presets/timeline.
3. [`PLAN.md`](PLAN.md): value choice, implementation order and acceptance.
4. [`DIRECTOR_CAMERA_PRESETS.spec.md`](DIRECTOR_CAMERA_PRESETS.spec.md):
   serializable application state, generated keyframes and UI contract.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): progress, commits and handoff.
6. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md): one-time interpretation
   of the focused clone screenshots.
7. [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md): post-batch Director
   maturity and next-candidate ranking.

## Batch Goal

```text
select a camera track
  -> open 预设运镜
  -> choose 替换运镜 or 追加运镜
  -> apply one of seven source-named presets
  -> generate deterministic finite camera keyframes
  -> scrub/play the real R3F result
  -> expose exact no-room and follow-conflict states
```

## Evidence Discipline

- **LibTV source fact:** the current locale proves the trigger, two modes,
  seven presets, no-room error and follow conflict.
- **Source runtime limit:** the public chunk corpus exposes labels but not
  authenticated panel DOM/CSS, preset geometry, timing, easing or mutations.
- **Existing replication fact:** fixed upstream commit
  `8c8bd361790be4d37158a7430365e65546e358fe` has no animation timeline or
  preset camera-motion workflow.
- **Clone decision:** generate ordinary typed camera keyframes and preserve
  existing camera relation/FOV contracts. All geometry and timeline
  allocation rules remain explicit clone calibration.

## Scope Boundary

This batch does not claim source-exact curves, durations, path overlays,
replace/append internals, easing, collision handling or Inspector geometry. It
does not add a new backend/rendering engine or a second timeline model.
