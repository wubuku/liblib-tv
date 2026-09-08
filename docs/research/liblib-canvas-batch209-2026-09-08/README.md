# Batch 209 — 画布 chrome 对齐（无 attribution/无 controls，MiniMap 默认关闭）

## 源站事实（窗口 rAF ~31fps；`source-minimap-check.json` / 截图存档）

- 源站画布 **无 MiniMap、无 Controls、无 react-flow attribution**——
  仅背景点阵（`.react-flow__background` 1 个）。
- clone 核对：MiniMap 本就默认关闭（opt-in，与源站一致）；Controls
  本就未渲染；**attribution 有 1 个实例**（React Flow 默认渲染）——
  唯一差异。

## 实施

- `page.tsx` ReactFlow 增加 `proOptions={{ hideAttribution: true }}`。

## 验收

- `verify-liblib-batch209.py`：5 checks（minimap/attribution/controls
  全零 + background 存在 + 0 page error）。
- 回归绿：22 / 9 / 51 / 172 / 205。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 源站测试残留清理：0 残留（本批无源站节点操作）。
