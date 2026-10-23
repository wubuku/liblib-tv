# FrameOS 画布功能用户手册

本目录只覆盖 `frameos.cn` 的画布编辑功能，不覆盖账户、计费、发布或生成费用。

## 想自己动手试试？打开本站的复刻原型

> 本手册描述的是**真实产品 FrameOS**；本站另有一个**交互原型**（本地 mock 数据），
> 让你不用真账号也能把上面的操作练一遍。

- **怎么打开**：仓库根目录执行 `npm install && npm run dev`（固定端口 `4317`），
  然后打开 <http://localhost:4317/>（站点根目录），
  再点顶栏最左侧的 **LibTV 芯片** ⇒ 进 `/frameos/canvas/demo`。
- **怎么交互测试**：Prompt 编辑器里输入文字 ⇒ 点生成 ⇒ 看 mock 结果进画布；
  画布空白处**右键** ⇒ 上下文菜单；点节点 ⇒ 浮动工具条 ＋ 右侧编辑面板；
  `⌘Z` / `⌘⇧Z` 试撤销与重做；框选多节点后试成组。
- **哪些是 mock**：生成永远返回**本地 mock 结果**，不调用任何模型、账号或计费接口；
  FrameOS 用独立 store，不与 LibTV/即梦共享状态。

⇒ 完整清单（所有克隆页）见 [`docs/CLONE_PAGES_INDEX.md`](../../CLONE_PAGES_INDEX.md)。

## 当前状态

- 目标源站：`https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- 目标角色：已登录的普通画布创作者
- 深度：`thorough`
- 方法：由 `.agents/skills/web-studio-user-manual/` 的任务优先级、运行时取证、截图和回走审计流程管理。
- 证据边界：只有当前登录态浏览器中实际观察到的 DOM、ARIA、交互结果和安全网络证据才写入正文；早期 `docs/research/frameos/` 资料只作为候选线索。

## 入口

- [`00-quickstart.md`](00-quickstart.md)：最短路径上手（创建两个节点并连线）。
- [`10-tasks/create-first-node.md`](10-tasks/create-first-node.md)：创建节点。
- [`10-tasks/navigate-canvas.md`](10-tasks/navigate-canvas.md)：移动视野与缩放。
- [`10-tasks/edit-selected-node.md`](10-tasks/edit-selected-node.md)：编辑选中的节点。
- [`10-tasks/connect-nodes.md`](10-tasks/connect-nodes.md)：连接与删除连线。
- [`10-tasks/duplicate-delete-history.md`](10-tasks/duplicate-delete-history.md)：复制、删除与撤销恢复。
- [`10-tasks/organize-and-search.md`](10-tasks/organize-and-search.md)：搜索节点与整理布局。
- [`10-tasks/group-and-ungroup.md`](10-tasks/group-and-ungroup.md)：多节点成组、换色、排列与解组。
- [`10-tasks/canvas-context.md`](10-tasks/canvas-context.md)：面包屑、项目资产与素材入口。
- [`10-tasks/help-and-shortcuts.md`](10-tasks/help-and-shortcuts.md)：帮助与快捷键总表。
- [`20-reference.md`](20-reference.md)：界面分区与菜单文字速查。
- [`30-concepts.md`](30-concepts.md)：画布核心概念。
- [`90-troubleshooting.md`](90-troubleshooting.md)：按症状排障。
- [`task-inventory.yml`](task-inventory.yml)：任务范围、频率、影响和覆盖状态。
- [`PROGRESS.md`](PROGRESS.md)：探索、编写和验证进度。
- [`AUDIT.md`](AUDIT.md)：真实浏览器回走审计。
- [`SOURCE_OBSERVATIONS.md`](SOURCE_OBSERVATIONS.md)：按证据类型记录的源站观察与截图识图台账。
- [`screenshots/manifest.yml`](screenshots/manifest.yml)：正式截图登记与哈希。
- [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)：已获授权的本地图片、音频、视频测试输入及付费生成禁令。

正文区分“已验证 / 产品声明 / 未验证”三类内容；Gate B 回走完成前，任务不会标为 `verified`。
