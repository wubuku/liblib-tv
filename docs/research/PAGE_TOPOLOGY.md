# LibTV Canvas Page Topology

## Page Type
**Canvas Editor** — A node-based flow/graph editor for video storyboarding and production.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      TOP NAV BAR (48px)                      │
│  [Logo] [ProjectName] [CanvasTab] ... [VIP] [Credits] [Avatar] │
├──────┬──────────────────────────────────────────────────────┤
│      │                                                       │
│ SIDE │              CANVAS AREA (React Flow)                 │
│ BAR  │                                                       │
│      │    [Node] ──edge── [Node] ──edge── [Node]            │
│  7   │         ╲                      ╱                      │
│ btns │          ╲                    ╱                       │
│      │           └──── [Node] ─────┘                        │
│      │                                                       │
│      │                                                       │
├──────┴──────────────────────────────────────────────────────┤
│                   BOTTOM TOOLBAR                             │
│  [AssetMgmt] [Arrange] [Minimap] [Grid] [Zoom: 54%]        │
└─────────────────────────────────────────────────────────────┘
```

## Sections (Top to Bottom)

### 1. Top Navigation Bar
- **Type:** Fixed, horizontal
- **Height:** 48px
- **Background:** Transparent (inherits page bg #141414)
- **Z-index:** High (above canvas)
- **Interaction:** Static (no scroll behavior)
- **Components:**
  - Logo (left)
  - Project name input (editable textbox)
  - Canvas tab selector (dropdown)
  - Spacer
  - Notification icon
  - VIP promotion button with badge
  - Credits display (64)
  - User avatar

### 2. Left Sidebar
- **Type:** Fixed, vertical
- **Width:** ~48px (icon buttons)
- **Background:** Transparent
- **Z-index:** Above canvas
- **Buttons (top to bottom):**
  1. 添加节点 (Add Node)
  2. 打开工具箱 (Open Toolbox)
  3. 素材库 (Material Library)
  4. 角色库 (Character Library)
  5. 历史记录 (History)
  6. 快捷键 (Shortcuts)
  7. 教程 (Tutorial)

### 3. Canvas Area (Main)
- **Type:** Scrollable, zoomable
- **Background:** #171717 (--bg-canvas)
- **Framework:** React Flow (node-based graph editor)
- **Interaction model:** Pan + zoom + drag nodes
- **Node types visible:**
  - **Text/Script node** ("剧本") — contains script text
  - **Image nodes** — display generated images with dimensions
  - **Storyboard group** ("分镜图") — groups related images
  - **Script execution node** — shows steps (确认镜头, 准备资产, 合成提示词)
  - **Edge connections** — SVG paths between nodes

### 4. Bottom Toolbar
- **Type:** Fixed, horizontal
- **Position:** Bottom of viewport
- **Components:**
  - 资产管理 (Asset Management) — text button
  - 整理画布 (Arrange Canvas) — icon button, shortcut: Option+Shift+F
  - 切换小地图 (Toggle Minimap) — icon button
  - 网格吸附 (Grid Snap) — icon button
  - 缩放选项 (Zoom Options) — shows "54%"

### 5. Floating Elements
- **"正在跟随" (Following) status** — bottom-right, with ESC cancel button
- **Alert area** — for notifications

## Node Details

### Script Node ("剧本")
- Title bar with icon and name
- Content: Multi-line text (script content)
- Has "打开脚本节点 →" button
- Connected via edges to image nodes

### Image Nodes
- Header with icon, filename, dimensions (e.g., "1808 × 1024")
- Image preview with watermark overlay
- Has close/settings buttons
- Connected to other nodes via edges

### Storyboard Group ("分镜图")
- Contains grouped image thumbnails
- Has label "分镜图 · 第一集：咖啡馆对峙-图片组"
- Contains multiple sub-images

### Script Execution Node
- Shows workflow steps:
  - 确认镜头 (Confirm shots)
  - 准备资产 (Prepare assets)
  - 合成提示词 (Compose prompts)
- Has "打开脚本节点 →" action button
- Connected to multiple input/output nodes
