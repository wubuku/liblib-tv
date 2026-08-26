# Director Model Library Specification

## Evidence Classification

| Contract | Basis |
|---|---|
| `模型库` viewport entry | fixed upstream toolbar/tests |
| five category tabs | fixed upstream catalog and screenshot ledger |
| floating card grid and outside close | fixed upstream CSS/tests |
| `我的模型` empty state | fixed upstream toolbar/tests |
| proxy item names, count and visuals | clone calibration |
| add-card creates a scene prop | upstream store boundary adapted to clone store |
| exact source geometry and real model files | not claimed |

## Catalog Contract

The clone exposes a bounded local descriptor:

```ts
interface DirectorModelLibraryItem {
  id: string;
  categoryId: "convenience" | "home" | "outdoor" | "tools";
  name: string;
  visual: "bottle" | "chair" | "lamp" | "plant" | "box";
  color: string;
}
```

The catalog is intentionally incomplete. It demonstrates category browsing
and scene insertion without shipping external model files.

## Interaction Contract

- clicking `模型库` opens the floating panel and closes other viewport menus;
- exactly one category is active at a time;
- active cards are scrollable and have stable accessible names;
- clicking a card adds one prop object, closes the panel and selects the object;
- `我的模型` renders `暂无任何模型` and does not imply a local file exists;
- clicking outside the toolbar/panel closes the panel;
- mobile uses the same anchored panel with measured document bounds.

## Scene Contract

- added items are ordinary serializable `DirectorObject` props;
- each proxy stores its library asset ID and visual descriptor;
- added objects use deterministic placement beside the existing scene;
- the object tree and Inspector route through the existing prop selection
  behavior;
- no remote asset URL or provider metadata is stored.
