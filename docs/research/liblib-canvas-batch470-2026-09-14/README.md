# Batch 470 — VR-018 Slice D：Director 导出重复完成抑制

> 状态：`IMPLEMENTATION_RECORDED`（command outcome/feedback 合同
> Slice D 子项；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch470-export-suppression-929-2026-09-14.png`、
> `scripts/verify-liblib-batch470.py`。

## 变更

- **`createDirectorAnimationExport`（canvasStore）**：同 exportId 的
  重复导出解析到既有节点（返回其 id，零新节点/零新边/零新历史）；
  丢失源仍为稳定 null。

## 验收（verify-liblib-batch470.py，SCRIPT_RECORDED_PASS）

- **export_accepted**：首次导出创建节点/边/+1 历史；
- **export_duplicate_suppressed**：同 exportId 二次导出返回既有节点
  id、零新增；
- **missing_source_stable_null**：未知源返回 null；
- console/pageerror/requestfailed 为 0；无溢出。

## 后续（VR-018）

Slice C（节点反馈 owner 绑定）与 Slice E（路由瞬态通道，条件项）。
