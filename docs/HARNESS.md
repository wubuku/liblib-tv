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
| LibTV behavior | `python3 scripts/verify-liblib-batch4.py` ... `batch11.py` | script-specific assertions and no console errors |

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

Run them serially because they use the same local dev server and write dated visual references:

```bash
for script in scripts/verify-liblib-batch{4..13}.py; do
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
