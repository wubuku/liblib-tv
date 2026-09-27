# Batch 539 — 导演台 AI 识图导入模态

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 已存截图转录
> （liblib-source-exploration-2026-09-25 44-director-rail-27.png，零新采样）
> ——rail「AI 识图导入」打开的居中模态。

## 源站实测（SOURCE_FACT）

- 标题栏「AI 识图导入」+ ✕；页签 本地上传（默认）| 历史记录；
- 虚线拖拽上传区：「点击上传图片 或 拖拽本地图片至此上传」+ 注释
  「上传后画布将新连一个图片节点并自动替换当前图源」；
- 单选组「选择是否覆盖场景」：插入当前导演台（默认选中；作为站位
  参考层插入，不覆盖当前全景、角色和机位）/ 覆盖当前导演台（作为
  站位参考层插入，覆盖当前全景、角色和机位）；
- 底栏：「关闭不会中断识图任务，生成站位参考后自动导入导演台」+
  「生成站位参考」按钮（未上传时禁用态灰底）。

## clone 合同

- `data-director-ai-import-modal`（z-290 居中，backdrop 点击 / ✕ 关闭）；
- 页签切换：历史记录 → 「暂无历史记录」空态占位；
- 覆盖场景单选组本地切换（insert 默认）；
- 「生成站位参考」恒为禁用——真实识图/上传/生成为云端 AI 动作，
  clone 永不触发（diagnostics:zero 覆盖无网络）；
- 上传区为可视占位（真实上传流不实现——避免任何图源替换副作用）。

## 内容

- `src/components/director/DirectorAiImportModal.tsx`（新组件）；
- `src/components/director/DirectorIconRail.tsx`（ai-import 接通模态）；
- `scripts/verify-liblib-batch539.py`（17 检查）；
- 回归：batch 536/70 全绿；`npm run check` 全门绿（typecheck/lint/build）。
- `runtime-audit.json`：本目录。
