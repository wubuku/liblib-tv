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
| LibTV behavior | `python3 scripts/verify-liblib-batch<N>.py`，当前脚本范围为 Batch 4-33、35-50、52-65、67-95（中间无脚本的 batch 除外） | script-specific assertions and no unexpected console/page/request errors |

## LibTV Batch Coverage

| Script | Contract |
|---|---|
| Batch 4 | grouping, ungrouping, delete/undo, mobile overflow |
| Batch 5 | multi-drag, transactional undo/redo, duplicate selection |
| Batch 6 | historical marquee implementation, H/V tools, Space pan, input guard |
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
| Batch 68 | Director structured owner key, in-memory project/session/generation, A/B and cross-canvas isolation, duplicate reset, active-delete tombstone compatibility, memory capture sidecar and graph isolation |
| Batch 69 | Director authored/runtime object split, seek/playback/path authored fingerprint stability, object/camera/pose authoring restore, close/reopen and owner/graph isolation |
| Batch 70 | Director project-local command result/history, no-op and rejection outcomes, gesture coalescing, undo/redo, future truncation, reopen continuity and ordinary graph/history isolation |
| Batch 71 | Director Inspector/pose/camera/path/free-draw pointer lifecycle, gesture commit/cancel/pointercancel cleanup and ordinary graph/history isolation |
| Batch 72 | Director reference-aware delete planning, object/group/camera/track/path/capture/resource closure, last-camera/resource policy, runtime repair, exact delete/undo/redo and ordinary graph/history isolation |
| Batch 73 | Director capture/export/phone async operation/attempt/result authority, owner/source freshness, duplicate/stale convergence and export resource transfer/release |
| Batch 74 | Director browser-local durable project persistence, strict envelope restore, stale save, owner isolation, runtime/UI/resource-byte exclusion and storage failure continuity |
| Batch 75 | Director project-scoped clipboard packet, typed closure, identity/reference remap, resource alias, deterministic paste, one-entry history and keyboard/persistence isolation |
| Batch 76 | Director all-canvas owner reachability, inactive source/canvas tombstone, active shell/session/runtime cleanup, idempotency, stale async, graph undo boundary and retained persistence |
| Batch 77 | source-aligned wheel/middle/Space/H/V canvas navigation, blank-drag no-op, modifier zoom, mobile diagnostics and real Director TransformControls pointer drag/gesture cleanup |
| Batch 78 | Director Curve Editor/Phone Vcam/Timeline pointercancel, blur, visibility, unmount cleanup, pointer reuse and stale-pointer prevention |
| Batch 79 | Director whole-project duplicate: graph/parent/edge and Director project/entity two-pass remap, clean target authority, resource policy and source/target isolation |
| Batch 80 | Director durable tombstone envelope, save resurrection guard, active/inactive cleanup, capture sidecar cleanup, shared/unshared local resource release and reload reopen rejection |
| Batch 81 | Director strict project JSON import/export, owner/project rebinding, one-entry history, undo/redo, zero-partial rejection, download/file-input round trip and ordinary graph isolation |
| Batch 82 | Director local resource descriptor/provenance, attempt freshness, retry/cancel/release, finite OBJ/FBX materialization, parse-failure proxy retention, model-library feedback and zero diagnostics |
| Batch 83 | Director typed command outcome/reason feedback projection, fixed-header status surface, ARIA semantics, committed-success suppression, meaningful no-op visibility, mobile geometry and zero diagnostics |
| Batch 84 | Director object-tree lock/visibility controls, locked-target Inspector/Viewport/Timeline/Curve protection, typed rejection, zero document/history mutation, unlock recovery and zero diagnostics |
| Batch 85 | Director object-tree selection context, single/multi-selection count, project-scoped copy, clear zero-history, reference-aware batch delete, mobile discovery and zero diagnostics |
| Batch 86 | Director transform target context, object/group pointer cancellation and lost-capture cleanup, real gizmo drag, authored/runtime/history continuity, locked rejection, mobile geometry and zero diagnostics |
| Batch 87 | Director undo/redo selection preservation and repair across object-tree, Inspector, Viewport and Timeline, portable-document selection exclusion and zero diagnostics |
| Batch 88 | Director selection/timeline/TransformControls authority, single/multi/group normalization, reverse timeline selection, delete repair, locked zero mutation and mobile geometry |
| Batch 89 | Director scene settings, ground/grid/background controls, add-camera entrypoints, camera track/keyframe continuity, portable export and mobile geometry |
| Batch 90 | Director project/session lifecycle diagnostics, scene semantic command, draft/commit, persistence, one-entry history, no-op/rejection, undo/redo and mobile Inspector |
| Batch 91 | Director object/camera/group typed command boundary, name draft/commit, reference validation, persistence, one-entry history, invalid/no-op protection and zero diagnostics |
| Batch 92 | Director local resource descriptor/decoded-byte budget, owner-scoped request/lease, deferred/final release, finite OBJ/FBX materialization, retry/cancel and zero diagnostics |
| Batch 93 | Final Director desktop/mobile shell/R3F regression, ordinary canvas cross-batch regression, Batch 59/67-92 current-gate serial run, governance and full repository checks |
| Batch 94 | Director workspace focus containment, mobile tree/Inspector local focus scopes, focus return, inactive-drawer `aria-hidden`/`inert`, Escape/editable boundary and desktop/mobile diagnostics |
| Batch 95 | Director direct canvas-image ingress, session-only environment preview, source switching/clearing/stale cleanup, malformed data URL preflight, desktop/mobile and failure-isolation diagnostics |
| Batch 96 | Director portable multi-camera Shot records, legacy V1 decode, Shot create/switch/update, history undo/redo, capture provenance/gallery, camera delete repair, clipboard/whole-project duplicate remap, reload/import/export and desktop/mobile diagnostics |
| Batch 97 | Agent drawer alignment with the 2026-09-05 source audit: header action set with disabled states, source-named Skill cards, composer attachment/model/skill/mode controls, selection-model catalog menu (7 image + 8 video with premium badges), generation mode menu and local status feedback |

The current source-contract coverage and historical assertion boundaries are tracked separately in [`research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md`](research/liblib-seedance-2.5-2026-08-25/LIBTV_VERIFICATION_COVERAGE.md). Batch 9 and Batch 10 remain valid for their dated clone snapshots; they do not silently become coverage for the current `1092.5px` toolbar or structured AutoLink contract.

Run them serially because they use the same local dev server and write dated visual references:

```bash
for script in scripts/verify-liblib-batch{4..33}.py scripts/verify-liblib-batch{35..50}.py scripts/verify-liblib-batch52.py scripts/verify-liblib-batch53.py scripts/verify-liblib-batch54.py scripts/verify-liblib-batch56.py scripts/verify-liblib-batch{57..65}.py scripts/verify-liblib-batch{67..96}.py; do
  python3 "$script" || exit 1
done
```

Batch 34 和 Batch 66 没有对应的专项 verifier，不应被循环命令隐式当作已验证
行为。Batch 67 是无浏览器 pure codec gate；Batch 68、Batch 69、Batch 70、
Batch 71、Batch 72、Batch 73、Batch 74、Batch 75、Batch 76 是 pure + browser hybrid
且不生成截图；其余视觉脚本仍按
各自 batch screenshot ledger 维护。

Batch 77 是 source-aligned navigation + Director pointer hybrid gate，默认不写
截图；它保留 DOM/computed style、viewport runtime、R3F canvas pixels 和
真实 mouse pointer drag 断言。

Batch 79 是 Director whole-project duplicate hybrid gate，默认不写截图；它保留
pure planner 的 deterministic corpus 和 fresh-page graph/Director isolation audit。
它只证明 clone-owned copy contract，不证明 LibTV 原站 duplicate、真实资源或
remote persistence。

Batch 78 是 Director pointer cancellation hybrid gate，默认不写截图；它保留
真实 mouse pointer 输入、pointer capture 状态、gesture/history、stale listener
与跨 owner/canvas R3F Canvas teardown 断言。2026-08-28 已串行复跑 Batch 59、
67-80，全部通过；这仍是 clone-owned reliability gate，不是源站 Director
source parity。

Batch 80 是 Director durable tombstone hybrid gate，默认不写截图；它保留 strict
tombstone pure corpus 和 fresh-page active/inactive owner cleanup、capture sidecar、
local resource reachability、reload reopen guard 与 zero-diagnostic audit。它只证明
clone-owned browser-local cleanup contract，不证明 LibTV 原站删除/恢复 UI、remote
persistence 或真实资源 materialization。

Batch 81 是 Director strict project import/export hybrid gate，默认不写截图；它
保留 strict V1 document corpus、fresh BrowserContext download/file-input workflow、
owner/project rebind、capture/runtime/UI exclusion、one-entry history、undo/redo、
same-document no-op、invalid zero-partial、ordinary graph/history isolation 和零
console/page/request diagnostics。它只证明 clone-owned local file workflow，不证明
LibTV 原站存在相同文件格式、导入/导出 UI、remote sync 或真实资源 materialization。

Batch 82 是 Director local resource materialization hybrid gate，默认不写截图；它
保留 typed descriptor/provenance、attempt freshness、retry/cancel/release、valid
OBJ materialization、parse-failure proxy retention、unsupported-extension
zero-mutation、UI status feedback 和 zero-diagnostic audit。它只证明 clone-owned
session-local 的有限 materializer，不证明生产 loader/cache、复杂 FBX/纹理、remote
persistence 或 LibTV 原站资源语义。

Batch 83 是 Director command feedback hybrid gate，默认不写截图；它保留
typed disposition/reason 到 clone-owned fixed-header status surface 的映射、
`role=status`/`aria-live=polite`/`aria-atomic=true`、rejected/stale/conflict/
meaningful-no-op 可见性、committed-success 抑制、mobile header geometry、
zero-history feedback boundary 和 zero-diagnostic audit。它只证明 Director
前台反馈投影，不证明 LibTV 原站 feedback taxonomy、文案、颜色、ARIA 或
ordinary canvas 的统一 feedback owner。

Batch 84 是 Director lock/editability hybrid gate，默认不写截图；它保留
对象树 lock/visibility 并列控制、locked target 的 Inspector/Viewport/Timeline/
Curve 编辑保护、`DIRECTOR_TARGET_LOCKED` 拒绝、zero document/history mutation、
visibility continuity、unlock recovery 和 mobile discoverability。它只证明
clone-owned Director 编辑保护，不证明 LibTV 原站 Director 是否有相同 lock
UI、文案、键盘策略或 source-exact behavior。

Batch 85 是 Director selection/CRUD discoverability hybrid gate，默认不写截图；
它保留单选/Shift 多选/分组选择的数量投影、project-scoped copy、clear
zero-history、reference-aware batch delete、mobile tree discovery 和 zero
diagnostics。它只证明 clone-owned selection action bar，不证明 LibTV 原站
Director 是否有相同 selection bar、文案、键盘策略或 source-exact behavior。

Batch 86 是 Director transform-context/cancellation hybrid gate，默认不写截图；
Batch 87 是 Director restore-selection hybrid gate，默认不写截图；Batch 88 是
Director selection/timeline authority hybrid gate；Batch 89 是 Director
scene-settings/add-camera hybrid gate，默认不写截图。它们保留目标上下文、真实
gizmo pointer drag、authoring/runtime/history、pointercancel/lost pointer capture、
selection normalization、track/keyframe/path ownership、scene settings、camera
creation、locked rejection、mobile geometry 和 zero-diagnostic 断言。它们只证明
clone-owned Director 变换、选择和场景入口，不证明 LibTV 原站 Director gizmo
placement、目标文案、Timeline 联动、add-camera defaults、undo selection 或
source-exact behavior。Batch 90 是 Director project/session + scene command hybrid
gate，默认不写截图；它保留 session outcome/lifecycle diagnostics、scene draft/
commit、typed scene command、persistence、one-entry history、no-op/rejection、
undo/redo、mobile Inspector 和 zero-diagnostic 断言。它只证明 clone-owned
project/session 与 scene command 边界，不证明 LibTV 原站 Director project/session、
history、persistence、文案或 source-exact behavior。
Batch 91 是 Director object/camera/group command hybrid gate，默认不写截图；它保留
对象属性、相机设置、角色组创建/重命名/变换、name draft/commit、reference
validation、persistence、one-entry history、invalid/no-op zero mutation 和
zero-diagnostic 断言。它只证明 clone-owned mutation boundary，不证明 LibTV 原站
Director command/history/persistence、文案或 source-exact behavior。

Batch 92 是 Director local-resource lifecycle hybrid gate，默认不写截图；它保留
strict descriptor/decoded-byte budget、owner-scoped request/lease、terminal
status/error invariant、deferred release、最后一个 lease 的 final release、
有限 OBJ/FBX materialization、parse-failure proxy retention、retry/cancel 和
zero-diagnostic 断言。Batch 82 历史 verifier 也按当前 owner/lease 合同串行复跑。
它只证明 clone-owned session-local resource lifecycle，不证明 LibTV 原站资源
协议、生产 loader/cache、复杂 FBX/纹理、remote persistence 或 ordinary canvas
media ingress。

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
