# TDCanvas 画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)、[`AUDIT.md`](AUDIT.md) 和
> [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-09-30（**维护态，当前 14 任务 verified**；M20–M22 补齐导航两个页面的覆盖缺口，Gate A/B/final 全通过）。
- 当前目标：为 TDCanvas（桌面端 AI 无限画布，v0.14.0）的普通创作者编写中文、任务导向、可回走验证的用户手册。
- 当前专项目录：`docs/user-manual/tdcanvas-canvas/`。
- 被测应用：TDCanvas 本地工作副本 `/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas`（锁定提交 `16b3127`），`web/` 下 `npm run dev`（需 nvm node 24）→ **http://localhost:3000**。
- 本轮已完成：**14 个任务**全部运行时走查并 verified；Gate A 与 final audit 均通过（14 tasks / 25 Markdown / 37 images，sha256 全校验）；站点构建 21 页 / 37 图 / 15M。调研包 `docs/research/tdcanvas-2026-09-26/`（47 轮迭代）与真实素材运行时探索（RUNTIME_AUDIT.md）为任务底稿。
- **M20–M22 摘要（2026-09-30）**：新增 `manage-assets`（我的资产，全链回走）与 `use-prompt-library`（提示词库，如实记录来源为空且无配置入口）两任务；补「导入资产」端到端还原回走；quickstart 增导航导览。详见本文件末尾 M20/M21/M22 条目。
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
| 逐任务探索 + 10-tasks 成稿 | 完成（14 任务全部 drafted 并回走；M20 补两个导航页面） |
| 00-quickstart / 20-reference / 30-concepts / 90-troubleshooting | 完成（quickstart M22 增导航导览；reference/troubleshooting 随 M20 扩充） |
| Gate A | 通过（14 tasks / 25 Markdown / 37 images） |
| Gate B 回走 + AUDIT.md | 通过（14/14，无 Blocker/Major） |
| final audit + 交付报告 | 通过（exit 0）+ 站点构建 21 页 / 37 图 |

- **Batch M6（2026-09-27）**：README 手册首页（任务索引表）+ 20-reference（键位/格式限制/状态表/设置项/存储）+ 30-concepts（节点类型/连线语义/双模式/项目/生成生命周期）成稿；manifest 重构为审计脚本 schema（26 条全字段 + sha256）、12 任务状态转换为 documented；**Gate A 通过**（12 tasks / 22 Markdown / 26 images）。剩余：Gate B 全量回走 → final audit。
- **Batch M7（2026-09-28）Gate B 完成**：按手册从入口重走 12 任务全部通过（AUDIT.md 回走结论表）；回走中新发现 Minor 缺陷（上传无内容嗅探）已记录并即时清理；**final audit 通过**（12 任务全部 verified，exit 0）。手册 v1 交付完成。
- **Batch M8（2026-09-28）**：generate-images 补充真实 S109 上传回走与伪装扩展名缺陷发现（已入 AUDIT 与排障）；Gate B 结论表落档；final audit 通过。

## 交付报告（v1，2026-09-28；2026-09-30 增补 M20–M22）

- **目标版本**：TDCanvas v0.14.0（锁定 `16b3127`）@ localhost:3000（Web）。
- **角色**：tdcanvas-desktop-web-creator（本地创作者，深度 thorough）。
- **覆盖率**：task-inventory **14/14** 任务 verified（1 个 generate-images 为描述型，付费边界前验证；use-prompt-library 为限制记录型）。
- **验证密度**：**37 张截图**（manifest 全字段+sha256）、14 任务回走（v1 阶段发现并修正 5 处问题：1 行号漂移、1 悬空 § 引用、1 卡号错位、1 README 状态过时、1 路径归属；M20–M22 新发现 3 处产品/一致性问题并写入手册）、五项自检 + verify-docs + Gate A/final audit 全绿。
- **未覆盖项**：生成类付费流程的运行时回走（红线）、ComfyUI 环境全流程、Agent 连接全流程、真实多用户协作；**提示词库有内容时的交互**（产品侧无提示词来源数据且无配置入口，运行时无法造数）。
- **已知限制**：多标签同项目编辑互相覆盖（产品缺陷，已入排障）；上传无内容嗅探（Minor）；缩放手柄在低缩放下较小（已补验：放大至 100% 后可精确拖拽，锁比保持）；视频资产无「编辑」按钮（Minor）；导航「提示词库」与页面标题「提示词中心」名称不统一（一致性）。
- **维护入口**：本文件 §1 → task-inventory → AUDIT；上游更新时按 UPSTREAM_DIFF_AUDIT 协议增量重验。

- **Batch M11（2026-09-28，维护轮）**：navigate-canvas.md 实测细节扩充——缩放锚点分野（滚轮=鼠标锚/滑杆=视口中心锚）、滚轮步进 ±10%、滑杆对数刻度实操提示、重置视图双行为补实测百分比（聚焦 156%/fit 54–100%）、并行会话错置截图（02-zoom-in-wheel 实为首页）判定与防误用说明入册。

- **Batch M15（2026-09-28，维护轮）**：IAB 窗格恢复；**缩放手柄精确拖拽补验完成**——视频节点 76% 缩放、角点 (638,528) 拖至 (720,600)，底缘 +22px 宽度不变（锁比生效），选中态/工具条正常；AUDIT 遗留项已在此前批次结案；三门禁全绿。

- **Batch M14（2026-09-28，维护轮）**：三门禁复跑全绿；90-troubleshooting 补「项目封面深色线框」条目（封面只取 AI 生成素材，仅本地上传/纯文本项目为线框预览——源码 canvas-home.ts 证据 + M4 首页截图佐证）。

- **Batch M13（2026-09-28，维护轮）**：IAB 窗格恢复（guest not attached 自愈）；**AUDIT 遗留项结案**——缩放手柄精确拖拽于 S109 视频节点 76% 缩放下实测成功（锁比保持）；IAB 重试探测/恢复过程记录。

- **Batch M12（2026-09-28，维护轮）**：IAB 窗格重试仍阻塞（guest not attached）；维护增量改为文档侧——90-troubleshooting 新增「上传的"视频"节点黑屏无法播放」条目（Gate B 实测的伪装扩展名缺陷之用户侧症状与修复），20-reference 生成状态表补轮询参数（4 秒间隔/60 分钟超时）。

- **Batch M10（2026-09-28，维护轮）**：IAB 窗格重试仍阻塞（guest not attached，非时间性自愈）；20-reference 补「连线与其他限制」节（同节点对去重/禁自连/组不连线/单入线/64 字符/字号 10–32）；90-troubleshooting 补「图片历史版本消失」条目（24 版上限与存资产预防）。

- **Batch M9（2026-09-28，维护轮）**：三门禁复跑全绿；缩放手柄补验遇 IAB webview 未就绪阻塞——已将操作指引（100% 缩放 + 角部 28px 手柄）写入 edit-nodes 页与 AUDIT 遗留项，待窗格可用后补验；90-troubleshooting 无需扩充（本轮回走无新症状）。

- **Batch M8（2026-09-28，维护轮）**：三门禁复跑全绿（调研包自检五项 / final audit / verify-docs 1111 文件）；90-troubleshooting 多标签覆盖条目补充四步实测复现步骤；缩放手柄精确验证留待下次打开画布时在 100% 缩放下补做（低缩放下手柄仅约 15px，CUA 定位困难——操作指引：滑杆拖至 100% 后选中节点，手柄在角部约 28px）。

## 收尾留档 — 2026-09-27（用户指示收尾，循环暂停）

1. **已完成**：工作文档五件套 + AUDIT 骨架；quickstart + 3 个旗舰任务成稿（create-canvas-project / create-nodes / edit-nodes，均运行时走查）；generate-images 占位（付费边界，描述型）；6 个任务占位页；截图 8 张入 manifest（sha256）；多标签覆盖真实缺陷已入 AUDIT 与手册排障。
2. **进度**：12 任务中 3 drafted + 1 描述型占位 + 8 planned（占位页有大纲）。
3. **恢复入口**：按 §1「下一步」顺序执行；每 batch 遵循 规划→实施→验收→commit→push 循环；素材注入方法见 TEST_MEDIA_ASSETS.md。
4. **红线不变**：不触发真实生成、不配置 API Key、不启动 ComfyUI、不用 stash/丢弃他人工作区修改。
5. **待用户输入**：任务优先级重排（当前 Agent 自行定级）；多标签覆盖缺陷复现素材如需入排障章另行授权。
- **Batch M18（2026-09-28，维护轮）**：站点预览实测（http.server 4173 双页 curl 200）；**skill 更新落档**——.agents/skills/web-studio-user-manual/SKILL.md 新增「§9 手册网站构建与发布（VitePress）」：必备四件表、srcExclude/截图引用/脱敏三要点、验收标准、已验证实例指针；三门禁复跑全绿。



- 2026-09-28 M16：例行维护轮——三门禁复跑全绿（自检五项/final audit/verify-docs 1115 文件），无新增增量，无包内改动；待决两项 ①③ 保持标注。
- 2026-09-28 M19：README「以网站形式查看」节落地并实测——4173 被并行 beeftv 预览服务器占用，改用 4174 全 200（index/quickstart/哈希截图）；dist 资产为 /assets/ 哈希路径；端口冲突回退说明入 README。

- **Batch M20（2026-09-30，覆盖缺口修复轮）**：扫描发现导航中的「我的资产」(`/assets`) 与「提示词库」(`/prompts`) 是两个完整页面（561 / 127 行实现）却无任何 how-to——原 12 任务全为画布内操作。**新增 2 任务 + 2 页面 + 10 张截图**：
  - `manage-assets`（完整）：新增/编辑/详情抽屉/搜索/类型筛选/批量下载/导出 zip/删除确认，全链运行时取证，截图 9 张。
  - `use-prompt-library`（简明）：如实记录当前版本来源为空、无添加入口（源码 + 四路由标签扫描双重证据），有内容时的交互按 i18n/源码描述并标注为「来源可用后参考」，不臆造可执行步骤。
  - 同步：README 任务索引、10-tasks/README.md（原占位 stub 漏 8 个页面，已补全为 14 页索引）、20-reference 增「我的资产」「提示词库」两节、90-troubleshooting 增 5 条、task-inventory 12→14、AUDIT 回走表 + 已知问题 + 未覆盖清单。
  - **订正 AUDIT 内部矛盾**：原「未覆盖清单」称「视频/音频真实字节上传未注入」，与同文件 Gate B 表「真实视频 809KB/1.15MB 与音频 1.1MB 注入成功」直接冲突，已删除该过期条目。
  - 自动化教训（已入 AUDIT）：`chromium.launch()` 每次全新 profile，IndexedDB 不保留；跨脚本验证必须用 `launchPersistentContext`。antd 组件定位：资产页新增/编辑是 `Modal`（`[role=dialog]`）、详情是 `Drawer`（`ant-drawer-section`，非 `ant-drawer-content`）；类型筛选点击后应读标题右侧 `N / N` 计数判定，`force:true` 有竞态。
- **Batch M21（2026-09-30，导入链路闭环轮）**：闭合 M20 留下的唯一未覆盖项——「导入资产」端到端回走。实测：建两个带标签文本资产（计数 2/2）→ 导出 `我的资产.zip`（1184 字节）→ 逐个删除至空态 → 导入该 zip → **两个资产完整还原**，标题/正文/标签（风光、长曝光 / 夜景）/来源全部一致，计数回到 2/2，**无 console 错误**。新增截图 `14-manage-assets-import.png`（26→36→37 图），manage-assets 页「导出与导入」节补五步还原流程与「导入为追加而非覆盖」提示；AUDIT 未覆盖清单中该项已移除。当前仅剩「提示词库有内容时的交互」因产品侧无数据源而无法回走（已在未覆盖清单说明）。
- **Batch M22（2026-09-30，导航导览补全轮）**：M20/M21 新增两个页面后，00-quickstart 的「下一步」未提及它们，新用户从快速上手看不到「我的资产」。本轮在 quickstart 新增「顶部导航都有什么」小节——五个入口（我的画布 / ComfyUI 本地 / 提示词库 / 我的资产 / 配置）逐条给出用途与对应任务页链接，并补「首次用生成类功能前先到配置填 API Key」提示；「下一步」补 manage-assets 链接。五个导航标签与 SOURCE_OBSERVATIONS.md §1 的运行时记录逐字一致（含「提示词库」导航名与「提示词中心」页面标题的差异说明）。两门禁复跑全绿。
- **Batch M22 续（2026-09-30，陈旧计数订正）**：M20–M22 增量后多处摘要数字过期，本轮统一订正——README 站点行 `19 页/26 图/14M` → `21 页/37 图/15M`；AUDIT 头部 `12 任务` → `14 任务` + 门禁数字；PROGRESS §1 当前暂停点（12→14 任务、22→25 Markdown、26→37 images）、交付报告（覆盖率 12/12→14/14、验证密度 26→37 张、未覆盖项补「提示词库有内容时的交互」、已知限制补视频资产无编辑与名称不统一）、**§5 阶段状态表**（原停留在 v1 草稿期的「进行中/未开始」五项，全部按实际完成情况更新）。历史 Batch 条目中的旧数字按时间点保留不改。
- **Batch M23（2026-09-30，站点实测与导航修复轮）**：对重建后的 VitePress 站点做真实浏览器实测，**发现并修复 M20 遗留的导航缺陷**——新增的两个页面未进 `.vitepress/config.mjs` 侧边栏，站点读者无法从侧边栏到达（markdown 内部链接可达，但侧边栏缺失）。修复：新增「工作区与素材库」分组收录两页。复测：侧边栏 6 组齐全、manage-assets 页 10/10 图片加载、use-prompt-library 1/1、全站**无任何 HTTP ≥400**、本地搜索输入「资产」返回 32 条命中。构建 21 页 / 37 图 / 15M。**教训：新增任务页必须同步更新 config.mjs 侧边栏，md 链接通过不等于站点导航通过。**
- **Batch M23 续（2026-09-30，构建门禁加固）**：把 M23 发现的侧边栏漏收录变成**可自动拦截的门禁**——`build-site.sh` 第 6 步新增「侧边栏完整性」校验：遍历所有已发布 md（排除 `srcExclude` 的内部账本与 README/PUBLISH），逐一确认其 slug 出现在 `config.mjs` 中，缺失即 warn。**双向验证过**：正常状态 `ok`；临时删掉 `use-prompt-library` 条目后准确报出该页；恢复后重新全绿。PUBLISH.md 六步表同步更新。此举防止后续新增任务页再次漏收录。
- **Batch M24（2026-10-01，图文并茂改写轮）**：响应「手册不应是干巴巴的截图+标题罗列」的要求，先用脚本量化审计 14 页的「中文字数 / 散文行字数」比值，定位最干瘪的页面：**`30-concepts.md` 0 图 + 881 中文字（比值 2.41，最干）**、`create-canvas-project.md`（3.11）、`use-prompt-library.md`（3.67）、`connect-references.md`（3.69）、`edit-nodes.md`（3.89）。
  - **`30-concepts.md` 重写**：0 图 → **5 图**。新增「一句话心智模型」（把画布想成无限大桌面，解释为什么节点可随意摆放/连线只表达引用/改上游影响下游）；补运行时新采集的「添加节点」菜单图（左侧 Dock「+」打开，七种类型逐字可见）与「两个文本节点」实拍图；复用已验证的 `03-create-nodes-all-types`（四种节点视觉身份，组为虚线框）与 `07-connect-references-drop-menu`（贝塞尔连线）+ `04-organize-canvas-appearance`。每张图配解释性正文而非孤立罗列，并补「组节点为什么不特殊」「latest/pinned 解决什么问题」「第 3 条停止≠远端停止最易踩坑」等**为什么**层面的说明。
  - **`create-canvas-project.md` 增补**：解释「无限画布」的空间隐喻、快捷芯片为何会在有内容后消失（并指向 Dock「+」）、项目编号从 1 起的常见误解、自动保存的另一面（删掉不会自动找回→需导出备份）、项目卡「N 节点 · M 连线」的用途；新增 1 张图。
  - 截图 37 → **39**；两门禁 exit 0；构建 21 页 / 39 图 / 15M，侧边栏完整性 ok。
  - 自动化教训：10-tasks/ 下的相对图片路径必须写 `../screenshots/`，写成 `screenshots/` 会被 audit 判为 missing image；manifest 的 `task_id` 必须是 task-inventory 中已存在的 id（概念页配图挂到 `create-nodes`）。
- **Batch M25（2026-10-01，图文并茂续 · 端口与节点信息）**：延续 M24 的比值审计处理次干的三页，运行时新采集 2 张图并补「为什么」层解释：
  - `connect-references.md`（3.69 → **2.50**，1 图 → 2 图）：新增端口实拍图（选中节点后左右各一圆形端口，明确标注左进右出），并补最易误解点的澄清「**连线不是执行顺序**」——连线只表示生成时带上谁，因此可随意增删连线与调整摆放；补「无线模式与连线模式共用同一套引用关系，切换不丢引用」；新增「连线时的常见限制」小节（同节点对不重复连线 / 不能自连 / 组不参与连线 / 非多选输入口只收一条入线）。
  - `edit-nodes.md`（3.89 → **3.31**，2 图 → 3 图）：**修掉一处排版 bug**（原第 30 行图片与「限制：最小 220×160…」文字粘连在同一行）；缩放手柄过小的应对从「留待回走」改为已实测结论（100% 以上手柄约 28px，76% 下实测拖角点成功且锁比保持）；新增节点信息明细图，并说明该面板在**排查问题**时的实际用途（ID 用于反馈缺陷、位置/尺寸确认是否误拖、状态判断是否空闲）。
  - 截图 39 → **41**；两门禁 exit 0；构建 21 页 / 41 图 / 15M，侧边栏完整性 ok。
  - 自动化教训：节点悬浮工具条的按钮**只有 aria-label 没有可见文字**（「查看节点信息」「移除节点」「加入我的资产」等），用 `getByText`/`getByRole(name)` 均定位不到，需走 `button[aria-label="…"]`；端口为 12px 的 `div.size-3.rounded-full.border-2`，靠 hover 节点才出现。
- **Batch M26（2026-10-01，图文并茂续 · 修正错置截图 + 三页增补）**：
  - **修正一处内容错误**：`project-management.md` 原第 20 行把 `02-navigate-canvas-zoom-in-wheel.png`（实为首页项目卡全景）配成「首页全景」图——图片与 caption 恰好对得上，但**文件归属是错的**（它登记在 navigate-canvas 任务下）。改用本就属于本页的 `13-project-management-home-with-card.png`。
  - **清理历史遗留错置文件**：该图自 Batch M4 起就被标注为「并行会话错置文件名的首页截图，与导航无关，未被本页引用」。M26 去掉错误引用后它彻底无引用，**连同 manifest 条目与文件一并删除**，并在 navigate-canvas 页移除对应的「遗留说明」段落。截图 41 → **40**（净减少 1 张错置图，新增 0 张）。
  - `project-management.md`（5.48 → 显著改善）增补：按最近修改排序的实用价值、卡片节点/连线数与加载速度的关系、重命名建议（带用途或日期）、删除无撤销无回收站的警告、导出是换机唯一带走方式、新增「画布项目 vs 我的资产」对照表（两者独立，删项目不影响资产）。
  - `upload-materials.md`（5.20 → 改善）增补：新增「三种上传方式怎么选」场景表、拖文件是最快铺素材方式、上传不收费、**澄清「已选空节点仍新建节点」是有意设计**（保持原始比例/可播放性）、上传后还需连线才能参与生成、删除素材节点的连带效应；并把「上传无内容嗅探」这一实测缺陷从 troubleshooting 提为页面内「已知限制」，给出用户侧判断方法（黑屏/无声→先确认文件本身）。
  - `use-prompt-library.md` 增补：把「为什么值得知道这件事」讲透（用户会以为软件坏了；等待和刷新都不会让提示词出现），并新增「那我该怎么做」推荐路径——用「我的资产」自建本机提示词库（4 步 + 配图），给出比等待未开放来源系统更实际的替代方案。
  - 两门禁 exit 0（14 tasks / 25 markdown / 40 images）；构建 21 页 / 40 图 / 15M。
- **Batch M27（2026-10-01，图文并茂续 · 分组实测 + quickstart 增补）**：
  - `organize-canvas.md`（18.88 → 大幅改善，2 图 → **4 图**）：运行时新采集 2 张**实测**图——刚创建的组（蓝色虚线框，徽标「0 个节点」）与拖入成员后的组（徽标变「1 个节点」，**已完成 0 → 1 的真实取证**）。增补解释：为什么需要组（节点一多就成散沙，按用途圈起来）、**组的边界是「归属」不是「遮挡」**（成员仍可拖出、照常连线生成，组只影响拖动组框时是否联动）、调整组大小只是让更多节点落在框内不会自动吸附、外观设置是项目级的（可给工作稿与展示稿两套配置）、**对齐辅助线与网格吸附解决的痛点不同**（前者临时后者持续）、辅助线不出现的真正原因（附近无可对齐对象）、隐藏连线在连线密集时的用途。
  - `00-quickstart.md` 增补「这五步背后发生了什么」小节：说明五步其实已展示全部工作方式（内容即节点、节点即可生成、标题即项目名、自动保存），并明确**上手不需要任何配置或注册，唯一门槛在生成环节**（需先填 API Key）；「下一步」补 organize-canvas 与 30-concepts 两个入口。
  - 截图 40 → **42**；两门禁 exit 0；构建 21 页 / 42 图 / 15M。
