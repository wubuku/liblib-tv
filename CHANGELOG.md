# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
