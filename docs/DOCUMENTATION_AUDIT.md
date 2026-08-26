# 文档体系维护审计

> 审计日期：2026-08-26
> 审计范围：根入口、正式指南、研究索引、验证手册、Batch 目录/脚本和当前 LibTV/Open Canvas 研究入口。
> 目的：检查文档是否仍准确反映当前仓库，而不是重新识别已有截图或修改业务实现。

## 1. 审计基线

当前文档体系已经具备四层入口：

```text
AGENTS.md / README.md
  -> docs/index.md
     -> formal guides
     -> research/README.md
        -> source audits / component contracts / Batch history
```

本轮以以下内容为交叉基线：

- `AGENTS.md` 的 agent 规则和协作红线；
- `docs/index.md`、`docs/research/README.md` 的正式导航；
- `docs/HARNESS.md`、`docs/DEVELOPMENT.md`、`CONTRIBUTING.md` 中的验证命令；
- `scripts/verify-liblib-batch*.py` 的实际文件集合；
- `docs/research/liblib-canvas-batchN-*` 的实际研究目录；
- 当前 Seedance/Open Canvas 研究入口及其 go/no-go 文档。

### 1.1 当前计数与范围

| 对象 | 当前观察 | 文档含义 |
|---|---|---|
| Batch 研究目录 | 已有 Batch 3-45 的目录记录 | Batch 45 是当前并行研究 WIP，不能只按已验证实现理解 |
| LibTV verifier | 有 Batch 4-33、35-44 的专项脚本 | Batch 34 没有专项 verifier；Batch 45 当前也没有专项 verifier |
| 默认工程门禁 | `npm run check`、`python3 scripts/verify-docs.py` | 不等于所有 Batch 行为回归都已执行 |
| 源站研究 | LibTV、FrameOS、Open Canvas 均有独立入口 | 源站事实、上游启发和 clone 决策必须继续分层 |
| 代码边界 | LibTV/FrameOS route 与 store 独立；后端为 mock | 研究文档不能暗示真实 Provider、上传或持久化已经存在 |

## 2. 发现的问题

| ID | 问题 | 风险 | 处理决策 |
|---|---|---|---|
| DOC-01 | 根 README 仍写 `Batch 4-40` | 低估当前验证资产范围 | 改为精确脚本范围 `4-33、35-44` |
| DOC-02 | Big Picture 自动化摘要仍写 `Batch 4-33` | 与后文 Batch 35-44 及 Harness 不一致 | 修正为脚本实际范围 |
| DOC-03 | Big Picture 仍称 root README/package.json 保留模板身份 | 与当前 README/package.json 已对齐事实冲突 | 删除该过期判断，保留真实 prototype 边界 |
| DOC-04 | Harness 总览写到 `batch43.py`，循环使用 `{4..44}` | 批量命令会把不存在的 Batch 34 当成脚本执行 | 改为显式 `4..33` 与 `35..44` 两段 |
| DOC-05 | Development/Contributing 只展示 Batch 4-10 | 新 agent 容易误以为后续 Batch 没有验证入口 | 改成单个窄脚本示例 + 链接到完整 Harness |
| DOC-06 | Documentation Plan 的原始审计仍写 Batch 3-10 | 维护者无法区分历史快照和当前状态 | 保留历史段落，增加本轮维护增量与 supersede 说明 |
| DOC-07 | Batch 45 已进入研究索引但尚无 verifier | 容易把研究目录误读为已完成回归 | 记录为并行 WIP，不为其伪造验证状态 |

## 3. 本轮已应用的修正

- 验证范围统一写成：专项脚本存在于 Batch `4-33` 和 `35-44`；
- `docs/HARNESS.md` 的批量示例不再跨过不存在的 Batch 34；
- 根 README、Big Picture、Development 和 Contributing 都链接到完整 Harness，而不是各自维护一份过时清单；
- Big Picture 的 README/package 身份判断以当前仓库实际内容为准；
- `docs/DOCUMENTATION_PLAN.md` 保留 2026-08-25 的迁移快照，并明确本审计是 2026-08-26 的维护增量；
- Batch 45 不被加入“已验证脚本”清单，等待其并行开发者提供稳定脚本和实施记录。

## 4. 仍然有意保留的差异

### 4.1 Batch 34 没有专项 verifier

Batch 34 是既有导演台代码考古、源站差距和可借鉴性研究，不应被虚构成一条行为回归脚本。它的入口和证据仍由 [`docs/research/README.md`](research/README.md) 管理。

### 4.2 Batch 45 不纳入本轮维护

Batch 45 目录和研究记录可能由其他开发者并行推进。本轮只读取其在索引中的存在，不修改其 `README.md`、`PLAN.md`、`IMPLEMENTATION.md`、截图或源码。是否增加 verifier、何时加入 Harness，由该批次稳定后单独维护。

### 4.3 旧 Batch 仍是历史合同

Batch 9/10 等历史截图和断言仍然有效，但只对各自日期的 clone 快照负责；它们不能覆盖当前 LibTV `1092.5px` 图片工具条、`10 + 24 * zoom` 顶部定位或 structured AutoLink 合同。

## 5. 后续文档 backlog

| 优先级 | 工作 | 价值 | 前置条件 |
|---|---|---|---|
| P0 | 任务到文档的 agent reading map | 新 agent 能按任务进入最小证据集合 | 已完成：[`AGENT_TASK_MAP.md`](AGENT_TASK_MAP.md) |
| P0 | 跨文档决策登记 | 关键红线和不可逆选择有单一索引 | 已完成：[`DECISION_REGISTER.md`](DECISION_REGISTER.md) |
| P1 | 证据 claim 反向索引 | 从产品能力反查 DOM/JSON/截图/脚本证据 | 已完成：[`TRACEABILITY_MATRIX.md`](research/TRACEABILITY_MATRIX.md) |
| P1 | verifier 能力台账 | 区分脚本存在、脚本通过、源站已复核和仅有文章证据 | 已完成：[`VERIFICATION_LEDGER.md`](research/VERIFICATION_LEDGER.md) |
| P2 | 文档生命周期清理 | 处理真正过时的草稿和重复索引 | 必须先确认没有 inbound links |

本审计不建议现在做全量目录重排、截图重命名或双语文档翻译；这些动作的收益低于继续维护证据可追溯性。

## 6. 验收

本批维护完成的最低标准：

1. `docs/index.md` 能发现本审计；
2. 所有验证范围描述与实际脚本集合一致；
3. Batch 34/45 的“无专项 verifier”状态没有被隐藏；
4. 文档链接检查通过；
5. 不修改代码、不修改上游 submodule、不覆盖其他开发者 WIP。
