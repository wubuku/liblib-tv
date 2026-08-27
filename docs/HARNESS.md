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
| LibTV behavior | `python3 scripts/verify-liblib-batch<N>.py`，当前脚本范围为 Batch 4-33、35-50、52-65、67-69（中间无脚本的 batch 除外） | script-specific assertions and no console errors |

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
| Batch 33 | long-video request/busy state, 12-node process graph, dense topology, repeated bounds and atomic undo/redo |
| Batch 35 | real director CTA, full-screen R3F pixels, tree/Inspector sync, camera/framing, helper-free capture, canvas return, atomic history and responsive drawers |
| Batch 36 | typed director tracks/keyframes, deterministic R3F scrub/playback, loop/navigation/zoom, auto-keyframe, lifecycle and compact timeline |
| Batch 37 | preset motion paths, arc-length R3F sampling, orient-to-path, speed presets/custom Bezier, helper-free capture and compact curve workflow |
| Batch 38 | pencil/pen pointer authoring, serializable anchors/handles, vertex/symmetric/asymmetric editing, cancellation, path structure edits, helper-free capture and responsive Inspector |
| Batch 39 | fixed path pivot, position/rotation/scale transform, world/local anchor inversion, offset/full reset distinction, transformed playback, capture and responsive Inspector |
| Batch 40 | real cropped WebGL recording, export settings/progress/error states, dynamic WebM decode/playback, ratio-shaped video return, target selection, atomic undo/redo and mobile geometry |
| Batch 41 | phone virtual-camera local boundary, real pose input, stability/level/hold/elevation controls, current-playhead recording, named camera-track import and mobile geometry |
| Batch 42 | articulated R3F character, 20 pose presets, SAM controls, independent pose tracks, transform-plus-pose composition, interpolation, path rejection and mobile geometry |
| Batch 43 | coordinate/rotation/object camera look-at, animated target follow, first/third-person modes, FOV composition, path/phone guards, recovery and mobile geometry |
| Batch 44 | seven preset camera motions, replace/append allocation, no-room/follow guards, path preservation/disablement, R3F pixel changes and mobile panel bounds |
| Batch 45 | character groups, 2×3 crowd creation, Shift multi-select grouping, group transforms, typed group tracks, scrub/play pixel changes, ungroup preservation and mobile bounds |
| Batch 46 | camera screenshot tabs, empty/grouped capture gallery, active selection, full-screen viewer, zoom/Escape, single/bulk canvas return, clear-all confirmation, returned-node preservation and mobile bounds |
| Batch 47 | model-library trigger, five category tabs, proxy cards, serializable prop insertion, tree/Inspector sync, R3F pixel change, `我的模型` empty state, dismissal and mobile bounds |
| Batch 48 | multiple FBX/OBJ local import, invalid-extension filtering, browser-local persistence, refresh recovery, repeated local proxy insertion, linked-instance cleanup, desktop/mobile bounds and dismissal |
| Batch 49 | Director viewport native coordinate gizmo, six axis commands, camera-mode recovery, projected hit geometry, path/phone guards, capture hiding, dual WebGL pixels and responsive bounds |
| Batch 50 | Director workspace sidebars collapse/restore, viewport expansion, mobile drawer recovery, focus ownership, page shortcut isolation, editable-target guard and Escape layering |
| Batch 52 | Current 13-action image toolbar, source-sized button geometry, page-level Preview, watermark/close geometry, keyboard isolation, unchanged graph/selection and mobile clipping |
| Batch 53 | Empty image annotate replacement, `536x49` toolbar, source-shaped tool/color/line-width controls, DPR2 canvas, standard-panel removal, keyboard isolation, unchanged graph/selection and mobile clipping |
| Batch 54 | Empty image element-edit replacement, `272x44` toolbar, node-local masked stage/guide, `400x50` empty record panel, tool/brush-size controls, standard-panel removal, keyboard isolation, unchanged graph/selection and mobile clipping |
| Batch 56 | Media-gated image rotate entry, `旋转与镜像` derived image node, source edge, typed metadata, selected-create state, atomic undo/redo, no-media disabled/no-op and desktop/mobile overflow |
| Batch 57 | Ordinary graph connection normalization, source/target Handle direction, duplicate/reverse/parallel/self/cycle guards, zero-mutation rejects, one-step history and desktop/mobile diagnostics |
| Batch 58 | Node-bound preview/annotate/element-edit/Director owner identity, delete/switch invalidation, UI-only cleanup, delete-only history delta and desktop/mobile diagnostics |
| Batch 59 | Director asset-library search, preview-only selection, explicit proxy insertion, object-tree/Inspector continuity, WebGL nonblank and desktop/mobile diagnostics |
| Batch 60 | Ordinary image double-overlay owner identity, selection migration, geometry invariants, panel pointer boundary, control interaction, active-tool replacement, graph/history isolation and desktop/mobile diagnostics |
| Batch 61 | React Flow whole-batch T0/T1 routing, current-snapshot selection/position/measurement and zero-partial semantic rejection |
| Batch 62 | validated selection command snapshot, editable/IME guard, foreground shortcut suspension, one-Escape and focus fallback |
| Batch 63 | actual React Flow host-centered default node placement |
| Batch 64 | Asset drawer host-resize anchor preservation |
| Batch 65 | responsive viewport bootstrap/stored ownership and stale callback rejection |
| Batch 67 | Director Project Document V1 pure strict codec, round-trip, runtime-field exclusion and invalid/future/reference corpus |
| Batch 68 | Director structured owner key, in-memory project/session/generation, A/B and cross-canvas isolation, duplicate reset, active-delete close, memory capture sidecar and graph isolation |
| Batch 69 | Director authored/runtime object split, seek/playback/path authored fingerprint stability, object/camera/pose authoring restore, close/reopen and owner/graph isolation |

The current source-contract coverage and historical assertion boundaries are tracked separately in [`research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md). Batch 9 and Batch 10 remain valid for their dated clone snapshots; they do not silently become coverage for the current `1092.5px` toolbar or structured AutoLink contract.

Run them serially because they use the same local dev server and write dated visual references:

```bash
for script in scripts/verify-liblib-batch{4..33}.py scripts/verify-liblib-batch{35..50}.py scripts/verify-liblib-batch52.py scripts/verify-liblib-batch53.py scripts/verify-liblib-batch54.py scripts/verify-liblib-batch56.py scripts/verify-liblib-batch{57..65}.py scripts/verify-liblib-batch67.py scripts/verify-liblib-batch68.py scripts/verify-liblib-batch69.py; do
  python3 "$script" || exit 1
done
```

Batch 34 和 Batch 66 没有对应的专项 verifier，不应被循环命令隐式当作已验证
行为。Batch 67 是无浏览器 pure codec gate；Batch 68、Batch 69 是 pure + browser
hybrid 且不生成截图；其余视觉脚本仍按各自 batch screenshot ledger 维护。

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
