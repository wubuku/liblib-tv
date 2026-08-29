# Batch 83 实施与验证记录

> 状态：`RECORDED_PASS`。
>
> 实施日期：2026-08-29。
>
> 代码 checkpoint：`6c1d4c1`。

## 1. 实施目标

Batch 70 以后 Director store 已经会产生 typed
`DirectorCommandResult`，但 `DirectorDesk` 主要只暴露 `data-*` 诊断属性；
一般的 rejected/conflict/stale/no-op 结果没有稳定的用户可见 primary
surface。本批补齐这个最小闭环，同时保持普通 LibTV route、FrameOS 和
Director project/history 的边界不变。

## 2. 代码变更

### 2.1 Pure feedback adapter

新增 [`src/lib/directorCommandFeedback.ts`](../../../src/lib/directorCommandFeedback.ts)：

- 以 `disposition` 和稳定 `reason` 为分支身份；
- 将 reason 映射到 clone-owned 中文 display copy；
- `COMMITTED` 隐藏通用 feedback；
- `NOOP` 只显示有恢复价值的原因；
- `REJECTED`、`CONFLICT`、`STALE`、`UNKNOWN` 分别映射 error/warning tone；
- 未知/缺失 reason 使用有界 fallback，不猜成功。

### 2.2 Director foreground surface

[`DirectorDesk.tsx`](../../../src/components/director/DirectorDesk.tsx) 在固定
header 中加入紧凑状态区：

- `data-director-command-feedback`；
- `data-director-command-feedback-disposition/reason`；
- `role=status`、`aria-live=polite`、`aria-atomic=true`；
- 固定最大宽度和 truncate，不推动右侧导出/关闭控件；
- committed 的高频 TransformControls、slider、input mutation 不产生通用
  成功噪音；
- 项目导入/导出已有的局部 feedback 继续独立存在。

## 3. 跨批 verifier fixture drift 修正

首次运行 current gate 时，Batch 80 使用的 shared local model fixture 是
`batch80-shared.glb`。Batch 82 已将当前 clone 的本地模型入口明确限制为
`.obj/.fbx`，所以 Batch 80 等待“共享资源仍保留”时永远无法成立。

本批仅将该 verifier fixture 改为最小合法
`batch80-shared.obj`，没有改变 Batch 80 的 tombstone、引用计数、cleanup、
reload 或 graph/history 断言。这是 current gate 数据兼容修正，不是产品策略
改变。

## 4. 验证结果

### 4.1 Pure gate

```bash
node --experimental-strip-types scripts/verify-liblib-batch83.mjs
```

通过：committed hidden、rejected/stale/conflict mapping、no-op recovery mapping
和 bounded unknown fallback。

### 4.2 Browser gate

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch83.py
```

通过：

| Slice | 结果 |
|---|---|
| visible/accessibility status surface | `PASS` |
| rejected result visible | `PASS` |
| committed generic feedback hidden | `PASS` |
| no-op visible with zero new history | `PASS` |
| mobile feedback stays inside fixed header | `PASS` |
| console/page/request diagnostics | `0 / 0 / 0` |

### 4.3 Current Director gate regression

固定 `localhost:4317` dev server 上，Batch 59、67–79 已通过；Batch 80 首次
运行发现上述 `.glb` fixture drift，修正后 Batch 80、81、82、83 均通过。纯
Batch 67–83 gate 也全部通过。所有最终专项 browser audit 的 console/page/
request errors 均为零；脚本不写截图。

最终串行回归记录在
[`current-gate-regression.json`](current-gate-regression.json)，并明确记录：

- 固定端口为 `4317`；
- Batch 80 只更换不兼容的 `.glb` fixture 为最小合法 `.obj`，不改变语义；
- 历史 runtime audit 没有被重写；
- 结果证明 clone-owned Director reliability，不提升为 LibTV source parity。

### 4.4 Project gates

本批收口实际结果：

| Gate | Result |
|---|---|
| `npm run check` | `PASS`；lint 9 条既有 warning，typecheck/build 通过 |
| `npm run docs:check` | `PASS`；603 Markdown files、3604 local targets |
| `python3 scripts/verify-docs.py` | `PASS`；603 Markdown files、3604 local targets |
| `git diff --check` | `PASS` |

### 4.5 Closeout checkpoint

代码 checkpoint 为 `6c1d4c1`；文档 closeout checkpoint 为 `8dd985e`。完成后
只保留 `master` 主 worktree，并确认 `master` 与 `origin/master` 同步、工作区
干净、`http://localhost:4317/` 返回 HTTP 200。

## 5. 证据边界

| 类型 | 本批结论 |
|---|---|
| `CLONE_FACT` | Director store 已有 typed command result；Desk 之前只有诊断属性和局部项目 IO feedback |
| `CLONE_DECISION` | 使用 fixed-header compact status region 作为 Director command primary projection |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有同样的 result taxonomy、文案、ARIA、颜色或位置 |
| `UPSTREAM_INSPIRATION` | Open Canvas typed result、persistent owner surface 与 transient/primary 分层仅作方法参考 |

本批不证明 LibTV 源站使用相同 feedback surface，不新增普通画布全局 toast，
不接入 provider/remote operation，也不把 presentation feedback 写入 graph、
Director history 或 portable project document。
