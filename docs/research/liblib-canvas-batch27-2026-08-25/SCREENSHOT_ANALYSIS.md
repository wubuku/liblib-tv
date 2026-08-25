# Batch 27 Screenshot Analysis

## 1. Source Visual Reuse

本批规划阶段没有重复识别原站整图。

复用事实：

- [`../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch24-2026-08-25/SCREENSHOT_ANALYSIS.md) 已记录 ready video 顶部工具条存在 `智能去字幕`；
- Batch 9 已记录 video top/bottom overlay 的 node-relative anchor；
- Batch 26 已记录当前 clone ready video、顶部工具条和 compact lower workflow 的视觉上下文。

本批新增 panel 与 region geometry 直接来自线上 bundle：

- panel `absolute -bottom-4`、`w-max`、`px-2 py-2`；
- close `32x32`、region tools `32x32`、submit `28x28`；
- region border `#0690ae`、fill `rgba(7, 184, 221, 0.15)`；
- 选中 region 的 edge/corner resize layer。

## 2. Planned Clone Ledger

专项脚本应生成：

| Planned file | Viewport / state |
|---|---|
| `liblib-clone-batch27-subtitle-smart-929-2026-08-25.png` | smart compact panel |
| `liblib-clone-batch27-subtitle-region-929-2026-08-25.png` | two regions, one selected |
| `liblib-clone-batch27-subtitle-target-929-2026-08-25.png` | pending target + edge |
| `liblib-clone-batch27-subtitle-mobile-390-2026-08-25.png` | natural clipping |
| `liblib-clone-batch27-subtitle-contact-sheet-2026-08-25.png` | four-state ledger |

文件尚未生成，因此此处使用 code spans 而不是 Markdown image links。

## 3. Re-inspection Rule

实现后只识别一次新 contact sheet，并立即把几何、层级、文字遮挡和响应式结论写回本文件。后续除非截图或实现变化，不重复识别整图；只检查缺失的最小 crop/state。
