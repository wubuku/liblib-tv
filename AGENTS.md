<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# LibTV + FrameOS Canvas Clones

Two parallel pixel-perfect reverse-engineered canvas editors, each on its own route, sharing React Flow primitives:

- **`/` (liblib-tv)** — node-based video storyboarding editor from `liblib.tv/canvas`
- **`/frameos/*` (FrameOS)** — AI prompt + canvas editor from `frameos.cn`

> **Discovery hub**: [`docs/README.md`](docs/README.md). It indexes every doc so you can navigate progressively (elevator pitch → routes → behaviors → per-component specs).

---

## Red Lines — read before touching code

1. **xyflow v12 selected state is reset by `applyNodeChanges`** — every `onNodesChange` resets `selected: false` on all nodes. FrameOS re-applies the store's `selectedNodeId` in `onNodesChange` for this reason. See `src/app/frameos/canvas/[id]/page.tsx`. The liblib-tv route doesn't have this issue because the data shape is simpler.
2. **xyflow v12 does NOT pass `node.style` as a prop to custom node components.** It applies it directly to the outer transform layer. If you need width/height in a custom node, read from the Zustand store (the source of truth) or `props.measured`, never `props.style`. The `FrameosImageNode` portrait detection bug came from this.
3. **The `<Handle>` IS the "+" icon.** Never decorate a separate "+" overlay near a handle — it blocks the drag and breaks connection creation. The handle renders the "+" via CSS `::before` in `src/app/globals.css` `/* Node Handle */`. See [`docs/README.md` § "Key Design Decisions"](docs/README.md#key-design-decisions).
4. **Edge hover flow is analysis-driven, not guessed.** The 3-segment flowing pulse + glow filter was extracted from the live original site via Playwright. If you "improve" it without re-extracting, you will regress. See [`docs/research/components/DeletableEdge.spec.md`](docs/research/components/DeletableEdge.spec.md).
5. **NodeEditPanel is DEBUG-only.** It is NOT part of the original frameos.cn. It is gated behind `isDebugMode` (toggle in the bottom-right of the canvas). If the user asks "why is this panel here?", it was a developer convenience added without verifying the original.
6. **No `any`. TypeScript strict. Tailwind utility classes preferred; inline `style` allowed only for dynamic values (xyflow position calculations, viewport coords, conditional colors).** All inline-style usage is documented at the call site.
7. **Two routes, two stores, separate node systems.** `canvasStore` (liblib-tv) and `frameosStore` (FrameOS) are independent. They share React Flow primitives and the `DeletableEdge` component, but their state shapes and node types differ. Do not unify them with a "mode" flag.
8. **Worktree isolation for parallel agents.** When launching agent teams, each teammate works in its own worktree branch. Merge at the end, resolving conflicts with full project context.
9. **Sync scripts after editing shared rules.** After editing `AGENTS.md`, run `bash scripts/sync-agent-rules.sh`. After editing `.claude/skills/clone-website/SKILL.md`, run `node scripts/sync-skills.mjs`.

---

## Commands

```bash
npm run dev        # localhost:3000 — main canvas editor (liblib-tv clone)
npm run build      # production build
npm run check      # lint + typecheck + build

# FrameOS canvas:  http://localhost:3000/frameos/canvas/demo
# Entry link:      homepage → top-right "FrameOS" pill
```

## Stack (one-line)

Next.js 16 (App Router, React 19, TS strict) · Tailwind v4 (`@theme inline`) · React Flow v12 (`@xyflow/react`) · Zustand (`canvasStore`, `uiStore`, `frameosStore`) · `@base-ui/react/tooltip` · inline SVG (no icon library) · DevTools: `window.__frameos_store` exposes the FrameOS store for e2e.

---

@docs/research/INSPECTION_GUIDE.md
