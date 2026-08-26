# LibTV + FrameOS Canvas Clones — Agent Navigation

## 1. Project Overview

- Type: reverse-engineered frontend prototype for two AI canvas editors.
- Routes: `/` = LibTV; `/frameos/*` = FrameOS.
- Stack: Next.js 16 App Router, React 19, TypeScript strict, React Flow 12, Zustand, Tailwind 4.
- Status: active research and UI/UX prototype; backend services are not implemented.

## 2. Documentation Index

- [Documentation Hub](docs/index.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
- [Layer Rules](docs/LAYERS.md)
- [Quality Rules](docs/QUALITY.md)
- [Verification Harness](docs/HARNESS.md)
- [Glossary](docs/GLOSSARY.md)
- [Research Index](docs/research/README.md)
- [Current Big Picture](docs/BIG_PICTURE.md)
- [Documentation Plan](docs/DOCUMENTATION_PLAN.md)
- [Agent Task Map](docs/AGENT_TASK_MAP.md)
- [Decision Register](docs/DECISION_REGISTER.md)

## 3. Quick Commands

```bash
npm run dev
npm run lint
npm run typecheck
npm run build
npm run check
python3 scripts/verify-docs.py
```

## 4. Module Map

| Area | Path | Responsibility |
|---|---|---|
| LibTV route | `src/app/page.tsx` | React Flow page orchestration |
| LibTV state | `src/store/canvasStore.ts`, `uiStore.ts` | graph, canvases, selection, UI |
| LibTV components | `src/components/`, `src/components/nodes/` | nodes, panels, dialogs, overlays |
| FrameOS route | `src/app/frameos/` | independent route and page orchestration |
| FrameOS state | `src/store/frameosStore.ts` | independent graph/UI/history mock |
| Shared utilities | `src/lib/`, `src/types/` | pure helpers and type contracts |
| Evidence | `docs/research/`, `docs/design-references/` | source observations and visual records |

## 5. Hard Constraints

- Read the relevant guide in `node_modules/next/dist/docs/` before changing Next.js APIs.
- Keep `canvasStore` and `frameosStore` separate; do not add a route `mode` flag.
- React Flow v12 does not pass `node.style` to custom node props; read store data or `props.measured`.
- `applyNodeChanges` resets selected state; FrameOS must re-apply `selectedNodeId` after changes.
- `<Handle>` is the real `+` connection affordance; never add a decorative overlay that blocks dragging.
- Do not change the LibTV edge flow effect without re-extracting source evidence.
- `FrameosNodeEditPanel` is DEBUG-only and is not source-site functionality.
- TypeScript is strict; do not use `any`. Prefer Tailwind; document dynamic inline styles.
- Separate source fact, evidence-backed inference and clone-only decision in research docs.
- Before visual reinspection, search existing `SCREENSHOT_ANALYSIS.md` records.

## 6. Change Protocol

1. Identify the route, store and component spec before editing.
2. Read the relevant architecture/behavior/research document.
3. Make the smallest scoped change.
4. Update the appropriate document when behavior or evidence changes.
5. Run the relevant Playwright script and `npm run check`.
6. For shared rules or skills, run the required sync script.

## 7. Documentation Maintenance

- New formal docs belong in `docs/` and must be linked from `docs/index.md`.
- New live research belongs in `docs/research/`; active plans belong in `docs/drafts/`.
- Historical batch records remain traceable and must link back to their evidence.
- Edit `AGENTS.md`, then run `bash scripts/sync-agent-rules.sh`.
- Edit `.claude/skills/clone-website/SKILL.md`, then run `node scripts/sync-skills.mjs`.
