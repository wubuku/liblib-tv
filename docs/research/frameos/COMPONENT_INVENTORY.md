# FrameOS 画布 — 组件清单

> 实施时文档，**对照 `src/components/frameos/`** 的实际文件结构。
> 数据来源：`find src/components/frameos -type f` + 逐文件审阅。
> 顶层入口见 [`IMPLEMENTATION.md`](./IMPLEMENTATION.md)，拓扑见 [`PAGE_TOPOLOGY.md`](./PAGE_TOPOLOGY.md)，交互见 [`BEHAVIORS.md`](./BEHAVIORS.md)，设计令牌见 [`DESIGN_TOKENS.md`](./DESIGN_TOKENS.md)。

> FrameOS 是与 liblib-tv clone **平行的另一条路由** — 不同布局、不同色板（蓝主色 `#2563EB`、更深背景 `#0D0D0D`）。两者共享 React Flow 库和 `DeletableEdge` 自定义边。

## 顶层组件

| 组件 | 文件 | 角色 | 关键依赖 |
|---|---|---|---|
| `FrameosAppHeader` | `FrameosAppHeader.tsx` | 顶部 100px 浮动条：logo + 撤销/重做 + 下载桌面端 + 金币/积分 | `undo`, `redo`, `past`, `future` |
| `FrameosBreadcrumb` | `FrameosBreadcrumb.tsx` | 项目/场景/画布 三级下拉 | `setBreadcrumb` |
| `FrameosToolRail` | `FrameosToolRail.tsx` | 左侧浮动工具栏 + 添加节点菜单 | `isAddNodeMenuOpen`, `addNode` |
| `FrameosMapDock` | `FrameosMapDock.tsx` | 左下 minimap + 缩放控件 + 整理方式菜单 | `zoomIn/Out/fitView` (useReactFlow), `setOrganizeMode`, `setNodes` |
| `FrameosSidePanel` | `FrameosSidePanel.tsx` | 左侧汉堡菜单触发的抽屉（项目/场景/画布列表） | — |
| `FrameosMaterialLibrary` | `FrameosMaterialLibrary.tsx` | 右侧抽屉：素材库（图片/视频） | — |
| `FrameosPromptEditor` | `FrameosPromptEditor.tsx` | 选中节点下方 AI prompt 栏 | `useViewport()` (跟随 pan+zoom), `isPromptFullscreen` |
| `FrameosNodeFloatingToolbar` | `FrameosNodeFloatingToolbar.tsx` | 选中节点上方浮动工具条（57px above） | `useViewport()` |
| `FrameosNodeEditPanel` | `FrameosNodeEditPanel.tsx` | **调试模式可见**的节点详情面板 | `isDebugMode`, `useViewport()` |
| `FrameosHelpPanel` | `FrameosHelpPanel.tsx` | 快捷键 + 操作指南弹层 | `isHelpOpen` |
| `FrameosContextMenu` | `FrameosContextMenu.tsx` | 全局右键菜单（节点 / 画布空白处） | `openContextMenu()` |
| `FrameosToast` | `FrameosToast.tsx` | 全局通知（撤销/复制/删除 等） | `showToast()` |
| `FrameosConfirmDialog` | `FrameosConfirmDialog.tsx` | 删除节点/边的确认弹窗 | `pendingConfirm`, `requestConfirm()` |
| `FrameosGenerationOverlay` | `FrameosGenerationOverlay.tsx` | 全屏生成中遮罩 | — |
| `FrameosAlignmentGuides` | `FrameosAlignmentGuides.tsx` | 节点拖动时的对齐辅助线 | — |
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
├── FrameosAppHeader.tsx              (355 行)  logo + undo/redo + 金币积分
├── FrameosAlignmentGuides.tsx        ( 50 行)  拖动对齐线
├── FrameosBreadcrumb.tsx             (190 行)  含三级下拉
├── FrameosConfirmDialog.tsx          ( 50 行)  删除确认
├── FrameosContextMenu.tsx            ( 80 行)  全局右键菜单
├── FrameosEdge.tsx                   ( 60 行)  蓝虚线边
├── FrameosGenerationOverlay.tsx      ( 40 行)  全屏生成遮罩
├── FrameosHelpPanel.tsx              (175 行)
├── FrameosMapDock.tsx                (270 行)  含整理方式菜单
├── FrameosMaterialLibrary.tsx        (110 行)  素材库抽屉
├── FrameosNodeEditPanel.tsx          (270 行)  调试模式
├── FrameosNodeFloatingToolbar.tsx    (170 行)  跟随节点
├── FrameosPromptEditor.tsx           (340 行)  跟随节点 + 全屏
├── FrameosSidePanel.tsx              ( 90 行)  汉堡菜单抽屉
├── FrameosToast.tsx                  ( 70 行)  全局通知
├── FrameosToolRail.tsx               (300 行)  含添加节点菜单（8 类型）
├── icons.tsx                         (310 行)  18+ SVG
└── nodes/
    ├── FrameosImageNode.tsx          (140 行)
    ├── FrameosNodeShell.tsx          (170 行)  通用外壳
    ├── FrameosTextNode.tsx           ( 65 行)
    └── FrameosVideoNode.tsx          (190 行)  含内嵌 video
```

总行数：约 **3535 行**（不含 CSS / store / types）。
