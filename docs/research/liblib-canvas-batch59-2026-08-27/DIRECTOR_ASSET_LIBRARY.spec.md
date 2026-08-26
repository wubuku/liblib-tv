# Director Asset Library Specification

## Evidence Classification

| Contract | Basis |
|---|---|
| Director asset library is a bounded clone surface | existing clone architecture |
| category vocabulary `模型 / 环境 / 我的模型` | clone/upstream-derived contract, not current authenticated source fact |
| query, preview and add-object states | this batch clone decision |
| serializable asset identity and proxy insertion | existing `directorModelLibrary` and `directorStore` |
| exact dimensions, thumbnails and remote persistence | unknown / clone calibration |

## Domain Contract

```ts
interface DirectorAssetLibraryQuery {
  category: DirectorModelLibraryCategoryId;
  search: string;
}

interface DirectorAssetLibrarySelection {
  assetId: string | null;
  categoryId: DirectorModelLibraryCategoryId | null;
}
```

The catalog item remains distinct from the scene object. Adding the same item
twice creates two object IDs, while both objects retain the same
`libraryAssetId`.

## Interaction Contract

- opening the library owns a Director-local surface;
- category buttons replace the visible result set;
- search is case-insensitive and trims query whitespace;
- empty results render a stable empty state;
- selecting a card changes preview selection only;
- preview can be closed without changing scene objects;
- add creates one serializable proxy object and selects it in the object tree;
- existing Inspector edits remain available after insertion;
- library state is local to the Director session and does not enter canvas graph
  history.

## Visual/Responsive Boundary

- use the existing Director dark shell, rail and Inspector tokens;
- keep cards compact and scan-friendly;
- on compact viewports, the library is inside the existing Inspector drawer;
- do not create a second nested full-screen card or introduce remote asset
  loading;
- exact source spacing remains unclaimed until authenticated source evidence is
  available.

