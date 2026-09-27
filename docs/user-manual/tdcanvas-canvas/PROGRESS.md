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
- **最近进展（2026-09-27）**：dev server 重启并清空本地数据获得干净首启；create-canvas-project 完成运行时走查与成稿（3 截图入 manifest）；**修正已知问题**——新项目默认标题实测「TDCanvas 1」（清数据后编号从 1 起，此前「TDCanvas 2」为残留计数），AUDIT.md 对应条目已结。
- **Batch M5（2026-09-27）**：generate-images（描述型：面板字段运行时取证、状态机/停止≠取消/刷新恢复为源码+官方文档取证并标注）+ undo-persistence + project-management + shortcuts-help 四任务成稿；manifest +3（累计 20 张）。12 任务全部 drafted。
- **Batch M4（2026-09-27）**：connect-references + navigate-canvas + organize-canvas 三任务成稿——拖线到空白的上下文生成菜单（按上游类型变化，新发现）、滚轮缩放/平移/小地图开合与点击导航、组拖入与外观面板四组设置；并行会话遗留 WIP 判定弃置（实为首页截图错置文件名），未收编。manifest +6。
- **Batch M3（2026-09-27）**：upload-materials + image-operations 成稿——真实图片(3.9MB)/视频(809KB)/音频(1.1MB)经 input 管线注入全成功（原生播放器节点 + toast「已添加 1 个素材节点…」逐字）；行为细节：有选中节点时上传仍新建节点；裁剪全流程回走（2048×2048 原图、1:1 默认 1556、比例预设七项、Cropped Image 子节点+连线）。manifest +4。
- **Batch M2（2026-09-27）**：edit-nodes 成稿——双击标题重命名、双击/工具条编辑文字、删除→历史 flyout 撤销恢复、信息面板（ID/尺寸/位置/状态 + JSON 页签）全部运行时证实；**发现真实缺陷：同项目多标签同时编辑会互相覆盖（无冲突保护），已写入手册排障章与 AUDIT**；缩放手柄拖拽取证精度不足，留 Gate B。manifest +1。
- **Batch M1（2026-09-27）**：create-nodes 完成运行时取证与成稿——双击菜单七项逐字截图、文字/视频/音频/组四类空节点创建实测、54% 全览截图；manifest +2（sha256）；inventory 状态 drafted。**并行协作者提示**：检测到另一会话在 navigate-canvas 上有 WIP 截图（02-navigate-canvas-zoom-in-wheel.png，未提交），本 batch 未触碰该任务与其文件。重置视图新发现：有选中节点时=聚焦选中（k≤1.5），无选中时=fit 全部（k≤1）。
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
| 逐任务探索 + 10-tasks 成稿 | 进行中（create-canvas-project drafted + 00-quickstart 完成；其余 11 任务 planned） |
| 00-quickstart / 20-reference / 30-concepts / 90-troubleshooting | 未开始 |
| Gate A | 未开始 |
| Gate B 回走 + AUDIT.md | 未开始 |
| final audit + 交付报告 | 未开始 |

## 收尾留档 — 2026-09-27（用户指示收尾，循环暂停）

1. **已完成**：工作文档五件套 + AUDIT 骨架；quickstart + 3 个旗舰任务成稿（create-canvas-project / create-nodes / edit-nodes，均运行时走查）；generate-images 占位（付费边界，描述型）；6 个任务占位页；截图 8 张入 manifest（sha256）；多标签覆盖真实缺陷已入 AUDIT 与手册排障。
2. **进度**：12 任务中 3 drafted + 1 描述型占位 + 8 planned（占位页有大纲）。
3. **恢复入口**：按 §1「下一步」顺序执行；每 batch 遵循 规划→实施→验收→commit→push 循环；素材注入方法见 TEST_MEDIA_ASSETS.md。
4. **红线不变**：不触发真实生成、不配置 API Key、不启动 ComfyUI、不用 stash/丢弃他人工作区修改。
5. **待用户输入**：任务优先级重排（当前 Agent 自行定级）；多标签覆盖缺陷复现素材如需入排障章另行授权。
