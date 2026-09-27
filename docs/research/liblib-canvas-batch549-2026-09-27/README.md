# Batch 549 — 场景显示字段接入视口渲染

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 18）：
> 「角色标签」开关控制角色头顶名称浮标（角色A）；「天空颜色」为天幕
> 底色；「地面…透明度」控制地面平面不透明度。batch 548 落了 schema 与
> 面板控件，本批把三个字段接进真实渲染。

## 合同

- **角色标签**：character 对象头顶渲染 drei `Html` 名称浮标
  （`data-director-character-label`，object.name，黑底白字），受
  `scene.showCharacterLabels`（默认开）控制；浮标 pointer-events 关闭
  不挡拖拽，zIndexRange 压到 40 避免遮盖桌面级浮层；
- **地面透明度**：地面 mesh 材质 `transparent + opacity=groundOpacity`
  （默认 0.4，updateScene 持久化）；
- **天空颜色**：无全景输入时画布背景使用 `scene.skyColor`；有全景时
  回落 `scene.backgroundColor`（全景球覆盖其上）；雾色仍用
  backgroundColor（保持纵深语义）；
- 其余字段（网格吸附/高斯地面吸附）为数据态，渲染吸附语义待后续。

## 内容

- `src/components/director/DirectorViewport.tsx`（Html 标签 + 背景/雾
  分离 + 地面材质透明）；
- `scripts/verify-liblib-batch549.py`（6 检查：标签默认渲染/关隐藏/
  重开恢复/天空与透明度 store 持久化）；
- 回归：batch 70/548 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
