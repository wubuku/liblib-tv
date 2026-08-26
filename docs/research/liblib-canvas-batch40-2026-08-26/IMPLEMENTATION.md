# Batch 40 Implementation Log

> Status: complete. Main implementation, focused browser verification,
> screenshot ledger, stable documentation, Batch 35-40 regression and final
> quality gates passed.

## Protection Points

1. Source export vocabulary and staged failure taxonomy.
2. Upstream absence and frontend WebM calibration boundary.
3. Recording/timeline/crop contract.
4. Atomic canvas video return contract.
5. Playwright, screenshot ledger, regressions and stable docs.

## Current Decisions

- Use real browser canvas recording, not a delayed success mock.
- Keep browser runtime objects out of Zustand.
- Retain source wording where truthful; do not claim upload or MP4 parity.
- Retain the director workspace after success so users can inspect status or
  return through the existing command.

## Main Implementation

### Recording utility

- Added a standalone browser recorder that crops the live R3F WebGL canvas into
  ratio-specific output canvases.
- Added capability checks, WebM MIME negotiation, first-frame pixel validation,
  non-empty blob validation, progress reporting and media-track cleanup.
- The full authored timeline is sampled over the requested output duration.

### Director integration

- Added the source-labeled `导出设置`, `时长`, `比例`,
  `导出视频到画布`, `导出中`, progress, success and error states.
- Export hides the same viewport helpers as still capture, blocks workspace
  close while recording, and restores prior timeline time/playback afterward.
- Browser runtime values remain inside the component/utility boundary.

### Canvas return

- Added `DirectorAnimationExportMetadata` and one
  `createDirectorAnimationExport` graph transaction.
- The transaction creates a ratio-shaped ready video node plus one direct edge,
  selects the result and records one history snapshot.
- `VideoNode` renders director results as a real native `<video>` with controls,
  blob URL, first-frame poster and semantic metadata attributes.

## Browser Smoke Result

Run against the local clone in Chromium at `1440x900`:

- requested a `1s`, `16:9` export;
- recorder produced `video/webm;codecs=vp9`, `60387` bytes;
- browser decoded `960x540` video with approximately `1.004s` duration;
- playback advanced to `0.177s`;
- the graph contained one returned node and its source edge;
- one undo removed the node/edge and one redo restored them;
- no console or page errors occurred.

Quality gates after the main implementation:

```bash
npm run typecheck
npm run lint -- --quiet
git diff --check
```

All passed.

## Focused Verification

Added `scripts/verify-liblib-batch40.py`. It covers:

- exact export labels and all ratio controls;
- finite duration clamping to `1..timeline.duration`;
- live `9:16` composition-frame update;
- exporting progress and close protection;
- prior timeline-time and capture-state restoration;
- still-image capture regression after video export;
- real WebM byte fetch, metadata decode and native playback;
- `540x960` portrait output and approximately `1s` duration;
- sampled early/late video-frame pixel difference proving non-static motion;
- returned metadata, direct edge, ratio-shaped node and target selection;
- one-step undo/redo for node plus edge;
- desktop/mobile overflow and mobile export-panel geometry;
- console, page and request failures.

The focused script passes and generates six Batch 40-only image artifacts.
Their first and only visual interpretation is recorded in
`SCREENSHOT_ANALYSIS.md`.

## Regression And Quality Result

The final gate passed on August 26, 2026:

- `python3 scripts/verify-liblib-batch35.py`
- `python3 scripts/verify-liblib-batch36.py`
- `python3 scripts/verify-liblib-batch37.py`
- `python3 scripts/verify-liblib-batch38.py`
- `python3 scripts/verify-liblib-batch39.py`
- `python3 scripts/verify-liblib-batch40.py`
- `npm run docs:check`
- `npm run check`
- `git diff --check`

`npm run check` completed lint, strict TypeScript and the Next.js production
build. ESLint still reports the same nine existing warnings in FrameOS and
`CustomHandle`; Batch 40 introduced no lint errors or new warning class.

## Commit Protection

- Plan protection: `7a2ffab`.
- Main implementation: `3065e92`.
- Focused verification: `e085e63`.
- Stable documentation/finalization: this documentation-only closeout commit.

## Interruption Handoff

Batch 40 is closed. Read `MATURITY_ASSESSMENT.md` before selecting the next
director batch. The bounded next candidate is phone virtual camera; if live
runtime evidence is insufficient, return to the source-confirmed canvas overlay
action/zoom gaps. Never stage verifier-regenerated historical screenshots.
