# Batch 562 — AI 导入「自动替换当前图源」全景源状态提升

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站注记（batch 539/554
> 转录）：「上传后画布将新连一个图片节点并**自动替换当前图源**」——
> batch 554 落地了节点+连边半边，本批完成「自动替换」半边。

## 合同

- DirectorDesk 将全景源 setter（`setPanoramaSourceId`）经
  DirectorIconRail 提升传入 DirectorAiImportModal
  （`onPanoramaSourceChange`）；
- 上传成功（image 节点 + 连边后）→ 自动
  `onPanoramaSourceChange(newNodeId)`：场景属性「画布环境」select 自动
  选中新建图片节点（`data-director-panorama-source` value = 新节点 id），
  全景运行时随 select 联动加载（既有机制）；
- 「已连接全景图」标签（batch 561）随之出现；
- 纯本地状态提升，无云端识别（diagnostics:zero 覆盖）。

## 内容

- `src/components/director/DirectorAiImportModal.tsx`（+onPanoramaSourceChange）；
- `src/components/director/DirectorIconRail.tsx`（透传）；
- `src/components/director/DirectorDesk.tsx`（传入 setPanoramaSourceId）；
- `scripts/verify-liblib-batch562.py`（7 检查：空源→上传→select 自动
  选中新建节点）；
- 回归：batch 554/561/70 全绿；typecheck 净（除并行 VitePress dist 噪音）。
- `runtime-audit.json`：本目录。
