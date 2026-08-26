# 当前项目文档体系整理计划

> 建档日期：2026-08-25
> 目的：将 `project-docs` 技能包移植到本项目，并把已有文档、代码、功能整理成开发者与 agents 可渐进发现的体系。
> 原则：不删除原站证据和实施历史；先建立稳定导航层，再把现有资料挂接到正确的生命周期和主题入口。

## 1. 当前审计

### 已有资产

- `AGENTS.md`：包含重要工程红线，但同时承担了过多架构说明。
- `README.md`：仍是通用 website-cloner 模板首页，不能准确描述当前 LibTV + FrameOS 原型。
- `docs/README.md`：已有丰富导航，但文件名和层级不符合移植技能定义的 `docs/index.md` 入口。
- `docs/BIG_PICTURE.md`：已有架构总览，是最重要的知识资产。
- `docs/research/`：包含原站审计、组件规格、FrameOS 资料和 Batch 3-10 实施历史。
- `CHANGELOG.md`：混合了上游模板历史和本项目 FrameOS 迭代记录。
- `.codex/skills/` / `.claude/skills/`：已有 `clone-website` 技能同步机制。

> 维护说明（2026-08-26）：本节是 2026-08-25 文档体系迁移时的审计快照；Batch 研究已继续推进到 Batch 45，当前验证脚本实际覆盖 Batch 4-33、35-44。现状漂移与修正记录见 [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md)，当前指引与历史合同的替代关系见 [`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md)。

### 主要缺口

| 优先级 | 缺口 | 影响 |
|---|---|---|
| P0 | 项目 README 仍介绍模板而非当前产品 | 人和 agents 会误判项目目标 |
| P0 | 没有明确的统一 `docs/index.md` | 文档发现依赖记忆或搜索 |
| P0 | AGENTS 不是“地图”，而是规则、架构和历史的混合体 | agents 进入项目成本高 |
| P1 | 缺少 Architecture / Development / Layers / Quality / Harness / Glossary | 修改影响面、验证路径和术语不够明确 |
| P1 | `docs/research/` 没有自己的导航入口 | 原站事实、组件规格、批次历史难以按主题发现 |
| P1 | 截图资产没有索引和复用说明 | 容易重复识图或误用过期截图 |
| P2 | 缺少 drafts/archive 生命周期入口 | 新计划与历史记录容易继续散落 |
| P2 | 缺少项目贡献指南 | 提交、验证、文档维护规则不集中 |

## 2. 目标结构

```text
AGENTS.md                 AI agent 入口，≤120 行，只保留地图和硬约束
README.md                 人类首页，≤200 行，准确说明项目和启动方式
CONTRIBUTING.md           开发/提交/文档维护约定
.agents/skills/project-docs/
                          自包含项目文档技能包
docs/
├── index.md              统一文档 Hub
├── ARCHITECTURE.md       两条路线、状态流、边界与关键决策
├── DEVELOPMENT.md        安装、启动、常用开发路径
├── LAYERS.md             代码层次和依赖边界
├── QUALITY.md            工程红线、证据纪律、编码质量
├── HARNESS.md            验证命令、浏览器验证和截图台账规则
├── GLOSSARY.md           LibTV / FrameOS / React Flow 术语
├── BIG_PICTURE.md        详细系统认知（保留并作为 Architecture 深读材料）
├── research/README.md    原站研究、组件规格、批次和原始证据入口
├── design-references/README.md
├── drafts/README.md
└── archive/README.md
```

## 3. 实施批次

### Batch A：技能迁移与计划落档

- 复制完整 `.agents/skills/project-docs/`，保持 `SKILL.md`、`references/` 自包含；
- 本计划先落档；
- 迁移结果写入文档体系索引。

### Batch B：P0 导航层

- 重写根 `README.md`；
- 将 `AGENTS.md` 收敛为 agent 导航地图，保留不可违反的工程红线；
- 新增 `CONTRIBUTING.md`；
- 添加 `docs/index.md`，并让 `docs/README.md` 成为兼容入口。

### Batch C：P1 指南层

- 新增 `ARCHITECTURE.md`、`DEVELOPMENT.md`、`LAYERS.md`、`QUALITY.md`、`HARNESS.md`、`GLOSSARY.md`；
- 不复制大段历史内容，使用链接指向已有详细研究。

### Batch D：Reference / lifecycle 入口

- 新增 `docs/research/README.md`；
- 新增 `docs/design-references/README.md`；
- 新增 `docs/drafts/README.md`、`docs/archive/README.md`；
- 在索引中明确当前文档、研究证据、实施历史和过期资料的区别。

### Batch E：验证与维护

- 检查所有新增/修改文档的相对链接；
- 检查命令与当前 `package.json`、脚本一致；
- 运行 `npm run check`；
- 记录迁移和整理结果，commit/push。

## 4. 不做

- 不移动或重命名现有 Batch 研究目录；
- 不把原站观察、推断和 clone 决策混写；
- 不为了“模板完整”创建不存在的 REST API、数据库或部署文档；
- 不把历史截图重新识别一遍；
- 不修改产品代码行为。

## 5. 验收标准

- 新 agent 从 `AGENTS.md` 能在 2 次跳转内找到架构、开发、质量和验证文档；
- 人类从根 `README.md` 能在 3 次跳转内找到两条路线、运行地址、研究入口和已知边界；
- `docs/index.md` 覆盖所有正式 P1 文档、研究入口、生命周期入口；
- `docs/research/README.md` 覆盖两条路线、组件规格、Batch 3-45、原站审计和 Seedance 研究；专项 verifier 的实际范围另见 [`docs/HARNESS.md`](HARNESS.md)。
- 技能包不依赖源目录或机器外文件；
- 文档相对链接无死链；
- `npm run check` 通过；
- 整理历史可通过 Git commit 追踪。

## 6. 实施结果

> 状态：已完成（2026-08-25）。

### 已交付

- `.agents/skills/project-docs/` 已从外部工作区完整移植；`SKILL.md` 和两个 reference 文件与源包逐文件一致，技能包不依赖源工作区。
- 根入口已重写为当前 LibTV + FrameOS 原型，`AGENTS.md` 已收敛为 agent 导航地图，并通过 `scripts/sync-agent-rules.sh` 同步平台规则副本。
- 已补齐 `CONTRIBUTING.md`、`docs/index.md`、P1 指南、研究入口、截图台账入口和 drafts/archive 生命周期入口。
- `docs/README.md` 保留为兼容入口；现有研究批次、原站证据、Seedance 背景和 `BIG_PICTURE.md` 均未删除或重命名。
- package 元数据已对齐 `wubuku/liblib-tv`；上游模板版本历史和许可证归属仍保留并明确标注 provenance。
- `scripts/verify-docs.py` 已支持仓库根基准的同步 agent 规则副本，并通过 `npm run docs:check`。

### 验证记录

| 检查 | 结果 |
|---|---|
| `npm run docs:check` | 通过：114 个 Markdown 文件，226 个本地目标 |
| `npm run check` | 通过：lint、typecheck、production build 均成功 |
| `git diff --check` | 通过 |
| 技能包逐文件 `cmp` | 通过 |

`npm run lint` 当前仍报告 9 个既有 warning、0 个 error；本批仅修正文档和元数据，没有借机修改无关产品代码。Next.js build 仍会提示工作区上层存在额外 lockfile，但构建成功。

### 接力规则

后续 agent 从 [`docs/index.md`](index.md) 开始；需要改代码时先读 [`AGENTS.md`](../AGENTS.md)、[`ARCHITECTURE.md`](ARCHITECTURE.md) 和对应研究规格。新增截图先查现有 `SCREENSHOT_ANALYSIS.md`，新增正式文档同步更新本页、`docs/index.md` 和必要的研究入口。
