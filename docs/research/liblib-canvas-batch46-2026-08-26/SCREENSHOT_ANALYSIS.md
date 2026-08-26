# Batch 46 Screenshot Analysis

> First and only focused visual reading for this batch, recorded on
> 2026-08-26. These are clone verification outputs, not authenticated LibTV
> screenshots. Read this ledger before opening the contact sheet again.

## Capture Setup

| Field | Value |
|---|---|
| Browser | Playwright Chromium, headless |
| Desktop viewport | `1440x900`, device scale factor `1` |
| Mobile viewport | `390x844`, device scale factor `1` |
| Route | local clone `/` |
| Render surface | live R3F WebGL canvas plus Director Desk DOM |
| Capture set | `EMPTY`, `GALLERY`, `VIEWER`, `RETURN + EMPTY`, `MOBILE` |
| Contact sheet | `docs/design-references/liblib-clone-batch46-director-capture-contact-sheet-2026-08-26.png` |

## Direct Visual Observations

### `EMPTY`

Path: `docs/design-references/liblib-clone-batch46-director-capture-empty-1440-2026-08-26.png`

- The Director Desk keeps the established three-region shell: scene tree on
  the left, R3F viewport in the center and Inspector on the right, with the
  timeline spanning the bottom.
- Selecting a camera and opening `摄像机截图` replaces the previous single
  preview with a dedicated gallery surface.
- The empty state is centered in the scrollable Inspector area and includes an
  image-library affordance plus `暂无摄像机截图`.
- `全部清空` and `发送到画布` remain visible in a fixed footer and are
  disabled when there are no records.

### `GALLERY`

Path: `docs/design-references/liblib-clone-batch46-director-capture-gallery-1440-2026-08-26.png`

- Two composition records render as compact square thumbnails in a three-column
  grid, grouped under the active camera label.
- The active record has a cyan selection border; both records retain their
  camera-derived labels and small per-card actions.
- The central R3F scene remains visible and non-empty while the gallery is
  open. The gallery does not alter the timeline or scene tree ownership.
- The fixed footer separates local record management (`全部清空`) from the
  canvas transaction (`发送到画布`).

### `VIEWER`

Path: `docs/design-references/liblib-clone-batch46-director-capture-viewer-1440-2026-08-26.png`

- The viewer is a black, full-viewport layer with the captured composition
  centered and the Director Desk visibly dimmed behind it.
- The upper-right toolbar provides compact icon-only controls for zoom out,
  zoom in, download and close.
- The image keeps its composition ratio and is bounded by the viewport rather
  than stretching the Inspector column.
- The viewer is rendered through a body portal so its stacking context covers
  the Director header and all side panels.

### `RETURN + EMPTY`

Path: `docs/design-references/liblib-clone-batch46-director-capture-return-1440-2026-08-26.png`

- After one single send and one bulk send, two capture nodes remain on the
  canvas graph while the local Director gallery is cleared.
- Reopening the camera screenshot tab shows the same empty state, proving that
  local gallery cleanup is separate from returned React Flow node ownership.
- The scene, camera framing and timeline remain intact after the return/clear
  workflow.

### `MOBILE`

Path: `docs/design-references/liblib-clone-batch46-director-capture-mobile-390-2026-08-26.png`

- At `390x844`, the Director shell uses the existing mobile drawer pattern.
- The Inspector drawer remains inside the viewport and the camera tabs stay
  readable without horizontal document overflow.
- The empty gallery and fixed footer fit within the narrow drawer; the R3F
  canvas and timeline remain visible behind the drawer.

## DOM-Backed Findings

- The focused verifier measures the viewer at the full `1440x900` document
  bounds and confirms the gallery stays inside the Inspector bounds on desktop
  and mobile.
- It verifies two camera-tagged records, active selection changes, bounded
  viewer zoom, Escape dismissal, single-send idempotence, bulk-send
  idempotence and clear-all confirmation.
- It confirms that clearing local records leaves both returned graph nodes in
  place.
- Desktop and mobile flows collect zero console errors, page errors or failed
  requests.

## Runtime Fixes Captured By This Batch

Two integration defects were found during the focused run and fixed before
closeout:

1. A viewer nested inside the `Inspector` stacking context could be visually
   present while its toolbar was blocked by the Director header. The viewer is
   now portaled to `document.body`.
2. The Director shell Escape handler could close the entire workspace before
   the gallery closed its viewer. The shell now yields when a capture viewer is
   present.

## Evidence Boundaries

- These screenshots prove clone behavior and visual coherence only.
- The current LibTV locale proves screenshot-management vocabulary and states;
  it does not prove these exact panel dimensions, colors, thumbnail cropping or
  graph transactions.
- The upstream StoryAI implementation proves a borrowable interaction
  hierarchy, not current LibTV runtime geometry.
- Camera grouping is derived from the clone's existing `cameraName` field; it
  is not presented as recovered LibTV camera-document serialization.
