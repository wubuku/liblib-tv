# Batch 49：导演台视口原生坐标控件

> 状态：已完成（clone-owned 有界合同）。
> 本批在 Batch 48 的本地模型库收口之后，继续以导演台为最高优先级，
> 复刻一个有固定上游证据、低 graph 风险、可独立验收的 R3F 视口交互。

## 目标

在导演台 3D 视口右上角补齐原生坐标控件：

```text
视口相机
  -> 小型 R3F GizmoViewport 方向反馈
  -> 六个透明 DOM 方向命中区
  -> 点击轴向
  -> 相机切换到对应正/反方向
```

## 为什么现在做

- 固定的 `storyai-3d-director-desk` checkout 已实现独立 gizmo canvas、
  `GizmoHelper`、`GizmoViewport` 和六方向相机跳转；
- 当前 clone 已有真实 R3F 视口、Director/Camera 两种视角和可交互相机，
  但没有轴向反馈，用户只能依靠 OrbitControls 判断空间方向；
- 本批不需要真实资产、上传、远程任务或 React Flow graph mutation。

## 文档入口

- [`PLAN.md`](PLAN.md)：范围、优先级、验收和选择器；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：当前可声称的事实和不确定性；
- [`UPSTREAM_ARCHAEOLOGY.md`](UPSTREAM_ARCHAEOLOGY.md)：固定上游实现考古；
- [`DIRECTOR_VIEWPORT_GIZMO.spec.md`](DIRECTOR_VIEWPORT_GIZMO.spec.md)：clone 行为契约；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证和中断接力记录；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批唯一视觉检查台账。

## 明确边界

- 只实现方向反馈和六个离散正/反轴向视角；
- 不实现 Gizmo 拖动、自由旋转、视图立方体面点击或相机持久化；
- 不声称这是当前 LibTV 生产界面的完整截图或精确 CSS；
- 不复制上游模型、图片、外部 URL 或许可证边界之外的资产。
