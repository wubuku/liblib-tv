# Batch 72 计划：Director Reference-Aware Delete And Resource Closure

> 状态：`COMPLETE / REFERENCE_DELETE_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 上游 checkpoint：`217dbe9`。

## 1. 目标

实现 Director destructive mutation 的最小可靠闭环：

1. pure typed delete planner 与显式 inverse-reference registry；
2. object/camera/group/track/path/capture/resource 的完整结构闭包；
3. last-camera、locked target、in-use resource 与 invalid post-state 的原子拒绝；
4. selection、timeline、path draft、phone/preset runtime 的同事务清理；
5. accepted delete 一条 history，reject/noop 零条；
6. delete -> undo -> redo 的 strict document 往返；
7. 对象树按钮与 Director foreground Delete/Backspace 路由。

## 2. 证据和边界

本批依赖：

- Batch 67 `DirectorProjectDocumentV1` strict codec；
- Batch 68 owner/session/generation registry；
- Batch 69 authored/runtime projection；
- Batch 70 project-local command/history；
- Batch 71 pointer commit/cancel lifecycle；
- [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)
  第 9-16 节。

StoryAI 固定上游只提供部分 object/camera/asset repair 方法；它不覆盖当前 clone 的
group、typed tracks、motion paths、capture、phone/preset 和 project-local history。
本批可借鉴其“两阶段 remap/repair”思想，但不复制其 store，也不把它当作 LibTV
source-exact 证据。

## 3. 删除政策矩阵

| Intent | Structural closure | Runtime repair | Reject condition |
|---|---|---|---|
| object/prop/character | detach group；删 object tracks、绑定 paths；清 camera refs | selection、track/path/draft、preset 清理 | missing、locked、project becomes empty |
| camera | object closure；capture `cameraId` 变 weak/null；active camera deterministic fallback | camera view、phone runtime、preset 清理 | deleting last camera |
| group `UNGROUP` | 保留 members；删 group tracks 与绑定 paths | selection 指向 surviving members | missing group |
| group `CASCADE` | group + member object closures | 同 object/camera closure | locked member、last camera |
| track | 删 track；删绑定 path并解绑共享引用 | track/keyframe/path/draft、preset 清理 | missing track |
| motion path | 删 path；所有 tracks 清 `motionPathId` | path/anchor/draft 清理 | missing path |
| capture | 删 descriptor 和 memory sidecar entry | active capture fallback | missing capture |
| resource `BLOCK` | 不修改 project | typed usage count | resource has object/capture refs |
| resource `CASCADE` | 删引用对象/capture，再删 resource ref | local descriptor只在 commit 后释放 | locked object、last camera、invalid closure |

对象删除后，camera `lookAtObjectId` / `followTargetId` 清空并切换到可解析的 coordinate
target；保留 document 中已存 target 数值。本批不声称这是 LibTV 的 exact freeze
算法。

## 4. 实现切片

### Slice A：pure planner

- [x] 新增 `directorDeletePlanner.ts`；
- [x] typed command、plan、deleted entity summary、runtime invalidation；
- [x] 显式 object/group/track/path/capture/resource inverse refs；
- [x] stable document-order fallback；
- [x] strict normalizer 作为 post-state gate；
- [x] reject/noop 保持 input document 不变。

### Slice B：store authority

- [x] 新增统一 `deleteDirectorEntity` command；
- [x] 取消 active gesture 后再计划 destructive command；
- [x] 通过 registry current owner/generation 校验；
- [x] 一次性 restore planned document；
- [x] 显式生成 typed result 和一条 history；
- [x] reconcile selection/timeline/path draft/phone/preset/capture sidecar；
- [x] local asset storage 只在 accepted resource command 后更新。

### Slice C：UI routing

- [x] ObjectTree object/group 删除 icon button；
- [x] Director foreground Delete/Backspace；
- [x] editable、active gesture、viewer/panel 优先级不回归；
- [x] timeline 与 capture 的既有删除按钮改走统一 command；
- [x] 最后机位、resource in-use 的 reason 通过 workspace diagnostics 可检查。

### Slice D：focused verifier

- [x] pure planner corpus；
- [x] character in group + tracks + path + camera refs closure；
- [x] active camera fallback + capture provenance repair；
- [x] last-camera reject 与 zero partial mutation；
- [x] group `UNGROUP` / `CASCADE`；
- [x] track/path reciprocal cleanup；
- [x] capture delete不改变 ordinary graph；
- [x] local resource `BLOCK` / explicit `CASCADE`；
- [x] delete/undo/redo exact document；
- [x] one accepted command one history；
- [x] keyboard route 与 editable guard；
- [x] zero console/page/request errors、zero screenshots。

### Slice E：治理与收口

- [x] 更新 current verifier manifest、fixture catalog、coverage、traceability；
- [x] 更新 verification ledger、HARNESS、research hubs、Big Picture、decision register；
- [x] 运行 Batch 67-72 focused gates；
- [x] 运行 `npm run docs:check`、`git diff --check`、`npm run check`；
- [x] commit/push 并确认唯一 master worktree 干净同步。

## 5. Fixture

共享 fixture：`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`。

本批在 fresh Director owner 中构造：

```text
character A in group G
  -> transform/pose tracks
  -> transform track P
camera A active
  -> lookAt/follow character A
  -> capture descriptor
camera B fallback
local model resource R
  -> instance object
  -> transform track/path
ordinary canvas graph/history baseline
```

每个 destructive 场景使用 fresh Page 或重新打开独立 owner，避免前一场景 history、
selection、local storage 或 resource side effect 污染下一场景。

## 6. 验收停止条件

只有全部满足才标记 `REFERENCE_DELETE_FOCUSED_PASS`：

- planner 是 pure function，输入 document 未被 mutation；
- accepted post-state 通过 strict V1 validation；
- 所有 strong refs 可解析，active camera 必定有效；
- last camera、locked target、in-use resource block 为零部分变更；
- object/group/track/path/capture/resource closure 符合政策矩阵；
- selection 与 transient runtime 不指向已删除实体；
- accepted delete 形成一条 history，reject/noop 为零条；
- undo/redo 恢复 exact portable document；
- capture delete不删除普通 graph result；
- ordinary canvas graph/history 与 FrameOS store不受影响；
- focused verifier、跨批回归、docs check 和 `npm run check` 全部通过；
- 文档记录证据边界、实现结果、失败修正和剩余风险；
- `master` 与 `origin/master` 同步且工作区干净。

## 7. 实施结果

2026-08-27 完成本批实现。pure planner verifier 与 fresh-page Playwright verifier
均通过；Batch 59、67、68、69、70、71 以及 `npm run check` 也通过。最终结果、
命令、动态 artifact 处理和剩余边界见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
与 [`runtime-audit.json`](runtime-audit.json)。
