# Batch 47 Plan

## Goal

Complete a source-bounded Director model-library loop:

```text
open 模型库
  -> switch category tabs
  -> inspect proxy thumbnail cards
  -> add one item to the live scene
  -> verify tree selection, Inspector state and R3F pixels
  -> inspect 我的模型 empty state
```

## Value Choice

| Candidate | Current evidence | Existing foundation | Decision |
|---|---|---|---|
| model-library entry and category browser | upstream UI/tests + Batch 34 archaeology | viewport toolbar and serializable prop objects | implement |
| real FBX/OBJ model import | upstream loader only, unresolved external assets | no current loader or asset schema | defer |
| environment/panorama library | upstream import path + no current source contract | no environment state in clone | defer |
| remote asset persistence | no safe current contract | no provider boundary | defer |

## In Scope

- viewport toolbar `模型库` trigger;
- floating dialog with five source-shaped category tabs;
- clone-owned proxy catalog with card thumbnails and names;
- scrollable card grid and selected-item feedback;
- `我的模型` empty state with an explicit deferred local-import affordance;
- add-card transaction creating one serializable `prop` object;
- tree selection, Inspector name/transform continuity and visible R3F proxy;
- desktop/mobile panel bounds and outside-pointer close;
- stable selectors, focused Playwright verification and one screenshot ledger.

## Out Of Scope

- external FBX/OBJ/GLB files or copied upstream thumbnails;
- real environment/panorama authoring;
- remote library calls, persistence or provider claims;
- imported asset deletion and scene-instance cleanup;
- exact current LibTV panel geometry;
- full catalog completeness;
- undo/redo beyond the existing local graph boundary.

## Ordered Work

1. Protect current evidence, upstream archaeology and this plan.
2. Add a clone-owned proxy catalog and asset-to-prop mapping.
3. Add Director store action for adding a library prop.
4. Add viewport toolbar trigger, category dialog and card actions.
5. Add bounded proxy geometry and tree/Inspector continuity.
6. Add `scripts/verify-liblib-batch47.py`.
7. Inspect one generated contact sheet and immediately write the screenshot
   analysis ledger.
8. Run Batch 35-47 regression, docs check, `npm run check` and diff check.
9. Update maturity/stable docs, commit and push.

## Acceptance Gates

- `模型库` opens from the viewport toolbar;
- all five category tabs are discoverable and switch the card set;
- at least two proxy cards render in the active category;
- clicking a card adds exactly one new prop object and selects it;
- the object tree exposes the new object and the Inspector preserves its
  editable name/transform surface;
- the R3F canvas remains non-blank and changes pixels after insertion;
- `我的模型` shows its empty state without pretending local assets exist;
- outside pointer closes the panel;
- desktop/mobile panel bounds have no horizontal overflow;
- no console, page or failed-request errors.

## Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-model-library-trigger]` | toolbar entry |
| `[data-director-model-library-panel]` | floating dialog |
| `[data-director-model-library-tab]` | category tab |
| `[data-director-model-library-card]` | proxy model card |
| `[data-director-model-library-empty]` | `我的模型` empty state |
| `[data-director-model-library-add]` | add-card command |
| `[data-director-model-library-asset-id]` | stable proxy asset ID |
