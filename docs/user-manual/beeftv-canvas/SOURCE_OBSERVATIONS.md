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

## 上游在途分支（不影响当前手册）

`codex/depth-action-video-preview`（深度动作捕捉 + 桌面更新，140 文件未合入 main）——监控中，合入后触发增量审计。
