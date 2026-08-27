# Batch 73 实施与验证记录

> 状态：`COMPLETE / ASYNC_AUTHORITY_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> implementation checkpoint：`ec81801`。

## 1. 实施目标

Batch 72 之后，Director 的 project/session/delete authority 已经可以保护同步
语义操作，但 capture、视频导出和手机运镜的完成结果仍缺少共同的 operation、
attempt、owner/session/generation、source fingerprint 和 duplicate disposition。

本批只完成 clone-owned 的本地异步身份与完成结果收敛，不接 provider、网络任务、
上传、远端 persistence 或新的源站截图识别。

## 2. 代码变更

### 2.1 Pure async authority

新增 [`directorAsyncAuthority.ts`](../../../src/lib/directorAsyncAuthority.ts)：

- typed operation descriptor 冻结 `projectId`、`sessionId`、`generation`、
  `canvasId`、`sourceNodeId`、source fingerprint 和 request fingerprint；
- result envelope 分开 operation、attempt、result 和 result version；
- `begin` 支持同一 operation 的 retry，新 attempt 会使旧 attempt 失去 current
  authority；
- `reconcile` 区分 `apply-current`、`duplicate-noop`、`reject-stale` 和
  `reject-invalid`；
- owner/session/generation、source fingerprint、kind、attempt 和 terminal state
  都在结果进入 projection 前检查；
- resource ledger 只允许 producer resource transfer 或 release 一次；
- authority snapshot 可被 fresh-page verifier 读取，但不进入 portable Director
  project document。

### 2.2 Director integration

- [`DirectorViewport.tsx`](../../../src/components/director/DirectorViewport.tsx)
  的 capture request 在接受时冻结 owner/source fingerprint，完成时先 reconcile，
  stale/invalid result 不进入 capture archive；
- [`DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx) 的 video
  export request/result 携带 authority descriptor，只有 current completion 才能
  调用 `createDirectorAnimationExport`；
- 导出 Blob URL 在 graph node 接受后才 transfer；stale、reject 或 graph commit
  failure 只 release/revoke producer-owned URL；
- [`directorStore.ts`](../../../src/store/directorStore.ts) 的 phone take import
  先经过相同的 owner/source/operation result gate，再生成 camera/track；
- 浏览器诊断暴露
  `window.__director_async_authority_snapshot()`，仅供 verifier/diagnostics 使用。

## 3. 验证结果

### 3.1 Pure corpus

运行：

```bash
node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON \
  --experimental-strip-types scripts/verify-liblib-batch73.mjs
```

结果：`PASS`。覆盖：

1. current progress 与 terminal apply；
2. owner/session/generation stale；
3. source fingerprint drift；
4. retry attempt supersession；
5. duplicate terminal delivery；
6. terminal conflict；
7. invalid descriptor/envelope；
8. resource transfer exactly once；
9. resource release exactly once。

### 3.2 Fresh-page corpus

运行：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch73.py
```

结果：`PASS`。

| 场景 | 结果 |
|---|---|
| Director capture | capture archive 增加 1；普通 canvas node/edge/history 不变；operation 为 `capture/succeeded` |
| Director animation export | 普通 canvas 增加 1 node + 1 edge；`video-export` operation 为 `succeeded`；resource ledger 有 1 条 |
| diagnostics | console/page/request errors 为 0 |
| screenshots | 0；本批没有重复截图识别成本 |

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

## 4. 跨批回归与质量门禁

Batch 73 实施期间已通过：

- Batch 73 pure verifier；
- Batch 73 fresh-page verifier；
- `npm run typecheck`；
- `npm run lint -- --no-cache`，0 error，保留既有 lint warning；
- `git diff --check`。

最终收口结果：

- Batch 67-73 focused regression：`PASS`；
- `npm run docs:check`：`PASS`；
- `npm run check`：`PASS`；
- `git diff --check`：`PASS`；
- worktree：唯一 `master` worktree，提交后与 `origin/master` 同步。

完整命令、HEAD、运行环境和结构化结果见
[`LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`](../LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md)
和 [`VERIFICATION_LEDGER.md`](../VERIFICATION_LEDGER.md)。

## 5. 证据边界与失败修正

- 这是 clone-owned async authority，不是 LibTV source-exact API 或状态文案；
- Open Canvas 只提供 operation/run/patch 分层与 stale 反例的研究启发；
- StoryAI 只提供 scoped project/history 的借鉴背景；
- 当前普通 canvas delayed writers 仍没有统一 operation ingress；
- source media version、remote run/cancel/poll、superseded result UI、durable
  result envelope 和真实 resource reachability 仍未完成；
- capture 的 data URL 不需要 Blob lease；视频 export 的 object URL 才进入本批
  resource ledger。

## 6. Git 与 worktree

- 计划 checkpoint：`14304a9`，已推送；
- 代码 checkpoint：`ec81801`，已推送；
- 文档收口 checkpoint：见本批最终提交；
- 仅保留主 `master` worktree，不创建其他 worktree。
