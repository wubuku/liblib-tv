# Batch 41 Screenshot Analysis

> Screenshot recognition ledger. Read this file before opening any Batch 41
> screenshot. Add each artifact immediately after its first visual inspection.

## Source Runtime

No authenticated source screenshot for the phone virtual-camera feature has
been captured. Locale evidence proves workflow vocabulary but not visual
geometry. Do not use clone screenshots as source evidence.

## Planned Clone Artifacts

| Artifact | Viewport/state | First inspection |
|---|---|---|
| `liblib-clone-batch41-director-phone-waiting-1440-2026-08-26.png` | desktop waiting/local-preview boundary | inspected in contact sheet |
| `liblib-clone-batch41-director-phone-controls-1440-2026-08-26.png` | desktop connected controls | inspected in contact sheet |
| `liblib-clone-batch41-director-phone-recording-1440-2026-08-26.png` | desktop active take | inspected in contact sheet |
| `liblib-clone-batch41-director-phone-imported-1440-2026-08-26.png` | desktop imported camera track | inspected in contact sheet |
| `liblib-clone-batch41-director-phone-mobile-390-2026-08-26.png` | mobile connected controls | inspected in contact sheet |
| `liblib-clone-batch41-director-phone-contact-sheet-2026-08-26.png` | summary sheet | inspected once on 2026-08-26 |

## First And Only Visual Inspection

Inspection source:
`liblib-clone-batch41-director-phone-contact-sheet-2026-08-26.png`,
`1488x1845`, generated from four `1440x900` desktop captures and one
`390x844` mobile capture. The individual screenshots are clone evidence, not
LibTV source evidence.

### Waiting / Local Boundary

- The panel is anchored inside the lower-right of the central 3D viewport and
  stays above the viewport toolbar. It does not cover the right Inspector.
- Layer order is scene, composition frame, panel, then unchanged fixed
  workspace shell/timeline.
- The header shows the phone icon, `虚拟相机`, cyan `本机预演` badge and close.
- A blue waiting dot and same-Wi-Fi source sentence precede a square,
  intentionally non-scannable pairing motif with an overlaid `本机预演` label.
- Certificate guidance and the light `启动本机预演` command remain inside the
  panel without clipping.
- The exact placement, motif and dimensions are clone-calibrated because no
  source runtime screenshot exists.

### Connected Controls

- The expanded panel rises toward the viewport top but preserves the scene,
  left object tree, right Inspector, toolbar and timeline as separate visible
  regions.
- Visible vertical order is connection status, GYRO value/pad, gyro/calibrate
  commands, stability slider, level/hold/elevation row, time/remaining row and
  fixed-height record command.
- The cyan pose marker is clearly visible against the restrained black grid.
  Text and controls do not overlap at desktop size.
- The active view is `机位视角`; the selected camera remains synchronized
  between object tree and Inspector.

### Recording

- The workspace header gains a red pulse/status at the far right while the
  panel status also turns red.
- The record command changes to a stable-width red `停止录制` button; sample
  count replaces remaining duration without shifting the layout.
- Export, capture and close commands visibly enter disabled styling.
- The timeline playhead has advanced from the recording start and the 3D
  camera composition differs from the connected screenshot, matching the
  tested live-pose change.

### Imported Camera Track

- Green connection/import feedback replaces the recording state and the
  primary command returns to `录制`.
- `手机运镜 1` appears simultaneously in the left object tree, right Inspector
  name field and a new selected timeline row.
- The imported row contains a dense sequence of camera keyframe diamonds, with
  the last keyframe/playhead selected. This visually confirms that the result
  is a real typed track rather than a toast-only mock.
- The panel, scene and timeline remain readable with no incoherent overlap.

### Mobile Controls

- DOM-backed geometry from the same verification run:
  `x=12`, `y=131`, `width=366`, `height=465` at `390x844`.
- The panel uses the full safe mobile width while keeping both 12px side
  margins. Its bottom remains above the viewport toolbar; the toolbar remains
  above the timeline.
- Header, GYRO pad, two-command row, slider, four-control row and record command
  all fit without horizontal clipping.
- The compact workspace header and timeline remain partially visible, so the
  phone surface reads as an overlay within the director rather than a new
  route.

## Interpretation Boundary

- **Direct screenshot facts:** hierarchy, visible text/state, non-overlap,
  imported object/track visibility and responsive fit.
- **DOM-backed facts:** viewport sizes, mobile panel geometry, no document
  overflow, state selectors and disabled controls.
- **Source-backed but not visually verified:** same-Wi-Fi QR flow, certificate
  trust, source phone-connected state and exact control wording.
- **Clone-calibrated:** trigger/panel placement, colors, spacing, pairing motif,
  pose-pad geometry and mobile dimensions.

## Reinspection Rule

Reopen only the smallest artifact needed to answer a new question. The first
inspection must record visible hierarchy, geometry, text fit, clipping,
interaction state, direct DOM-backed facts and any remaining uncertainty.
