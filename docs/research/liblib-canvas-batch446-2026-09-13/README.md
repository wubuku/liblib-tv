# Batch 446 — VR-022 Slice B：equality-aware graph commit adapter（owner/generation/fingerprint 校验）

> 状态：`IMPLEMENTATION_RECORDED`（editor session/commit/history 合同
> Slice B；clone-only，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch446-commit-adapter-929-2026-09-13.png`、
> `scripts/verify-liblib-batch446.py`。

## 变更

- **`planLibTVEditorSessionCommit`（纯 planner，编辑器会话模块）**：
  owner 存在性 → canvasId → canvasGeneration → 指纹四段校验，输出
  命名状态 `accepted / no-op / stale / invalid-owner / conflict`
  （含稳定 reason：OWNER_MISSING、CANVAS_CHANGED、GENERATION_CHANGED、
  SCOPED_FIELD_DRIFTED、DRAFT_EQUALS_{BASELINE,CURRENT}）。
- **`canvasStore.canvasGeneration`（新）**：每次成功切换画布单调 +1
  （§3.3 世代不变量的最小实现；未知目标 NOOP 不计数）。
- **`canvasStore.submitLibTVEditorSessionCommit(request)`（新动作）**：
  组装当前观测、跑 planner；`accepted` 时以归一化草值写回目标字段并
  **恰好一条 graph 历史**；no-op/conflict/stale/invalid-owner **零变更
  零历史**。本批不迁移既有编辑器调用（Slice C 范围）。

## 验收（verify-liblib-batch446.py，SCRIPT_RECORDED_PASS）

- **accepted**：带空白草值经 trim 归一后提交，filename 更新、恰好
  +1 历史；
- **no-op**：同一草值重复提交 → `no-op`、零历史零变更；
- **conflict**：作用域字段被旁路改为「第三方」后按旧基线提交 →
  `SCOPED_FIELD_DRIFTED`，零变更（不覆盖现值、草值保留语义）；
- **stale**：切换往返使旧世代失效 → `GENERATION_CHANGED` 拒绝；
  携带新世代重新提交 → accepted；
- **invalid-owner**：缺失节点 → `OWNER_MISSING`；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-022）

Slice C（迁移现有功能岛：TextNode 取消/提交守卫、Picture 语义详情、
Subtitle 幂等——把现有编辑器接到本适配器）。
