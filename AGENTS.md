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
- Director framing aspect ratio (`frameAspectRatio` in `directorStore`: six source
  ratios plus `null` = auto) changes the **camera framing box only**; the canvas
  container stays fixed (source evidence, Batch 860 — this reversed Batch 859's
  D11). `null` means **no framing box at all**. It is a *different* state from the
  export/capture aspect (`aspectRatio`, three values, consumed by
  `directorVideoExport.ts` / `directorProjectDocument.ts` /
  `libtvMediaDimensionAuthority.ts`) — do not mix them.
- Director「全景图」panel rows (Batch 861): the source site opens a **hidden file
  input** for「本地上传」(verbatim `et.current?.click()`), and both「历史记录」and
  「AI生成」open the **same** picker (the AI row adds「生成」「上传图片」).
  The clone's local panorama uses a **session-scoped blob URL** — it uploads
  nothing — and the「生成」entry **must never** call a real generation API
  (real image generation costs money); `verify-liblib-batch861.py` fails the
  build if a network call appears in the picker source.
- The camera framing box's **composition-reference toggle** lives **on the box's
  top-right corner**, not in the viewport bottom toolbar (Batch 862, source
  verbatim `mP`: `style:{left:u.left+u.width-40, top:u.top+8}`, `title`＝
  「构图参考线」, 32×32). It exists **only while the box exists** (source:
  `onToggleCompositionGrid:null!==tr?…:void 0`), so "auto" (`null`) shows
  neither box nor toggle. Frame outline is `outline` (white 18%, 1px, −1px
  offset, radius 12px) — not `border` — and the thirds are white **50%**.
  The bottom-toolbar entry (`aria-label="开启九宫格辅助线"`) is a **clone
  extension** (D19); keep both pointing at the same `showThirds` state.
- ~~The source writes the framing ratio and the reference-line flag **onto the
  camera object** (`aspect_ratio` / `reference_line`, selected camera first,
  otherwise the first camera). The clone does **not** do that yet (D17) — the
  global `frameAspectRatio` is a single scene-wide value (that part matches the
  source: its framing box reads one component-level state).~~
  **CORRECTED by Batch 864 — D17 was WRONG.** The source does **not** store those
  values on the camera object at all: its `n4(cameraId, key, value, "right_panel")`
  is an **analytics beacon** (`nZ.S("libtv.canvas.director.camera.update", …)`),
  proven by source runtime capture (the request goes to the log endpoint
  `api2.liblib.art/api/www/log/acceptor/f` and **no** project-state write
  happens) and by the fact that `reference_line` occurs **exactly once** in the
  whole source chunk. The source model is **two component-level single values**
  (`tr` framing ratio, `ti` reference line) — so the clone's global
  `frameAspectRatio` + `showThirds` **already match the source** and there is
  **no gap**. The only real difference is that the source reports the change to
  a backend while the clone keeps a **local** record
  (`directorStore.telemetryLog`, verbatim event name and the four setting keys,
  **never touching the network**).
- The「选择画幅比例」seven cells keep the source's "no camera ⇒ all disabled"
  binding (Batch 862), but that branch is **unreachable on both sides** (the
  clone's delete planner enforces `DIRECTOR_LAST_CAMERA_REQUIRED`, so at least
  one camera always survives). It may therefore only be judged from source
  code — do not claim a runtime reading for it (D16).
- Research-doc comment discipline (Batch 862): **never copy the clone's own JSX
  literals into comments**. A negative control that replaces by literal hits the
  comment copy first, changes nothing in the code, and the gate stays green —
  a false green that leaves the negative control empty. Anchor such
  mutations at the indented code line instead.
- The framing box's **outside mask** is a **separate layer**, not a box-shadow
  (Batch 863, source verbatim `mP`): a `pointer-events-none … z-10` container
  holds `absolute inset-0 bg-black/20 backdrop-blur-md` plus a CSS mask that
  **hollows the box area** (`mask-composite: exclude`, two `linear-gradient`s,
  second position/size = the box's offset and size). The box itself carries
  **no** `box-shadow`. `bg-black/20` / `backdrop-blur-md` are usable as class
  names only because the clone already uses them elsewhere (4317's Tailwind
  scan is frozen); arbitrary-value classes still need inline styles.
- Negative controls: **"rc=0 with zero red lines" means the mutation never
  landed** (Batch 863 — `apply_mutation` computed the mutated text but wrote
  the original back; 7/7 mutations were no-ops and every gate stayed green).
  Make `apply_mutation` **return the mutated source**, and assert per mutation
  that the new value is actually present in the file on disk.
- Probe discipline: **count first, then measure** (Batch 863). If the element
  under test does not exist (e.g. the HEAD state of a controlled comparison),
  the criterion must fail **by name** — never fall back to default geometry and
  sample two unrelated points, whose difference can pass by luck.
- Pixel differences are **not** criteria when the 3D scene animates
  (Batch 863: the in-box/out-of-box brightness ratio drifted 0.87 ↔ 0.90).
  Use a **deterministic probe**: tint the mask red and require the area outside
  the box to be red while the area inside stays untinted.
- Verifier expectations must be **parsed from committed source evidence**, never
  typed from memory (Batch 863): the gate reads the verbatim source excerpt
  (chunk path + offsets + sha256) and derives even the percentages
  (`bg-black/20`, `outline-white/18`) from it; a missing evidence file fails
  the gate outright.
- Read a failing criterion's **detail against its own thresholds** before
  blaming the code under test (Batch 863): a red line whose detail satisfied
  every threshold was a **gate bug** (the probe's success payload was missing a
  key, so the predicate was always false). Compare detail ↔ thresholds first;
  if they agree, the implementation of the criterion is wrong.
- A colour probe that **paints** a target colour must assert the **hue**, not a
  single channel (Batch 863): an R-only check cannot tell "painted red" from
  "the background was already bright" (the out-of-box sample reached R=222 on
  a bright backdrop). Assert `R − G` (paint ⇒ large; already-white ⇒ ≈ 0).
- The clone **never touches the network** (Batch 864). The source site's
  `libtv.canvas.director.camera.update` beacon is reproduced **locally**:
  `directorStore.telemetryLog`, verbatim event name plus exactly the four
  source keys `camera_uuid` / `setting_name` / `setting_value` /
  `operation_source`. Keep `var` to those four keys — clone-specific context
  belongs in the store entry, never inside `var` — and never add a
  `fetch`/`axios` call to a director path.
- Adding a `z-index` to a container **creates a stacking context** and traps
  the children's `z-index` (Batch 864: the framing box's source-verbatim mask
  container `z-10` trapped the composition-toggle's `z-20`, so the toggle was
  unclickable — `elementFromPoint` hit the viewport gizmo's "flip X" button
  instead). After adding any positioned + `z-index` container, **re-test every
  clickable inside it**; fix by moving the **clone's own** widget, not by
  editing the source-verbatim structure.
- "Can I click it?" must be answered by a **hit test** (`elementFromPoint` at
  the target's center ⇒ the topmost element **is** the target), not by "the
  click worked this time" (Batch 864: a criterion that sometimes passed and
  sometimes failed was measuring luck, not the UI).
  **CORRECTED by Batch 864** — the hit test is not enough on its own: it must
  run **in a state where the defect actually reproduces**, and that state's
  premise must itself be a criterion. The first version of the Batch 864
  hit-test criterion ran after the aspect-ratio loop, which ends on `9:16`
  (the narrowest ratio) — the framing box is then far from the viewport's
  top-right gizmo, so the two **never overlap** and the criterion stayed
  green in the HEAD and MIX states (the defect was real: the gizmo's
  "flip X" button was the topmost hit). Fix: switch the ratio to `16:9` via
  the store first, and assert the ratio as its own criterion
  (`clone:the-hit-test-runs-at-the-ratio-where-they-overlap`), plus a
  mechanism criterion that reads both computed `z-index` values
  (`clone:the-viewport-gizmo-does-not-outrank-the-mask-container`).
- A gate that **crashes** must never count as "having teeth" (Batch 864). The
  controlled-comparison script checked only "HEAD rc ≠ 0", so a
  `FileNotFoundError` (the module the batch adds does not exist at HEAD)
  satisfied it — the most dangerous kind of false green: a gate that crashes
  hard enough looks like a gate that proves something. Criteria must require
  **named red lines + zero crashes**, never an exit code alone.
- A criterion's **premise** (ratio, breakpoint, mode, scroll position) must be
  part of the criterion (Batch 864). A hit test taken in a state where the
  defect cannot occur measures nothing — assert the premise, then the effect.
- A regression's "must stay green" watch-list must contain **only gates that
  were green in the baseline** (Batch 864). The first version put 10
  already-red legacy gates into the watch-list, so the script reported "10 red
  watch gates" and exited 1 — i.e. it charged legacy debt to this batch and
  drowned the real signal. Keep legacy debt in a separate `KNOWN_RED` set and
  make the criterion "**new** red (red − legacy) == 0".
- Source-site probe discipline (Batch 864): the source intermittently shows an
  "Agent upgraded to TV Director" modal, and **not finding it is the normal
  state** — never use a button that exists only in one state (e.g. the
  composition-toggle) as the criterion for "the director console opened".
  Locate the "open director console" trigger by whole-page text match, and
  close the modal by exact leaf text + DOM `.click()` with retries.
- The director framing box's **pixel size** is **layout-level, not a gap**
  (Batch 864, D18): the source computes `width = min(availW − 96, availH × ratio)`
  inside a **1920×1080** canvas while the clone's viewport box is **810px** tall
  ⟹ ⟹ absolute pixels are **not comparable** and must not be "fixed".
- The **screenshot/export ratio panel** (three values) is a **clone extension**
  (Batch 864, D23): the source's「截图」button has **no** ratio panel — it
  captures with the current framing ratio. Keep the clone's three ratios and
  label them as an extension instead of aligning them against the source.

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

**The local `pre-commit` hook treats any added table row whose first cell is a
bare number as a *beeftv-manual* batch row.** Its regex is `^\+\|\s*(\d+)[a-z]?\s*\|`
over `git diff --cached`, so a row like `| 45 | \`AssertionError\` |` in **any**
file — a probe's docstring table, a research README — is read as "a new Batch 45
was registered", and the commit is rejected with *"the last green build only
reached Batch 341"*. That numbering space is shared with the LibTV batches, so
it is a false positive. Do not `--no-verify` around it; write the first cell as
`门禁 45` / `Batch 45` instead so the row stops matching.

**The index is shared too, so the check above is a TOCTOU race.** Batch 295
(2026-10-07) used exactly the correct sequence above and still swept in 8 files
from a parallel agent: `git diff --cached --name-only` listed only its own 4
paths, but between that check and `git commit` the other agent staged its files
into the *same* index, and the plain commit took all 12. Two habits close it:

- Chain the verification into the **same shell command** as the commit, and abort
  if the path list is not exactly yours:

  ```bash
  git add -- <only your paths> \
    && { git diff --cached --name-only | grep -qv -e '^docs/user-manual/jimeng-canvas/' -e '^scripts/jimeng-b295' \
         && { echo "ABORT: index holds foreign paths"; git diff --cached --name-only; exit 1; }; } \
    && git commit -F /tmp/my-msg.txt
  ```

- Never leave a long gap between the check and the commit — writing a multi-KB
  commit message with a heredoc or a Python heredoc is exactly that gap. Build
  the message file *first*, then do `add → check → commit` back to back.

If it already happened and you pushed: do not rewrite. Record it in the batch
note (what was swept in, and that nothing was lost) and tell them.

**When the index already holds someone else's staged files, aborting is not
enough — you still owe them a commit.** Batch 312 (2026-10-07) hit exactly this:
a parallel agent had staged 5 `tdcanvas-canvas` files, so the guard fired and
refused to commit. But `git commit` (plain) would have taken *their* files too,
and `git commit -- <path>` is banned above. The fix is a **private index**: build
a throwaway index from `HEAD`, stage only your own paths into it, and commit from
it — **the shared `.git/index` is never read as the commit source, so their
staged state is left exactly as it was.**

```bash
TMPIDX=$(python3 -c "import tempfile; print(tempfile.mktemp(prefix='idx-'))")
export GIT_INDEX_FILE="$TMPIDX"
git read-tree HEAD                      # start from HEAD, not from the shared index
git add -- <only your paths>            # your paths only
git diff --cached --name-only           # guard again, inside the private index
[ "$(git diff --cached --name-only | wc -l)" = "<your count>" ] || { echo ABORT; exit 1; }
git commit -F /tmp/my-msg.txt
unset GIT_INDEX_FILE                    # leave the temp file for /tmp to reap
```

Then **verify their staged files survived**: `git diff --cached --name-only`
must still list their paths, and `git diff --cached --numstat -- <their dir>`
must still show their numbers. Two cautions: build the message file *before*
entering the block (the `read-tree`/`add` window is short but non-zero), and
**do not `rm` the temp path** — pass cleanup to `python3` or let the OS reap it.

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
