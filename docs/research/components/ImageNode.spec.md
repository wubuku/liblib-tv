# ImageNode Specification

## Overview
- **Target file:** `src/components/nodes/ImageNode.tsx`
- **Screenshot:** `docs/design-references/canvas-desktop-full.png`
- **Interaction model:** Draggable (React Flow node)

## DOM Structure
```
<div> <!-- node container -->
  <div> <!-- header -->
    <div> <!-- icon container -->
      <svg /> <!-- image icon -->
    </div>
    <div> <!-- filename -->
      <div>image_2026-06-15T11-22-00</div>
      <div>
        <svg /> <!-- expand icon -->
      </div>
    </div>
    <div>1808 × 1024</div> <!-- dimensions -->
  </div>
  <div> <!-- image container -->
    <div> <!-- image wrapper -->
      <div> <!-- inner container -->
        <div></div>
      </div>
      <div> <!-- image display -->
        <img /> <!-- main image -->
        <img /> <!-- watermark overlay -->
      </div>
      <img /> <!-- close/settings button -->
    </div>
  </div>
</div>
```

## Computed Styles (exact values from getComputedStyle)

### Container
- backgroundColor: #1f1f1f (mantine dark-8)
- borderRadius: 8px
- border: 1px solid #363636
- boxShadow: 0 1px 3px rgba(0,0,0,0.3)
- minWidth: 240px

### Header
- display: flex
- alignItems: center
- gap: 8px
- padding: 8px 12px
- borderBottom: 1px solid #363636

### Filename
- fontSize: 12px
- fontWeight: 400
- color: #f7f7f7
- overflow: hidden
- textOverflow: ellipsis
- whiteSpace: nowrap

### Dimensions
- fontSize: 12px
- fontWeight: 400
- color: #919191 (--color-fg-muted)

### Image Container
- position: relative
- overflow: hidden

### Main Image
- width: 100%
- height: auto
- objectFit: cover
- display: block

### Watermark Overlay
- position: absolute
- top: auto
- bottom: auto
- right: auto
- left: auto
- width: 210px
- height: 102px
- pointerEvents: none
- zIndex: 10
- userSelect: none

## States & Behaviors

### Selection State
- **border:** changes to accent color (#09caf5)

### Hover State
- **boxShadow:** increases slightly
- **Close button:** becomes visible

### Image Loading
- Shows skeleton/placeholder while loading
- Transitions to full image on load

## Assets
- Main image: `public/images/scene-coffee-1.png` (example)
- Watermark: `public/images/watermark.png`
- Icons: inline SVGs (image, expand, close)

## Responsive Behavior
- **Desktop (1440px):** Full node with image preview
- **Canvas zoom:** Node scales with canvas zoom level
