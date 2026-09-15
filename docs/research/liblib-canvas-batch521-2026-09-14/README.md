# Batch 521 — GRAPH-DELETE derived-reference 场景聚焦验收 + batch 520 勘误

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> createFirstFrameReference / removeNode / undo：
> ① 全新 video 的派生创建为单事务（image 节点 + image→video 边 +
> 一条 history）；② 已有 image→video 边的 video 触发 batch 246/255
> 防重守卫（仅记 attempt 跳过建图）；③ 删除源 video 后派生 image
> 独立存活、零悬挂边、恰一步；④ undo 零残缺恢复。

## 勘误（batch 520）

batch 520 曾把派生场景判定为 BLOCKED_BY_FIXTURE（归因「无就绪媒体」）。
本批探证：no-op 实为防重守卫（demo video 已带 preset image 边），
以全新 video 反证。FIXTURE_CATALOG 已同步纠正。

## 内容

- `scripts/verify-liblib-batch521.py`（4 场景）；
- FIXTURE_CATALOG GRAPH-DELETE 行勘误更新；
- `runtime-audit.json`：本目录。
