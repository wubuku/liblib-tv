# 即梦画布功能用户手册

本目录只覆盖 `jimeng.jianying.com` AI 画布（`/ai-tool/ai-canvas/:projectId`）的
画布编辑功能，不覆盖账户、充值、订阅、积分购买和画布之外的页面。

## 当前状态

- 目标源站：`https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f`（测试项目）
- 目标角色：已登录的普通画布创作者
- 深度：`thorough`
- 方法：由 `.agents/skills/web-studio-user-manual/` 的任务优先级、运行时取证、
  截图和回走审计流程管理，与 frameos-canvas 手册同一套规范。
- 证据边界：只有当前登录态浏览器中实际观察到的 DOM、ARIA、交互结果和安全网络
  证据才写入正文；`docs/research/jimeng-canvas/` 的复刻研究只作为候选线索，
  其中的 `CLONE_DECISION` 永远不是源站事实。
- 安全边界：不执行任何真实生成或按积分计费的操作；生成类任务只记录到
  「点击执行前一步」。
- 进度：2026-09-23 完成 14 个任务的全量取证（22 张截图）与正文编写；
  任务状态 `documented`，Gate B 回走进行中。

## 手册正文

- [快速上手](00-quickstart.md)
- 任务指南（`10-tasks/`）：创建节点、平移缩放、连接节点、节点工具条、
  准备生成、文本节点、复制删除撤销、资产库与上传、播放预览、编组整理、
  音频配音、AI 对话抽屉、画布上下文、帮助快捷键
- [参考速查](20-reference.md) ｜ [核心概念](30-concepts.md) ｜ [排障](90-troubleshooting.md)

## 入口

- [`task-inventory.yml`](task-inventory.yml)：任务范围、频率、影响和覆盖状态
  （候选清单，待用户确认）。
- [`PROGRESS.md`](PROGRESS.md)：探索、编写和验证进度（当前接力入口）。
- [`AUDIT.md`](AUDIT.md)：真实浏览器回走审计。
- [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)：按证据类型记录的源站观察
  与截图识图台账。
- [`screenshots/manifest.yml`](screenshots/manifest.yml)：正式截图登记与哈希
  （当前为空）。
- [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)：已获授权的本地图片、音频、
  视频测试输入及付费生成禁令。

手册正文按用户目标放在 `10-tasks/`；未完成 Gate A/Gate B 的任务不会写成已验证
功能。当前 `10-tasks/` 为空：候选任务确认门尚未通过，正式探索尚未开始。
