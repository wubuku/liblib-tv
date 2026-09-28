# Batch 555 — 全景球水平旋转/球形半径滑杆

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 45/48
> 右栏「全景球」组）：水平旋转（度，默认 0）与球形半径（源站示值 60）
> 两滑杆。

## 合同

- `DirectorScene` 新增 `panoramaRotation`（0）与
  `panoramaSphereRadius`（30——保持 clone 现渲染；源站示值 60 记
  SOURCE_DIFF）；
- V1 文档 optional 字段 + `expectScene` 兼容解码（batch 548 模式）；
- 场景属性面板 全景背景 区新增两滑杆：水平旋转 0-360°（°角标）、
  球形半径 10-100，均经 updateScene 持久化；
- 渲染接线：DirectorPanoramaRuntime 球体 mesh 应用 rotation-y 与半径
  props（props 自 DirectorViewport scene 传入）。

## 内容

- `src/store/directorStore.ts`（2 字段）；
- `src/lib/directorProjectDocument.ts`（V1 optional + 解码）；
- `src/components/director/DirectorInspector.tsx`（两滑杆）；
- `src/components/director/DirectorViewport.tsx`（props 传递 + 球体
  rotation/radius）；
- `scripts/verify-liblib-batch555.py`（7 检查）；
- 回归：batch 548/70 全绿；typecheck 净（除并行 frameos WIP）；
  verify-docs pass。
- `runtime-audit.json`：本目录。
