# Batch 281 — 生成历史面板 scope chips 对齐（源站 2026-09-10 采样落地）

> 状态：`IMPLEMENTED`（batch 280 采样 → 漂移对齐 → 14 checks 验收 →
> 40 项回归绿）。
>
> 源站证据：`../liblib-canvas-batch280-2026-09-10/生成历史.png`。

## 对齐内容（batch 280 采样事实）

HistoryPanel（batch 101 已有实现）的漂移仅为 **scope chips**：源站为
「全部画布 + 本画布」两个 chip，clone 原只有 本画布。已补 全部画布
chip（`data-history-scope-chip="all"`，与本画布 chip 互斥 aria-pressed；
视图不随 scope 变化——本地 mock 数据无画布归属，CLONE_DECISION）。

其余结构（图片/视频/音频计数页签、所有评级/时间倒序/批量操作、
暂无历史记录 空态）与源站一致，无需改动。

## 验收

- `verify-liblib-batch281.py`：**14 checks**（覆盖层打开；两个 scope
  chip；默认 本画布/可切 全部画布；三计数页签；评级/排序/批量控件；
  video 页签空态）。
- 回归绿：21–268 维护集 40 项。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。

## 不证明

- scope 切换的真实数据视图差异（mock 数据无画布归属）；
- 全部画布 chip 的选中样式与源站像素级一致性（结构性对齐）。
