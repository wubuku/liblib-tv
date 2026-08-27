# Batch 69 计划：Director Authored And Runtime Projection Split

> 状态：`COMPLETE / AUTHORED_RUNTIME_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 风险等级：高。修改 Director store 的数据权威和大量 projection writer，但不
> 修改普通 React Flow graph、两个 submodule 或 source site 状态。

## 1. 为什么是这一批

Batch 68 已关闭 Director 跨 source/canvas 的单例 project 串场，但其 snapshot
仍从 `state.objects` 读取。当前 `state.objects` 同时承担作者编辑值和 timeline
采样值：

```text
seek/playback -> applyTimelineAtTime -> objects
close/switch  -> snapshot(objects) -> project document
```

因此一个普通的非零时间 seek 就可能污染后续 project restore。Batch 69 先建立
最小双层模型，再进入 Director history/delete；不在同一批次顺手重写 3,800 行
store。

## 2. 已确定的状态模型

```text
authoredObjects
  = project document objects
  = direct semantic authoring baseline

objects
  = derive(authoredObjects, timeline, currentTime, groups)
  = current R3F/Inspector runtime projection
```

约束：

1. `snapshotCurrentDirectorProject` 只能使用 `authoredObjects`；
2. `setTimelineTime`、`advanceTimeline`、keyframe selection 和 path sampling
   只能更新 `objects`；
3. authoring mutation 必须更新 `authoredObjects`，再派生 `objects`；
4. runtime-only phone preview 不更新 `authoredObjects`；
5. imported phone take 是 authored camera/track mutation；
6. 现有 `objects` selector 暂时保留，避免一次性破坏已有 Director 组件和历史
   verifier；后续可再评估改名为 `runtimeObjects`。

## 3. Authoring mutation policy

| Mutation | authored layer | current keyframe | runtime |
|---|---|---|---|
| object name/color/visible/locked | 更新 | 不自动创建 | 重新派生 |
| transform Inspector/TransformControls | 更新 | `autoKeyframe` 且已有对应 track 时同步当前帧 | 重新派生 |
| camera target/FOV/follow settings | 更新 | `autoKeyframe` 且已有 camera track 时同步当前帧 | 重新派生 |
| group transform | 更新成员 authored transform | `autoKeyframe` 且已有 group track 时同步当前帧 | 重新派生 |
| pose control/preset | 更新 rig | 当前 pose keyframe | 重新派生 |
| timeline/path/keyframe edit | 不改 object baseline | 更新 project timeline | 重新派生 |
| phone live pose/recording | 不更新 | 不更新 | runtime-only preview |
| phone take import | 新 camera + track | 写入 timeline | 重新派生 |
| model/crowd add/remove | 更新对象集合 | 不自动创建 | 重新派生 |

若 `autoKeyframe=false`，direct transform/camera/group edit 只改 authored baseline；
当前已有时间轴采样可能继续覆盖视图，这是显式且可记录的语义，不通过猜测修改
旧 keyframe。

## 4. 实施切片

### Slice A：计划与纯 projection 设计

- [x] 记录 Batch 69 目标、状态模型和不重复截图理由；
- [x] 明确所有 `state.objects` 写入点；
- [x] 保留既有 runtime selector 兼容；
- [x] 增加 authored/runtime fingerprint 断言。

### Slice B：store 双层 authority

- [x] 增加 `authoredObjects` state；
- [x] 初始化、restore、snapshot 改为 authored source；
- [x] 所有 timeline projection writer 改用 authored source；
- [x] 所有对象集合和 semantic authoring writer 同步维护 authored/runtime；
- [x] phone live preview 保持 runtime-only。

### Slice C：verifier

- [x] pure helper/static assertions；
- [x] browser seek/playback fingerprint stability；
- [x] Inspector/keyframe authoring stability；
- [x] owner close/reopen restores authored baseline；
- [x] zero graph/history mutation、zero console/page/request errors。

### Slice D：治理与收口

- [x] 更新 current verifier manifest、fixture catalog、coverage、traceability；
- [x] 更新 `BIG_PICTURE`、`ARCHITECTURE`、`DEVELOPMENT`、`HARNESS`、`CHANGELOG`
  和 research hubs；
- [x] Batch 67/68/69/59、docs、full check；
- [x] commit/push checkpoint，确认 main workspace clean。

## 5. 停止条件

如果发现某个 mutation 需要同时猜测 authored、sampled 和 source semantics，
只记录为后续 `DIR-PROJECT-I04`/command contract 缺口，不扩张为无边界重构。

本批不因历史 verifier 仍读取 `state.objects` 而删除兼容字段；必须先证明
`objects` 的 runtime projection 语义稳定，再考虑更名或 API 收缩。
