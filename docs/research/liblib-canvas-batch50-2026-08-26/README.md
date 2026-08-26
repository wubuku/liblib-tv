# Batch 50：导演台工作区折叠与键盘边界

> 状态：已完成（2026-08-26）。本批是 clone-owned 的 Director workspace
> shell 有界合同，不是当前 LibTV authenticated source 的精确 DOM/CSS 证明。
> 本批继续以导演台为最高优先级，处理高频工作区壳层交互：
> 侧栏折叠、视口扩展和 Director workspace 的键盘 ownership。

## 目标

```text
视口工具条“全屏”
  -> 折叠/恢复左对象树与右 Inspector
  -> 中央 R3F 视口扩展
  -> gizmo、画幅框、底部工具条随视口重新布局

Director workspace keyboard boundary
  -> workspace 建立可发现的 dialog/focus owner
  -> page-level canvas shortcuts 不穿透
  -> Escape 按内部 surface 优先级逐层关闭
```

## 证据边界

- fixed upstream `storyai-3d-director-desk` commit
  `8c8bd361790be4d37158a7430365e65546e358fe` 提供可借鉴的
  `viewportPanelsCollapsed`、`全屏` action、shell sidebars hidden 和
  editable-target shortcut guard；
- 现有 LibTV authenticated source 没有在本批重新取得 Director shell 的
  精确 DOM/CSS 合同，因此 upstream 结构是 `UPSTREAM_FACT`，不是
  `LIBTV_SOURCE_FACT`；
- clone 的折叠状态采用 session-local Director UI 状态，不写入普通画布
  graph，不改变 active camera、objects、timeline 或 capture payload。

## 文档入口

- [`PLAN.md`](PLAN.md)：范围、状态矩阵、验收门和停止条件；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：source/clone/unknown 分层；
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)：固定上游代码考古；
- [`DIRECTOR_WORKSPACE_SHELL.spec.md`](DIRECTOR_WORKSPACE_SHELL.spec.md)：
  本批 clone 行为契约；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：四态截图和一次性视觉识别台账；
- [`MATURITY_ASSESSMENT.md`](MATURITY_ASSESSMENT.md)：成熟度、残余风险和后续边界；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证和接力记录。

## 明确不包含

- 不调用 `document.documentElement.requestFullscreen()`；
- 不把面板折叠写成 React Flow graph/history transaction；
- 不在本批重写 Director 所有浮层的 focus trap；
- 不把上游 panel 宽度、颜色和 CSS 直接宣称为 LibTV source exact；
- 不修改普通 LibTV 画布或 FrameOS route/store。
