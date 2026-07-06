# FrameOS 画布 — 设计令牌

> 取自 https://www.frameos.cn/#/canvas/01KT17B610DG417X8Q76QZSN8Z/01KWS3TK5BTEH7680N4W9JW4KW 的精确计算样式

## 颜色

### 基础（深色主题）

| Token | 值 | 用途 |
|---|---|---|
| `--canvas-bg` | `#0D0D0D` (rgb 13,13,13) | 画布底色 |
| `--app-bg` | `#0A0A0A` | AppHeader/Modal 底 |
| `--surface-1` | `#1C1C1C` (rgb 28,28,28) | 节点卡片 |
| `--surface-2` | `#1A1A1A` | 工具栏/Dock/面包屑 |
| `--surface-3` | `#171717` | 二级 surface |
| `--border-1` | `rgba(255,255,255,0.12)` | 浅边框 |
| `--border-2` | `rgba(255,255,255,0.08)` | 更浅边框 |
| `--border-3` | `#2A2A2A` | 暗边框 |

### 文字

| Token | 值 | 用途 |
|---|---|---|
| `--text-primary` | `#FFFFFF` | 主文字 |
| `--text-secondary` | `#C2C2C2` (rgb 194,194,194) | 次文字（段落、dock-btn 文字） |
| `--text-tertiary` | `#A3A3A3` (rgb 163,163,163) | 弱化文字（节点标题） |
| `--text-muted` | `#E0E0E0` (rgb 224,224,224) | footer cost 文字 |

### 主色

| Token | 值 | 用途 |
|---|---|---|
| `--brand-blue-600` | `#2563EB` | rail-btn--primary 渐变起点 |
| `--brand-blue-700` | `#1D4ED8` | rail-btn--primary 渐变终点 |
| `--brand-blue-500` | `#3B82F6` | box-shadow glow (rgba 59,130,246,0.35) |
| `--brand-blue-400` | `#60A5FA` | dock-btn.is-active 文字/边框 |
| `--brand-blue-glow` | `rgba(59,130,246,0.16)` | dock-btn.is-active 背景 |

### 状态色

| Token | 值 | 用途 |
|---|---|---|
| `--warning-amber-500` | `#F59E0B` (rgb 245,158,11) | "审核未通过" 徽章文字/图标 |
| `--success` | `#22C55E` | (推断，未直接出现) |
| `--danger` | `#EF4444` | (推断) |

### 图标徽章 (cr-badge)

| Token | 值 | 用途 |
|---|---|---|
| `--coin-orange` | `#FFC35E` (rgb 255,195,94) | 金币图标 |
| `--point-blue` | `#60A5FA` | 积分图标 |

## 字体

```
font-family: -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, ...
```

| 用途 | size | weight | line-height |
|---|---|---|---|
| 段落 (text-display) | 13px | 400 | 20.15px (1.55) |
| 节点 header / breadcrumb | 12-13px | 500 | 20px |
| breadcrumb 主文字 | 13px | 500 | — |
| AppHeader (默认 16px) | 16px | 400 | normal |
| H3 (账号登录等) | 14px | 700 | 19.6px |
| AppHeader 子元素 (按钮) | 13.33px | 400 | — |
| input | 14px | 400 | — |
| node title (floating) | 12px | 500 | 20px |

## 间距

| Token | 值 | 用途 |
|---|---|---|
| `--gap-2` | 2px | breadcrumb 元素间距 |
| `--gap-3` | 3px | node-floating-title gap |
| `--gap-4` | 4px | footer 间距 |
| `--gap-10` | 10px | tool-rail 元素间距 |
| `--space-2` | 2px | 通用 (node-replace inset) |
| `--space-3` | 3px | — |
| `--space-4` | 4px | 通用 |
| `--space-5` | 5px (5px 8px 5px 10px) | breadcrumb padding |
| `--space-8` | 8px | breadcrumb padding-y/圆角/控件 padding-x |
| `--space-10` | 10px | node-card radius |
| `--space-12` | 12px | node-floating-title top:-22px offset |
| `--space-18` | 18px | resize-handle, replace-btn |
| `--space-24` | 24px | AppHeader padding-x |

## 圆角

| 元素 | 值 |
|---|---|
| breadcrumb-switcher | 8px |
| 节点卡 (node-card) | 10px |
| node-content-replace | 6px |
| rail-btn | 9999px (pill) |
| dock-btn | 8px |
| cr-badge | 4px |
| minimap | (未指定) |

## 尺寸

| 元素 | 尺寸 |
|---|---|
| AppHeader | 1440 × 60 |
| 文本节点 | 300 × 200 |
| 视频节点 | 300 × 169 (16:9) |
| 图片节点 | 300 × 169 或 225 × 300 (4:3?) |
| rail-btn | 36 × 36 |
| rail-btn--primary | 36 × 36 |
| dock-btn | 32 × 32 |
| resize-handle | 18 × 18 |
| replace-btn | 18 × 18 |
| play-btn | 40 × 40 |
| cr-icon | 22 × 22 |
| prompt-bar | 514 × 68 (initial) |

## 阴影

```
rail-btn--primary: rgba(59,130,246,0.35) 0 2px 8px 0
replace-btn:       rgba(0,0,0,0.3) 0 4px 12px 0
node-card hover:   rgba(0,0,0,0.3) 0 4px 12px 0  (推断)
```

## 过渡

```
通用: transition: all
node-card:         transition: box-shadow 0.15s
node-floating-title: transition: all
replace-btn:       transition: background 0.15s, border-color 0.15s, box-shadow 0.15s
breadcrumb:        transition: background 0.15s, border-color 0.15s
dock-btn:          transition: background 0.15s, color 0.15s
rail-btn:          transition: background 0.15s, transform 0.15s, box-shadow 0.15s
resize-handle:     transition: opacity 0.15s
```

## 图标系统

- **Remix Icon** (CSS class `ri-*`, 字体名 `remixicon`)
- 主要图标:
  - `ri-arrow-go-back-line` (撤销)
  - `ri-arrow-go-forward-line` (重做)
  - `ri-add-line` (添加)
  - `ri-folder-image-line` (素材库)
  - `ri-upload-cloud-2-line` (上传)
  - `ri-question-line` (帮助)
  - `ri-map-pin-2-line` (小地图钉)
  - `ri-subtract-line` (缩小)
  - `ri-fullscreen-exit-line` (适应)
  - `ri-layout-grid-line` (网格整理)
  - `ri-arrow-down-s-line` (下拉箭头)
  - `ri-text` (文本节点)
  - `ri-image-line` (图片节点)
  - `ri-film-line` (视频节点)
  - `ri-play-fill` (播放)
  - `ri-upload-2-line` (替换)
  - `ri-error-warning-fill` (审核警告)
  - `ri-arrow-left-line` (返回菜单)
