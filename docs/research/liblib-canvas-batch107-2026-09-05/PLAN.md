# Batch 107 Plan：Skill 标题轮换对齐 2026-09-05 源站观察

> 状态：`DONE`（见 [`README.md`](README.md)）
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 106（`batch/106-project-menu`）。
>
> 源站证据：2026-09-05 多次登录态采样，Agent 抽屉标题先后为
> `选一个 Skill，让创作更快一步`、`让 Skill 帮你迈出第一步`、
> `一个 Skill，慢慢打磨你的故事`（已归档审计 §5）。

## 1. 范围

- **包含**：AgentDrawer 标题改为三条源站文案的轮换（`换一批` 推进、按 3 回绕）；
  与 `editorMode` 解耦；卡片批次按 2 取模不受影响。
- **不包含**：Skill 卡集合变更、composer/模型菜单变更、源站轮换驱动研究。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 三种标题文案均在源站观察到 |
| `CLONE_DECISION` | 轮换由 换一批 驱动并回绕；不再绑定 editorMode |
| `SOURCE_UNKNOWN` | 源站轮换的真实驱动（会话/模式/随机） |

## 3. 验证与完成定义

- `scripts/verify-liblib-batch107.py`：三条标题随 换一批 依序出现并回绕、
  卡片仍 4 张、零诊断。
- 相邻 batch97/14/11 复跑通过；`npm run check`、`npm run docs:check` 通过。
- 特性分支 commit/push。
