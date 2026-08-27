# Batch 74 实施与验证记录

> 状态：`PERSISTENCE_FOCUSED_PASS`。
>
> 建档日期：2026-08-27；实施 checkpoint：`d68285b`。

Batch 74 完成了 clone-owned Director browser-local durable project persistence
切片。它只解决当前前端原型的可靠性边界，不把 localStorage、envelope 或
恢复 UI 推断为 LibTV 原站的 source-exact 行为。

## 1. 实施内容

### 1.1 Storage authority

- 新增 [`directorProjectPersistence.ts`](../../../src/lib/directorProjectPersistence.ts)；
- 以 `route + canvasId + sourceNodeId` 生成 owner-scoped storage key；
- 定义 versioned storage envelope，保存 project ID、owner、generation、
  savedAt、document fingerprint 和 canonical `DirectorProjectDocumentV1`；
- load 先做 envelope shape、schema、owner/project identity 和 document
  fingerprint 校验，再调用 strict V1 decoder；
- corrupt、future schema、invalid envelope/document、owner/project mismatch
  都是 zero-replacement reject；
- save request 使用 request ID、generation 和 fingerprint；旧 completion
  返回 `STALE_IGNORED`，不能覆盖新请求；
- storage 不可用或写入失败时返回 `SESSION_ONLY`，不破坏当前内存 session；
- 当前 data URL capture 没有 stable locator，因此被排除；只有 stable
  resource reference 才能进入 persisted document。

### 1.2 Registry/store integration

- `directorProjectRegistry.open` 可接收已校验的 persisted document；
- Director open、canonical mutation、switch、close/reopen 路径接入 persistence；
- 恢复后的 session generation 递增，runtime projection 从 time zero 重建；
- persistence status 记录在 authority snapshot 中，不进入 Director semantic
  history，也不写入普通 `canvasStore` graph/history；
- 暴露 `window.__director_project_persistence_snapshot()` 供 focused verifier
  读取 storage status、失败原因、generation 和 fingerprint。

## 2. 验证范围与结果

### 2.1 Pure verifier

`node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON
--experimental-strip-types scripts/verify-liblib-batch74.mjs` 通过，覆盖：

- missing storage；
- strict envelope round-trip；
- capture byte exclusion；
- stale save completion；
- corrupt payload、future schema、owner/project mismatch；
- write failure 与 storage unavailable；
- input isolation 和 canonical fingerprint。

### 2.2 Fresh-page Playwright verifier

`python3 scripts/verify-liblib-batch74.py` 通过，使用新 BrowserContext 验证：

- authored edit -> reload 恢复同一 project；
- reload 后 session generation 递增，playhead/playing 等 runtime 不恢复；
- A/B owner 使用独立 storage key，普通画布 graph/history 不变；
- corrupt payload 被拒绝且原始 payload 保留；
- serialized envelope 不含 selection、playhead、panel、phone、capture bytes、
  Blob/File/Object URL 或 Three.js runtime 字段；
- 模拟 quota 时当前内存编辑仍可见并进入 `SESSION_ONLY`；
- console、page、request errors 均为零；
- 本批不生成截图，也未重复截图识别。

结构化结果保存在 [`runtime-audit.json`](runtime-audit.json)。

## 3. 证据边界

本批已证明的是当前 clone 的 Director persistence contract：

- `PERSISTENCE_FOCUSED_PASS` 只表示上述 clone-owned fixture 和 runtime gate
  通过；
- 不证明 LibTV 原站使用 localStorage、同一 storage schema、同一恢复 UI 或
  同一 project API；
- 不包含普通画布 graph/document persistence、remote/cloud storage、durable
  history、真实资源 materialization、inactive-owner reconciliation、
  copy/paste identity remap 或 source-exact Director UI。

## 4. 文档与工作区

- 已同步 Director contract、current verifier manifest、fixture catalog、
  verification ledger、traceability、coverage matrix、Big Picture、Agent
  Task Map、HARNESS、decision register、research hubs 和 CHANGELOG；
- Batch 67-74 focused gates 全部通过；
- `npm run docs:check` 通过：571 个 Markdown 文件、3387 个本地目标；
- `npm run check` 通过：lint 保留既有 9 条 warning，typecheck 和 Next
  production build 成功；
- `git diff --check` 通过；
- 当前主分支仅保留一个 `master` worktree；
- 最终全量回归与 commit/push 结果以本文件的 closeout 记录和 git history 为准。
