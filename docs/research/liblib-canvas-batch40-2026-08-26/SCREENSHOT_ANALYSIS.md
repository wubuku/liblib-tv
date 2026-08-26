# Batch 40 Screenshot Analysis

> First visual inspection completed on 2026-08-26 from the generated contact
> sheet. Read this ledger before reopening any Batch 40 image. The individual
> images were not separately re-inspected.

## Capture Context

| Property | Value |
|---|---|
| site | local LibTV clone |
| desktop viewport | `1440x900`, DPR 1 |
| mobile viewport | `390x844`, DPR 1 |
| source zoom | browser default |
| desktop ratio under test | `9:16` |
| mobile ratio under test | `1:1` |
| recognition source | `liblib-clone-batch40-director-animation-export-contact-sheet-2026-08-26.png` |

## Artifact Ledger

| Artifact | Interaction state | First-inspection result |
|---|---|---|
| `liblib-clone-batch40-director-export-settings-1440-2026-08-26.png` | director open, timeline at `2s`, export panel idle, `9:16` selected | A compact dark panel is anchored below the top-right export command and overlays the Inspector rather than shifting the three-column layout. Icon/title, duration row, three ratio options, format note and full-width primary command are visible. The active ratio has a cyan outline/fill. The centered portrait composition frame remains visible behind the panel; grid and selected-object transform gizmo are still visible because recording has not begun. |
| `liblib-clone-batch40-director-exporting-1440-2026-08-26.png` | active browser recording | The panel stays at the same coordinates and dimensions. A cyan progress rail, spinner, `正在导出动画视频...` copy, percentage and disabled gray primary button replace the idle state without panel reflow. The top header also shows an exporting indicator. Grid, camera rig/path helpers and transform gizmo are absent from the viewport while scene objects remain visible, directly confirming helper-free recording mode. |
| `liblib-clone-batch40-director-export-success-1440-2026-08-26.png` | recording complete, prior timeline restored | The same panel shows a green check/success row and a full cyan progress rail. The primary export command becomes available again. The portrait frame, floor grid and selected transform gizmo return. The playhead is visibly back at the pre-export `2s` position rather than remaining at the animation end. |
| `liblib-clone-batch40-director-video-return-1440-2026-08-26.png` | director closed, returned result selected | A portrait video node appears below/right of the source director node and is connected by a direct edge. The node media is the recorded 3D scene, with native video controls visible along its bottom edge and a cyan selected outline. Existing ready-video processing controls open above the selected node, and the existing generation/editor surface remains attached below/right. Their wide geometry is inherited clone behavior, not newly measured LibTV export geometry. |
| `liblib-clone-batch40-director-export-mobile-390-2026-08-26.png` | mobile director, panel idle, `1:1` selected | The export trigger collapses to an icon in the header. The `286px` settings panel remains fully inside the `390px` viewport, below the header and above the timeline. All labels, numeric duration, three ratio buttons, note and primary command fit without clipping. The square composition frame is visible behind the panel and the document has no horizontal overflow. |
| `liblib-clone-batch40-director-animation-export-contact-sheet-2026-08-26.png` | combined first-inspection surface | Five states are readable without reopening individual images. Desktop settings/recording/success use stable geometry; graph return and mobile adaptation are visually distinct. |

## Layer And Geometry Findings

- **Direct pixels:** the export panel is above the right Inspector and viewport,
  but below the global full-screen header layer; it does not resize the
  viewport, tree, Inspector or timeline.
- **Direct pixels:** desktop panel width and row dimensions stay fixed across
  idle, recording and success states. Progress/status content does not shift
  the panel.
- **Direct pixels:** the portrait aspect frame remains centered within the
  viewport safe area and is not occluded by the bottom viewport toolbar.
- **Direct pixels:** the returned portrait node preserves media aspect ratio;
  the existing wide selected-video toolbar/editor extends beyond the node body.
- **Direct pixels:** mobile panel left/right margins are visibly non-zero and
  all content remains above the timeline.
- **DOM-backed:** Playwright measured the returned media at `540x960`, decoded
  approximately `1.0s`, and confirmed a `9:16` React Flow node ratio.
- **DOM-backed:** Playwright measured no root/body overflow at desktop or
  mobile sizes.

## Evidence Classification

### LibTV source-backed

- Labels: `导出设置`, `时长`, `比例`, `导出视频到画布`,
  `正在导出动画视频...`, `导出中`, `动画视频已导出到画布`.
- Settings → recording → success → returned canvas video workflow.

### Clone calibration

- Header trigger and panel placement.
- `286px` panel width, typography, colors, spacing and animation.
- Duration range, ratio output pixels, WebM format note and native video
  controls.
- Keeping the director open after success.
- Selecting the returned video and exposing existing ready-video processing
  tools immediately.

### No longer unresolved

- The local export panel has stable desktop geometry across all three states.
- Recording mode removes viewport helpers from captured pixels.
- Portrait and mobile outputs do not overflow their containers.
- The returned local video is visible and playable rather than a pending or
  decorative placeholder.

## Recognition Rule

Do not reopen these images to recover the findings above. Re-inspect only when
answering a new question, after a visual implementation change, or when a
specific region is marked uncertain. Prefer the smallest relevant individual
image or crop instead of the full contact sheet.
