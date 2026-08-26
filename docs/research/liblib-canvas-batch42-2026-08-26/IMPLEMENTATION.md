# Batch 42 Implementation Log

> Status: planned. Evidence and specification are complete; implementation is
> the next action.

## Protection Points

1. Exact 50-key pose/SAM-related extraction from the current LibTV locale.
2. Exact 20 current source preset names.
3. Distinct source `姿态关键帧` / `姿态` timeline semantics.
4. Fixed upstream commit and reusable procedural-rig boundaries.
5. Explicit warning that upstream geometry, values and CSS are not LibTV
   source facts.
6. Required fix for the current one-track-per-object sampling bug.

## Progress

- [x] source vocabulary extraction
- [x] upstream pose code archaeology
- [x] implementation specification
- [ ] articulated rig and pose data
- [ ] Inspector preset/SAM controls
- [ ] pose track sampling/composition
- [ ] focused browser verification and screenshots
- [ ] screenshot interpretation ledger
- [ ] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: pending
- Main implementation: pending
- Focused verification: pending
- Stable documentation/finalization: pending

## Interruption Handoff

Continue with `PLAN.md` step 1. Do not re-open historical screenshots: this
batch has no source or clone screenshot yet. Preserve all unrelated dirty PNGs
and stage only exact Batch 42 paths. The most important implementation invariant
is that transform and pose tracks must compose for one character rather than
compete in a `Map<objectId, track>`.
