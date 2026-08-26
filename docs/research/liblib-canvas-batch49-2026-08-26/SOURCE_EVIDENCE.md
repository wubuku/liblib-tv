# Batch 49 源站与证据记录

## 1. 当前可用证据

### LibTV source contract

Batch 34 的当前 LibTV bundle/locale 研究确认：

- 画布包含 `DIRECTOR_CONSOLE_3D` 导演台节点；
- 导演台属于真实 3D authoring domain，而非普通 React Flow 节点面板；
- 源站 bundle 载有 scene、camera、timeline、path、pose、capture 和
  animation export 等导演台能力词汇；
- 但当前证据没有证明 LibTV 生产实现一定使用 Three.js 或 R3F；
- 当前 source 的 orientation gizmo 精确 DOM/CSS 尚未在本批重新取得。

因此本批的“可做”依据主要是固定上游实现和当前 clone 已有的 R3F
导演台基础，不把 gizmo 形状或尺寸写成 LibTV source fact。

### Clone audit

Batch 48 收口后的 clone 已具备：

- `DirectorViewport` 的主 R3F `<Canvas>`；
- Director/Camera 视角切换；
- `TransformControls` 和 `OrbitControls`；
- aspect frame、thirds、capture、path drawing、phone vcam、model-library
  等 overlay；
- `directorStore` 中可序列化的 Director object/camera/timeline 状态。

当前缺口是没有可见的轴向坐标反馈，也没有离散轴向相机跳转入口。

## 2. 不可推出的结论

- 不能由上游仓库证明当前 LibTV 使用同一个 `GizmoViewport`；
- 不能由 clone 的 R3F 实现反推源站 renderer；
- 不能把 gizmo 点击视为修改 camera object 或 timeline 的 source transaction；
- 不能把上游 80×80px、20px offset 视为 authenticated LibTV 的精确值；
- 不能由本批验证结果声称 source-side camera persistence 或完整视图立方体。

## 3. 允许的 clone 决策

- 复用上游“独立 gizmo canvas + transparent DOM hit layer”的结构；
- 将主相机的 target/radius 映射为 clone-local `DirectorCameraSnapshot`；
- 点击正/反轴只改变当前导演视角的相机 snapshot；
- 不改变 `activeCameraId` 对应对象，也不写入 timeline；
- 在 capture 和 authoring modal 状态中隐藏或禁用，保证现有流程不受干扰。

## 4. 引用入口

- fixed upstream commit：`8c8bd361790be4d37158a7430365e65546e358fe`；
- [`../liblib-canvas-batch34-2026-08-26/CODE_ARCHAEOLOGY.md`](../liblib-canvas-batch34-2026-08-26/CODE_ARCHAEOLOGY.md)；
- [`../liblib-canvas-batch34-2026-08-26/LIBTV_DIRECTOR_EVIDENCE.md`](../liblib-canvas-batch34-2026-08-26/LIBTV_DIRECTOR_EVIDENCE.md)；
- [`../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md`](../liblib-canvas-batch35-2026-08-26/DIRECTOR_WORKSPACE.spec.md)；
- [`../liblib-canvas-batch48-2026-08-26/MATURITY_ASSESSMENT.md`](../liblib-canvas-batch48-2026-08-26/MATURITY_ASSESSMENT.md)。
