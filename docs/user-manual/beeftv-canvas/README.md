# BeefTV 用户手册

> 适用版本：BeefTV `v1.5.9`（Web；界面文字取自源码与真实界面）。
> 面向读者：使用 BeefTV 进行 AI 视频/图片创作、时间线剪辑与导演台编排的普通用户、Agent 用户与管理员。
> 手册编写中——Batch 1 脚手架已就绪，章节按 [PROGRESS.md](PROGRESS.md) 的 batch 计划逐批发布。

## 这是什么

BeefTV 是一个「无限画布 + 时间线剪辑 + 三维导演台 + 云端 Agent」的 AI 影视创作工作台：

- **无限画布**：把提示词、参考素材、图片、视频、音频放在同一张画布上，连线组织「素材 → 生成」流程；
- **时间线剪辑**：把生成的片段拖上轨道剪辑，配字幕、导出成片；
- **导演台**：三维场景里摆机位、设运镜、录关键帧动画，一键渲染白膜视频；
- **云端 Agent**：用自然语言让 Agent 替你操作画布，关键操作需你审批。

## 阅读路线

| 阶段 | 页面 | 状态 |
|---|---|---|
| 快速开始 | [00-quickstart.md](00-quickstart.md) | ✍️ 编写中（Batch 2） |
| 任务指南（How-to，24 篇） | [10-tasks/](10-tasks/) | ✍️ 按 batch 逐篇发布 |
| 参考（快捷键/路由/端点） | [20-reference.md](20-reference.md) | ✍️ 编写中（Batch 5） |
| 概念解释 | [30-concepts.md](30-concepts.md) | ✍️ 编写中（Batch 9） |
| 故障排查 | [90-troubleshooting.md](90-troubleshooting.md) | ✍️ 编写中（Batch 9） |

## 任务清单与进度

- 任务账本（29 个候选任务，含角色/频率/影响/证据）：[task-inventory.yml](task-inventory.yml)
- Batch 计划与运行环境：[PROGRESS.md](PROGRESS.md)
- 证据索引（全部界面文字的来源）：[SOURCE_OBSERVATIONS.md](SOURCE_OBSERVATIONS.md)
- 回走审计：[AUDIT.md](AUDIT.md)

## 约定

- 界面文字（按钮、菜单、提示）均逐字取自 BeefTV 源码，不做翻译或改写；
- 生成类操作涉及云端渠道按量计费，相关页面有费用提示；
- 快捷键以 macOS 修饰键书写（⌘/⇧/⌥），Windows 对应 Ctrl/Shift/Alt。
