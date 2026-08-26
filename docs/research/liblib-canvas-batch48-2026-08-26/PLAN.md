# Batch 48 Plan

## Status

Plan/evidence protection prepared on 2026-08-26. Implementation starts after
this context-protection commit.

## Goal

Close the highest-value Batch 47 gap:

```text
我的模型 empty
  -> choose one or more FBX/OBJ files
  -> persist local descriptors
  -> browse cards after import and refresh
  -> add a local card to the live R3F scene
  -> remove the card and its scene instances
```

## Value Choice

| Candidate | Evidence | Existing foundation | Decision |
|---|---|---|---|
| local model import/list/re-add/delete | fixed upstream code/tests | Batch 47 model panel and proxy objects | implement |
| real FBX/OBJ parsing and mesh loading | not present in current clone; assets unresolved | no loader/runtime contract | defer |
| remote model library | no provider/API evidence | no remote asset boundary | defer |
| environment library | separate rendering/schema contract | no environment library state | defer |

## In Scope

- enabled `本地导入` action inside `我的模型`;
- multiple `.fbx`/`.obj` file selection;
- browser-local serialized model descriptors;
- populated local cards with filename/name and stable asset ID;
- refresh recovery of local cards;
- add local card to scene through the existing serializable prop boundary;
- delete local card and linked local scene instances;
- empty/populated states, outside/Escape behavior, stable selectors and
  desktop/mobile bounds;
- one generated screenshot contact sheet and written visual analysis.

## Out Of Scope

- parsing or rendering the uploaded FBX/OBJ bytes;
- copying upstream model files or thumbnails;
- remote uploads, sync, user accounts or cloud storage;
- environment/panorama imports;
- local-model preview thumbnails generated from 3D;
- claims about current LibTV's persistence implementation.

## Acceptance Gates

- `我的模型` exposes an enabled local-import action;
- multiple valid files create local cards without adding scene objects yet;
- invalid extensions do not create cards or console/page errors;
- local cards survive a page refresh;
- clicking a local card adds exactly one selected local proxy prop;
- deleting a local card removes its linked scene instances and returns to the
  empty state when it was the last local model;
- local storage contains only the bounded local model descriptors;
- desktop/mobile panel bounds have no horizontal overflow;
- focused Playwright and Batch 35-48 regression pass.

## Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-model-library-local-input]` | multiple local file input |
| `[data-director-model-library-import]` | local import command |
| `[data-director-model-library-local-card]` | populated local card |
| `[data-director-model-library-local-delete]` | local card deletion |
| `[data-director-model-library-local-file-name]` | source filename metadata |
| `[data-director-model-library-local-asset-id]` | stable local asset ID |

## Ordered Work

1. Protect this evidence, plan and contract.
2. Add local descriptor types, defensive storage and store actions.
3. Add the multiple-file input and populated local-card branch.
4. Add proxy insertion and delete cleanup.
5. Add focused Playwright, screenshot capture and one-time visual ledger.
6. Run Batch 35-48, docs check, `npm run check` and diff check.
7. Record maturity limits and commit/push.
