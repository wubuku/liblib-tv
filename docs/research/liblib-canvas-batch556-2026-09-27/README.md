# Batch 556 — 时间线引导气泡（1/5 coachmark）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：batch 552
> （截图 48）——时间线打开时左下角出现引导气泡：「请选择一个角色或者
> 摄像机后，可新建轨道」+「1/5」步数 +「跳过」/「下一步」按钮。

## 合同

- DirectorTimeline 根容器内绝对定位气泡
  （`data-director-timeline-coachmark`，bottom-left，w-300px）；
- 文案与 1/5 步数、跳过（ghost）/下一步（primary filled）两按钮；
- 步骤 2-5 未采样——跳过/下一步均收起气泡（CLONE_DECISION）；
- 每次挂载再现（组件本地态；会话级记忆留待后续）；
- 收起后时间线面板其余内容不受影响。

## 内容

- `src/components/director/DirectorTimeline.tsx`（coachDismissed 本地态
  + 气泡渲染；预设运镜面板 JSX 因插入竞态一度失衡，已还原 opener 行）；
- `scripts/verify-liblib-batch556.py`（9 检查：气泡内容、双按钮、跳过
  收起、重载再现、下一步收起）；
- 回归：batch 70/548/553 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
