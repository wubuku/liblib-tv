# Batch 449 — VR-022 Slice E：确定性请求移交（fake operation acceptor）

> 状态：`IMPLEMENTATION_RECORDED`（editor session/commit/history 合同
> Slice E；clone-only，无源站依赖；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch449-operation-acceptor-929-2026-09-13.png`、
> `scripts/verify-liblib-batch449.py`。

## 变更

- **`src/lib/libtvOperationHandoff.ts`（新，纯模块）**：
  `acceptLibTVOperation` —— 冻结描述符
  `{operationId, kind, canvasId, nodeId, acceptedAt}`，完成时**重新
  校验 owner 存续**（isOwnerCurrent 谓词）：仍持有 → 执行任务
  （completed）；已消失 → `stale-owner` 稳定处置；`cancel()` 显式
  取消。替换裸 setTimeout 身份。
- **VideoNode 四个 owner-bearing 定时器**（audio-split 600ms /
  smart-matting 480ms / picture-edit 520ms / depth-motion 520ms）迁移到
  acceptor：接受时冻结 canvasId+nodeId，完成时 owner 再校验；
  任务完成清空 op 引用（保留防重入门）；卸载清理统一 cancel
  （切换画布取消挂起任务——声明处置不变）。三个纯 UI 反馈定时器
  保持原样。

## 验收（verify-liblib-batch449.py，SCRIPT_RECORDED_PASS —— 真实 matting 流）

- **accepted_completion**：提交经 acceptor 完成——派生节点/边/历史
  恰好各一落在属主画布；
- **switch_cancels_pending**：提交后立即切换画布 → 两侧画布均无迟到
  产物（cancel 处置）、output 徽标数不变、历史不变；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-022）

Slice F（Annotate 纵切，source-evidence gated）、Slice G/H（次级
profile 与生产 adapter）为授权后范围。
