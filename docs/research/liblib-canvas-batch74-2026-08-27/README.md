# Batch 74: Director Durable Project Persistence

> 状态：`PLANNED / PERSISTENCE_AUTHORITY_PENDING`。
>
> 建档日期：2026-08-27。

## 1. 背景

Batch 67-73 已经建立 Director 的 V1 portable document、strict codec、
owner/session/generation、authored/runtime 分离、project-local
command/history/delete，以及 capture/export/phone 的 async result authority。
当前最高价值的可靠性缺口是：刷新页面后 Director project 仍没有 clone-owned
durable restore，registry 仍只存在于当前 JavaScript session。

本批只补齐浏览器本地的版本化 project persistence。它不把 StoryAI、
Open Canvas 或未经认证的 LibTV 行为写成 source fact，也不引入后端、云同步、
真实 provider 或新的视觉取证。

## 2. 本批决策

```text
active Director state
  -> canonical V1 document snapshot
  -> versioned storage envelope
  -> strict decode/normalize
  -> owner/project/generation guard
  -> in-memory registry restore
  -> authored/runtime projection
```

- storage adapter 独立于 `directorStore`，不把 `localStorage` 调用散落到组件；
- key 按 route/canvas/source owner 隔离，envelope 同时保留 project ID；
- load 只接受当前 schema；corrupt、future schema、owner/project mismatch
  均为显式 reject 且不覆盖已有有效值；
- save completion 只更新与 request 相同的 project/generation/fingerprint；
- storage 不可用或写入失败时，当前内存 session 继续可用，并暴露
  `SESSION_ONLY`/失败原因；
- 只持久化 authored document、stable resource reference 和 capture descriptor；
  capture 的 data URL、Blob/File/Object URL、Three.js refs、selection、
  playhead、panel、phone live state、history 不进入 envelope；
- 没有 stable locator 的 capture 不伪造为可恢复资源；
- 本批不实现 cloud sync、remote persistence、conflict merge、migration
  beyond V1 或普通画布 graph persistence。

## 3. 证据边界

| 标记 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前 clone committed code 直接支持 |
| `DESIGN_DECISION` | 为 prototype 可靠性建立的合同 |
| `PROTOTYPE_BOUNDARY` | 不代表真实 LibTV/后端行为 |
| `SOURCE_UNKNOWN` | 仍需 authenticated LibTV evidence |

已有上位合同：

- [`LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)
- [`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)
- [`LIBTV_FIXTURE_CATALOG.md`](../LIBTV_FIXTURE_CATALOG.md)
- [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)

## 4. 交接入口

- [`PLAN.md`](PLAN.md)：实施切片、fixture、验证和停止条件；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：完成后的实施与验证记录；
- [`runtime-audit.json`](runtime-audit.json)：结构化结果；
- [`../../BIG_PICTURE.md`](../../BIG_PICTURE.md)：跨项目可靠性地图；
- [`../../HARNESS.md`](../../HARNESS.md)：验证入口。

## 5. 当前状态

Batch 74 已完成研究与计划落档，代码实施尚未开始。下一步是先提交本计划
checkpoint，再实现独立 persistence adapter、store/registry 接入和 pure +
fresh-page verifier。
