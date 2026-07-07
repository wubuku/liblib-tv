# FrameOS 画布 — 组件清单

> 实施时文档，**对照 `src/components/frameos/`** 的实际文件结构。
> 数据来源：`find src/components/frameos -type f` + 逐文件审阅。
> 顶层入口见 [`IMPLEMENTATION.md`](./IMPLEMENTATION.md)，拓扑见 [`PAGE_TOPOLOGY.md`](./PAGE_TOPOLOGY.md)，交互见 [`BEHAVIORS.md`](./BEHAVIORS.md)，设计令牌见 [`DESIGN_TOKENS.md`](./DESIGN_TOKENS.md)。

> FrameOS 是与 liblib-tv clone **平行的另一条路由** — 不同布局、不同色板（蓝主色 `#2563EB`、更深背景 `#0D0D0D`）。两者共享 React Flow 库和 `DeletableEdge` 自定义边。

## 顶层组件

| 组件 | 文件 | 角色 | 关键依赖 |
|---|---|---|---|
| `FrameosAppHeader` | `FrameosAppHeader.tsx` | 顶部 60px 浮动条：logo + 下载桌面端 + 金币/积分 | — |
| `FrameosBreadcrumb` | `FrameosBreadcrumb.tsx` | 项目/场景/画布 三级下拉 | `setBreadcrumb` |
| `FrameosHistoryDock` | `FrameosHistoryDock.tsx` | 撤销/重做（接入 history stack） | `undo`, `redo`, `past.length`, `future.length` |
| `FrameosToolRail` | `FrameosToolRail.tsx` | 左侧浮动工具栏 + 添加节点菜单 | `isAddNodeMenuOpen`, `addNode` |
| `FrameosMapDock` | `FrameosMapDock.tsx` | 左下 minimap + 缩放控件 + 整理方式菜单 | `zoomIn/Out/fitView` (useReactFlow), `setOrganizeMode`, `setNodes` |
| `FrameosPromptBar` | `FrameosPromptBar.tsx` | 选中节点下方 AI prompt 栏 | `useViewport()` (跟随 pan+zoom), `isPromptFullscreen` |
| `FrameosNodeToolbar` | `FrameosNodeToolbar.tsx` | 选中节点上方浮动工具条 | `useViewport()` |
| `FrameosNodeEditPanel` | `FrameosNodeEditPanel.tsx` | **调试模式可见**的节点详情面板 | `isDebugMode`, `useViewport()` |
| `FrameosHelpPanel` | `FrameosHelpPanel.tsx` | 快捷键 + 操作指南弹层 | `isHelpOpen` |
| `FrameosDebugToggle` | `FrameosDebugToggle.tsx` | 右下角 DEBUG 开关 | `isDebugMode`, `toggleDebugMode` |
| `icons` | `icons.tsx` | 18+ 内联 SVG 图标 | — |

## 节点组件

| 组件 | 文件 | 节点类型 | 复用 `FrameosNodeShell` | 特性 |
|---|---|---|---|---|
| `FrameosTextNode` | `nodes/FrameosTextNode.tsx` | `text` | ✅ | contenteditable 文本 |
| `FrameosImageNode` | `nodes/FrameosImageNode.tsx` | `image` | ✅ | hover 蒙层 + 预览/编辑按钮 + replace 按钮 |
| `FrameosVideoNode` | `nodes/FrameosVideoNode.tsx` | `video` | ✅ | 中心播放按钮 + hover 时长徽章 + 顶部进度条 + 内嵌 video |
| `FrameosNodeShell` | `nodes/FrameosNodeShell.tsx` | 通用外壳 | — | floating title + 左右 handle + resize handle |

## 共享资源

| 资源 | 文件 | 说明 |
|---|---|---|
| `frameosStore` | `src/store/frameosStore.ts` | 全部 frameos 状态的来源 (Zustand) |
| `FrameosNode` 类型 | `src/types/frameos.ts` | `Node<FrameosNodeData, "text" | "image" | "video">` |
| `frameos-canvas.css` | `src/app/frameos-canvas.css` | 全局动画 keyframes + 拖拽视觉 + handle 样式 |

## 与 liblib-tv 画布共用

| 共享 | 文件 | 说明 |
|---|---|---|
| `@xyflow/react` 库 | `package.json` | 所有节点/边/handle/react flow 基础 |
| `DeletableEdge` | `src/components/nodes/DeletableEdge.tsx` | 边 hover 流动脉冲 + 剪刀删除按钮（frameos 复用 liblib 已实现的） |
| `cn()` utility | `src/lib/utils.ts` | shadcn cn (目前未使用，但保留) |

## 文件树

```
src/components/frameos/
├── FrameosAppHeader.tsx        (180 行)
├── FrameosBreadcrumb.tsx       (190 行)  含三级下拉
├── FrameosDebugToggle.tsx      ( 40 行)  新增
├── FrameosHelpPanel.tsx        (175 行)
├── FrameosHistoryDock.tsx      (105 行)  接入 history
├── FrameosMapDock.tsx          (270 行)  含整理方式菜单
├── FrameosNodeEditPanel.tsx    (270 行)  调试模式
├── FrameosNodeToolbar.tsx      (170 行)  跟随节点
├── FrameosPromptBar.tsx        (340 行)  跟随节点 + 全屏
├── FrameosToolRail.tsx         (180 行)  含添加节点菜单
├── icons.tsx                   (310 行)  18+ SVG
└── nodes/
    ├── FrameosImageNode.tsx    (140 行)
    ├── FrameosNodeShell.tsx    (170 行)  通用外壳
    ├── FrameosTextNode.tsx     ( 65 行)
    └── FrameosVideoNode.tsx    (190 行)  含内嵌 video
```

总行数：约 **2525 行**（不含 CSS / store / types）。
