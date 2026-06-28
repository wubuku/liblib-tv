# LibTV Canvas Design Tokens

## Overview
- **Framework:** Next.js + Mantine UI + Tailwind CSS
- **Theme:** Dark mode (default)
- **Body Background:** `#141414` (--bg-page, --color-background, --mantine-color-dark-9)
- **Body Text:** `#f7f7f7` (--color-fg-default, --color-neutral-50)
- **Body Font Size:** 16px
- **Canvas Background:** `#171717` (--bg-canvas, --bg-surface, --input-bg, --color-neutral-950)

## Typography

### Font Families
- **Primary (CJK):** `-apple-system, "system-ui", "Segoe UI", "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`
- **Mantine Default:** `-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji`
- **Headings:** Same as Mantine default
- **Monospace:** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`
- **Hero:** `"Helvetica Neue Condensed Italic", "Arial Narrow", ...`

### Font Sizes (Mantine)
- `--mantine-font-size-xs`: `calc(.75rem*1)` = 12px
- `--mantine-font-size-sm`: `calc(.875rem*1)` = 14px
- `--mantine-font-size-md`: `calc(1rem*1)` = 16px
- `--mantine-font-size-lg`: `calc(1.125rem*1)` = 18px
- `--mantine-font-size-xl`: `calc(1.25rem*1)` = 20px

### Heading Sizes
- `--mantine-h1-font-size`: `calc(2.125rem*1)` = 34px, weight: 700
- `--mantine-h2-font-size`: `calc(1.625rem*1)` = 26px, weight: 700
- `--mantine-h3-font-size`: `calc(1.375rem*1)` = 22px, weight: 700
- `--mantine-h4-font-size`: `calc(1.125rem*1)` = 18px, weight: 700
- `--mantine-h5-font-size`: `calc(1rem*1)` = 16px, weight: 700
- `--mantine-h6-font-size`: `calc(.875rem*1)` = 14px, weight: 700

### Line Heights
- `--mantine-line-height-xs`: 1.4
- `--mantine-line-height-sm`: 1.45
- `--mantine-line-height`: 1.55
- `--mantine-line-height-md`: 1.55
- `--mantine-line-height-lg`: 1.6
- `--mantine-line-height-xl`: 1.65

### Font Weights
- `--font-weight-normal`: 400
- `--font-weight-medium`: 500
- `--font-weight-semibold`: 600
- `--font-weight-bold`: 700

## Colors

### Primary Colors
- `--color-primary`: `#09caf5` (brand cyan)
- `--color-primary-foreground`: `#fff`
- `--border-brand`: `#09caf5`
- `--input-border-focus`: `#09caf5`

### Background Colors
- `--bg-page`: `#141414` (main page bg)
- `--bg-canvas`: `#171717` (canvas area)
- `--bg-surface`: `#171717`
- `--bg-surface-elevated`: `#363636`
- `--bg-surface-secondary`: `#363636`
- `--bg-overlay`: `#000000b2` (70% black)
- `--color-background-popover`: `#1c1d29`
- `--color-background-secondary`: `#1c1d29`
- `--color-background-select-dropdown`: `#1c1d29`
- `--color-modal-background`: `#2a2d3d`
- `--color-background-normal`: `#262626`
- `--color-background-hover`: `#353639`

### Text Colors
- `--color-fg-default`: `#f7f7f7` (primary text)
- `--color-fg-muted`: `#919191` (muted text)
- `--color-text`: `#fff`
- `--color-text-light`: `#ccc`
- `--color-text-lighter`: `#999`
- `--color-caption`: `#fff`
- `--color-caption-light`: `#999`

### Border Colors
- `--border-default`: `#525252`
- `--border-muted`: `#363636`
- `--border-strong`: `#fff`
- `--border-emphasis`: `#86909c`
- `--border-hair-color`: `#525252`
- `--input-border`: `#525252`
- `--input-border-hover`: `#86909c`
- `--color-border1`: `#3e3b4b`

### Neutral Scale
- `--color-neutral-0`: `#fff`
- `--color-neutral-50`: `#f7f7f7`
- `--color-neutral-100`: `#f2f3f5`
- `--color-neutral-200`: `#e5e6ec`
- `--color-neutral-300`: `#e3e3e3`
- `--color-neutral-400`: `#c4c4c4`
- `--color-neutral-500`: `#919191`
- `--color-neutral-600`: `#86909c`
- `--color-neutral-700`: `#525252`
- `--color-neutral-800`: `#363636`
- `--color-neutral-900`: `#171717`
- `--color-neutral-950`: `#141414`

### Mantine Dark Scale
- `--mantine-color-dark-0`: `#c9c9c9`
- `--mantine-color-dark-1`: `#b8b8b8`
- `--mantine-color-dark-2`: `#828282`
- `--mantine-color-dark-3`: `#696969`
- `--mantine-color-dark-4`: `#424242`
- `--mantine-color-dark-5`: `#3b3b3b`
- `--mantine-color-dark-6`: `#2e2e2e`
- `--mantine-color-dark-7`: `#242424`
- `--mantine-color-dark-8`: `#1f1f1f`
- `--mantine-color-dark-9`: `#141414`

### Accent Colors
- `--color-danger`: `#ff6a6f`
- `--color-red-400`: `#f76560`
- `--color-red-500`: `#f53f3f`
- `--color-red-700`: `#cb272d`
- `--color-blue-400`: `#3d9bff`
- `--color-blue-500`: `#147dff`
- `--color-blue-600`: `#206ccf`
- `--color-green-400`: `#85ff75`
- `--color-green-500`: `#64d959`
- `--color-green-600`: `#4ec740`
- `--color-yellow-400`: `#ff9a2d`
- `--color-yellow-500`: `#ff7d00`
- `--color-amber-400`: lab(80.16% 16.60 99.21)
- `--color-amber-500`: lab(72.72% 31.87 97.94)
- `--color-brand-300`: `#5ddcff`
- `--color-brand-400`: `#09caf5`
- `--color-brand-500`: `#3d9bff`
- `--color-brand-600`: `#05a3c5`

### Canvas-Specific Accent
- `--canvas-accent`: `#05dff6` (cyan highlight for VIP/credits)
- `--canvas-gold`: `#FFDBA4` (lightning/credit icon color)

### Mantine Primary (Blue)
- `--mantine-primary-color-0`: `#e7f5ff`
- `--mantine-primary-color-1`: `#d0ebff`
- `--mantine-primary-color-2`: `#a5d8ff`
- `--mantine-primary-color-3`: `#74c0fc`
- `--mantine-primary-color-4`: `#4dabf7`
- `--mantine-primary-color-5`: `#339af0`
- `--mantine-primary-color-6`: `#228be6`
- `--mantine-primary-color-7`: `#1c7ed6`
- `--mantine-primary-color-8`: `#1971c2`
- `--mantine-primary-color-9`: `#1864ab`

## Spacing (Mantine)
- `--mantine-spacing-xs`: `calc(.625rem*1)` = 10px
- `--mantine-spacing-sm`: `calc(.75rem*1)` = 12px
- `--mantine-spacing-md`: `calc(1rem*1)` = 16px
- `--mantine-spacing-lg`: `calc(1.25rem*1)` = 20px
- `--mantine-spacing-xl`: `calc(2rem*1)` = 32px

## Border Radius
- `--mantine-radius-xs`: `calc(.125rem*1)` = 2px
- `--mantine-radius-sm`: `calc(.25rem*1)` = 4px
- `--mantine-radius-default`: `calc(.25rem*1)` = 4px
- `--mantine-radius-md`: `calc(.5rem*1)` = 8px
- `--mantine-radius-lg`: `calc(1rem*1)` = 16px
- `--mantine-radius-xl`: `calc(2rem*1)` = 32px
- `--radius-sm`: 4px
- `--radius-md`: 6px
- `--radius-lg`: 8px
- `--radius-xl`: 12px
- `--radius-2xl`: 16px
- `--radius-3xl`: 1.5rem = 24px
- `--radius-full`: 9999px

## Shadows
- `--mantine-shadow-xs`: `0 1px 1px #0000000d, 0 1px 2px #0000001a`
- `--mantine-shadow-sm`: `0 1px 1px #0000000d, 0 2px 5px -1px #0000000d, 0 2px 4px -1px #0000000a`
- `--mantine-shadow-md`: `0 1px 1px #0000000d, 0 5px 7px -1px #0000000d, 0 3px 3px -1px #0000000a`
- `--mantine-shadow-lg`: `0 1px 1px #0000000d, 0 8px 7px -2px #0000000d, 0 4px 4px -2px #0000000a`
- `--mantine-shadow-xl`: `0 1px 1px #0000000d, 0 10px 8px -2px #0000000d, 0 6px 6px -2px #0000000a`
- `--canvas-shadow-menu`: `0 8px 32px #00000026, 0 2px 8px #0000001a`
- `--canvas-shadow-dropdown`: `0px 4px 10px #00000040, 0px 2px 4px #0000004d`
- `--canvas-shadow-panel`: `0px 2px 5px #00000026`
- `--panel-transparent-shadow`: `0px 4px 10px 0px #0000001a`
- `--drop-shadow-sm`: `0 1px 2px #00000026`

## Breakpoints (Mantine)
- `--mantine-breakpoint-xs`: 36em = 576px
- `--mantine-breakpoint-sm`: 48em = 768px
- `--mantine-breakpoint-md`: 62em = 992px
- `--mantine-breakpoint-lg`: 75em = 1200px
- `--mantine-breakpoint-xl`: 88em = 1408px
- `--mantine-breakpoint-b640`: 640px
- `--mantine-breakpoint-b768`: 768px
- `--mantine-breakpoint-b1024`: 1024px
- `--mantine-breakpoint-b1280`: 1280px
- `--mantine-breakpoint-b1440`: 1440px
- `--mantine-breakpoint-b1520`: 1520px
- `--mantine-breakpoint-b1600`: 1600px
- `--mantine-breakpoint-b1920`: 1920px
- `--mantine-breakpoint-b2240`: 2240px

## Z-Index Layers
| Layer | z-index | Element |
|-------|---------|---------|
| Watermark | 10 | Watermark overlay on images |
| App | 100 | `--mantine-z-index-app` |
| Popover | 300 | `--mantine-z-index-popover` |
| Modal | 500 | `--mantine-z-index-modal` |
| Overlay | 600 | `--mantine-z-index-overlay` |
| Max | 9999 | `--mantine-z-index-max` |

## Transitions
- **Default button transition:** `0.15s cubic-bezier(0.4, 0, 0.2, 1)`
- **Duration classes:** `duration-200`, `duration-300`
- **Transform transitions:** `transition-transform`

## Canvas-Specific
- `--bg-topbar-btn`: `#2c2c2d`
- `--bg-topbar-btn-hover`: `#1b1b20`
- `--bg-topbar-hover`: `#303030`
- `--bg-topbar-msg-hover`: `#2a2d3d`
- `--input-bg`: `#171717`
- `--input-placeholder`: `#86909c`
- `--canvas-controls-icon`: icon color for control buttons
- `--canvas-primary-btn-icon`: icon color for primary action button

## Component Dimensions
- **Nav height:** 48px
- **Nav padding:** 0px 16px
- **Sidebar container:** width 298px, padding 8px, border-radius 12px, bg #262626
- **Sidebar button:** 32px × 32px, border-radius: 8px
- **Toolbar button:** 28px × 28px, border-radius: 8px
- **Primary button:** height 40px, border-radius: 12px
- **Bottom toolbar:** bg rgba(20,20,20,0.7), padding 6px, border-radius 12px

## Tech Stack Detected
- **UI Framework:** Mantine (CSS variables with `--mantine-*` prefix)
- **CSS:** Tailwind CSS (utility classes observed)
- **Icons:** Iconify (`iconify--libtv` custom icon set)
- **Node Editor:** React Flow / XY Flow (canvas with nodes and edges)
- **Chat Support:** 网易七鱼 (qiyukf.net customer service)
- **Analytics:** Bing tracking pixel
