# Batch 536 — 导演台左侧图标栏（六入口）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。第二轮源站采样
> （liblib-source-exploration-2026-09-25 NOTES §8 + 截图
> 18-director-console-opened.png）：3D 导演台最左窄图标栏（约 46px），
> 纵排六入口——图层（激活态）/人物/机位/帧/文件夹/导入。

## 合同

- `data-director-icon-rail`（46px，左缘，border-r）；
- 六按钮 `data-director-rail-entry`：layers/characters/cameras/frames/
  folders/import，aria-label 用中文名（图层/人物/机位/帧/文件夹/导入）；
- 默认 layers 激活（aria-pressed）；点击切换激活态（单选视觉态）；
- 未采样面板（其余五项）不导航——标题标注「源站面板未采样」
  （CLONE_DECISION），场景树（layers 对应面板）不受影响常驻；
- 布局：树面板 left 0→46px（移动端滑出仍归零避免露边），视口 main
  左偏移 220→266px；batch 70/341 桌面+移动回归绿。

## 内容

- `src/components/director/DirectorIconRail.tsx`（新组件）；
- `src/components/director/DirectorDesk.tsx`（挂载 + 布局偏移）；
- `scripts/verify-liblib-batch536.py`（14 检查）；
- 回归：batch 70（桌面导演台）、341（工具条/移动溢出）全绿；
  lint 0 error。
- `runtime-audit.json`：本目录。
