# Upstream Director Desk Screenshot Analysis

> First visual inspection: 2026-08-26. Read this ledger before reopening the
> upstream README screenshots. These screenshots describe the upstream
> implementation, not automatically the current LibTV source.

## Shared Frame

Screenshots `images/01.png` through `images/06.png` are `1728x937`. They show a
dark full-screen editor with four stable regions:

1. a 70px top bar containing `3D导演台`, a centered director/camera segmented
   control and a close button;
2. a 220px left object tree with search, semantic groups and row actions;
3. a central full-bleed WebGL viewport;
4. a 300px right inspector whose content follows selection.

The bottom viewport toolbar is a centered floating capsule inside the viewport.
The axis gizmo sits in the viewport's top-right safe area. Both sidebars overlay
the same full-size canvas rather than shrinking a card inside another card.

## Screenshot Ledger

### `images/01.png`

- State: director view, one character selected, transform/property inspector.
- The left tree contains one character and one camera with visibility and lock
  actions.
- The viewport shows a blue mannequin, ground grid, world-space transform gizmo
  and a billboard label.
- The right inspector shows name, position, rotation, scale, uniform scale and
  color.
- The toolbar exposes transform modes, add/import commands, camera, framing,
  capture variants and fullscreen.

### `images/02.png`

- State: director view, seven character variants, add-character menu open and
  pose inspector selected.
- The character menu includes multiple body silhouettes plus crowd and geometry
  submenus.
- The right inspector exposes a preset grid and continuous body/joint tuning.
- This is direct visual support for the source test phrase `LibTV-style
  procedural body types`.

### `images/03.png`

- State: multiple characters with different poses and one selected transform.
- Selection in the left tree, 3D outline/gizmo and right inspector are visibly
  synchronized.
- Character labels remain screen-facing and scale for readability.
- The viewport supports dense overlapping subjects while the object tree
  remains the deterministic selection fallback.

### `images/04.png`

- State: model-library modal over the live viewport.
- The modal is centered above the viewport and toolbar, not a new route.
- Tabs are `便利生活`, `居家生活`, `户外出行`, `工具配件` and `我的模型`.
- The screenshot shows the intended catalog shell, but the fixed checkout lacks
  the external sibling model assets needed to populate it.

### `images/05.png`

- State: aspect-ratio menu open above its toolbar trigger.
- Options are automatic, `1:1`, `2:1`, `3:4`, `4:3`, `16:9`, `21:9` and `9:16`.
- The menu is compact and trigger-relative. It does not displace the viewport.
- This supports treating the visible frame as capture state, not only display
  decoration.

### `images/06.png`

- State: camera view with the camera inspector.
- The segmented control visibly switches to `机位视角`.
- The inspector contains camera selection, position, look-at mode/target, FOV
  and a camera-capture section.
- The central composition is the active shot rather than an orbit-editor view.
- The empty capture state tells the user to generate a preview from the current
  camera.

### `images/07.jpeg`

- Dimensions: `1200x675`.
- State: exported/captured scene without editor chrome, grid or transform
  helpers.
- Nineteen labeled characters are arranged in a crowd composition with distinct
  colors and poses.
- This is evidence that helper-free capture is a first-class output, not merely
  a screenshot of the editor UI.

## Visual Conclusions

- The upstream UI is already a coherent implementation of the LibTV-like
  director-desk shell, not a generic Three.js sandbox.
- The strongest reusable visual contracts are the three-zone workbench,
  selection synchronization, bottom command capsule, context inspector, visible
  aspect frame and helper-free output.
- The screenshots do not show an animation timeline, motion paths, phone virtual
  camera or animation-video export. Those are current LibTV source capabilities
  that the upstream implementation has not yet replicated.
- Exact colors and dimensions remain upstream implementation facts. They may be
  used as a starting point, then replaced by authenticated LibTV measurements.
