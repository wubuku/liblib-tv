# Batch 341 — 工作流工具栏 chrome 标签对照修正（`IMPLEMENTED_VERIFIED`）

> 状态：以源站 2026-09-11 aria-label 直证对照 clone 工作流底部
> 工具栏，修正两处标签漂移；`verify-liblib-batch341.py` 19 checks
> 全绿。证据：batch 340 会话的源站 aria-label 转储
> （`data-liblib-overlay` 探针，2026-09-11）。

## 源站事实（`SOURCE_FACT`，2026-09-11 aria-label 直证）

- 底部左簇（6 控件，顺序）：`资产管理`、`整理画布，Option+Shift+F`、
  `切换小地图`、`隐藏节点连线`、`网格吸附`、`缩放选项`；
- 底部中簇（8 钮）：`添加节点`、`移动`、`打开工具箱`、`素材库`、
  `角色库`、`生成历史`、`快捷键`、`教程`。

## Clone 修正（`SOURCE_FACT` 对齐）

- `显示缩略图` → **`切换小地图`**（aria-label 漂移修正）；
- `吸附到网格` → **`网格吸附`**；
- 其余 12 个标签与源站逐字一致，无需改动。

## 验收

- `verify-liblib-batch341.py` 19 checks：14 个标签存在性 + 2 个漂移
  标签消除 + 左簇顺序 + 缩放百分比文本，全绿；
- 回归：19（改引用）/21/171/240/334/336/337 全绿；
- `npm run check` 0 errors；docs check 通过（900 Markdown）。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 图片栏 对话/展开 行为采样；
- 新表面随源站更新巡检。
