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
| Batch 98 | Add-node panel alignment with the 2026-09-05 source audit: smart-clip label, script NEW/legacy flyout, material style/effect flyout, canvas-node search filter and local resource statuses |
| Batch 99 | Shortcuts help panel copy alignment with the 2026-09-05 source audit: four-column items, keycap counts, suffixes, deletion row placement, canvas-node-search row, Windows-redo removal and crosswalk snapshot refresh (no runtime handler changes) |
| Batch 100 | Empty-canvas state with source hint and four quick-create chips (SD 2.5 badges), pointer-events-safe overlay, honest local chip feedback, canvas-switch reachability and mobile overflow |
| Batch 101 | Generation-history panel alignment with the 2026-09-05 source audit: title, thumbnail size slider, canvas-scope chip, counted image/video/audio tabs, local rating menu with favorite filter, empty-state copy and toolbar entry rename |
| Batch 102 | Asset manager drawer alignment with the 2026-09-05 source audit: rating/display controls with honest local hints, exact empty-state copy, footer count + collapse button, search/filter aria naming |
| Batch 103 | Top-bar mode toggle alignment with the 2026-09-05 source audit: 工作流/故事板 aria naming, pressed-state round trip, batch11/13/14/17 assertion migration (internal editorMode values unchanged) |
| Batch 104 | Storyboard three-section alignment with the 2026-09-05 source audit: text/image/video column order, zoom column buttons, 暂无 copy, empty-canvas key-elements hiding and batch13 assertion migration |
| Batch 105 | Collaborative follow banner from the 2026-09-05 computed-style audit: top-center z-305 pill, faded default, uiStore follow session, follow-banner as top single-escape surface (batch62 contract) |
| Batch 106 | Project menu (logo dropdown) alignment with the 2026-09-05 sampling: four source-named items with grouping divider, honest local statuses, outside-close, tutorial popover lock |
| Batch 107 | Skill headline rotation per the three 2026-09-05 source-observed copies, driven by 换一批 with wrap and decoupled from editorMode |
| Batch 108 | Cross-batch serial regression over the full verifier queue for the 97-107 alignment series: 81 pass, node-PATH environment fixes, 12 failures attributed pre-existing at baseline 86673b6 |
| Batch 110 | Aged-gate deprecation: 12 pre-existing-drift verifiers marked AGED_GATE/HISTORICAL_CONTRACT with replacement-map §4.z (no runtime changes) |
| Batch 111 | Character library modal alignment with the 2026-09-05 sampled geometry (1304x731@68) and detail tags: fluid shell, 1:1:1:2.37 image columns, sampled tag map, close aria (batch11 assertion migrated) |
| Batch 112 | Character filter panel alignment with the 2026-09-05 sampling: five sampled chip groups, clear-all, upward panel anchored to the toggle, local tag-based filtering with 古代 alias (culture group unknown) |
| Batch 113 | Uniform character strip spacing: removed position-specific margin hack, uniform 19px gap per the 2026-09-05 source screenshot |
| Batch 114 | Multi-canvas dropdown alignment with the 2026-09-06 disposable-project sampling: switch + hover-gated more button rows, four-item row menu, delete confirm dialog, 副本{n} duplicate naming, newest-first order, creation-adjacent delete fallback |
| Batch 115 | Canvas double-click opens the add-node panel (2026-09-06 sampling), no node creation, escape/re-trigger |
| Batch 116 | Script-generator node type (脚本 NEW): 350x350 card with three attempt modes, reference entry, GVLM 3.1 model tag and local prompt; add-panel 脚本NEW now creates the node (batch98 assertions migrated) |
| Batch 117 | Director node card alignment with the 2026-09-06 sampling: card title/description/打开导演台 copy, workspace entry via node button, escape close (batch50 workspace aria unchanged) |
| Batch 119 | /project list page: back/title/recycle/new-folder structure, create-card canvas creation, canvas cards navigate+activate, logo-menu 全部项目 real routing |
| Batch 121 | Topbar freshness alignment with the 2026-09-06 source: credits 100, membership 限时 45 折 entry, 教程 entry rename (batch11 assertion migrated) |
| Batch 128 | Attempt chips driving settings label: 5分钟超长视频→Auto·300s, 首尾帧→Auto·5s; deselect keeps current settings (CLONE_DECISION) |
| Batch 131 | Second full verifier serial regression: 99/114 pass, batch16/21 fixed, batch93 flake confirmed, 12 aged gates unchanged |
| Batch 143 | Video panel default duration 6s→5s alignment (source 16:9·720P·5s·1个), batch21 duration assertions migrated |
| Batch 124 | Canvas recycle bin: soft delete with full CanvasData snapshot, /project recycle panel (30-day copy, restore), restore without active-canvas switch (batch119 assertion migrated) |
| Batch 125 | Video panel attempts row (5分钟超长视频/首尾帧/首帧 chips), 新功能：支持真人 bar, prompt placeholder alignment (toolbar/generate flow unchanged) |
| Batch 135 | Credits ratio factor calibrated on the 2026-09-06 data points (16:9→27/s, Auto→46/s); other ratios unsampled at 46/s |
| Batch 139 | Topbar 积分超市 / 积分余额 split: two independent entries per the sampled source order (supermarket display-only, balance 100) |
| Batch 141 | Video model menu full catalog (35 items sampled 2026-09-07): scrollable menu container, batch22 matrix/premium assertions migrated |
| Batch 148 | /project project card cover placeholders: gradient cover area with play icon and node count badge on each canvas card |
| Batch 149 | Video panel advanced settings vertical column (heading + three 36px rows, right-aligned switches; hidden in process view), default model Seedance 2.0 VIP with abbreviated trigger "2.0", reference slots 48x55 (batch21/22/33 assertions migrated) |
| Batch 150 | /project canvas card opens the canvas in a new tab (source 2026-09-07; list page stays put) + add-node panel container rounded-2xl/backdrop-blur-[32px]/hairline border (batch119 popup assertion migrated) |
| Batch 151 | Video panel toolbar pills h-26 px-2 and credits block min-w-[85px]/justify-end/muted gray per 2026-09-07 round-2 sample; selection-bound panel and one-time 尝试 gate recorded, menus rAF-gated (unopenable in throttled window) |
| Batch 152 | /project card sub-line date-only (workspace prefix removed per 2026-09-07 sample) + surface coverage matrix refreshed with Batch 149-152 facts |
| Batch 153 | Evidence batch: Auto→46/s confirmed on source (230 = 5×46), fresh video nodes show no panel, credits-block classes match Batch 151 implementation; no code change |
| Batch 154 | Full sweep of all 124 verifiers: 112 pass, 12 aged (exact Batch 108/131 list), 0 unexplained; batch124 migrated to popup contract (Batch 150 consequence), batch93 timing flake documented; never prefix verifiers with `timeout` (Rosetta/PIL dlopen artifact) |
| Batch 155 | 5分钟超长视频 chip switches the params duration range to 30..300 (long layout) and deselect clamps duration to <=30 (CLONE_DECISION); credits formula unchanged |
| Batch 156 | batch93 mobile drawer-close clicks hardened to drawer-exterior points (left tree drawer w-[220px] -> x=320; right inspector drawer w-72 -> x=56), 3/3 stable runs |
| Batch 158 | Default model reverted to Seedance 2.5 (fresh node 2.5 + attempt node 2.5 vs preset-carrier-only 2.0); batch128 Auto+300s linkage confirmed by controlled re-test; batch149/22/33 assertions migrated back; corrections recorded for batch151/153 conclusions |
| Batch 159 | 尝试 chips moved into the video node card (vertical 36px pills below preview, per 2026-09-07 geometry); panel no longer duplicates the attempts row; attempt state lifted to VideoNode with linkage effect (128/155 contracts intact); batch21/22 menu offsets migrated -32 |
| Batch 160 | 5min chip selects the whole long-video mode (trigger 超长视频, credits 14700 = 300×49 per source full-panel dump); reference slot row conditional on non-empty references; 「新功能」bar removed (absent in source 2026-09-07 panel); batch21/22 offsets migrated -24 |
| Batch 161 | Video panel grown to 397px — fixed 274px overflowed after the Batch 149 advanced column (prompt squeezed to 16px, 35px overflow); prompt restored to ~95px (source 96px); batch21/22/26 height+offset assertions migrated |
| Batch 162 | Mobile 390x844 breakpoint verified after the 397px growth: no page-level overflow, panel vertically in-viewport, prompt intact; verify-liblib-batch161.py extended with a mobile phase + screenshot record |
| Batch 163 | Tablet breakpoints 768x1024 / 1024x768 verified: no page-level overflow, prompt intact, vertical clipping per accepted contract; tablet phases + screenshots added (verifier now 20 checks) |
| Batch 164 | Footer triggers aligned to sampled source classes: model min-w-[88px] justify-between 13px normal, mode justify-center pl-2 pr-2.5, params justify-between, footer h-8 without top border; batch21 x offsets migrated +37 |
| Batch 165 | Reference slot row aligned to sampled classes (flex-wrap items-start pl-1, no fixed height — h-12 clipped 55px slots) and the absent-in-source 「Auto Link：」summary removed |
| Batch 166 | Prompt textarea background/rounding removed (source scroll region is plain) and the 「3 个匹配」 AutoLink popup chip removed (absent in sampled toolbars, popup superseded by the inline advanced column) |
| Batch 167 | /project secondary surface alignment: filled secondary header buttons (回收站/新建文件夹 h-8), create card restructured to aspect-video cover + title row (dashed placeholder removed), canvas card covers aspect-video (~150px, card ~208px), 14px medium titles |
| Batch 168 | /project left sidebar added (240px sticky: 新建项目, nav rows 首页/项目-active/LibTV Agent/创作者挑战赛, bottom SD2.5 promo + 帮助) per the 2026-09-07 DOM re-audit; unwired entries are local placeholders |
| Batch 169 | Character library modal tab chrome (公共角色库 / Seedance2.0&2.5合规素材库) + Seedance consent gate replicated as local-only state (accept/decline both local; no account action taken on the user's behalf); 素材库 tab shows a local empty state |
| Batch 170 | Canvas top bar workspace rename input (13px, min-w-30 max-w-100 cursor-text, transparent, left of the canvas chip) bound to projectName; store default renamed 未命名项目 -> 未命名工作区; batch16/17 assertions migrated |
| Batch 171 | Bottom-left asset bar aligned to sampled geometry: bar items-end gap-2 without padding box, 资产管理 button rounded-lg 13px (94x28), zoom chip rounded-lg 13px (42x28) |
| Batch 172 | Canvas right-click context menu (blank pane + node): full-screen catcher + menu fixed at the click point, six items 上传/保存到我的资产/添加节点/撤销⌘Z/重做⇧⌘Z/粘贴⌘V with two 0.5px dividers; 保存到我的资产 gated on selection, 撤销/重做 wired to store history; 上传/保存/粘贴 are click-to-close placeholders (no backend) |
| Batch 173 | Node right-click menu errata (different from pane menu): 保存到我的资产/创建主体 disabled + 复制节点⌘C/创建副本⌘D/粘贴⌘V/删除⌘⌫/复制到剪贴板 with "?" glyphs and two dividers; 创建副本/删除 wired to store, rest placeholders; model menu selected row bg aligned to sampled white/15%; source default model is account-stateful (2.5 vs 2.0 VIP same day) — clone keeps 2.5 |
| Batch 174 | Model menu row system aligned to three-state direct measurement: all rows fixed 52px (no selected growth), selected bg white/15% without border, hover white/10%, 34px icon tile, descriptions present in every row clipped by the 36px column; batch22 height/description assertions migrated to the current-source contract |
| Batch 175 | Mode menu re-sampled in a rendering window: exactly five items (no 超长视频/视频编辑), only 文生视频 enabled on an empty node, rows h-8 selected white/15%, container 161px; params menu ratio grid is six tiles without Auto (grid-cols-4, 62px tiles); long-video entry is the node-card attempt chip — batch21/33 migrated off the mode-menu route (process ratio Auto, duration 300 via batch128 linkage) |
| Batch 176 | Long-video params menu sampled (2026-09-08): ratio grid SEVEN tiles with Auto first/selected in long mode (five per row) — Batch 175's Auto-internal-only narrowed to normal mode; long hint replaced with the sampled copy 因剧情和画面设计…; long chip also switches the model to 2.5 (footer direct evidence); count section confirmed absent in long mode; batch21 long-phase assertions migrated |
| Batch 177 | Model row hover slide + chip no-toggle (2026-09-08): text column translate-y-2 → 0 on group-hover or data-selected inside the 36px clip column (200ms, row stays 52px); attempt chips are not toggles — re-click keeps selection (batch128/155/160 deselect assertions migrated to stays-selected), panel mount replays attempt linkage (prevAttempt starts null) |
| Batch 178 | Chip selected marker + cancel path (2026-09-08): selected chip = white/10% bg with unchanged #f7f7f7 text, rounded-lg, leading 14px lucide icon substitutes; ESC does not cancel the attempt (only deselects; persists across reselect — asserted); the real cancel path is the mode menu, which now clears the chip via the new onAttemptChange prop and clamps duration with a functional setMode guard preserving the user's mode choice |
| Batch 179 | Canvas token harvest (2026-09-08): --canvas-controls-hover #ffffff1a / -bg #262626 / -border #363636 / -text #fff, --z-panel 400 --z-modal 500, --fg-default/--fg-muted recorded; tokens defined in globals.css, chip hover and context-menu text use them; consent-gate re-probe confirms the gate still blocks 素材库 (nothing accepted on the user's behalf) |
| Batch 180 | Attempt chip icons use the harvested iconify (libtv) glyphs verbatim (viewBoxes 16/20.05x22/22) replacing lucide substitutes; z-scale migration evaluated and rejected — source topnav is z-1000 over panel 400, a clone-wide re-map would touch 10+ components for no visible gain (decision recorded) |
| Batch 181 | Aged-verifier triage: batch49 self-healed (aged list now 11); batch72 revived — Batch 96 shot→camera validation postdated its fixture, oneCameraDocument now cascades the shot; batch74 revived — REAL persistence regression fixed: documentForPersistence strips non-portable captures without pruning shots[].captureIds, so load re-validation REJECTED its own saves; remaining 9 aged gates stay AGED_GATE |
| Batch 182 | batch75 timeout root-caused with a falsification test (reverting the Batch 181 persistence fix reproduces the exact 30s wait_for_function timeout) — downstream symptom of the same regression, revived with zero code changes; aged list now 10 |
| Batch 183 | batch9/51 revived — their (1092.5, 900.5) failures were verifier migration gaps: the source-backed image toolbar contract is 1092.5×49 (Batch 51/52 screenshot analysis) and the width assert still said 900.5; batch9's video-panel wait bumped to 450ms; a wrong image-panel 274→397 migration was reverted after direct source sampling showed the empty image panel at 660×191 (274 is the storyboard-state contract); batch20 confirmed green all along — aged list now 6 (6/40/41/44/46/48) |
| Batch 184 | Remaining six aged verifiers triaged with per-script failure signatures — all CONFIRMED AGED_GATE (surfaces already covered by the passing Batch 59/67-96 current gates; batch6 superseded by Batch 77 navigation evidence; batch40 is a fixture media artifact); zero code changes, headers now self-document the triage |
| Batch 185 | Batch 172-178 surfaces verified at the 390 breakpoint (new verify-liblib-batch185.py, 14 checks): context menus both variants fit the viewport, attempt chips render glyphs with white/10 selected state, model menu keeps 52px rows + slide classes after fit-view; harness notes — 390 needs elementFromPoint pane probing and a Meta+0 fit before in-card panels (660px wide anchors off-screen at native zoom) |
| Batch 186 | Video panel footer icon group aligned (2026-09-08 harvest): order params → doc-sparkle (new, harvested libtv path) → 文A translate (harvested path replaces lucide) → lucide settings2 (new; source uses lucide there) → credits → generate (harvested up-arrow path); click semantics unsampled so new buttons are inert placeholders; batch21's panel-relative menu x asserts migrated to font-independent trigger-relative offsets (-68/-60) after footer flex reflow showed bimodal 119/124.16 jitter; batch125's missed no-toggle migration applied |
| Batch 187 | doc-sparkle/settings2 click semantics sampled — both buttons are click-INERT on an empty fresh node (no popover, no toggle, no mounted layer; class diff is hover noise only), matching the clone's placeholders; verify-liblib-batch187.py (9 checks) pins the inertness as a regression contract |
| Batch 188 | Toolbar pill icons aligned to harvested iconify (libtv) glyphs (12x12; 参考=plus, 标记=pin+sparkle, 特效=camera+lens, 角色库=shield-check, 运镜=video-camera; transforms verbatim) replacing lucide approximations; new ToolbarPillIcons.tsx, unused lucide imports dropped |
| Batch 191 | Pill popovers sampled — 运镜/参考/标记 click-inert on an empty node (recorded divergence: the clone keeps its batch146 运镜 menu); 特效 opens a screen-centered effects gallery (8 cards on source, 4 sampled) — clone implements the gallery overlay (data-effects-gallery, gradient thumbnails, hover 收藏, name/商用/author/credits, closes on outside mousedown) with verify-liblib-batch191.py (10 checks) |
| Batch 192 | Effect card click behavior (source screenshot): clicking a card closes the gallery and spawns a 素材 - 特效 - <名> node lower-left of the video node with an edge flowing INTO it (credits unchanged); clone implements via addNodeAtPosition + addEdge with explicit sourceHandle/targetHandle (the validator rejects missing handle direction — INVALID_HANDLE_DIRECTION); verify-liblib-batch192.py (5 checks) |
| Batch 193 | 参考/标记 pills stay click-inert with a typed prompt too (precondition still unfound — likely needs real reference content); verify-liblib-batch193.py (6 checks) pins the prompt-state inertness as a regression contract; zero code changes |
| Batch 194 | Material-precondition attempt failed again (effects-gallery card located off-viewport at y≈912) — new finding: the source gallery anchor is STATE-DEPENDENT (above the trigger yesterday, below it today), diverging from the clone's fixed bottom-[175px] centering; 参考/标记 inertness holds in all sampled states; zero code changes, divergence recorded |
| Batch 195 | Gallery anchor rule CLOSED by three-state sampling — the box is identical [177, 444, 1567, 235] regardless of trigger position: STATIC screen positioning (retracts Batch 194's state-dependent finding, a locator artifact); clone re-anchored to top-[444px] and portaled to document.body because fixed inside the React Flow transform subtree was hijacked (y=923 measured); verify-liblib-batch195.py (8 checks) |
| Batch 196 | Topnav + bottom-toolbar icons aligned to harvested libtv glyphs (ChromeIcons.tsx: workflow/layout-panel/panel-toggle/grid/map/link/magnet, paths verbatim); one mapping error caught and reverted (the two 12px topnav icons were dropdown chevrons, not the pill glyphs — Globe2/Link2 kept); verify-liblib-batch196.py (16 checks) |
| Batch 197 | Canvas dropdown chevron aligned to the harvested libtv glyph (12px, g transform translate(4.345 5.825), 133-char path) replacing lucide ChevronDown; the source's data-open rotate-180 semantics recorded as unsampled for the clone; verify-liblib-batch197.py (7 checks) |
| Batch 198 | Topnav right cluster aligned to harvested libtv glyphs (ChromeIcons.tsx: ShareNodesGlyph 0 0 14 14, MemberShopGlyph 0 0 16 16 replacing the ♦ placeholder, BoltGlyph 0 0 16 16, AgentFaceGlyph 0 0 17.58 14); first harvest was truncated at 500 chars and re-harvested in full; verify-liblib-batch198.py (12 checks) |
| Batch 199 | Agent drawer re-sampled (2026-09-08): a FOURTH skill headline 「Skill 就位，ready when you are」 added to the rotation (batch107 HEADLINES synced); the four-skill first batch matches the clone's batch97 record exactly; notification banner text already matches; drawer width reads ~427 at 1920 vs the clone's 340 — open question (single sample); verify-liblib-batch199.py (9 checks) |
| Batch 200 | Drawer width rule SOLVED (400px constant at 1920/1680/1440 — Batch 199's 427 was a measuring artifact) and Skill-card click behavior sampled (chip inserted into the input, drawer stays open, chip removable); clone widened 340→400 and implements the chip; verify-liblib-batch200.py (9 checks) |
| Batch 202 | Asset drawer re-sampled (2026-09-08): left sidebar measures ~280px wide (texts reach x≈270) with 画布/资产 tabs, 所有评级 filter and the verbatim empty/counter texts the clone already has — only the width aligned (w-60 → w-[280px]); verify-liblib-batch202.py (10 checks incl. tab toggling) |
| Batch 204 | After a page reload the asset drawer appears as a persistent left sidebar and 展示设置 becomes a node-type filter menu (180×369, ten options 全部/文本/…/脚本（旧版）matching the add-panel types) — clone implements the menu (data-asset-manager-typemenu) and batch102's hint assertions migrated; batch202's assets-tab assertions adjusted for the non-empty preset canvas |
| Batch 205 | Type filter menu wired to the node list (label→NodeFilter mapping incl. 智能剪辑/导演台/逐帧拉片/音频/脚本/脚本（旧版）); matchesFilter extended; trigger shows 展示设置 on 全部; dead hint state removed; verify-liblib-batch205.py (8 checks) |
| Batch 206 | Empty-canvas chip click sampled (evidence batch): the 故事脚本生成 chip creates a PAIR — a text node pre-filled with 剧本 markdown plus a new source node type script-v2 (350×350 脚本生成器, no edge); chip set varies per session (2 vs 4 chips); script-v2 implementation deferred (major new surface) |
| Batch 203 | 所有评级 filter menu implemented per the sampled source menu (180x225, six options 所有评级/1-5, verbatim labels); batch102's local-hint assertions migrated to menu-open assertions |
| Batch 201 | 换一批 real skill directory harvested — four batches (15 skills total, batch 3 has 3 cards) replacing the clone-shaped second-batch filler; ids from path slugs, thumbnails stay local placeholders; verify-liblib-batch201.py (7 checks incl. wrap-around) |
| Batch 189 | Ratio tile glyphs aligned to the sampled structure (17px centering box + 1.5px border-current rect with exact px dims per ratio); open question recorded — today's normal menu showed SEVEN tiles incl Auto (2.5 model day) vs Batch 175's six (2.0 day), model-dependency unconfirmed, clone grid unchanged |
| Batch 190 | Model-dependency hypothesis REJECTED by bidirectional sampling (2.5→2.0 switch with viewport override — both show seven tiles incl Auto in normal mode); ratio grid unified to seven tiles grid-cols-5 in both modes (Batch 176's long/normal split dropped); batch175/21 ratio assertions migrated; harness note — the model menu needs the CDP viewport override when the trigger sits near the viewport bottom edge |
| FrameOS Batch 157 | Context menu verified end-to-end (node: 复制/创建副本/删除, pane: add nodes, Esc close); BEHAVIORS.md stale ❌ row corrected to ✅; stable selectors data-frameos-context-menu/-item added |
| Batch 136 | Recycle bin selection: per-item checkboxes, 已选择 N 项 counter, batch restore button; empty state after restoring the only item |
| Batch 146b | Character filter 文化区域 options: 华语/日韩/欧美/东南亚 four regional chips (CLONE_DECISION) |
| Batch 146b | Character filter 文化区域 options: 华语/日韩/欧美/东南亚 four regional chips added to the filter panel (CLONE_DECISION) |
| Batch 126 | Inline advanced settings row in the video panel: 高级设置 label + three compact switch chips (联网搜索/自动校验素材/智能引用 AutoLink), superseded gear+popup removed |
| Batch 133 | FrameOS duplicate node insertion fix: Cmd+D now appends the copy to nodes with selection, undo/redo cycle, copy toast; breadcrumb useRef hygiene |
| Batch 134 | FrameOS copy/paste clipboard cycle: internal nodeClipboard synced by Cmd+C/X, Cmd+V pastes selected copy with history, writeText promise rejection handled |

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
