# Batch 107：Skill 标题轮换对齐 2026-09-05 源站观察

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 106（`batch/106-project-menu`）。

2026-09-05 多次登录态采样观察到 Agent 抽屉三种 Skill 标题：`选一个 Skill，
让创作更快一步`、`让 Skill 帮你迈出第一步`、`一个 Skill，慢慢打磨你的故事`。
本批把 Batch 97 的「双模式绑定标题」改为三文案轮换（换一批推进、可回绕），
并取消对 editorMode 的耦合。

## 导航

- [PLAN.md](PLAN.md)：范围与证据边界。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `SOURCE_FACT` | 三种标题文案均在源站观察到 |
| `CLONE_DECISION` | 轮换由 换一批 驱动并回绕；不再绑定 editorMode |
| `SOURCE_UNKNOWN` | 源站轮换的真实驱动（会话/模式/随机） |

## 实施结果

- `AgentDrawer`：标题数组轮换，`skillBatch` 无界递增、卡片按 2 取模、标题按
  3 取模；移除 editorMode 耦合。
- batch97 断言（boot 显示第一条标题）无需变更并通过。

## 完成定义

1. `verify-liblib-batch107.py` 6 checks、`0/0/0` diagnostics 通过。
2. 相邻 `verify-liblib-batch97/14/11.py` 通过。
3. `npm run check`、`npm run docs:check` 通过。
4. 特性分支 commit/push。

通过结果只证明 clone-owned 标题轮换合同；源站真实轮换驱动仍是
`SOURCE_UNKNOWN`。
