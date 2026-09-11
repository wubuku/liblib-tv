# Batch 344 — 故事板栏展开切换与图片栏对话反馈（`CLONE_DECISION` 实装）

> 状态：展开图标 = 栏宽放大切换、对话按钮 = 本地状态反馈，实装并
> 通过验证（`verify-liblib-batch344.py` 21 checks 全绿）。
> 源站目标行为未采得（画布渲染劣化持续，恢复探测
> `RECOVERY: still-broken`）——**CLONE_DECISION**，文档明标。

## Clone 实现

1. **展开切换**：图片/视频栏头部的展开图标点击后该栏放大为主位
   （`data-storyboard-expanded="true"`、`aria-expanded`、图标切
   Minimize2、aria-label 放大↔还原），另一栏收窄为从位；再点还原
   默认宽度。宽度合同：图片栏 393→410（视频 319→302），视频栏
   展开时图片收至 26%、视频占余下主位；
2. **对话反馈**：图片栏 对话 按钮（`data-storyboard-dialog`，
   aria-expanded）切换 `data-storyboard-dialog-status` 提示
   「本地原型：对话未连接」。

## 验收

- `verify-liblib-batch344.py` 21 checks：默认宽度、双向展开/还原
  的宽度与属性断言、aria 标签切换、对话提示开合，全绿；
- 回归：334/336/337/341/100 全绿；`npm run check` 0 errors
  （8 warnings 基线）；docs check 通过（903 Markdown）。

## 后续候选

- 源站恢复后：以真实展开/对话行为替换 CLONE_DECISION；
- BLOCKED_SOURCE 三项补采；
- 新表面随源站更新巡检。
