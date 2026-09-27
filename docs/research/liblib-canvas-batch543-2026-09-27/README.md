# Batch 543 — 导演台重置视角按钮

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第二轮源站采样
> （liblib-source-exploration-2026-09-25 NOTES §8 + 截图
> 18-director-console-opened.png）：导演台视口右上为姿态 gizmo +
> 其正下方「重置视角」胶囊按钮。clone 此前只有 gizmo 本体（322-396 行
> 已有坐标控件），无重置按钮。

## 合同

- 重置按钮（`data-director-reset-view`）渲染于 gizmo 容器正下方
  （absolute top-[calc(100%+8px)]）；
- 点击 → `setDirectorCameraCommand({ ...DEFAULT_DIRECTOR_VIEWPORT_SNAPSHOT })`
  （新对象引用触发 CameraController 重新应用快照：position 6.2/4.25/7.4、
  target 0/1/0、fov 45），恢复导演台默认机位；
- 交互纯本地（无网络、无生成）。

## 内容

- `src/components/director/DirectorViewport.tsx`（gizmo 组件 +onResetView
  prop、按钮渲染、DirectorViewport 复位 handler）；
- `scripts/verify-liblib-batch543.py`（7 检查：可见性、文案、gizmo 下方
  定位、点击后工作区稳定）；
- 回归：batch 70/535 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
