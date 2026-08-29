# Batch 87 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 代码和文档在 `master` 主 worktree 完成。

## 1. 实施内容

### 1.1 恢复策略显式化

`restoreDirectorProjectState` 增加恢复 policy：

- `default`：首次打开、重开和项目导入使用既有确定性默认选择；
- `preserve-current`：undo、redo 和 gesture cancel 保留当前 UI selection，
  再按恢复后的 document 做合法性修复。

selection 没有被加入 `DirectorProjectDocumentV1`，因此不会污染导出文件、
持久化 fingerprint 或 Director domain history。

### 1.2 Selection repair

`repairDirectorSelectionState` 负责：

- 过滤恢复文档中不存在的 selected object IDs；
- 保留仍有效的 group，并把分组成员重新投影为当前对象 selection；
- 清理失效 group、track、keyframe、motion path、anchor 和 handle；
- 保留当前 playhead/curve editor/zoom 等允许保留的 runtime UI 状态；
- 在 selection 全部失效时返回空选择，不跳到无关的 timeline 首项。

恢复后仍通过 `applyTimelineAtTime` 从 `authoredObjects` 生成 runtime
`objects`，没有改变 Batch 69 的 authoring/runtime boundary。

### 1.3 未改变的边界

- 未改变普通 React Flow、FrameOS 或 Director project owner/session；
- 未改变 one-entry history、redo truncation、reference-aware delete、
  locked-target rejection 或 pointer cancellation；
- 未把 StoryAI、Open Canvas 或 clone-only selection 策略写成 LibTV 原站事实；
- 未新增截图或真实 LibTV Director source-exact 结论。

## 2. 验证

### 2.1 Pure/source verifier

```bash
node --experimental-strip-types scripts/verify-liblib-batch87.mjs
```

结果：`PASS`。覆盖 explicit restore policy、object/group/timeline selection
repair、portable document exclusion 和 source boundary。

### 2.2 Fresh-page Playwright

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch87.py
```

结果：`SCRIPT_RECORDED_PASS`。覆盖：

- 对象与 timeline track authority 基线；
- one-entry document mutation；
- undo/redo 保留对象选择，并保持对象树、Inspector、Viewport context 同步；
- 非法 object/group/timeline selection 清理；
- portable export 不包含 selection；
- console/page/request diagnostics `0 / 0 / 0`。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

### 2.3 相邻与全量检查

在固定 `http://localhost:4317` 上串行运行 Batch 59、67–87 current gates，并执行：

```bash
npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

回归结果和执行日期写入
[`current-gate-regression.json`](current-gate-regression.json)。

## 3. 证据边界

| 类型 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前 clone 的 document schema、Director restore path 和 UI selection surfaces |
| `CLONE_DECISION` | undo/redo/cancel 保留当前 selection，并对失效目标做确定性 repair |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否保存或恢复 selection，以及 exact undo/redo policy |
| `UPSTREAM_INSPIRATION` | StoryAI/Open Canvas 只作为领域和验证方法参考 |

## 4. 结果

| Gate | Result |
|---|---|
| pure/source verifier | `PASS` |
| fresh-page Batch 87 | `SCRIPT_RECORDED_PASS` |
| current-gate Batch 59, 67–87 | `CURRENT_GATE_SERIAL_REGRESSION_RECORDED_PASS` |
| npm/docs full checks | `PASS` |
| diagnostics | `0 / 0 / 0` |
| screenshot artifact delta | `0` |
| source-exact Director claim | `NONE` |
