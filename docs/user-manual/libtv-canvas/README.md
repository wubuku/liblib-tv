# LibTV 画布用户手册

> 适用版本：LibTV（`https://www.liblib.tv`），首页左下角显示「版本更新记录 v1.5」。取证日期 2026-10-01。
> 面向读者：用 LibTV 做 AI 视频 / 图片 / 音频创作的普通创作者与重度创作者。
> 所有界面文字逐字取自真实运行界面，不翻译、不改写；找不到证据的地方宁可留白，也不编。

## ⭐ 一键启动本手册网站（维护者）

<details>
<summary><b>👉 点这里展开：一条命令启动手册网站（仅维护者需要，普通读者请忽略）</b></summary>

```bash
cd docs/user-manual/libtv-canvas
./serve.sh
```

就这一条命令。它会**构建站点并起本地预览**，最后打印访问地址。
默认地址：**<http://127.0.0.1:4189/>**

| 需求 | 命令 |
|---|---|
| 启动（构建 + 预览） | `./serve.sh` |
| 只启动，**不重新构建** | `./serve.sh --no-build` |
| 换个端口 | `./serve.sh --port 5000` |
| 看现在跑没跑、在哪个端口 | `./serve.sh --status` |
| 停掉 | `./serve.sh --stop` |
| 只构建、不起服务 | `./build-site.sh` |

**⚠️ 端口别搞混。** 本仓库里同时存在多本用户手册，每本都可能起着自己的预览：

- **4189** ← ✅ **LibTV 画布手册，本手册的默认端口**
- 4188 ← ⛔ **Flowable Trial 原站手册**。打开它**不是**这一本
- 4173 ← `build-site.sh --preview` 硬编码的端口，撞了不报错

打开后先看浏览器标签页标题确认：LibTV 这本是「**LibTV 画布用户手册**」。

**💡 端口被占时 `serve.sh` 不会杀任何进程**（那个端口上多半是别人的服务），
它会打印出「谁在占」，然后**自动改用下一个空闲端口**，并在最后告诉你实际地址。

**💡 改了正文想立刻看到效果：** `./serve.sh --no-build`

**⛔ 别用 `./build-site.sh --preview`：** 它底层是 `vite preview`，
**启动时就把文件清单缓存了**，改完刷新看到的还是旧页面，每次都得重起进程
（这件事记在 `PUBLISH.md` 里）。`serve.sh` 用的是无缓存的
`python3 -m http.server`，刷新就是新的。

</details>

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

任务实施账本见同目录 `task-inventory.yml`，逐张截图登记见 `screenshots/manifest.yml`，回走审计见 `AUDIT.md`。

> 这些是**维护者**用的账本，不随站点发布 —— 站点里只保留面向使用者的部分。
> **构建与预览方法见本文开头的「一键启动」，发布方法见同目录 `PUBLISH.md`。**
