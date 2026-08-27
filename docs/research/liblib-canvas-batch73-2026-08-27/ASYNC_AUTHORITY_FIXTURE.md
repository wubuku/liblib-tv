# Batch 73 Fixture 与 Verifier 设计

## 1. 目的

本文件是 Batch 73 的低成本、可重复 async authority 证据。它只验证纯
operation/result/resource 规则，不通过截图推断 LibTV，也不调用 provider、上传或
共享源站项目。

## 2. 身份模型

```text
owner:
  route=libtv
  canvasId=C1
  sourceNodeId=S1
  projectId=P1
  sessionId=SESSION-1
  generation=7

operation:
  operationId=O_EXPORT
  kind=video-export
  attemptId=A1
  sourceFingerprint=S1@V1

result:
  resultId=X1
  resultVersionId=X1v1
```

任何 envelope 都必须同时带有 operation、attempt、owner/session/generation、
source fingerprint 和 result/version identity。payload 不是 authority identity，
并且本批不接受任意 object spread 作为 graph patch。

## 3. Corpus

| Case | Setup | Completion | Expected |
|---|---|---|---|
| current apply | O_EXPORT/A1 current | X1v1 succeeded | `apply-current` |
| progress | O_EXPORT/A1 current | progress | `apply-current`，仍可接 terminal |
| owner stale | current owner改 canvas/session/generation | X1v1 | `reject-stale` |
| source drift | descriptor=S1@V1，current=S1@V2 | X1v1 | `reject-stale` |
| retry race | A1 then new A2 | A2 then A1 | A2 current，A1 stale |
| duplicate terminal | X1v1 delivered twice | second X1v1 | `duplicate-noop` |
| invalid envelope | missing/empty identity | any | `reject-invalid`，registry不变 |
| terminal conflict | A1 already terminal | different X1v2 | `reject-stale` |
| resource transfer | U1 owned by A1 | apply then transfer | one transfer |
| stale resource | U1 owned by A1 | stale/reject | one release |
| release duplicate | U1 already released | release again | duplicate-noop |
| transfer after release | U1 already released | transfer | reject-invalid |

## 4. Browser assertions

视频导出入口使用 deterministic local request：

- 导出 request 捕获 Director owner/session/generation 和 source document fingerprint；
- 完成回调构造 envelope；
- current completion 才允许调用 `createDirectorAnimationExport`；
- stale/duplicate completion 不新增普通 canvas node/edge/history；
- accepted projection 后 video URL ownership 被视为 transferred；
- projection 失败或 stale 时 URL 被 revoke；
- 当前用户在导出期间改变 selection 时，不因 completion 被强制切回 source/result，
  除非已有明确的 clone-owned contextual selection 规则。

capture 和 phone 的纯 adapter 只验证 identity contract；本批不重新识别已留档的
Director 画布截图。

## 5. 证据等级

| 结果 | 含义 |
|---|---|
| `PURE_CONTRACT` | Node corpus 直接证明纯 authority |
| `RUNTIME_INTEGRATION` | fresh-page 证明 clone 入口实际经过 authority |
| `CLONE_DECISION` | 本项目可靠性选择，不是源站事实 |
| `SOURCE_UNKNOWN` | 需要新的 LibTV authenticated evidence |
