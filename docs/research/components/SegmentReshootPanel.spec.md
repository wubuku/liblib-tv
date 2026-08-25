# SegmentReshootPanel

## Purpose

`src/components/SegmentReshootPanel.tsx` is the selected-ready-video lower editor for `片段重拍` and `智能续写`.

## Contract

- Screen width: `660px`
- Lower stack height: `316px`
- Filmstrip: separate `660x56` surface
- Prompt editor: separate `660x252` surface with an `8px` gap
- Filmstrip contains seven selectable 4-second ranges plus a disabled final 2-second remainder
- Reshoot allows at most five selected chunks
- Continue selects one chunk
- Prompt projection uses a `视频 1` token and exact `00:00-00:04`-style range chips
- No-range reshoot permits empty-intent submission because the source bundle defines it as a whole-video rerun
- Continue still requires intent in the local prototype
- Submit produces local whole-rerun, segment-remake or continuation confirmation only

## Structure

```text
lower stack
├── continuous filmstrip
│   ├── proportional 4s ranges
│   ├── disabled 2s remainder
│   └── current/5 count
└── prompt editor
    ├── 参考 / 标记 / 角色库 / expand
    ├── source video tile
    ├── video + range tokens
    ├── editable intent
    └── model/settings/audio/local-submit footer
```

There is no internal “片段重拍” title bar. The active `VideoProcessingToolbar` command switches back to the generator.

## Positioning

The panel uses the same node-relative, inverse-zoom contract as the generation editor. Its clone implementation uses `bottom: -17px` to compensate for the selected video's `1px` shell border and produce the source semantic `16 * zoom` gap.

Stable selectors:

- `[data-segment-reshoot-panel]`
- `[data-segment-filmstrip]`
- `[data-segment-editor]`
- `[data-segment-option]`
- `[data-segment-count]`
- `[data-segment-source]`
- `[data-segment-video-token]`
- `[data-segment-range-token]`
- `[data-segment-intent]`
- `[data-segment-submit]`
- `[data-segment-status]`

## Verification

Verified ready-video creation, separate geometry, proportional ranges, five-range cap, prompt tokens, empty-intent whole rerun, intent submission, generator handoff and mobile clipping.

Evidence:

- `scripts/verify-liblib-batch23.py`
- `docs/design-references/liblib-clone-batch23-segment-reshoot-contact-sheet-2026-08-25.png`
- `docs/research/liblib-canvas-batch23-2026-08-25/`
