# Batch 66 计划：Director Reliability Authority

> 状态：`CONTRACTS_RECORDED / VERIFIER_MANIFEST_IN_PROGRESS`。
>
> 日期：2026-08-27。
>
> 风险等级：低到中。本批先做静态研究、合同与验证治理，不修改 Director
> 业务 runtime、R3F scene 或 LibTV source fixture。

## 1. 输入与决策

本批综合两组已落档评估：

- Open Canvas 专题的 document、identity、mutation ingress、history、delete repair、
  async convergence、resource lifecycle、viewport 和 verifier 治理方法；
- StoryAI Director Desk 专题的 project schema、session persistence、undo batch、
  delete workflow、asset/shot model，以及当前 clone 成熟度审计。

当前判断：

1. Director 可见功能数量不再是主要短板；
2. 单例 store 让不同 canvas / source node 共用 scene、timeline 和 capture 状态；
3. mutation entrypoint 已扩展到 object、group、camera、pose、track、path、capture、
   local asset、video export 和 phone vcam，但没有共同 command/history authority；
4. 删除只覆盖 capture、local library item、track、keyframe、path/anchor 等局部对象，
   缺少 scene object/camera 的 reference-aware delete；
5. 17 个历史 focused verifier 没有 current gate，历史通过不能自动升级为 HEAD 通过。

## 2. 价值排序

| 候选 | 用户价值 | 风险降低 | 证据成熟度 | 本批决策 |
|---|---:|---:|---:|---|
| `STORY-R01` project/session authority | 5 | 5 | 5 | **完成静态审计与正式合同** |
| `STORY-R02` command/history/delete | 5 | 5 | 5 | **完成矩阵与正式合同** |
| `STORY-R04` current verifier manifest | 5 | 4 | 5 | **建立 manifest 与 gate 设计** |
| `STORY-I01` project document runtime | 5 | 5 | 3 | 本批研究完成后再单独授权 |
| `STORY-I02` edit safety runtime | 5 | 5 | 3 | 依赖 project identity，后续独立批次 |
| 真实 mesh / panorama | 4 | 4 | 2 | 延后到 owner/resource authority 后 |
| 多机位 / source calibration | 4 | 3 | 2 | 依赖 source/product 证据 |

## 3. 工作包

### A. Project / Session / Owner Audit

- 枚举 scene、object、group、camera、capture、timeline、track、keyframe、path、
  local asset、phone vcam 和 export identity；
- 区分 portable project、runtime state、session UI、resource lease；
- 记录 `route/canvasId/sourceNodeId/projectId/schemaVersion/generation` owner；
- 定义 open/switch/close/delete/duplicate/restore 的 lifecycle disposition；
- 对照 StoryAI schema/persistence 的正面模式与反例。

### B. Command / History / Delete Matrix

- 枚举 `directorStore` 全部 mutation action 及组件外部副作用；
- 分类为 transient、gesture update、gesture commit、semantic command、async result；
- 定义 invalid/noop/reject/commit、one-entry、undo/redo 和 cleanup；
- 建立 object/group/camera/track/keyframe/path/capture/local asset 引用图；
- 给出 delete closure、detach、fallback、retain/release 和 unknown 决策。

### C. Current Verifier Manifest

- 盘点 Batch 35-50、59 共 17 个 Director focused verifier；
- 记录 fixture、query/setup、主要 capability、artifact、副作用、预估成本；
- 分类 `CURRENT_GATE`、`MERGE_CANDIDATE`、`HISTORICAL_ONLY`、`SOURCE_STALE`；
- 区分 historical recorded pass 与 current HEAD 实际运行；
- 设计 current smoke/full 命令和 warning baseline，不覆盖历史截图。

### D. 可发现性与交接

- 新增稳定 project/session 与 command/history/delete 合同；
- 新增 current verifier manifest；
- 更新 Research Hub、Big Picture、Agent Task Map、coverage、fixture、verifier、
  traceability、decision register 和 verification ledger；
- 形成 implementation record，明确下一批可编码的最小 slice。

## 4. 计划产物

Batch 目录：

```text
README.md
PLAN.md
SCREENSHOT_ANALYSIS.md
STATIC_AUDIT_2026-08-27.md
EVIDENCE_MATRIX.md
IMPLEMENTATION.md
```

稳定研究权威：

```text
docs/research/LIBTV_DIRECTOR_PROJECT_SESSION_AUTHORITY_CONTRACT.md
docs/research/LIBTV_DIRECTOR_COMMAND_HISTORY_DELETE_CONTRACT.md
docs/research/LIBTV_DIRECTOR_CURRENT_VERIFIER_MANIFEST.md
```

建议预留：

- fixture：`LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01`；
- verifier：`LIBTV-VR-024`；
- implementation sequence：project document -> command/history -> delete repair ->
  current gate。

## 5. 明确不做

- 不修改 `research/upstream/storyai-3d-director-desk` submodule pointer；
- 不把 StoryAI JSON、undo stack、camera shot 或 CSS 原样复制；
- 不修改 Director runtime store、components、R3F scene 或普通 canvas graph；
- 不新增真实 mesh、panorama、多机位、cloud sync 或 source-shaped UI；
- 不重跑截图识别，不覆盖历史 screenshot/runtime audit；
- 不把历史 verifier pass 写成当前完整回归；
- 不把 clone/StoryAI/Open Canvas 行为写成 LibTV source fact。

## 6. 验证

静态研究阶段：

```bash
rg / sed / git show
npm run docs:check
git diff --check
```

current verifier manifest 需要对脚本做静态解析，并至少运行一个低成本只读 smoke；
是否运行全部 17 个脚本由 manifest 对 fixture 污染、截图覆盖和成本的审计结果决定。
任何运行生成的历史 artifact 在提交前恢复。

## 7. Checkpoint

1. 计划、证据边界和截图成本台账先 commit/push；
2. static audit 与 evidence matrix 完成后建立保护性 checkpoint；
3. 正式合同和 current manifest 完成后运行文档门禁；
4. 同步稳定索引、记录实施结果并 commit/push；
5. 依据合同选择下一批最小代码 slice，不在本批顺手重构 3,800 行 store。

## 8. 当前进度

| 工作项 | 状态 | 记录 |
|---|---|---|
| 计划、边界、截图成本 | `DONE` | `a7bcf21` |
| project/session/owner 静态审计 | `DONE` | [`STATIC_AUDIT_2026-08-27.md`](STATIC_AUDIT_2026-08-27.md) |
| command/history/delete 静态审计 | `DONE` | 同上 |
| evidence matrix | `DONE` | [`EVIDENCE_MATRIX.md`](EVIDENCE_MATRIX.md) |
| 两份稳定合同 | `DONE` | project/session + command/history/delete |
| 17-script current manifest | `IN_PROGRESS` | 待静态分级和至少一次 current smoke |
| governance/implementation closeout | `PENDING` | 待合同与验证完成 |
