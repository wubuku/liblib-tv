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
│ LEFT   │  │ +/- │           CANVAS AREA (React Flow)             │
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
- Per-node topology/structure details live in their component specs under [`components/`](./components/). This page only describes page-level layout.

## Related

- [`PAGE_TOPOLOGY.md` for FrameOS route](./frameos/PAGE_TOPOLOGY.md) — different layout entirely (floating toolbar + prompt bar + breadcrumb header).
- Per-component topology: see [`components/<Name>.spec.md`](./components/).