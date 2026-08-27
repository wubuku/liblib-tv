# Batch 60 截图分析

> 状态：`NO_NEW_SCREENSHOT_REQUIRED`（2026-08-26）。

本批没有新增截图。Batch 51/52 的截图、DOM rect 和多 zoom 结构化台账已经
覆盖标准图片双浮层的视觉几何；本批新增的是 pointer hit-testing boundary
和 owner identity，使用 DOM/CSS/runtime assertions 记录，避免重复识别旧图。

## 已复用证据

- [`../liblib-canvas-batch51-2026-08-26/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch51-2026-08-26/SCREENSHOT_ANALYSIS.md)
  ：zoom-aware toolbar top gap、panel bottom gap、center 和 natural clipping；
- [`../liblib-canvas-batch52-2026-08-26/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch52-2026-08-26/SCREENSHOT_ANALYSIS.md)
  ：当前 13-action toolbar、标准 panel 和 active Preview replacement。

## 本批新增观察

- `data-owner-node-id` 使上/下两个标准 surface 可以直接与 selected node
  做 runtime 对照；
- panel wrapper/section 的 pointer-events 为 `none`，textarea、button 和
  已有交互控件显式恢复为 `auto`；
- 这只是 clone-owned 命中边界，不证明认证后 LibTV 源站在重叠区域的真实
  pointer routing；
- 由于面板本身是可编辑 surface，不能声称任意被 panel 覆盖的节点像素都能
  穿透点击。该冲突保留在本批边界中。
