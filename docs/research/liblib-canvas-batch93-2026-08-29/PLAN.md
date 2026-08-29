# Batch 93 计划：Director 最终跨批回归与治理收口

> 状态：`PLANNED`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`ab5cf28`。
>
> 本批是当前用户指定的最后一批。Batch 93 完成后停止，不自动启动
> Batch 94 或新的循环迭代。

## 1. 目标

Batch 93 不新增产品功能，目标是把 Batch 67-92 已形成的 clone-owned
Director reliability slices 合并成一份可重复执行、可发现、可审计的当前
回归结果，并确认桌面/移动端的 Director shell 与 R3F 工作区没有跨批回归。

本批不重新解释 LibTV 原站，也不把 StoryAI、Open Canvas 或 clone-only
实现升级为 LibTV source-exact 事实。

## 2. 批次范围与排序

| 优先级 | Slice | 交付 | 停止条件 |
|---|---|---|---|
| P0 | Batch 92 closeout compatibility | Batch 92 pure/fresh-page 与 Batch 82 compatibility verifier | 两个脚本均通过，诊断为 0/0/0 |
| P0 | current Director gate serial run | Batch 59、67-92 按固定顺序串行执行 | 所有 gate 通过并写入结构化 regression audit |
| P0 | desktop/mobile Director regression | fresh page 下 `1440x900` 与 `390x844` 检查 workspace、WebGL、tree、Inspector、Timeline、overflow 和 close/reopen | 两端关键 surface 可见、无横向溢出、无浏览器错误 |
| P1 | cross-batch ordinary canvas regression | 运行当前已维护的普通画布/导航/overlay 低成本回归 | 普通 graph、image overlay、canvas navigation 不受 Director/resource 修改影响 |
| P1 | governance closeout | 更新 manifest、ledger、Harness、fixture、traceability、coverage、Research Hub、Big Picture 与 Batch 93 台账 | 能从 docs Hub、Research Hub、Agent Task Map 和 verifier manifest 找到本批结果 |
| P1 | full repository gate | `npm run check`、`npm run docs:check`、`verify-docs.py`、`git diff --check` | 全部通过，保留既有 lint warning 但不新增 error |

## 3. 验证策略

### 3.1 固定服务

使用仓库固定端口：

```text
http://localhost:4317
```

不得切换到 `3000`、`3001` 或临时端口。涉及浏览器本地状态和 WebGL
生命周期的脚本必须串行执行。

### 3.2 Current Director gates

按 manifest 的 current gate 顺序运行：

```text
Batch 59
Batch 67
Batch 68
Batch 69
Batch 70
Batch 71
Batch 72
Batch 73
Batch 74
Batch 75
Batch 76
Batch 77
Batch 78
Batch 79
Batch 80
Batch 81
Batch 82
Batch 83
Batch 84
Batch 85
Batch 86
Batch 87
Batch 88
Batch 89
Batch 90
Batch 91
Batch 92
```

Batch 67 的 pure verifier 使用 Node 24；其余有 browser verifier 的批次使用
`LIBLIB_BASE_URL=http://localhost:4317`。每个脚本的历史边界仍以各自台账为准。

### 3.3 桌面/移动端回归

新建 Batch 93 专项脚本，使用 fresh BrowserContext，不写截图，记录：

- desktop `1440x900`：Director workspace、R3F canvas nonblank、object tree、
  Inspector、Timeline、resource library/status surface、close/reopen；
- mobile `390x844`：Director workspace、mobile drawer/panel、R3F canvas、
  object tree/Inspector/Timeline 可发现性和 `scrollWidth <= clientWidth`；
- 两端都收集 console error、page error、request failure；
- 只验证当前 clone-owned surface，不声称 LibTV source DOM/CSS parity。

### 3.4 普通画布跨批回归

至少串行运行 Batch 57、60、61、63、64、65 与 Batch 77，确认：

- graph connection reject/accept 合同仍成立；
- image 双浮层 owner/selection/pointer 边界未被 Director 改动破坏；
- React Flow change routing、actual-host placement、asset resize anchor、
  responsive viewport bootstrap 和 source-aligned navigation 仍通过。

## 4. 预定交付文件

- `README.md`
- `PLAN.md`
- `IMPLEMENTATION.md`
- `runtime-audit.json`
- `current-gate-regression.json`
- `scripts/verify-liblib-batch93.py`

并更新：

- `docs/research/README.md`
- `docs/index.md`
- `docs/HARNESS.md`
- `docs/research/VERIFICATION_LEDGER.md`
- `docs/research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md`
- `docs/research/LIBTV_FIXTURE_CATALOG.md`
- `docs/research/TRACEABILITY_MATRIX.md`
- `docs/research/components/COVERAGE_MATRIX.md`
- `docs/AGENT_TASK_MAP.md`
- `docs/BIG_PICTURE.md`

## 5. 证据边界

| 结果 | 解释 |
|---|---|
| current gate pass | 当前 clone-owned contract 在本次 HEAD 上通过 |
| desktop/mobile pass | 当前 clone 两个 viewport 的结构、WebGL、overflow 和 diagnostics 通过 |
| ordinary canvas pass | Director 变更没有破坏已选普通画布 slices |
| source parity | 仍为 `SOURCE_UNKNOWN`，本批不产生新 source-exact 结论 |

## 6. 完成与停止条件

Batch 93 只有在以下事项全部完成后才可标记完成：

1. 专项 desktop/mobile verifier 通过；
2. Batch 92、Batch 82 compatibility、Batch 59/67-92 current gates 通过；
3. 普通画布跨批回归通过；
4. 全量检查和文档检查通过；
5. 结果、治理索引和结构化审计已落档；
6. commit/push 完成；
7. `master == origin/master`、工作区干净、无其他 worktree。

完成后立即停止并等待用户下一步指示。

