# Batch 124：画布回收站（软删除 + 恢复）

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 123。
>
> 源站证据：[`../liblib-projects-page-2026-09-06/README.md`](../liblib-projects-page-2026-09-06/README.md) 回收站采样（30 天保留/勾选/恢复）。

`removeCanvas` 改为软删除：完整 CanvasData 快照（含 nodes/edges/viewport）进
`removedCanvases`（带 removedAt）；`/project` 页「回收站」按钮展开真实面板
（「仅显示最近 30 天内删除的内容」+ 空态 + 条目「名称 · 日期 · 剩余 30 天」+
恢复按钮）。新增 `restoreCanvas`（恢复回列表，不自动切换活动画布）与
`purgeRemovedCanvas`。确认框文案不变。

## 完成定义

1. `verify-liblib-batch124.py` 14 checks、`0/0/0` diagnostics 通过：删除→回收站
   列出→恢复→内容完整（≥10 节点）→激活态正确。
2. 相邻 batch13/119 通过（119 回收站断言随本批迁移）。
3. `npm run check`、`npm run docs:check` 通过。
4. master commit/push。

30 天自动清除不做（CLONE_DECISION：条目保留至手动清除）；被删画布的
Director 数据随恢复完整性未采样（`SOURCE_UNKNOWN`）。
