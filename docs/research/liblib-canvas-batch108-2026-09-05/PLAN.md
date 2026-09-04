# Batch 108 Plan：普通画布对齐系列跨批回归（Batch 97-107）

> 状态：`IN_PROGRESS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 107（`batch/107-skill-headline-rotation`）。

## 1. 范围

照 Batch 93 的 Director 跨批回归模式，为 Batch 97-107 的普通画布对齐系列
执行一次**全量 verifier 串行回归**：

- 串行运行 `scripts/verify-liblib-batch*.py` 全部现有队列（含 Director 批），
  逐项记录 exit/耗时到 `runtime-audit.json`；
- 失败项逐个判定：断言漂移（按 replacement 协议处理）或真实回归（修复）；
- `npm run check`、`npm run docs:check` 收口。

## 2. 边界

- 本批不新增功能、不改 UI；只验证与记录；
- 源站采样不在范围（共享项目只读纪律维持）；
- 预期漂移点：本系列已迁移的 batch5/11/12/13/14/15/17/62 aria/文案断言。

## 3. 完成定义

1. 串行队列全部 exit=0（或漂移项按协议处理后复跑通过）。
2. `runtime-audit.json` 记录每项结果与耗时。
3. 治理文档更新；特性分支 commit/push。
