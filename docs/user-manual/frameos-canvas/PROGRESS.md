# FrameOS 画布用户手册进度与恢复入口

> 本文件是本专项的接力入口。退出当前会话后，下一位 Agent 应先读本文件，再读
> [`task-inventory.yml`](task-inventory.yml)、[`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)、
> [`AUDIT.md`](AUDIT.md) 和 [`screenshots/manifest.yml`](screenshots/manifest.yml)。不要把会话记忆、
> 截图印象或旧摘要当作验证结果。

## 1. 当前暂停点

- 最后整理日期：2026-09-22。
- 当前目标：为已登录的 FrameOS 画布创作者编写中文、任务导向、可回走验证的最终用户手册。
- 当前专项目录：`docs/user-manual/frameos-canvas/`。
- 当前源站：
  `https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- 当前源站身份：用户登录态下的普通画布创作者；当前测试画布显示为“画布 1”。
- 本轮已完成：方法论移植、任务范围确认、一轮真实源站探索、第一批截图和初步观察台账。
- 本轮未完成：正式用户手册正文、Gate A、Gate B、最终机械审计。
- 本轮暂停原因：用户要求先把完整上下文落档，暂不继续探索或编写正文。

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
| 源站 readiness smoke | 已完成 | `SOURCE_OBSERVATIONS.md`、截图 01-03 | 不把 smoke 当作 Gate B |
| 文本节点编辑取证 | 已完成一轮 | `SOURCE_OBSERVATIONS.md`、截图 04 | 正文写成 how-to 前仍需 Gate B 回走 |
| 节点连接取证 | 已完成一轮 | `SOURCE_OBSERVATIONS.md`、截图 05 | 已记录 DOM/边数量证据；仍需 Gate B 回走 |
| 前期探索信息转存 | 已完成本轮 | `SOURCE_OBSERVATIONS.md`、`task-inventory.yml`、本文件第 5-12 节 | 后续只追加新证据，不重复识别已有截图 |
| 正式手册正文 | 未开始 | `10-tasks/` 尚不存在 | 先修正观察台账，再按任务逐页编写 |
| 截图 manifest | 部分完成 | manifest 目前登记 01-03 | 核验 04-05 后决定裁剪、登记或废弃 |
| Gate A | 未开始 | `AUDIT.md` 仍为空结果表 | 正文和 manifest 完成后运行 |
| Gate B | 未开始 | `AUDIT.md` | 按 8 个任务逐项回走 |
| 最终检查与提交 | 未开始 | - | Gate B 后运行文档检查、`npm run check`、提交并推送 |

## 5. 已取得的源站证据

以下内容来自 2026-09-22 的真实浏览器探索；它们可以指导正文，但在 Gate B 前不要标记
任务为 `verified`。

### 5.1 空态和创建入口

- 页面空态标题/提示逐字为“选择一种方式开始创作”。
- 空态可见入口为“文本”“图片”“视频”“音频”“3D导演台”“上传文件”。
- 左栏存在“添加节点”“查看项目资产”“从素材库选择”“本地上传”“帮助”。
- “添加节点”菜单中观察到“文本”“图片”“视频”“音频”“3D模型”“3D导演台”
  “视频剪辑台”“添加资源”“上传文件”。
- 点击空态“文本”后，空态消失并出现“文本节点1”和“（双击编辑文本）”；顶部“撤销”
  变为可用，“重做”仍不可用。
- 本次未触发图片或视频生成。

### 5.2 文本节点编辑

- 源站节点类是 `.vue-flow__node`，不是 `.react-flow__node`；这是重要纠错。
- 选中文本节点后，节点具有 `selected` 状态，并出现节点上方工具条和下方 Prompt 面板。
- 双击 `.text-display` 后，编辑面变为聚焦的
  `textarea.text-edit.nowheel.nodrag.nopan`。
- 输入 `FrameOS 手册测试文本` 时，textarea 值立即变化，但节点显示文本和历史状态尚未变化。
- 按 `Escape` 未提交，也未取消：textarea、值、焦点和节点文本均保持不变。
- 点击画布空白区域 `(1100, 500)` 后，textarea 消失，节点显示更新为
  “文本节点1 FrameOS 手册测试文本”，“撤销”变为可用。
- 对最终手册的准确表述应是“双击进入编辑 → 点击画布空白处失焦提交”；不能声称
  `Escape` 是取消或提交快捷键。

### 5.3 选中节点和图片 Prompt 面板

选中图片节点时观察到以下可见文本或控件：

- “聚焦”“故事版”“参考”“删除连线”“替换参考”；
- “描述你想要的图像，@引用素材”“全屏编辑”；
- “Seedream 5.0 Pro”“2K · 16:9”“高级设置”“60”“30”“5 折”。

这些文本只证明当前选中态的面板内容，不证明生成、计费、模型能力或按钮最终效果。

### 5.4 连接节点

- 已有一个文本节点和一个图片节点时，将文本节点右侧 Handle 拖到图片节点左侧
  Handle，观察到连线成功。
- 连接前边数量为 0，连接后边数量为 1。
- 可访问性边组名形如：
  `Edge from 635585ae-c096-4599-aaac-4ab447153bc6 to 7544ea6e-ad68-44a1-ad96-207f392981fd`。
- 目前只验证了成功连接；连接失败、删除连线和循环/非法连接规则仍未验证。

### 5.5 导航、搜索和整理

- 左下工具条可见“画布小地图”“缩小”“100%”“放大”“适应画布”“搜索节点”
  “一键整理 · 网格整理”“选择整理方式”。
- 点击缩放按钮观察到显示值变化过 `100% -> 87% -> 100%`；不要使用
  `.vue-flow__viewport` 的空 `transform` 字段作为缩放成功判据。
- 搜索框 placeholder 为“搜索节点名称”；输入“图片”时仅显示“图片节点1”。
- 整理菜单包含：
  - “按连线横向 沿连线从左到右分层”
  - “按连线纵向 沿连线从上到下分层”
  - “网格整理 保持相对位置去重叠对齐”
- 鼠标、macOS 触摸板和快捷键的完整行为仍需按帮助声明和实际事件分别回走。

### 5.6 右键菜单、帮助和上下文

- 节点右键菜单观察到“复制 ⌘ C”“创建副本 ⌘ D”“删除 ⌫”。
- 画布空白处右键菜单观察到“添加节点”“上传文件”“粘贴 ⌘ V”“整理”“重置 ⌘ 0”。
- 帮助对话框标题为“快捷键”，内容分为“创作”“缩放”“移动画布”“其他”。
- 帮助面板声明的操作包括：双击空白处添加节点、复制/剪切/粘贴、原地复制、
  拖拽复制、保存；双击节点聚焦填满视口、放大、缩小、重置视图、触控板双指捏合、
  鼠标滚轮/`⌘`滚轮；空格拖动、左键拖动、触控板双指平移、鼠标中键/右键拖动、
  滚轮平移；撤销、重做、删除、搜索节点、小地图、帮助和取消选中。
- “使用教程”会打开外部页面，标题观察为“FrameOS使用手册 - 飞书云文档”。
- breadcrumb 观察到“测试作品 / 测试项目 / 画布 1”；各级切换行为尚未完整回走。
- 创建副本、删除、撤销/重做已在探索中观察到入口或状态变化，但持久化和恢复边界
  仍需 Gate B 明确记录。

## 6. 截图状态

### 已登记且可作为候选正式图

manifest 当前登记 01-03：

- `01-create-first-node-empty-state.png`：1280x660，SHA-256
  `618404c81447bd390c2975203f0a6f9019d498ec242a4083b3399ea99e11768e`。
- `02-canvas-context-left-rail.png`：1280x660，SHA-256
  `4e9e182f5f74aa626f7f275427e508d8dac44348fc3b0540aaeedd6af85d262e`。
- `03-navigate-canvas-toolbar.png`：1280x660，SHA-256
  `1917f85ddb19a7e94ec166cdfa96b03f7132b7f9cfe05ad96792633eab595a35`。

三张图都裁掉了 y=0-60 的账户区域，并且使用实时 DOM bounding box 高亮目标。它们只
证明入口位置和可见上下文，不证明后续交互成功。

### 未登记、已清理、待正文引用

- `04-edit-selected-node.png`：1280x660，SHA-256
  `339e23ce009730d72a3d081f96e3ebe38af8d6a02b834bc12bbd9f2e2a162653`。
- `05-connect-nodes.png`：1280x660，SHA-256
  `73e9a044d845fcb03344438b64259e50d70f3f19ea84458fc6955e37f8360706`。

这两张图已裁掉顶部 60px 账户区域并目视确认，仍是工作区未登记截图。恢复后可以
直接在正文和 manifest 中引用，但必须先确认对应步骤仍与当前源站回走结果一致。

## 7. 已知不一致与纠错清单

恢复后必须先处理以下事项：

1. `SOURCE_OBSERVATIONS.md` 的 readiness smoke 旧段落曾写有
   `.react-flow__node` / `.react-flow__edge`，本轮已改为 `.vue-flow__node` /
   `.vue-flow__edge`，并明确“Vue Flow”。恢复时若看到旧类名，以当前观察台账为准。
2. `SOURCE_OBSERVATIONS.md` 已追加导航、搜索/整理、右键菜单、帮助、breadcrumb、
   网络请求、截图 04/05 处理状态和证据等级约定；后续只追加新观察，不重复识别已有
   截图。
3. `AUDIT.md` 的审计基线 commit 仍是旧值 `c1ffd4391f44e91a07810226f89320655dbbb70f`；
   Gate B 开始时应使用当时实际源站/手册基线，并说明与当前 Git HEAD 的关系。
4. `task-inventory.yml` 的 8 个任务仍是 `pending`；它们已经补充当前已知证据，但仍
   有未验证边界。正式正文完成后才改为 `documented`，Gate B 成功后才改为 `verified`。
5. 当前尚无 `00-quickstart.md`、`10-tasks/`、`20-reference.md`、`30-concepts.md`、
   `90-troubleshooting.md`；不要运行 Gate A 期待通过。

## 8. 下一次接力的精确执行顺序

### A. 先恢复和固化证据

1. 执行：

   ```bash
   cd /Users/yangjiefeng/Documents/wubuku/liblib-tv
   git status --short --branch
   sed -n '1,260p' docs/user-manual/frameos-canvas/PROGRESS.md
   sed -n '1,360p' docs/user-manual/frameos-canvas/SOURCE_OBSERVATIONS.md
   ```

2. 核对 `SOURCE_OBSERVATIONS.md` 的当前事实分类；若源站版本变化，只追加带日期的
   新段落，不覆盖 2026-09-22 的历史证据。
3. 确认已清理的 `04/05` 与 Gate B 当前状态仍一致；如源站版本未变，可直接登记。
4. 更新 `screenshots/manifest.yml`，只登记已检查并会被正文引用的图片。

### B. 编写正文

依次创建以下文件，每个 how-to 必须包含：适用角色、目标、前置条件、入口、原子步骤、
成功判据、取消/恢复、相关任务：

- `00-quickstart.md`
- `10-tasks/create-first-node.md`
- `10-tasks/navigate-canvas.md`
- `10-tasks/edit-selected-node.md`
- `10-tasks/connect-nodes.md`
- `10-tasks/duplicate-delete-history.md`
- `10-tasks/organize-and-search.md`
- `10-tasks/canvas-context.md`
- `10-tasks/help-and-shortcuts.md`
- `20-reference.md`
- `30-concepts.md`
- `90-troubleshooting.md`

正文必须区分：

- 已在源站真实执行的动作；
- 帮助面板声明但本轮未独立执行的手势/快捷键；
- 尚未验证的功能或限制。

### C. Gate A 与 Gate B

1. 先将 8 个任务改为 `documented`，确保每个 `manual_pages` 文件存在、核心任务有
   manifest 截图。
2. 运行 Gate A；修复所有机械问题后才开始 Gate B。
3. 使用已登录的有头浏览器，从手册入口逐条回走：
   `create-first-node`、`navigate-canvas`、`edit-selected-node`、
   `connect-nodes`、`duplicate-delete-history`、`organize-and-search`、
   `canvas-context`、`help-and-shortcuts`。
4. 每条任务把结果、级别、证据和修复写入 `AUDIT.md`。未独立执行的帮助声明不能写成
   `verified`。
5. 最终将任务改为 `verified` 或带原因的 `excluded`，运行 final audit。

### D. 最终质量门与保存

```bash
python3 scripts/verify-docs.py
npm run check
git diff --check
git status --short --branch
```

确认无敏感截图、无占位文本、无错误链接后，再提交并推送。若工作区同时存在其他
开发者的文档 WIP，先阅读并保留，不要用 destructive Git 命令覆盖。

## 9. 当前 Git 工作区快照

在本轮落档提交前：

- 分支：`master`，跟踪 `origin/master`；
- HEAD：`69fb4be4 docs: record FrameOS manual readiness checkpoint`；
- 本轮相关修改：`PROGRESS.md`、`SOURCE_OBSERVATIONS.md`、`task-inventory.yml`；
- 本轮相关未跟踪截图：`screenshots/04-edit-selected-node.png`、
  `screenshots/05-connect-nodes.png`；
- 工作区另有一个与本手册无关的既有修改：
  `docs/design-references/jimeng/jimeng-clone-batch40-gen-send-1680.png`；
  本轮不读取其内容、不覆盖、不提交。
- 未发现本轮产品源代码修改。

本轮已完成截图敏感信息检查；后续接力仍应先核对实际 `git status`，不要假设上面的
快照仍然是当前状态。

## 10. 停止点

当前可以安全暂停。下一次继续的唯一推荐入口是本文件第 8 节 A；不要直接从空白状态
重新探索，也不要从截图反推未验证的用户操作。完成正文、Gate A、Gate B 和最终检查
之前，不能把“FrameOS 画布用户手册已完成”作为项目状态对外宣称。
