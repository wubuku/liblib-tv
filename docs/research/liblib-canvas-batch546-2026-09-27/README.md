# Batch 546 — AI 识图导入历史记录页签（本地模型库等效）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（batch 539，
> 截图 44-director-rail-27）仅有空态「暂无历史记录」——含条目的历史
> 内容未采样（SOURCE_UNCERTAIN）。本批为本地等效：历史页签列出
> `directorStore.localModelLibrary` 已导入模型（batch 542 本地上传
> 管线的产物）作为识别源候选。

## 合同

- 空库 → 「暂无历史记录」空态保持（batch 539 合同不变，回归绿）；
- 有已导入模型 → `data-director-ai-import-history-item` 行列出
  （模型名 + 文件名），纯可视不触发识别；
- 本地等效边界：源站历史为云端识图任务史（未采样），clone 以本地
  模型库近似（CLONE_DECISION 注记于组件头）。

## 内容

- `src/components/director/DirectorAiImportModal.tsx`（历史页签列表）；
- `scripts/verify-liblib-batch546.py`（4 检查：空态 → batch 542 导入
  后列出条目）；
- 回归：batch 539/542 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
