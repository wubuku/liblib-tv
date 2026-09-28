# Batch 558 — 高斯地面吸附渲染端夹紧

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：截图 45
> （高斯地面吸附开启时角色贴地）。batch 551 在 authored 持久层夹紧 Y，
> 但 runtime 投影可能被时间线采样覆盖导致视觉不反映夹紧；本批在渲染端
> 兜底。

## 合同

- SceneObject 渲染位：`gaussianGroundSnap` 开且对象为 character 时，
  渲染组 Y = max(authored Y, 0)；机位/道具与关闭状态渲染自由 Y；
- known transient：selectObject 卸载/重挂周期触发 TransformControls
  attach 告警（batch 553 已留痕，与本批无关）——verifier 显式过滤；
- 实测：authored 与 runtime 均 0（runtime 投影继承 authored 夹紧），
  渲染端为防御性兜底；机位 -5 保持自由。

## 内容

- `src/components/director/DirectorViewport.tsx`（SceneObject 渲染位
  Y 夹紧 + gaussianGroundSnap 选择器）；
- `scripts/verify-liblib-batch558.py`（5 检查）；
- 回归：batch 70/548/551 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
