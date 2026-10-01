# BeefTV 用户手册 · 源码观察账本（证据索引）

> 本手册的界面文字、流程步骤与行为描述的**证据基座**。每个正式断言都可回溯到以下证据之一。

## 主证据：调研包（702 处断言抽查 100% 吻合）

位置：`docs/research/beeftv-canvas-2026-09-27/`（锁定提交 `85c9686`/v1.5.7）

| 文件 | 内容 | 手册用途 |
|---|---|---|
| SOURCE_ANALYSIS.md | 35 章模块级源码证据（视口/状态/节点/连线/生成管线/Agent/导演台/时间线/插件/后端）+ §32 交叉校验台账 689 行 | 章节正文的行为依据 |
| INTERACTION_CATALOG.md | 交互目录 10 节（视口手势/工具/选择/连线/生命周期/右键/生成流/周边/快捷键/LibTV 对照） | how-to 步骤来源 |
| PATTERN_CARDS.md | 45 张模式卡 | 概念章素材 |
| ITERATION_LOG.md | 128 轮迭代史与覆盖面登记 | 证据强度标定 |
| ADOPTION_DECISION_MATRIX.md | 44 项机制采纳决策 | 不直接用于手册 |

## 证据等级约定

- **static（静态源码）**：UI 标签/文案/端点/常量逐字取自源码字符串。标注为 `static` 的步骤在 Batch 10 本地起服后升级为 `runtime`。
- **runtime（运行时取证）**：本地 vite :3000 + Go server 实际走查 + 截图（Batch 10 起）。
- **inference（推断）**：仅用于概念解释，不进入操作步骤。

## 与手册目标版本的差异（v1.5.7 → v1.5.9）

- v1.5.8：工作区和画布支持**浅色模式**（三主题：浅/深/自定义）；画布外观面板入口恢复。
- v1.5.9：视频生成**素材限制校验与错误提示**对齐（video-validation +90 行、generation-error +98 行、后端 16 文件同主题）。
- 涉及章节：organize-canvas（外观）、generate-video（素材限制）、90-troubleshooting（错误文案）。

## v1.5.9 → v1.6.6 增量审计（Batch 9，2026-09-29）

上游发布 v1.6.6（9 提交 / 205 文件 / +6953−10507，含 depth-action 分支合入）：
- v1.6.0：深度动作捕捉 + 稳定视频预览合入；旧桌面 Agent 退场（v1.6.2 架构收敛）；
- v1.6.1：审核/版权/额度失败分类精确化（moderation_input/moderation_reference/quota_limit 等）；
- v1.6.3-6.6：Seedance 2.5 任务模式约束、参考能力保留、轮询错误码保留（新增官方页 seedance-task-constraints.mdx）；
- 新后端域：`backend/internal/depthruntime`（深度素材服务端拉取与校验）。
手册已回写：generate-video（任务模式/三层限制/TaskTypeConstraint）、90-troubleshooting（审核/额度/路由三类）、local-runtime（后端 depthruntime 注记）、README 版本行。
截图摄于 v1.5.7 构建；v1.6.x 界面差异（视频参数/错误文案）已用文字标注，下一轮重摄时更新。

## v1.6.16 取证对象说明（Batch 130 起持续适用）

BeefTV 工作区当前是 **detached HEAD `@852961a`（v1.6.14）**，而手册声明适用 **v1.6.16（`3a74793`）**。
取证一律**读 `origin/main` 的对象**（`git show <rev>:<path>`、`git grep <rev>`），不读工作树——
闸门脚本与本批全部源码结论均如此。Batch 130 曾逐文件比对确认所依赖的文件在两版间**逐字节相同**；
若某批依赖的文件在两版间有差异，须在该批账本写明，不能默认相等。

## Batch 135 新增证据锚点（只读画布 / 画布副本）

| 断言 | 证据 | 位置 |
|---|---|---|
| 只读判定与两种等价写法 | static | `web/src/pages/canvas/project.tsx:262` |
| 只读透传到画布容器与顶栏 | static | 同上 `:2847`、`:2873`、`:2894`、`:2958`、`:3112` |
| `interactive=false` 关掉缩放/平移/框选/快捷键/视口持久化 | static | `web/src/components/canvas/infinite-canvas.tsx:74,120,152,234,324,406` |
| 只读顶栏两种样式（普通 / LibTV chrome 多一个 ✕） | static | `web/src/pages/canvas/canvas-project-top-bar.tsx:140-157,335-343` |
| 十个 fixture 在只读下一律不注入 | static | `web/src/pages/canvas/project.tsx:527-698`（每条 effect 开头含 `readOnly`） |
| 只读入口零产出（无任何界面动作能生成只读网址） | static | 全库零处写入 `readonly` / `mode=readonly`；由 `verify-unreachable.py` 的 `canvas-readonly-no-ui-entry` 持续盯住 |
| 副本不上传：三条复制路径两条走 `importProject` | static | `project.tsx:700-718`、`:731-757`；`use-canvas-store.ts:553`（纯 set，无网络） |
| 对照组确实上传 | static | `services/local-workspace-repository.ts` 的 `createLocalCanvasProject` 含 `await syncLocalCanvasProjectToBackend(id)` |
| 两种写法的界面表现、编辑坞/空态消失 | **runtime** | v1.6.14 dev :3001，外部无头 Playwright 1440×900，截图 54/55 |
| 库内「创建副本」后端列表新增 vs 顶栏「复制画布」写请求数 0 | **runtime** | 同上，截图 56；`?stay=1` 保留在库内以便连续观测 |

## Batch 136 新增证据锚点（画布改名 / 两个名字）

| 断言 | 证据 | 位置 |
|---|---|---|
| 顶栏切换器读 `canvasTitle`，为空回落「画布 N」 | static | `web/src/pages/canvas/project.tsx:290-295`（`canvasProjects` useMemo 映射） |
| 顶栏标签消费该映射 | static | `web/src/pages/canvas/canvas-project-top-bar.tsx:105,270,294` |
| 画布库卡片读 `title` | static | `web/src/components/canvas/canvas-folder-card.tsx:119,141` |
| 顶栏改名写 `canvasTitle`，无后端同步 | static | `web/src/pages/canvas/project.tsx:725-729`（`renameCanvasFromMenu`） |
| 库内改名写 `title`，无后端同步 | static | `web/src/components/canvas/canvas-folder-card.tsx:71-79`（`saveTitle`） |
| 对照组确实带同步 | static | `web/src/services/local-workspace-repository.ts:91`（`createLocalCanvasProject`） |
| 正常保存才带同步 | static | `web/src/pages/canvas/use-canvas-project-lifecycle.ts:367`、`:285`（500ms 防抖调度） |
| 顶栏同时并存两个名字 | **runtime** | v1.6.14 dev :3001，外部无头 Playwright 1440×900，截图 57 |
| 两种改名瞬间写请求 0；库内改名可被后续内容保存带上、顶栏改名带不上 | **runtime** | 同上，观测 `/api/canvas-projects` 的 PUT/POST/PATCH |

