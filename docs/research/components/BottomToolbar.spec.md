# BottomToolbar Specification

## Overview
- **Target file:** `src/components/BottomToolbar.tsx`
- **Screenshot:** `docs/design-references/canvas-desktop-full.png`
- **Interaction model:** Static (no scroll behavior)

## DOM Structure
```
<div> <!-- toolbar container -->
  <button> <!-- 资产管理 -->
    <div>
      <svg />
    </div>
    <div>资产管理</div>
  </button>
  <button> <!-- 整理画布 -->
    <div>
      <svg />
    </div>
  </button>
  <button> <!-- 切换小地图 -->
    <div>
      <svg />
    </div>
  </button>
  <button> <!-- 网格吸附 -->
    <div>
      <svg />
    </div>
  </button>
  <button> <!-- 缩放选项 -->
    54%
  </button>
</div>
```

## Computed Styles (exact values from getComputedStyle)

### Container
- display: flex
- flexDirection: row
- gap: 4px (estimated)
- padding: 8px (estimated)
- backgroundColor: transparent
- position: fixed
- bottom: 0
- left: 0
- right: 0

### Asset Management Button (text button)
- fontSize: 16px
- fontWeight: 400
- color: #f7f7f7
- backgroundColor: transparent
- borderRadius: 8px
- padding: 0px 12px
- height: 28px
- cursor: pointer
- display: flex
- alignItems: center
- gap: 4px

### Icon Buttons (arrange, minimap, grid)
- width: 28px
- height: 28px
- borderRadius: 8px
- backgroundColor: transparent
- border: 0px solid #525252
- cursor: pointer
- display: flex
- alignItems: center
- justifyContent: center

### Zoom Button
- fontSize: 16px
- fontWeight: 400
- color: #f7f7f7
- backgroundColor: transparent
- borderRadius: 8px
- width: 28px
- height: 28px
- cursor: pointer

## States & Behaviors

### Hover State
- **Trigger:** Mouse hover on button
- **backgroundColor:** changes to #353639
- **transition:** background-color 0.15s ease

### Active State (toggle buttons)
- **Grid Snap / Minimap:** May show active indicator
- **backgroundColor:** different shade when active

## Text Content (verbatim)
- 资产管理
- 整理画布，Option+Shift+F (tooltip)
- 切换小地图 (tooltip)
- 网格吸附 (tooltip)
- 54% (zoom level)

## Keyboard Shortcuts
- **Option+Shift+F:** 整理画布 (Arrange Canvas)

## Assets
- Icons: 4 inline SVGs (arrange, minimap, grid, zoom)
- Icon viewBoxes: 16×16, 17×17 (varies)

## Responsive Behavior
- **Desktop (1440px):** Full toolbar visible at bottom
- **Tablet (768px):** Toolbar adapts, some items may hide
- **Mobile (390px):** Toolbar becomes more compact
