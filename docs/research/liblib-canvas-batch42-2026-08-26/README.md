# Batch 42: Director Character Pose And SAM Tracks

> Status: planned. Source evidence and upstream archaeology are protected;
> implementation and focused verification are pending.

## Read Order

1. [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md): exact current LibTV pose,
   timeline and SAM vocabulary.
2. [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md): reusable ideas from
   the fixed `storyai-3d-director-desk` submodule and their evidence boundary.
3. [`PLAN.md`](PLAN.md): value ranking, implementation order and acceptance
   criteria.
4. [`DIRECTOR_CHARACTER_POSE.spec.md`](DIRECTOR_CHARACTER_POSE.spec.md):
   articulated mannequin, Inspector and independent pose-track contract.
5. [`IMPLEMENTATION.md`](IMPLEMENTATION.md): live progress, commits,
   verification and interruption handoff.

## Batch Goal

```text
select a character
  -> open source-named 姿势 tab
  -> apply one of 20 source-named presets
  -> adjust source-named SAM bone groups
  -> see the articulated R3F character change
  -> author independent pose keyframes
  -> scrub/play interpolated transform and pose tracks together
```

## Evidence Discipline

- **LibTV source fact:** current locale contracts prove a `姿势` tab, 20 named
  presets, `姿势调节`, `SAM 骨骼姿势`, six bone groups, 14 bone labels and
  distinct `姿态关键帧` / `姿态` timeline semantics.
- **Runtime limit:** this batch has no authenticated pose-panel screenshot,
  DOM/CSS extraction or source implementation. Exact panel geometry, control
  count, slider ranges, preset angles and interpolation remain unknown.
- **Existing replication fact:** the fixed upstream project implements the
  same 20 names with a procedural mannequin, grouped continuous controls and
  serializable rig state, but has no animation timeline or pose tracks.
- **Clone decision:** reuse the upstream implementation shape as calibrated
  engineering input while keeping LibTV names and evidence boundaries
  explicit. Add pose tracks to this clone's existing typed timeline rather
  than presenting upstream behavior as source fact.

## Scope Boundary

This batch does not implement imported humanoid skeleton discovery, IK,
per-bone viewport gizmos, retargeting, character crowds, model/body libraries
or authenticated source geometry.
