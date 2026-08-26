# Batch 44 Implementation Log

> Status: complete. Source evidence, bounded implementation, focused
> verification, screenshot analysis, cross-batch regression and stable docs
> passed on 2026-08-26.

## Protection Points

1. Fresh current HTML and decoded locale hashes.
2. Exact seven preset labels and two modes.
3. Exact no-room and follow-conflict copy.
4. Explicit absence of an upstream preset/timeline implementation.
5. Clone-calibrated geometry, timing and panel boundary.

## Progress

- [x] source extraction and vocabulary
- [x] upstream archaeology
- [x] implementation plan/specification
- [x] pure preset generator and store action
- [x] timeline panel and guards
- [x] focused browser verification
- [x] screenshot interpretation ledger
- [x] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: `35c23b3`
- Preset implementation: `8125872`
- Focused verification: closeout commit
- Stable documentation/finalization: closeout commit

## Implementation Notes

- The pure generator lives in
  [`src/components/director/directorCameraPresets.ts`](../../../src/components/director/directorCameraPresets.ts)
  and emits finite serializable camera values for seven source-named
  presets.
- `directorStore.applyCameraMotionPreset` owns replace/append allocation,
  atomic no-room/follow guards, status metadata and non-destructive disabling
  of an existing generic path.
- `DirectorTimeline` owns the selected-camera entry, source-named modes and
  options. The panel expands upward from the timeline and has an internally
  scrollable content region on compact viewports.
- `scripts/verify-liblib-batch44.py` uses fresh page state for operations that
  mutate timeline data. This avoids making append assertions depend on a
  previous replacement attempt.

## Verification

Passed:

```text
python3 scripts/verify-liblib-batch44.py
```

The focused check covers all seven preset IDs, real R3F pixel changes,
replace/append/no-room/follow contracts, generic-path preservation and
disablement, desktop/mobile bounds and zero browser errors. The one-time
visual reading is recorded in [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md).

## Closeout

The panel placement was adjusted after visual inspection: it now sits fully
above the timeline so it does not cover the compact timeline controls. This is
a clone UX decision, not a recovered LibTV layout fact.

## Interruption Handoff

Batch 44 is closed. Continue from
[`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md). The next evidence-first
Director candidates are source-backed group/crowd authoring, model/environment
library entry points and Director capture management. Preserve the dirty
historical PNGs by staging exact paths only.
