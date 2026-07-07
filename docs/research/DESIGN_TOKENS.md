# Design Tokens

> Colors, typography, spacing — the design system in this project.
>
> All tokens are defined in `src/app/globals.css`. Each section below maps to either a CSS custom property or hardcoded values extracted via Playwright DOM queries.

## Theme

- **Mode:** Dark only (no light theme)
- **Tech stack:** Tailwind v4 (`@theme inline`), pure CSS custom properties, no `mantine`/`shadcn` runtime
- **Body bg:** `#141414`
- **Body text:** `#f7f7f7`
- **Canvas bg:** `#171717` (slightly lighter than body)

## Colors

### Brand

| Token | Hex | Use |
|-------|-----|-----|
| Brand 400 | `#09caf5` | Primary cyan (logo, focus rings, "use" buttons, hover glow) |
| Brand 300 | `#5ddcff` | Lighter cyan (active states, secondary highlights) |
| Brand 600 | `#05a3c5` | Darker cyan (text accents) |

### Backgrounds

| Token | Hex | Use |
|-------|-----|-----|
| Page bg | `#141414` | Body, TopNav |
| Surface | `#171717` | Canvas area, inputs |
| Surface elevated | `#1f1f1f` | Card surfaces (ScriptNode, TextNode, etc.) |
| Surface secondary | `#2a2d3d` | ScriptExecutionNode (slightly lighter, hierarchy) |
| Surface tertiary | `#363636` | Buttons, muted surfaces |
| Surface transparent | `rgba(38,38,38,0.8)` | VIP/FrameOS buttons on TopNav |
| Overlay | `rgba(0,0,0,0.7)` | Modal backdrops |

### Text

| Token | Hex | Use |
|-------|-----|-----|
| Default | `#f7f7f7` | Primary body text |
| Muted | `#919191` | Captions, secondary info |
| Light | `#ccc` | Hover state text |
| Lighter | `#999` | Tertiary text |
| Caption | `#fff` | High-priority text |
| On brand | `#171717` | Text on cyan buttons |

### Borders

| Token | Hex | Use |
|-------|-----|-----|
| Default | `#525252` | Card borders |
| Muted | `#363636` | Subtle borders, dividers |
| Emphasis | `#86909c` | Hover borders |
| Brand | `#09caf5` | Active/selected borders |

### Handle / Edge Specific

| Token | Hex | Use |
|-------|-----|-----|
| Handle bg | `#1f1f1f` | `<Handle>` background |
| Handle border | `#86909c` | `<Handle>` border when idle |
| Handle bg hover | `#09caf5` | `<Handle>` background on hover/connect |
| Handle valid | `#64d959` | `<Handle>` when valid drop target |
| Edge default | `#86909c` | Inactive edge |
| Edge hover | `#c0c8d0` | Active edge (from `--canvas-edge-hover`) |
| Edge flow start | `rgba(180,220,255,0)` | Gradient transparency |
| Edge flow mid | `rgba(180,220,255,1)` | Gradient peak (saturated) |
| Edge glow outer | `rgba(120,200,255,0.6)` | feFlood color |
| Edge glow inner | `rgba(180,230,255,0.85)` | feFlood color |

### Accent / Status

| Token | Hex | Use |
|-------|-----|-----|
| Red 500 | `#f53f3f` | Delete buttons, danger |
| Red 400 | `#f76560` | Hover red |
| Yellow 400 | `#ff9a2d` | Warm accent (e.g. credits icon) |
| Yellow 500 | `#ff7d00` | VIP badge bg |
| Gold/cream | `#FFDBA4` | VIP button text/icon |
| Purple 600 | `#8B25E4` | "正在跟随" banner |

## Typography

### Font Family (single)

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue",
             Helvetica, Arial, "PingFang SC", "Hiragino Sans GB",
             "Microsoft YaHei", "Noto Sans CJK SC", sans-serif,
             "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
```

Loads from system fonts; no webfont fetch. Optimized for CJK + Latin.

### Sizes (commonly used)

| Class | Size | Use |
|-------|------|-----|
| `text-xs` | 12px | Captions, badges |
| `text-sm` | 14px | Default UI text |
| `text-base` | 16px | Body |
| `text-lg` | 18px | Dialog titles |
| `text-[10px]` | 10px | Tiny labels, badges |

### Weights

- `font-normal` (400) — default
- `font-medium` (500) — UI buttons
- `font-semibold` (600) — node titles

## Spacing

Tailwind defaults (4px base) — primary usage on this site:
- `gap-1` (4px) — small icon gaps
- `gap-2` (8px) — button gaps in vertical lists
- `gap-3` (12px) — node header items
- `gap-4` (16px) — section padding
- `p-1` (4px), `p-2` (8px), `p-3` (12px), `p-4` (16px), `p-6` (24px)

## Border Radius

| Token | Use |
|-------|-----|
| `rounded-md` (6px) | Inline elements |
| `rounded-lg` (8px) | Buttons, handle, small nodes |
| `rounded-xl` (12px) | VIP buttons, dialogs, large cards |
| `rounded-2xl` (16px) | Tabs/dropdowns |
| `rounded-full` | Avatar, circular icons |

## Shadows

| Use | Value |
|-----|-------|
| Card hover | `0 4px 12px rgba(0,0,0,0.3)` |
| Card selected | `0 0 0 2px rgba(9,202,245,0.3)` |
| Menu dropdown | `0 8px 32px #00000026, 0 2px 8px #0000001a` |
| Bottom toolbar | `0 4px 24px rgba(0,0,0,0.4)` |
| Handle hover glow | `0 0 8px rgba(9,202,245,0.6)` |
| Edge hover glow | `drop-shadow(0 0 4px rgba(9,202,255,0.6))` |

## Animations

| Name | Duration | Easing | Use |
|------|----------|--------|-----|
| Button hover | 150ms | ease | All buttons, hover bg |
| Edge hover | 150ms | ease | Edge stroke + width |
| Toolbar entry | 150ms | ease-in-out | Opacity + transform |
| Edge flow | 1600ms | linear | Light segments traveling along edge (3 segments @ -0.53s offsets) |
| Modal backdrop | 150ms | ease | Modal fade-in |

## Z-Index

| Layer | Value | Use |
|-------|-------|-----|
| Canvas content | 0 | React Flow edges |
| Toolbar | 10-20 | Bottom toolbar, handles |
| Sidebar | 40 | Left sidebar |
| Floating headers | 30 | Script header |
| Following banner | 40 | "正在跟随" |
| Modal | 60 | Camera/CameraMovement dialogs |

## Where these tokens live

| File | What it contains |
|------|-------------------|
| `src/app/globals.css` `:root` block | All `--*` CSS custom properties |
| `src/app/globals.css` `@theme inline` | Tailwind v4 theme mapping |
| `tailwind.config.ts` (or `globals.css` directly) | Tailwind extension tokens |
