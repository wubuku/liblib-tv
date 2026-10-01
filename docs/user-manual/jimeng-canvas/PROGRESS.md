# 即梦画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`AUDIT.md`](AUDIT.md) 和 [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、
> 截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-10-01。
- 当前目标：为已登录的即梦（jimeng.jianying.com）AI 画布创作者编写中文、任务导向、
  可回走验证的最终用户手册；方法与本仓库
  `docs/user-manual/frameos-canvas/` 完全一致。
- 当前专项目录：`docs/user-manual/jimeng-canvas/`（本目录）。
- 当前源站：`https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f`（测试项目「测试项目」）。
- 当前状态：**主体手册已成稿并通过质量门**（2026-09-23 取证/成稿/回走，2026-09-24 站点构建）。
  14 个任务全部 `verified`；正文 19 页
  （00-quickstart、10-tasks/×14、20-reference、30-concepts、90-troubleshooting）、
  22 张登记截图；Gate A、Gate B、final 审计通过；
  画布基线（2 节点 0 连线）已恢复并「已保存」。
- **2026-10-01 增量（两处，均为对既有台账记载的纠正）**：
  1. 修复真实质量门失败：`README.md` 与 `TEST_MEDIA_ASSETS.md` 存在越界链接
     `../../CANVAS_TEST_MEDIA.md`，`audit_manual.py` 判定 `link escapes manual root`，
     实际导致 gate-a 与 final **均为 exit=1**。此前本文件与 `README.md` 记载的
     「final OK / 审计通过」**当时并不成立**（属未复跑的乐观记载），现已改为纯文本
     引用并复跑，两道门现均 exit=0。
  2. 补齐 `use-node-toolbar` 覆盖缺口：图片节点工具条（与视频工具条不同套）、
     视频修剪内联修剪条、截取帧（首帧/尾帧直出图片节点 vs 自定义帧选择条）。
     三处均为既有台账已有证据但正文缺失的内容，非新增断言。
- 优先级原则（用户授权）：FrameOS 等价功能 或 视频/参考图生成常识关键功能 =
  重要、优先。据此旗舰层 5 项：create-first-node、navigate-canvas、connect-nodes
  （补录的等价任务）、use-node-toolbar、prepare-generation。
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
| 浏览器会话准备 | 已完成 | 登录会话（CDP attach 隔离 Chrome :9333） | 无 |
| 逐任务探索取证 | 已完成 | `SOURCE_OBSERVATIONS.md` §2.1–2.17（当日基线 + 16 组任务取证） | 改版时按第 8 节 C 重走受影响任务 |
| 截图 manifest | 已完成 | `screenshots/manifest.yml` 22 条记录（含真实 SHA-256） | 重拍时同步更新哈希 |
| 正式手册正文 | 已完成 | 19 页正文（00/10-tasks×14/20/30/90） | 无 |
| Gate A / Gate B / final | 已完成 | `AUDIT.md` 结果表；2026-10-01 复跑两道门均 exit=0 | 增量修改后必须复跑 |
| 手册网站构建 | 已完成 | VitePress 站点（`build-site.sh` 六步全绿） | 改内容后重新构建 |

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

已完成 22 张正式截图（`01-`–`22-`），全部登记在 `screenshots/manifest.yml` 并附真实
SHA-256，Gate A/final 校验哈希一致。管线沿用 FrameOS：实时 DOM 高亮 overlay →
截图裁剪（隐藏账户/积分区域）→ 落盘 → 登记 manifest（真实 SHA-256）→ 清除 overlay。
截图涉及用户作品名/租户名时必须遮蔽（参考 FrameOS 截图 17 的 PIL 高斯模糊做法）。
重拍或新增截图后必须同步更新 manifest 哈希，否则 final 审计报 `sha256 mismatch`。

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

### B. 浏览器会话（已完成，2026-09-23）

已用 CDP attach 用户隔离 Chrome（:9333）打开并登录
`https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f`，
project-id 与画布上下文已回填至第 1 节。**改动正文不需要登录**；只有重走源站
（Gate B 复验或改版重测）才需要重新建立登录会话。

### C. 逐任务探索取证（已完成，2026-09-23；下述为改版重走时的顺序）

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

### C2. 已知未取证面（下一位 Agent 的候选工作，2026-10-01 记录）

**取证通道（2026-10-01 已就绪）**：仓库内新增 Playwright 取证脚本，可用于关闭下表缺口：

| 脚本 | 作用 |
|---|---|
| `scripts/jimeng-browser.mjs` | 启动**独立**有头 Chromium（CDP 端口 **9444**，独立 profile `/tmp/jimeng-manual-profile`），固定 viewport 1280x720、locale zh-CN、时区 Asia/Shanghai |
| `scripts/jimeng-probe.mjs` | 通过 CDP 只读探测当前页面登录态/画布态 |
| `scripts/jimeng-open-canvas.mjs` | 把该浏览器导航到测试画布 URL |

> **端口与隔离**：本机 **9222 已被另一个 Chrome 占用**（其他开发者/用户），切勿 attach
> 或复用。取证一律用 9444 + 独立 profile，不读取任何既有浏览器会话或 cookie。
> 登录需用户本人手动完成；脚本本身不接触凭据。

**下表缺口需登录后才能关闭**（主体 / 时间线 / 导演台 / 标题重命名 / 布局 / 快捷键 / 上传 / 智能布局 已于 2026-10-01 关闭）：

| 元素 | 已知事实 | 缺什么 |
|---|---|---|
| **主体**节点 ✅ | **已于 2026-10-01 补齐**：完整操作页 `10-tasks/subject-node.md`，含创建、改名/描述、四种导入入口、从画布选择的选取模式与取消方式、`subject` DOM 契约与「无浮动工具条」结论 | 仅剩：四种导入方式的完成态、保存到主体库结果、@主体 引用效果（生成属扣费边界） |
| **时间线**节点 ✅ | **已于 2026-10-01 补齐**：完整操作页 `10-tasks/timeline-node.md`，含 1055×182 尺寸、内嵌控制栏逐字、5 秒一格刻度尺、状态串三段式、仅 1 个手柄 | 仅剩：添加素材面板、分割/删除/重排执行结果、全屏编辑、导出时间线（对外产出动作需授权） |
| **导演台**（Beta） ✅ | **已于 2026-10-01 补齐**：操作页 `10-tasks/director-node.md`，含 `node-external` DOM 契约、281×281、唯一按钮「进入导演台」、连线禁用规则 | 3D 导演工作台本身在**画布之外**，本手册范围止于画布（正文已声明） |
| 上传完成态 ✅ | **已于 2026-10-01 关闭**：filechooser 实选 PNG → 节点数 +1、标题取文件名、状态串逐字 `<file>.png: Upload complete`、顶栏「已保存」 | 无（资产库内「点选→确认」的插入动作仍未走完：资产库无视频素材、图片页为空态） |
| 智能布局 ✅ | **已于 2026-10-01 关闭**：同为 2 行、行间距 400、尺寸不变；与宫格布局肉眼差别很小 | 无 |
| 时间线 添加素材/分割/删除/重排 ✅ | **已于 2026-10-01 关闭**：三选项菜单逐字；图片默认 5.0 秒（aria `Clip 1, 图片, 5.0 seconds`）；必须先点刻度尺移动播放头才能分割（否则提示「将播放头移动到目标片段内进行剪切。」）；1→2 分割、2→1 删除、Shift+→ 重排均实测 | 仅剩拖拽重排路径与 Q/W 裁剪未验证 |
| 画布标题重命名 ✅ | **已于 2026-10-01 关闭**：点击标题→输入框→Enter 提交→改回→Enter 还原，闭环实测成功；另发现输入框内 ⌘A 不能全选 | 无 |
| 宫格/智能布局 ✅ | **宫格布局已于 2026-10-01 关闭**：菜单浮层 180×88、两项 172×38 逐字；5 节点重排坐标已留档；⌘Z 可完全还原；**发现布局不会自动缩放视口** | 仅剩「智能布局」未单独执行（与宫格同一菜单的另一项） |
| ⌘V 粘贴 ✅ | **已于 2026-10-01 关闭并推翻旧结论**：⌘C 后 ⌘V 使节点数 5→6，粘贴生效（面板未声明） | 无 |
| ⌘A 全选 ✅（结论） | 面板未列出；焦点置于 `.react-flow` 后按 ⌘A 选中数不变 → **产品本就没有该快捷键**，非环境限制 | 无 |
| Shift+点选 ✅（结论） | 面板未列出；实测**反向取消选中**（1 选中 → 0 选中）→ 不是加选手势 | 无 |
| 官方快捷键面板全表 ✅ | **已于 2026-10-01 关闭**：四组逐字抓取；纠正「全屏 F」为「预览视图 F」，补回漏记的「宫格视图 G」；逐项实测并发现 `G` 弹「此快捷键当前不可用」 | 时间线组（⌘B/Q/W）与文本编辑组未逐键实测（需进入对应编辑态） |
| ⌘Z 撤销边界 ✅ | 同会话内可撤销删除（3→2→3→2→1 连续回退）；删除后先 reload 则 10 次 ⌘Z 无恢复 → 结论为「可撤销删除，但不跨刷新」 | 无 |

这些是**范围/环境决策**而非产品缺陷：均不影响已交付任务的正确性，正文也已逐项
标注。补写时沿用本节 C 的取证规范，并严守第 7 节的扣费边界。

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
- 本目录已全部入库：`README.md`、`PROGRESS.md`、`SOURCE_OBSERVATIONS.md`、
  `task-inventory.yml`、`TEST_MEDIA_ASSETS.md`、`AUDIT.md`、`PUBLISH.md`、
  `build-site.sh`、`.vitepress/`、`10-tasks/`×14 页、`screenshots/`×22 图 +
  `manifest.yml`。构建产物 `dist/`、`cache/`、`node_modules/` 由本目录
  `.gitignore` 排除，不入库。
- 工作区中与本手册无关的既有修改保持原样，不并入本手册提交；不使用
  `stash` / `reset --hard` / `checkout --` / `clean`。

## 10. 停止点

当前可安全暂停：手册已成稿并通过两道质量门，画布基线已恢复，无扣费风险残留。
下一次继续有三个入口，按优先级：

1. **源站改版** → 按第 8 节 C 重走受影响任务（`task-inventory.yml` 中带
   `source-drift-alert` 的三个任务优先），重拍截图并更新 manifest 哈希；
2. **补写未覆盖面** → 按第 8 节 C2 表格逐项取证成稿；
3. **纯文档增量** → 直接改正文，**无需登录**，但改完必须复跑两道门：
   ```bash
   python3 ../../.agents/skills/web-studio-user-manual/scripts/audit_manual.py \
     docs/user-manual/jimeng-canvas --phase gate-a
   python3 ../../.agents/skills/web-studio-user-manual/scripts/audit_manual.py \
     docs/user-manual/jimeng-canvas --phase final
   ```
   并在第 11 节追加一行增量记录。**不要在未复跑的情况下声称门通过**——
   2026-10-01 正是发现此前「final OK」的记载并不成立（实际 exit=1）。

## 11. 完成记录

### 2026-09-23（初版）

- 14 个任务状态：`verified`（见 `AUDIT.md` 结果表与限制披露）。
- Gate A OK、final OK（14 tasks / 23 Markdown / 22 images）、
  Gate B 关键流程回走通过（创建/导航/连线/生成面板/删除撤销）。
- 未覆盖项与环境限制在 `AUDIT.md`「未覆盖与已接受限制」全量披露；
  正文各页以「已验证说明」小节逐页划分 实测/声明/待验证。

> **勘误（2026-10-01）**：上条「final OK」在初版记录时**并未经复跑验证**，事后实测
> `audit_manual.py --phase final` 返回 exit=1（`README.md`/`TEST_MEDIA_ASSETS.md` 越界
> 链接）。已修复并复跑通过。教训：**质量门结论必须来自当次命令输出，不能沿用旧结论**。

### 2026-10-01（增量一：质量门修复 + 覆盖缺口补齐）

- 修复越界链接，gate-a 与 final 复跑均 exit=0（14 tasks / 24 Markdown / 22 images）。
- `use-node-toolbar.md` 补齐：图片节点工具条、视频修剪内联修剪条、截取帧两种路径；
  证据改按「当日实测 / 复刻研究 SOURCE_FACT / 扣费边界未验证」三层标注。
- `20-reference.md`：节点类型表拆分图片/视频空态与带内容态，新增「不耗积分的本地
  加工操作」表；`90-troubleshooting.md`：新增 4 条工具条/加工类症状。
- 新增本文件第 8 节 C2「已知未取证面」表，把此前散落在各页「待验证」的缺口汇总
  为下一位 Agent 的可执行清单。
- 后续增量维护入口：源站改版时按第 8 节 C 重走受影响任务，重拍截图并更新
  manifest 哈希；改版监测可复用 docs/design-references/jimeng/ 的进化巡逻扫描。

## 12. 手册网站构建（2026-09-24）

按 skill §9（TDCanvas 实战沉淀模式）为手册构建 VitePress 静态站点：

- 新增站点四件套：`build-site.sh`（六步一键构建+产物校验）、
  `.vitepress/config.mjs`（zh-CN、本地中文搜索、侧边栏按任务分组、
  srcExclude 排除内部账本、README→index 首页改写）、`package.json`（仅
  vitepress devDependency）、`PUBLISH.md`（构建/预览/发布/脱敏审查/运维 FAQ）；
  另有 `.gitignore`（dist/cache/node_modules 不入库）。
- 构建实测：六步全绿——dist 20 页 HTML（19 内容页+404）、22 张截图全部经
  引用进入 dist/assets（哈希命名，逐链接 200）、无 .md 残留链接、总体积 12M；
  `python3 -m http.server` 预览实测首页/任务页/参考页 200、站点标题正确。
- 坑与修复：bash 中 `$VAR` 紧跟全角括号时变量名会吞入多字节首字节报
  unbound variable——脚本内变量后一律用 ASCII 标点或空格分隔（已修复）。
- 发布前须按 PUBLISH.md 完成截图脱敏审查（截图文稿帧含 AI 生成人物画面）。
- 收尾补记（2026-09-24）：`npm run lint` 会扫描磁盘上各手册站点的 `.vitepress/dist`
  构建产物导致误报——已在 `eslint.config.mjs` 的 globalIgnores 增加
  `docs/user-manual/**/.vitepress/{dist,cache}/**`；`npm run check` 重新全绿。
