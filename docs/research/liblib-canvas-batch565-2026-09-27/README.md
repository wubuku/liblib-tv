# Batch 565 — 全景背景联动端到端核对（零产品代码改动）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站证据：截图 45/48
> （全景背景 已连接全景图 状态 + 画布环境 select）。零产品代码改动，
# 端到端形式化既有联动链路。

## 合同（验证既有实现）

- 连接上游图片节点（image.source → director.target）后：
  - `collectDirectorCanvasMediaInputs` 收集该节点 → 画布环境 select 出现
    该选项；
  - `resolvedPanoramaSourceId` 默认 = 第一个 input → select 自动选中；
  - `DirectorPanoramaRuntime` 加载贴图 → `panoramaRuntimeState === ready`；
  - 「已连接全景图」标签出现（batch 561）；
- 状态点 `data-director-panorama-state=ready`。

## 内容

- `scripts/verify-liblib-batch565.py`（6 检查：空 select → 连边 → 自动
  选中 → ready → 标签）；
- 回归：batch 548/561 全绿；typecheck 净；verify-docs pass。
- `runtime-audit.json`：本目录。
