# Batch 522 — GRAPH-DELETE shot 聚合场景聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> completeShotBreakdown（dimensions 为 "storyboard"|"motion"|"music"
> 字符串联合，非对象数组）/ removeNode / undo：完成创建 4 个
> shot-breakdown-result 节点、每个带 sourceBreakdownId 反向引用、恰
> 一步 history；删除 breakdown 后 cohort 全部存活、反向引用按观察契约
> 保留（删除不清洗引用——记录为观察行为）、零悬挂边、恰一步；undo
> 零残缺恢复 breakdown。long-video process 聚合与 canvas 场景未建。

## 内容

- `scripts/verify-liblib-batch522.py`（3 场景）；
- FIXTURE_CATALOG GRAPH-DELETE 行更新（shot 场景入档）；
- `runtime-audit.json`：本目录。
