# Batch 40 Implementation Log

> Status: plan protected. Main implementation and verification are pending.

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

## Commit Protection

- Plan protection: pending.
- Main implementation: pending.
- Focused verification: pending.
- Stable documentation/finalization: pending.

## Interruption Handoff

Implement `directorVideoExport.ts`, connect it through `DirectorDesk` and
`DirectorViewport`, add `canvasStore.createDirectorAnimationExport`, and render
the returned blob URL in `VideoNode`. Stage only intentional Batch 40/code/doc
files; historical screenshots are verifier noise.
