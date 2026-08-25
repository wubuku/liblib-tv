# FrameOS Research Index

> `frameos.cn` 原站观察、结构化抽取、组件规格、行为记录和当前 clone 运行手册。

## Guides

- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：设计决策、store 状态机、路由边界和已知 prototype 边界。
- [`RUNBOOK.md`](RUNBOOK.md)：启动、浏览器诊断、DEBUG 模式和扩展步骤。
- [`PAGE_TOPOLOGY.md`](PAGE_TOPOLOGY.md)：画布布局与 overlay 层级。
- [`BEHAVIORS.md`](BEHAVIORS.md)：交互行为。
- [`COMPONENT_INVENTORY.md`](COMPONENT_INVENTORY.md)：FrameOS 组件清单。
- [`DESIGN_TOKENS.md`](DESIGN_TOKENS.md)：颜色、尺寸和视觉 token。

## Raw Evidence

- `*.json`：原站 DOM、计算样式、节点、按钮、SVG 和资产抽取。
- `original-*.png`：原站状态截图。
- [`../../design-references/frameos/`](../../design-references/frameos/)：clone 的局部诊断和回归截图。

FrameOS 的 runtime 实现位于 `src/app/frameos/`、`src/components/frameos/` 和 `src/store/frameosStore.ts`。它与 LibTV route 的 store 和节点系统保持隔离。
