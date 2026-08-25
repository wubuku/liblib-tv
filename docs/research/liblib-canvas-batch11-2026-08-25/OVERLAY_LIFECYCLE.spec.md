# Overlay Lifecycle Specification

## Scope

This contract covers the LibTV route's top-level canvas surfaces. It does not unify LibTV and FrameOS state.

## Surface taxonomy

| Surface | Owner | State |
|---|---|---|
| Bottom primary panel | `LeftSidebar` | `uiStore.activePrimaryPanel` |
| Add node | `AddNodePanel` | `uiStore.isAddNodePanelOpen` |
| Keyboard shortcuts | `KeyboardShortcutsDialog` | `uiStore.isShortcutsPanelOpen` |
| Canvas dropdown | `CanvasTabDropdown` | `uiStore.isCanvasDropdownOpen` |
| Asset drawer | `AssetManagerPanel` | `uiStore.isAssetPanelOpen` |
| Share menu | `TopNavBar` | `uiStore.isSharePanelOpen` |
| Agent drawer | `AgentDrawer` | `uiStore.isAgentOpen` |
| Zoom menu | `BottomToolbar` | `uiStore.isZoomMenuOpen` |
| Organize confirmation | `page.tsx` local transaction state | intentionally independent |

## Mutual exclusion

Opening one top-level surface closes all other top-level surfaces. Closing the currently open surface does not open another one.

The primary panel values are:

```text
move | toolbox | material | character | history | tutorial | null
```

## Mode lifecycle

- `storyboard` mode opens Agent and closes other top-level surfaces.
- `workbench` mode closes Agent.
- Mode switching does not change graph nodes, edges or viewport.

## Escape lifecycle

`Escape` calls `closeAllPanels()` and clears the selected node through the existing page handler. The result must be:

- no primary panel;
- no add-node panel;
- no shortcut panel;
- no canvas dropdown;
- no asset drawer;
- no share menu;
- no Agent drawer.
- no zoom menu.

## Selector contract

Visible surfaces expose:

```html
data-liblib-overlay="primary:toolbox"
data-liblib-overlay="asset"
data-liblib-overlay="share"
data-liblib-overlay="agent"
data-liblib-overlay="canvas-dropdown"
data-liblib-overlay="add-node"
data-liblib-overlay="shortcuts"
data-liblib-overlay="zoom-menu"
```

The selector is a test/debug contract, not visible product copy.
