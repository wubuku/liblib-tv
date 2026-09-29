# BeefTV 用户手册 · 最终报告

> 依据 web-studio-user-manual SKILL §8 完成标准出具。

## 目标与版本

| 项 | 值 |
|---|---|
| 目标应用 | BeefTV（AI 影视创作工作台：无限画布 + 时间线剪辑 + 三维导演台 + 云端 Agent） |
| 手册对应版本 | **v1.6.13**（公共最新发布；截图摄于 v1.5.7 与 v1.6.6 构建，v1.6.7–v1.6.13 增量已审计并以文字注记标注于对应页面） |
| 源码锚点 | 调研证据锁定 `85c9686`/v1.5.7（702 处断言抽查 100% 吻合），增量差异已审计至 v1.6.13（10 提交/201 文件，覆盖 Seedance 付费确认/素材校验强化/企业协议修复/Windows 深度运行时/导演台扩展） |
| 目标 URL | 本地 `http://localhost:3001`（自托管站同构） |
| 发布产物 | `.vitepress/dist/`（28+ 页 HTML，构建校验六步全绿） |

## 角色与深度

| 角色 | 覆盖章节 | 深度 |
|---|---|---|
| beeftv-creator（普通创作者） | 画布核心九篇 + 整理/历史/快捷键 | 旗舰/完整 |
| beeftv-creator（进阶） | 时间线剪辑三篇 | 旗舰/标准 |
| beeftv-creator（导演台） | 导演台三篇（Batch 26 起运行时实证） | 旗舰/标准/简明 |
| beeftv-agent-user | 云端 Agent + 记忆技能 | 旗舰/标准 |
| beef-admin | 插件管理 + 本地伴随进程 | 标准/简明 |

## 覆盖率

- 任务账本 25 项：**18 verified**（运行时走查或内容一致性审查通过；Batch 26 起含导演台三篇）/ **7 excluded**（带原因与开放条件表，见 PROGRESS §17c）；
- 36 张真实截图入册（screenshots/manifest.yml 逐张登记 sha256/定位证据/alt）；
- 界面文字逐字取自源码与运行时 DOM；v1.6.x 界面差异以文字标注。

## 未覆盖项（7 项 excluded 摘要）

| 类别 | 任务 | 原因 |
|---|---|---|
| 付费边界 | media-versions | 版本族需真实生成产生 |
| 入口未开放 | timeline 三篇 | 时间线剪辑面板入口未挂载（视频处理下拉仅三项） |
| 面板禁用 | cloud-agent、agent-memory-skills | BeefTV Agent 面板「正在开发」 |
| 进程未启动 | local-runtime | 本环境为 Web 自托管：桌面端 v1.6.12 起自动下载深度组件，Web 模式仍需本机伴随进程 |

## 已知限制

1. **webview 点击不可靠**（与帧界 batch 292 同源）：部分下拉/菜单点击落空，剪辑台内部的运行时走查仍受阻；项目卡操作菜单端到端（Batch 23 合成点击走查）与模型下拉（Batch 23 结案：未配渠道设计性跳转模型配置，清单渠道驱动）已解决——均记录于 AUDIT.md；
2. **视频模型下拉清单**：受同上限制暂以 Batch 299 源站 14 模型采样文字替代（当前值「2.0」已实证）；
3. **生成操作**：按量计费，全部流程止于付费边界前一步（安全红线）；
4. **depth-action 分叉**：`codex/depth-action-video-preview`（5 提交，备发布 v1.6.0）与 main 并行——注意 v1.6.12/13 已将 **Windows 深度运行时**以另一条路径并入 main（depth-runtime-v2 组件发布），分叉合流后仍需双向差异审计（重点：视频预览稳定性部分是否已被覆盖）。

## 审计状态

- Gate A：OK（25 tasks / 32 Markdown / 36 images）；
- Gate B：15+ 项走查记入 AUDIT.md（发现均已修复或如实记录）；
- `--phase final`：OK（25 tasks / 32 Markdown files / 36 images）；
- verify-docs.py：1169 文件全绿（Batch 26 复验）。
