# Batch 80 实施与验证记录

> 状态：`DURABLE_TOMBSTONE_FOCUSED_PASS`。
>
> 建档日期：2026-08-28。

## 1. 当前实施

### 1.1 Persistence authority

`src/lib/directorProjectPersistence.ts` 已增加：

- strict `DirectorProjectStorageTombstoneEnvelopeV1`；
- 合法 tombstone 的 decode/load；
- `tombstone()` typed API；
- tombstone 幂等与 project/generation guard；
- save 发现 tombstone 时返回 `STALE_IGNORED / PROJECT_TOMBSTONED`；
- storage unavailable/write failure 不伪造 durable success。

### 1.2 Registry/store lifecycle

`src/lib/directorProjectRegistry.ts` 增加 tombstoned record 的 transient memory
清理入口。`src/store/directorStore.ts` 已把 durable tombstone 接入 owner
reconciliation 和 active cleanup：

- durable 成功才删除 project history/capture archive；
- tombstoned registry record 的 memory captures 清零；
- local model descriptor 按 live/session-only 引用集合保留或释放；
- storage 失败时保留 session-only record 和资源；
- `REJECTED` persistence result 显式映射为上层 `SESSION_ONLY`。

## 2. 已通过

```bash
node --experimental-strip-types scripts/verify-liblib-batch80.mjs
npm run typecheck
npm run lint -- --no-cache
```

Pure corpus 已覆盖：

- strict tombstone envelope round-trip；
- durable load block；
- idempotent tombstone；
- save cannot resurrect；
- malformed marker rejection；
- stale generation；
- write failure continuity；
- storage unavailable。

Lint 保留仓库既有 9 条 warning，0 error。

## 3. Closeout 验证

```bash
python3 scripts/verify-liblib-batch80.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch59.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch67.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch68.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch69.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch70.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch71.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch72.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch73.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch74.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch75.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch76.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch78.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch79.py
```

The pure and browser verifiers passed on a fresh `localhost:4317` run. The
serial current gate was recorded for Batch 59 and Batch 67-80. `npm run check`,
`npm run docs:check` and `git diff --check` were required closeout gates.

## 4. 证据边界

本批没有新增 LibTV 原站 source-exact 结论。durable tombstone、browser-local
storage、capture archive cleanup 和 local resource release 都是当前 clone 的
可靠性决策；后端持久化、账户资产和真实资源 materialization 仍未实现。

## 4. Checkpoint

Batch 80 closeout is committed and pushed after the gates above. The final SHA,
`master`/`origin/master` equality, clean worktree and single-main-worktree
state are recorded in `current-gate-regression.json`.
