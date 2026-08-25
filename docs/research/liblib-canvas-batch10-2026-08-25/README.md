# LibTV 画布 Batch 10：图片编辑器五节点状态矩阵

> 建档日期：2026-08-25
> 状态：已完成规划，等待实施与验证
> 目标：用同一登录态原站审计中的五个图片节点逐一校准 clone，消除按粗粒度 `editorVariant` 猜测面板高度、入口和内容的偏差。

## 为什么做这一批

Batch 9 已证明图片上下浮层的锚点、反缩放和裁切行为正确，但面板内部仍有明显脑补：

- `咖啡馆` 只有 7 字 Prompt，原站面板仍为 `191px`，clone 却因 `prompt` variant 显示 `211px`；
- 无参考图的 `咖啡`、`咖啡馆` 错误显示“参考”入口；
- `咖啡` Prompt 被截短到 197 字，而原站为 602 字；
- placeholder、顶部 chip 高度、footer 控件高度和部分图标不一致；
- AutoLink 被放成顶部可见文字 pill，原站五个采样状态的顶部直接控件中没有该 pill。

这些差异都位于图片生成主工作流，属于高频、可见且已有强证据支持的高价值修正。

## 文档导航

- [`PLAN.md`](PLAN.md)：缺口、优先级、范围和验收标准
- [`IMAGE_EDITOR_STATE_MATRIX.spec.md`](IMAGE_EDITOR_STATE_MATRIX.spec.md)：五节点原站事实、证据边界和 clone 合同
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、测试、截图和提交记录

## 证据入口

- `docs/research/liblib-live-2026-08-25/image-node-state-audit.json`
- `docs/research/liblib-canvas-batch9-2026-08-25/SCREENSHOT_ANALYSIS.md`
- `docs/research/components/ImageEditPanel.spec.md`
- `docs/design-references/liblib-original-image-selected-2026-08-25.png`

## 截图复用

本批原站视觉结构已在 Batch 9 的识图记录中落档，面板逐节点数据来自结构化 DOM JSON。只有专项验证产生新的 clone 截图；不重复识别原站整图。

## 证据边界

- **原站直接事实**：节点 ID、Prompt、placeholder、参考图数量、顶部入口文字、面板矩形、控件矩形、generation settings。
- **证据反推**：面板高度必须由具体节点状态显式表达，而不能仅由“是否有 Prompt”推断。
- **clone 决策**：保留本地 AutoLink 交互闭环，但把入口收敛为 footer 图标按钮；具体图标采用 Lucide 近似，不声称是原站 SVG 的逐路径复制。

