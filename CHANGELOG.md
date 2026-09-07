# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-07

### Added
See [Unreleased] below for the complete batch-by-batch record
(Batches 77-143: Director reliability series, LibTV canvas alignment
sampled 2026-09-05/06, /project page, recycle bin, video panel alignment,
FrameOS fixes, coverage matrix and regression sweeps).

## [Unreleased]

### Added
- Batches 77-96 (Director reliability series): canvas-viewport freshness,
  source runtime navigation audit, overlay/multi-zoom alignment, clipboard
  identity remap, whole-project duplicate, durable tombstones, strict V1
  import/export, session-local resource materialization, command feedback
  projection, project/session diagnostics, selection CRUD, transform context,
  restore selection, selection/timeline authority, scene camera discoverability,
  semantic commands, object/camera/group command boundary, local resource
  lifecycle, final desktop/mobile regression, focus containment, canvas-media
  ingress, multi-camera Shot workflow and authoring integrity. Gated by the
  Director current verifier manifest; see
  `docs/research/VERIFICATION_LEDGER.md`.
- Batches 114-119, 124-126 and 128 (LibTV canvas alignment, sampled
  2026-09-05/06): multi-canvas dropdown CRUD with row more-menu, delete
  confirm and creation-adjacent fallback; canvas double-click opens the add
  panel; shortcuts panel four-column alignment; empty-canvas quick chips;
  generation-history modal; asset drawer controls; top bar 工作流/故事板
  naming; storyboard three-section copy; collaboration follow banner; project
  menu; attempt chips driving settings linkage; inline advanced settings row.
  Evidence under `docs/research/liblib-canvas-batch1xx-2026-09-*`.
- /project list page with recycle bin: back/title/recycle/new-folder
  structure, create card, canvas cards navigating back, recycle panel with
  30-day copy, per-item restore, selection counter and batch restore
  (Batches 119, 124, 136).
- Character library modal tab chrome replicated (Batch 169, source
  2026-09-07): 公共角色库 / Seedance2.0&2.5合规素材库 tabs plus a local-only
  Seedance commitment gate on the 素材库 tab (both buttons are local state;
  the consent was NOT accepted on the user's behalf during sampling —
  不同意 was clicked to preserve the status quo)
- Bottom-left asset bar aligned to the sampled source geometry
  (Batch 171, 2026-09-07): items-end gap-2 container without a padding
  box, 资产管理 button and zoom chip both rounded-lg at 13px
- Canvas top bar workspace rename input (Batch 170, source 2026-09-07):
      13px inline input left of the canvas chip bound to projectName; store
      default renamed 未命名项目 -> 未命名工作区; batch16/17 migrated
- /project left sidebar added (Batch 168, source 2026-09-07 re-audit):
  240px sticky column with 新建项目, nav rows 首页/项目(active)/LibTV
  Agent/创作者挑战赛, and a bottom SD2.5 promo card + 帮助; unwired
  entries surface local placeholder status messages
- /project secondary surface alignment (Batch 167, source 2026-09-07
  re-audit): 回收站/新建文件夹 as filled secondary buttons, the create card
  restructured to an aspect-video cover + title row, canvas card covers
  aspect-video (~150px, card ~208px) with 14px medium titles; the
  character-library modal re-sample stays blocked (rAF throttle)
- Prompt textarea background/rounding removed and the 「3 个匹配」
  AutoLink popup chip deleted (Batch 166, source 2026-09-07): the sampled
  prompt region is a plain scroll area and the sampled toolbars contain
  only the five pills; the chip's advanced popup was already superseded
- Reference slot row aligned to the sampled source classes (Batch 165):
  flex-wrap, items-start, pl-1, no fixed row height (h-12 previously
  clipped the 55px slots); the 「Auto Link：」summary text removed as
  absent in every sampled panel state
- Footer trigger geometry aligned to the sampled source class strings
  (Batch 164): model trigger min-w-[88px] justify-between with 13px normal
  text, mode trigger justify-center pl-2 pr-2.5, params justify-between,
  footer row 32px without a top border; batch21 params-menu x offsets
  migrated +37
- Tablet breakpoints 768x1024 and 1024x768 verified after the panel
  growth (Batch 163): no page-level overflow, prompt intact, vertical
  clipping per the accepted canvas-clip contract; tablet phases and
  screenshots added to verify-liblib-batch161.py (now 20 checks)
- Mobile 390x844 breakpoint verified after the panel growth (Batch 162):
  no page-level overflow, the 397px panel stays vertically in-viewport and
  the prompt region stays intact; mobile phase + screenshot added to
  verify-liblib-batch161.py
- Video panel grown to 397px (Batch 161): the fixed 274px panel had been
  overflowing since the Batch 149 advanced column — prompt squeezed to 16px
  and the advanced section crossing the border by 35px; prompt restored to
  ~95px matching the source's 96px; measurement assertions added to
  prevent recurrence; batch21/22/26 height+offset assertions migrated
- 5分钟超长视频 chip selects the whole long-video mode (Batch 160, source
  full-panel dump: mode trigger 超长视频, credits 14700 = 300x49); reference
  slot row now renders only when references exist and the 「新功能」 bar is
  removed (both absent in the 2026-09-07 panel); batch21/22 offsets -24
- 尝试 suggestion chips moved into the video node card (Batch 159, source
  2026-09-07 geometry: vertical 36px pills below the preview, panel without
  an attempts row); attempt state lifted to VideoNode with the settings
  linkage applied via effect — 128/155 contracts preserved; batch21/22
  menu y-offsets migrated -32
- Default model reverted to Seedance 2.5 (Batch 158, controlled
  re-sample after page reload): fresh-node and attempt-node panels both
  show 2.5; the 2.0 sample was preset-carrier-specific; batch128's
  Auto+300s chip linkage confirmed on source; earlier one-time-gate and
  no-panel conclusions corrected (chips stay inside the node card beside
  the floating panel); batch149/22/33 assertions migrated back
- FrameOS context menu verified end-to-end (FrameOS Batch 157): node
  right-click offers 复制/创建副本/删除 and pane right-click adds nodes,
  Esc/outside close; BEHAVIORS.md gap table corrected (menu was already
  implemented); stable data-frameos-context-menu/-item selectors added
- batch93 mobile drawer-close clicks hardened (Batch 156): overlay click
  points moved outside the left tree drawer (x=320) and right inspector
  drawer (x=56), eliminating the intermittent tree-row/drawer intercept
  timeout; 3/3 stable runs, director 36/43/77 regression green
- 5分钟超长视频 attempt chip now switches the params duration range to
  30..300 with the long menu layout (Batch 155), fixing the broken
  half-state where a 300s value sat on a 4..30 slider; deselecting the
  chip clamps duration back to <=30 (CLONE_DECISION, source cancel
  linkage unsampled); credits formula unchanged
- Full regression sweep across all 124 verifiers (Batch 154): 112 pass,
  12 aged failures matching the documented Batch 108/131 list exactly,
  zero unexplained; batch124 recycle verifier migrated to the popup
  contract after the Batch 150 new-tab change; batch93 director mobile
  timing flake documented; verifiers must never run under `timeout`
  (Rosetta/PIL dlopen artifact)
- Evidence batch 153 (source 2026-09-07 round-3): Auto-ratio credits
  factor confirmed on a direct source data point (Auto/720P/5s/1 -> 230 =
  5x46), fresh video nodes show no generation panel, and the credits block
  classes match the Batch 151 implementation verbatim; docs/matrix updates
  only, no code change
- /project card sub-line shows date only (Batch 152, 2026-09-07 sample:
  title + date, no workspace prefix); surface coverage matrix refreshed with
  the Batch 149-152 re-sampling facts (credits 4th data point, rAF-gated
  menus, group-embedded panel)
- Video panel toolbar pills h-26 and credits block aligned to the
  2026-09-07 round-2 sample (Batch 151): min-w-[85px], right-aligned, muted
  gray; selection-bound panel confirmed, one-time 尝试 gate and rAF-gated
  menus recorded for future sampling
- /project canvas cards open the canvas in a new tab and add-node panel
  container aligned to the sampled source classes (Batch 150, 2026-09-07):
  rounded-2xl, backdrop-blur-[32px], hairline border; batch119 popup
  contract migrated
- Video panel advanced settings vertical column (Batch 149, source
  2026-09-07 re-sample): 高级设置 heading + three 36px rows with right-aligned
  switches, hidden in the long-video process view; default model moved to
  Seedance 2.0 VIP with abbreviated trigger display "2.0"; reference slots
  48x55 cursor-grab; continuation panel keeps 全能参考 trigger; batch21/22/33
  assertions migrated, batch21/22 menu y-offsets shifted -27.8
- Credits ratio factor calibrated on the 2026-09-06 data points
  (16:9→135, Auto→230 at 720P·5s·1个) (Batch 135).
- FrameOS duplicate node insertion and copy/paste clipboard cycle:
  Cmd+D appends the copy to nodes, Cmd+C/X sync an internal clipboard,
  Cmd+V pastes a selected copy with history (Batches 133-134).
- Research records: LibTV live audits (2026-09-05/06) covering the canvas
  shell, director desk, video generation panel rework, projects page and
  recycle bin; surface coverage matrix roadmap.
- Recycle bin selection and batch restore on the /project page:
  per-item checkboxes, 已选择 N 项 counter, batch restore button and empty
  state after restoring the only item (Batch 136).
- Topbar 积分超市 / 积分余额 split: two independent entries per the sampled
  source order (supermarket display-only, balance 100) (Batch 139).
- Docs: surface coverage matrix roadmap (Batches 118/137), source session
  degradation notes, credits data points (135@16:9 vs 230@Auto) and formula
  drift record (Batches 130/132).

### Fixed
- FrameOS duplicateNode now inserts the copy into nodes (previously the
  constructed copy was never added, so Cmd+D did not create a node)
  (Batch 133).
- Superseded AdvancedMenu popup removed from the video generation panel
  footer after the inline advanced settings row landed (Batch 126); footer
  geometry restored and parameter menu offsets migrated (Batches 21-22 via
  Batch 131 regression).
- Canvas dropdown CRUD assertions migrated to the sampled row structure
  (Batches 114/131).


### Added
- Closed Batch 76 Director owner reachability reconciliation: all-canvas live
  owner planning, one-time inactive source/canvas tombstones, two-phase active
  shell/session/runtime cleanup, idempotency, stale async completion, retained
  persistence and ordinary graph-history isolation. Added pure and fresh-page
  Playwright gates and reran Batch 59 plus Batch 67-76 serial regression with
  zero screenshots or browser diagnostics. Durable tombstones,
  storage/resource deletion and graph-undo restoration remain separate product
  decisions.
- Closed Batch 75 Director clipboard identity remap: project-scoped
  portable packet, object/group/track/path closure, two-pass IDs and references,
  camera detach/freeze, stable resource alias, deterministic offset, one-entry
  paste history, guarded `Cmd/Ctrl+C/V`, A-B-A owner isolation and reload
  non-persistence. System/cross-project clipboard, whole-project duplicate and
  real resource transfer remain outside scope.
- Closed Batch 74 with clone-owned Director browser-local durable project
  persistence: versioned storage envelope, strict V1 restore,
  owner/project/generation/fingerprint guards, stale-save rejection, corrupt
  payload preservation, runtime/UI/resource-byte exclusion and
  `SESSION_ONLY` storage-failure continuity. Cloud sync, ordinary canvas
  persistence, real resource materialization and source-exact LibTV persistence
  remain outside scope.
- Added Batch 73 Director async result authority:
  typed capture/export/phone operation and attempt identity, owner/session/
  generation and source/request freshness checks, stale/duplicate/invalid
  convergence, ordinary graph projection and exactly-once Blob URL resource
  transfer/release. Ordinary canvas async ingress and durable persistence remain
  separate implementation slices.
- Added Batch 72 Director reference-aware delete planning and resource closure:
  object/group/camera/track/path/capture/resource repair or block/cascade policy,
  last-camera protection, selection/runtime cleanup, exact delete/undo/redo and
  ordinary graph isolation. Added pure and fresh-page verification with stable
  structured audit output; inactive-owner reconciliation, async freshness,
  persistence, copy/paste identity remap and source-exact UI remain separate.
- Added Batch 70 Director project-local command/history kernel:
  typed command results, bounded `past/future`, no-op/rejection reasons,
  gesture coalescing, undo/redo, redo-future truncation and close/reopen
  history continuity. Added pure and fresh-page Playwright verification with
  zero console/page/request errors; reference-aware delete, async freshness and
  persistence remain separate slices.
- Added Batch 69 Director authored/runtime projection separation:
  `authoredObjects` is now the portable project baseline while the existing
  `objects` selector is derived for timeline/path/R3F runtime state. Added pure
  and Playwright fingerprint-stability verification for seek, playback, path
  sampling, authoring restore, close/reopen and owner isolation.
- Added Batch 68 Director owner registry and session lifecycle with structured
  route/canvas/source ownership, per-owner project records, fresh session
  generations, A/B and cross-canvas isolation, memory-only capture sidecars and
  a pure plus Playwright verifier.
- Added Batch 67 Director Project Document V1 with strict
  decode/normalize/encode, an explicit current-state snapshot adapter and a
  dependency-free 17-case contract verifier; project registry, persistence and
  Director history remain separate later slices.
- Closed Batch 65 with per-canvas responsive viewport ownership: demo
  desktop/mobile presets now remain bootstrap-only, user/stored viewports survive
  breakpoint and canvas switches, and stale/invalid callbacks are zero-mutation.
- Closed Batch 64 with page-owned Asset drawer host-resize reconciliation:
  toolbar toggle, explicit close and Canvas-context transition preserve the old
  host-center flow anchor across desktop/mobile layout changes without graph,
  selection or history mutation.
- Closed Batch 63 with actual React Flow host-centered default placement for
  Add Node and Character Library, including finite conversion helpers, page-owned
  current-instance routing and focused desktop/mobile runtime evidence.
- Closed Batch 48 with a browser-local Director `我的模型` workflow:
  multiple FBX/OBJ descriptor import, localStorage refresh recovery,
  repeated proxy insertion and linked-instance cleanup.
- Added the Batch 48 Playwright verifier, one-time screenshot ledger and
  maturity assessment; real mesh loading and remote persistence remain outside
  the prototype contract.
- Closed Batch 53 with a source-backed empty image annotate replacement:
  node-local DPR2 canvas, `536x49` tool surface, source-shaped tool/color/line-width
  controls, empty undo/redo disabled state, and enabled no-op save.
- Closed Batch 54 with a source-backed empty image element-edit replacement:
  node-local masked stage, `272x44` tool surface, `400x50` empty record panel,
  point/box/brush and brush-size controls, empty undo/generate disabled state,
  and keyboard/graph isolation.
- Closed Batch 56 with a bounded image rotate graph slice: media-gated
  `旋转` entry, `旋转与镜像` derived image node, source edge, typed
  `rotateMirror` metadata, selected-create state and atomic undo/redo; real
  bitmap rotation and editor/save semantics remain fixture-gated.

### Documentation
- Migrated the self-contained `.agents/skills/project-docs` package into this repository
- Added the documentation hub and agent-facing guides for architecture, development, layers, quality, verification and terminology
- Added research, design-reference, draft and archive indexes so source evidence and implementation history remain discoverable
- Reworked `README.md`, `AGENTS.md` and `CONTRIBUTING.md` around the LibTV + FrameOS canvas prototype
- Added `npm run docs:check` to validate local Markdown links
- Recorded the fixed upstream director-desk archaeology, the current LibTV
  director evidence boundary and the implemented R3F workspace verification.
- Added LibTV UI state hierarchy, Open Canvas pattern cards, Seedance dependency
  risk queue and the research go/no-go authorization gate.
- Added agent task navigation, cross-project decision register, claim
  traceability matrix, verifier maturity ledger and clone-website project
  adaptation guidance.
- Audited documentation freshness and corrected Batch verifier ranges, while
  explicitly retaining Batch 34 and the parallel Batch 45 work as unverified.
- Added a source-component contract coverage matrix that distinguishes dedicated
  specs, parent/domain contracts, batch-only evidence, missing contracts,
  legacy helpers and parallel WIP.
- Added a documentation lifecycle and supersession register, retaining dated
  source snapshots and Batch contracts while making current authority explicit.
- Added dedicated Toolbox, Character Library, History and Smart Matting component
  contracts that separate source evidence from local mock behavior and graph
  side effects.
- Synchronized formal documentation with the stable Batch 45 verifier and moved
  the explicit parallel-WIP boundary to Batch 46.
- Added the stable StoryboardBoard projection/mode contract and corrected
  ScriptHeader documentation to reflect that it is an unmounted legacy prototype.
- Added a KeyboardShortcutsDialog contract that records the source/clone command
  delta and separates help text from actual keyboard-handler coverage.
- Added a LibTV shortcut runtime crosswalk that separates source-advertised
  commands, clone help rows, global handlers, React Flow gestures, local context
  precedence and graph/history side effects.
- Added a LibTV graph transaction catalog covering route event compression,
  store actions, node/edge/selection deltas, atomic history, evidence maturity
  and known transaction risks.
- Synchronized formal documentation with the stable Batch 46 verifier and
  moved the explicit parallel-WIP boundary to Batch 47.
- Added a LibTV UI overlay runtime catalog covering actual store authority,
  mount owners, per-surface close paths, keyboard/Director boundaries,
  node-relative anchoring strategies and unmounted compatibility state.
- Synchronized formal documentation with the stable Batch 47 model-library
  verifier and Batch 35-47 serial regression.
- Moved the explicit parallel-WIP documentation boundary to the planned Batch
  48 local model-library persistence slice.
- Added a current LibTV UI/UX parity backlog with stable gap IDs, evidence and
  verification readiness, risk, dependencies, authorization gates, fixture
  blockers and explicit prototype/out-of-scope boundaries.
- Added Batch 53 source evidence, screenshot ledger, component contract,
  runtime audit and implementation closeout documentation.
- Added Batch 54 source evidence, screenshot ledger, component contracts,
  runtime audit and implementation closeout documentation.
- Added Batch 56 source evidence, screenshot ledger, focused verifier,
  runtime audit and bounded rotate implementation closeout documentation.

### Fixed
- Restored the complete Asset/edge/snap/zoom secondary toolbar after adjacent
  regression exposed hidden zoom and broken minimap follow; collision avoidance
  now clamps only the screen-space primary toolbar and leaves graph anchoring
  unchanged.
- Kept the Asset drawer open across Add Node and primary-panel workflows, centered
  the primary toolbar in the remaining desktop host and compacted conflicting
  secondary controls so drawer-open node creation remains reachable.
- Updated the selected-image toolbar to the current source-shaped 13-action
  contract (`1092.5x49`), separating Preview from graph-mutating actions and
  keeping unsupported high-risk actions visibly bounded instead of guessing
  their side effects.
- Added a page-level read-only image Preview overlay with intrinsic-ratio media,
  watermark/close geometry, Escape/Tab focus boundaries and unchanged graph,
  selection and Prompt state.
- Added a media-gated image rotate entry that creates a source-linked local
  prototype node named `旋转与镜像`; the prototype records source identity
  without pretending to rotate the bitmap.
- Aligned the selected-image toolbar's top host with the source-confirmed
  `10 + 24 * zoom` geometry while preserving the node-centered inverse-scaled
  bottom editor; Batch 51 records the focused clone verification and keeps the
  older toolbar action set explicitly separate from the current source contract.

### Verification
- Added Batch 52 focused Playwright/runtime-audit coverage for the current image
  action set and Preview at desktop/mobile viewports; Batch 10 and Batch 11
  adjacent regressions also pass.
- Added Batch 53 focused Playwright/runtime-audit coverage for empty image
  annotate replacement at desktop/mobile viewports; Batch 52, Batch 10 and
  Batch 11 adjacent regressions remain covered.
- Added Batch 54 focused Playwright/runtime-audit coverage for empty image
  element-edit replacement at desktop/mobile viewports; Batch 53, Batch 52,
  Batch 10 and Batch 11 adjacent regressions remain covered.
- Added Batch 56 focused Playwright/runtime-audit coverage for the bounded image
  rotate graph slice at desktop/mobile viewports, including no-media disabled
  behavior and atomic undo/redo.
- Centralized LibTV top-level overlay lifecycle and added Batch 11 Playwright coverage for mutual exclusion, Escape cleanup and storyboard Agent transitions
- Completed the LibTV asset manager's canvas/assets tab behavior and local media-node selection flow
- Bound LibTV storyboard mode to the active canvas and aligned its key-elements/storyboard column structure with the source evidence
- Aligned the LibTV Agent/share surfaces with source evidence and fixed top-nav pointer/layer conflicts that made their commands unreachable
- Corrected the LibTV add-node menu so 音频 creates an audio node and 素材库 opens a material submenu instead of creating unrelated node types
- Closed the LibTV canvas dropdown after project/canvas navigation actions and made Escape/outside-click cleanup deterministic
- Removed the hard-coded asset drawer canvas label and fixed canvas/assets empty-state semantics
- Moved the LibTV zoom menu into the unified overlay lifecycle so Escape, outside clicks and other panels clean it up
- Moved the LibTV minimap from React Flow's default bottom-right to the source toolbar-anchored position
- Replaced the guessed LibTV panorama action that copied source media with a source-backed empty `720°全景图` node, edge and specialized panel
- Replaced compact Seedance parameter pills with source-sized normal and long-video dialogs
- Replaced the guessed four-item Seedance model menu with the seven source-visible rows and selected-only descriptions
- Replaced the guessed segment-reshoot title panel with a source-shaped filmstrip and tokenized Prompt editor
- Replaced the guessed smart-continuation reshoot branch with the source-backed two-stage range-selector and target-node workflow
- Replaced the subtitle dropdown's temporary feedback with source-backed smart/region panels, multi-rectangle editing and a pending target graph transaction
- Replaced the guessed audio menu and temporary feedback with the current three-item audio-split menu, trigger-relative popover, observable busy state and dual-output graph transaction
- Replaced the guessed long-video four-card panel preview with a source-linked pending process graph, request metadata, repeated-batch avoidance and atomic undo/redo

### Changed
- Raised the project Node.js baseline to 24 across local development, CI, Docker, and contributor-facing documentation
- Added the source-shaped 9-entry add-node menu, conservative audio preview node, and local upload/history feedback
- Moved the LibTV project name into `canvasStore` and rebuilt the canvas dropdown around the source project/canvas hierarchy
- Rebuilt the LibTV asset drawer around source project/canvas context, node hierarchy and local sort/filter/search controls
- Rebuilt the LibTV zoom menu around the source percent row and six viewport commands, removing the unsupported grid entry
- Calibrated the LibTV minimap panel, node blocks, viewport outline, asset-drawer follow and compact-toolbar avoidance
- Extended LibTV derived-node creation with optional dimensions and world offsets while preserving existing caller defaults
- Added Batch 20 panorama Playwright coverage for geometry, panel anchoring, history transactions and responsive clipping
- Added source-shaped ratio cards, duration value controls, audio/count segments and Batch 21 parameter-dialog coverage
- Aligned the Seedance model popover to `380x410`, added premium/estimate hierarchy and Batch 22 model-menu coverage
- Added Batch 23 coverage for 4-second range selection, five-range cap, prompt tokens and empty-intent whole-video rerun
- Added Batch 26 coverage for continuation range constraints, graph transactions, target Prompt state, clear behavior and responsive anchoring
- Added Batch 27 coverage for subtitle mode handoff, rectangle history, request metadata, target/edge lifecycle and responsive anchoring
- Added Batch 28 coverage for AV/vocals/background output naming, metadata, direct source-edge topology, selection, atomic history and responsive clipping
- Replaced the guessed static script-execution card with a lazy-loaded real R3F
  director workspace, camera framing, helper-free capture and atomic canvas return.
- Extended the director timeline with preset and freehand motion paths,
  serializable editable anchors/Bezier handles, deterministic arc-length
  playback, source-labeled path controls and responsive Inspector authoring.
- Added fixed-pivot path-level position/rotation/scale, inverse world-anchor
  commits and distinct offset/full reset workflows while preserving serializable
  local geometry and helper-free capture.
- Added source-labeled director animation export settings and real cropped WebGL
  recording through browser `MediaRecorder`, with playable ratio-shaped WebM
  video return, direct source edges and atomic undo/redo.

> Releases `0.1.0` through `0.3.1` below are inherited template history. Their original upstream links are retained for provenance; current project development is tracked from this point in `wubuku/liblib-tv`.

## [0.3.1] - 2026-03-29

### Fixed
- `sync-agent-rules.sh` failing to resolve `@file` imports on Windows due to CRLF line endings — platform instruction files now correctly inline the Inspection Guide content

## [0.3.0] - 2026-03-29

### Added
- Multi-URL support for `/clone-website` — clone multiple sites in a single command with parallel processing and isolated output
- CI quality gates via GitHub Actions — automated lint, typecheck, and build on every push and PR
- `npm run typecheck` and `npm run check` scripts for local quality validation
- `.gitattributes` for cross-platform line ending normalization
- `.nvmrc` to pin Node.js 20 for contributor consistency

### Changed
- Streamlined PR template — removed redundant checklist items and screenshots section
- Improved project description and README — clearer use cases, limitations, and modern wording
- Refined documentation and agent rules across all platforms for clarity and consistency
- Fixed CRLF handling in `sync-skills.mjs` for reliable Windows operation

### Removed
- Outdated use case from README documentation

## [0.2.0] - 2026-03-28

### Added
- Multi-platform AI agent support: Claude Code, Codex CLI, OpenCode, GitHub Copilot, Cursor, Windsurf, Gemini CLI, Cline/Roo Code, Continue, Amazon Q, Augment Code, Aider
- Platform-specific instruction files and `/clone-website` skill for each supported agent
- `scripts/sync-agent-rules.sh` to regenerate platform instruction files from AGENTS.md
- `scripts/sync-skills.mjs` to regenerate `/clone-website` skill across all platforms
- GEMINI.md for Gemini CLI configuration
- Supported Platforms table in README
- "Updating for Other Platforms" documentation section in README

### Changed
- README now describes the project as multi-agent (Claude Code recommended, not required)
- AGENTS.md updated with sync script reminders

## [0.1.1] - 2026-03-28

### Added
- Bug report and feature request issue templates
- Pull request template with checklist
- CHANGELOG.md following Keep a Changelog format
- Package.json metadata (description, repository, homepage, keywords, engines)

### Fixed
- LICENSE copyright holder now attributed to JCodesMore

## [0.1.0] - 2026-03-28

### Added
- Initial template scaffold for website reverse-engineering with Claude Code
- `/clone-website` skill for full-site cloning pipeline
- `/build-from-spec` and `/customize` skills
- Parallel builder agents with git worktree isolation
- Chrome MCP integration for design token extraction
- Comprehensive inspection guide and project structure documentation
- Next.js 16 + shadcn/ui + Tailwind CSS v4 base scaffold
- MIT license
- README with badges, demo section, quick start, and star history

[Unreleased]: https://github.com/JCodesMore/ai-website-cloner-template/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/JCodesMore/ai-website-cloner-template/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/JCodesMore/ai-website-cloner-template/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JCodesMore/ai-website-cloner-template/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/JCodesMore/ai-website-cloner-template/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JCodesMore/ai-website-cloner-template/releases/tag/v0.1.0

## 2026-07-07 — FrameOS 复刻 / 打磨阶段

### Added
- **`FrameosNodeTooltip`** — hover 节点时显示节点标题 + 缩略图
- **`FrameosToast`** — 操作反馈 (撤销/重做/复制/删除时显示)
- **`FrameosContextMenu`** — 节点 / 画布右键菜单 (复制节点 / 删除节点 / 添加 3 种节点 / 适应画布)
- **`FrameosNodeEditPanel` (DEBUG-only)** — 节点详情面板，仅 DEBUG 模式可见（原站没有，是我加的开发者便利）
- **`FrameosDebugToggle`** — 右下角 DEBUG 开关
- **`FrameosEdge`** — FrameOS 专用边：蓝色虚线 (`rgba(59,130,246,0.42)`, 7,5 dasharray) + hover 变实线 + flowing pulse 复用 liblib 的 `DeletableEdge` 行为
- **@-mention asset picker** — PromptBar 输入 @ 弹出素材列表
- **E2E 测试** (`e2e/frameos.spec.ts`) — 6 个 Playwright 测试用例
- **完整 keyboard shortcuts** — Esc / Delete / Cmd+Z / Cmd+Shift+Z / Cmd+D / ? / + / - / 0
- **History stack (undo/redo)** — `past` + `future` 数组，最多 20 步
- **`updateNodeData` action** — 节点数据更新
- **`isDebugMode` toggle** — 隔离开发者便利功能

### Fixed
- **PromptBar / EditPanel / NodeToolbar 距离 bug** — 用 `useViewport()` 拿 pan + zoom，用 `position: fixed` 定位 + `transition: left 0.15s` 平滑跟随
- **节点选中态 handle 显示** — `selectNode` 同步 `selected: true` 到 nodes array
- **节点选中态视觉** — 移除错误的 box-shadow，handle 用 16×16 深底白边圆形 + `translate(8px, -8px)` 偏移
- **node-card 背景** — 从错误的 #1C1C1C 改为 transparent
- **边样式** — 从灰色实线改为蓝色虚线

### Documentation
- `docs/README.md` — 顶层入口，更新 FrameOS Canvas 表格 + Known Limitations
- `docs/research/frameos/IMPLEMENTATION.md` (new) — 设计决策 + 状态机 + 共享组件说明
- `docs/research/frameos/COMPONENT_INVENTORY.md` — 重写
- `docs/research/frameos/BEHAVIORS.md` — 重写
- `docs/research/frameos/RUNBOOK.md` (new) — 开发者操作手册
- `AGENTS.md` — 项目 red lines + 文档入口
