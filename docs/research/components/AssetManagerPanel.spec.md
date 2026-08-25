# AssetManagerPanel Specification

## Current Contract

`AssetManagerPanel` is the LibTV clone's 240px left drawer opened from the bottom canvas toolbar.

- `画布` tab lists all nodes in the active canvas.
- `资产` tab lists only active-canvas `image` and `video` nodes.
- Clicking either list item selects the corresponding node through `canvasStore.selectNode`.
- Closing the drawer calls `useUIStore.toggleAssetPanel`.
- The asset view is a local derived prototype view, not a remote account asset library.

## Evidence and Batch History

- Source shell and gap audit: [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- Batch plan and evidence boundary: [`../liblib-canvas-batch12-2026-08-25/README.md`](../liblib-canvas-batch12-2026-08-25/README.md)
- Implementation and verification: [`../liblib-canvas-batch12-2026-08-25/IMPLEMENTATION.md`](../liblib-canvas-batch12-2026-08-25/IMPLEMENTATION.md)
