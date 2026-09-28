# BeefTV 用户手册 · 最终报告

> 依据 web-studio-user-manual SKILL §8 完成标准出具。

## 目标与版本

| 项 | 值 |
|---|---|
| 目标应用 | BeefTV（AI 影视创作工作台：无限画布 + 时间线剪辑 + 三维导演台 + 云端 Agent） |
| 手册对应版本 | **v1.6.6**（公共最新发布；截图摄于 v1.5.7 与 v1.6.6 构建，差异已标注） |
| 源码锚点 | 调研证据锁定 `85c9686`/v1.5.7（702 处断言抽查 100% 吻合），增量差异已审计至 v1.6.6 |
| 目标 URL | 本地 `http://localhost:3001`（自托管站同构） |
| 发布产物 | `.vitepress/dist/`（28+ 页 HTML，构建校验六步全绿） |

## 角色与深度

| 角色 | 覆盖章节 | 深度 |
|---|---|---|
| beeftv-creator（普通创作者） | 画布核心九篇 + 整理/历史/快捷键 | 旗舰/完整 |
| beeftv-creator（进阶） | 时间线剪辑三篇 | 旗舰/标准 |
| beeftv-creator（导演台） | 导演台三篇 | 旗舰/标准/简明 |
| beeftv-agent-user | 云端 Agent + 记忆技能 | 旗舰/标准 |
| beef-admin | 插件管理 + 本地伴随进程 | 标准/简明 |

## 覆盖率

- 任务账本 25 项：**14 verified**（运行时走查或内容一致性审查通过）/ **11 excluded**（带原因与开放条件表，见 PROGRESS §17c）；
- 26 张真实截图入册（screenshots/manifest.yml 逐张登记 sha256/定位证据/alt）；
- 界面文字逐字取自源码；v1.6.x 界面差异以文字标注。

## 未覆盖项（12 项 excluded 摘要）

| 类别 | 任务 | 原因 |
|---|---|---|
| 付费边界 | media-versions | 版本族需真实生成产生 |
| 入口未开放 | timeline 三篇、director 三篇 | 时间线面板/导演台入口「正在开发」 |
| 面板禁用 | cloud-agent、agent-memory-skills | BeefTV Agent 面板「正在开发」 |
| 进程未启动 | local-runtime | framefield-local-runtime 未在本机启动 |
| 概念页 | concepts-architecture | 无操作步骤，不适用回走 |

## 已知限制

1. **webview 点击不可靠**（与帧界 batch 292 同源）：部分下拉/菜单点击落空，剪辑台内部、生成历史弹窗、版本记录 v1.6.6 侧栏的运行时走查受阻——均已记录于 AUDIT.md，环境改善后可补；
2. **视频模型下拉清单**：受同上限制暂以 Batch 299 源站 14 模型采样文字替代（当前值「2.0」已实证）；
3. **生成操作**：按量计费，全部流程止于付费边界前一步（安全红线）；
4. **depth-action 分叉**：`codex/depth-action-video-preview`（163 文件，备发布 v1.6.0）与 main 并行——合流后按双向差异审计修订手册对应章节。

## 审计状态

- Gate A：OK（25 tasks / 31 Markdown / 26 images）；
- Gate B：15+ 项走查记入 AUDIT.md（发现均已修复或如实记录）；
- `--phase final`：OK（25 tasks / 31 Markdown files / 26 images）；
- verify-docs.py：1165 文件 4834 链接全绿。
