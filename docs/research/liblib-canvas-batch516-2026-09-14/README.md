# Batch 516 — SUBGRAPH-COPY focused fixture：duplicate 子图拷贝聚焦验收

> 状态：`FOCUSED_BROWSER_RECORDED_PASS`（commit 本批）。经真实
> `duplicateGraphSelection`（selectElements + duplicateSelectedNodes）：
> 拷贝获全新 ID 且数据深相等、源节点身份不动、选择迁移到拷贝、一命令
> 一步 history；两节点加内部边时内部边端点重映射到拷贝、连向未选中
> 邻居的外部边不泄漏；单次 undo 移除整个拷贝 cohort。
> 专用 group/child topology UI 场景与全量 corpus 未建（留档）。

## 内容

- `scripts/verify-liblib-batch516.py`（3 场景组）；
- FIXTURE_CATALOG SUBGRAPH-COPY 状态升级（双表）；
- `runtime-audit.json`：本目录。
