# 即梦画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`AUDIT.md`](AUDIT.md) 和 [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、
> 截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-09-23。
- 当前目标：为已登录的即梦（jimeng.jianying.com）AI 画布创作者编写中文、任务导向、
  可回走验证的最终用户手册；方法与本仓库
  [`docs/user-manual/frameos-canvas/`](../frameos-canvas/PROGRESS.md) 完全一致。
- 当前专项目录：`docs/user-manual/jimeng-canvas/`（本目录）。
- 当前源站：`https://jimeng.jianying.com/ai-tool/ai-canvas/<project-id>`（具体画布
  project-id 由用户提供的登录会话决定，首次取证时回填）。
- 当前状态：**确认门已过（2026-09-23 用户授权 Agent 定级）**，14 个任务与优先级
  已定稿（`scope_authorization.user_confirmed: true`）；已弹出有头浏览器等待用户
  登录即梦。用户登录并示意继续后，即可开始探索、截图、记录与编写。
- 优先级原则（用户授权）：FrameOS 等价功能 或 视频/参考图生成常识关键功能 =
  重要、优先。据此旗舰层 5 项：create-first-node、navigate-canvas、connect-nodes
  （补录的等价任务）、use-node-toolbar、prepare-generation。
- 尚未发生：正式浏览器探索、正式截图、手册正文、Gate A、Gate B。
- 2026-09-23 补充：已完成复刻材料评估（见第 5 节与
  [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md) §1.1），发现源站 09-21→09-23
  存在活跃改版（视频工具条「补帧/提示词反推」撤为「工具」入口）。探索顺序上把
  「当日基线盘点」列为第 C 步的第一项。

## 2. 范围与安全边界

### 纳入范围

只记录即梦 `/ai-tool/ai-canvas/:projectId` 画布内的创作操作：节点创建、选择、编辑、
连接、复制、删除、撤销恢复；视图平移缩放、小地图、编组与布局整理；节点工具条与
生成面板（到执行前一步）；媒体预览、资产库与本地上传；帮助、快捷键与画布上下文。

### 不纳入范围（比 FrameOS 更严格，必须遵守）

- **一切真实生成与按积分计费的操作**：生成发送钮、局部重拍、智能超清、补帧、
  提示词反推、智能改图、配音/音乐生成等按钮一律只观察、不点击执行；
- 充值、订阅、会员购买、积分详情、账户页（源站订阅页已在复刻研究中按用户决策除牌）；
- 登录流程本身；`jimeng.jianying.com` 画布之外的任何页面；
- 把 `docs/research/jimeng-canvas/README.md` 里的 `CLONE_DECISION`（复刻侧决策）或
  `/jimeng` 本地 clone 的行为写成源站事实；
- 未通过 DOM/ARIA、网络状态或可重复交互证据验证的快捷键和手势。

### 与 FrameOS 手册的关键差异（写作前先读）

1. 源站画布是 **React Flow (xyflow v12)**（`.react-flow__node`），不是 FrameOS 的
   Vue Flow；选择器、边形态（源站边由全屏 canvas 层绘制，无 `.react-flow__edge`
   DOM）完全不同，不得互抄。
2. 导航语义不同：即梦空白左键拖拽**不平移**、滚轮=垂直平移、ctrl+滚轮=缩放
   （batch 21 实测）；FrameOS 是左键拖动空白不平移、滚轮未验证。两份手册各自实测。
3. 即梦画布几乎每个工具条都含 VIP✦/积分扣费入口，安全边界远比 FrameOS 紧。
4. 正式桌面视口仍为 `1280x720`、locale `zh-CN`；早期复刻研究用 1680×826 提取，
   其屏幕坐标不可复用到手册截图。

### 测试媒体

授权的本地图片、音频、视频登记在 [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)
（与 FrameOS 手册共用同一批文件，2026-09-23 抽查核对仍在）。只用于上传、挂载、
预览和连接测试；不得触发生成动作。

## 3. 方法论和完成标准

- 规范来源：`.agents/skills/web-studio-user-manual/SKILL.md`（同一套 references、
  `scripts/audit_manual.py`、`scripts/highlight-target.js`）。
- 流程与 FrameOS 手册相同：确认门 → 逐任务真实浏览器探索取证（先 DOM/网络后截图）
  → 任务导向中文正文 → Gate A 机械审计 → Gate B 逐任务回走 → final 审计。
- 每条正式步骤必须使用源站当前 DOM/ARIA 可见标签，记录入口、原子动作、成功判据、
  取消/恢复路径和必要的网络证据。
- 截图只解释界面，不单独证明交互成功。每张正式截图必须同时存在于文件系统、
  manifest 和正文引用中，并有真实 SHA-256。
- Gate A：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/jimeng-canvas --phase gate-a
  ```

- Gate B：按手册从入口重新走完每条任务，记录到 `AUDIT.md`；作者记忆不能替代回走。
- 最终审计：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/jimeng-canvas --phase final
  ```

只有所有纳入任务为 `verified` 或有理由的 `excluded`，且无 Blocker/Major，才可报告
手册完成。因扣费边界只记录到“执行前一步”的任务（如 prepare-generation），其成功
判据必须写成可回走的面板状态，不得把“未执行生成”当作缺陷。

## 4. 阶段状态

| 阶段 | 状态 | 当前产物 | 下一步 |
|---|---|---|---|
| 快速扫描 | 已完成 | `task-inventory.yml` + 本文件第 5 节 | 无 |
| 候选任务确认门 | 已完成（用户授权定级） | 14 个任务、`user_confirmed: true`、优先级原则入档 | 无 |
| 浏览器会话准备 | **进行中** | 有头浏览器已打开即梦登录页 | 等用户登录并示意开始 |
| 逐任务探索取证 | 未开始 | `SOURCE_OBSERVATIONS.md` 仅有骨架与候选线索索引 | 登录后按第 8 节 C 顺序取证 |
| 截图 manifest | 未开始 | `screenshots/manifest.yml` 为空表 | 探索时同步登记 |
| 正式手册正文 | 未开始 | `10-tasks/` 为空 | 取证后编写 |
| Gate A / Gate B / final | 未开始 | `AUDIT.md` 空结果表 | 正文完成后依序执行 |

## 5. 已有证据线索（候选，不是手册证据）

`docs/research/jimeng-canvas/README.md`（2000+ 行）记录了 2026-09-12 起约 480 个
批次的源站提取，viewport 1680×826、CDP attach 用户已登录 Chrome。它为候选任务
提供了**线索**（布局骨架、工具条逐字、菜单结构、导航语义、受阻面），但：

- 提取日期距今较久，站点可能已改版；正式取证必须全部在当前登录会话重提；
- 其中 `CLONE_DECISION` 是复刻侧决策、`BLOCKED_BY_FIXTURE` 是未完成观察，
  两者都不得写成源站事实；
- 已知受阻面（探索时先复测再决定是否可写）：工具∨ 菜单项从未展开
  （BLOCKED_BY_EXTRACTION）；截取帧下拉在部分会话不展开（batch 81/84 判定源站侧
  变化/缺陷）；智能超清/补帧真实流程因积分副作用从未执行。
- 候选任务 → 线索批次的对照索引见 [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md) 第 1 节；
  四类复刻材料（研究 README、45 张源站截图、23 份进化巡逻扫描、91 个验证器 +
  40 个复刻组件）的用途与边界地图见同文件 §1.1。
- **已确认漂移**：巡逻扫描显示源站 09-21→09-23 之间改版——视频工具条一级条目
  由 7 项（含 补帧/提示词反推）变为 6 项 +「工具」入口（775→670 宽），节点右键
  菜单禁用项出现「无需重做操作/无需撤销操作」提示。`task-inventory.yml` 的
  use-node-toolbar / duplicate-delete-history / audio-node-voice 已挂 drift-alert。
  这印证了「正式取证必须当日重提」的原则，也说明旧线索只能缩小探索范围、
  不能直接当事实引用。

## 6. 截图状态

尚无正式截图。首次取证时从 01 开始编号，沿用 FrameOS 的管线：实时 DOM 高亮
overlay → 截图裁剪（隐藏账户/积分区域时先确认隐私面）→ 落盘 → 登记 manifest
（真实 SHA-256）→ 清除 overlay。截图涉及用户作品名/租户名时必须遮蔽
（参考 FrameOS 截图 17 的 PIL 高斯模糊做法）。

## 7. 已知风险与注意事项

1. 即梦是真实计费产品：所有 ✦/VIP/积分按钮、Agent 抽屉发送、生成发送钮都在
   扣费边界内。宁可少记录一个面板，不可多点击一次扣费按钮。
2. 用户真实项目名、租户名、素材名不得写入台账正文；截图必须遮蔽。
3. 复刻研究记录过“源站截图捕获超时”“菜单不展开”等站点 A/B 变化：遇到行为与
   旧记录不符时，以当前会话实测为准，并在 `SOURCE_OBSERVATIONS.md` 记录差异。
4. 自动化经验可参考 FrameOS 的 `SOURCE_OBSERVATIONS.md` §13.12（cua 坐标点击、
   合成 contextmenu、drag/scroll ack 超时但生效、节点虚拟化计数等），但那是
   Vue Flow 站点的教训，逐条重新验证后再用。
5. 工作区可能存在其他在途修改（当前 git status 中有与本手册无关的 jimeng 设计
   参考图和 LIBTV 文档改动）：只提交本目录文件，不碰无关文件，不用破坏性 Git 命令。

## 8. 下一次接力的精确执行顺序

### A. 确认门（已完成，2026-09-23）

用户授权 Agent 按以下原则定级：FrameOS（帧界）手册中存在相同或等价任务的功能、
或视频生成/参考图生成常识中的关键功能 = 重要、优先。已据此定稿 14 个任务并补录
`connect-nodes`（FrameOS 等价任务，源站连线交互从未被系统取证）。

### B. 浏览器会话（进行中）

已用有头浏览器打开 `https://jimeng.jianying.com/`，等待用户登录。用户示意继续后：
回填第 1 节的 project-id 与画布上下文，更新 `AUDIT.md` 审计基线，然后进入 C。

### C. 逐任务探索取证（定稿顺序）

1. **当日基线盘点**（新增，因 09-21→09-23 已确认改版）：对画布做一次 DOM 巡检，
   重建「A 视频工具条 / B 节点右键菜单 / C 音频生成面板 / D 上传节点」当日快照，
   逐字记录「工具」菜单内容（旧证据中 补帧/提示词反推 已不是一级条目）；
2. `create-first-node`（旗舰）
3. `navigate-canvas`（旗舰）
4. `connect-nodes`（旗舰，补录任务：Handle 拖拽连线、选中、删除）
5. `use-node-toolbar`（旗舰，先视频节点后图片/多选工具条，含「工具」菜单展开）
6. `prepare-generation`（旗舰，只到发送前一步）
7. `edit-text-node`（完整）
8. `duplicate-delete-history`（完整）
9. `assets-and-upload`（完整，本地上传仅用 TEST_MEDIA_ASSETS 授权文件）
10. `media-playback`（完整）
11. `organize-group-layout`（完整）
12. `audio-node-voice`（完整，生成类按钮只记录不点击）
13. `ai-agent-drawer`（简明，不发送任何消息）
14. `canvas-context`（简明）
15. `help-and-shortcuts`（简明）

每个任务产出：入口/原子动作/成功判据/取消路径 + DOM/网络证据 + 步骤截图；全部
写入 `SOURCE_OBSERVATIONS.md` 并同步 manifest。遇到扣费边界立即停止并记录按钮状态。

### D. 编写正文

文件清单与 FrameOS 相同结构：`00-quickstart.md`、`10-tasks/*.md`（每个纳入任务
一页）、`20-reference.md`、`30-concepts.md`、`90-troubleshooting.md`。每个 how-to
必须包含：适用角色、目标、前置条件、入口、原子步骤、成功判据、取消/恢复、相关
任务。正文区分三类内容：已执行动作 / 面板或帮助声明未验证 / 扣费或环境限制未验证。

### E. Gate A → Gate B → final

1. 全部任务改 `documented`，运行 Gate A 并修复；
2. 用已登录会话按手册回走（更新 `AUDIT.md` 基线 commit），任务改 `verified` /
   `excluded`；
3. `python3 scripts/verify-docs.py`、`npm run check`（需要 node ≥24，先
   `export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"`）、`git diff --check`，
   再提交。提交只含本目录与同步更新的登记文件。

## 9. 当前 Git 工作区快照

- 分支：`master`，跟踪 `origin/master`。
- 本目录为本轮新建：`README.md`、`PROGRESS.md`、`SOURCE_OBSERVATIONS.md`、
  `task-inventory.yml`、`TEST_MEDIA_ASSETS.md`、`AUDIT.md`、
  `screenshots/manifest.yml`（空表）。`10-tasks/` 暂为空目录（Git 不跟踪空目录）。
- 工作区中与本手册无关的既有修改
  （`docs/design-references/jimeng/jimeng-clone-batch{1,40,50}-*.png`、
  `docs/research/LIBTV_SOURCE_FRESHNESS_REINSPECTION.md`）保持原样，不并入本手册提交。

## 10. 停止点

当前可安全暂停：账本已建立，未做任何浏览器操作，未产生任何扣费风险。下一次
继续的唯一推荐入口是本文件第 8 节 A（确认门）；确认门未通过前，不得开始正式
浏览器探索、截图或成稿。
