# Batch 43 Implementation Log

> Status: complete. Implementation, focused verification, cross-batch
> regression and stable documentation passed on 2026-08-26.

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
- [x] serializable camera relation and pure math
- [x] Inspector and R3F camera behavior
- [x] conflict guards
- [x] focused browser verification and screenshots
- [x] screenshot interpretation ledger
- [x] cross-batch regression and stable documentation

## Commits

- Plan/evidence protection: `4aa0fb3`
- Camera relation implementation: `8a4baf5`
- Focused verification: `4ff8976`
- Stable documentation/finalization: this closeout commit

## Implemented

- Added a pure, serializable camera-relation module with coordinate, rotation
  and object look-at plus target-local first/third-person follow resolution.
- Changed timeline evaluation to sample every object first and resolve camera
  relationships in a second pass, so animated targets drive the camera at the
  same playhead.
- Preserved relation fields through camera-track sampling, phone-camera pose
  updates, imports, restoration and object cloning.
- Added exact source-named Inspector controls and stable selectors.
- Applied manual Euler rotation to the real R3F camera only in rotation mode;
  coordinate/object/follow modes use the resolved target.
- Guarded preset/free path authoring and phone-camera connection/recording in
  both UI and store actions without deleting existing paths or tracks.

## Verification

Passed:

```text
python3 scripts/verify-liblib-batch43.py
python3 scripts/verify-liblib-batch35.py ... batch43.py
npm run docs:check
npm run check
git diff --check
```

The full quality gate reported the nine existing FrameOS/`CustomHandle`
warnings and no errors. Focused checks prove all three look-at modes, animated
target follow, same-time first/third-person pixel differences, FOV composition,
path/phone guards, recovery after disabling follow and desktop/mobile bounds.

## Interruption Handoff

Batch 43 is closed. Continue from [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md).
The next evidence-first Director candidate is source `预设运镜`; groups/crowds
remain second. Do not claim source geometry or math, and preserve the dirty
historical PNGs by staging exact paths only.
