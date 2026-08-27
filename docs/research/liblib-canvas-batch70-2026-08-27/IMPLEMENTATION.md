# Batch 70 实施与验证记录

> 状态：`COMPLETE / DIRECTOR_HISTORY_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> 代码范围：Director store、command kernel、workspace gesture adapters 和
> Batch 70 pure/browser verifier；普通 React Flow graph、FrameOS route、
> submodule 和源站共享项目未修改。

## 1. 实施目标

Batch 70 把 Batch 67-69 已建立的 Director V1 document、owner/session 和
authored/runtime baseline 接到一个 project-local command/history kernel。目标
不是一次包装 Director 的全部 85 个 action，而是先建立可验证的 reliability floor：

```text
semantic mutation
  -> current owner/document validation
  -> normalized fingerprint comparison
  -> one project history entry or zero entry
  -> exact document undo/redo
```

## 2. 代码变更

### 2.1 Typed command kernel

新增 [`src/lib/directorCommandKernel.ts`](../../../src/lib/directorCommandKernel.ts)：

- `DirectorCommandResult`：command identity、disposition、stable reason、
  projectChanged、historyEntries、selection/resource/graph effect slots；
- `DirectorHistoryState`：bounded `past/future` 和 active gesture；
- `DirectorHistoryEntry`：strict V1 document `before/after`；
- `DirectorGestureTransaction`：project/session generation、target、field scope
  和 baseline fingerprint；
- deterministic JSON document fingerprint、history cloning、push semantics。

`generation` 仍用于判断当前 gesture/session 是否新鲜，但不是 project-local
history 的永久身份；close/reopen 之后旧 entry 允许在同一个 `projectId` 中继续
undo/redo。

### 2.2 Director store

修改 [`src/store/directorStore.ts`](../../../src/store/directorStore.ts)：

- 以 `projectId` 为 key 的内存 history sidecar，open/focus/close 时恢复或保存；
- document snapshot 只来自 `authoredObjects` 与 portable timeline/group/capture
  descriptors，不包含 runtime sampled objects、selection、phone preview、
  Three.js refs 或 graph-return side effects；
- subscription 对没有 active gesture 的 semantic document change 自动创建一条
  history entry，并抑制 history restore 的递归 observation；
- `beginDirectorGesture`、`commitDirectorGesture`、`cancelDirectorGesture`、
  `undoDirector`、`redoDirector`；
- `updateObjectTransform` 对 target missing、non-finite 和 same-value 输入返回
  typed rejected/no-op result，保证零 mutation/零 history；
- undo/redo 验证 `projectId + current document fingerprint`，不再将 reopen 后
  递增的 session generation 错判为 history conflict。

### 2.3 UI gesture adapters

- [`DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx)：Director
  workspace 消费 Cmd/Ctrl+Z、Shift+Cmd/Ctrl+Z、Cmd/Ctrl+Y；Escape 优先取消
  active gesture；根节点暴露 history/command diagnostics。
- [`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)：
  object/group TransformControls 在 pointer begin/end 形成 gesture boundary。
- [`DirectorCurveEditor.tsx`](../../../src/components/director/DirectorCurveEditor.tsx)：
  speed-curve handle drag 在 pointer begin/end 形成 gesture boundary。

## 3. 不在本批范围

- object/group/camera/track/path/capture/resource 的 reference-aware delete；
- copy/paste、clipboard remap、last-camera policy 和 resource lease；
- capture/export async owner freshness；
- browser persistence、cloud sync、真实 mesh/panorama loading；
- LibTV authenticated Director 的 source-exact DOM/CSS/shortcut 文案；
- 将所有旧 action 机械改名为 typed command，或新增全局 command bus。

## 4. 验证结果

### 4.1 Pure/static

命令：

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON \
  --experimental-strip-types scripts/verify-liblib-batch70.mjs
```

结果：`PASS`。覆盖 typed kernel、strict before/after、bounded history、store
subscription、no-op/invalid/missing-target reason、gesture adapters 和普通
graph history 隔离。

### 4.2 Fresh-page Playwright

命令：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch70.py
```

结果：`PASS`，见 [`runtime-audit.json`](runtime-audit.json)。

覆盖：

| 场景 | 结果 |
|---|---|
| 一次 semantic object transform 一条 history | PASS |
| same-value no-op：`DIRECTOR_COMMAND_NO_CHANGE` | PASS |
| `NaN`：`DIRECTOR_INVALID_VALUE` | PASS |
| missing target：`DIRECTOR_TARGET_MISSING` | PASS |
| exact undo/redo round-trip | PASS |
| new commit truncates redo future | PASS |
| repeated gesture one entry | PASS |
| owner A/B history isolation | PASS |
| close/reopen generation continuity | PASS |
| ordinary canvas graph/history isolation | PASS |
| console/page/request errors | 0 |
| screenshot writes | 0 |

### 4.3 Project checks

本轮已通过：

```text
npm run typecheck
npm run lint
git diff --check
```

`npm run lint` 仍报告项目既有的 9 条 warning，没有新增 error。

## 5. 失败与修正记录

| 现象 | 分类 | 处理 |
|---|---|---|
| 新增纯 verifier 的组合正则假设 reason 顺序 | verifier defect | 拆成三个独立 source assertions |
| close 后直接调用 store close 再 open 不触发 React UI effect | verifier lifecycle defect | 改为点击真实 `[data-close-director]` 并等待 workspace detached |
| reopen 后 history 被旧 generation 阻断 | implementation defect | undo/redo 改为 projectId + document fingerprint 校验；generation 保留给 active session/gesture freshness |

## 6. 当前交接

Batch 70 完成了 `LIBTV-VR-024` 的 command/history/gesture focused slice。下一批
优先实现真实 pointer lifecycle 的完整 begin/update/commit/cancel 接入，然后进入
object/camera/group/track/path/capture/resource 的 reference-aware delete planner。
删除规划必须继续遵守 zero-partial、last-camera、reference repair、resource
reachability 和 command result 合同，不能把当前 history observer 当作删除安全性。
