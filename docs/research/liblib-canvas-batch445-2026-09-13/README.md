# Batch 445 — VR-022 Slice A：纯编辑器 profile/session/history 模型

> 状态：`IMPLEMENTATION_RECORDED`（editor session/commit/history 合同
> 首个 runtime 切片；纯模型、无 React/store 变更；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch445-editor-session-929-2026-09-13.png`、
> `scripts/verify-liblib-batch445.py`。

## 变更

- **`src/lib/libtvEditorSession.ts`（新，纯模块）**：
  - 十项 profile 判别注册表（§5：INLINE_SCALAR … EMPTY_EVIDENCE_GATED），
    每项声明 commit 触发集、Escape 政策、history owner、acceptance、
    evidenceGated、归一化方式；
  - §5.2 非法组合不变量检查（evidence-gated 不得暴露验收命令、
    multiline 裸 Enter、live inspector 非合并历史、bitmap 非记录
    指纹）；
  - §9 语义归一/脏检查/无操作（INLINE_SCALAR trim；INLINE_MULTILINE
    保留空白）；
  - §7 会话状态机 reducer 子集（CLOSED/OPEN_CLEAN/OPEN_DIRTY/
    COMMITTING_SYNC/ACCEPTED/REJECTED_RETRYABLE/INVALIDATED/DISPOSING）
    与稳定拒绝原因（非法迁移、重复 open、clean commit、失效后提交）；
  - §10.7/§10.2 本地历史预算（50 条）与同窗口同 kind 手势合并（600ms）。
- **page.tsx**：只读 window 诊断暴露（模型函数族），无 UI/状态变更。

## 验收（verify-liblib-batch445.py，SCRIPT_RECORDED_PASS）

- **profile_registry**：10 项注册表全部通过各自不变量；
- **profile_invariants**：篡改 evidence-gated/multiline/live 三项
  逐一检出违规；
- **session_state_machine**：open→edit(dirty)→commit-sync→accepted
  主链、cancel→disposal 链、回到基线的 edit 为 handled-noop、
  clean commit/重复 open/失效后提交均稳定拒绝；
- **normalization_noop**：scalar trim、multiline 保留空白；
- **history_budget_coalescing**：窗口内合并（2→1）、预算封顶 50；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-022）

Slice B（equality-aware graph commit adapter）、Slice C（迁移现有
功能岛：TextNode 取消/提交守卫、Picture 语义详情、Subtitle 幂等）。
