# Asset Manager Context and Tree Specification

## Scope

- **Target files:** `src/components/AssetManagerPanel.tsx`, `src/components/TopNavBar.tsx`
- **State source:** `canvasStore` project/canvas graph; `uiStore` overlay lifecycle
- **Prior contract:** Batch 12 canvas/assets tabs and node selection remain valid

## Source-shaped shell

```text
[LibTV mark lives in TopNavBar]
[project name] | [active canvas name v]
--------------------------------------
[画布] [资产]                 [close]
--------------------------------------
画布元素 [sort]        [全部 v] [search]

top-level node
group node
  child node

共 N 节点
```

When the drawer is open, the top mode controls move to the right of the 240px drawer and the duplicate top canvas button is hidden.

## Tree contract

- Top-level rows are nodes without `parentId`.
- Direct children render immediately after their parent with `data-asset-manager-depth="1"`.
- Asset-tab media nodes whose parent group is filtered out render at depth 0.
- Selection still calls `canvasStore.selectNode`.

## Local browse controls

| Control | Behavior |
|---|---|
| Sort | Toggle graph order / label order |
| Type filter | `全部`, `图片`, `视频`, `文本`, `分组` |
| Search | Case-insensitive substring match on `nodeLabel` |
| Clear search | Restore current filter result |

These behaviors are clone-only decisions inferred from source-visible controls; they do not represent a remote search API.

## Stable selectors

- `[data-asset-manager-context]`
- `[data-asset-manager-project]`
- `[data-asset-manager-canvas]`
- `[data-asset-manager-heading]`
- `[data-asset-manager-sort]`
- `[data-asset-manager-filter]`
- `[data-asset-manager-filter-option="<filter>"]`
- `[data-asset-manager-search]`
- `[data-asset-manager-search-input]`
- `[data-asset-manager-item="<node-id>"]`
- `[data-asset-manager-depth="0|1"]`
- `[data-asset-manager-empty]`

## Non-goals

- No account asset inventory.
- No recursive group editor beyond the current one-level source graph.
- No backend sort/search persistence.
