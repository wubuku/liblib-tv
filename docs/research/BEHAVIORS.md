# LibTV Canvas Interaction Behaviors

## Page-Level

### Canvas Interaction Model
- **Type:** Pan + Zoom + Drag (React Flow)
- **Pan:** Click and drag on empty canvas area
- **Zoom:** Scroll wheel or pinch gesture
- **Current zoom:** 54%
- **Grid snap:** Toggle-able via bottom toolbar

### Keyboard Shortcuts
- **Option+Shift+F:** 整理画布 (Arrange canvas)
- **ESC:** Cancel "正在跟随" (Following) mode

## Navigation Bar

### Project Name Input
- **Type:** Inline editable textbox
- **Default value:** "未命名项目"
- **Interaction:** Click to edit

### Canvas Tab Selector
- **Type:** Dropdown button
- **Current value:** "画布 2"
- **Interaction:** Click to show dropdown with canvas options
- **Has:** Chevron icon (dropdown indicator)

### VIP Button
- **Hover:** Background changes
- **Click:** Opens VIP store/modal
- **Badge:** "限时 37 折" (Limited time 37% off) - animated/pulsing

### Credits Button ("64")
- **Hover:** Background changes
- **Click:** Opens credits/purchase panel

## Left Sidebar Buttons

### General Button Behavior
- **Default:** Transparent background, 32×32px
- **Hover:** Background color change (--color-background-hover: #353639)
- **Active/Selected:** Different background
- **Cursor:** pointer
- **Transition:** Background color transition

### Button Functions
1. **添加节点** — Opens node type selector/menu
2. **打开工具箱** — Opens toolbox panel
3. **素材库** — Opens material library panel
4. **角色库** — Opens character library panel
5. **历史记录** — Opens history panel
6. **快捷键** — Shows keyboard shortcuts overlay
7. **教程** — Opens tutorial/guide

## Canvas Nodes

### Node General Behavior
- **Draggable:** Yes (React Flow)
- **Selectable:** Yes (click to select)
- **Connectable:** Yes (edges between nodes)
- **Border:** 1px solid border
- **Border-radius:** 8px
- **Shadow:** Subtle shadow on hover/select

### Image Node
- **Watermark overlay:** Always visible on images
- **Image preview:** `object-fit: cover`
- **Dimensions display:** Shows pixel dimensions (e.g., "1808 × 1024")

### Script Node
- **Text content:** Multi-line, scrollable if long
- **Action button:** "打开脚本节点 →" at bottom

### Edges (Connections)
- **Type:** SVG bezier curves
- **Interaction:** Clickable (can select/edit)
- **Labels:** Optional edge labels

## Bottom Toolbar

### Asset Management
- **Hover:** Background changes
- **Click:** Opens asset management panel

### Arrange Canvas (Option+Shift+F)
- **Click:** Auto-arranges all nodes on canvas

### Minimap Toggle
- **Click:** Shows/hides minimap overlay

### Grid Snap Toggle
- **Click:** Enables/disables grid snapping

### Zoom Control
- **Displays:** Current zoom percentage
- **Click:** Opens zoom options (fit, percentage presets)

## Floating Elements

### Following Status
- **Position:** Bottom-right corner
- **Animation:** Possibly pulsing or glowing
- **Cancel button:** Click or press ESC to exit
- **Tooltip:** "按 ESC 退出"
