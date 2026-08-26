# Batch 45 Screenshot Analysis

> First and only focused visual reading for this batch, recorded on
> 2026-08-26. The images are clone verification outputs, not screenshots of
> the authenticated LibTV source. Read this ledger before inspecting them
> again.

## Capture Setup

| Field | Value |
|---|---|
| Browser | Playwright Chromium, headless |
| Desktop viewport | `1440×900`, device scale factor `1` |
| Mobile viewport | `390×844`, device scale factor `1` |
| Route | local clone `/` with `?batch45=1` |
| Render surface | live R3F WebGL canvas plus Director Desk DOM |
| Capture set | `CROWD_PANEL`, `CROWD_GROUP`, `GROUP_KEYFRAME`, `GROUP_PLAYBACK`, `MULTI_SELECT`, `MOBILE` |

## Direct Visual Observations

### `CROWD_PANEL`

Path: `docs/design-references/liblib-clone-batch45-director-crowd-panel-1440-2026-08-26.png`

- The Director Desk remains a three-region shell: object tree at left, R3F
  viewport in the center and Inspector at right, with the timeline spanning
  the bottom.
- `添加群众阵列` opens a compact dark panel centered above the viewport
  toolbar. It contains the title, computed count, `行数 × 列数`, `间距`,
  `取消` and `添加`.
- The panel does not cover the timeline in this desktop state.
- The viewport remains visibly non-empty behind the panel: lead mannequin,
  table/mug, wall and grid are all visible.

### `CROWD_GROUP`

Path: `docs/design-references/liblib-clone-batch45-director-crowd-group-1440-2026-08-26.png`

- After adding `2×3`, six colored mannequin characters appear as a compact
  centered array to the right of the lead character.
- The left tree shows a selected crowd group row with a group icon and member
  count; the right Inspector changes to `分组属性` and shows `群众`, member
  count, array metadata and transform fields.
- The bottom timeline still preserves the original character and camera
  tracks. The crowd group is not represented as six unrelated timeline rows.
- The group selection state is visible in the tree and Inspector. The R3F
  transform operation is represented by the selected group anchor in the live
  canvas, while the individual meshes remain ordinary scene objects.

### `GROUP_KEYFRAME`

Path: `docs/design-references/liblib-clone-batch45-director-group-keyframe-1440-2026-08-26.png`

- The group timeline row is visibly distinct from the ordinary transform and
  camera rows and contains group keyframe diamonds.
- The Inspector's position X field is edited at a later playhead time; the
  crowd moves as a unit while retaining its internal arrangement.
- The timeline playhead is at the later keyframe and the viewport shows the
  updated crowd anchor. This is consistent with the verifier's store assertion
  that all member positions remain finite and are updated by fan-out.

### `GROUP_PLAYBACK`

Path: `docs/design-references/liblib-clone-batch45-director-group-playback-1440-2026-08-26.png`

- The later scrubbed/playback state visibly differs from the initial crowd
  state in the WebGL pixel comparison.
- The group row remains selected while the timeline is scrubbed; the object
  tree and Inspector do not collapse or switch to a single member.
- The camera and character tracks remain present, so group animation is
  additive to the existing Director timeline rather than a replacement.

### `MULTI_SELECT`

Path: `docs/design-references/liblib-clone-batch45-director-multi-select-1440-2026-08-26.png`

- The object tree shows a manually created two-character group after
  Shift-based selection and `打组`.
- The group is promoted to a stable tree row and Inspector target; it is not
  only a temporary selection highlight.
- `解组` is verified by DOM/store assertions to remove the group row and
  group track while preserving the member objects.

### `MOBILE`

Path: `docs/design-references/liblib-clone-batch45-director-crowd-mobile-390-2026-08-26.png`

- At `390×844`, the full-screen Director shell switches to the compact
  mobile layout with top controls, a single viewport and bottom timeline.
- The crowd panel remains within the viewport bounds and sits above the
  viewport toolbar/timeline area; the panel does not create document-level
  horizontal overflow.
- The mobile screenshot intentionally captures the panel before submission,
  so it documents the authoring entry state rather than the six-person result.

## DOM-Backed Findings

- The Playwright script measured panel and viewport bounding boxes rather than
  relying on visual estimates.
- The script asserted six unique member IDs, six unique positions, finite
  transform tuples, selected group state, group-track metadata and removal
  semantics.
- The script compared the WebGL canvas at timeline `0` and `4` and observed a
  non-zero pixel difference; it also observed playback advance the playhead.
- No console, page or failed-request errors were collected in the tested
  desktop/mobile flows.

## Evidence Boundaries

- These screenshots prove clone behavior and visual coherence only.
- They do not prove that LibTV uses the same panel dimensions, colors,
  centered-array placement, derived-anchor formula, R3F gizmo shape or
  timeline row styling.
- Rows/columns/spacing limits, average-position anchoring and the compact panel
  geometry remain clone calibration, explicitly separated in
  [`DIRECTOR_GROUPS.spec.md`](DIRECTOR_GROUPS.spec.md).
- A `data-director-group-rig` attribute on an R3F `<group>` is not a DOM
  selector. The verifier therefore uses store selection plus visual/state
  assertions for the runtime rig and does not mistake Three object props for
  browser DOM evidence.
