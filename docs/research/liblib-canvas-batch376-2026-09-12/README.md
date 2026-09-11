# Batch 376 — jimeng batch 2 工具条对照抽查（`REVIEW_RECORDED`）

> 状态：jimeng batch 2「选中态处理工具条」可视化对照完成——**1:1
> 一致，无干预需要**。liblib.tv 恢复重测：`RECOVERY: still-broken`
> 维持。无代码变更。

## 对照（源站 2026-09-12 截图 vs clone batch 2 截图）

- **一致**：处理工具条 7 动作（局部重拍 / 智能超清 / 视频编辑 /
  截取帧∨ / 补帧 / 视频修剪 / 提示词反推）+ ↗ 全屏 + 下载 双图标
  ——动作集合、顺序、胶囊形状、节点上方位置全部对应；
- **一致**：视频节点选中态 + 右侧「视频 1」第二节点 + 节点命名
  （sb_518102884…-tf5q2）+ 底部播放器（00:02 / 00:06 + 倍速 + 全屏）；
- **差异**：clone 视频画面为占位图（无视频源）——mock 边界
  （CLONE_DECISION，并行路线已记录）。

## 源站状态

liblib.tv：`RECOVERY: still-broken` 维持（probe-source-recovery.py
本批复测）。jimeng.jianying.com 独立站点不受影响。

## 后续候选

- jimeng batch 3-8 的同款对照抽查（genpanel/context/repaint/
  video-edit/zoom-help/infer——随并行路线节奏）；
- liblib.tv 恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换。
