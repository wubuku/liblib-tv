# Batch 124 Plan：画布回收站（软删除 + 恢复）

> 状态：`IN_PROGRESS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 123。
>
> 源站证据：[`../liblib-projects-page-2026-09-06/README.md`](../liblib-projects-page-2026-09-06/README.md) 回收站采样（仅显示最近 30 天内删除的内容/勾选/恢复）。

## 1. 范围

### 包含

1. **store**：`removedCanvases`（完整 CanvasData 快照 + removedAt）；`removeCanvas`
   改为软删除（移入 removedCanvases，保留原 history 清理语义）；新增
   `restoreCanvas(id)`（整卡恢复回列表，不自动切换活动画布）与
   `purgeRemovedCanvas(id)`（永久清除）。
2. **/project 回收站面板**：`回收站` 按钮展开面板（`仅显示最近 30 天内删除的内容`
   文案 + 空态），列表项 = 画布名 + 移除日期 + `恢复` 按钮。
3. 确认框文案不变（源站采样原文）。

### 不包含

- 30 天自动清除（clone 不做定时清除，条目保留到手动清除）；
- 被删画布的 Director project/持久化恢复语义（source 行为未采样）；
- 项目级回收站（clone 单项目）。

## 2. 证据边界

`SOURCE_FACT`：回收站存在、30 天文案、勾选与恢复按钮；
`CLONE_DECISION`：软删除保留完整快照、恢复不自动切换、无定时清除；
`SOURCE_UNKNOWN`：恢复后的画布内容完整性、回收站勾选批量操作、Director 数据随恢复行为。

## 3. 验证

- `scripts/verify-liblib-batch124.py`：删除 画布 2 → /project 回收站列出 →
  恢复 → 画布回列表且内容（节点）完整 → 再次删除/恢复幂等；空回收站文案；
  零诊断。
- 复跑 batch13/65/119；`npm run check`、`npm run docs:check`。

## 4. 完成定义

软删除/恢复闭环、内容完整；相邻回归与全量门通过；master commit/push。
