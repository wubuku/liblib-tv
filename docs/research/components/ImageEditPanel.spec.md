# ImageEditPanel Specification

## Evidence

- **Target file:** `src/components/ImageEditPanel.tsx`
- **Live sample:** LibTV canvas, measured 2026-08-25
- **Trigger:** an `ImageNode` is selected
- **Reference:** `docs/design-references/liblib-original-image-selected-2026-08-25.png`

## Positioning Contract

The editor is not a page-level fixed overlay. It is mounted inside the selected image node so it follows node movement, viewport pan, and viewport zoom.

```text
selected node
└── node shell (position: relative)
    └── ImageEditPanel wrapper
        position: absolute
        left: 50%
        bottom: -17px in the clone's bordered shell
        translate: -50% 100%
        width: 660px
        transform: scale(1 / viewportZoom)
        transform-origin: top center
```

This produces two intentional behaviors:

1. The panel center always equals the selected node's screen-space center.
2. The panel remains `660px` wide on screen. Its gap below the node is `16 * zoom` screen pixels.

The original does not clamp the panel to the viewport. Near an edge, it is clipped by the React Flow container.

Multi-zoom source checks confirm the bottom gap contract at two direct live samples: about `4.525px` at `0.282798` and `8px` at `0.5`, both `16 * zoom`. The source panel stays `660px` wide on screen. The corresponding toolbar is also `1092.5x49` at both samples, but its measured gap above the node is about `16.794px` at 28% and `22px` at 50%; keep that toolbar contract separate until its source positioning formula is fully explained. See [`../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md).

The source class uses `-bottom-4`. The clone mounts the panel directly inside a node shell with a `1px` border, so `-bottom-4` produced only `15 * zoom` outside the node border. The current `-bottom-[17px]` is a clone-specific box-model compensation that restores the source geometry; it is not a claim that the source CSS uses `17px`.

## Live Measurements

At `zoom = 0.282798`, with `分镜 #2` selected:

| Element | Screen rect |
|---|---|
| Selected node | `x=537.278, y=232.188, w=175.900, h=98.979` |
| Edit panel | `x=295.229, y=335.692, w=660.000, h=273.797` |

Both centers are `x=625.23`. The vertical gap is `4.525px`, equal to `16 * 0.282798` within sub-pixel rounding.

With the lower `咖啡` node selected, the panel starts at `x=-24.616`; this confirms that horizontal viewport clamping is not part of the original behavior.

Batch 9 clone measurement at inferred `zoom = 0.283816`:

| Element | Measured result |
|---|---|
| Node / panel center | `393.120 / 393.120` |
| Panel gap | `4.541px = 16 * 0.283816` |
| Panel size | `660x274` |

## Visual Structure

- `660px` fixed screen width
- `16px` corner radius
- `#262626` panel surface with a subtle border and shadow
- source placeholder: `可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜`
- `54x26` reference, mark, and style controls
- optional `47x47` image references
- prompt editor
- `32px` model, output and icon controls
- translation, undo, and generate actions

Panel height is explicit per known source node and must not be inferred only from Prompt presence:

| Source node | Height | Prompt | References | Top controls |
|---|---:|---:|---:|---|
| male | 191 | 0 | 0 | mark / style |
| female | 191 | 0 | 0 | mark / style |
| coffee | 211 | 602 | 0 | mark / style |
| cafe | 191 | 7 | 0 | mark / style |
| storyboard | 274 | 204 | 2 | reference / mark / style |

The `咖啡馆` state directly disproves `hasPrompt => 211px`. Known nodes carry `editorHeight`; only compatibility data falls back to the older variant mapping.

AutoLink is not a visible top-row text pill or a conditional footer icon. Current source evidence places `智能引用 AutoLink` inside the advanced-settings disclosure and persists it through the global local preference `libtv:promptMentionEnabled`, defaulting to enabled.

The source interaction is an inline Prompt workflow: connected/reference assets form the candidate pool, non-committing ghost spans are injected at matching occurrences, and click/`Tab`/`Shift+Tab` accept one or all suggestions. Accepted media mentions are `contenteditable=false` badges carrying stable node ID, media type and projected ordinal. `Escape`, edit and blur reject ghosts; IME composition and stale async results are guarded.

The clone is currently known-inaccurate: it exposes a footer icon only when Prompt exists without references, uses the fixed `陈默 / 咖啡` candidate array, opens a separate confirmation popover, accepts both entries together and prepends ordinary token strings. Do not treat that flow as source-backed. The full source/clone matrix and live dimensions are in [`../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md).

The footer uses icon components instead of the old guessed `⌘` and `▭` text characters. Exact original SVG paths remain unconfirmed. Backend generation remains outside the prototype boundary.

## Panorama Variant

The source-backed `panorama` variant is separate from the five initial image-editor states:

- explicit `252px` screen height;
- one `47x47` source-image reference and numbered badge;
- `+参考`, purple `720` marker and `720全景`;
- helper copy `点击生成，直接将场景图像转为720全景图，支持文生/参考图`;
- `Lib Image` and `2:1 · 标准画质 · 2K · 1张`;
- local-only submit feedback with no generated media.

It uses the same `660px` node-centered inverse-scale wrapper and `16 * zoom` outer gap. It is allowed to clip at desktop and mobile viewport edges.

Stable selectors:

- `[data-panorama-edit-panel]`
- `[data-panorama-reference]`
- `[data-panorama-prompt]`
- `[data-panorama-submit]`

The geometry values are screenshot-derived inference, while the empty node, single reference and visible copy are direct source observations. See [`../liblib-canvas-batch20-2026-08-25/`](../liblib-canvas-batch20-2026-08-25/).

## Interaction Rules

- `nodrag nowheel nopan` prevents editor gestures from moving the React Flow node or viewport.
- Pan, zoom, and node drag must move the panel without a one-frame page-level positioning lag.
- The panel's buttons and textarea remain at normal screen scale at every canvas zoom.
- Multi-selection hides all single-node editing overlays.
- Stable test selector: `data-image-edit-panel`.
- Five-state regression: `scripts/verify-liblib-batch10.py`.
- Panorama regression: `scripts/verify-liblib-batch20.py`.

## Files Referenced

- `src/components/ImageEditPanel.tsx`
- `src/components/nodes/ImageNode.tsx`
- `src/components/ImageToolbar.tsx`
- `scripts/verify-liblib-batch9.py`
- `scripts/verify-liblib-batch10.py`
- `docs/research/liblib-canvas-batch10-2026-08-25/`
