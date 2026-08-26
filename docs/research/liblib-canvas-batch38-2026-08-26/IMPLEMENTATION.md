# Batch 38 Implementation Log

> Status: evidence and implementation plan complete; product work pending.

## Protection Points

1. Current source hashes, exact vocabulary and evidence boundary.
2. Serializable anchor/handle contract and pure curve rebuild.
3. Store drawing/edit lifecycle.
4. R3F drawing/TransformControls and Inspector/timeline UI.
5. Playwright, screenshot ledger, regressions and stable docs.

## Current Decisions

- Preserve Batch 37's `path.points` sampling boundary and derive it from richer
  anchors.
- Keep drawing draft serializable; keep pointer state and Three.js refs local to
  R3F components.
- Use separate selectors for free-draw tools so Batch 37's exact three-preset
  contract remains stable.
- Do not implement path transforms or animation export in this batch.

## Commit Protection

- Plan protection: pending.
- Implementation protection: pending.
- Verification/finalization: pending.

## Interruption Handoff

If interrupted after the plan commit, begin with
`src/components/director/directorMotionMath.ts` and
`src/store/directorStore.ts`. Add pure anchor-to-polyline rebuilding before
touching R3F. Do not stage concurrent `docs/research/open-canvas-2026-08-26/`
changes or verifier-regenerated historical screenshots.

