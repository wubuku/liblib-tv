# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Raised the project Node.js baseline to 24 across local development, CI, Docker, and contributor-facing documentation

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
