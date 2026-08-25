# AssetManagerPanel Specification

## Scope

`src/components/AssetManagerPanel.tsx` is the local 240px asset-management drawer opened from the LibTV bottom canvas toolbar.

## Source-derived shell

- Drawer width: `240px`.
- Drawer is a left-side canvas overlay that causes the main canvas to shrink.
- Header exposes `画布` and `资产` tabs plus a close button.
- Existing canvas view lists current project nodes and selects the corresponding node.

## Clone-only asset view

The `资产` tab is a local derived view over the active canvas:

```text
asset nodes = node.type === "image" || node.type === "video"
```

It must not claim to represent account-owned assets or remote history.

## State contract

| State | Trigger | Result |
|---|---|---|
| Canvas tab | click `画布` | render all active-canvas nodes |
| Asset tab | click `资产` | render image/video nodes only |
| Asset select | click an item | call `selectNode(node.id)` |
| Empty asset list | active canvas has no media nodes | render local empty state |
| Close | click close button | call `toggleAssetPanel()` |

## Selectors

```html
data-asset-manager-tab="canvas"
data-asset-manager-tab="assets"
data-asset-manager-list="canvas"
data-asset-manager-list="assets"
data-asset-manager-item="<node-id>"
```
