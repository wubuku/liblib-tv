# Development Guide

## Prerequisites

- Node.js 24+
- npm
- Chromium-capable browser for visual exploration
- Python 3 for the repository's synchronous Playwright verification scripts
- Existing local login session when inspecting the authenticated LibTV source

Install dependencies:

```bash
npm install
```

## Run The Prototype

```bash
npm run dev
```

| URL | Use |
|---|---|
| `http://localhost:3000` | LibTV clone |
| `http://localhost:3000/frameos/canvas/demo` | FrameOS clone |

The dev server is usually left running while Playwright scripts execute. Use another port only when port 3000 is already occupied by an unrelated server.

## Standard Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Next.js development server |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript strict check |
| `npm run build` | production build |
| `npm run check` | lint + typecheck + build |
| `npm run docs:check` | local Markdown link check |

## Code Navigation

### LibTV Change

1. Read [`ARCHITECTURE.md`](ARCHITECTURE.md), [`BIG_PICTURE.md`](BIG_PICTURE.md) and the relevant component spec.
2. Confirm whether state belongs in `canvasStore`, `uiStore` or local component state.
3. Modify the smallest route-specific component set.
4. Add or update a stable selector when browser verification needs to measure a new state.
5. Run the narrowest `scripts/verify-liblib-batch*.py` script, then `npm run check`.
6. Update the relevant batch implementation record.

### FrameOS Change

1. Read [`research/frameos/IMPLEMENTATION.md`](research/frameos/IMPLEMENTATION.md) and [`research/frameos/RUNBOOK.md`](research/frameos/RUNBOOK.md).
2. Keep `frameosStore`, FrameOS nodes and `frameos-canvas.css` isolated.
3. For selection changes, account for xyflow v12 selected-state reset.
4. Use `window.__frameos_store` for browser diagnostics when useful.
5. Run the available local route checks and `npm run check`.

## Adding A LibTV Node

1. Add the renderer in `src/components/nodes/`.
2. Register it in `src/app/page.tsx`.
3. Add its default data/dimensions in `src/store/canvasStore.ts`.
4. Add the entry in `src/components/AddNodePanel.tsx` if user-facing.
5. Add `docs/research/components/<Node>.spec.md`.
6. Add a focused browser verification script if behavior is non-trivial.

## Adding A FrameOS Node

1. Add the type in `src/types/frameos.ts`.
2. Add the store case in `src/store/frameosStore.ts`.
3. Build the renderer with `FrameosNodeShell`.
4. Register it in the FrameOS page `nodeTypes`.
5. Add it to `FrameosToolRail.tsx`.
6. Document its states and route behavior in `docs/research/frameos/`.

## Source-Site Exploration

The project uses a staged evidence workflow:

1. Search `docs/research/` for existing source audits and screenshot ledgers.
2. Inspect the smallest missing browser state; do not repeat full screenshot recognition.
3. Record viewport, interaction state, DOM facts, geometry, behavior and uncertainty.
4. Separate source fact, inference and clone decision.
5. Implement only after the evidence record is discoverable.

Read [`research/INSPECTION_GUIDE.md`](research/INSPECTION_GUIDE.md) and the local [`clone-website` skill](../.codex/skills/clone-website/SKILL.md) for the full extraction protocol.

## Browser Verification

The LibTV batch scripts use independent pages when state contamination is possible. Run the narrowest script for the change; the complete script-backed range is maintained in [`HARNESS.md`](HARNESS.md):

```bash
python3 scripts/verify-liblib-batch<N>.py
```

当前专项 verifier 覆盖 Batch 4-33、35-44；Batch 34 是研究批次，Batch 45 是当前并行研究/实现 WIP，均不代表已经有专项回归脚本。

They check DOM geometry, interaction lifecycle, screenshots and console errors. Treat the corresponding `docs/design-references/` images as dated evidence, not as an automatically current screenshot.

## Shared Rule Maintenance

- Edit `AGENTS.md`, then run `bash scripts/sync-agent-rules.sh`.
- Edit `.claude/skills/clone-website/SKILL.md`, then run `node scripts/sync-skills.mjs`.
- The portable `project-docs` skill lives at `.agents/skills/project-docs/`; keep its references self-contained.
