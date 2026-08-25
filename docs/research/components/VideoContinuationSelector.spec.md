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

The store transition is one history transaction. Target data contains the source ID/label/poster, selected start/end seconds and declared edge ID. The target is selected after creation.

## Implementation Notes

- The selector is mounted inside the selected source node and inverse-scaled by `1 / zoom`.
- The clone uses `bottom: -9px` to compensate for the node's `1px` border and produce the source semantic `8 * zoom` gap.
- Capture-phase Escape cancels the selector before the page-level Escape handler clears selection.
- Wrapper pointer/click propagation is stopped so confirm cannot re-select the source after the store selects the target.
- Timeline thumbnails loop local assets and do not claim real frame extraction.

## Verification

`scripts/verify-liblib-batch26.py` covers:

- geometry and anchor at 100%/50%;
- initial range, both handles and region drag;
- minimum/maximum duration constraints;
- close/Escape;
- graph creation, target selection and undo/redo;
- source drag/canvas pan following;
- multi-selection hiding and mobile clipping.

## Evidence

- `docs/research/liblib-canvas-batch26-2026-08-25/SOURCE_EVIDENCE.md`
- `docs/research/liblib-canvas-batch26-2026-08-25/VIDEO_CONTINUATION_WORKFLOW.spec.md`
- `docs/research/liblib-canvas-batch26-2026-08-25/SCREENSHOT_ANALYSIS.md`
- `docs/design-references/liblib-clone-batch26-continuation-contact-sheet-2026-08-25.png`
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
