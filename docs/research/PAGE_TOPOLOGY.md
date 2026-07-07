# LibTV Canvas Page Topology

> Current state of the rebuilt clone. Diagrams show actual rendered layout.

## Page Type
**Canvas Editor** — Node-based flow graph editor for video storyboarding and production.

## Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TOP NAV BAR (h-12 = 48px)                     │
│  [□ Logo]  [未命名项目] [画布 2 ▾]                  [🔔] [⚡ 会员.. 64] [FrameOS] [👤] │
│   bg #141414, border-b #262626                                    │
├─────────────────────────────────────────────────────────────────────┤
│        ┌──────────────────────────────────────────────────────────┐  │
│        │   SCRIPT HEADER (脚本标题节点 "第一集：咖啡馆对峙" + 正在跟随) │  │  absolute top-3, centered
│        ├──────────────────────────────────────────────────────────┤  │
│        │                                                          │  │
│        │  ┌─────┐                                                │  │
│ LEFT   │  │ +/- │           CANVAS AREA (React Flow)             │  │
│ BAR    │  │ Tbx │                                                │  │
│ (abs   │  │ Img │            [Nodes connected by edges]         │  │
│ left)  │  │ Chs │                                                │  │
│ h-8 w-8│  │ Hst │                                                │  │
│ 7 btns │  │ Shc │                                                │  │
│        │  │ Tut │                                                │  │
│        │  └─────┘                                                │  │
│        │                                                          │  │
│        ├──────────────────────────────────────────────────────────┤  │
│        │                                                          │  │
│        │              BOTTOM TOOLBAR                              │  │
│        │  ┌──────────────────────────────────────────────────┐    │  │
│        │  │ [资产管理] | [整理] [👤] [+大青色+] [整理节点] [⭐] [⏰] [📷] [?] | 54%  │    │  │
│        │  └──────────────────────────────────────────────────┘    │  │
│        │       centered floating, bg rgba(20,20,20,0.7), blur     │  │
│        │                                                          │  │
└────────┴──────────────────────────────────────────────────────────┘
```

## Sections (top-to-bottom of visible viewport)

### 1. Top Navigation Bar (`<TopNavBar>`)
- **Type:** Fixed, horizontal (not `sticky` since `page.tsx` uses flex column).
- **Height:** `48px` (`h-12`).
- **Background:** `#141414` with `border-b border-[#262626]`.
- **Children (left to right):**
  - Logo (24×24 film/camera glyph SVG)
  - Project name input (`未命名项目`, click-to-edit)
  - Canvas tab dropdown (`画布 2 ▾`)
  - Notification bell
  - VIP + credits combined button (`⚡ 会员特惠37折 | ⚡ 64`)
  - FrameOS link (added later)
  - User avatar (round, 32×32)

### 2. Script Header (`<ScriptHeader>`)
- **Type:** Absolutely positioned at top center (`fixed top-[60px] left-1/2 -translate-x-1/2`)
- **z-index:** 30
- **Content:** Compact 节点-style chip showing document icon + "第一集：咖啡馆对峙" + small connection-handle dots on each side.
- **Behavior:** Hover ↔ no state change. Pure display.

**Note:** Earlier versions of this component included the "正在跟随" banner; that banner now lives in page.tsx directly above the canvas area.

### 3. Left Sidebar (`<LeftSidebar>`)
- **Type:** Absolutely positioned at left center (`absolute left-0 top-1/2 -translate-y-1/2`).
- **Layout:** Vertical column of 7 icon-only buttons, 32×32 each, 4px gap.
- **z-index:** 40.
- **Buttons (top to bottom):** 添加节点, 工具箱, 素材库, 角色库, 历史记录, 快捷键, 教程.
- Each button has `hover:bg-[rgba(255,255,255,0.08)]` and `active:bg-[rgba(255,255,255,0.15)]`.

### 4. Canvas Area (React Flow)
- **Type:** Fills remaining viewport (`flex-1`).
- **Background:** `#171717` (`bg-canvas` token).
- **Contents:** Nodes (script, image, video, etc.) connected by custom `DeletableEdge` paths.
- **Interaction model:** Pan + Zoom + Drag (React Flow), with `panOnScroll`, `zoomOnScroll`, `panOnDrag` enabled.
- **Defaults:** `fitView`, `minZoom=0.1`, `maxZoom=2`, `snapGrid=[20, 20]`.
- **Backgrounds:** Optional dot grid via `<Background>` component (toggled by `useUIStore.showGrid`).

### 5. Following Status Banner (NEW location)
- **Type:** Absolutely positioned at top center of canvas (`absolute top-0 left-1/2 -translate-x-1/2`).
- **Background:** `#8B25E4` (purple).
- **Content:** "正在跟随" + "取消ESC" text.
- **Behavior:** Click "取消ESC" or press `Escape` to exit (no actual follow-mode implemented; pure UI).

### 6. Bottom Toolbar (`<BottomToolbar>`)
- **Type:** Fixed, centered horizontally, near bottom (`fixed bottom-4 left-1/2 -translate-x-1/2`).
- **Background:** `rgba(20,20,20,0.7)` + `backdrop-blur-md` + border `border-[#363636]`.
- **Border-radius:** `rounded-xl` (12px).
- **Padding:** `p-1.5`.
- **Children (left to right):** 资产管理 (text button) | [整理, 👤, 大青色+, 整理节点, ⭐, ⏰, 📷, ?] (icon buttons) | 54% (zoom).
- **Tooltip:** Each icon button uses `@base-ui/react/tooltip` with 300ms delay.

## Notes

- The currently rendered clone uses a **centered floating bottom toolbar** matching the original site (not a docked bottom strip). Earlier iterations had a docked bar that did not match the original.
- The handle is positioned and styled in `globals.css` (see `/* Node Handle */` block). The handle is the connection source — drag from it to create edges.

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
