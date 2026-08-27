# Batch 67: Director Project Document V1

> 状态：`COMPLETE / PROJECT_CODEC_FOCUSED_PASS`。
>
> 建档日期：2026-08-27。
>
> 前置批次：[`liblib-canvas-batch66-2026-08-27`](../liblib-canvas-batch66-2026-08-27/README.md)。

## 目标

将 Director 当前单例 Zustand store 中可持久化的 authored state 提取为一个独立、
可版本化、可严格校验的 `DirectorProjectDocumentV1`。本批是后续 project/session
隔离、Director history、reference-aware delete、真实资源生命周期和多机位扩展
的可靠性底座。

本批不追求一次迁移现有全部 action，也不把 StoryAI JSON 直接兼容为 LibTV 格式。
实现必须保持 R3F runtime、普通 React Flow graph 和两个 submodule 的边界。

## 证据与边界

- Director 当前字段、action 和 sampled timeline 语义来自
  [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
  与 [`LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)。
- StoryAI 的 versioned project/schema 只是 `UPSTREAM_FACT` 和借鉴方法，不是
  LibTV source-exact 事实。
- 当前 clone 的 store shape 是 `CLONE_STATIC_FACT`；本批新增的 schema、字段白名单、
  unknown-field policy 和 error code 是 `CLONE_ENGINEERING_DECISION`。
- 没有新的 authenticated LibTV Director 证据；不新增 source UI、persistence 或
  import/export 行为的 source claim。

## 交接入口

- [`PLAN.md`](PLAN.md)：本批范围、切片顺序、验收标准和停止条件；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：截图零重复识别记录；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码、verifier、验证、风险和接力；
- [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  project/session/runtime/resource 分权；
- [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)：
  Director 当前及历史 verifier 分级；
- [`LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md)：
  后续 fixture 身份和隔离约束。

## 预期代码产物

建议新增纯模块：

```text
src/lib/directorProjectDocument.ts
```

职责：

1. 定义 `DirectorProjectDocumentV1` 及其子类型；
2. 创建默认 document 和当前 Director state snapshot adapter；
3. 对 unknown、malformed、future、duplicate、dangling、non-finite 输入做 strict
   decode；
4. normalize 后提供 deterministic encode/decode round-trip；
5. 对 document 做深隔离，避免调用方修改 store 或 history snapshot。

## 明确排除

以下值不能进入 V1 document：

```text
selection / focus / view mode / transform mode / panel state
currentTime / isPlaying / timeline zoom / selected track/keyframe/path
motionPathDraft / phone recorder runtime / export progress
File / Blob / object URL / Three.js Object3D / renderer / controls
sentNodeId graph projection cache / ordinary canvas graph history
```

`DirectorCapture.dataUrl` 是当前 clone 的临时媒体 bytes，不进入 portable document；
V1 只保留 capture descriptor，后续由 media/resource contract 处理稳定资源引用。

## 完成结论

Batch 67 已实现并验证：

- `DirectorProjectDocumentV1` 封闭 DTO、strict decode/normalize/encode；
- current Director state snapshot adapter；
- unknown/future/duplicate/dangling/non-finite zero-partial rejection；
- runtime、UI、capture bytes、Three.js refs 与普通 graph projection exclusion；
- deterministic round-trip、deep isolation 与 authored array order preservation。

本批只完成 portable document codec，不表示 owner registry、session restore、
authored/runtime split、Director history/delete 或 persistence 已完成。下一可靠性
切片应从 `route + canvasId + sourceNodeId` owner registry 和 session lifecycle 开始。
