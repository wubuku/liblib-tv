# FrameOS 画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`AUDIT.md`](AUDIT.md) 和 [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、
> 截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-09-23（第二轮）。
- 当前目标：为已登录的 FrameOS 画布创作者编写中文、任务导向、可回走验证的最终用户手册。
- 当前专项目录：`docs/user-manual/frameos-canvas/`。
- 当前源站：
  `https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- 当前源站身份：用户登录态下的普通画布创作者；测试画布为“画布 1”。
- 本轮已完成：正式手册正文 12 个文件全部写成（`00-quickstart.md`、8 个
  `10-tasks/*.md`、`20-reference.md`、`30-concepts.md`、`90-troubleshooting.md`）；
  8 个任务置为 `documented`；**Gate A 通过**（8 tasks / 17 Markdown / 19 images OK）；
  `verify-docs.py`、`git diff --check`、`npm run check` 通过。
- 本轮未完成：**Gate B 真实浏览器回走**（登录态浏览器标签页已被关闭，需用户重新
  提供登录会话）与 final audit。
- 本轮暂停原因：Gate B 需要用户重新打开并登录帧界画布。

## 2. 范围与安全边界

### 纳入范围

只记录 FrameOS `#/canvas/:workspaceId/:canvasId` 画布内的：

- 节点创建、选择、编辑、连接、复制、删除和历史恢复；
- 画布拖动、缩放、聚焦、搜索和整理；
- 画布上下文、添加资源入口、帮助和快捷键；
- 后续经安全验证的图片、音频、视频上传及节点预览/参考素材流程。

### 不纳入范围

- 账户、登录、计费、积分、发布和项目外页面；
- 真实图片生成、视频生成或任何可能扣费的 Provider 调用；
- 将本地 clone 的行为、`docs/research/frameos/` 的推断或 StoryAI 行为写成 FrameOS
  源站事实；
- 未通过 DOM/ARIA、网络状态或可重复交互证据验证的快捷键和手势。

### 测试媒体

可使用的本地图片、音频、视频及其字节数登记在
[`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)。它们只用于上传、挂载、预览和连接测试；
不得触发生成动作。

## 3. 方法论和完成标准

- 规范来源：`.agents/skills/web-studio-user-manual/SKILL.md`。
- 技能包已移植到当前项目，`references/`、`scripts/audit_manual.py` 和
  `scripts/highlight-target.js` 均在该目录内。
- 任务优先级由用户授权 Agent 自行定级，当前深度为 `thorough`；任务库存见
  [`task-inventory.yml`](task-inventory.yml)。
- 每条正式步骤必须使用源站当前 DOM/ARIA 可见标签，记录入口、原子动作、成功判据、
  取消/恢复路径和必要的网络证据。
- 截图只解释界面，不单独证明交互成功。每张正式截图必须同时存在于文件系统、manifest
  和正文引用中，并有真实 SHA-256。
- Gate A：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/frameos-canvas --phase gate-a
  ```

- Gate B：按手册从入口重新走完每条任务，记录到 `AUDIT.md`；不能把本轮作者记忆替代
  回走证据。
- 最终审计：

  ```bash
  python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
    docs/user-manual/frameos-canvas --phase final
  ```

只有所有纳入任务为 `verified` 或有理由的 `excluded`，且无 Blocker/Major，才可报告
手册完成。

## 4. 阶段状态

| 阶段 | 状态 | 当前产物 | 下一步 |
|---|---|---|---|
| 技能移植 | 已完成 | `.agents/skills/web-studio-user-manual/` | 无 |
| 候选任务确认 | 已完成 | `task-inventory.yml` | 保持 8 个任务范围，除非新的源站证据要求拆分 |
| 源站 readiness smoke | 已完成 | `SOURCE_OBSERVATIONS.md` §1-9、截图 01-03 | 不把 smoke 当作 Gate B |
| 第一轮取证（文本编辑/连接） | 已完成 | `SOURCE_OBSERVATIONS.md` §2-8、截图 04-05 | 已并入第二轮汇总 |
| 第二轮逐任务回走取证 | 已完成 | `SOURCE_OBSERVATIONS.md` §13、截图 06-19 | 正文写作时区分“已执行/声明/未验证” |
| 截图 manifest | 已完成 | manifest 登记 01-19（含真实 SHA-256） | 截图重拍时同步更新哈希与正文引用 |
| 正式手册正文 | 已完成 | `00-quickstart.md` + 8 个 how-to + reference/concepts/troubleshooting | Gate B 发现问题时修订 |
| Gate A | 已通过 | gate-a OK（8 tasks / 17 Markdown / 19 images） | 修订正文后重跑 |
| Gate B | 未开始 | `AUDIT.md` 结果表为回走占位 | 需用户重新提供登录态浏览器；按第 8 节 C 逐项回走 |
| 最终检查与提交 | 随轮次执行 | git log | Gate B 通过后任务置 verified/excluded，跑 final audit 再提交推送 |

## 5. 已取得的源站证据

权威记录在 [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)。第一轮（2026-09-22）
见 §1-9；第二轮（2026-09-23）见 §13，包含：

- 持久化与历史边界：图内容跨刷新持久，撤销历史不跨会话；撤销可恢复被删节点并连带
  恢复连线。
- 创建：添加节点菜单两组入口、双击空白打开“选择节点类型”菜单、新建节点自动选中。
- 编辑：文本节点选中态只有“全屏查看/下载”工具条（无 Prompt 面板，纠正第一轮表述）；
  textarea 编辑、点击空白提交、Escape 无效；图片节点面板（聚焦/故事版/参考、删除连线、
  替换参考、Seedream 5.0 Pro、2K·16:9、高级设置、积分显示）与“聚焦模式”（局部框选）。
- 连线：边 ID 含 `text_out`/`prompt_in` Handle 名；删除连线按钮 1→0；拖拽重建 0→1；
  空白处释放即取消。
- 复制/删除/历史：右键菜单含禁用的“复制图片”“重新生成”；创建副本命名 `（副本）`、
  偏移 (+30,+30)、不复制连线；⌘D/⌫/⌘Z/⌘⇧Z 实测生效。
- 搜索/整理：搜索结果点击会选中并缩放聚焦节点；无匹配显示“无匹配节点”；网格整理
  微调布局并适配视口；三种整理方式菜单逐字。
- 导航：缩小/放大约 13% 步进；适应画布 273%→100%；⌘0 重置；小地图开关卸载/恢复；
  左键拖动空白**不平移**（与帮助声明不一致）；滚轮/触摸板/空格拖动未验证。
- 帮助：快捷键面板全量逐字（含 ⌘X/⌘F/M/?/⌘S/⌥拖动复制等）；已列“实测生效”与
  “环境限制未验证”两份清单。
- 上下文：面包屑三级下拉（画布列表含新建/重命名/删除，只观察未执行）；项目资产面板
  （角色/物品/环境）；“选择素材”对话框（筛选、批量操作、本地上传；文件 input 的
  accept 显示支持 image/video/audio/txt/docx/pdf）。
- 网络事实（第一轮）：`/api/canvas/ops`、`/api/canvas/detail`、
  `/api/canvas/realtime/connect_token`、`/api/asset/list` 返回 200。

## 6. 截图状态

manifest 已登记 01-19（全部含真实 SHA-256、任务、步骤、locator 与 alt）：

- 01-03：第一轮 readiness smoke（空态入口、左栏、缩放工具条）。
- 04-05：第一轮文本编辑与连线（已确认哈希一致并在本轮登记）。
- 06-19：第二轮逐任务取证（添加菜单、创建结果、选中态、图片面板、重建连线、右键
  菜单、搜索、网格整理、整理方式、面包屑下拉、项目资产、素材库、帮助快捷键、聚焦
  模式）。17 已对用户自有项目名称做模糊遮蔽。

## 7. 已知不一致与纠错清单

1. 文本节点选中态没有下方 Prompt 面板；第一轮 §5.3 的面板内容属于图片节点。
   以 §13.3 为准。
2. 节点右键菜单比第一轮多出禁用项“复制图片”“重新生成”；以 §13.6 为准。
3. 帮助面板快捷键清单比第一轮完整（⌘X、⌘F、M、?、⌘+/⌘−、⌘S、⌥拖动复制）；
   以 §13.9 为准。
4. 帮助声明“左键拖动”移动画布，但实测左键拖动空白处不平移；正文必须区分。
5. `AUDIT.md` 的审计基线 commit 仍是旧值；Gate B 开始时更新为当时实际基线。
6. 自动化环境备忘见 §13.12（定位器点击挂起、隔离世界 evaluate、drag/scroll 超时
   但生效、cua 无右键、节点虚拟化、剪贴板/全选限制）。下一轮取证先读它。

## 8. 下一次接力的精确执行顺序

### A. Gate B（唯一剩余阶段）

正文与 Gate A 已完成。下次接力只需完成 Gate B：

1. 请用户在有头浏览器中重新登录帧界并打开画布
   `#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`。
2. 更新 `AUDIT.md` 审计基线 commit 为当时 HEAD。
3. 依据手册（而不是记忆）逐条回走 8 个任务：
   `create-first-node`、`navigate-canvas`、`edit-selected-node`、`connect-nodes`、
   `duplicate-delete-history`、`organize-and-search`、`canvas-context`、
   `help-and-shortcuts`。每条任务把结果、级别、证据和修复写入 `AUDIT.md`。
4. 回走中发现手册与实际不一致时：修订正文、重跑 Gate A、再重走受影响流程。
5. 全部通过后把任务置为 `verified`（或带 `exclusion_reason` 的 `excluded`），运行：

   ```bash
   python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py \
     docs/user-manual/frameos-canvas --phase final
   ```

6. 最终质量门与提交：

   ```bash
   python3 scripts/verify-docs.py
   npm run check
   git diff --check
   ```

   确认无敏感截图、无占位文本、无错误链接后提交并推送。

### B. 自动化环境备忘

回走时先读 `SOURCE_OBSERVATIONS.md` §13.12：本应用对 Playwright 定位器 click 会挂起
（用坐标点击）；locator.evaluate 在隔离世界；drag/scroll 可能超时但已生效（以 DOM
状态为准）；cua 无右键（用合成 contextmenu 事件）；节点虚拟化会隐藏视口外节点；
合成键盘事件不携带剪贴板数据、⌘A 行为不定。

### C. 历史背景（已完成，勿重做）

- 第一轮取证（2026-09-22）：readiness smoke、文本编辑、连接，见 `SOURCE_OBSERVATIONS.md`
  §1-9；
- 第二轮取证（2026-09-23）：8 任务逐项回走取证，见 §13；
- 截图 01-19 均已登记 manifest，勿重复拍摄。

## 9. 当前 Git 工作区快照

- 分支：`master`，跟踪 `origin/master`；
- 本轮（2026-09-23 收尾）提交内容：`PROGRESS.md`、`SOURCE_OBSERVATIONS.md`、
  `task-inventory.yml`、`AUDIT.md`、`screenshots/manifest.yml`、截图 06-19；
- 截图 04-05 已在上一轮提交（d85758e9），本轮仅登记进 manifest；
- 工作区中与本手册无关的既有修改
  （`docs/design-references/jimeng/jimeng-clone-batch{1,40,50}-*.png`）按用户收尾
  指令以独立 chore 提交，不在本手册提交内；
- 未发现本轮产品源代码修改。

## 10. 停止点

当前可安全暂停。下一次继续的唯一推荐入口是本文件第 8 节 A（编写正文）；不要重新
探索已验证的交互，不要从截图反推未验证的用户操作。完成正文、Gate A、Gate B 和最终
检查之前，不能把“FrameOS 画布用户手册已完成”作为项目状态对外宣称。
