# 即梦画布功能用户手册

本目录只覆盖 `jimeng.jianying.com` AI 画布（`/ai-tool/ai-canvas/:projectId`）的
画布编辑功能，不覆盖账户、充值、订阅、积分购买和画布之外的页面。

## 当前状态

- 目标源站：`https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f`（测试项目）
- 目标角色：已登录的普通画布创作者
- 深度：`thorough`
- 方法：`.agents/skills/web-studio-user-manual/` 的任务优先级、运行时取证、截图
  和回走审计流程（与 frameos-canvas 手册同一套规范）。
- 证据边界：只有当前登录态浏览器中实际观察到的 DOM、ARIA、交互结果和安全网络
  证据才写入正文；`docs/research/jimeng-canvas/` 的复刻研究只作为候选线索。
- 安全边界：不执行任何真实生成或按积分计费的操作；生成类任务只记录到
  「点击执行前一步」。
- 进度：**手册已成稿并通过质量门**——**17** 个任务全部 `verified`，**23** 页正文 +
  **159** 张登记截图（另 4 张示意图），并已构建 VitePress 静态站点。
  - 2026-10-01 增量：任务集由 14 补至 17（新增时间线 / 主体 / 导演台三页操作指南），
    截图由 22 增至 53；本 README 原先的计数与任务清单停留在初版口径，已按实际文件订正。
  - 2026-10-01 增量：修复越界链接导致的两道质量门失败（详见仓库内
    `AUDIT.md` 的「机械审计复跑记录」），并补齐 `use-node-toolbar`
    的图片节点工具条、视频修剪、截取帧三处覆盖缺口。gate-a / final 当日复跑均 exit=0。
  - 已知未取证面（时间线/主体/导演台节点等）汇总在仓库内 `PROGRESS.md` §8 C2，
    属范围决策而非缺陷。

## 手册正文

- [快速上手](00-quickstart.md)
- 任务指南（`10-tasks/`，**17 页**）：
  - 上手与画布：[创建第一个节点](10-tasks/create-first-node.md) ｜
    [平移与缩放画布](10-tasks/navigate-canvas.md) ｜
    [连接节点建立参考](10-tasks/connect-nodes.md) ｜
    [使用节点工具条](10-tasks/use-node-toolbar.md) ｜
    [准备生成（执行前一步）](10-tasks/prepare-generation.md)
  - 编辑与整理：[编辑文本节点](10-tasks/edit-text-node.md) ｜
    [复制、删除与撤销](10-tasks/duplicate-delete-history.md) ｜
    [编组与布局整理](10-tasks/organize-group-layout.md)
  - 节点类型：[时间线节点](10-tasks/timeline-node.md) ｜
    [主体节点](10-tasks/subject-node.md) ｜
    [导演台节点（Beta）](10-tasks/director-node.md) ｜
    [音频与配音](10-tasks/audio-node-voice.md)
  - 素材与预览：[资产库与本地上传](10-tasks/assets-and-upload.md) ｜
    [媒体播放与预览](10-tasks/media-playback.md)
  - 画布环境：[AI 对话抽屉](10-tasks/ai-agent-drawer.md) ｜
    [画布上下文](10-tasks/canvas-context.md) ｜
    [帮助与快捷键](10-tasks/help-and-shortcuts.md)
- [参考速查](20-reference.md) ｜ [核心概念](30-concepts.md) ｜ [排障](90-troubleshooting.md)

## 以网站形式查看

手册可构建为 VitePress 静态站点（本地中文搜索、侧边栏分组）：

```bash
cd docs/user-manual/jimeng-canvas
./build-site.sh --preview                                # 构建并预览 http://localhost:4173
# 或者仅预览已有产物（无缓存，推荐）：
python3 -m http.server 4173 -d .vitepress/dist
```

- 产物：`.vitepress/dist/`（纯静态，整体拷贝到任意 Web 服务器即可发布）；
- 构建、子路径部署、发布前截图脱敏审查与运维 FAQ 见仓库内 `PUBLISH.md`
  （内部文档，不进入网站构建）；
- 重新构建后如用 `--preview`，必须重启预览进程（sirv 启动时缓存文件清单）。

## 工作账本（Agent 接力入口）

以下都是**仓库内的内部工作文档**，按 `.vitepress/config.mjs` 的 `srcExclude`
不进入网站构建，因此这里用文件名而非站内链接引用（在 GitHub/编辑器中直接打开
本目录即可）：

- `task-inventory.yml`：**17** 个任务的范围、频率、影响与 `verified` 状态。
- `PROGRESS.md`：探索、编写、验证与站点构建的完整进度记录。
- `AUDIT.md`：真实浏览器回走审计结果、机械审计复跑记录与已接受限制。
- `SOURCE_OBSERVATIONS.md`：源站观察台账（当日基线、逐任务 DOM/交互事实、
  源站演进纠错）。
- `screenshots/manifest.yml`：**53** 张正式截图 + **4** 张示意图的登记与哈希。
- `TEST_MEDIA_ASSETS.md`：授权测试媒体使用记录
  （权威清单见仓库级 `docs/CANVAS_TEST_MEDIA.md`，位于本手册目录之外）。
- `FINAL-REPORT.md`：最终交付报告（目标版本/URL、角色、深度、覆盖率、
  未覆盖项与已知限制），即 skill §8 的完成标准交付物。
