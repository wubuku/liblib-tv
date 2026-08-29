# Batch 88 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 代码和文档在 `master` 主 worktree 完成。

## 1. 实施内容

### 1.1 统一 selection normalization

`src/store/directorStore.ts` 新增 `normalizeDirectorTimelineSelection` 和
`chooseDirectorTimelineTrack`：

- 单对象选择只接受该对象的普通、相机或 pose track；
- 当前 track 属于该对象时优先保留；
- 切换对象时优先非 pose track，再退化到 pose track；
- 多选清空单目标 Timeline entity selection；
- group selection 只接受对应 group track；
- keyframe、motion path 和 anchor 必须继续属于当前 selected track/path；
- 选择动作不创建轨道，也不写 Director document history。

### 1.2 接入所有高风险入口

除对象树和 Timeline 选择外，以下直接写入选择/轨道上下文的入口也经过
normalization：

- 对象/相机 transform 和属性自动关键帧；
- 姿态 preset/control 写入；
- motion path 创建、绘制完成和 anchor 选择；
- camera motion preset；
- phone Vcam take import；
- project-scoped clipboard paste；
- delete projection、portable restore、undo/redo 和 gesture cancel。

`DirectorInspector` 现在只在 `timeline.selectedTrackId` 与当前 object/group
owner 同时匹配时显示 selected track，并提供
`data-director-inspector-track-id` 作为验证选择器。

### 1.3 回归发现与修复

最终跨批回归先暴露了两个与本批 authority 直接相关的问题，均已在本批修复：

- `updateCamera` 被错误地改成总是选中被更新相机。恢复为：当前操作本来就在该
  相机上下文时保持相机 selection；外部更新非当前目标相机时保留原 selection，
  避免 reference-aware delete 等既有调用被误导。
- restore-selection 使用的 normalization 被错误地允许 fallback 到对象已有轨道。
  增加 `fallbackToCompatibleTrack: false`，使 preserve-current repair 在非法
  `selectedTrackId` 后保持空 track；正常对象/group selection 仍使用兼容轨道
  fallback。

同时，`finishMotionPathDrawing` 现在会完整写入
`selectedObjectId/selectedObjectIds/selectedGroupId`，并经过同一 normalization；
Batch 88 verifier 增加了该自由绘制完成场景。

### 1.3 保持既有边界

- `authoredObjects` 仍是 portable authoring baseline，`objects` 仍是 playhead
  runtime projection；
- selection、playhead、editor mode 和 TransformControls 引用不进入
  `DirectorProjectDocumentV1`；
- locked target 仍返回 `DIRECTOR_TARGET_LOCKED`，不改变 document 或 history；
- 不修改普通 React Flow、FrameOS、Director owner/session 或 TransformControls
  attachment/pointer lifecycle；
- 不把 StoryAI、Open Canvas 或 clone selection policy 写成 LibTV 原站事实。

## 2. 验证

### 2.1 Pure/source verifier

```bash
node --experimental-strip-types scripts/verify-liblib-batch88.mjs
```

结果：`PASS`。覆盖 normalization helper、单/多选和 group track 规则、删除
修复、直接编辑入口、Inspector/Timeline 连接、Viewport transform context 和
source boundary。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch88.py
```

结果：`SCRIPT_RECORDED_PASS`。覆盖：

- 无轨道对象不会继承前一对象的 track/path/keyframe；
- 同对象可保留兼容 track，Timeline track/keyframe 点击会反向驱动对象树、
  Inspector 和 Viewport；
- 多选清空单目标 Timeline 上下文；
- group track 与 group Inspector 一致；
- motion path/anchor 不会跨对象保留；
- 删除 track/object 后不保留悬挂 selection context；
- locked mutation 保持 document/history 零变化；
- selection-only 操作不写 portable document/history；
- mobile workspace 不越出 viewport。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

### 2.3 跨批与全量检查

在固定 `http://localhost:4317` 上串行运行 Batch 59、67–88 current gates；最终
回归在上述两个修复之后重新执行，23 个 gate 全部通过。执行：

```bash
npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

回归结果见 [`current-gate-regression.json`](current-gate-regression.json)，其中
记录了执行时的 HEAD、server、artifact delta 和 worktree 状态。

## 3. 证据边界

| 类型 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前 clone 的 selection surfaces、Director store authority 和 component selectors |
| `CLONE_DECISION` | 以单一 normalization 保持对象树、Timeline、Inspector、Viewport 和 TransformControls 一致 |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 的 selection、Timeline 联动、undo/redo selection 和 exact UI policy |
| `UPSTREAM_INSPIRATION` | StoryAI/Open Canvas 只作为领域组织和验证方法参考 |

## 4. 结果

| Gate | Result |
|---|---|
| pure/source verifier | `PASS` |
| fresh-page Batch 88 | `SCRIPT_RECORDED_PASS` |
| current-gate Batch 59、67–88 | `CURRENT_GATE_SERIAL_REGRESSION_RECORDED_PASS` |
| npm/docs full checks | `PASS` |
| diagnostics | `0 / 0 / 0` |
| screenshot artifact delta | `0` |
| source-exact Director claim | `NONE` |

Closeout commit: `306786d`, pushed to `origin/master`; the final master worktree
was verified clean.
