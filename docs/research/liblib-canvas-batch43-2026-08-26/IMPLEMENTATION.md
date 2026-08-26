# Batch 43 Implementation Log

> Status: planned. Evidence, upstream archaeology and the bounded camera
> relation specification are complete. Implementation is next.

## Protection Points

1. Fresh 2026-08-26 target HTML hash and 108-chunk count.
2. Exact current source look-at/follow labels.
3. Exact source conflicts with preset motion, path drawing and phone camera.
4. Proof that current component/runtime code is not present in the public
   chunk corpus.
5. Fixed upstream object-look-at behavior and explicit absence of follow.
6. Clone-calibrated math and Inspector geometry boundary.

## Progress

- [x] fresh source extraction
- [x] full current chunk search
- [x] upstream object-target archaeology
- [x] implementation specification
- [ ] serializable camera relation and pure math
- [ ] Inspector and R3F camera behavior
- [ ] conflict guards
- [ ] focused browser verification and screenshots
- [ ] screenshot interpretation ledger
- [ ] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: pending
- Camera relation implementation: pending
- Focused verification: pending
- Stable documentation/finalization: pending

## Interruption Handoff

Implement `PLAN.md` steps 1-7. Do not claim source geometry or math. Preserve
the dirty historical PNGs, stage exact paths only and commit/push this plan
before changing runtime code.
