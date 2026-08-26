# Batch 35 Screenshot Analysis

> Recognition ledger. Read this file before visually reopening any Batch 35
> screenshot. Reinspect only for a new question or after pixels change.

## Evidence

| Screenshot | Viewport / state | Status |
|---|---|---|
| `liblib-clone-batch35-director-desktop-1440-2026-08-26.png` | `1440x900`, default director view | inspected |
| `liblib-clone-batch35-director-camera-1440-2026-08-26.png` | `1440x900`, camera view + 16:9 frame | inspected |
| `liblib-clone-batch35-director-capture-1440-2026-08-26.png` | `1440x900`, capture preview | inspected |
| `liblib-clone-batch35-director-output-16x9-2026-08-26.png` | raw helper-free PNG | inspected |
| `liblib-clone-batch35-director-return-1440-2026-08-26.png` | `1440x900`, returned image node | inspected |
| `liblib-clone-batch35-director-mobile-390-2026-08-26.png` | `390x844`, compact viewport + drawer | inspected |
| `liblib-clone-batch35-director-contact-sheet-2026-08-26.png` | contact sheet | inspected |

Observation date: 2026-08-26. Source is the local Batch 35 clone at
`http://localhost:3000`; screenshots were produced by
`scripts/verify-liblib-batch35.py`. The final contact sheet and raw capture were
visually inspected after the verifier passed.

## Desktop Director View

- **Direct screenshot facts:** the 48px top bar, 220px object tree, central dark
  3D viewport and 288px Inspector form one full-screen editor without floating
  page cards. The center viewport is `932x852` at `1440x900`.
- The object tree shows one character, three scene objects and one camera. The
  selected character uses a cyan row edge and the Inspector shows name, visible,
  color and three stable XYZ field grids.
- The 16:9 frame is centered above the viewport toolbar. The scene contains a
  procedural character, table, cup, wall/window blocks, ground, shadows and grid.
- TransformControls are visible only for the selected scene object. The reduced
  camera rig remains a small authoring object in director view and no longer
  dominates the foreground.
- **DOM-backed facts:** the root covers `1440x900`; React Flow remains mounted
  behind it; the WebGL canvas has non-zero range on all RGB channels and channel
  standard deviations above 26.

## Camera View And Guides

- **Direct screenshot facts:** switching to camera view changes the composition
  to the active shot and routes the right rail to camera name, transform, FOV and
  target controls.
- The current active camera rig and its TransformControls are absent from its own
  view. This was not true in the first screenshot pass: the rig occupied a large
  cyan shape on the right. The final image records the corrected state.
- The rule-of-thirds lines align to the 16:9 frame, not to the whole viewport.
- **DOM-backed facts:** switching to `9:16` changes the frame geometry to a
  portrait ratio and switching back restores `16:9`; the WebGL canvas remains
  nonblank in camera mode.

## Capture Preview And Raw PNG

- The capture view keeps the authored frame and guides visible in the editor,
  while the right rail adds a fixed current-capture preview and send command.
- The saved raw PNG is `852x479`, a `16:9` result within rounding tolerance.
- **Direct raw-image facts:** the PNG contains only scene geometry, materials,
  lighting and shadows. It does not contain grid lines, TransformControls,
  camera rig, aspect frame, thirds guides, toolbar, sidebars or labels.
- This establishes helper-free output visually; the verifier independently
  checks PNG dimensions, aspect and pixel variance.

## Canvas Return

- **Direct screenshot facts:** after close, the original React Flow graph remains
  in its existing viewport and contains a new image node showing the captured
  composition. The new node participates in the existing edge topology.
- **DOM-backed facts:** return adds exactly one image node and one source edge;
  close reselects the source director node; one undo removes both and one redo
  restores both.

## Mobile

- At `390x844`, the top bar keeps return, product name, both view modes and close
  reachable on one row.
- The object tree becomes a 220px left drawer over a full-screen viewport. The
  uncovered portion of the live 3D viewport and toolbar remains visible.
- The right Inspector is a symmetric 288px right drawer and is mutually exclusive
  with the tree in the automated flow.
- **DOM-backed facts:** both drawers finish flush with their respective viewport
  edge after the 200ms transition; document and body have no horizontal overflow.

## Fact Boundary

- The screenshots prove the current clone result, not exact current LibTV source
  geometry. Panel widths and the procedural coffee-shop scene are Batch 35
  calibration based on the existing replication and current clone language.
- The source-backed product truth remains: a 3D director surface, camera framing,
  composition capture and output back to the canvas.
- Exact original colors, shell dimensions, current asset catalog and animation
  timeline geometry remain unresolved runtime questions for later calibration.

