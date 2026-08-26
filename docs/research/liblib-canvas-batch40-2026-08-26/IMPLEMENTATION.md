# Batch 40 Implementation Log

> Status: main implementation and browser smoke complete. Focused Playwright,
> screenshot ledger, cross-batch regression and stable closeout are pending.

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

## Commit Protection

- Plan protection: `7a2ffab`.
- Main implementation: pending.
- Focused verification: pending.
- Stable documentation/finalization: pending.

## Interruption Handoff

Add `scripts/verify-liblib-batch40.py` for real media bytes/metadata/playback,
timeline restoration, ratio output, graph selection/edge/history, still-capture
regression and mobile geometry. Generate only Batch 40 screenshots, inspect
them once into `SCREENSHOT_ANALYSIS.md`, and never stage verifier-regenerated
historical screenshots.
