# Verification Harness

## Standard Sequence

```text
focused browser check -> lint -> typecheck -> build -> docs link check
```

The repository does not currently have a single `npm test` suite. The source canvas checks are executable Python Playwright scripts, while the production gate is `npm run check`.

## Command Matrix

| Step | Command | Pass criteria |
|---|---|---|
| Docs | `npm run docs:check` | no missing local Markdown/image links |
| Lint | `npm run lint` | exit 0; existing warnings are reported |
| Typecheck | `npm run typecheck` | `tsc --noEmit` exit 0 |
| Build | `npm run build` | Next production build succeeds |
| Full gate | `npm run check` | lint + typecheck + build all succeed |
| LibTV behavior | `python3 scripts/verify-liblib-batch4.py` ... `batch32.py` | script-specific assertions and no console errors |

## LibTV Batch Coverage

| Script | Contract |
|---|---|
| Batch 4 | grouping, ungrouping, delete/undo, mobile overflow |
| Batch 5 | multi-drag, transactional undo/redo, duplicate selection |
| Batch 6 | marquee selection, H/V tools, Space pan, input guard |
| Batch 7 | source-like organize topology, confirmation, restore/keep |
| Batch 8 | video group parent-child hierarchy, copy and cascade delete |
| Batch 9 | selected-node overlays, anchor geometry, pan/zoom and clipping |
| Batch 10 | five image editor states, Prompt, references, controls and AutoLink |
| Batch 11 | top-level overlay exclusivity, Escape cleanup, mode lifecycle and mobile overflow |
| Batch 12 | asset manager canvas/assets tabs, media filtering and node selection |
| Batch 13 | storyboard mode key-elements rail, canvas data binding and card selection |
| Batch 14 | Agent drawer Skill cards, notification/composer states and share feedback |
| Batch 15 | add-node entry semantics, audio node creation and material submenu |
| Batch 16 | project metadata, canvas CRUD lifecycle, menu cleanup and active-canvas check |
| Batch 17 | asset drawer context, source-order node tree, browse controls and active-canvas empty states |
| Batch 18 | source-shaped zoom menu, viewport commands, Escape/outside cleanup and overlay mutual exclusion |
| Batch 19 | minimap source anchor, fit-view outline update, asset-drawer follow and mobile toolbar avoidance |
| Batch 20 | 720° panorama node/edge transaction, placeholder, specialized panel, geometry and responsive clipping |
| Batch 21 | Seedance normal/long parameter dialog geometry, controls, mode matrix and `300s / 14700` |
| Batch 22 | Seedance source-visible model menu geometry, seven-row matrix, premium hierarchy and selected descriptions |
| Batch 23 | Seedance segment-reshoot filmstrip/editor layers, range cap, prompt tokens and whole-rerun semantics |
| Batch 24 | shot-breakdown result graph transaction, dimension filtering, output groups and responsive bounds |
| Batch 25 | video-clip empty node, single-column modes, node-anchored editor and responsive clipping |
| Batch 26 | smart-continuation selector, range manipulation, target/edge lifecycle, clear and undo/redo |
| Batch 27 | smart/region subtitle erase, rectangle history, request metadata and pending target graph |
| Batch 28 | current audio-split menu/busy state, dual-output graph, metadata, direct source edges and undo/redo |
| Batch 29 | top/player frame-capture entries, first/last/current metadata, source-linked image graph, overlap slots and undo/redo |
| Batch 30 | subject-edit menu correction, hover timing, duration guards, smart-matting panel, pending video graph and undo/redo |
| Batch 31 | subject remove/modify/replace marking editor, mode validation, pending edit graph and undo/redo |
| Batch 32 | depth motion guard, node-anchored panel, resolution/busy state, pending graph and undo/redo |

Run them serially because they use the same local dev server and write dated visual references:

```bash
for script in scripts/verify-liblib-batch{4..32}.py; do
  python3 "$script" || exit 1
done
```

## Browser Evidence Requirements

When adding a browser-verified behavior:

- use stable `data-*` selectors for measured regions;
- collect console errors and page errors;
- isolate pages when prior interactions can create derived nodes or alter selection;
- save screenshots in `docs/design-references/`;
- record screenshot interpretation in the batch `SCREENSHOT_ANALYSIS.md`;
- state what is direct evidence, inference and clone-only behavior.

The screenshot ledger rule is important: do not spend visual recognition budget re-opening a full screenshot when a written record already answers the question.

## FrameOS Checks

The FrameOS route can be tested manually at `/frameos/canvas/demo`. Its older `e2e/frameos.spec.ts` describes intended interactions but is not part of the default npm scripts and may require Playwright test dependencies. Do not claim it passed unless it has actually been run.

Use the browser console diagnostic:

```js
window.__frameos_store.getState()
```

Selection, prompt, history and debug-mode behavior are documented in [`research/frameos/RUNBOOK.md`](research/frameos/RUNBOOK.md).

## Documentation Check

`scripts/verify-docs.py` scans tracked Markdown files, resolves local relative links and skips external URLs and anchors. It is intentionally small and dependency-free so agents can run it before the JavaScript toolchain.

## Post-Change Checklist

- [ ] Relevant source evidence or existing spec read
- [ ] Focused browser behavior verified
- [ ] Console error count is zero for the tested flow
- [ ] `npm run check` passes
- [ ] Documentation and screenshot ledger updated
- [ ] New formal docs linked from `docs/index.md`
