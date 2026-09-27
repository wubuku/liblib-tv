# Batch 541 — 添加角色 flyout 预设项本地等效动作

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（batch 537，
> 截图 44-director-rail-23）：添加角色 flyout 列出 本地上传、八种预设
> 体型与两个子菜单行；源站点击预设会加入对应 3D 角色变体。

## clone 合同（本地等效）

- **群众 (3x3)** → `directorStore.addCrowdArray({rows:3, columns:3,
  spacing:1.2})`（与 DirectorViewport 群众面板同默认），场景对象真实
  增加，flyout 收起 + ack「已加入群众 (3x3)（本地等效）」；
- **预设体型**（标准男性/标准女性/健硕/纤细/少年/儿童/宽厚/二头身）→
  ack「预设角色「…」为本地等效占位」——store 无单角色变体加建
  （CLONE_DECISION：不伪造 3D 生成），对象数不变；
- 本地上传/几何模型 → 静默收起（真实上传流/子菜单未采样）；
- ack 元素 2 秒自动淡出（`data-director-character-ack`，aria-live）。

## 内容

- `src/components/director/DirectorIconRail.tsx`（flyout 项接线 +
  ack 回显）；
- `scripts/verify-liblib-batch541.py`（9 检查：群众对象数递增、预设
  占位不生成 3D、flyout 关闭、ack 淡出）；
- 回归：batch 536/540/70 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
