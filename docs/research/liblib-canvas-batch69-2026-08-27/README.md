# Batch 69: Director Authored And Runtime Projection Split

> 状态：`COMPLETE / AUTHORED_RUNTIME_FOCUSED_PASS`。
>
> 建档日期：2026-08-27。
>
> 前置批次：[`liblib-canvas-batch68-2026-08-27`](../liblib-canvas-batch68-2026-08-27/README.md)。

## 目标

把 Director 当前混合的 `objects` 状态拆成两层：

- `authoredObjects`：可进入 `DirectorProjectDocumentV1` 的作者基线；
- `objects`：由作者基线、timeline、motion path 和当前 playhead 派生的 R3F
  runtime projection。

本批解决 Batch 66-68 已确认的 P0 风险：seek/playback 后关闭或切换项目时，
不得把 sampled 姿态误保存为 authored project。

## 证据与决策

- 当前混写事实来自
  [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
  和 Batch 66 static audit。
- Batch 67 的 codec 与 Batch 68 的 owner/session registry 保持不变。
- StoryAI/Open Canvas 只提供状态分层和 runtime projection 的工程启发，不是
  LibTV source-exact 证据。
- 不新增截图识别，不重新推导 LibTV Director 的视觉行为。

## 本批范围

1. 新增 `authoredObjects` store authority，保留 `objects` 作为兼容的 runtime
   projection 读取入口。
2. snapshot/close/switch 只从 `authoredObjects` 构造 V1 document。
3. seek、播放、keyframe selection、path editing 和 speed curve 更新只重新派生
   `objects`，不修改 `authoredObjects`。
4. Inspector/group/object/camera 等 authoring mutation 写入 authored layer；
   auto-keyframe 场景同步更新当前语义 keyframe。
5. 手机 live pose/recording 继续是 runtime-only；imported take 是明确的
   authored camera + timeline command。
6. 增加 pure/browser stability verifier，证明 seek/playback 后 document fingerprint
   不变，并覆盖跨 owner restore。

## 交接入口

- [`PLAN.md`](PLAN.md)：范围、状态模型、mutation policy 和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码切片、验证命令、运行结果和已知边界；
- [`runtime-audit.json`](runtime-audit.json)：Batch 69 最近一次结构化 verifier 结果；
- [`../../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  `LIBTV-VR-024` 当前 gate。

## 明确不解决

```text
Director command result / undo-redo / gesture transaction
reference-aware object/camera/group delete
async capture/export destination freshness
browser persistence / cloud sync
真实 mesh / panorama / resource lease
LibTV source-exact Director DOM/CSS
```

## 验收结论

Batch 69 已达到 focused pass：

- runtime `objects` 与 `authoredObjects` 的职责可由 DOM/store diagnostics 发现；
- 非零 playhead seek、loop playback 和 path sampling 后，encoded authored document
  fingerprint 不变；
- authored transform/camera/group/pose mutation 可恢复，且 current keyframe 语义
  不被旧 sampled 值覆盖；
- close/switch/reopen 只恢复 authored document，再在 time-zero 派生 runtime；
- 普通 graph/history、owner registry、capture sidecar 和手机 runtime 边界不回归；
- Batch 67、Batch 68、Batch 69、Batch 59、docs check、`npm run check` 通过。

本批仍不宣称 Director project authority 全部完成；command/history、reference-aware
delete、async freshness、durable persistence、真实资源和 LibTV source-exact Director
UI 仍是独立后续合同。
