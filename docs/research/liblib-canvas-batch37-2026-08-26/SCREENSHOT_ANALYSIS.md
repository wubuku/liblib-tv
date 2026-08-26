# Batch 37 Screenshot Analysis

> Recognition ledger. Read this file before opening a Batch 37 screenshot.
> Record the first visual inspection immediately.

## Evidence

| Screenshot | Viewport / state | Status |
|---|---|---|
| `liblib-clone-batch37-director-path-menu-1440-2026-08-26.png` | path preset menu | inspected |
| `liblib-clone-batch37-director-ring-path-1440-2026-08-26.png` | selected ring trajectory | inspected |
| `liblib-clone-batch37-director-curve-editor-1440-2026-08-26.png` | custom speed curve editor | inspected |
| `liblib-clone-batch37-director-path-playback-1440-2026-08-26.png` | path playback + orientation | inspected |
| `liblib-clone-batch37-director-path-mobile-390-2026-08-26.png` | compact rectangle path + curve workflow | inspected |
| `liblib-clone-batch37-director-path-contact-sheet-2026-08-26.png` | contact sheet | inspected |

Observation date: 2026-08-26. Source is the local clone at
`http://localhost:3000`; screenshots were produced by
`scripts/verify-liblib-batch37.py`. The contact sheet was visually inspected once
after the focused verifier passed.

## Path Menu

- **Direct screenshot facts:** `创建运动轨迹` appears in the existing compact
  timeline command row. Its `176px` dark menu opens directly below the trigger and
  overlays the timeline rows rather than changing the director workspace height.
- The menu contains only the three implemented source-backed presets:
  `直线路径`, `圆环路径`, `矩形路径`. Icons distinguish the geometry without
  introducing explanatory cards or a second modal.
- The R3F scene, object tree, Inspector, timeline labels and keyframe rows remain
  visible behind the menu, preserving editing context.
- **DOM-backed facts:** the menu remains inside the `1440px` viewport and document
  overflow stays zero.

## Ring Trajectory

- **Direct screenshot facts:** the selected ring is a cyan world-space line on
  the scene floor, with small cyan anchors and one white start anchor. It follows
  scene perspective and occlusion rather than behaving like a 2D overlay.
- The ring is visibly associated with the selected character and sits around its
  authored start position. The timeline row gains a small path indicator, while
  enable/orient/delete commands appear in the header.
- The line is bright enough to read over the grid but remains thinner and less
  dominant than the selected object and transform gizmo.
- **DOM/store-backed facts:** the ring has 16 persisted points, is closed/enabled,
  is bound to the character transform track and produces more than 100 changed
  WebGL pixels compared with the helper-free baseline.

## Curve Editor

- **Direct screenshot facts:** curve mode replaces only the timeline body. The
  top director workspace remains live and shows the character sampled to the
  current path position.
- The editor has a compact `返回时间线 / 设置曲线` row, exact preset labels,
  current Bezier values and a stable dark graph with subtle quarter grid lines.
- The cyan curve spans bottom-left to top-right. Two white/cyan handles and their
  guide lines are visible; the screenshot records a custom handle state after a
  real pointer drag.
- The Inspector simultaneously shows the path-controlled Y rotation hint, tying
  the graph, trajectory and transform state together.
- **Store-backed facts:** `缓入` changes the `4s` world position relative to
  linear sampling; dragging a handle switches the preset to `custom`, keeps all
  values finite/in-range and changes the same sampling pipeline.

## Playback

- **Direct screenshot facts:** playback returns to the ordinary timeline. The
  pause icon, cyan playhead, world-space ring and moved/oriented character are
  visible in one state.
- The path remains an authoring helper while the character position and facing
  update along it. The trajectory does not replace object selection or the
  transform gizmo.
- **DOM/store-backed facts:** after about `320ms`, time and object position both
  advance; deleting/disabling a path safely restores ordinary keyframe sampling.

## Mobile

- At `390x844`, the rectangle trajectory remains visible in the live R3F scene
  and follows perspective. The viewport toolbar stays reachable above the
  `176px` timeline band.
- The long command row is internally scrolled to the path/curve controls; it does
  not widen the document.
- Curve mode keeps the compact editor in the bottom band. Presets and the
  `440px` graph scroll inside their own containers; the screenshot intentionally
  shows a cropped portion of the graph rather than shrinking labels or handles.
- **DOM/store-backed facts:** one rectangle path is bound, `缓出` affects the
  selected track, graph scroll width exceeds client width, and document/body
  overflow checks pass.

## Capture And Fact Boundary

- The focused verifier creates a real capture while a ring path is active. The
  raw PNG contains fewer than 20 cyan-helper pixels, confirming that trajectory,
  anchors, gizmo and other authoring helpers remain outside returned media.
- These screenshots prove the Batch 37 clone result, not exact LibTV runtime
  geometry. Path dimensions, point counts, line/anchor styling, menu placement,
  curve graph geometry and preset Bezier values are clone calibration.
- Current LibTV source evidence directly supports the workflow, labels, path
  presets, curve presets, Bezier adjustment and orient-to-path behavior.
- Pencil/pen drawing, editable path anchors/handles, path offsets and animation
  video export remain unresolved in this visual set.
