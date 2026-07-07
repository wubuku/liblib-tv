<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# LibTV Canvas Clone

Reverse-engineered clone of `liblib.tv/canvas` (a node-based video storyboarding editor) plus a parallel FrameOS canvas route. Built on the `clone-website` template scaffold.

> **Start here**: [`docs/README.md`](docs/README.md) — the discovery hub. It indexes every important doc so you can navigate progressively (elevator pitch → tech stack → behaviors → per-component specs).

---

## Red Lines — read before touching code

These are rules that have caused real bugs in this project. They are short on purpose; the "why" lives in the docs they point to.

1. **The `<Handle>` IS the "+" icon.** Never decorate a separate "+" overlay near a handle — it blocks the drag and breaks connection creation. The handle renders the "+" via CSS `::before` in `src/app/globals.css` `/* Node Handle */`. See [`docs/README.md` § "Key Design Decisions" § 1](docs/README.md#key-design-decisions).
2. **Edge hover flow is analysis-driven, not guessed.** The 3-segment flowing pulse + glow filter was extracted from the live original site via Playwright. If you "improve" it without re-extracting, you will regress. See [`docs/research/components/DeletableEdge.spec.md`](docs/research/components/DeletableEdge.spec.md).
3. **Pixel-perfect matching comes from DOM extraction, not visual guessing.** Use Playwright to query computed styles / DOM from the live target site. Save raw output into spec files rather than reconstructed summaries.
4. **Worktree isolation for parallel agents.** When launching agent teams, each teammate works in its own worktree branch. Merge at the end, resolving conflicts with full project context.
5. **No `any`. TypeScript strict. Tailwind utility classes, no inline styles** (the rare inline `style` exception is documented inline where it occurs).
6. **Sync scripts after editing shared rules.** After editing `AGENTS.md`, run `bash scripts/sync-agent-rules.sh`. After editing `.claude/skills/clone-website/SKILL.md`, run `node scripts/sync-skills.mjs`.

---

## Commands

```bash
npm run dev        # localhost:3000 — main canvas editor (liblib-tv clone)
npm run build      # production build
npm run check      # lint + typecheck + build
# FrameOS canvas: localhost:3000/frameos/canvas/demo
```

## Stack (one-line)

Next.js 16 (App Router, React 19, TS strict) · Tailwind v4 (`@theme inline`) · React Flow (`@xyflow/react`) · Zustand (`canvasStore`, `uiStore`, `frameosStore`) · `@base-ui/react/tooltip` · inline SVG (no icon library).

---

@docs/research/INSPECTION_GUIDE.md