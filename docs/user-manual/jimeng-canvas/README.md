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
- 进度：**2026-09-24 手册已完成**——14 个任务全部 `verified`（Gate A/Gate B/
  final 审计通过），19 页正文 + 22 张登记截图，并已构建 VitePress 静态站点。

## 手册正文

- [快速上手](00-quickstart.md)
- 任务指南（`10-tasks/`，14 页）：创建节点、平移缩放、连接节点、节点工具条、
  准备生成、文本节点、复制删除撤销、资产库上传、播放预览、编组整理、
  音频配音、AI 对话抽屉、画布上下文、帮助快捷键
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
- 构建、子路径部署、发布前截图脱敏审查与运维 FAQ 见 [PUBLISH.md](PUBLISH.md)；
- 重新构建后如用 `--preview`，必须重启预览进程（sirv 启动时缓存文件清单）。

## 工作账本（Agent 接力入口）

- [`task-inventory.yml`](task-inventory.yml)：14 个任务的范围、频率、影响与
  `verified` 状态。
- [`PROGRESS.md`](PROGRESS.md)：探索、编写、验证与站点构建的完整进度记录。
- [`AUDIT.md`](AUDIT.md)：真实浏览器回走审计结果与已接受限制。
- [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)：源站观察台账（当日基线、
  逐任务 DOM/交互事实、源站演进纠错）。
- [`screenshots/manifest.yml`](screenshots/manifest.yml)：22 张正式截图的登记
  与哈希。
- [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)：授权测试媒体使用记录
  （权威清单见 [docs/CANVAS_TEST_MEDIA.md](../../CANVAS_TEST_MEDIA.md)）。
