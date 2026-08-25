# SegmentReshootPanel

## Purpose

`src/components/SegmentReshootPanel.tsx` is the selected-ready-video lower editor for `片段重拍` and `智能续写`.

## Contract

- Screen width: `660px`
- Normal panel height: `286px`
- Filmstrip contains seven selectable 4-second chunks plus a disabled final 2-second remainder
- Reshoot allows at most five selected chunks
- Continue selects one chunk
- Prompt projection includes `视频 1` and exact `00:00-00:04`-style ranges
- Submit is disabled without user intent text
- Submit produces a local confirmation only

## Positioning

The panel uses the same node-relative, inverse-zoom contract as the generation editor. The panel bottom is intentionally kept above the fixed lower canvas toolbar at the observed desktop zoom.

## Verification

Verified five-chunk selection, prompt projection, disabled submit before intent, enabled submit after intent, local completion text, and geometry (`660x286`) on the local desktop clone. Evidence: `docs/design-references/liblib-clone-seedance-segment-reshoot-2026-08-25.png`.
