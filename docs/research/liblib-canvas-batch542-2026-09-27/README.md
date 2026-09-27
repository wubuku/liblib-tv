# Batch 542 — 添加角色「本地上传」接通本地模型库导入管线

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（batch 537，
> 截图 44-director-rail-23）：添加角色 flyout 的「本地上传」上传自定义
> 角色模型。clone 复用导演台既有本地模型库导入管线
> （`readDirectorLocalModelFiles` → `addLocalModelLibraryItem`，与
> DirectorViewport 模型库同源）。

## 合同

- flyout「本地上传」→ 打开文件选择器（隐藏 input，accept
  .glb/.gltf/.fbx/.obj，multiple）；
- 有效模型文件（管线实际支持 .fbx/.obj，`LOCAL_MODEL_EXTENSION_RE`）
  逐个入本地模型库（我的模型 分类），ack 回显
  「已导入 N 个本地模型至模型库」（2s 淡出）；
- 无有效文件时 ack「未选择可用模型文件」；flyout 点击后收起；
- 纯本地管线复用——无云端动作（diagnostics:zero 覆盖）。

## 内容

- `src/components/director/DirectorIconRail.tsx`（本地上传分支 +
  隐藏 file input + 异步导入处理）；
- `scripts/verify-liblib-batch542.py`（7 检查：file chooser、库 +2、
  ack、flyout 关闭、ack 淡出）；
- 回归：batch 536/540/541 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
