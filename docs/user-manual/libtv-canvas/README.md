# LibTV 画布用户手册

> 适用版本：LibTV（`https://www.liblib.tv`），首页左下角显示「版本更新记录 v1.5」。取证日期 2026-10-01。
> 面向读者：用 LibTV 做 AI 视频 / 图片 / 音频创作的普通创作者与重度创作者。
> 所有界面文字逐字取自真实运行界面，不翻译、不改写；找不到证据的地方宁可留白，也不编。

## 这是什么

LibTV 是一张**无限画布式 AI 影视工作台**。它的心智模型和 Figma / 剪映都不太一样，先建立这个印象，后面每一步都会顺很多：

- 你不是在「填一个表单」，而是在**一张可以拖来拖去的画布上摆节点**；
- 节点之间靠**连线**组成流水线：上游做完的东西喂给下游；
- 「工作流」和「故事板」是**同一批内容的两种排布方式** —— 工作流看的是依赖关系，故事板看的是时间顺序。

## 从这里开始

| 我想做的事 | 从哪读起 |
|---|---|
| 第一次打开 LibTV | [00-quickstart.md](00-quickstart.md) |
| 摆第一张画布、跑通第一条链路 | [10-tasks/enter-canvas.md](10-tasks/enter-canvas.md) → [10-tasks/create-nodes.md](10-tasks/create-nodes.md) → [10-tasks/connect-nodes.md](10-tasks/connect-nodes.md) |
| 管理一张项目里的多张画布 | [10-tasks/manage-canvases.md](10-tasks/manage-canvases.md) |
| 把画布理顺 / 找回看丢的东西 | [10-tasks/organize-canvas.md](10-tasks/organize-canvas.md) |
| 生成图片、视频、音频 | [10-tasks/generate-media.md](10-tasks/generate-media.md) |
| 让 Agent 帮我干活 | [10-tasks/agent-director.md](10-tasks/agent-director.md) |
| 用角色、用素材风格 | [10-tasks/character-studio.md](10-tasks/character-studio.md) · [10-tasks/asset-library.md](10-tasks/asset-library.md) |
| 按时间顺序看内容 | [10-tasks/storyboard-mode.md](10-tasks/storyboard-mode.md) |
| 查键位、查参数、查名词 | [20-reference.md](20-reference.md) · [30-concepts.md](30-concepts.md) |
| 出错了先看这里 | [90-troubleshooting.md](90-troubleshooting.md) |

## 开始之前必须知道的五件事

1. **生成要花积分，且本手册不会替你试。** 测试账户余额 20 积分，因此本手册所有生成相关页面都**只写到「参数填好、提交按钮在哪」为止**，一次都没有真的点过生成。哪些是实测、哪些是按界面推断，每一页都分开标了出来。
2. **「新建项目」点了就直接进画布，没有对话框。** 名字之后再改 —— 不是按钮坏了。
3. **一张画布 = 一个独立的项目地址。** 顶栏 URL 里的 `projectId` 跟着画布走，所以你把画布链接发给别人，对方打开的确实就是这一张。
4. **「教程」按钮不是教程。** 底部工具条上那个标着「教程」的圆按钮，实现上是一个联系入口，点下去不会打开任何教程页面。正文如实写明。
5. **整理画布会问你一次「是否保留此次整理结果？」。** 不点「保留」，这次整理就不会生效 —— 这是最容易「以为整理没生效」的地方。

## 约定

- 界面文字（按钮、菜单、提示）均逐字取自 LibTV 真实界面；
- 快捷键按 **macOS** 书写（⌘ / ⌥ / ⇧），Windows 对应 Ctrl / Alt / Shift；
- 每篇操作指南都标注了**哪些步骤是实跑验证的、哪些没有**；
- 截图取自真实运行界面，固定视口 1440×810、深色主题。

---

## 维护者

任务实施账本见 [`task-inventory.yml`](task-inventory.yml)，逐张截图登记见 [`screenshots/manifest.yml`](screenshots/manifest.yml)，接力说明见 [`PROGRESS.md`](PROGRESS.md)，回走审计见 [`AUDIT.md`](AUDIT.md)。构建可浏览站点的方法见同目录 `PUBLISH.md`。
