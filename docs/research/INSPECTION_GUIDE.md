# Website Inspection Guide

## How to Reverse-Engineer Any Website

This guide outlines what to capture when inspecting a target website via Chrome MCP or browser DevTools.

## Phase 1: Visual Audit

### Screenshots to Capture
- [ ] Every distinct page — desktop, tablet, mobile
- [ ] Dark mode variants (if applicable)
- [ ] Light mode variants (if applicable)
- [ ] Key interaction states (hover, active, open menus, modals)
- [ ] Loading/skeleton states
- [ ] Empty states
- [ ] Error states

### Screenshot Recognition Ledger

截图识别成本较高。第一次识图后必须立即把结果写成可发现的文本证据，后续先读记录，不凭记忆重复识图。

识图前：

- [ ] 在 `docs/research/` 中搜索截图文件名、组件名和交互状态
- [ ] 确认现有记录是否已经回答当前问题
- [ ] 只有图片发生变化、问题不同或旧记录明确不确定时才重新识别

第一次识图后，写入当前 batch 的 `SCREENSHOT_ANALYSIS.md` 或对应组件规格，至少记录：

- [ ] 截图路径、来源、采样日期、viewport、zoom、交互状态
- [ ] 可见区域、层级、遮挡与裁切关系
- [ ] 文案、控件、图标、媒体及空白/loading/error 状态
- [ ] 几何、间距、对齐、颜色；标明是测量值还是视觉估计
- [ ] 与相邻状态对比后可确认的行为变化
- [ ] 原站截图直接事实、DOM 证据、实现反推和未确认假设的边界
- [ ] 模糊或不可读区域，以及再次截取局部图的明确理由

同一工作流有多张截图时，优先维护一个 batch 级 `SCREENSHOT_ANALYSIS.md`，再把组件结论同步到 `docs/research/components/<Name>.spec.md`。再次识图时只检查缺失的最小区域或新状态。

### Design Tokens to Extract
- [ ] **Colors** — background, text (primary/secondary/muted), accent, border, hover, error, success, warning
- [ ] **Typography** — font family, sizes (h1-h6, body, caption, label), weights, line heights, letter spacing
- [ ] **Spacing** — padding/margin patterns (look for a scale: 4px, 8px, 12px, 16px, 24px, 32px, etc.)
- [ ] **Border radius** — buttons, cards, avatars, inputs
- [ ] **Shadows/elevation** — card shadows, dropdown shadows, modal overlay
- [ ] **Breakpoints** — when does the layout shift? (inspect with DevTools responsive mode)
- [ ] **Icons** — which icon library? custom SVGs? sizes?
- [ ] **Avatars** — sizes, shapes, fallback behavior
- [ ] **Buttons** — all variants (primary, secondary, ghost, icon-only, danger)
- [ ] **Inputs** — text fields, textareas, selects, checkboxes, toggles

## Phase 2: Component Inventory

For each distinct UI component, document:
1. **Name** — what would you call this component?
2. **Structure** — what HTML elements / child components does it contain?
3. **Variants** — does it have different sizes, colors, or states?
4. **States** — default, hover, active, disabled, loading, error, empty
5. **Responsive behavior** — how does it change at different breakpoints?
6. **Interactions** — click, hover, focus, keyboard navigation
7. **Animations** — transitions, entrance/exit animations, micro-interactions

### Common Components to Look For
- Navigation (top bar, sidebar, bottom bar)
- Cards / list items
- Buttons and links
- Forms and inputs
- Modals and dialogs
- Dropdowns and menus
- Tabs and segmented controls
- Avatars and user badges
- Loading skeletons
- Toast notifications
- Tooltips and popovers

## Phase 3: Layout Architecture

- [ ] **Grid system** — CSS Grid? Flexbox? Fixed widths?
- [ ] **Column layout** — how many columns at each breakpoint?
- [ ] **Max-width** — main content area max-width
- [ ] **Sticky elements** — header, sidebar, floating buttons
- [ ] **Z-index layers** — navigation, modals, tooltips, overlays
- [ ] **Scroll behavior** — infinite scroll, pagination, virtual scrolling

## Phase 4: Technical Stack Analysis

- [ ] **Framework** — React? Vue? Angular? Check `__NEXT_DATA__`, `__NUXT__`, `ng-version`
- [ ] **CSS approach** — Tailwind (utility classes), CSS Modules, Styled Components, Emotion, vanilla CSS
- [ ] **State management** — Redux (check DevTools), React Query, Zustand, Pinia
- [ ] **API patterns** — REST, GraphQL (check network tab for `/graphql` requests)
- [ ] **Font loading** — Google Fonts, self-hosted, system fonts
- [ ] **Image strategy** — CDN, lazy loading, srcset, WebP/AVIF
- [ ] **Animation library** — Framer Motion, GSAP, CSS transitions only

## Phase 5: Documentation Output

After inspection, create these files in `docs/research/`:
1. `DESIGN_TOKENS.md` — All extracted colors, typography, spacing
2. `COMPONENT_INVENTORY.md` — Every component with structure notes
3. `LAYOUT_ARCHITECTURE.md` — Page layouts, grid system, responsive behavior
4. `INTERACTION_PATTERNS.md` — Animations, transitions, hover states
5. `TECH_STACK_ANALYSIS.md` — What the site uses and our chosen equivalents
