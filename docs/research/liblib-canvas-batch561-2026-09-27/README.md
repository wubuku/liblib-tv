# Batch 561 — 全景背景已连接/提示标签

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 45/48
> 右栏）：3D 场景面板「全景背景」section——已连接时显示「已连接全景
> 图」状态；无上游图片节点时显示虚线提示框「请将图片节点连接到导演台
> 左侧输入口」。

## 合同

- 场景属性「画布环境」section 顶部新增「全景背景」标题；
- `panoramaRuntimeState === "ready"` → 「已连接全景图」状态文本
  （`data-director-panorama-connected`）；
- `panoramaInputs` 为空（无上游图片节点）→ 虚线提示框
  （`data-director-panorama-hint`）「请将图片节点连接到导演台左侧
  输入口」；
- 与既有 画布环境 select（batch 558 前：panorama source 选择）与
  状态点文本共存。

## 内容

- `src/components/director/DirectorInspector.tsx`（全景背景标题 +
  已连接标签 + 空上游提示框）；
- `scripts/verify-liblib-batch561.py`（5 检查：section/标题、空上游
  提示框文本）；
- 回归：batch 539/70 全绿；typecheck 净（除并行 VitePress dist 噪音）。
- `runtime-audit.json`：本目录。
