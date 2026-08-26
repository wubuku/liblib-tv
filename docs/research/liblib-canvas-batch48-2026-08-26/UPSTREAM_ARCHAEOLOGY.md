# Batch 48 Upstream Archaeology

## Relevant Files

| File | Borrowable fact |
|---|---|
| `src/editor/loaders/localModelImport.ts` | `.fbx`/`.obj` gate and browser data-URL read |
| `src/editor/canvas/ViewportToolbar.tsx` | multiple-file input, `我的模型` projection, add/delete actions |
| `src/editor/store/directorStore.ts` | local asset persistence, restore, removal and scene-object creation |
| `src/editor/schema/directorProject.ts` | serializable asset reference and object-to-asset link |
| `src/editor/canvas/ViewportToolbar.test.tsx` | import, refresh, add and delete interaction contracts |

## Data Flow

```text
file input
  -> extension gate
  -> data URL
  -> local model collection
  -> browser storage
  -> 我的模型 card
  -> add object from asset
  -> delete asset + linked scene instances
```

## Portability Decision

Port:

- the multiple-file local-import affordance;
- the populated/empty `我的模型` state transition;
- persistence and refresh recovery;
- card-to-scene and delete cleanup semantics.

Adapt:

- use the current clone's independent `directorStore`;
- keep a `DirectorLocalModelLibraryItem` collection separate from the fixed
  catalog descriptors;
- map imported file names to an owned proxy visual so the R3F scene changes;
- use a clone-owned storage key and defensive parsing.

Do not port directly:

- the upstream external `模型库/` asset glob;
- external model URLs or thumbnails;
- an unverified loader dependency;
- upstream store names or project schema wholesale.
