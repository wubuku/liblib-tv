# Quality Standards

## TypeScript And React

- TypeScript strict is mandatory; `any` is prohibited.
- Use existing local types and helpers before inventing new abstractions.
- Keep props and store data explicit; do not hide route differences behind broad unions.
- Use Tailwind utility classes for static styling. Inline styles are for dynamic viewport coordinates, zoom math or conditional runtime values, and must have a nearby comment when non-obvious.

## React Flow Safety

- xyflow v12 does not pass `node.style` through custom node props. Read dimensions from the store or `props.measured`.
- `applyNodeChanges` resets selected flags. FrameOS must restore the selected node from `selectedNodeId`.
- `<Handle>` is the connection affordance. Do not place decorative plus elements over it.
- Node-anchored floating UI must follow the node's actual screen geometry, not browser center or a stale store position.
- Parent-child nodes must use the correct absolute/relative coordinate model.

## Route Boundaries

- LibTV uses `canvasStore` + `uiStore`; FrameOS uses `frameosStore`.
- Do not add a `mode` switch that merges the two state systems.
- Shared CSS changes require visual checks on both `/` and `/frameos/canvas/demo`.
- `FrameosNodeEditPanel` is DEBUG-only and must not become user-facing source-site behavior.

## Evidence Discipline

Every reverse-engineering claim must be classified:

| Class | Meaning | Example |
|---|---|---|
| Source fact | directly observed in DOM, JSON, screenshot or interaction | panel width `660px` |
| Inference | derived from repeated source facts | panel is node-anchored |
| Clone decision | local implementation needed for a prototype | Lucide icon substitute |

- Prefer structured DOM/JSON measurements over visual guesses.
- Search `docs/research/` before reopening a screenshot.
- After first visual inspection, write a `SCREENSHOT_ANALYSIS.md` record.
- Preserve the source date, viewport, zoom and interaction state.
- Never turn a sampled product value into a permanent backend contract without evidence.

## Documentation Quality

- New formal docs must be linked from [`index.md`](index.md).
- New research must be linked from [`research/README.md`](research/README.md).
- Active plans belong in a named batch directory or `docs/drafts/`.
- Historical implementation records remain immutable in intent; append corrections instead of silently rewriting facts.
- Claims about current runtime behavior should point to code or a verification script.

## Security And Scope

- Never commit credentials, cookies, tokens or private browser state.
- Do not imply that local mock actions call a real generation or account service.
- Keep external source assets and reproduction decisions within the project's documented research scope.

## Review Gate

Before merging a change:

1. Read the route and component spec.
2. Run the narrowest behavior check.
3. Run `npm run check`.
4. Run `python3 scripts/verify-docs.py` when docs or links changed.
5. Update implementation history and commit message with the actual scope.
