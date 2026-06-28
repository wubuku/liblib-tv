# ScriptNode Specification

## Overview
- **Target file:** `src/components/nodes/ScriptNode.tsx`
- **Screenshot:** `docs/design-references/canvas-desktop-full.png`
- **Interaction model:** Draggable (React Flow node)

## DOM Structure
```
<div> <!-- node container -->
  <div> <!-- header -->
    <div> <!-- icon container -->
      <svg /> <!-- script icon -->
    </div>
    <div>剧本</div> <!-- title -->
  </div>
  <div> <!-- content area -->
    <p> <!-- script text -->
      第一集：咖啡馆对峙
      角色：陈默(男主,面容冷峻)、林小婉(女主,眼神忧郁)
      场景1：咖啡馆
      陈默坐在窗边，咖啡已凉。林小婉走进来，走到他对面坐下。
      林小婉提高音量说："你到底还要躲我到什么时候？"
      陈默不正眼看她，声音低沉："我没有躲你。"
      林小婉眼眶红了，说："你知道我有多担心吗？"
      陈默转过头，无声地冷笑了一下，说："当初你离开的时候，怎么没想过我会担心？"
    </p>
  </div>
  <div> <!-- footer -->
    <img /> <!-- some icon -->
    <img /> <!-- some icon -->
  </div>
</div>
```

## Computed Styles (exact values from getComputedStyle)

### Container
- backgroundColor: #1f1f1f (mantine dark-8)
- borderRadius: 8px
- border: 1px solid #363636 (--mantine-color-dark-6)
- boxShadow: 0 1px 3px rgba(0,0,0,0.3)
- minWidth: 280px
- maxWidth: 400px

### Header
- display: flex
- alignItems: center
- gap: 8px
- padding: 12px 16px
- borderBottom: 1px solid #363636

### Header Icon
- width: 16px
- height: 16px
- color: #f7f7f7

### Header Title
- fontSize: 14px
- fontWeight: 600
- color: #f7f7f7

### Content Area
- padding: 16px
- maxHeight: 300px
- overflowY: auto

### Script Text (p)
- fontSize: 14px
- fontWeight: 400
- color: #f7f7f7
- lineHeight: 1.6
- whiteSpace: pre-wrap

### Footer
- display: flex
- justifyContent: flex-end
- gap: 8px
- padding: 8px 16px
- borderTop: 1px solid #363636

## States & Behaviors

### Selection State
- **Trigger:** Click on node
- **border:** changes to accent color (#09caf5)
- **boxShadow:** may increase

### Hover State
- **Trigger:** Mouse hover on node
- **boxShadow:** increases slightly

### Drag State
- **Trigger:** Click and drag
- **cursor:** grabbing
- **opacity:** may reduce slightly

## Text Content (verbatim)
- Title: "剧本"
- Content:
  ```
  第一集：咖啡馆对峙
  角色：陈默(男主,面容冷峻)、林小婉(女主,眼神忧郁)
  场景1：咖啡馆
  陈默坐在窗边，咖啡已凉。林小婉走进来，走到他对面坐下。
  林小婉提高音量说："你到底还要躲我到什么时候？"
  陈默不正眼看她，声音低沉："我没有躲你。"
  林小婉眼眶红了，说："你知道我有多担心吗？"
  陈默转过头，无声地冷笑了一下，说："当初你离开的时候，怎么没想过我会担心？"
  ```

## Assets
- Header icon: inline SVG (script/document icon)
- Footer icons: 2 inline SVGs

## Responsive Behavior
- **Desktop (1440px):** Full node with all content
- **Canvas zoom:** Node scales with canvas zoom level
