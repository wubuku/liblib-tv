# TopNavBar Specification

## Overview
- **Target file:** `src/components/TopNavBar.tsx`
- **Screenshot:** `docs/design-references/canvas-desktop-full.png`
- **Interaction model:** Static (no scroll behavior)

## DOM Structure
```
<nav>
  <div> <!-- left section -->
    <div> <!-- logo area -->
      <img /> <!-- logo image 1 -->
      <img /> <!-- logo image 2 (toggle?) -->
    </div>
    <input /> <!-- project name: "未命名项目" -->
    <button> <!-- canvas tab selector -->
      <span>画布 2</span>
      <svg /> <!-- dropdown chevron -->
    </button>
  </div>
  <div> <!-- right section -->
    <img /> <!-- notification icon -->
    <div> <!-- VIP section -->
      <button> <!-- VIP button -->
        <svg />
        <span>会员超市</span>
      </button>
      <div> <!-- VIP promo badge -->
        <span>限时 37 折</span>
        <div>
          <svg />
          <div>
            <span>会员特惠</span>
            <span>37折</span>
          </div>
        </div>
      </div>
    </div>
    <button> <!-- credits button -->
      <svg />
      <span>64</span>
    </button>
    <img /> <!-- user avatar -->
  </div>
</nav>
```

## Computed Styles (exact values from getComputedStyle)

### Container (nav)
- height: 48px
- padding: 0px 16px
- backgroundColor: transparent
- border: 0px solid #525252
- display: flex
- justifyContent: space-between
- alignItems: center

### Project Name Input
- fontSize: 16px
- fontWeight: 400
- color: #f7f7f7
- backgroundColor: transparent
- border: none

### Canvas Tab Button
- fontSize: 16px
- fontWeight: 400
- color: #f7f7f7
- backgroundColor: transparent
- borderRadius: 8px
- padding: 0px 8px
- height: 32px
- cursor: pointer

### VIP Button
- fontSize: 13px
- fontWeight: 400
- color: #05dff6 (cyan)
- backgroundColor: rgba(38, 38, 38, 0.8)
- borderRadius: 12px
- padding: 6px 12px
- border: 0.5px solid #363636
- height: 40px
- cursor: pointer

### Credits Button ("64")
- fontSize: 13px
- fontWeight: 400
- color: #f7f7f7
- backgroundColor: rgba(38, 38, 38, 0.8)
- borderRadius: 12px
- padding: 0px 12px
- border: 0.5px solid #363636
- height: 40px
- cursor: pointer

### User Avatar
- size: 32px × 32px (estimated)
- borderRadius: 50% (circle)
- objectFit: cover

## States & Behaviors

### Hover States
- **Canvas Tab Button:** backgroundColor changes on hover
- **VIP Button:** backgroundColor changes on hover
- **Credits Button:** backgroundColor changes on hover
- **Notification Icon:** backgroundColor changes on hover

## Text Content (verbatim)
- Project name: "未命名项目"
- Canvas tab: "画布 2"
- VIP button: "会员超市"
- VIP promo: "限时 37 折"
- VIP detail: "会员特惠" "37折"
- Credits: "64"

## Assets
- Logo images: inline SVGs
- User avatar: `public/images/avatar.png`
- Icons: inline SVGs (notification, chevron, VIP, credits)

## Responsive Behavior
- **Desktop (1440px):** Full layout with all elements visible
- **Tablet (768px):** Some elements may collapse or hide
- **Mobile (390px):** Minimal layout, most elements hidden or in menu
