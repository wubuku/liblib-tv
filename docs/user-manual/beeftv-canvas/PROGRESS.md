# BeefTV 用户手册 · 进度账本

> 手册根：`docs/user-manual/beeftv-canvas/`。任务账本见 [task-inventory.yml](task-inventory.yml)，审计见 [AUDIT.md](AUDIT.md)，证据基座见 [SOURCE_OBSERVATIONS.md](SOURCE_OBSERVATIONS.md)。

## Batch 计划与状态

| Batch | 内容 | 状态 |
|---|---|---|
| 1 | 脚手架：task-inventory（29 候选任务）/PROGRESS/AUDIT/SOURCE_OBSERVATIONS/README | ✅ 完成（commit 2836f442） |
| 2 | 00-quickstart + create-nodes / navigate-canvas / upload-materials / connect-references / prompts-and-mentions / generate-images / media-versions / undo-history-versions（占位） | ✅ 静态成稿（8 页，占位 1） |
| 3 | （已并入 Batch 2） | — |
| 4 | generate-video / media-versions 已成稿；undo-history-versions / organize-canvas 全文 | ✅ 完成（Batch 3） |
| 5 | shortcuts-help + 20-reference.md（快捷键全表/导演台键位/路由/REST 端点/本地进程） | ✅ 完成（Batch 3） |
| 6 | 时间线三篇（timeline-editing / subtitle-highlights / timeline-export） | ⏳ 待做 |
| 7 | 导演台三篇（director-basics / director-keyframes-record / director-rig-bones） | ⏳ 待做 |
| 8 | cloud-agent + agent-memory-skills + plugins-management | ⏳ 待做 |
| 9 | local-runtime + 30-concepts.md + 90-troubleshooting.md | ⏳ 待做 |
| 10 | 本地起 BeefTV（vite :3000 + go server）真实截图补齐 manifest | ⏳ 待做 |
| 11 | Gate A 机械审计 + 修订 | ⏳ 待做 |
| 12 | Gate B 回走审计 + 最终审计 + VitePress 站点（复制 tdcanvas 四件套） | ⏳ 待做 |

## 方法论适配说明（相对 SKILL 的差异）

- **证据形态**：BeefTV 为参考项目，本手册第一阶段以**源码静态证据**为主（调研包 702 处断言抽查 100% 吻合，UI 标签逐字取自源码字符串）；SKILL 要求的运行时取证在 Batch 10 本地起服后补齐（manual 目标版本 v1.5.9 = 公共最新，源码即真实 UI 的字面来源）。
- **确认门**：/goal 指令「不要停下来询问」= 对「Agent 依证据自行定级」的常设授权（SKILL §2 允许的授权路径）；候选表持续可见可重排。
- **安全边界**：生成类动作按量计费——回走验证只到付费边界前一步；不配置 Provider Key；不触发真实生成。
- **工作区纪律**：master 分支直改；不碰他人 WIP（design-references/liblib-canvas 审计等）；不用 stash。

## 运行环境（Batch 10 使用）

- web：`cd web && bun install && bun run dev`（vite，端口 3000；`dev:slim` 关全量媒体资源）
- backend：Go，`backend/cmd/server`（SQLite）；启动方式待 Batch 10 实测记录
- 版本：工作树 VERSION=v1.5.7；公共最新 v1.5.9（浅色模式 + 素材限制对齐，见调研包 §35）
