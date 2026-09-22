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

The project development server intentionally uses the fixed port `4317`. This
keeps local verification away from the commonly occupied `3000`/`3001` ports
and prevents accidentally testing an unrelated or stale server. `next dev`
still accepts an explicit `--port` override when a separate environment
requires it; update `LIBLIB_BASE_URL` for verifier commands in that case.

| URL | Use |
|---|---|
| `http://localhost:4317` | LibTV clone |
| `http://localhost:4317/frameos/canvas/demo` | FrameOS clone |

The dev server is usually left running while Playwright scripts execute. Do not
reuse `3000` or `3001` for routine local work; use an explicit alternate port
only when `4317` is occupied.

### One-command restart

When an old Next.js dev process is still holding the port, use the restart
wrapper. It only terminates listeners that can be traced back to this project;
an unrelated process is reported and left untouched.

```bash
# Restart the default project port.
npm run dev:restart

# Use a less common port for this session.
npm run dev:restart -- 4387
npm run dev:restart -- --port 4387
DEV_PORT=4387 npm run dev:restart
```

When using a non-default port, point browser verifiers at the same origin:

```bash
LIBLIB_BASE_URL=http://localhost:4387 python3 scripts/verify-liblib-batch<N>.py
```

### When a canvas suddenly appears non-interactive

A listening port or an HTTP `200` response does not prove that the current
browser page has a healthy React/React Flow runtime. A stale Next.js child
process, a half-updated HMR page, or an old browser context can leave the shell
visible while nodes or event handlers are missing. Use this order before
changing canvas code:

1. Restart only this project's server:

   ```bash
   npm run dev:restart
   ```

2. Confirm the listener belongs to this checkout:

   ```bash
   lsof -nP -iTCP:4317 -sTCP:LISTEN
   ps -axo pid,ppid,lstart,command | rg 'next (dev|server)|next-server'
   ```

   `scripts/restart-dev.sh` refuses to kill an unrelated process that owns the
   port. Choose another port instead of killing an unknown listener.

3. Open a **new browser context** at `http://localhost:4317`, not only a
   previously open tab. Use the same `localhost` origin for HMR and verifier
   runs; switching between `localhost` and `127.0.0.1` can introduce a
   development-only HMR cross-origin warning.

4. Check runtime consistency in the browser before diagnosing a regression:

   - LibTV: `.react-flow__node` and `.react-flow__edge` should agree with
     `window.__libtv_store.getState().getActiveCanvas()`.
   - FrameOS: `.react-flow__node` and `.react-flow__edge` should agree with
     `window.__frameos_store.getState().nodes` and `.edges`.
   - A page with only the shell, toolbar, or dot grid is not a passing canvas.

5. Run the route-specific interaction gates:

   ```bash
   LIBLIB_BASE_URL=http://localhost:4317 \
     python3 scripts/verify-liblib-batch77.py
   LIBLIB_BASE_URL=http://localhost:4317 \
     python3 scripts/verify-frameos-batch157.py
   ```

   These gates use real Playwright input. Batch 77 checks LibTV pan, zoom,
   selection, `H`/`V`/`Space`, mobile overflow, and Director pointer behavior;
   Batch 157 checks FrameOS node rendering, context menus, duplicate/add,
   undo, and Escape dismissal.

This incident was reproduced once with an old server/browser state and did not
reproduce after a fresh project-owned restart and fresh browser context. The
2026-09-22 checkpoint passed both route gates with no page, console, or request
errors. Do not label this class of symptom a code regression until the fresh
context and route gates fail.

## Standard Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Next.js development server |
| `npm run dev:restart` | Stop this project's stale dev server and start a fresh one |
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

当前专项 verifier 覆盖 Batch 4-33、35-50、52-65、67-69（中间无脚本的 batch
除外）。Batch 67 是不需要 dev server 的 Director V1 pure codec gate；Batch 68
组合 pure registry 与 browser owner/session gate；Batch 69 组合 pure static
projection gate 与 browser authored/runtime gate。Batch 34 是 research-only，
Batch 66 是 authority/governance 批次，两者都不应被隐式纳入脚本循环。当前
Director reliability batch 至少运行：

```bash
python3 scripts/verify-liblib-batch67.py
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch68.py
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch69.py
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch59.py
```

They check DOM geometry, interaction lifecycle, screenshots and console errors. Treat the corresponding `docs/design-references/` images as dated evidence, not as an automatically current screenshot.

## Shared Rule Maintenance

- Edit `AGENTS.md`, then run `bash scripts/sync-agent-rules.sh`.
- Edit `.claude/skills/clone-website/SKILL.md`, then run `node scripts/sync-skills.mjs`.
- The portable `project-docs` skill lives at `.agents/skills/project-docs/`; keep its references self-contained.
