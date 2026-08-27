# Batch 70 计划：Director Command And History Kernel

> 状态：`COMPLETE / DIRECTOR_HISTORY_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 上游 checkpoint：`f545289`。

## 1. 目标

实现 Director project-local command/history 的最小可靠闭环，重点解决：

1. semantic project document mutation 的统一 commit；
2. `past/future` undo/redo；
3. repeated gesture update 的 one-entry coalescing；
4. noop、empty、owner-stale 的 zero-entry 行为；
5. Director history 与普通 canvas graph history 隔离；
6. 明确为下一批 reference-aware delete 留出 command kernel 接口。

## 2. 证据和边界

本批依赖：

- Batch 67 的 strict `DirectorProjectDocumentV1` codec；
- Batch 68 的 owner/session/generation registry；
- Batch 69 的 `authoredObjects` baseline 与 runtime projection；
- `LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md` 第 4、7、8、14、15、16、17 节。

本批把当前 clone contract 转换为可执行的 reliability floor，不把 StoryAI 的
store、截图或 UI 当作 LibTV source-exact 证据。

## 3. 实现切片

### Slice A：typed command kernel

- [x] 新增 command disposition/reason/result 类型；
- [x] 新增 deterministic document fingerprint；
- [x] 新增 bounded history state 和 entry；
- [x] 新增 gesture baseline identity。

### Slice B：store history authority

- [x] history 以 `projectId` 内存 sidecar 隔离；
- [x] document mutation observation 自动记录 semantic commit；
- [x] active gesture 期间抑制中间 entries；
- [x] registry update 与 history commit 保持同一 current owner；
- [x] open/close/switch 不产生伪 history。

### Slice C：undo/redo 与 gesture API

- [x] `undoDirector` exact document restore；
- [x] `redoDirector` exact document restore；
- [x] 新 commit 清空 future；
- [x] `beginDirectorGesture` 捕获 project/session/generation/baseline；
- [x] `commitDirectorGesture` one-entry/noop；
- [x] `cancelDirectorGesture` restore baseline/zero entry；
- [x] Director shortcuts 不穿透到普通 canvas。

### Slice D：focused verifier

- [x] pure kernel/static assertions；
- [x] semantic mutation one-entry；
- [x] same-value/no-op zero-entry；
- [x] gesture repeated update one-entry；
- [x] undo/redo exact document round-trip；
- [x] redo future truncation；
- [x] project A/B history isolation；
- [x] Director history 不改变普通 graph/history；
- [x] zero console/page/request errors。

### Slice E：治理与收口

- [x] 更新 current verifier manifest、fixture catalog、coverage、traceability；
- [x] 更新 `AGENT_TASK_MAP`、`HARNESS`、research hubs、`CHANGELOG`；
- [x] 运行 Batch 67/68/69/70/59、docs check、`npm run check`；
- [x] commit/push 并确认主 worktree 干净。

## 4. 验收停止条件

只有满足以下条件才标记 `DIRECTOR_HISTORY_FOCUSED_PASS`：

- history entry 的 before/after 都是 strict-valid V1 document；
- 一个 semantic mutation 最多一条 entry；
- gesture 多次 update 只产生一条 entry；
- same-value/noop/empty/stale/cancel 产生零 entry；
- undo/redo 恢复 exact portable document；
- 新 commit 清除 redo future；
- A/B owner 不能消费彼此 history；
- Director undo/redo 不改变普通 canvas graph/history；
- focused verifier、docs check 和 `npm run check` 通过。

## 5. 完成记录

2026-08-27 已完成代码、verifier 和文档收口。Batch 70 fresh-page verifier
使用 `http://localhost:3001`，不产生截图，结果见
[`runtime-audit.json`](runtime-audit.json)。关键补强包括：

- `updateObjectTransform` 对缺失目标、非 finite 值和同值输入返回明确的
  rejected/no-op command result，均为零 history entry；
- undo/redo 继续验证当前 `projectId` 和 document fingerprint，但不把新的
  session `generation` 当成旧 project history 的冲突条件；
- 通过真实 Director close/reopen 验证 generation 递增后，A 项目仍可消费自己的
  history，且不会改变普通 canvas graph/history；
- `DirectorDesk`、TransformControls 和 speed-curve pointer lifecycle 暴露并消费
  history/gesture diagnostics。

## 6. 已知后续

本批完成后，下一优先级仍是：

1. `DIR-CMD-I03`：把 TransformControls、Inspector、pose、curve、path 的真实
   pointer lifecycle 接到 begin/update/commit/cancel；
2. `DIR-CMD-I04`：object/camera reference-aware delete planner；
3. `DIR-CMD-I05`：group/track/path/capture/local asset delete 与 copy/paste。
