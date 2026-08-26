# Batch 57 实施记录：普通画布连接事务

> **Purpose**: 记录 Batch 57 的实现、验证、失败修正和 checkpoint，供后续 agents 接力。
> **Status**: `RECORDED_PASS`（2026-08-27）；pure validator、route boundary、
> store commit boundary 和 focused browser verification 已完成。
> **Source boundary**: 本文只记录已有 source static evidence 投影到 clone 的结构连接行为；不把未观察到的 invalid UI feedback 写成源站事实。

## 1. 实施范围

计划范围见 [`PLAN.md`](PLAN.md)。以下表格记录当前批次的完成状态：

| Slice | 内容 | 状态 |
|---|---|---|
| A | pure normalization、endpoint/pair/self/cycle guard | 已完成 |
| B | React Flow validator boundary、store commit boundary | 已完成 |
| V | focused Playwright、跨批回归和质量检查 | 已完成 |

## 2. 变更记录

| 时间 | 变更 | 结果 |
|---|---|---|
| 2026-08-27 | 修正 source evidence 中静态审计文件链接 | 已完成 |
| 2026-08-27 | 建立 Batch 57 实施与截图分析记录骨架 | 已完成 |
| 2026-08-27 | 新增 `libtvGraphConnection.ts`，接入 route `isValidConnection`/`onConnect` 和 store 二次校验 | 已完成 |
| 2026-08-27 | 运行 Batch 57 focused Playwright，覆盖真实 Handle drag、target-start、reject reasons、undo/redo、desktop/mobile overflow 与诊断错误 | 通过 |

## 3. 验证记录

已运行 `npm run typecheck`、`npm run lint`；均退出 0。lint 保留仓库已有的
9 个 warning，无 error。Batch 57 focused Playwright 已通过，并写入
`runtime-audit.json`；不使用截图替代 DOM/state 验证。选定的跨批回归、
`npm run check`、`python3 scripts/verify-docs.py` 和 `git diff --check` 均已通过。

### Closeout command record

```text
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch8.py
python3 scripts/verify-liblib-batch20.py
python3 scripts/verify-liblib-batch29.py
python3 scripts/verify-liblib-batch52.py
python3 scripts/verify-liblib-batch53.py
python3 scripts/verify-liblib-batch54.py
python3 scripts/verify-liblib-batch56.py
python3 scripts/verify-liblib-batch57.py
npm run check
python3 scripts/verify-docs.py
git diff --check
```

结果：所有选定 LibTV 回归、lint/typecheck/build、文档链接检查和 whitespace
检查通过。`npm run check` 保留 9 个既有 lint warning，无 error。

### Focused verifier result

```text
Batch 57 Playwright verification passed:
real source/target Handle drag, target-start normalization, accepted one-step
history, undo/redo, structural rejection reasons, zero-mutation rejected store
submit, desktop/mobile overflow and console diagnostics.
```

运行产物：

- [`scripts/verify-liblib-batch57.py`](../../../scripts/verify-liblib-batch57.py)
- [`runtime-audit.json`](runtime-audit.json)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)

## 4. Checkpoints

| Commit | 内容 | 状态 |
|---|---|---|
| `fd52b9f` | Batch 57 计划、证据和接力文档 | 已 push |
| `cbb47fe` | 连接纯校验器、route/store 实施、focused verifier 和 closeout 文档 | 已 push |

## 5. 未决与边界

- `REFERENCE` source、domain compatibility、import/batch/sync、持久化和源站 invalid feedback 仍不在本批实现范围。
- `docs/design-references/` 中的截图是验证证据，不应通过 `.gitignore` 删除或忽略。

## 6. Closeout decision

本批可标记为 `RECORDED_PASS`，因为 focused verifier 已对本地 fixture 的
结构连接事务闭环；不能标记为完整 LibTV connection parity。后续若继续处理
`LIBTV-PAR-008`，优先进入 document/snapshot 或 subgraph-copy 的独立 batch，
并继续保留 Reference/domain/source feedback 的阻塞说明。
