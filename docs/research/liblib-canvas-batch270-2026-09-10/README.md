# Batch 270 — 预设容器标题行探测：无折叠控件，标题可编辑（源站 2026-09-10）

> 状态：`SAMPLING_RECORDED`（clone 已对齐项确认；无代码变更）。

## 源站事实（`SOURCE_FACT`，container.png + 标题行 DOM dump）

- 「预设 - 图片高清」容器标题行**无折叠/展开控件**（无 chevron/按钮）
  ——展开/折叠交互不存在；
- 标题为**可编辑文本**（外层 cursor-pointer + 内层 cursor-text，
  13px fg-muted）；
- 子图片节点头部：图标 + 「图片节点 1」+ 尺寸徽章；**AI生成 徽章**
  在媒体左上（与 clone batch 268 实现一致）；
- 容器宽大（向视口右侧延伸出屏）。

## Clone 对齐状态

- 组标题渲染：clone storyboard-group 已显示 title（batch 268 验证器
  以标题文本重选成功）✓；
- AI生成 徽章：batch 268 已实现 ✓；
- 折叠控件：源站不存在，clone 亦无——天然对齐，无需实施。

## 验收

- docs check 通过；源站画布 **0 残留**；无代码变更。
