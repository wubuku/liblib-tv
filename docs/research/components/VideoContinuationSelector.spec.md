# VideoContinuationSelector

## Purpose

`src/components/VideoContinuationSelector.tsx` is the selected-ready-video lower timeline used by `智能续写`. It is a separate workflow from `SegmentReshootPanel`.

## Source Contract

- Screen width: `660px`
- Screen height: `56px`
- Timeline height: `48px`
- Start/end handle width: `16px`
- Node-relative center anchor
- Source margin: `8 * zoom`
- Initial range: `0-min(sourceDuration, 30)`
- Valid duration: `4-30s`
- Start, end and whole-region pointer drag
- Two-decimal selected duration
- Close/Escape cancel and `确认续写`

## Graph Handoff

Confirm creates a connected right-side `video` target with continuation metadata. The target owns the continuation Prompt; the selector does not include a Prompt editor.

## Evidence

- `docs/research/liblib-canvas-batch26-2026-08-25/SOURCE_EVIDENCE.md`
- `docs/research/liblib-canvas-batch26-2026-08-25/VIDEO_CONTINUATION_WORKFLOW.spec.md`
- current source bundles sampled on 2026-08-25

## Stable Selectors

- `[data-video-continuation-selector]`
- `[data-video-continuation-timeline]`
- `[data-video-continuation-start]`
- `[data-video-continuation-end]`
- `[data-video-continuation-region]`
- `[data-video-continuation-duration]`
- `[data-video-continuation-confirm]`
- `[data-video-continuation-close]`
