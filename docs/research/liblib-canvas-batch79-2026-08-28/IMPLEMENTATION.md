# Batch 79 实施与验证记录：Director Whole-Project Duplicate

> 状态：`WHOLE_PROJECT_DUPLICATE_FOCUSED_PASS`。
>
> 日期：2026-08-28。
>
> 本记录描述 clone-owned 实施结果；不把它升级为 LibTV 原站 duplicate 的
> source-exact 事实。

## 1. 实施目标

普通 `duplicateCanvas` 过去只复制 React Flow graph，并为新的 Director node
创建默认 project。这样复制画布会丢失 Director authored scene、对象、机位、
时间轴和路径。本批将 duplicate 变为一个跨 graph、Director registry 与
persistence 边界的可验证 copy transaction。

## 2. 代码变更

### 2.1 Pure planner

`src/lib/directorWholeProjectDuplicate.ts` 新增：

- graph node、edge、parent 的两阶段 identity map；
- Director project、object、group、track、keyframe、motion path、anchor、
  resource 和 capture descriptor 的完整 ID allocation；
- camera active/look-at/follow、group member offset、track/path/anchor 和
  capture resource/camera 引用重写；
- `directorCapture`、`directorAnimationExport` graph provenance 重写；
- V1 strict decode/normalize、source owner/canvas/lifecycle 检查；
- local、blob/data/object URL 和 memory resource 的 zero-mutation reject；
- source document 缺失时只接受明确的 `MISSING` persistence disposition，并创建
  fresh target document；
- source/target 输入不变式和 target node map 一致性校验。

planner 先生成完整 plan。未知引用、非法 document、资源策略失败或 identity
冲突都会在 graph/registry mutation 前返回 `REJECTED`。

### 2.2 Registry and store coordinator

`src/lib/directorProjectRegistry.ts` 新增 `registerCopies()`：

- 对整个 registration batch 先验证 owner、project、generation、document identity
  和 registry 冲突；
- 全部通过后一次性登记 target records；
- target record 为 `CLOSED`、generation 1、无 active session；
- captures 只接受显式 sidecar，不由 duplicate 隐式搬运 capture bytes。

`src/store/directorStore.ts` 新增：

- `getDirectorProjectDuplicateSource()`：按 registry -> persistence 顺序读取 source；
- `createFreshDirectorProjectDocument()`：生成严格可恢复的 fresh document；
- `registerDirectorProjectCopies()`：登记 target records，初始化 target history/
  capture archive，并逐 owner写 persistence；
- persistence 失败时返回 `COMMITTED_SESSION_ONLY` 与逐 owner
  `SAVED/SESSION_ONLY` 状态，不伪造 durable success。

`src/store/canvasStore.ts` 的 `duplicateCanvas()`：

1. 找到 source canvas；
2. 为每个 `script-execution` node 收集 source owner/document；
3. 构造并验证 whole-project plan；
4. 登记 Director target copies；
5. 提交新 graph、激活 target、清空普通 selection、初始化空 graph history；
6. 返回 typed `LibTVCanvasDuplicateResult`。

原有 `CanvasTabDropdown` 忽略返回值仍可工作；新调用者可以读取显式
`COMMITTED`、`COMMITTED_SESSION_ONLY` 或 `REJECTED`。

## 3. 验证

### 3.1 Pure corpus

```bash
node --experimental-strip-types scripts/verify-liblib-batch79.mjs
```

通过多 Director root、graph/Director 两阶段映射、camera/group/path/keyframe/
capture/resource 引用重写、fresh document、non-portable resource reject、
rejected persistence source 和 source input isolation。

### 3.2 Browser corpus

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch79.py
```

通过：

- `canvas-2` source graph 复制到新 target；
- source/target node、edge、project、owner、persistence key 独立；
- authored object 改动复制到 target；
- target Director history、clipboard 和 active session 初始为空；
- target 修改不污染 source；
- 普通 selection 清空、target graph history 为空；
- console/page/request errors 均为 0；
- 本批不写截图。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

### 3.3 项目门禁

- `npm run typecheck`：通过；
- `npm run lint -- --no-cache`：0 error，保留仓库既有 9 条 warning；
- `git diff --check`：通过；
- `npm run check`：通过；
- `npm run docs:check`：通过；
- Director current gate：Batch 59、67-79 串行通过。

## 4. 证据与产品边界

Batch 79 证明的是当前 clone 的 whole-project duplicate contract。当前没有
source-exact LibTV authenticated evidence 可以确认：

- 原站 duplicate 是否复制 Director authored document；
- stable/local resource 如何 materialize；
- capture gallery、导出结果、history、session 是否复制；
- persistence 失败、部分成功和用户反馈如何呈现。

因此本批 duplicate policy 标记为 `CLONE_DECISION`。后续优先补 durable
tombstone/storage cleanup 和 strict import/export 的可恢复 workflow，再决定是否
接入真实资源加载。

## 5. Checkpoint

本批 closeout 记录 commit SHA、push 结果、`master == origin/master`、唯一
worktree 和干净状态；下一批从 Batch 80 计划开始。
