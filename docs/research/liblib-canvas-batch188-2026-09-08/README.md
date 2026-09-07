# Batch 188 — 工具条 pill 图标原字形对齐（源站 2026-09-08 直采）

## 源站事实（窗口 rAF ~31fps；`source-toolbar-pills.json` / 截图已存档）

- 视频面板工具条五枚 pill 均带 12×12 libtv 图标（`text-fg-muted`）：
  - 参考：`0 0 17 17` 加号（新增引用）；
  - 标记：`0 0 16 16` 定位针 + 星芒（内含 g transform）；
  - 特效：`0 0 16 16` 相机 + 镜头圆（g transform）；
  - 角色库：`0 0 16 16` 盾牌 + 对勾（g transform）；
  - 运镜：`0 0 16 16` 摄影机（g transform）。
- pill 尺寸 54×26（角色库 66，两字 + 图标）。

## 实施

- 新增 `src/components/nodes/ToolbarPillIcons.tsx`：五枚图标 JSX 逐字
  内嵌（viewBox/g transform/path 与源站一致）。
- `VideoGenerationPanel` 工具条 map 弃用 lucide
  （Images/AtSign/Sparkles/Box → 移除未用 import；Film/Sparkles 仍被
  模型菜单使用故保留），改用 `PillIcon`；运镜的菜单箭头逻辑不变。

## 验收

- `verify-liblib-batch188.py`：12 checks（五枚 pill svg viewBox 与源站
  直采逐一相同 + path 非空 + 0 console error）。
- 回归绿：22 / 151 / 166 / 172 / 178 / 185 / 186。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：iconify 集内其它图标（参数菜单比例瓦片图形为独立绘制系统，
  未在本批范围）；pill 激活态样式。
- 源站测试残留清理：采样节点已删（0 残留）。
