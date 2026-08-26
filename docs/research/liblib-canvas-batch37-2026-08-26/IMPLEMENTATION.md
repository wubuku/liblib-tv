# Batch 37 Implementation Log

> Status: planned.

## Protection Points

1. Fresh path/curve source extraction, plan, spec and selectors.
2. Pure Bezier/path sampling plus director store schema/actions.
3. R3F trajectory presentation and path-driven playback.
4. Path commands, functional curve editor and responsive states.
5. Playwright, screenshot ledger, regressions, stable docs and final handoff.

## Current Evidence Boundary

- Current LibTV source directly proves the path/curve command vocabulary and
  guide sequence from track creation to playback preview.
- Exact runtime geometry, path point generation and preset control values remain
  unresolved.
- The fixed upstream replication has no implementation to port for this layer.

## Commit Protection

- Plan protection: pending.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the plan commit, implement in this order:

```text
directorMotionMath
  -> directorStore path/curve schema and actions
  -> timeline sampling integration
  -> DirectorMotionPaths in R3F
  -> path menu and curve editor
  -> focused Playwright
```

Do not stage verifier-regenerated historical screenshots from Batch 9/15/21/26-36.
