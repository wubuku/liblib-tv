# Batch 38 Screenshot Analysis

> Recognition ledger. Read this file before opening a Batch 38 screenshot.
> First inspection completed on August 26, 2026. Re-open only for a new,
> explicitly missing visual question.

## Evidence Index

| Screenshot | Viewport / state | Status |
|---|---|---|
| [`liblib-clone-batch38-director-pencil-path-1440-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-pencil-path-1440-2026-08-26.png) | `1440x900`, committed pencil path | inspected |
| [`liblib-clone-batch38-director-pen-draft-1440-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-pen-draft-1440-2026-08-26.png) | `1440x900`, active pen draft | inspected |
| [`liblib-clone-batch38-director-anchor-editor-1440-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-anchor-editor-1440-2026-08-26.png) | `1440x900`, selected asymmetric anchor | inspected |
| [`liblib-clone-batch38-director-path-playback-1440-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-path-playback-1440-2026-08-26.png) | `1440x900`, pen path playback | inspected |
| [`liblib-clone-batch38-director-path-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-path-mobile-390-2026-08-26.png) | `390x844`, path Inspector drawer | inspected |
| [`liblib-clone-batch38-director-path-authoring-contact-sheet-2026-08-26.png`](../../design-references/liblib-clone-batch38-director-path-authoring-contact-sheet-2026-08-26.png) | `1488x1845`, combined states | inspected |

All screenshots use device scale factor `1`. No screenshot in this ledger is
LibTV source evidence; each proves only the current clone implementation.

## First Inspection

### Pencil path

Direct screenshot facts:

- The full-screen desk retains the established three-band composition: 48px
  header, scene/tree/Inspector work area, and bottom timeline.
- A dense cyan freehand path wraps around the table; persisted vertex anchors
  read as a continuous chain rather than three preset-only control points.
- The selected first anchor shows the translate gizmo in the viewport.
- The right Inspector remains attached to the character and exposes the
  `运动轨迹` section, pencil source label, editable name, enabled/open state,
  17-anchor grid and selected-anchor controls.
- The path and object do not visually displace the aspect frame, viewport
  toolbar or timeline.

DOM-backed facts:

- The path has 17 anchors and 17 straight sampled points before conversion.
- The first anchor is selected and the path Inspector exists exactly once.

### Pen draft

Direct screenshot facts:

- The previously committed cyan pencil path stays visible while the new pen
  draft is orange, making replacement pending rather than destructive.
- The orange draft uses three large control points and two curved segments.
- `正在绘制曲线` appears in a compact overlay above the viewport toolbar with
  completion and cancellation controls.
- The right Inspector still shows the preserved pencil path while drawing.

DOM-backed facts:

- Draft anchor types are `symmetric`, `vertex`, `symmetric`.
- Capture is disabled during the draft.
- The selected object remains the path-bound character throughout pointer
  gestures.

### Anchor editor

Direct screenshot facts:

- The committed path remains cyan with a selected anchor and visible transform
  gizmo.
- The Inspector shows the anchor grid, `顶点` / `对称` / `非对称` segmented
  control, position fields and handle fields in one vertically scrollable rail.
- The selected `非对称` state uses the same compact active treatment as the
  rest of the desk instead of a detached modal or floating card.

DOM-backed facts:

- Editing one asymmetric output handle leaves the input handle unchanged.
- The same edit rebuilds `path.points`, so the screenshot is not a cosmetic
  control-only state.

### Path playback

Direct screenshot facts:

- The replacement pen path is a sparse, readable cyan curve across the table
  with three anchor positions and visible selected-anchor handle guides.
- The timeline playhead is beyond zero and the playback command shows its
  running state.
- The character is sampled on the curve while the right Inspector continues to
  expose the pen path and selected anchor.

DOM-backed facts:

- The committed pen path has three anchors and 25 sampled points.
- Playback advances both timeline time and the character position.
- The helper-free PNG capture contained zero detected cyan and orange helper
  pixels.

### Mobile

Direct screenshot facts:

- At `390x844`, the 288px Inspector drawer occupies the right side of the
  viewport and leaves roughly 102px of the scene visible on the left.
- The drawer stays between the fixed header and bottom timeline; it does not
  push either outside the viewport.
- Internal vertical scrolling exposes the path name, enabled/open controls,
  17-anchor grid, anchor type control, XYZ position and insert/delete commands.
- Text and numeric controls remain inside the drawer; no document-width
  overflow or card-within-card structure is visible.

DOM-backed facts:

- The drawer finishes at or before the 390px viewport edge.
- Document and body scroll widths remain bounded by their client widths.

## Calibration Boundary

- Cyan/orange helper color, point radii, handle guide thickness, Inspector
  geometry and the horizontal drawing plane are clone calibration.
- The screenshots do not establish LibTV's exact camera pose, pointer
  thresholds, completion gesture, anchor density or responsive breakpoint.
- Source-backed claims remain limited to the vocabulary and workflow recorded
  in `SOURCE_EVIDENCE.md`; implementation-only observations stay in this file.
