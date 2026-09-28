# Batch 575 — 摄像机面板轴向关键帧菱形标记

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 574
> （截图 60）——摄像机面板 位置 X/Y/Z 输入右侧的青色菱形关键帧标记
> （该轴存在关键帧的指示）。

## 合同

- `AxisFields` 新增 `keyframedAxes` prop：该轴存在关键帧时在轴标签旁
  渲染青色菱形标记（`data-director-keyframed-axis` + index）；
- 摄像机面板 位置 AxisFields 传入 keyframedAxes——从变换轨道反查当前
  播头时间的轴关键帧；相机轨道关键帧 value 形如 { transform, target,
  fov }，取 `value.transform[field]` 判存；
- 新增机位的创建关键帧（t=0，cloneCameraValue 含三轴）→ 徽标立现；
- 标记为可视指示，不改变交互。

## 内容

- `src/components/director/DirectorInspector.tsx`（AxisFields + 徽标 +
  keyframedAxes memo）；
- `scripts/verify-liblib-batch575.py`（4 检查：新增机位后三徽标立现，
  变换提交后保持）；
- 回归：batch 36/70/563 全绿；typecheck 净（除并行 frameos WIP）；
  verify-docs pass。
- `runtime-audit.json`：本目录。
