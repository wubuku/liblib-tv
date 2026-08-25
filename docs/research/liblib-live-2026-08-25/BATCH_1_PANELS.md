# Batch 1：主工具栏入口面板复核

> 日期：2026-08-25  
> 采样视口：`929x874`  
> 方法：先记录旧克隆缺口，再按价值排序；只有完成原站 DOM、几何和素材提取后才修改克隆。

## 1. 缺口与价值排序

评分为 1-5；“成本”越高表示实现和回归成本越高。

| 入口 | 旧克隆 | 原站事实 | 视觉 | 工作流 | 证据 | 成本 | 决策 |
|---|---|---|---:|---:|---:|---:|---|
| 工具箱 | 约 300px 的左侧占位栏 | 底部主工具条上方 `480x460` 浮层，3 列、25 个真实预设 | 5 | 4 | 5 | 4 | 实现 |
| 素材库 | `288px` 侧栏，关闭关系不完整 | 工具条上方 `240x163` 浮层，两个 `52px` 入口 | 4 | 4 | 5 | 1 | 实现 |
| 角色库 | `320px` 侧栏和彩色占位块 | 居中 `793x710` Modal，详情图、标签和横向角色素材 | 5 | 3 | 5 | 4 | 实现 |
| 历史记录 | `320px` 侧栏和彩色占位块 | `90vw x calc(100vh - 160px)` Modal，筛选、缩放、批选和真实结果图 | 5 | 3 | 5 | 2 | 实现 |
| 快捷键 | 带遮罩的 `480px` 居中对话框 | 底部按钮上方 `905x447` 无遮罩面板，4 列命令 | 5 | 3 | 5 | 2 | 实现 |
| 教程 | 结构接近但锚点、字号有误 | `104x154` 菜单，固定在教程按钮正上方 | 2 | 2 | 5 | 1 | 调整 |

这批优先处理的不是后端能力，而是六个一级入口的空间拓扑。它们都能从首屏直接进入，旧克隆的“侧栏或通用 Modal”模型会让用户在第一次点击时立即感到产品不一致。

## 2. 原站提取事实

完整 DOM、图片 URL、自然尺寸和计算样式保存在 [`panel-audit.json`](panel-audit.json)。关键几何如下：

| 面板 | 原站边界或锚点 | 内容证据 |
|---|---|---|
| 工具箱 | `x=160, y=341, w=480, h=460` | 25 个预设；首行图片 `141x141`，`y=410.5` |
| 素材库 | `x=320, y=638, w=240, h≈163` | “我的素材库”“预设素材库”两个入口 |
| 角色库 | `x=68, y=82, w=793, h=710` | 4 张详情图和 23 张角色缩略图 |
| 历史记录 | `x≈46.45, y=80, w≈836.09, h=714` | 首屏 3 张 `144x144` 结果图 |
| 快捷键 | `x=12, y=354.5, w=905, h=446.5` | 4 列快捷键，不阻断画布背景 |
| 教程 | `x=557, y≈647.4, w=104, h≈153.6` | 4 个教程/帮助入口 |

原站截图位于 `docs/design-references/liblib-original-{toolbox,material-library,character-library,history,shortcuts,tutorial-menu}-2026-08-25.png`。

## 3. 克隆实现

- `ToolboxPanel` 使用原站 25 个标题和本地化图片，保留滚动、hover 与使用态。
- `MaterialLibraryPanel` 按按钮锚点定位，入口可关闭且与其他主面板互斥。
- `CharacterLibraryPanel` 改为响应式 Modal，使用 27 张本地素材；“应用到画布”会创建并选中新图片节点。
- `HistoryPanel` 改为响应式 Modal，提供类型 Tab、排序、缩放、批选、收藏与结果操作的前端状态。
- `KeyboardShortcutsDialog` 改为按钮锚定的无遮罩 4 列面板；窄屏时可滚动且避让两排底部工具条。
- 教程菜单按原站宽高与底部锚点调整。
- `canvasStore.addNode` 统一补全新节点默认宽高并选中新节点，修复角色素材已添加但不可见的问题。
- `scripts/download-liblib-panel-assets.mjs` 可从审计 JSON 重建 `public/images/liblib-panels`，`manifest.json` 记录来源。

## 4. 验证

桌面证据：

- `docs/design-references/liblib-clone-batch1-toolbox-2026-08-25.png`
- `docs/design-references/liblib-clone-batch1-material-library-2026-08-25.png`
- `docs/design-references/liblib-clone-batch1-character-library-2026-08-25.png`
- `docs/design-references/liblib-clone-batch1-history-2026-08-25.png`
- `docs/design-references/liblib-clone-batch1-shortcuts-2026-08-25.png`
- `docs/design-references/liblib-clone-batch1-tutorial-2026-08-25.png`

在 `390x844` 复核角色库、历史记录和快捷键：历史面板边界为 `x=19.5, y=80, w=351, h=684`，快捷键为 `x=12, y=288, w=366, h=447`；可见按钮和标签未检测到横向文本溢出。角色素材应用后节点数增加且新节点被选中。

## 5. 有意保留的边界

- 素材和历史均为本地 mock，不声称连接用户账户或生成服务。
- 工具箱“使用”、历史下载/查看等只验证前端状态，不发起真实业务请求。
- 原站素材只作为本项目的研究证据和本地原型资产；来源 URL 保存在清单中，下载脚本避免手工漂移。
