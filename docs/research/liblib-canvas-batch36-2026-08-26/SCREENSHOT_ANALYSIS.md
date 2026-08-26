# Batch 36 Screenshot Analysis

> Recognition ledger. Read this file before opening a Batch 36 screenshot.
> Record the first visual inspection immediately.

## Evidence

| Screenshot | Viewport / state | Status |
|---|---|---|
| `liblib-clone-batch36-director-timeline-1440-2026-08-26.png` | `1440x900`, default timeline | inspected |
| `liblib-clone-batch36-director-keyframe-1440-2026-08-26.png` | selected keyframe and sampled scene | inspected |
| `liblib-clone-batch36-director-playback-1440-2026-08-26.png` | active playback | inspected |
| `liblib-clone-batch36-director-timeline-mobile-390-2026-08-26.png` | compact timeline + tree drawer | inspected |
| `liblib-clone-batch36-director-timeline-contact-sheet-2026-08-26.png` | contact sheet | inspected |

Observation date: 2026-08-26. Source is the local clone at
`http://localhost:3000`; screenshots were produced by
`scripts/verify-liblib-batch36.py`. The contact sheet was visually inspected once
after the focused verifier passed.

## Desktop Timeline

- **Direct screenshot facts:** the existing top bar and three-zone director
  workspace remain visually intact. A full-width `196px` timeline band occupies
  the bottom of the `1440x900` viewport without floating over the object tree,
  R3F viewport or Inspector.
- The timeline is divided into a command row, a fixed `220px` label column and a
  ruler/track canvas. This aligns the label column with the object-tree rail while
  allowing the time surface to use the remaining width.
- The compact command row contains the source-backed interaction vocabulary:
  play/pause, previous/next keyframe, loop, timecode, auto-keyframe, track,
  keyframe, delete and zoom.
- Two rows are visible by default: character transform and camera. Both show
  complete diamonds at `0s`, `4s` and `8s`; the corrected endpoint diamonds no
  longer clip at either horizontal boundary.
- The selected character row uses a restrained cyan band. Grid/ruler lines remain
  subordinate to the R3F scene rather than turning the timeline into a bright
  spreadsheet.
- **DOM-backed facts:** the timeline root is `1440x196` at `y=704`; the initial
  track/keyframe counts are `2 / 6`; document and body have no horizontal overflow.

## Keyframe Selection And Playback

- At the selected `4s` character keyframe, the cyan playhead crosses the ruler and
  both track rows. The selected diamond is cyan while unselected diamonds remain
  neutral gray, giving track and keyframe selection distinct but related states.
- The R3F character visibly changes from the default left-side position to the
  center/right sampled pose. The Inspector simultaneously shows the sampled
  transform, so scene, timeline and form communicate one authored state.
- During playback, the pause icon replaces play and the timecode/playhead advance
  to about `4.4s`; the character is visibly between authored fixture positions.
- **Store-backed facts:** exact `4s` sampling produces character X `0.65`;
  playback advances both time and transform; loop-off stops at `8s`.

## Mobile

- At `390x844`, the timeline becomes a `176px` bottom band. It stays below the
  live R3F viewport and does not overlap the top bar.
- The open `220px` object-tree drawer still ends above the timeline. The uncovered
  viewport remains visible to the right, preserving scene context.
- The timeline label column contracts to `132px`; track names truncate rather than
  resizing rows. The command row and time canvas scroll internally, so controls
  beyond the right edge do not create page overflow.
- The cyan playhead and selected diamond remain visible at the compact size.
- **DOM-backed facts:** the timeline is `390x176` at `y=668`; both internal regions
  have scrollable width and document/body overflow checks pass.

## Fact Boundary

- These screenshots prove the local Batch 36 clone result. The `196/176px`
  heights, fixed label widths, eight-second duration and fixture motion are clone
  calibration, not measured LibTV runtime geometry.
- Current LibTV source evidence directly supports the timeline, playhead,
  play/pause, loop, zoom, track/keyframe lifecycle, typed transform/camera
  keyframes and navigation vocabulary.
- Curve shape, Bezier handles, motion-path geometry, pose/group runtime and video
  export remain unresolved in these images and are intentionally deferred.

## Interim Smoke Inspection

`/tmp/liblib-batch36-smoke.png` was captured once from the local clone at
`1440x900` after opening the director, seeking to `4s`, playing to about `4.47s`
and adding a mug transform track. This is a non-durable smoke artifact, not final
design evidence.

- **Direct screenshot facts:** the timeline occupies a `1440x196` full-width
  bottom band below the object-tree / R3F / Inspector region. It does not overlap
  the viewport toolbar or side rails.
- The command row visibly contains title, play, previous/next, active loop,
  timecode, active auto-keyframe, track/keyframe commands, delete and zoom.
- Three rows are visible: character transform, camera and the newly added mug
  transform track. The mug row selection matches the selected tree row and
  Inspector.
- The cyan playhead crosses ruler and rows near `4.47s`; the live scene shows the
  character between its `4s` and `8s` fixture positions.
- **DOM/store-backed facts:** the initial two tracks contain six keyframes;
  seeking `4s` changes character X from `-1.25` to `0.65`; `450ms` playback moves
  time and character again; adding the mug produces exactly one third track;
  no console or page error occurred.
- **Issue found and resolved:** diamonds at `0s` and `8s` were clipped by the
  horizontal content boundary. DOM measurement showed a rotated `12px` marker has
  a visual box near `16.97px`; marker centers now use a `9px` inner clamp. The
  final screenshots confirm full endpoint diamonds.
