# Batch 553 — 时间线「+ 新建轨道」按钮与 store 动作

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 552
> （截图 48）——时间线左控制簇含「+ 新建轨道」，onboarding 提示
> 「请选择一个角色或者摄像机后，可新建轨道 1/5」。

## 合同

- `directorStore.createTrackForSelectedObject`：为选中对象（character/
  camera）经 `createTrackForObject` 创建变换轨道并选中，走完整
  before/after 文档快照 + 历史提交（getDirectorDocumentSnapshot 模式，
  STALE 兜底）；
- 无合格选中 → REJECTED（DIRECTOR_TARGET_MISSING）；对象已有轨道 →
  NOOP（DIRECTOR_COMMAND_NO_CHANGE，数量与历史不变）；
- 时间线控制簇新增按钮（`data-director-add-track`，Plus 图标）：
  无合格选中时 disabled，tooltip 提示源站 onboarding 文案；
- **克隆不变量**：创建路径（addDirectorCamera/addCrowdArray 等）保证
  角色/机位恒有轨道，故按钮的可行创建态在 clone 中不可达——点击恒为
  NOOP（verifier 断言数量与历史不变）；保留按钮以维持源站形态
  （CLONE_DECISION）。

## 内容

- `src/store/directorStore.ts`（createTrackForSelectedObject）；
- `src/components/director/DirectorTimeline.tsx`（按钮）；
- `scripts/verify-liblib-batch553.py`（5 检查：禁用态、启用、NOOP
  幂等、历史不变）；
- 回归：batch 70/536/549 全绿；typecheck 净；lint 0 error（并行
  VitePress dist 产物告警除外，非我方文件）。
- `runtime-audit.json`：本目录。
