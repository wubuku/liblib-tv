# Batch 447 — VR-022 Slice C：RECORD_EDITOR 单验收路径（subtitle/picture 提交幂等）

> 状态：`IMPLEMENTATION_RECORDED`（editor session/commit/history 合同
> Slice C 的可落地子集；clone-only；心跳批次）。
>
> 证据：`runtime-audit.json`、
> `docs/design-references/liblib-clone-batch447-record-editor-idempotent-929-2026-09-13.png`、
> `scripts/verify-liblib-batch447.py`。

## 变更

- **`fingerprintLibTVEditorRecords` / `LibTVRecordEditorSubmitResult`
  （编辑器会话模块新增）**：键序规范化的记录指纹 + 命名提交结果
  （accepted / no-op / rejected + targetId）。
- **`createSubtitleErase` / `createPictureEdit`（store）**：提交前以
  (sourceId + mode + 规范化 regions/marks) 指纹扫描同画布既有目标——
  **相同重提交 = no-op 返回既有 targetId**（零新节点、零新边、零新
  历史）；不同 mode/记录仍创建新目标。rejected（空 regions/marks）
  也改为命名结果。

## Slice C 对照说明

- TextNode：现状为 markdown 展示块、无 textarea（源站编辑入口未
  采样，batch 218）——「cancel/blur/commit guard」无可迁移对象，
  记录在案；
- Picture/Subtitle：本批以 RECORD_EDITOR 指纹幂等关闭其「一条验收
  路径」缺口；
- 剩余：命令诚实度 pass（Slice D）与 REQUEST_DRAFT 描述符（Slice E）
  待后续批次。

## 验收（verify-liblib-batch447.py，SCRIPT_RECORDED_PASS）

- subtitle 相同 smart 提交两次 → 首次 accepted、二次 no-op 且
  targetId 相同；节点/边/历史各恰好 1；
- region 模式（不同记录）→ accepted 新目标（+1 节点/+1 历史）；
- picture 相同 marks 提交两次 → 二次 no-op 同 targetId；
- console/pageerror/requestfailed 为 0；无溢出。
