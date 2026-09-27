# Batch 548 — 3D 场景设置面板扩展（显示字段）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 18/45
> 右栏 3D 场景面板）：显示区含 天空颜色 #060608、角色标签（开）、
> 网格吸附（关）、高斯地面吸附（开）、地面透明度 0.40。

## 合同

- `DirectorScene` 新增 5 字段（additive）：`skyColor`（#060608）、
  `showCharacterLabels`（true）、`snapToGrid`（false）、
  `gaussianGroundSnap`（true）、`groundOpacity`（0.4）；
- `updateScene` 白名单 + 类型校验同步扩展；
- 持久化向后兼容：`DirectorSceneDocumentV1` 新字段 optional，
  `expectScene` 改用 `expectExactKeysWithOptional`，restore 侧
  `normalizeRestoredScene` 按默认场景兜底（旧文档零破坏）；
- 场景属性面板新增 5 行控件（天空颜色取色器、三开关、透明度
  range 0-1 step 0.05），updateScene 持久化；
- 场景缩放/平移/旋转与全景球字段**暂不克隆**（源站数值型场景变换，
  clone 3D 渲染无对应实现，记 SOURCE_FACT 待渲染能力补齐）。

## 内容

- `src/store/directorStore.ts`（schema + defaults + 白名单 +
  normalizeRestoredScene）；
- `src/lib/directorProjectDocument.ts`（V1 optional 字段 + expectScene
  兼容解码）；
- `src/components/director/DirectorInspector.tsx`（5 行设置控件）；
- `scripts/verify-liblib-batch548.py`（10 检查：默认值、三开关持久化、
  透明度滑杆持久化）；
- 回归：batch 70/536/547 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
