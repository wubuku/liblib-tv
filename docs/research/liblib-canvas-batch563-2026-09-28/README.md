# Batch 563 — 摄像机面板三页签 + 运动轨迹(NEW) 页签

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：CDP 截图
> 50/51（2026-09-29）——选中机位1 后摄像机面板出现三页签
> 属性 | 运动轨迹(NEW) | 截图；运动轨迹页签内容为 虚拟相机（wifi 提示
> + QR + 录制/重试）+ ⟳ 预设运镜 + 创建运动轨迹。

## 合同

- cameraTab 扩展为 properties/motion/captures；摄像机面板页签栏三列，
  运动轨迹页签带 NEW 角标（`data-director-camera-motion-new`）；
- motion 页签内容（`DirectorCameraMotionTab`）：虚拟相机 section
  （wifi 提示 + QR + 录制/重试）+ ⟳ 预设运镜 + 创建运动轨迹提示按钮；
- **QR 点击 → connectPhoneVcamLocal**（真实 store 动作，status →
  local-ready）；**录制 → startPhoneVcamRecording**（真实动作；未连接
  禁用，源站需先扫码）；重试为可视按钮；
- 预设运镜/创建运动轨迹完整面板位于时间线控制簇，此处提示态渲染
  （CLONE_DECISION）；无云端动作。

## 内容

- `src/components/director/DirectorCameraMotionTab.tsx`（新组件）；
- `src/components/director/DirectorInspector.tsx`（三页签 + motion
  branch）；
- `scripts/verify-liblib-batch563.py`（17 检查：三页签、NEW 角标、
  QR 连接、录制状态机、提示按钮）；
- 回归：batch 70/547/561 全绿；typecheck 净。
- `runtime-audit.json`：本目录。
