# Batch 43 Screenshot Analysis

> This ledger records the one completed visual inspection of the Batch 43
> clone screenshots. Read this file before opening the same images again.

## Capture Matrix

| Screenshot | Surface | Viewport | State |
|---|---|---:|---|
| `../../design-references/liblib-clone-batch43-director-look-at-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | object look-at, no follow |
| `../../design-references/liblib-clone-batch43-director-follow-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | character follow, third person, `4s` |
| `../../design-references/liblib-clone-batch43-director-first-person-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | same target/time/offset, first person |
| `../../design-references/liblib-clone-batch43-director-phone-conflict-1440-2026-08-26.png` | clone | `1440x900`, 100% zoom | followed camera rejects phone preview |
| `../../design-references/liblib-clone-batch43-director-follow-mobile-390-2026-08-26.png` | clone | `390x844`, 100% zoom | mobile Inspector follow controls |
| `../../design-references/liblib-clone-batch43-director-camera-follow-contact-sheet-2026-08-26.png` | clone | composite | all five states above |

Capture date: 2026-08-26. All images are local clone verification, not
authenticated LibTV source screenshots.

## Desktop Look-At

- The full-screen Director shell retains the established layer order: object
  tree, WebGL viewport with frame mask, Inspector, floating viewport toolbar
  and timeline.
- The camera Inspector shows `注视目标` with `角色01 · 陈默` selected,
  followed by disabled derived `注视坐标` fields reading approximately
  `-1.25 / 1.48 / 0.20`.
- `跟随目标` remains `不跟随`; follow offset and view controls are absent.
- The camera view remains nonblank and framed. The retained Y rotation value
  is visible above, while object mode visibly frames the selected character
  target rather than using manual rotation.
- No control text clips the right Inspector and no panel crosses the timeline.

## Third-Person Follow

- At `4s`, the selected character is centered as the dominant camera-view
  subject and appears much closer than in the object-look-at screenshot.
- The Inspector visibly stacks the selected object target, derived coordinate,
  `跟随目标`, `跟随偏移` values `0 / 1.2 / 4.5`, and the two equal-width
  `跟随视角` segments.
- `第三人称` is the active cyan-tinted segment; `第一人称` is inactive.
- The amber exact-copy guard `请先关闭机位跟随，再绘制轨迹` appears directly
  below the segmented control.
- Existing ring-path controls remain below the relation section. This supports
  the intended non-destructive conflict behavior: the path still exists but
  new path authoring is unavailable while follow is active.

## First-Person Follow

- The same playhead, target and offset produce a materially different WebGL
  frame: the character shifts toward the lower-right foreground and the
  background composition changes.
- `第一人称` is active while `第三人称` is inactive. The segmented control
  does not resize or shift between modes.
- The derived camera target fields change to the forward target produced by
  the clone-calibrated first-person rule.
- The exact path guard stays visible and the existing path section remains
  serialized below it.
- The close foreground crop is a clone-calibrated consequence of the current
  offset and forward-distance math, not a recovered LibTV camera formula.

## Phone Conflict

- The phone virtual-camera panel is layered above the WebGL viewport and below
  neither the right Inspector nor the timeline; it remains entirely inside
  the viewport region.
- Its header, local-preview badge, red error status, QR placeholder,
  `启动本机预演` command and amber exact conflict copy are all visible.
- The Inspector simultaneously preserves the active first-person follow state
  and path guard, so the rejected phone action does not clear camera
  relationships or existing paths.
- The panel does not cover the timeline controls or overflow the document.

## Mobile

- The Inspector drawer occupies the right side from below the Director header
  to above the compact timeline. A narrow WebGL strip remains visible behind
  it, preserving spatial context.
- The vertically scrolled camera section exposes object look-at, disabled
  coordinates, follow target, three offset inputs, both view segments and the
  exact path guard.
- The longest visible labels fit within the drawer. Inputs stay in three
  stable columns, segmented controls remain two equal tracks and there is no
  horizontal document overflow.
- The timeline remains visible and usable below the drawer; its track labels
  truncate rather than widening the page.

## Evidence Classification

### Direct clone screenshot facts

- all layout, text visibility, selected states, clipping and layer-order
  observations above;
- third- and first-person frames are visibly different;
- desktop and mobile controls remain within their containing surfaces.

### DOM/store-backed facts from the same verification

- look-at modes and stable target IDs serialize correctly;
- the target is sampled before camera relation resolution at `0s`, `4s` and
  during playback;
- camera-track FOV reaches `47` at `4s`;
- path creation/drawing and phone connection/recording are rejected;
- disabling follow restores ordinary path-sampled camera values.

### Not source evidence

- Inspector geometry, focus heights, offset values, yaw-relative math,
  first-person forward distance and resulting composition;
- the QR placeholder and local-preview transport boundary;
- any exact LibTV Three.js/R3F implementation detail.

## Reinspection Rule

Do not reopen these screenshots to recover the facts above. Reinspect only if
the images are regenerated after a relevant UI change or a new question
requires a smaller crop that this ledger does not answer.
