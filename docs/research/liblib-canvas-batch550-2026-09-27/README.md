# Batch 550 — 网格吸附接入变换系统

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 45，
> 3D 场景面板）：「网格吸附」开关默认关。batch 548 落了 schema 与开关，
> 本批把语义接进变换系统。

## 合同

- `scene.snapToGrid` 开启 → 全部三处 TransformControls
  （SceneObject 对象 / DirectorGroupTransformRig 分组 / PathControlPoint
  路径锚点）启用 `translationSnap=0.5`（drei 透传 three-stdlib）；
  关闭 → `translationSnap=null` 自由移动；
- 开关为 `updateScene` 持久化字段（batch 548 schema），选中对象后
  状态保持；默认关；
- 高斯地面吸附为数据态（其吸附语义涉及高斯模型脚底对齐，渲染侧
  待后续，CLONE_DECISION 注记于 batch 548）。

## 内容

- `src/components/director/DirectorViewport.tsx`（三处 rig 组件
  snapToGrid 选择器 + translationSnap prop）；
- `scripts/verify-liblib-batch550.py`（5 检查：默认关、开启持久、
  选中后保持、关闭恢复）；
- 回归：batch 70/548/549 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
