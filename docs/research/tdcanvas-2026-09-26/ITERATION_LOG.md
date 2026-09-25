# ITERATION LOG — TDCanvas 调研包维护史

本文件记录调研包的版本演进、每轮迭代的方法与覆盖面、以及下一轮证据队列。目标协议：持续迭代改进，直到用户喊停。

## v1 — 2026-09-26（首轮落档）

**方法**：锁定提交 `16b3127`（upstream master，2026-09-15，v0.14.0）的干净工作树；5 个并行专题只读调研（渲染内核 / 状态与持久化 / 节点体系 / 交互与生成流 / Agent 与插件），全部结论带 file:line 证据；随后落档本包。

**交付物**：
- README.md（锚点 + Read Order + 结论摘要）
- REPORT.md（面向决策的完整结论）
- SOURCE_ANALYSIS.md（7 章：版本锚点/渲染内核/状态与持久化/节点体系/交互与生成流/Agent 通道/插件与 comfyui-local/证据边界）
- PATTERN_CARDS.md（TD-01..15 模式卡）
- ADOPTION_DECISION_MATRIX.md（20 行采纳矩阵）
- ITERATION_LOG.md（本文件）

**已知覆盖面缺口（按价值排序）**：
1. `chatSessions` 画布 AI 助手会话：数据模型已进项目文档，但助手面板（local-agent-panel 之外）的交互细节未深挖。
2. canvas-home 首页（项目列表页）UI 结构、i18n 双语机制、`CanvasRefreshShell` 挂载细节。
3. `use-canvas-ui-store`/素材库（assets store 全 API）、提示词库（prompt source store）。
4. Rust 侧 lib.rs 全量命令面（除 media_cache 外：窗口、updater、本地文件 reveal 等）。
5. 与上游 `basketikun/infinite-canvas` 的 diff（继承 vs 原创归属）——需要先 clone 上游。

**证据边界声明**：全部为静态源码阅读；未运行应用；行号随上游演进老化。

## 下一证据队列（带停止条件）

| # | 动作 | 产出 | 停止条件 |
|---|---|---|---|
| Q1 | clone `basketikun/infinite-canvas` 为 `research/upstream/infinite-canvas` submodule，diff `16b3127` | UPSTREAM_DIFF_AUDIT.md：机制归属表（继承/改造/新增） | 归属表覆盖 PATTERN_CARDS 全部 15 卡 |
| Q2 | 深挖 chatSessions/助手面板 | SOURCE_ANALYSIS §2 增补 + 交互目录条目 | 面板事件流与数据写回路径闭环 |
| Q3 | 首页/资产库/提示词库/侧栏盘点 | SOURCE_ANALYSIS 增补章 | 全部用户可达 surface 有 file:line 条目 |
| Q4 | Rust 命令面盘点 | 附录表 | invoke() 调用点全部映射到 lib.rs command |
| Q5 | 若上游发新版本：按 UPSTREAM_VERSION_IMPACT 协议（借鉴 open-canvas 包同名片）重审主张 | 版本影响审计 | claims 重核完成 |

## 维护记录

- 2026-09-26 v1：首轮落档（本条）。
