# LeftSidebar Specification

## Overview
- **Target file:** `src/components/LeftSidebar.tsx`
- **Screenshot:** `docs/design-references/canvas-desktop-full.png`
- **Interaction model:** Static (no scroll behavior)

## DOM Structure
```
<div> <!-- sidebar container -->
  <button> <!-- 添加节点 -->
    <div>
      <svg />
    </div>
  </button>
  <button> <!-- 打开工具箱 -->
    <svg />
  </button>
  <button> <!-- 素材库 -->
    <svg />
  </button>
  <button> <!-- 角色库 -->
    <svg />
  </button>
  <button> <!-- 历史记录 -->
    <svg />
  </button>
  <button> <!-- 快捷键 -->
    <svg />
  </button>
  <button> <!-- 教程 -->
    <svg />
  </button>
</div>
```

## Computed Styles (exact values from getComputedStyle)

### Container
- display: flex
- flexDirection: column
- gap: 4px (estimated)
- padding: 8px (estimated)
- backgroundColor: transparent

### Sidebar Buttons (default state)
- width: 32px
- height: 32px
- borderRadius: 8px
- backgroundColor: transparent
- border: 0px solid #525252
- cursor: pointer
- display: flex
- alignItems: center
- justifyContent: center

### Sidebar Button Icons
- width: 16px
- height: 16px
- color: #f7f7f7

## States & Behaviors

### Hover State
- **Trigger:** Mouse hover on button
- **backgroundColor:** changes to #353639 (--color-background-hover)
- **transition:** background-color 0.15s ease

### Active/Selected State
- **backgroundColor:** different shade (possibly more opaque)
- **Icon color:** may change to accent color

### Tooltip
- Shows on hover after delay
- Contains button label text
- Position: right of button

## Text Content
- 添加节点 (Add Node)
- 打开工具箱 (Open Toolbox)
- 素材库 (Material Library)
- 角色库 (Character Library)
- 历史记录 (History)
- 快捷键 (Shortcuts)
- 教程 (Tutorial)

## Assets
- Icons: 7 inline SVGs (one per button)
- Icon viewBoxes: 16×16, 17×17 (varies)

## Responsive Behavior
- **Desktop (1440px):** Full sidebar visible
- **Tablet (768px):** Sidebar may collapse to icons only
- **Mobile (390px):** Sidebar hidden or becomes bottom menu
