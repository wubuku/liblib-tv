# Segment Reshoot Editor Specification

## Scope

- `src/components/SegmentReshootPanel.tsx`
- ready video 的 `片段重拍` lower editor

## Layer model

```text
selected ready video
├── VideoProcessingToolbar
└── lower stack (node-anchored, inverse zoom)
    ├── segment filmstrip surface
    └── prompt editor surface
```

The lower stack remains `660px` screen width and uses the established `bottom:-17px` clone compensation for the source semantic `16 * zoom` gap.

## Filmstrip

- 7 selectable `4.0s` ranges covering `00:00-00:28`;
- final `2.0s` remainder is disabled;
- selected range uses cyan outline and duration badge;
- count is `{current}/5 个片段`;
- reshoot selection stops at five ranges;
- filmstrip is visually separate from the editor.

Stable selectors:

- `[data-segment-reshoot-panel]`
- `[data-segment-filmstrip]`
- `[data-segment-option]`
- `[data-segment-count]`

## Prompt editor

- no internal “片段重拍” header;
- top command row: `参考`, `标记`, `角色库`, expand;
- one source-video reference tile;
- when ranges exist, show:
  - video token `视频 1`;
  - one range chip per selected range;
  - editable intent after the tokens;
- without ranges, show the whole-video helper and permit empty submission.

Stable selectors:

- `[data-segment-editor]`
- `[data-segment-source]`
- `[data-segment-video-token]`
- `[data-segment-range-token]`
- `[data-segment-intent]`
- `[data-segment-submit]`
- `[data-segment-status]`

## Submission boundary

- no ranges + empty intent: local whole-video rerun feedback;
- ranges selected + optional intent: local segment-remake feedback;
- no network request, credits mutation, media creation or result-node claim.

## Fidelity boundary

The source evidence is an article composite plus current bundle strings, not a live DOM rect. Exact panel height, original media and source SVG icons remain clone-only approximations. `智能续写` is not covered by this contract and is implemented separately by Batch 26.
