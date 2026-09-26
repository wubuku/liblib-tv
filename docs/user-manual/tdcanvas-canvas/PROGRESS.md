# TDCanvas 画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)、[`AUDIT.md`](AUDIT.md) 和
> [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-09-26（工作文档准备完成，等待逐任务探索与成稿）。
- 当前目标：为 TDCanvas（桌面端 AI 无限画布，v0.14.0）的普通创作者编写中文、任务导向、可回走验证的用户手册。
- 当前专项目录：`docs/user-manual/tdcanvas-canvas/`。
- 被测应用：TDCanvas 本地工作副本 `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`（锁定提交 `16b3127`），`web/` 下 `npm run dev`（需 nvm node 24）→ **http://localhost:3000**。
- 本轮已完成：五份工作文档就绪（本文件、task-inventory、SOURCE_OBSERVATIONS、TEST_MEDIA_ASSETS、screenshots/manifest 骨架）；调研包 `docs/research/tdcanvas-2026-09-26/`（47 轮迭代，414 处核验引用）与一次真实素材运行时探索（RUNTIME_AUDIT.md）可作为任务探索底稿。
- **下一步（按序）**：
  1. 重启 dev server（见 §4），按 task-inventory 顺序逐任务探索：每任务先 DOM/网络取证，再按需截图入 manifest；
  2. 每完成一个任务即写对应 `10-tasks/*.md` 与 `00-quickstart.md`，状态 planned→drafted；
  3. 全部 drafted 后跑 Gate A → 逐任务回走（Gate B，记录 AUDIT.md）→ final audit；
  4. 交付报告列出覆盖率与未覆盖项。
- **任务确认门状态**：任务优先级由 Agent 按调研包证据自行定级（用户目标明确授权编写手册并准备工作文档）；候选表在本目录 task-inventory.yml 中完全可见，用户可随时要求增删或重排——重排后只需更新 inventory 的 frequency/impact/status，不必推翻手册结构。

## 2. 范围与安全边界

### 纳入范围

只记录 TDCanvas 画布相关页面（`/canvas`、`/canvas/:id` 及画布内直达的提示词库/资产入口）中的：

- 项目创建与管理、节点创建、素材上传、编辑、连接/引用、分组与外观；
- 撤销重做与自动保存、快捷键与帮助；
- 图片生成本地前半程（入口/参数/状态语义）——流程描述允许，**回走验证止于付费边界前**。

### 不纳入范围

- **任何真实生成调用**（图片/视频/音频生成、反推提示词、AI 角度重渲染——Aitudou API 按量计费）；手册正文描述生成流程时标注「来源：官方文档/源码，未回走」。
- 配置 API Key、启动 ComfyUI 环境、安装第三方插件、连接真实 Codex/Claude Agent。
- 账户/登录（TDCanvas 无账号体系，本地优先）、生产数据。
- 把官方 mdx 文档的旧版生成流（Config 生成配置节点、/v1/videos）写成当前 UI 事实——冲突处以运行时为准并记入 SOURCE_OBSERVATIONS §9。

### 测试媒体

14 个真实素材（10 图 / 2 音 / 2 视频及字节数）登记于
[`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)，仅用于上传、预览、连线与编辑验证。

## 3. 方法论和完成标准

- 规范来源：`.agents/skills/web-studio-user-manual/SKILL.md`（确认门→冻结环境→逐任务探索→截图规范→中文成稿→Gate A→Gate B→final）。
- 深度：`thorough`；证据优先级：运行时取证 > 源码 file:line（调研包） > 官方文档 > 推断。
- 自动化要点（2026-09-26 实测）：locator 点击会被画布覆盖层拦截 → 用 CUA 坐标路径（截图定位）；`page.evaluate` 不可靠 → 用 `locator("body").evaluate`；IAB 无文件选择器 → 素材注入用 `web/public/__rt__/` 同源 fetch 管线（用后删除）。
- Gate A：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/tdcanvas-canvas --phase gate-a
  ```

- Gate B：按手册从入口重走每个任务，证据记 `AUDIT.md`；Blocker/Major 清零后方可交付。
- 最终审计：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/tdcanvas-canvas --phase final
  ```

## 4. 冻结环境备忘

- 被测应用：TDCanvas 仓 `web/`，`nvm use 24 && npm run dev`（Vite @3000，--host 0.0.0.0）；启动约 1s；IndexedDB 数据随浏览器 profile 保留。
- viewport 固定 1440×900；中文 locale（默认）；暗色主题（默认）；不配置 API Key。
- 素材注入：复制 14 项素材中所需者到 `web/public/__rt__/`（ASCII 文件名），页内 fetch 后注入全局 file input；**结束必须删除 `__rt__` 目录**（保持 TDCanvas 工作副本干净）。
- 已知偏差：浏览同页后 Playwright locator 点击会超时（覆盖层拦截 actionability），一律改用 `tab.cua` 坐标路径。

## 5. 阶段状态

| 阶段 | 状态 |
|---|---|
| 快速扫描（调研包 47 轮 + 官方文档） | 完成 |
| 确认门（候选表自行定级，标注待复核） | 完成（PROGRESS §1 可重排） |
| 工作文档冻结 | 完成（本目录五件套） |
| 逐任务探索 + 10-tasks 成稿 | 未开始（12 任务 planned） |
| 00-quickstart / 20-reference / 30-concepts / 90-troubleshooting | 未开始 |
| Gate A | 未开始 |
| Gate B 回走 + AUDIT.md | 未开始 |
| final audit + 交付报告 | 未开始 |
