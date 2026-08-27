# AssetManagerPanel Specification

## Current Contract

`AssetManagerPanel` is the LibTV clone's 240px left drawer opened from the bottom canvas toolbar.

- The context row shows `canvasStore.projectName` and the active canvas name.
- Clicking the active canvas context hands off to the top canvas dropdown through
  the page-owned Asset layout transaction.
- `画布` tab lists all nodes in the active canvas.
- `资产` tab lists only active-canvas `image` and `video` nodes.
- The canvas tab renders top-level nodes plus direct `parentId` children as a one-level tree.
- The source project uses its saved 10-item asset-manager order; unknown nodes have a stable fallback.
- Sort, type filter and search are local browse controls over the active canvas.
- Clicking either list item selects the corresponding node through `canvasStore.selectNode`.
- Closing from the explicit X uses the page-owned Asset layout transaction; the
  component does not own React Flow instance or viewport formulas.
- The asset view is a local derived prototype view, not a remote account asset library.
- Empty copy distinguishes no nodes from no media assets.

## Evidence and Batch History

- Source shell and gap audit: [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- Batch plan and evidence boundary: [`../liblib-canvas-batch12-2026-08-25/README.md`](../liblib-canvas-batch12-2026-08-25/README.md)
- Implementation and verification: [`../liblib-canvas-batch12-2026-08-25/IMPLEMENTATION.md`](../liblib-canvas-batch12-2026-08-25/IMPLEMENTATION.md)
- Source-shaped context/tree upgrade: [`../liblib-canvas-batch17-2026-08-25/`](../liblib-canvas-batch17-2026-08-25/)
- Host-resize anchor preservation:
  [`../liblib-canvas-batch64-2026-08-27/`](../liblib-canvas-batch64-2026-08-27/)
