# Video Model Menu Specification

## Scope

- `src/components/VideoGenerationPanel.tsx`
- model trigger and source-visible model popover

## Geometry

```text
width: 380px
height: 410px
left relative to generation panel: ~0px
top relative to generation panel: ~-176.7px
```

The current clone footer layout expresses this as trigger-relative `left:-9px; bottom:32px`.

## Source-visible items

| ID | Label | Estimate | Premium |
|---|---|---|---|
| `2.5` | Seedance 2.5 | `2min` | yes |
| `2.0 VIP` | Seedance 2.0 VIP | `2min` | yes |
| `Minimax H3` | Minimax H3 | `2min` | yes |
| `2.0 Fast VIP` | Seedance 2.0 Fast VIP | `2min` | yes |
| `2.0 Mini` | Seedance 2.0 Mini | `2min` | yes |
| `Wan 3.0 Prime` | Wan 3.0 Prime | `1min` | no |
| `Wan 3.0` | Wan 3.0 | `3min` | no |

`Kling O3` is not part of this source-visible state.

## Row behavior

- all rows show icon tile, title and estimate pill;
- premium rows show a gold diamond;
- only the selected row shows description and expanded selected surface;
- clicking a row updates the footer model and closes the popover;
- reopening the menu shows the new selected row.

Known descriptions:

- Seedance 2.5: `最强视频模型，全能参考，30s音画同步`
- Seedance 2.0 Fast VIP: `最强视频模型快速版，会员专属通道，15s音画同步`

Other descriptions remain absent until directly extracted.

## Stable selectors

- `[data-video-model-trigger]`
- `[data-video-model-menu]`
- `[data-video-model-option]`
- `[data-video-model-premium]`
- `[data-video-model-description]`

## Non-goals

- No completeness or availability claim.
- No real model invocation.
- No exact source SVG logos.
- No model-menu search, scrolling or keyboard navigation without source evidence.

