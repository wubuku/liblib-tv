# Batch 70: Director Command And History Kernel

> 状态：`COMPLETE / DIRECTOR_HISTORY_FOCUSED_PASS`。
>
> 建档日期：2026-08-27。

## 1. 背景

Batch 67 建立了 `DirectorProjectDocumentV1` strict codec，Batch 68 建立了按
`route + canvasId + sourceNodeId` 隔离的 project/session owner，Batch 69 又把
`authoredObjects` 与当前 R3F runtime projection 分开。当前最大剩余可靠性缺口是：
Director 的 semantic mutation 没有 project-local history，连续拖动/输入没有统一
gesture transaction，undo/redo 也没有和普通 canvas graph history 明确隔离。

本批实现 `LIBTV-VR-024` 的 `DIR-CMD-I01 + DIR-CMD-I02` 核心切片，并为
`DIR-CMD-I03` 提供可复用的 gesture API。

## 2. 本批决策

```text
portable project document fingerprint
  -> semantic mutation observation
  -> one Director history entry
  -> project-local past/future
  -> explicit gesture begin/update/commit/cancel
```

- 使用 Batch 69 已验证的 portable document 作为 history before/after；
- selection、playhead、panel、phone preview、capture bytes 和 Three.js runtime
  不进入 history snapshot；
- 没有 active gesture 时，document 发生一次语义变化就产生一条 history；
- active gesture 期间的多次 preview 只保留在当前 store，不产生中间 history；
- gesture commit 只在 fingerprint 变化时产生一条 history；
- noop、空 history、无效 gesture、owner 不匹配不产生 history；
- Director undo/redo 只恢复 Director document，不调用普通 `canvasStore.undo/redo`；
- history 以 `projectId` 为 key 的内存 sidecar 保留，owner 切换不串 history；
- 本批不把所有旧 action 机械改名为 command，不实现 delete planner/copy/paste。

## 3. 预期结果

- 新增 typed `DirectorCommandResult`、stable reason 和 history/gesture 类型；
- 新增 `history.past/future/activeGesture/limit` store state；
- 既有 document mutation 通过统一 observation 自动进入 Director history；
- 提供 `beginDirectorGesture`、`commitDirectorGesture`、
  `cancelDirectorGesture`；
- 提供 `undoDirector`、`redoDirector`；
- Director workspace 消费 `Cmd/Ctrl+Z`、`Shift+Cmd/Ctrl+Z`、
  `Cmd/Ctrl+Y`，editable target 仍交给原生编辑器；
- 新增 pure/static 与 fresh-page Playwright verifier；
- 普通 canvas graph/history、FrameOS store 和 phone runtime 边界不回归。

## 4. 明确不解决

- object/camera/group 的 reference-aware delete；
- last-camera policy、resource lease、capture/export async freshness；
- copy/paste 与 clipboard remap；
- Director source-exact undo/redo UI、按钮文案和 LibTV authenticated evidence；
- browser persistence、cloud sync 和跨设备历史；
- 重新截图或重复识别已有源站截图。

## 5. 交接入口

- [`PLAN.md`](PLAN.md)：计划、状态机、验收与停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施切片、验证结果和历史；
- [`runtime-audit.json`](runtime-audit.json)：最近一次稳定结构化 verifier 结果；
- [`../../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  command/history/delete 总合同；
- [`../liblib-canvas-batch69-2026-08-27/`](../liblib-canvas-batch69-2026-08-27/)：
  authored/runtime 前置实现与 verifier。

## 5. 结果

Batch 70 已完成 Director project-local command/history kernel 的 focused pass：

- semantic document mutation 自动形成一条 bounded history entry；
- same-value、invalid-value、missing-target、empty-history、cancel 和 stale
  路径不会产生伪 history；
- repeated object-transform、group-transform 和 speed-curve gesture 可合并为
  一条 entry；
- undo/redo 恢复 strict-valid portable document，新的 commit 清空 redo future；
- project A/B、close/reopen generation 和普通 canvas graph/history 保持隔离；
- fresh-page Playwright、pure verifier、typecheck、lint、docs check 和 full
  project gate 的最终结果以 `IMPLEMENTATION.md` 为准。

本批仍不证明 LibTV source-exact Director UI、reference-aware delete、async
capture/export freshness、真实 mesh/resource loading、durable persistence 或
StoryAI 上游 schema parity。
