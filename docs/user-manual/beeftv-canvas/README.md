# BeefTV 用户手册

> 适用版本：BeefTV `v1.6.6`（Web 与桌面端；界面文字取自源码与真实界面。v1.6.x 主要变化：Seedance 任务模式与素材限制对齐、生成失败分类精确化、旧桌面 Agent 退场、深度动作捕捉工具）。
> 面向读者：使用 BeefTV 进行 AI 视频/图片创作、时间线剪辑与导演台编排的普通用户、Agent 用户与管理员。
> 全部章节已发布（Gate A / Gate B / --phase final 审计通过）；可浏览站点由 `./build-site.sh` 构建到 `.vitepress/dist/`。

## 这是什么

BeefTV 是一个「无限画布 + 时间线剪辑 + 三维导演台 + 云端 Agent」的 AI 影视创作工作台：

- **无限画布**：把提示词、参考素材、图片、视频、音频放在同一张画布上，连线组织「素材 → 生成」流程；
- **时间线剪辑**：把生成的片段拖上轨道剪辑，配字幕、导出成片；
- **导演台**：三维场景里摆机位、设运镜、录关键帧动画，一键渲染白膜视频；
- **云端 Agent**：用自然语言让 Agent 替你操作画布，关键操作需你审批。

## 阅读路线

| 阶段 | 页面 |
|---|---|
| 快速开始 | [00-quickstart.md](00-quickstart.md) |
| 任务指南（How-to） | create-nodes / navigate-canvas / upload-materials / connect-references / prompts-and-mentions / generate-images / generate-video / media-versions / undo-history-versions / organize-canvas / shortcuts-help / timeline-editing / subtitle-highlights / timeline-export / director-basics / director-keyframes-record / director-rig-bones / cloud-agent / agent-memory-skills / plugins-management / local-runtime（均位于 10-tasks/） |
| 参考（快捷键/路由/端点） | [20-reference.md](20-reference.md) |
| 概念解释 | [30-concepts.md](30-concepts.md) |
| 故障排查 | [90-troubleshooting.md](90-troubleshooting.md) |

## 任务清单与进度

编写账本（任务清单/Batch 计划/回走审计/证据索引）保存在本目录：`task-inventory.yml`、`PROGRESS.md`、`AUDIT.md`、`SOURCE_OBSERVATIONS.md`（面向编者的内部资料，不进入发布站点）。

## 约定

- 界面文字（按钮、菜单、提示）均逐字取自 BeefTV 源码，不做翻译或改写；
- 生成类操作涉及云端渠道按量计费，相关页面有费用提示；
- 快捷键以 macOS 修饰键书写（⌘/⇧/⌥），Windows 对应 Ctrl/Shift/Alt。
