# Batch 537 — 导演台 rail 标签 DOM 修正 + 添加角色 flyout

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。2026-09-27 CDP DOM 补采
> （有头浏览器导演台实开，rail 按钮 aria-label 枚举 + 逐面板截图
> 42-44）：batch 536 从 NOTES §8 推断的六标签与源站不符——实际七入口：
> **场景 / 添加角色 / 添加机位 / 全景图 / 选择画幅比例 / AI 识图导入 +
> 帮助**（? 圆钮在栏底部，即截图 18 左下 ? 的本体）。

## 修正与新增

- rail 标签全量修正为 DOM 实证七入口（id：scene/add-character/
  add-camera/panorama/aspect-ratio/ai-import/help）；536 verifier
  迁移至修正合同（台账规则：记录合同更替依据——DOM aria-label 实证
  优于 NOTES 视觉推断）；
- **添加角色 flyout**（截图 44-director-rail-23 转录）：本地上传 +
  预设角色 标准男性/标准女性/健硕/纤细/少年/儿童/宽厚/二头身 +
  子菜单项 群众 (3x3)/几何模型（›角标）；菜单项为可视态——
  3D 角色加建为 3D 内容动作，clone 不实现（CLONE_DECISION）；
- 添加机位为直接动作（点击无面板，token 采样证实），保留视觉切换；
- 帮助按钮落栏底（对应截图 18 左下 ?）；点击后无弹层采样
  （HELP 文本采样均否），保持无动作。

## 内容

- `src/components/director/DirectorIconRail.tsx`（标签修正 + flyout +
  帮助底部钮）；
- `scripts/verify-liblib-batch536.py`（迁移至七入口合同 + flyout 11 项
  菜单断言）；
- 回归：batch 536（迁移后）/70 全绿；lint 0 error；typecheck 净。
- 截图 42/43/44-*：exploration 目录。
