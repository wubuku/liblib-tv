# Batch 73: Director Async Result Authority

> 状态：`IN_PROGRESS / ASYNC_AUTHORITY_FOCUSED_PASS_PENDING`。
>
> 建档日期：2026-08-27。

## 1. 背景

Batch 67-72 已建立 Director 的 V1 portable document、owner/session/generation、
authored/runtime 分离、project-local history、pointer lifecycle 和
reference-aware delete。当前最危险的剩余缺口是 capture、视频导出和手机运镜的
完成结果仍可能直接越过 owner/session freshness，晚到结果也没有统一的
stale/duplicate disposition。

本批建立一个 clone-owned 的本地 async authority，并将视频导出的浏览器完成结果
接入该 authority。它借鉴 [`LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)
中的 envelope、attempt 和 freshness 规则，不把 Open Canvas、StoryAI 或当前
prototype 近似写成 LibTV source-exact 行为。

## 2. 本批决策

```text
accepted request
  -> captured owner/session/generation + source fingerprint
  -> attempt identity
  -> completion envelope
  -> current/stale/duplicate classification
  -> graph projection only after apply-current
```

- accepted operation 不依赖 React component 是否仍 mounted；
- 同一 operation 的新 attempt 会使旧 attempt 立即失去 current authority；
- owner、project、session、generation 或 source fingerprint 不匹配时零 graph mutation；
- 相同 terminal result/version 重复到达时 `duplicate-noop`；
- async completion 默认保留当前 UI selection，不由 authority 强行抢焦点；
- 浏览器生成的 Blob URL 只有 graph projection 接受后才转移给普通画布结果节点；
  stale、reject 或 projection 失败时由 producer 释放；
- phone take 的本地导入先复用同一 identity 规则，仍不接真实手机网络或远端 provider。

## 3. 证据边界

| 标记 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前 clone committed code 直接支持 |
| `DESIGN_DECISION` | 为 prototype 建立的可靠性合同 |
| `PROTOTYPE_BOUNDARY` | 不代表真实 LibTV/后端行为 |
| `SOURCE_UNKNOWN` | 仍需新的 authenticated LibTV evidence |

本批不做：

- 真实 provider、上传、轮询、云端 persistence 或计费；
- 普通 canvas 全部 delayed writer 的一次性迁移；
- Three.js/R3F 结构调整；
- LibTV authenticated Director 的 source-exact async 文案、状态或 API 结论；
- 通过截图重复识别已记录的画布 UI。

## 4. 交接入口

- [`PLAN.md`](PLAN.md)：切片、fixture、验收和停止条件；
- [`ASYNC_AUTHORITY_FIXTURE.md`](ASYNC_AUTHORITY_FIXTURE.md)：纯 authority corpus；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：实施、验证、失败修正和剩余风险；
- [`runtime-audit.json`](runtime-audit.json)：最终结构化结果；
- [`../../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md`](../LIBTV_ASYNC_RESULT_INGRESS_CONVERGENCE.md)：
  上位 async ingress 合同；
- [`../../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md`](../LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md)：
  Director owner/session/generation 合同；
- [`../../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md`](../LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md)：
  Director command/history/graph boundary。

## 5. 当前状态

代码与 verifier 仍在实施。完成条件是 pure authority corpus、导出完成结果的
freshness guard、Batch 67-72 回归、docs check、`npm run check` 和
commit/push 全部通过。
