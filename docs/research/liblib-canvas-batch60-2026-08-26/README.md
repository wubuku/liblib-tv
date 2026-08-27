# Batch 60：图片双浮层选择切换与 owner 一致性

> 状态：`SCRIPT_RECORDED_PASS`。普通 LibTV 画布 clone-owned interaction
> slice。
> 本批处理图片节点上下双浮层在相邻节点选择切换时的 owner 一致性和
> pointer hit-testing，不改已经通过的 zoom-aware 几何合同。

## 为什么做

已有 Batch 51/52 已经验证单个图片节点的 toolbar、panel 几何和 screen-size
preservation，但没有验证“下方面板覆盖相邻节点时，用户仍能可靠切换到
另一个图片节点”。这类失败会留下旧浮层，直接表现为浮层位置错误。

## 证据边界

- `10 + 24 * zoom`、`16 * zoom`、node-center 和自然裁切来自既有 source
  contract；
- “被 panel 覆盖的相邻节点如何响应 pointer”是本批 clone-owned interaction
  decision，不冒充当前 LibTV 源站事实；
- 本批不重复识别已有截图；若需新视觉证据，先更新
  `SCREENSHOT_ANALYSIS.md`。

## 接力入口

- [`PLAN.md`](PLAN.md)：范围、价值、决策和验收；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码、验证和 checkpoint；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图识别台账；
- [`runtime-audit.json`](runtime-audit.json)：focused verifier 结果。

## 已完成

- standard `ImageToolbar` 与 `ImageEditPanel` 输出同一
  `data-owner-node-id`；
- selection 切换时旧双浮层卸载、新双浮层迁移；
- panel 非交互区域不 blanket 捕获 pointer，textarea、按钮和弹出控件保持
  可交互；
- 保留既有 source-shaped 几何、自然裁切、active-tool replacement 和
  graph/history 不变合同；
- desktop/mobile focused Playwright、诊断、无溢出和相邻回归已记录；
- 本批没有新增截图，复用 Batch 51/52 已登记的几何证据。

正式实施结果和最终 checkpoint 见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)。
