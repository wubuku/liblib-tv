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
| 6a | 时间线三篇（timeline-editing / subtitle-highlights / timeline-export） | ✅ 完成（Batch 4） |
| 6b | 导演台三篇 | ✅ 完成（Batch 4） |
| 6c | Gate B 前置：全部 24 页成稿 | ✅ 完成（Batch 5） |
| 8a | cloud-agent / agent-memory-skills / plugins-management | ✅ 完成（Batch 5） |
| 8b | local-runtime + 30-concepts.md + 90-troubleshooting.md | ✅ 完成（Batch 5） |
| 10 | 本地起 BeefTV（vite :3000 + go server）真实截图补齐 manifest | ⏳ 待做 |
| 11 | Gate A 机械审计 + 修订 | ⏳ 待做 |
| 12 | 本地起服真实截图 + Gate A | ✅ 完成（Batch 6，commit a94130ac：25 tasks / 30 md / 12→14 images） |
| 13 | Gate B 回走审计（15 项走查：缩放步进/拖线快速创建/快捷键中心/小地图/版本记录/composer 等）+ AUDIT.md + 修复（排障页新增「正在打开画布」条目） | ✅ 完成（Batch 7：11 verified / 14 excluded 带原因） |
| 14 | --phase final 最终审计 | ✅ OK（25 tasks / 31 md / 14 images） |
| 15 | VitePress 站点（四件套适配，构建 28 页 / 11 图 / 2.8M / 1.51s，无 .md 残留链接） | ✅ 完成（Batch 8） |
| 16 | 上游 v1.6.6 增量修订（generate-video/troubleshooting/local-runtime/README + 版本口径 v1.5.9→v1.6.6） | ✅ 完成（监控轮，commit 860dfc5c） |
| 17 | v1.6.6 重摄（composer 界面未漂移，09 sha256 更新）+ 发布前预览走查（首页/quickstart/generate-video/troubleshooting 四页渲染与图片均正常；README 发布状态行与账本死链修正） | ✅ 完成 |
| 17b | 发布产物保鲜重建 ×2（收纳 16-25 号新截图、v1.6.6 修订四页、30-concepts 增补两节） | ✅ 完成（28+ 页 / 14 图 / 无 .md 残留链接） |
| 17c | SKILL §8 最终报告 FINAL-REPORT.md（目标版本/角色/深度/覆盖率/未覆盖项/已知限制） | ✅ 完成 |
| 17c | excluded 任务开放条件系统化（12 项，供后续接手者按表解锁） | ✅ 完成 |
| 18 | 可达升级两例：plugins-management / troubleshooting 升 verified | ✅ 完成（excluded 13→12） |

### excluded 任务开放条件表（12 项，2026-09-29 快照）

| 任务 | 开放条件 | 升级路径 |
|---|---|---|
| media-versions | 真实生成产生版本族（付费） | 生成 ≥2 版后回走版本切换/对比 |
| timeline-editing / subtitle-highlights / timeline-export | 时间线编辑器入口开放（当前视频处理下拉仅三项且无剪辑台跳转实可达；面板未挂载） | 入口开放后回走八面板 |
| director-basics / director-keyframes-record / director-rig-bones | 导演台入口解禁（当前「正在开发」） | 解禁后回走检查器/关键帧/白膜 |
| cloud-agent | BeefTV Agent 面板解禁 | 解禁后回走发起/审批/插话/取消 |
| agent-memory-skills | 同上（记忆面板挂于 Agent 设置弹窗） | 解禁后回走批准/压缩/技能 @ |
| local-runtime | 本机启动 framefield-local-runtime | 启动后回走深度/线稿/姿态 |
| concepts-architecture | 不适用回走（概念页无操作步骤）；内容已随源码审查闭环 | 可随时出 excluded（保持 excluded 亦准确） |
| 18 | 回收站弹窗/模型渠道配置页/资产页补拍 + plugins-management、troubleshooting 升级 verified（excluded 13→12） | ✅ 完成（commits b1b1b1ec/43260f11/fb946cc1） |

## 方法论适配说明（相对 SKILL 的差异）

- **证据形态**：BeefTV 为参考项目，本手册第一阶段以**源码静态证据**为主（调研包 702 处断言抽查 100% 吻合，UI 标签逐字取自源码字符串）；SKILL 要求的运行时取证在 Batch 10 本地起服后补齐（manual 目标版本 v1.5.9 = 公共最新，源码即真实 UI 的字面来源）。
- **确认门**：/goal 指令「不要停下来询问」= 对「Agent 依证据自行定级」的常设授权（SKILL §2 允许的授权路径）；候选表持续可见可重排。
- **安全边界**：生成类动作按量计费——回走验证只到付费边界前一步；不配置 Provider Key；不触发真实生成。
- **工作区纪律**：master 分支直改；不碰他人 WIP（design-references/liblib-canvas 审计等）；不用 stash。

## 运行环境（Batch 10 使用）

- web：`cd web && bun install && bun run dev`（vite，端口 3000；`dev:slim` 关全量媒体资源）
- backend：Go，`backend/cmd/server`（SQLite）；启动方式待 Batch 10 实测记录
- 版本：工作树 VERSION=v1.5.7；公共最新 v1.5.9（浅色模式 + 素材限制对齐，见调研包 §35）
