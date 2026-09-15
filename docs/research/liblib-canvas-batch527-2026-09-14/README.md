# Batch 527 — GRAPH-DELETE canvas 场景聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> addCanvas/addNode/setActiveCanvas/removeCanvas/restoreCanvas：
> ① 删除非活动画布——注册表移除、removedCanvases 快照（带 removedAt）、
> historyByCanvas 条目清理；② 删除活动画布——相邻画布回退（batch 114）、
> 选择清空；③ restoreCanvas 恢复画布且图内容完整（batch 124/136 回收站
> 合同）。至此 GRAPH-DELETE 四组场景（plain/derived/shot/canvas）全部
> 聚焦验收完毕。

## 内容

- `scripts/verify-liblib-batch527.py`（3 场景）；
- FIXTURE_CATALOG GRAPH-DELETE 行定稿（四组场景全验收）；
- `runtime-audit.json`：本目录。
