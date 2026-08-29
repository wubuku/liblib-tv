# Batch 88 计划：Director selection、Timeline 与变换目标交叉一致性

> 状态：`COMPLETED / RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 本批是当前五批连续迭代中的第五批，也是本轮最后一批。完成本批后暂停，
> 等待 review，不启动 Batch 89。

## 1. 背景与证据

Batch 87 修复了 undo/redo 和 gesture cancel 的 restore-selection policy，但
当前仍存在一个相邻的 authority 缺口：对象树/Viewport 通过
`selectedObjectId`，Inspector 通过当前对象重新查找关联轨道，而 Timeline
高亮直接使用 `timeline.selectedTrackId`。这些字段在不同入口被分别更新，可能
短暂或持续指向不同实体。

已确认的 clone 事实：

- `selectObject`、`toggleObjectSelection` 和 `selectGroup` 是 UI-only selection
  action，不产生 Director document history；
- `selectTimelineTrack` 和 `selectTimelineKeyframe` 会反向更新对象/分组选择；
- `DirectorViewport` 的对象/分组 `TransformControls` 只在当前选择上下文挂载；
- `DirectorInspector` 依据当前对象/分组查找相关 transform/camera/group track；
- `DirectorTimeline` 依据 `timeline.selectedTrackId` 高亮轨道，并依据该轨道
  判断 lock、path、keyframe、curve 和可编辑入口；
- `authoredObjects` 是 Director portable authoring baseline，`objects` 是
  当前 playhead 的 runtime projection；
- selection、playhead、timeline editor mode 和 TransformControls 引用都不属于
  portable Director document；
- Batch 84–87 已建立 locked-target、selection/CRUD、transform context、
  pointer cancellation 和 restore-selection 合同。

## 2. 本批高价值问题

| 问题 | 影响 |
|---|---|
| 对象树选择对象后仍高亮旧的 Timeline track | 用户会看到对象树/Inspector 与 Timeline 不是同一目标 |
| 选中无轨道对象后仍保留旧 track/path/keyframe | Timeline 操作可能误作用于上一个对象，或产生错误的 lock/path 上下文 |
| 对象轨道被删除、对象撤销恢复后 track selection 悬挂 | Inspector、Timeline、Curve 和 TransformControls 的目标语义分裂 |
| group selection 与 group track 不一致 | 分组 Inspector/Viewport 可能可用，但 Timeline 仍显示成员或旧分组轨道 |
| selected keyframe/path/anchor 跨对象保留 | playhead、路径控制点和变换目标可能指向已不相关的实体 |
| selection-only 修复若进入 document history | 破坏既有 history 与 portable document 边界 |

## 3. Clone-owned 决策

### 3.1 选择对象时同步 Timeline

- 单对象选择：
  1. 如果当前 selected track 已经属于该对象，保留当前 track（包括 pose track）；
  2. 否则优先选择该对象已有的非 pose track；
  3. 若没有非 pose track，再选择该对象已有的 pose track；
  4. 若对象没有任何 track，清空 selected track/keyframe/path/anchor；
  5. 不自动创建新 track，不改变 document/history。
- 多选对象：
  - 保持多选语义；
  - 清空 Timeline track/keyframe/path/anchor selection，避免把单目标轨道误投影为
    多目标编辑上下文。
- 分组选择：
  - 如果当前 selected track 属于该 group，保留；
  - 否则选择该 group 已有的 group track；
  - 没有 group track 时清空 Timeline entity selection；
  - 不自动创建 group track。
- 清除选择：
  - 同时清空 selected track/keyframe/path/anchor/handle；
  - 保留当前 playhead、zoom、loop 和 editor mode。

### 3.2 Timeline 反向选择

- 点击 track/keyframe 时继续由 Timeline 作为选择 authority；
- 选中 track/keyframe 必须让 object/group、Inspector、Viewport transform context
  与其指向同一 object/group；
- keyframe 选择继续改变 playhead 和 runtime projection，但不写 document history；
- pose track 可以选择对象，但不把 pose track误判为 transform gizmo 的替代物。

### 3.3 Restore、删除与 locked guard

- undo/redo/cancel 继续使用 Batch 87 的 preserve-and-repair；
- repair 后 selected track 的 owner 必须与 selected object/group 相容；
- selected keyframe 必须属于 selected track；
- selected motion path 必须属于 selected track，anchor 必须属于 selected path；
- 删除/撤销/重做后不得保留已删除的 gizmo target、track、path 或 anchor；
- locked target 的拒绝与 Batch 84–87 保持不变，selection-only 操作不生成 history。

这些决策只描述 clone-owned authority，不宣称 LibTV 原站 Director 的 exact
selection、timeline 联动、undo selection 或 locked UI policy。

## 4. 实施范围

纳入：

- 提取可测试的 Timeline selection normalization/helper；
- 让 object/group/multi-selection 与 timeline entity selection 使用单一兼容规则；
- 让 Batch 87 restore repair 同时校验 track owner 与 object/group selection；
- 在 delete/restore 路径后清理悬挂 track/path/keyframe/anchor selection；
- 增加 Batch 88 pure/source verifier 和 fresh-page Playwright verifier；
- 更新 current verifier manifest、verification ledger、Harness、research index、
  component coverage 和实施记录；
- 运行固定 `http://localhost:4317` 的 Batch 59、67–88 current-gate 回归。

不纳入：

- 不把 selection、timeline UI 或 TransformControls 引用加入 portable document；
- 不自动为选择对象创建轨道；
- 不改变 authored/runtime、Director owner/session、history/delete、ordinary
  React Flow 或 FrameOS 边界；
- 不改变 TransformControls 的 Three.js attachment 或 pointer lifecycle；
- 不新增 LibTV 源站截图或把 clone behavior 写成 source-exact 事实。

## 5. 验收标准

- 对象树单选对象后，Timeline selected track 要么属于该对象，要么为空；
- 对象树多选后不显示单目标 selected track/path/keyframe；
- 选中 group 后，Timeline selected track 要么属于该 group，要么为空；
- Timeline track/keyframe 点击后，对象树、Inspector、Viewport context、gizmo
  target 和 Timeline 全部指向同一 object/group；
- 无轨道对象和无轨道 group 不会继承上一个目标的 track 操作上下文；
- undo/redo/cancel、delete/undo/redo 后没有悬挂 track/path/keyframe/anchor 或
  已删除 TransformControls 目标；
- locked rejection 仍为 zero document/history mutation；
- selection/timeline-only actions 不产生 document fingerprint 或 history delta；
- pure verifier、fresh-page Playwright、Batch 59、67–88 current-gate、
  `npm run check`、`npm run docs:check`、`python3 scripts/verify-docs.py` 和
  `git diff --check` 全部通过，browser diagnostics 为 `0 / 0 / 0`；
- Batch 88 结果和 artifact 完整落档，commit/push 后 `master` 工作区干净；
- 完成 Batch 88 后本轮进度为 `5/5`，暂停等待 review。

## 6. 执行步骤

- [x] 阅读 Batch 84–87 合同、store restore/delete 路径和 Director 组件选择路径；
- [x] 记录高价值缺口、selection normalization 决策和证据边界；
- [x] 实施 timeline/entity selection normalization；
- [x] 新增并运行 Batch 88 pure/source verifier；
- [x] 新增并运行 Batch 88 fresh-page Playwright verifier；
- [x] 运行 Batch 59、67–88 current-gate 回归；
- [x] 更新台账、manifest、Harness、索引、coverage 和 Batch 88 实施记录；
- [x] 运行全量检查并 commit/push；
- [x] 确认工作区干净，报告 5/5 并暂停。
