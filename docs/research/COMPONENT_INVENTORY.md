# LibTV Canvas Component Inventory

## Layout Components

### 1. TopNavBar
- **File:** `src/components/TopNavBar.tsx`
- **Structure:** Horizontal flex container
- **Children:** Logo, ProjectNameInput, CanvasTabSelector, Spacer, NotificationIcon, VIPButton, CreditsDisplay, UserAvatar
- **Height:** 48px
- **Background:** transparent
- **Padding:** 0 16px

### 2. LeftSidebar
- **File:** `src/components/LeftSidebar.tsx`
- **Structure:** Vertical flex container
- **Children:** 7 icon buttons
- **Width:** ~48px
- **Button size:** 32×32px
- **Gap between buttons:** 4px (estimated)

### 3. CanvasArea
- **File:** `src/components/CanvasArea.tsx`
- **Structure:** React Flow container
- **Background:** #171717
- **Contains:** Nodes, Edges, MiniMap

### 4. BottomToolbar
- **File:** `src/components/BottomToolbar.tsx`
- **Structure:** Horizontal flex container
- **Position:** Fixed bottom
- **Children:** AssetMgmtButton, ArrangeButton, MinimapButton, GridSnapButton, ZoomControl

## Node Components

### 5. ScriptNode
- **File:** `src/components/nodes/ScriptNode.tsx`
- **Header:** Icon + title "剧本"
- **Body:** Multi-line paragraph text
- **Footer:** "打开脚本节点 →" button
- **Border:** 1px solid #363636 (estimated)
- **Border-radius:** 8px
- **Background:** #1f1f1f (dark-8)

### 6. ImageNode
- **File:** `src/components/nodes/ImageNode.tsx`
- **Header:** Icon + filename + dimensions
- **Body:** Image preview with watermark overlay
- **Controls:** Close/settings buttons
- **Border:** 1px solid #363636
- **Border-radius:** 8px

### 7. StoryboardGroupNode
- **File:** `src/components/nodes/StoryboardGroupNode.tsx`
- **Structure:** Labeled group containing image thumbnails
- **Label:** "分镜图 · 第一集：咖啡馆对峙-图片组"

### 8. ScriptExecutionNode
- **File:** `src/components/nodes/ScriptExecutionNode.tsx`
- **Header:** Icon + title "第一集：咖啡馆对峙"
- **Body:** Step indicators (确认镜头, 准备资产, 合成提示词)
- **Footer:** "打开脚本节点 →" button
- **Has:** Progress/status indicators

## UI Components

### 9. IconButton
- **File:** `src/components/ui/IconButton.tsx`
- **Size:** 32×32px (sidebar) or 28×28px (toolbar)
- **Border-radius:** 8px
- **Background:** transparent
- **Hover:** background change
- **Cursor:** pointer

### 10. VIPButton
- **File:** `src/components/VIPButton.tsx`
- **Height:** 40px
- **Border-radius:** 12px
- **Background:** rgba(38, 38, 38, 0.8)
- **Border:** 0.5px solid #363636
- **Text color:** #05dff6 (cyan)
- **Contains:** Icon + "会员超市" text + badge "限时 37 折"

### 11. CreditsDisplay
- **File:** `src/components/CreditsDisplay.tsx`
- **Height:** 40px
- **Border-radius:** 12px
- **Background:** rgba(38, 38, 38, 0.8)
- **Border:** 0.5px solid #363636
- **Text:** "64"
- **Text color:** #f7f7f7

### 12. UserAvatar
- **File:** `src/components/UserAvatar.tsx`
- **Size:** 32×32px (or similar)
- **Border-radius:** full (circle)
- **Source:** CDN avatar image

### 13. ZoomControl
- **File:** `src/components/ZoomControl.tsx`
- **Text:** "54%"
- **Size:** 28×28px
- **Border-radius:** 8px

### 14. Edge
- **File:** `src/components/Edge.tsx`
- **Type:** SVG path (bezier curve)
- **Color:** Default edge color
- **Interaction:** Clickable (ref attribute present)

### 15. Watermark
- **Overlay on images**
- **Position:** absolute, z-index: 10
- **Source:** `https://libtv-res.liblib.art/watermark.png`
- **Size:** 210×102px
- **Class:** `pointer-events-none absolute z-10 h-auto select-no`

## Floating Components

### 16. FollowingStatus
- **File:** `src/components/FollowingStatus.tsx`
- **Position:** Bottom-right
- **Contains:** "正在跟随" text + "取消ESC" button
- **Tooltip:** "按 ESC 退出"
