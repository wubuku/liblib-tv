# Batch 36 Implementation Log

> Status: planned.

## Protection Points

1. Fresh source evidence, plan, timeline spec and selectors.
2. Timeline schema/store/sampling and workspace UI.
3. Track/keyframe lifecycle, auto-keyframe and scene/camera integration.
4. Playwright, screenshot ledger, regression and quality gates.
5. Final handoff and next-batch decision.

## Current Evidence Boundary

- Current LibTV source directly proves the timeline capability and interaction
  vocabulary.
- Exact runtime geometry remains unresolved.
- The fixed upstream replication has no timeline implementation to port.
- Batch 36 must therefore implement new source-backed behavior while clearly
  labeling its geometry and default fixture motion as clone calibration.

## Commit Protection

- Plan protection: pending.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the plan commit, implement in this order:

```text
directorTimelineMath
  -> directorStore discriminated tracks/actions
  -> DirectorTimeline
  -> DirectorDesk layout
  -> Inspector/gizmo auto-keyframe
  -> focused Playwright
```

Do not include the 37 historical Batch 9/15/21/26-33 screenshot modifications in
any Batch 36 commit.
