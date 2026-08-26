# Batch 39 Screenshot Analysis

> Recognition ledger. Read this file before opening a Batch 39 screenshot.
> First inspection completed on August 26, 2026. Re-open only for a new,
> explicitly missing visual question.

## Evidence Index

| Screenshot | Viewport / state | Status |
|---|---|---|
| [`liblib-clone-batch39-director-path-transform-1440-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-path-transform-1440-2026-08-26.png) | `1440x900`, non-identity path transform | inspected |
| [`liblib-clone-batch39-director-world-anchor-1440-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-world-anchor-1440-2026-08-26.png) | `1440x900`, transformed symmetric anchor | inspected |
| [`liblib-clone-batch39-director-reset-offset-1440-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-reset-offset-1440-2026-08-26.png) | `1440x900`, edited geometry after offset reset | inspected |
| [`liblib-clone-batch39-director-full-reset-1440-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-full-reset-1440-2026-08-26.png) | `1440x900`, creation snapshot restored | inspected |
| [`liblib-clone-batch39-director-path-transform-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-path-transform-mobile-390-2026-08-26.png) | `390x844`, transform/reset Inspector | inspected |
| [`liblib-clone-batch39-director-path-transform-contact-sheet-2026-08-26.png`](../../design-references/liblib-clone-batch39-director-path-transform-contact-sheet-2026-08-26.png) | `1488x1845`, combined states | inspected |

All screenshots use device scale factor `1`. No screenshot in this ledger is
LibTV source evidence; each proves only the current clone implementation.

## First Inspection

### Path transform

Direct screenshot facts:

- The cyan rectangle has moved forward/right and rotated relative to its
  creation position while retaining four visible world anchors.
- The path remains inside the established aspect frame and does not alter the
  tree, viewport toolbar or bottom timeline geometry.
- The right Inspector shows exact `位置`, `旋转` and `缩放` labels as compact
  three-axis rows, followed by `重置偏移` and `重置`.
- The current character sample follows the transformed path rather than the
  untransformed local rectangle.

DOM-backed facts:

- Local anchors remain byte-for-byte equal to the initial snapshot.
- Transform values are position `[1.6,0.4,-0.35]`, rotation `[0,48,0]` and
  scale `[1.45,1,0.7]`.
- World points and the character position changed while the local anchors did
  not.

### World anchor

Direct screenshot facts:

- The selected world anchor is displaced from the original rectangle corner.
- A gold handle endpoint and guide line are visible alongside the cyan path and
  selected anchor.
- The Inspector keeps whole-path transform rows visible above the anchor grid
  and selected symmetric-anchor controls.

DOM-backed facts:

- A requested world anchor target round-trips through the store inverse
  transform within `0.001`.
- A requested world output-handle target creates a local handle whose opposite
  handle is the exact negative tuple.
- Curved sampling expands beyond the four straight preset points.

### Reset offset

Direct screenshot facts:

- Whole-path transform fields visibly return to position/rotation zero and
  scale one.
- The path does not return to the pristine rectangle: its moved first anchor and
  curved corner remain visible.
- The selected anchor and handle editing state stay active.

DOM-backed facts:

- Edited anchors are preserved exactly.
- `path.points[0]` returns to the edited local anchor position under identity
  transform.
- The path remains bound to the same timeline track.

### Full reset

Direct screenshot facts:

- The path returns to a straight four-corner rectangle with the original
  placement and identity transform fields.
- The first restored anchor remains selected, so authoring can continue without
  losing path context.
- The reset does not disturb the surrounding director workspace or timeline.

DOM-backed facts:

- A previously inserted fifth anchor is removed.
- Current anchors equal the deep creation snapshot and the pivot equals the
  creation pivot.
- Position/rotation/scale all return to identity.

### Mobile

Direct screenshot facts:

- At `390x844`, the 288px right drawer exposes all three transform rows, both
  reset commands and the four-anchor selector in one internally scrollable
  column.
- A narrow scene strip remains visible on the left and the bottom timeline
  remains visible below the drawer.
- Numeric values fit their three-column fields; the two reset labels fit their
  side-by-side commands without clipping.

DOM-backed facts:

- Rotation Y persists as `35`.
- The drawer ends at or before the 390px viewport edge.
- Document and body scroll widths remain bounded by client widths.

## Calibration Boundary

- Pivot choice, X→Y→Z order, per-axis scale, transform field placement, button
  hierarchy and reset semantics are clone calibration.
- The screenshots do not prove source transform gizmos, ranges, steps, negative
  scale handling or exact Inspector geometry.
- Source claims remain limited to the exact path property/reset labels in
  `SOURCE_EVIDENCE.md`.
