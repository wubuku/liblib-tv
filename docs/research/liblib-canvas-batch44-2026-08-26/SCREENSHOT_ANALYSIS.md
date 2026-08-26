# Batch 44 Screenshot Analysis

> This ledger records the one completed visual inspection of the Batch 44
> clone screenshots. Read it before reopening the same images.

## Capture Matrix

| Screenshot | Surface | Viewport | State |
|---|---|---:|---|
| `../../design-references/liblib-clone-batch44-director-preset-panel-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | selected camera track, preset panel open |
| `../../design-references/liblib-clone-batch44-director-preset-replace-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | `环绕` replacement, playhead at `4s` |
| `../../design-references/liblib-clone-batch44-director-preset-append-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | `拉远` append, playhead at `6s` |
| `../../design-references/liblib-clone-batch44-director-preset-no-room-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | append rejected at timeline end |
| `../../design-references/liblib-clone-batch44-director-preset-follow-conflict-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | followed camera plus phone conflict panel |
| `../../design-references/liblib-clone-batch44-director-preset-mobile-390-2026-08-26.png` | clone | `390x844`, 100% zoom | compact camera timeline with preset panel |
| `../../design-references/liblib-clone-batch44-director-preset-camera-contact-sheet-2026-08-26.png` | clone | composite | all six states above |

Capture date: 2026-08-26. These are local clone verification screenshots,
not authenticated LibTV source screenshots.

## Desktop Preset Panel

- The Director shell retains the established three-zone hierarchy: semantic
  object tree at left, framed R3F viewport in the middle, camera Inspector at
  right and the full-width timeline at the bottom.
- `预设运镜` opens as a dark compact surface anchored to the selected camera
  timeline context. It has a 40px header, a two-segment `替换运镜 / 追加运镜`
  control, a two-column grid of seven source-named choices and a stable
  status/error row.
- The panel uses the same restrained dark surface, thin white border and cyan
  active state as the rest of the Director authoring UI. The seven buttons keep
  stable dimensions; `螺旋上升` occupies the final single grid cell without
  widening the surface.

## Replacement And Append States

- `环绕` replacement changes the camera-view composition and expands the
  camera track to the complete `0..8s` generated sequence. The selected camera
  remains the same and the playhead remains independently controllable.
- `拉远` append keeps the existing early keyframes visible and adds the
  generated tail through the timeline end. The active option and green status
  line identify the last application without changing the Inspector width.
- The no-room state keeps the panel and timeline stable. The amber error line
  appears in the reserved status area rather than causing surrounding
  controls to shift.

## Conflict State

- When follow is active, the timeline trigger is visibly disabled and the
  exact amber copy `跟随目标时不可使用预设运镜` remains available in the
  timeline context.
- The follow screenshot preserves the existing R3F scene, camera Inspector
  and phone virtual-camera panel. The rejected preset action does not replace
  keyframes or remove the camera relationship.
- This is a clone state composition verified through DOM/store assertions; it
  is not evidence that the source uses the same overlay placement.

## Mobile

- At `390x844`, the compact Director shell leaves a visible framed R3F strip
  above the timeline and keeps the right-side authoring context intact.
- The preset surface is `304px` wide and expands upward from the timeline
  boundary. Its bottom edge stays at the timeline top within one device pixel,
  so the timeline control band remains visible and the document has no
  horizontal or vertical overflow.
- All seven options remain discoverable in the two-column grid. The internal
  content region is scrollable if the viewport becomes shorter than the
  panel's stable content height.
- The panel is intentionally allowed to obscure part of the lower viewport;
  this preserves the trigger's context while avoiding an off-screen bottom
  popover.

## Evidence Classification

### Direct clone screenshot facts

- visible layer order, dark surfaces, cyan selected states, panel text,
  seven-option grid, timeline relation, and desktop/mobile clipping;
- replacement, append, no-room and follow-conflict screenshots show distinct
  visible states;
- mobile panel bounds and timeline preservation are supported by the focused
  geometry assertions.

### DOM/store-backed facts from the same verification

- all seven generated trajectories contain finite values and change the real
  R3F canvas at a matched playhead;
- replacement spans `0..8s`, append starts at the latest prior keyframe and
  preserves the earlier sequence;
- no-room and follow conflicts reject atomically;
- an existing generic path remains serialized but becomes disabled after
  successful preset application;
- browser console, page-error and request-failure collections are empty.

### Not source evidence

- panel dimensions, icon choices, upward placement, keyframe counts, preset
  geometry, duration allocation, easing, FOV policy and path-disable behavior;
- any assumption that the public LibTV locale extraction reveals the source
  implementation or authenticated runtime DOM.

## Reinspection Rule

Do not reopen these screenshots to recover the facts above. Reinspect only
after a relevant UI change, regenerated reference image, or a new question
that this ledger does not answer.
