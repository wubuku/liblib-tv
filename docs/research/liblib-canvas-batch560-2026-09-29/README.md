# Batch 560 — 场景变换（缩放/平移/旋转）接入渲染分组

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 45/48
> 右栏 3D 场景面板顶部）：场景缩放（会话示值 300%）、场景平移 XYZ、
> 场景旋转 XYZ。batch 548/555 模式的收尾批次。

## 合同

- `DirectorScene` 新增 `sceneScale`（1）、`sceneTranslate`（[0,0,0]）、
  `sceneRotate`（[0,0,0]，度）——默认保持 clone 现渲染（源站会话示值
  300% 记 SOURCE_DIFF，可能为该会话缩放状态而非出厂默认）；
- V1 文档 optional 字段 + `expectScene` 兼容解码（expectTuple3）；
- 场景属性面板顶部新增「场景变换」section：缩放滑杆（50-300%，百分比
  角标）+ 平移/旋转各三轴 number 输入；
- 渲染接线：视口将 objects + groups 内容包进 scene transform group
  （scale/position/rotation 自 scene 传入，旋转度→弧度）；地面/网格/
  灯光/全景球为辅助不参与。

## 内容

- `src/store/directorStore.ts`（3 字段 + 白名单）；
- `src/lib/directorProjectDocument.ts`（V1 optional + expectTuple3 解码）；
- `src/components/director/DirectorInspector.tsx`（场景变换 section）；
- `src/components/director/DirectorViewport.tsx`（scene transform
  group 包裹）；
- `scripts/verify-liblib-batch560.py`（7 检查）；
- 回归：batch 70/548/558 全绿；typecheck 净；verify-docs pass。
- `runtime-audit.json`：本目录。
