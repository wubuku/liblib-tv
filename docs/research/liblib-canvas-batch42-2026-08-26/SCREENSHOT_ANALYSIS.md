# Batch 42 Screenshot Analysis

> Recognition policy: interpreted once from the Batch 42 contact sheet on
> 2026-08-26. Read this ledger before opening any individual screenshot.

## Provenance

Source: local LibTV clone at `http://localhost:3000`.

Capture script: `scripts/verify-liblib-batch42.py`.

Viewports:

- desktop: `1440x900`, device scale factor `1`;
- mobile: `390x844`, device scale factor `1`.

Contact sheet:

```text
docs/design-references/liblib-clone-batch42-director-pose-contact-sheet-2026-08-26.png
```

The contact sheet and all images below are **clone verification artifacts**,
not authenticated LibTV source screenshots.

## State Ledger

### Pose presets

Screenshot:
`liblib-clone-batch42-director-pose-presets-1440-2026-08-26.png`.

Direct screenshot facts:

- the three-zone director workspace remains visible: object tree, unframed R3F
  viewport, 288px Inspector and full-width bottom timeline;
- the character is an articulated mannequin with visible head, torso, limb
  segments and joints rather than the former rigid six-part primitive;
- the selected `姿势` tab, `姿势预设` title and four-column 20-button matrix fit
  within the Inspector without horizontal clipping;
- active `站立` styling uses the existing cyan director accent;
- `姿势调节` and the beginning of `SAM 骨骼姿势` remain visible below the
  preset matrix;
- the transform and camera timeline rows remain unchanged before a pose edit.

DOM-backed facts from the verifier:

- exactly 20 preset commands and six SAM groups exist;
- all 20 source preset labels, six source group labels and 14 source bone
  labels are present;
- the nonblank WebGL canvas passes variance and range checks.

### SAM controls

Screenshot:
`liblib-clone-batch42-director-sam-controls-1440-2026-08-26.png`.

Direct screenshot facts:

- applying `招手` produces a visibly bent raised arm and changed upper-body
  silhouette in the real R3F viewport;
- the right-arm group expands in place within the Inspector;
- bone taxonomy appears as muted compact text while individual channels use
  label, numeric degree output and cyan range input;
- the panel scrolls vertically without resizing the viewport or timeline;
- the new pose timeline row is visible and selected at the bottom.

DOM-backed facts:

- the stored preset is `wave`;
- `rightElbow.bend` equals `90`;
- the first pose edit creates one pose track and one `0s` keyframe;
- stand-to-wave canvas pixels differ measurably.

### Pose track

Screenshot:
`liblib-clone-batch42-director-pose-timeline-1440-2026-08-26.png`.

Direct screenshot facts:

- the character is visibly sampled in the `踢球` endpoint while also occupying
  its `4s` transform-track position;
- the timeline contains three independent rows: character transform, camera
  and character pose;
- the pose row uses a distinct standing-person icon and cyan selected state;
- pose diamonds align with `0s` and `4s`;
- the right-side preset matrix shows `踢球` active.

DOM-backed facts:

- the lead character's track kinds are exactly `transform` and `pose`;
- the pose track label is `角色01 · 陈默 · 姿态`;
- a direct store request to create a ring path on the pose track is rejected
  without mutating motion paths.

### Interpolated pose

Screenshot:
`liblib-clone-batch42-director-pose-interpolation-1440-2026-08-26.png`.

Direct screenshot facts:

- at `2s` the character silhouette is visibly between the wave and kick
  endpoints rather than snapping to either;
- no preset button is falsely highlighted; the panel reports a custom state;
- the transform playhead and pose keyframe row remain aligned in the shared
  timeline.

DOM-backed facts:

- transform X is approximately `-0.3`;
- right shoulder pitch is `18°`;
- right elbow bend is `45°`;
- the intermediate rig preset identity is `null`;
- endpoint and intermediate WebGL pixels differ.

### Mobile pose

Screenshot:
`liblib-clone-batch42-director-pose-mobile-390-2026-08-26.png`.

Direct screenshot facts:

- the existing right Inspector drawer occupies the right 288px and leaves a
  narrow live viewport strip visible on the left;
- the drawer starts below the 48px workspace header and ends directly above
  the 176px compact timeline;
- `属性 / 姿势`, the complete four-column preset matrix and `看手机` active
  state fit the drawer width;
- the first expanded SAM group remains readable; lower controls continue by
  internal vertical scrolling;
- the pose timeline row is visible below with a distinct icon and selected
  keyframe;
- no text or control visibly crosses the viewport edge.

DOM-backed facts:

- the drawer stays inside `390px`;
- the pose panel has no horizontal overflow;
- its scroll parent has greater scroll height than client height;
- the document and body have no horizontal overflow.

## Layer And Geometry Conclusions

- Pose controls belong to the existing Inspector scroll layer, not a floating
  viewport popover.
- The timeline remains a sibling below the viewport/Inspector region, so
  expanding SAM groups never covers timeline controls.
- Desktop and mobile use the same pose content; responsive behavior is
  provided by the existing Inspector drawer rather than a second mobile UI.
- Fixed preset/button dimensions keep the grid stable when active/custom state
  changes.

## Evidence Boundary

Source-backed vocabulary visible in the clone:

- `姿势`, `姿势预设`, `姿势调节`, `SAM 骨骼姿势`;
- 20 preset names;
- six SAM groups and 14 bone names;
- the distinct pose track/keyframe concept.

Clone-calibrated and not source-proven:

- exact 288px Inspector geometry;
- four-column grid, colors, spacing and typography;
- mannequin geometry/materials and scene placement;
- slider channels, limits, values and expanded-group defaults;
- standing-person track icon, marker styling and linear pose interpolation.

No new source screenshot was captured, so pixel fidelity against LibTV's
current pose panel remains unresolved. Another screenshot inspection is
justified only after obtaining an authenticated source pose state or changing
the clone images.
