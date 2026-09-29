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
| 19 | 监控轮：上游无变化（main v1.6.6 / depth-action 5 提交未合流）；生成历史弹窗首次点开并 DOM 取证（回写 create-nodes）；local-runtime 可达性评估（二进制不在仓库，维持 excluded） | ✅ 完成（AUDIT 环境记录四） |
| 20 | 监控轮：上游无变化；补拍两张受阻截图——版本记录侧栏 v1.6.6 重摄（07）+ 生成历史弹窗新增（28，嵌入 create-nodes）；模型下拉确认为条件渲染结构性受阻（源码 popover:59） | ✅ 完成（AUDIT 环境记录五） |
| 21 | 监控轮（收尾轮）：上游无变化；模型下拉重试失败但定位根因——视频节点 1/文本节点 1 被 S83 大节点遮挡（锚点坐标证实），自动整理与快捷键均未能重排；项目卡菜单走查未开始 | ✅ 部分完成，如实留档（AUDIT 环境记录六） |
| 22 | 上游增量修订 v1.6.6→v1.6.13（10 提交/201 文件）：generate-video（付费风险确认/素材校验强化 v1.6.8-11/任务模式跟随注记）、troubleshooting（画幅比确认/读不出与帧率/接口未安装/深度组件下载）、local-runtime（Windows 深度运行时）、director-basics（v1.6.13 扩展注记）、版本口径三处、开放条件表同步 | ✅ 完成（AUDIT 增量审计记录） |
| 23 | 走查突破轮：项目卡操作菜单端到端（删除→回收站→恢复，合成点击手法）；模型下拉 #16 结案（未配渠道设计性跳转，清单渠道驱动）；composer 全结构实证；新截图 29（非空回收站）；「移至文件夹」转写修正 | ✅ 完成（AUDIT 环境记录七） |
| 24 | v1.6.13 细节补遗：桌面端更新流程（定期检查/保存并安装/关闭再开）入 20-reference；低缩放裁剪/修剪标签可读性注记入 upload-materials | ✅ 完成 |
| 25 | 上游增量：`69fbf9b`（Unreleased）深度组件下载支持系统代理（与桌面更新共用规则）——回写 local-runtime/troubleshooting；depth-action 分叉仍未合流 | ✅ 完成（AUDIT 环境记录八） |
| 27 | 上游增量：v1.6.14（`852961a`）任务详情实时刷新——generate-images 注记 + 版本口径 v1.6.14；工作树同步 | ✅ 完成（AUDIT 环境记录十） |
| 28 | 白膜导出全流程补走查：导出→loading→素材空间 +1→镜头节点封面更新（截图 37）；director-keyframes-record 导出缺口关闭；新截图 29→37 张 | ✅ 完成（AUDIT 环境记录十一） |
| 29 | 收尾轮：上游无变化；时间线入口源码调研——v1.6.14 已注册「进入剪辑」工具但视频节点分支不渲染、处理器把视频路由到内联修剪，多轨弹窗仅音频节点可达；timeline 三篇开放条件细化后维持 excluded | ✅ 完成（AUDIT 环境记录十二） |
| 26 | **导演台解禁升级轮**：BeefTV 工作树 detached 5b1c060(v1.6.6)→69fbf9b(v1.6.13)（依赖零变化，后端重启）；导演台入口 v1.6.7+ 已解禁（源码 + 运行时双证）——完整走查 入口→模板→镜头节点→工作台四模式→摄像机检查器/动画时间轴(记录落帧)/姿态 rig(49 骨骼/20 姿势)；**三任务升 verified（18/7）**；新增截图 30-36；director-basics 检查器表按运行时重构改写 | ✅ 完成（AUDIT 环境记录九） |

### excluded 任务开放条件表（12 项，2026-09-29 快照）

| 任务 | 开放条件 | 升级路径 |
|---|---|---|
| media-versions | 真实生成产生版本族（付费） | 生成 ≥2 版后回走版本切换/对比 |
| timeline-editing / subtitle-highlights / timeline-export | 多轨时间线弹窗（二期组件已在 v1.6.14 挂载）目前仅能经**有内容的音频节点**「进入剪辑」打开；视频节点被路由到内联修剪且不渲染该按钮 | 备好音频测试媒体经音频节点进入后回走；或等视频节点分支接入 |
| cloud-agent | BeefTV Agent 面板解禁 | 解禁后回走发起/审批/插话/取消 |
| agent-memory-skills | 同上（记忆面板挂于 Agent 设置弹窗） | 解禁后回走批准/压缩/技能 @ |
| local-runtime | 本机启动 framefield-local-runtime（v1.6.12 起 Windows 桌面端改为首次使用自动下载签名组件；本环境为 Web 自托管，仍需本机进程） | Web 模式：启动伴随进程后回走深度/线稿/姿态；桌面端：安装组件后回走 |
| ~~concepts-architecture~~ | 内容一致性审查已通过，已升级 **verified**（Batch 18） | 已升级 |
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
