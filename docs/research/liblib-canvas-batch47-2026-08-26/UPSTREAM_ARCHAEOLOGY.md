# Batch 47 Upstream Archaeology

## Fixed Checkout

```text
research/upstream/storyai-3d-director-desk
commit 8c8bd361790be4d37158a7430365e65546e358fe
```

## Relevant Files

| File | Borrowable fact |
|---|---|
| `src/editor/canvas/ViewportToolbar.tsx` | trigger, outside-pointer close, category tabs, cards and add-to-scene action |
| `src/editor/modelLibrary/modelLibraryCatalog.ts` | five categories and catalog item shape |
| `src/editor/store/directorStore.ts` | asset references and scene-object creation boundary |
| `src/styles/index.css` | frosted floating panel, five-tab underline, six-column card grid |
| `src/editor/canvas/ViewportToolbar.test.tsx` | open/close, category switching, add card and empty-state interaction contracts |

## Upstream UI Contract

The panel is a floating dialog attached above the viewport toolbar. Its
interaction hierarchy is:

```text
模型库
  -> 便利生活 / 居家生活 / 户外出行 / 工具配件 / 我的模型
  -> 66px thumbnail cards in a six-column scrollable grid
  -> click card to add the selected model to the scene
```

`我的模型` has a centered empty state with `暂无任何模型` and a local import
action when there are no imported assets.

## Upstream Data Boundary

The catalog item shape includes:

```ts
{
  categoryId,
  fileName,
  id,
  name,
  thumbUrl?,
  url
}
```

The fixed checkout obtains the actual model and thumbnail URLs from an
external sibling `模型库/` directory using Vite glob imports. That directory
is absent from the self-contained submodule checkout and its asset rights are
separate from the repository's MIT code license.

## Adaptation Decision

Borrow the panel hierarchy, category vocabulary, card density and add-to-scene
event shape. Replace external model URLs with a small clone-owned catalog of
proxy descriptors. Map each descriptor to an existing or newly bounded R3F
proxy primitive so the scene transaction is visible and testable without
claiming model-file parity.
