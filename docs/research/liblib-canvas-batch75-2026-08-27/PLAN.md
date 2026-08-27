# Batch 75 计划：Director Clipboard Identity Remap

> 状态：`COMPLETED / CLIPBOARD_REMAP_FOCUSED_PASS`。
>
> 日期：2026-08-27；实现 checkpoint：`27c6127`。

## 1. 目标

完成同一 Director project 内的 typed copy/paste：

1. portable clipboard packet；
2. group/object/track/path closure；
3. object/group/track/path/keyframe/anchor two-pass ID remap；
4. camera internal remap 与 external detach/freeze；
5. deterministic spatial offset；
6. stable resource alias 与 bytes/capture exclusion；
7. one accepted paste -> one Director history；
8. project-scoped clipboard、editable shortcut guard 和普通 graph isolation。

## 2. 实施切片

### Slice A：pure packet/planner

- [x] 新增 `src/lib/directorClipboard.ts`；
- [x] 定义 V1 packet、selection、build/paste result 与 stable reason；
- [x] 收集 object/group/track/path/resource closure；
- [x] two-pass remap 所有 project-local ID/reference；
- [x] strict normalize final document，失败 zero-partial；
- [x] same-project、resource conflict 和 empty packet guard。

### Slice B：store authority

- [x] `DirectorState` 增加 project-scoped clipboard 与 paste count；
- [x] `copyDirectorSelection` 不修改 project/history；
- [x] `pasteDirectorClipboard` 通过 registry/document/history/persistence 一次提交；
- [x] paste 后选择新 object/group；
- [x] undo/redo、close/reopen、A-B-A 和 persistence 不携带 clipboard。

### Slice C：workspace UX

- [x] 非 editable/composing 状态支持 `Cmd/Ctrl+C`；
- [x] 非 editable/composing 状态支持 `Cmd/Ctrl+V`；
- [x] foreground viewer/busy state 不执行 paste；
- [x] 不增加无源站证据的 visible toolbar/context menu。

### Slice D：focused verifier

- [x] pure single object、multi object、group closure；
- [x] internal/external camera relation；
- [x] track/path/keyframe/anchor remap；
- [x] stable resource alias、capture/runtime exclusion；
- [x] repeated paste offset/identity；
- [x] empty/stale/resource-conflict zero mutation；
- [x] browser keyboard copy/paste、selection、one history、undo/redo；
- [x] A/B project clipboard isolation、reload persistence boundary；
- [x] ordinary canvas graph/history 和 diagnostics 零变化；
- [x] screenshots 为零。

### Slice E：治理与回归

- [x] 更新 Director contracts、manifest、fixture、ledger、traceability；
- [x] 更新 coverage、Big Picture、Agent Task Map、HARNESS、hubs、CHANGELOG；
- [x] 运行 Batch 67-75 focused gates；
- [x] 运行 `npm run docs:check`、`git diff --check`、`npm run check`；
- [x] 记录实施结果、commit/push，确认唯一主 worktree 干净。

## 3. Fixture

```text
project A:
  character A + prop B + camera C
  group G(A, D)
  transform/pose/camera/group tracks
  motion path P bound to A
  camera C -> internal A and external B variants
  stable catalog resource R
  capture X with sentNodeId

project B:
  independent owner/document/history
```

核心断言：

- packet 不含 capture、runtime、UI、history、persistence metadata；
- paste 新 ID 全部唯一，旧 ID 只允许出现在 source packet；
- internal refs 全映射，external camera refs 全 detach；
- accepted paste document strict-valid，exact one history；
- stale/invalid paste 不改变 document/history/selection/persistence；
- repeated paste offset 为 deterministic `0.6 * ordinal`。

## 4. 停止条件

只有全部满足才升级为 `CLIPBOARD_REMAP_FOCUSED_PASS`：

- pure packet/planner 覆盖完整 typed closure；
- store copy/paste 只通过 canonical authority；
- keyboard 不劫持 editable/composition；
- one paste one history，undo/redo exact；
- A/B project、ordinary graph 和 persistence 边界通过；
- Batch 67-75、docs check、`npm run check` 全部通过；
- 文档明确 clone-owned decision、source unknown 和跨 project/resource non-goal；
- commit/push 完成，`master == origin/master` 且唯一 worktree 干净。

上述条件均已满足；精确命令和结果见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)。

## 5. 暂不解决

- system clipboard MIME、跨浏览器/跨窗口 paste；
- cross-project/cross-canvas Director packet transfer；
- resource bytes、lease transfer 或真实 asset materialization；
- capture/capture gallery copy；
- source/canvas duplicate 的整个 Director project deep clone；
- Option-drag、visible context menu、source-exact copy/paste feedback；
- ordinary React Flow graph clipboard。
