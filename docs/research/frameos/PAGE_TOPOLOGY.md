# FrameOS 画布页 — 页面拓扑

**目标 URL**: https://www.frameos.cn/#/canvas/01KT17B610DG417X8Q76QZSN8Z/01KWS3TK5BTEH7680N4W9JW4KW

## 视觉层叠（z-index 从高到低）

```
┌──────────────────────────────────────────────────────────────┐
│  z=2000  AppHeader (60px, absolute top:0, padding 0 24px)     │  ← 浮动顶部
│           Logo("帧界 FrameOS") · 下载桌面端 · 金币 · 积分     │
├──────────────────────────────────────────────────────────────┤
│  z=2700  CanvasToolRail (左侧, absolute left:12, top:360)     │  ← 添加节点
│           · 添加节点 (蓝色渐变 pill)                            │
│           · 分隔线                                              │
│           · 从素材库选择                                         │
│           · 本地上传                                             │
│           · 分隔线                                              │
│           · 帮助                                                │
├──────────────────────────────────────────────────────────────┤
│  z=2700  HistoryDock (顶部 right, near logo)                  │
│           · 撤销 / 重做 (32px, dock-btn)                       │
├──────────────────────────────────────────────────────────────┤
│  z=2700  CanvasMapDock (左下, 152×276 minimap+tools)         │
│           · 小地图 (160×100)                                    │
│           · 小地图钉 / 缩小 / 100% / 放大 / 适应 / 一键整理     │
├──────────────────────────────────────────────────────────────┤
│  z=2700  PromptBar (底部中央, 浮动条 514×68)                  │  ← AI prompt
│           · 删除连线 (scissors icon, 浮动在左上)               │
│           · 输入框 "描述你想要的图像，@引用素材" (contenteditable)│
│           · 全屏编辑                                            │
│           · 模型 (帧界 O2) · 1K · 16:9 · 更多参数 · 60 (积分)  │
├──────────────────────────────────────────────────────────────┤
│  z=19-26  Nodes (node-card-wrap, 绝对定位 transform)          │  ← 画布核心
│           · 文本节点1 / 文本节点2 (300×200, bg #1C1C1C)        │
│           · 视频节点1 / 视频节点2 / 视频节点3 (300×169)       │
│           · 图片节点1 / 图片节点2 (300×169 或 225×300)         │
│           · 节点间有 5 条 Bezier 边                            │
├──────────────────────────────────────────────────────────────┤
│  z=0     Canvas Background (#0D0D0D, dots 网格)                │
└──────────────────────────────────────────────────────────────┘
```

## 画布上的节点位置（截屏 1440×900, 100% 缩放）

```
   ┌─ 文本节点1 ───────┐        ┌─ 视频节点1 ───────┐
   │  442, 33          │        │   996, 39          │
   │  300 × 200        │        │   300 × 169        │
   │  "一对怨侣在..."  │        │   [视频封面缩略图] │
   └───────────────────┘        └───────────────────┘
              │                              │
              ▼                              ▼
┌─ 图片节点2 ───────┐            ┌─ 图片节点1 ───────┐ [selected]
│  361, 359         │            │   855, 306         │
│  225 × 300 (竖)   │            │   300 × 169        │
│  [人物肖像图]     │            │   [图缩略图]       │
└───────────────────┘            └───────────────────┘
              ▲                              ▲
              │                              │
┌─ 文本节点2 ───────┐                        │
│  61, 96           │                        │
│  300 × 200        │                        │
│  "（双击编辑）"   │                        │
└───────────────────┘                        │
                                ┌─ 视频节点3 ───────┐
                                │   723, 597         │
                                │   300 × 169        │
                                │   [视频封面] 审核未通过│
                                └───────────────────┘
                                                ┌─ 视频节点2 ───────┐
                                                │   1221, 524        │
                                                │   300 × 169        │
                                                │   [视频封面]        │
                                                └───────────────────┘
```

## 顶部 AppHeader（左 → 右）

```
┌────────────────────────────────────────────────────────────────────────┐
│ [Logo "帧界 FrameOS"]                              [下载桌面端] [金币 16942 ▎积分 19712] │
└────────────────────────────────────────────────────────────────────────┘
```

## FrameOS vs 现有 LibTV 画布 — 关键差异表

| 元素 | FrameOS | 现有 LibTV | 决策 |
|---|---|---|---|
| 顶部布局 | AppHeader 浮动（60px, z=2000）| TopNavBar + ScriptHeader + 工具区 | **重写** — frameos 风格 |
| 左侧 | CanvasToolRail（绝对定位, 浮动） | LeftSidebar (固定 280px) | **新写** FrameosToolRail |
| 右侧 | undo/redo（顶部 header 集成） | 在 TopNavBar 内部 | **集成** FrameosAppHeader |
| 底部工具 | PromptEditor + CanvasMapDock | BottomToolbar（固定底栏） | **新写** FrameosPromptEditor + FrameosMapDock |
| 节点 header | node-floating-title（绝对 top:-22px） | header 在卡片顶部 border-b | **新写** FrameosNodeTitle |
| 节点卡 | node-card (bg #1C1C1C, radius 10px) | bg #212121/#171717, radius xl | **样式重写** |
| 文本节点 | 300×200, paragraph 居中 | border-b header + 内容 | **新写** FrameosTextNode |
| 视频节点 | 300×169, 视频封面 + 播放 | aspect-video + 标题 + 运镜按钮 | **新写** FrameosVideoNode |
| 图片节点 | 视频封面样式 + 替换按钮 (右上下角 18px) | border header + 图 + 编辑面板 | **新写** FrameosImageNode |
| 节点 handle | 单边 left + right (target/source) | Handle width:20 | **复用** CustomHandle 模式 |
| 边 | Bezier 曲线 #86909c 2px | 同 + flowing pulse 已实现 | **复用** DeletableEdge |
| 缩放控件 | dock-btn + 100% 文字 | XYFlow Controls | **新写** FrameosZoomDock |
| 主题色 | 主蓝 #2563EB / #1D4ED8 渐变 + glow | 主青 #09caf5 | frameos 蓝 |
| 背景色 | #0D0D0D | #141414 / #171717 | frameos 更深 |
| 字体 | 系统字体栈 | 系统字体栈 | 相同 |

## 交互模型

- **画布拖拽**: pan + zoom (XYFlow)
- **节点拖拽**: 自由拖动 (XYFlow)
- **节点连接**: 拖 handle → 创建 Bezier 边 (XYFlow)
- **边删除**: hover 边出现剪刀按钮 (复用 DeletableEdge)
- **节点缩放**: 右下角 resize-handle (18×18, opacity:0 → hover:1)
- **顶部 breadcrumb**: 展开菜单 / 默认作品 / 咖啡馆对峙 / 画布 1 — 静态展示，不展开下拉
- **撤销/重做**: 顶部右上角 (HistoryDock)
- **缩放**: dock-btn +/- 或适应画布 / 一键整理
- **PromptBar**: contenteditable 输入框，无后端，纯展示

## 数据契约（mock data）

```ts
type FrameosNode = {
  id: string
  type: "text" | "image" | "video"
  position: { x: number; y: number }
  data: {
    title: string                       // "文本节点1"
    content?: string                    // 文本节点内容
    imageUrl?: string                   // 图片/视频节点
    reviewFailed?: boolean              // "审核未通过" 徽章
  }
  style: { width: number; height: number }  // 文本=300×200, 视频=300×169, 图片=300×169 或 225×300
}
```

## 路由规划

新建路由 `src/app/frameos/canvas/[...path]/page.tsx`，作为 frameos 画布主页。
在现有 `src/app/page.tsx` 加一个链接到 `/frameos/canvas/01KT17B610DG417X8Q76QZSN8Z/01KWS3TK5BTEH7680N4W9JW4KW`。
