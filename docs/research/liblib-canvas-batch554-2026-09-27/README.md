# Batch 554 — AI 识图导入拖拽上传落地（画布图片节点 + 连边）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站注记（batch 539
> 转录）：「上传后画布将新连一个图片节点并自动替换当前图源」。本批把
> batch 539 的可视拖拽区升级为可用的本地上传入口。

## 合同

- 拖拽区（`data-director-ai-import-dropzone`，role=button）点击 →
  隐藏 file chooser（accept image/*）；
- 选中图片 → FileReader 转 dataURL → 活动画布新建 image 节点
  （imageUrl=dataUrl）→ `addEdge` 连边 图片.source → 导演台节点.target
  （经 `validateLibTVGraphConnection` 校验）；
- ack「已创建图片节点并连接到导演台（本地等效）」；无有效图片 →
  「未选择可用图片」；
- **自动替换当前图源留待**——需 DirectorDesk 全景源状态提升
  （CLONE_DECISION，画布环境 select 中可手动选择新节点）；
- 纯本地管线，无云端识别（diagnostics:zero 覆盖）。

## 内容

- `src/components/director/DirectorAiImportModal.tsx`（dropzone 可交互
  + 隐藏 file input + dataURL→节点→连边）；
- `scripts/verify-liblib-batch554.py`（6 检查：file chooser、画布
  image 节点 +1、连边、ack、✕ 关闭）；
- 回归：batch 539/546/70 全绿；typecheck 净（除并行 frameos WIP）；
  lint 0 error。
- `runtime-audit.json`：本目录。
