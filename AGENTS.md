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
- [Canvas Navigation](docs/CANVAS_NAVIGATION.md)
- [Glossary](docs/GLOSSARY.md)
- [Research Index](docs/research/README.md)
- [Current Big Picture](docs/BIG_PICTURE.md)
- [Documentation Plan](docs/DOCUMENTATION_PLAN.md)
- [Agent Task Map](docs/AGENT_TASK_MAP.md)
- [Decision Register](docs/DECISION_REGISTER.md)
- [Clone Website Adaptation](docs/CLONE_WEBSITE_ADAPTATION.md)

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
| Jimeng route | `src/app/jimeng/` | Jimeng canvas route and page orchestration |
| Jimeng state | `src/store/jimengStore.ts` | independent Jimeng graph/UI mock |
| Jimeng components | `src/components/jimeng/` | Jimeng nodes, toolbars, panels |
| Jimeng research | `docs/research/jimeng-canvas/` | Jimeng source evidence and tokens |
| Shared utilities | `src/lib/`, `src/types/` | pure helpers and type contracts |
| Evidence | `docs/research/`, `docs/design-references/` | source observations and visual records |

## 5. Hard Constraints

- Read the relevant guide in `node_modules/next/dist/docs/` before changing Next.js APIs.
- Keep `canvasStore`, `frameosStore` and `jimengStore` separate; do not add a route `mode` flag.
- React Flow v12 does not pass `node.style` to custom node props; read store data or `props.measured`.
- `applyNodeChanges` resets selected state; FrameOS must re-apply `selectedNodeId` after changes.
- `<Handle>` is the real `+` connection affordance; never add a decorative overlay that blocks dragging.
- Current LibTV canvas navigation authority is `docs/CANVAS_NAVIGATION.md`; Batch 77
  source runtime evidence governs wheel/middle/`Space`/`H`/`V`/blank-drag behavior.
  Blank-drag stays no-op; marquee is Shift+drag (v12 `selectionOnDrag=false`),
  verifier-covered since Batch 362 (Batch 6 un-aged).
- Do not change the LibTV edge flow effect without re-extracting source evidence.
- `FrameosNodeEditPanel` is DEBUG-only and is not source-site functionality.
- Director `authoredObjects` is the portable authoring baseline; `objects` is its
  timeline/path runtime projection. Timeline sampling must start from authored
  state, while phone live preview remains runtime-only.
- TypeScript is strict; do not use `any`. Prefer Tailwind; document dynamic inline styles.
- Separate source fact, evidence-backed inference and clone-only decision in research docs.
- Before visual reinspection, search existing `SCREENSHOT_ANALYSIS.md` records.
- Source-site canvas exploration that needs real uploads must use the authorized
  test media in `docs/CANVAS_TEST_MEDIA.md`; uploading is allowed, but never
  trigger real video/image generation (paid, expensive) or enter billing pages
  without separate user confirmation.
- Director `TransformControls` must use explicit object attachment and read back the
  same Three.js object that was dragged; run Batch 77 after changing this path.

## 6. Change Protocol

1. Identify the route, store and component spec before editing.
2. Read the relevant architecture/behavior/research document.
3. Make the smallest scoped change.
4. Update the appropriate document when behavior or evidence changes.
5. Run the relevant Playwright script and `npm run check`.
6. For shared rules or skills, run the required sync script.

### 6.1 Committing in this shared master workspace

Several agents work in the same `master` working tree at the same time. Never
discard anyone else's edits and never use `git stash` — it yanks their work out
from under them.

**Never use `git commit -- <pathspec>` to isolate your commit.** It does *not*
commit the index; it commits the **current working-tree content** of those paths,
so it silently sweeps in whatever uncommitted work a parallel agent has in them.
This was actually done here once: a `git commit -- <paths>` intended to commit 10
small files also swallowed a parallel agent's ~240 lines of unrelated in-flight
work in two of them.

Correct sequence:

```bash
git add -- <only your paths>          # stage exactly your own files
git diff --cached --name-only         # verify the index, immediately before
git diff --cached --numstat           # per-file line counts: a number far
                                      # larger than your change means you
                                      # staged someone else's work
git commit                            # plain commit — commits the index
```

The `numstat` check is the one that catches it. A ring-shadow tweak should be
`3 5`; if you see `193 12`, stop and re-stage.

Recovery, if you already committed someone else's work and have **not** pushed:
`git reset --mixed HEAD~1` (restores their edits to the working tree, unstaged),
stage only your own hunks, then plain `git commit`. If you have already pushed,
do not rewrite shared history — leave it and tell them.

Other shared-workspace rules:

- A batch/section number is not reserved by asking; two agents will pick the same
  one. Put a topic suffix on any new verifier (`verify-jimeng-batchNNN-topic.py`)
  and re-check for collisions at the moment you create the file.
- Keep per-batch evidence in its own `docs/research/<topic>-batchNNN-<date>/`
  directory so concurrent batches cannot collide.
- The dev server on port 4317 is shared and gets restarted by other agents:
  require **3 consecutive HTTP 200s** before trusting a run.
- Cross-site geometry comparisons must normalize zoom first. Measure the
  `.react-flow__viewport` transform and divide by it, or the default ~73% zoom
  turns a 36px element into a phantom 26px "regression".

## 7. Documentation Maintenance

- New formal docs belong in `docs/` and must be linked from `docs/index.md`.
- New live research belongs in `docs/research/`; active plans belong in `docs/drafts/`.
- Current LibTV canvas input instructions belong in `docs/CANVAS_NAVIGATION.md`; update
  it when source-aligned navigation semantics change.
- Historical batch records remain traceable and must link back to their evidence.
- Edit `AGENTS.md`, then run `bash scripts/sync-agent-rules.sh`.
- Edit `.claude/skills/clone-website/SKILL.md`, then run `node scripts/sync-skills.mjs`.
